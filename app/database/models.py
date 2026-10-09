"""Pydantic models: AI structured output and valid status values."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

STATUS_NOT_CONTACTED = "Not Contacted"
STATUS_DRAFTED = "Drafted"
STATUS_SENT = "Sent"
STATUS_REPLIED = "Replied"
STATUS_INTERESTED = "Interested"
STATUS_FOLLOWUP = "Follow-up"
STATUS_MEETING = "Meeting Scheduled"
STATUS_NOT_INTERESTED = "Not Interested"
STATUS_CLOSED = "Closed"

ALL_STATUSES = (
    STATUS_NOT_CONTACTED,
    STATUS_DRAFTED,
    STATUS_SENT,
    STATUS_REPLIED,
    STATUS_INTERESTED,
    STATUS_FOLLOWUP,
    STATUS_MEETING,
    STATUS_NOT_INTERESTED,
    STATUS_CLOSED,
)


class CompanyAnalysis(BaseModel):
    """Structured result of the company-analysis prompt."""

    company_summary: str = ""
    industry: str = ""
    products_services: str = ""
    ai_relevance: str = ""
    potential_student_opportunities: str = ""
    personalization_angle: str = ""
    location: str = ""
    key_contacts: list[dict] = Field(default_factory=list) # e.g. [{"name": "...", "role": "...", "email": "..."}]
    unknown_fields: list[str] = Field(default_factory=list)

    @field_validator("potential_student_opportunities", mode="before")
    @classmethod
    def _coerce_opportunities(cls, v):
        if isinstance(v, list):
            return ", ".join(str(item) for item in v)
        return str(v) if v is not None else ""


class PersonInfo(BaseModel):
    """Parsed contact information submitted by the user."""

    name: str
    role: str = ""
    company_name: str = ""
    linkedin_url: str = ""
    email: str = ""
    notes: str = ""


class OutreachDraft(BaseModel):
    """A generated outreach draft held in the user's session."""

    channel: str  # "Email" or "LinkedIn"
    message: str
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
