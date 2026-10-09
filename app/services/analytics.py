"""Outreach analytics: volumes, response rate, interest rate."""

from __future__ import annotations

from app.database.models import (
    STATUS_CLOSED,
    STATUS_DRAFTED,
    STATUS_FOLLOWUP,
    STATUS_INTERESTED,
    STATUS_MEETING,
    STATUS_NOT_INTERESTED,
    STATUS_REPLIED,
    STATUS_SENT,
)
from app.database.repository import Repository


def rates(sent: int, replied: int, interested: int) -> tuple[str, str]:
    """Response rate = replied / sent; interest rate = interested / sent."""
    if sent <= 0:
        return ("", "")
    response = f"{(replied / sent) * 100:.0f}%"
    interest = f"{(interested / sent) * 100:.0f}%"
    return response, interest


async def compute_analytics(repository: Repository) -> dict[str, object]:
    counts = await repository.status_counts()
    totals = await repository.totals()
    sent = counts.get(STATUS_SENT, 0)
    replied = counts.get(STATUS_REPLIED, 0)
    # Once someone replies, the status moves on (Interested, Meeting...),
    # so count replies as everything that reached reply stage or beyond.
    replied_total = replied + counts.get(STATUS_INTERESTED, 0) + counts.get(
        STATUS_MEETING, 0
    ) + counts.get(STATUS_NOT_INTERESTED, 0) + counts.get(STATUS_CLOSED, 0)
    interested_total = counts.get(STATUS_INTERESTED, 0) + counts.get(STATUS_MEETING, 0)
    sent_total = sent + replied_total
    response_rate, interest_rate = rates(sent_total, replied_total, interested_total)
    return {
        "total_companies": totals.get("total_companies", 0),
        "total_contacts": totals.get("total_contacts", 0),
        "drafted": counts.get(STATUS_DRAFTED, 0),
        "sent": sent,
        "replied": replied_total,
        "interested": interested_total,
        "meetings": counts.get(STATUS_MEETING, 0),
        "followups": counts.get(STATUS_FOLLOWUP, 0),
        "not_interested": counts.get(STATUS_NOT_INTERESTED, 0),
        "closed": counts.get(STATUS_CLOSED, 0),
        "response_rate": response_rate,
        "interest_rate": interest_rate,
    }


def render_status(analytics: dict[str, object]) -> str:
    return (
        f"📊 <b>Outreach Status</b>\n"
        f"Companies: {analytics['total_companies']}  •  "
        f"Contacts: {analytics['total_contacts']}\n"
        f"Drafted: {analytics['drafted']}  •  Sent: {analytics['sent']}\n"
        f"Replied: {analytics['replied']}  •  "
        f"Interested: {analytics['interested']}\n"
        f"Meetings: {analytics['meetings']}  •  "
        f"Follow-ups: {analytics['followups']}\n"
        f"Not interested: {analytics['not_interested']}  •  "
        f"Closed: {analytics['closed']}\n"
        f"Response rate: {analytics['response_rate'] or '—'}  •  "
        f"Interest rate: {analytics['interest_rate'] or '—'}"
    )
