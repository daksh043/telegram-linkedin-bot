"""Start and help handlers."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.common import HELP_TEXT, guard, reply


@guard
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    services = context.bot_data["services"]
    await reply(
        update,
        f"👋 Hi {services.config.student_name}!\n\n"
        "I help you research companies, draft personalized outreach, and "
        "track everything in SQLite + Excel.\n\n"
        "Start with <b>/company</b> and send a LinkedIn/company URL or "
        "pasted information.\n\n"
        "⚠️ You review and send every message manually.",
    )


@guard
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, HELP_TEXT)
