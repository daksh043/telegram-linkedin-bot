"""Outreach orchestration: research pipeline and draft generation.

Pipeline per TRD §8:
Input → Validate → Research → Normalize → Duplicate Check → AI Analysis
→ Personalize → Generate Drafts (user reviews, sends manually).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Config
from app.database.models import PersonInfo
from app.database.repository import Repository
from app.services import enrichment, linkedin
from app.services.ai import AIService
from app.utils import validators


@dataclass
class ResearchResult:
    company_id: int
    company: dict
    is_new: bool
    brief: str


class OutreachService:
    def __init__(self, config: Config, repository: Repository) -> None:
        self.config = config
        self.repository = repository
        self.ai = AIService(config)

    # ------------------------------------------------------------------
    # company research
    # ------------------------------------------------------------------

    async def research_company(self, user_text: str) -> ResearchResult:
        ok, error = validators.validate_user_input(user_text)
        if not ok:
            raise ValueError(error)

        parsed_linkedin = linkedin.parse(user_text)
        website_url = validators.extract_website_url(user_text)
        website_text = ""
        if website_url:
            website_text = await enrichment.fetch_website_text(website_url)

        guessed_name = ""
        if parsed_linkedin.kind == "company":
            guessed_name = parsed_linkedin.display_name

        brief = enrichment.build_research_brief(
            user_text=user_text,
            linkedin_url=parsed_linkedin.url,
            website_url=website_url,
            website_text=website_text,
        )
        
        candidate = guessed_name or _first_company_name(user_text)
        
        # If SerpApi key is present, find contacts and append them to the brief for the AI to parse
        if self.config.serpapi_key and candidate:
            serp_results = enrichment.search_contacts_via_serpapi(candidate, self.config.serpapi_key)
            if serp_results:
                brief += f"\n\nWeb search results for {candidate} employees on LinkedIn:\n{serp_results}"

        analysis = None
        if self.config.ai_enabled:
            analysis = await self.ai.analyze_company(brief)

        # Duplicate check by name (LinkedIn slug-derived or AI-guessed).
        candidate = guessed_name or _first_company_name(user_text)
        existing = None
        if candidate:
            existing = await self.repository.find_company_by_name(candidate)

        if existing:
            updates: dict = {}
            if analysis:
                updates.update(_analysis_fields(analysis))
            if parsed_linkedin.url and not existing.get("linkedin_url"):
                updates["linkedin_url"] = parsed_linkedin.url
            if website_url and not existing.get("website"):
                updates["website"] = website_url
            if updates:
                await self.repository.update_company(existing["id"], **updates)
                existing = await self.repository.get_company(existing["id"])
            if analysis and getattr(analysis, "key_contacts", None):
                for c in analysis.key_contacts:
                    if c.get("name"):
                        await self.save_contact(existing["id"], PersonInfo(name=c["name"], role=c.get("role", ""), email=c.get("email", "")))
            return ResearchResult(existing["id"], existing, is_new=False, brief=brief)

        name = candidate or "Unknown Company"
        fields: dict = {"name": name}
        if parsed_linkedin.url:
            fields["linkedin_url"] = parsed_linkedin.url
        if website_url:
            fields["website"] = website_url
        if analysis:
            fields.update(_analysis_fields(analysis))
        company_id = await self.repository.add_company(**fields)
        company = await self.repository.get_company(company_id)
        if analysis and getattr(analysis, "key_contacts", None):
            for c in analysis.key_contacts:
                if c.get("name"):
                    await self.save_contact(company_id, PersonInfo(name=c["name"], role=c.get("role", ""), email=c.get("email", "")))
        return ResearchResult(company_id, company, is_new=True, brief=brief)

    # ------------------------------------------------------------------
    # contact research
    # ------------------------------------------------------------------

    def parse_person(self, user_text: str) -> PersonInfo:
        """Parse pasted contact info with heuristics (no invented data)."""
        ok, error = validators.validate_user_input(user_text)
        if not ok:
            raise ValueError(error)

        person_url = validators.extract_linkedin_person_url(user_text)
        email = validators.extract_email(user_text)
        lines = [ln.strip() for ln in user_text.splitlines() if ln.strip()]

        name = ""
        role = ""
        for ln in lines:
            lower = ln.lower()
            if lower.startswith("name:"):
                name = ln.split(":", 1)[-1].strip()
            elif lower.startswith(("role:", "title:", "designation:", "position:")):
                role = ln.split(":", 1)[-1].strip()
            elif validators.is_http_url(ln) or "@" in ln:
                continue
        if not name and lines:
            # First line that is not a URL and has no email.
            for ln in lines:
                if not validators.is_http_url(ln) and "@" not in ln:
                    name = ln.strip(" -–—")
                    break
        # Drop prefixes like "Name - John Doe" leftovers.
        name = name.strip()

        company_name = ""
        for ln in lines:
            lower = ln.lower()
            if lower.startswith(("company:", "organisation:", "organization:")):
                company_name = ln.split(":", 1)[-1].strip()
                break

        notes = user_text.strip()
        return PersonInfo(
            name=name or "Unknown Contact",
            role=role,
            company_name=company_name,
            linkedin_url=person_url,
            email=email,
            notes=notes[:2000],
        )

    async def save_contact(
        self, company_id: int, person: PersonInfo
    ) -> tuple[int, bool]:
        """Add contact unless duplicate. Returns (contact_id, is_new)."""
        existing = await self.repository.find_contact(company_id, person.name)
        if existing:
            return existing["id"], False
        contact_id = await self.repository.add_contact(
            company_id,
            name=person.name,
            role=person.role,
            linkedin_url=person.linkedin_url,
            email=person.email,
            notes=person.notes,
        )
        return contact_id, True

    # ------------------------------------------------------------------
    # drafts
    # ------------------------------------------------------------------

    def _require_ai(self) -> None:
        if not self.config.ai_enabled:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. Add it to .env to use AI drafting."
            )

    async def draft_email_stream(
        self, company: dict, contact: dict | None, brief: str
    ):
        self._require_ai()
        async for chunk in self.ai.generate_email_stream(
            company_name=company["name"],
            company_information=brief,
            personalization_angle=company.get("personalization_angle", ""),
        ):
            yield chunk

    async def draft_linkedin_stream(
        self, company: dict, contact: dict | None, brief: str
    ):
        self._require_ai()
        contact_name = (contact or {}).get("name", "")
        contact_role = (contact or {}).get("role", "")
        if not contact_name:
            contact_name = f"the {company['name']} team"
            contact_role = "company representative"
        async for chunk in self.ai.generate_linkedin_message_stream(
            contact_name=contact_name,
            contact_role=contact_role,
            company_name=company["name"],
            company_information=brief,
        ):
            yield chunk

    async def rewrite_stream(self, message: str, style: str):
        self._require_ai()
        async for chunk in self.ai.rewrite_stream(message, style):
            yield chunk


def _analysis_fields(analysis) -> dict:
    return {
        "description": analysis.company_summary,
        "industry": analysis.industry,
        "products_services": analysis.products_services,
        "ai_relevance": analysis.ai_relevance,
        "opportunity": analysis.potential_student_opportunities,
        "personalization_angle": analysis.personalization_angle,
        "location": analysis.location,
    }


_NAME_SEPARATORS = (" — ", " – ", " | ", " - ", ": ")


def _first_company_name(user_text: str) -> str:
    """Best-effort company name from the first non-URL line."""
    for ln in user_text.splitlines():
        ln = ln.strip()
        if not ln or validators.is_http_url(ln) or "@" in ln:
            continue
        lower = ln.lower()
        if lower.startswith(("name:", "company:")):
            return ln.split(":", 1)[-1].strip()
        for sep in _NAME_SEPARATORS:
            # Pasted lines often read "Acme Labs — AI data company".
            if sep in ln:
                ln = ln.split(sep, 1)[0].strip()
                break
        return ln[:120]
    return ""
