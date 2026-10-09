"""Message formatting helpers for Telegram output."""

from __future__ import annotations

import html


def esc(text: str | None) -> str:
    """HTML-escape text for Telegram parse_mode=HTML."""
    return html.escape(str(text or ""))


def truncate(text: str, limit: int = 4000, suffix: str = "…") -> str:
    if len(text) <= limit:
        return text
    return text[: limit - len(suffix)].rstrip() + suffix


def section(title: str) -> str:
    return f"━━ {title} ━━"


def company_card(company: dict) -> str:
    """Render a saved company as a Telegram HTML card."""
    parts = [
        f"<b>🏢 {esc(company['name'])}</b>  <i>#{company['id']}</i>",
    ]
    fields = [
        ("Industry", company.get("industry")),
        ("Location", company.get("location")),
        ("Website", company.get("website")),
        ("LinkedIn", company.get("linkedin_url")),
        ("Products / Services", company.get("products_services")),
        ("AI relevance", company.get("ai_relevance")),
        ("Opportunity", company.get("opportunity")),
        ("Personalization angle", company.get("personalization_angle")),
        ("Summary", company.get("description")),
    ]
    for label, value in fields:
        if value:
            parts.append(f"\n<b>{esc(label)}:</b> {esc(value)}")
    return "\n".join(parts)


def contact_card(contact: dict, company_name: str = "") -> str:
    parts = [
        f"<b>👤 {esc(contact['name'])}</b>  <i>#{contact['id']}</i>"
    ]
    if contact.get("role"):
        parts.append(esc(contact["role"]))
    if company_name:
        parts.append(f"at {esc(company_name)}")
    for label, key in (("LinkedIn", "linkedin_url"), ("Email", "email"), ("Notes", "notes")):
        if contact.get(key):
            parts.append(f"<b>{label}:</b> {esc(contact[key])}")
    return "\n".join(parts)
