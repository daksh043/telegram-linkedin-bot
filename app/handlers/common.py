"""Shared handler plumbing: services container, access guard, replies."""

from __future__ import annotations

import functools
from dataclasses import dataclass

from telegram import Update

from app.config import Config
from app.database.repository import Repository
from app.services.excel import ExcelService
from app.services.outreach import OutreachService


@dataclass
class Services:
    config: Config
    repository: Repository
    outreach: OutreachService
    excel: ExcelService


def get_services(context) -> Services:
    return context.bot_data["services"]


async def reply(update: Update, text: str, **kwargs) -> None:
    """Reply with HTML parsing, falling back to plain text if needed."""
    message = update.effective_message
    if message is None:
        return
    kwargs.setdefault("parse_mode", "HTML")
    try:
        await message.reply_text(text, **kwargs)
    except Exception:  # malformed HTML should never kill a handler
        kwargs.pop("parse_mode", None)
        await message.reply_text(text, **kwargs)


def guard(func):
    """Allowlist gate applied to every handler (per SECURITY.md)."""

    @functools.wraps(func)
    async def wrapper(update: Update, context) -> None:
        services = get_services(context)
        user = update.effective_user
        if user is None:
            return
        allowed = services.config.allowed_user_ids
        if not allowed:
            await reply(
                update,
                "🔒 The bot is locked. Your Telegram ID is "
                f"<code>{user.id}</code>.\nAdd it to TELEGRAM_ALLOWED_USER_IDS "
                "in .env and restart the bot.",
            )
            return
        if user.id not in allowed:
            await reply(
                update,
                "⛔ You are not authorized to use this bot.\n"
                f"Your Telegram ID is <code>{user.id}</code>. If that is you, "
                "add it to TELEGRAM_ALLOWED_USER_IDS in .env and restart "
                "the bot.",
            )
            return
        return await func(update, context)

    return wrapper


HELP_TEXT = """<b>OutreachAI commands</b>

<b>Research</b>
/company — research a company (send URL or pasted info)
/person — add a contact at the current company
/companies — list saved companies
/company_info &lt;id&gt; — show a company and select it

<b>Outreach</b>
/email — generate an email draft
/message — generate a LinkedIn message
/rewrite &lt;instruction&gt; — rewrite the current draft
/short — shorter version
/formal — more formal version
/human — more natural version
/save — save the current draft

<b>Tracking</b>
/mark_sent &lt;id&gt; — mark outreach as sent (schedules follow-up)
/mark_replied &lt;id&gt; [status] [response] — record a response
/followups — outreach needing follow-up
/status — outreach metrics
/export — build and send the Excel tracker

<b>Other</b>
/settings — student profile and preferences

You review and send every message manually — the bot only drafts and tracks."""
