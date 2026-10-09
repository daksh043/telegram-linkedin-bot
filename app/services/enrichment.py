"""Data acquisition and normalization.

Permitted sources only: user-pasted text, LinkedIn/company URLs supplied
by the user, and public company website pages fetched with a plain HTTP
GET (no authentication bypass, no scraping of LinkedIn).
"""

from __future__ import annotations

import re

import httpx

MAX_WEBSITE_CHARS = 6000
FETCH_TIMEOUT = 15.0

_TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_HTML_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def html_to_text(html: str) -> str:
    text = _TAG_RE.sub(" ", html)
    text = _HTML_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


async def fetch_website_text(url: str) -> str:
    """Fetch a public company website homepage as plain text.

    Failure-tolerant: returns "" on any error so research can continue
    with user-supplied information only.
    """
    if not url:
        return ""
    try:
        async with httpx.AsyncClient(
            timeout=FETCH_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "OutreachAI/1.0 (research assistant)"},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return html_to_text(resp.text)[:MAX_WEBSITE_CHARS]
    except (httpx.HTTPError, ValueError):
        return ""


def build_research_brief(
    user_text: str,
    linkedin_url: str = "",
    website_url: str = "",
    website_text: str = "",
) -> str:
    """Combine permitted sources into one brief for AI analysis."""
    parts: list[str] = []
    if linkedin_url:
        parts.append(f"LinkedIn page (URL provided by user): {linkedin_url}")
    if website_url:
        parts.append(f"Company website (URL provided by user): {website_url}")
        if website_text:
            parts.append(f"Website text:\n{website_text}")
    parts.append(f"Information provided by the user:\n{user_text.strip()}")
    return "\n\n".join(parts)[:18_000]


def search_contacts_via_serpapi(company_name: str, api_key: str) -> str:
    """Search for employee contacts using SerpApi."""
    if not api_key or not company_name:
        return ""
    try:
        from serpapi import GoogleSearch
        query = f'site:linkedin.com/in "{company_name}" (HR OR Recruiter OR CEO OR Founder OR Manager)'
        params = {
          "engine": "google",
          "q": query,
          "api_key": api_key,
          "num": 5
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        organic = results.get("organic_results", [])
        
        found = []
        
        ai_overview_1 = results.get("ai_overview", {})
        if ai_overview_1 and ai_overview_1.get("text"):
            found.append(f"Google AI Overview:\n{ai_overview_1['text']}")
            
        answer_box_1 = results.get("answer_box", {})
        if answer_box_1 and answer_box_1.get("snippet"):
            found.append(f"Google Answer Box:\n{answer_box_1['snippet']}")

        for r in organic:
            title = r.get("title", "")
            snippet = r.get("snippet", "")
            link = r.get("link", "")
            found.append(f"Found on LinkedIn:\nTitle: {title}\nSnippet: {snippet}\nLink: {link}")
            
        # Second query: look for email addresses
        email_query = f'"{company_name}" "email" OR "contact" "@"'
        email_params = {
          "engine": "google",
          "q": email_query,
          "api_key": api_key,
          "num": 3
        }
        email_search = GoogleSearch(email_params)
        email_results = email_search.get_dict()
        email_organic = email_results.get("organic_results", [])
        
        ai_overview_2 = email_results.get("ai_overview", {})
        if ai_overview_2 and ai_overview_2.get("text"):
            found.append(f"Google AI Overview (Emails):\n{ai_overview_2['text']}")
            
        answer_box_2 = email_results.get("answer_box", {})
        if answer_box_2 and answer_box_2.get("snippet"):
            found.append(f"Google Answer Box (Emails):\n{answer_box_2['snippet']}")
        
        for r in email_organic:
            title = r.get("title", "")
            snippet = r.get("snippet", "")
            found.append(f"Web search for emails:\nTitle: {title}\nSnippet: {snippet}")
            
        return "\n\n".join(found)
    except Exception as e:
        print(f"SerpApi Error: {e}")
        return ""
