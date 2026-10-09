"""Input validation and extraction helpers.

Only permitted data is used: user-pasted text and public URLs the user
supplies. No LinkedIn scraping happens anywhere in this module.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

MAX_INPUT_LENGTH = 15_000

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_LINKEDIN_COMPANY_RE = re.compile(
    r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/company/([\w\-'.%]+)",
    re.IGNORECASE,
)
_LINKEDIN_PERSON_RE = re.compile(
    r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/in/([\w\-'.%]+)",
    re.IGNORECASE,
)


def is_http_url(text: str) -> bool:
    try:
        parsed = urlparse(text.strip())
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def validate_user_input(text: str) -> tuple[bool, str]:
    """Validate free-form research input. Returns (ok, error message)."""
    stripped = (text or "").strip()
    if not stripped:
        return False, "Input is empty. Send a LinkedIn/company URL or pasted information."
    if len(stripped) > MAX_INPUT_LENGTH:
        return False, f"Input is too long (max {MAX_INPUT_LENGTH} characters)."
    return True, ""


def extract_linkedin_company_url(text: str) -> str:
    match = _LINKEDIN_COMPANY_RE.search(text)
    return match.group(0).rstrip("/") if match else ""


def extract_linkedin_person_url(text: str) -> str:
    match = _LINKEDIN_PERSON_RE.search(text)
    return match.group(0).rstrip("/") if match else ""


def extract_linkedin_company_slug(text: str) -> str:
    match = _LINKEDIN_COMPANY_RE.search(text)
    return match.group(1).lower() if match else ""


def company_name_from_slug(slug: str) -> str:
    """Best-effort display name from a LinkedIn company slug."""
    return slug.replace("-", " ").strip().title() if slug else ""


def extract_website_url(text: str) -> str:
    """Return the first non-LinkedIn http(s) URL found in the text."""
    for token in text.split():
        candidate = token.strip("<>()\"',")
        if not is_http_url(candidate):
            continue
        netloc = urlparse(candidate).netloc.lower()
        if "linkedin.com" in netloc:
            continue
        return candidate
    return ""


def extract_email(text: str) -> str:
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else ""
