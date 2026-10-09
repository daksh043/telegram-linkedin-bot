"""LinkedIn URL handling.

This module only parses URLs the user supplies. It performs NO scraping
and never bypasses access controls, per SECURITY.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.utils.validators import (
    company_name_from_slug,
    extract_linkedin_company_slug,
    extract_linkedin_company_url,
    extract_linkedin_person_url,
    is_http_url,
)


@dataclass
class ParsedLinkedIn:
    kind: str  # "company", "person", or ""
    url: str
    slug: str
    display_name: str


def parse(text: str) -> ParsedLinkedIn:
    """Identify a LinkedIn company/person URL in user-supplied text."""
    company_url = extract_linkedin_company_url(text)
    if company_url:
        slug = extract_linkedin_company_slug(text)
        return ParsedLinkedIn("company", company_url, slug, company_name_from_slug(slug))
    person_url = extract_linkedin_person_url(text)
    if person_url:
        slug = person_url.rsplit("/", 1)[-1]
        return ParsedLinkedIn("person", person_url, slug, slug.replace("-", " ").title())
    return ParsedLinkedIn("", "", "", "")


def looks_like_linkedin(text: str) -> bool:
    return is_http_url(text.strip()) and "linkedin.com" in text.strip().lower()
