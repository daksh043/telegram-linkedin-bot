"""Tracking handlers: mark sent/replied, follow-ups, status, export."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.database.models import (
    ALL_STATUSES,
    STATUS_FOLLOWUP,
    STATUS_SENT,
)
from app.handlers.common import guard, get_services, reply
from app.services.analytics import compute_analytics, render_status
from app.utils.dates import add_days, fmt, today_iso
from app.utils.formatting import esc, truncate


def _resolve_outreach_id(context: ContextTypes.DEFAULT_TYPE, arg: str | None) -> int | None:
    if arg and arg.isdigit():
        return int(arg)
    return context.user_data.get("last_outreach_id")


async def mark_sent_by_id(
    update: Update, context: ContextTypes.DEFAULT_TYPE, outreach_id: int
) -> None:
    services = get_services(context)
    existing = await services.repository.get_outreach(outreach_id)
    if not existing:
        await reply(update, f"Outreach #{outreach_id} not found.")
        return
    today = today_iso()
    follow_up = add_days(today, services.config.default_followup_days)
    record = await services.repository.update_outreach(
        outreach_id,
        status=STATUS_SENT,
        date_contacted=today,
        follow_up_date=follow_up,
    )
    await reply(
        update,
        f"📤 Outreach #{outreach_id} marked <b>Sent</b>.\n"
        f"Date contacted: {fmt(record['date_contacted'])}\n"
        f"Follow-up due: {fmt(record['follow_up_date'])}\n\n"
        f"I'll surface it in /followups from that date.",
    )


@guard
async def mark_sent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    outreach_id = _resolve_outreach_id(context, args[0] if args else None)
    if not outreach_id:
        await reply(update, "Usage: /mark_sent <id>  (or save a draft first with /save)")
        return
    await mark_sent_by_id(update, context, outreach_id)


@guard
async def mark_replied_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usage: /mark_replied <id> [status] [response text]

    Status defaults to Replied; any of the 9 tracker statuses is accepted.
    """
    services = get_services(context)
    args = context.args or []
    if not args or not args[0].isdigit():
        await reply(
            update,
            "Usage: /mark_replied <id> [status] [response]\n"
            f"Statuses: {', '.join(ALL_STATUSES)}",
        )
        return
    outreach_id = int(args[0])
    status = "Replied"
    rest = args[1:]
    if rest and rest[0].title() in ALL_STATUSES:
        status = rest[0].title()
        rest = rest[1:]
    response = " ".join(rest).strip()

    existing = await services.repository.get_outreach(outreach_id)
    if not existing:
        await reply(update, f"Outreach #{outreach_id} not found.")
        return
    fields: dict = {"status": status}
    if response:
        fields["response"] = response
    if status == STATUS_FOLLOWUP:
        fields["follow_up_date"] = add_days(today_iso(), services.config.default_followup_days)
    record = await services.repository.update_outreach(outreach_id, **fields)
    await reply(
        update,
        f"💬 Outreach #{outreach_id} → <b>{esc(record['status'])}</b>\n"
        + (f"Response: {esc(record['response'])}" if record.get("response") else ""),
    )


@guard
async def followups_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    services = get_services(context)
    due = await services.repository.due_followups()
    if not due:
        await reply(update, "🎉 No follow-ups due. (Sent items appear here after their follow-up date.)")
        return
    companies = {c["id"]: c for c in await services.repository.list_companies()}
    lines = ["<b>⏰ Follow-ups due</b>\n"]
    for o in due:
        company = companies.get(o["company_id"], {})
        lines.append(
            f"#{o['id']} {esc(company.get('name', '?'))} — "
            f"{esc(o['channel'])}, sent {fmt(o['date_contacted'])}, "
            f"due {fmt(o['follow_up_date'])}"
        )
    await reply(update, truncate("\n".join(lines), 4000))


@guard
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    services = get_services(context)
    analytics = await compute_analytics(services.repository)
    await reply(update, render_status(analytics))


@guard
async def export_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    services = get_services(context)
    status = await update.effective_message.reply_text("Building Excel tracker…")
    try:
        path = await services.excel.export()
    except Exception:
        await status.edit_text("⚠️ Export failed. Check logs.")
        raise
    with open(path, "rb") as fh:
        await update.effective_message.reply_document(
            document=fh,
            filename=path.replace("\\", "/").rsplit("/", 1)[-1],
            caption="📊 Outreach tracker (SQLite remains the source of truth).",
        )
    await status.delete()
