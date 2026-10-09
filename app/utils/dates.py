"""Date helpers used across the app (ISO format everywhere in storage)."""

from __future__ import annotations

from datetime import date, datetime, timedelta


def today_iso() -> str:
    return date.today().isoformat()


def add_days(iso_date: str, days: int) -> str:
    base = date.fromisoformat(iso_date)
    return (base + timedelta(days=days)).isoformat()


def fmt(iso_date: str | None) -> str:
    """Format an ISO date for display; empty string for missing values."""
    if not iso_date:
        return ""
    try:
        return date.fromisoformat(iso_date[:10]).strftime("%d %b %Y")
    except ValueError:
        return iso_date


def now_ts() -> str:
    return datetime.now().isoformat(timespec="seconds")
