"""Settings handler: show the student profile the bot drafts as."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.common import guard, get_services, reply
from app.utils.formatting import esc


@guard
async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    services = get_services(context)
    cfg = services.config
    await reply(
        update,
        "⚙️ <b>Settings</b>\n\n"
        f"<b>Student:</b> {esc(cfg.student_name)}\n"
        f"<b>College:</b> {esc(cfg.student_college)}\n"
        f"<b>Role:</b> {esc(cfg.student_role)}\n"
        f"<b>Default follow-up:</b> {cfg.default_followup_days} days\n"
        f"<b>AI model:</b> {esc(cfg.ai_model) if cfg.ai_enabled else 'not configured'}\n"
        f"<b>Database:</b> {esc(cfg.database_path)}\n"
        f"<b>Excel:</b> {esc(cfg.excel_path)}\n\n"
        "These live in <code>.env</code> — edit and restart to change.",
    )
