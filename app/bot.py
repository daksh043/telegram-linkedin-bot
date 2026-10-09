"""OutreachAI Telegram bot entry point.

Run with:  python -m app.bot
"""

from __future__ import annotations

import logging
import sys

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import Config
from app.database.repository import Repository
from app.handlers import company, outreach, person, settings, start, tracking
from app.handlers.common import Services
from app.services.excel import ExcelService
from app.services.outreach import OutreachService

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
# Never let library debug logs dump request payloads (may include user data).
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("outreach-ai")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error while processing update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Something went wrong. Please try again."
            )
        except TelegramError:
            pass


def build_application(config: Config) -> Application:
    repository = Repository(config.database_path)
    services = Services(
        config=config,
        repository=repository,
        outreach=OutreachService(config, repository),
        excel=ExcelService(config, repository),
    )

    application = (
        ApplicationBuilder()
        .token(config.telegram_bot_token)
        .post_init(lambda app: repository.init())
        .build()
    )
    application.bot_data["services"] = services

    application.add_handler(CommandHandler("start", start.start))
    application.add_handler(CommandHandler("help", start.help_cmd))

    application.add_handler(CommandHandler("company", company.company_cmd))
    application.add_handler(CommandHandler("companies", company.companies_cmd))
    application.add_handler(CommandHandler("company_info", company.company_info_cmd))
    application.add_handler(CommandHandler("person", person.person_cmd))

    application.add_handler(CommandHandler("email", outreach.email_cmd))
    application.add_handler(CommandHandler("message", outreach.message_cmd))
    application.add_handler(CommandHandler("rewrite", outreach.rewrite_cmd))
    application.add_handler(CommandHandler("short", outreach.short_cmd))
    application.add_handler(CommandHandler("formal", outreach.formal_cmd))
    application.add_handler(CommandHandler("human", outreach.human_cmd))
    application.add_handler(CommandHandler("save", outreach.save_cmd))

    application.add_handler(CommandHandler("mark_sent", tracking.mark_sent_cmd))
    application.add_handler(CommandHandler("mark_replied", tracking.mark_replied_cmd))
    application.add_handler(CommandHandler("followups", tracking.followups_cmd))
    application.add_handler(CommandHandler("status", tracking.status_cmd))
    application.add_handler(CommandHandler("export", tracking.export_cmd))
    application.add_handler(CommandHandler("settings", settings.settings_cmd))

    application.add_handler(CallbackQueryHandler(outreach.on_button))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, outreach.on_text)
    )

    application.add_error_handler(on_error)
    return application


def main() -> None:
    config = Config.from_env()
    if not config.telegram_bot_token:
        sys.exit(
            "TELEGRAM_BOT_TOKEN is missing. Copy .env.example to .env, "
            "create a bot with @BotFather, and paste the token."
        )
    if not config.allowed_user_ids:
        logger.warning(
            "TELEGRAM_ALLOWED_USER_IDS is empty — the bot will refuse all "
            "users and tell them their ID so you can allowlist yourself."
        )
    application = build_application(config)
    logger.info("OutreachAI starting (model=%s)", config.ai_model if config.ai_enabled else "AI off")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
