"""AI service: company analysis, draft generation, rewrites.

Uses the Groq SDK as the primary endpoint.
Falls back to the OpenAI SDK against Google AI Studio (Gemini) if Groq fails or is unavailable.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from groq import AsyncGroq
import groq
from openai import AsyncOpenAI
import openai
from pydantic import ValidationError

from app.config import Config
from app.database.models import CompanyAnalysis

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8")


def parse_company_analysis(raw: str) -> CompanyAnalysis:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("AI response did not contain a JSON object")
    data = json.loads(text[start : end + 1])
    return CompanyAnalysis.model_validate(data)


class AIService:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._groq_client: AsyncGroq | None = None
        self._gemini_client: AsyncOpenAI | None = None

    def _get_groq_client(self) -> AsyncGroq | None:
        if not self.config.groq_api_key:
            return None
        if self._groq_client is None:
            self._groq_client = AsyncGroq(api_key=self.config.groq_api_key)
        return self._groq_client

    def _get_gemini_client(self) -> AsyncOpenAI | None:
        if not self.config.gemini_api_key:
            return None
        if self._gemini_client is None:
            self._gemini_client = AsyncOpenAI(
                api_key=self.config.gemini_api_key,
                base_url=self.config.gemini_base_url
            )
        return self._gemini_client

    def _require_key(self) -> None:
        if not self.config.groq_api_key and not self.config.gemini_api_key:
            raise RuntimeError(
                "Neither GROQ_API_KEY nor GEMINI_API_KEY is configured. "
                "Please add one of them to your .env file."
            )

    async def _create_with_retry(self, **kwargs):
        last_exc: Exception | None = None
        
        groq_client = self._get_groq_client()
        gemini_client = self._get_gemini_client()
        
        # Determine whether to use Groq kwargs or basic kwargs
        groq_kwargs = {**kwargs}
        if "model" in groq_kwargs:
            groq_kwargs["model"] = self.config.ai_model
            groq_kwargs["temperature"] = 1
            groq_kwargs["max_tokens"] = 2048
            groq_kwargs["top_p"] = 1
            groq_kwargs["stream"] = kwargs.get("stream", False)
            if "response_format" in groq_kwargs:
                groq_kwargs.pop("response_format", None)
            
        gemini_kwargs = {**kwargs}
        if "model" in gemini_kwargs:
            gemini_kwargs["model"] = self.config.gemini_model
            gemini_kwargs["temperature"] = 0.4
            gemini_kwargs["stream"] = kwargs.get("stream", False)
        
        json_mode = kwargs.get("response_format", {}).get("type") == "json_object"
        is_stream = kwargs.get("stream", False)

        # Try Groq first
        if groq_client:
            for attempt in range(1, _MAX_ATTEMPTS + 1):
                try:
                    kw = {**groq_kwargs}
                    if json_mode:
                        kw["response_format"] = {"type": "json_object"}
                    return await groq_client.chat.completions.create(**kw)
                except groq.BadRequestError as e:
                    if not json_mode:
                        last_exc = e
                        break
                    logger.warning("Groq rejected json_mode; retrying without it.")
                    try:
                        return await groq_client.chat.completions.create(**groq_kwargs)
                    except Exception as e2:
                        last_exc = e2
                        break
                except (groq.RateLimitError, groq.APITimeoutError, groq.APIConnectionError, groq.InternalServerError) as exc:
                    last_exc = exc
                    if attempt == _MAX_ATTEMPTS or is_stream:
                        break
                    wait = 2.0 * 2 ** (attempt - 1)
                    logger.warning("Groq call failed (%s), retrying in %.0fs", exc.__class__.__name__, wait)
                    await asyncio.sleep(wait)
                except Exception as exc:
                    last_exc = exc
                    break

            logger.warning("Groq exhausted/failed (error: %s). Falling back to Gemini...", type(last_exc).__name__)

        # Fallback to Gemini
        if gemini_client:
            for attempt in range(1, _MAX_ATTEMPTS + 1):
                try:
                    return await gemini_client.chat.completions.create(**gemini_kwargs)
                except openai.BadRequestError as e:
                    if not json_mode:
                        last_exc = e
                        break
                    logger.warning("Gemini rejected json_mode; retrying without it.")
                    gemini_kwargs.pop("response_format", None)
                    try:
                        return await gemini_client.chat.completions.create(**gemini_kwargs)
                    except Exception as e2:
                        last_exc = e2
                        break
                except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError, openai.InternalServerError) as exc:
                    last_exc = exc
                    if attempt == _MAX_ATTEMPTS or is_stream:
                        break
                    wait = 2.0 * 2 ** (attempt - 1)
                    logger.warning("Gemini call failed (%s), retrying in %.0fs", exc.__class__.__name__, wait)
                    await asyncio.sleep(wait)
                except Exception as exc:
                    last_exc = exc
                    break
                    
        raise RuntimeError(
            "Both AI services are busy right now or failed - please try again in a minute. "
            f"(last error: {last_exc.__class__.__name__})"
        ) from last_exc

    async def _complete(self, system: str, user: str, json_mode: bool = False) -> str:
        self._require_key()
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        kwargs = {"messages": messages, "model": "placeholder"}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
            
        resp = await self._create_with_retry(**kwargs)
        content = resp.choices[0].message.content or ""
        logger.debug("AI call completed (%d chars)", len(content))
        return content

    async def _complete_stream(self, system: str, user: str):
        self._require_key()
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        kwargs = {"messages": messages, "model": "placeholder", "stream": True}
        stream = await self._create_with_retry(**kwargs)
        
        async for chunk in stream:
            content = ""
            if chunk.choices and len(chunk.choices) > 0:
                if hasattr(chunk.choices[0], "delta") and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                elif hasattr(chunk.choices[0], "text") and chunk.choices[0].text:
                    content = chunk.choices[0].text
            if content:
                yield content

    async def analyze_company(self, company_information: str) -> CompanyAnalysis:
        prompt = load_prompt("company_analysis").format(
            student_name=self.config.student_name,
            student_college=self.config.student_college,
            student_role=self.config.student_role,
            company_information=company_information,
        )
        system = (
            "You are a careful research assistant. Use only supplied "
            "information. Never invent company facts. Respond in JSON."
        )
        raw = await self._complete(system, prompt, json_mode=True)
        try:
            return parse_company_analysis(raw)
        except (ValueError, json.JSONDecodeError, ValidationError):
            logger.warning("Retrying company analysis after invalid JSON")
            raw = await self._complete(system, prompt, json_mode=True)
            return parse_company_analysis(raw)

    async def generate_email_stream(self, company_name: str, company_information: str, personalization_angle: str):
        prompt = load_prompt("outreach_email").format(
            student_name=self.config.student_name,
            student_college=self.config.student_college,
            student_role=self.config.student_role,
            company_name=company_name,
            company_information=company_information,
            personalization_angle=personalization_angle,
        )
        system = "You write concise, human-sounding professional outreach. Never invent facts about the company."
        async for chunk in self._complete_stream(system, prompt):
            yield chunk

    async def generate_linkedin_message_stream(self, contact_name: str, contact_role: str, company_name: str, company_information: str):
        prompt = load_prompt("linkedin_message").format(
            contact_name=contact_name or "there",
            contact_role=contact_role,
            company_name=company_name,
            company_information=company_information,
            student_name=self.config.student_name,
            student_college=self.config.student_college,
            student_role=self.config.student_role,
        )
        system = "You write short, natural LinkedIn messages. Never invent facts about the company or recipient."
        async for chunk in self._complete_stream(system, prompt):
            yield chunk

    async def rewrite_stream(self, message: str, style: str):
        prompt = load_prompt("rewrite").format(message=message, style=style)
        system = "You rewrite outreach messages while preserving factual accuracy. Never add invented information."
        async for chunk in self._complete_stream(system, prompt):
            yield chunk
