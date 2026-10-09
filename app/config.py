"""Application configuration loaded from environment variables (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_AI_MODEL = "openai/gpt-oss-120b"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"

# Load .env from the project root, independent of the working directory.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    groq_api_key: str
    gemini_api_key: str
    ai_model: str
    gemini_model: str
    gemini_base_url: str
    database_path: str
    excel_path: str
    student_name: str
    student_college: str
    student_role: str
    default_followup_days: int
    log_level: str
    serpapi_key: str = ""
    allowed_user_ids: frozenset[int] = field(default_factory=frozenset)

    @property
    def ai_enabled(self) -> bool:
        return bool(self.groq_api_key or self.gemini_api_key)

    @classmethod
    def from_env(cls) -> "Config":
        raw_ids = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "")
        ids = frozenset(
            int(part.strip())
            for part in raw_ids.split(",")
            if part.strip().isdigit()
        )
        
        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            gemini_api_key=os.getenv("GEMINI_API_KEY", "") or os.getenv("OPENAI_API_KEY", ""),
            ai_model=os.getenv("AI_MODEL", DEFAULT_AI_MODEL),
            gemini_model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
            gemini_base_url=os.getenv("GEMINI_BASE_URL", GEMINI_BASE_URL),
            database_path=os.getenv("DATABASE_PATH", "data/outreach.db"),
            excel_path=os.getenv("EXCEL_PATH", "data/Outreach_Tracker.xlsx"),
            student_name=os.getenv("STUDENT_NAME", "Daksh Khandagale"),
            student_college=os.getenv(
                "STUDENT_COLLEGE", "Universal AI University, Karjat"
            ),
            student_role=os.getenv(
                "STUDENT_ROLE", "Student involved in student-industry engagement"
            ),
            default_followup_days=int(os.getenv("DEFAULT_FOLLOWUP_DAYS", "7")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            allowed_user_ids=ids,
            serpapi_key=os.getenv("SERPAPI_API_KEY", ""),
        )
