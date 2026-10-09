"""Outreach handlers: drafts, rewrites, save, inline buttons, text router."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.database.models import STATUS_DRAFTED
from app.handlers.common import guard, get_services, reply
from app.utils.formatting import esc, truncate

STYLES = {
    "short": "significantly shorter while keeping the key personalization and request",
    "formal": "more formal and professional",
    "human": "more natural, conversational, and human — less corporate",
}


def draft_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✉️ Email", callback_data="gen:email"),
            InlineKeyboardButton("💬 LinkedIn", callback_data="gen:linkedin"),
        ]
    ])


def action_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Shorter", callback_data="rw:short"),
            InlineKeyboardButton("Formal", callback_data="rw:formal"),
            InlineKeyboardButton("Human", callback_data="rw:human"),
        ],
        [
            InlineKeyboardButton("🔁 Rewrite", callback_data="rw:rewrite"),
            InlineKeyboardButton("💾 Save", callback_data="act:save"),
        ],
    ])


async def _generate(update: Update, context: ContextTypes.DEFAULT_TYPE, channel: str) -> None:
    services = get_services(context)
    company_id = context.user_data.get("company_id")
    if not company_id:
        await reply(update, "No company selected. Use /company first.")
        return
    company = await services.repository.get_company(company_id)
    if not company:
        await reply(update, "Company not found. Use /company again.")
        return
    contact = None
    contact_id = context.user_data.get("contact_id")
    if contact_id:
        contact = await services.repository.get_contact(contact_id)

    brief = context.user_data.get("brief") or _fallback_brief(company)
    status = await update.effective_message.reply_text(
        f"Drafting {channel} message..."
    )
    
    import time
    message_chunks = ""
    last_update = time.time()
    
    try:
        if channel == "Email":
            gen = services.outreach.draft_email_stream(company, contact, brief)
        else:
            gen = services.outreach.draft_linkedin_stream(company, contact, brief)
            
        async for chunk in gen:
            message_chunks += chunk
            now = time.time()
            if now - last_update >= 1.0:
                try:
                    await status.edit_text(f"Drafting {channel} message...\\n\\n<blockquote>{esc(message_chunks)}</blockquote>", parse_mode="HTML")
                    last_update = now
                except Exception:
                    pass
    except RuntimeError as exc:
        await status.edit_text(f"❌ {esc(str(exc))}")
        return

    context.user_data["draft"] = message_chunks
    context.user_data["draft_channel"] = channel
    try:
        await status.delete()
    except Exception:
        pass
    await reply(
        update,
        f"✅ <b>{esc(channel)} draft - {esc(company['name'])}</b>\\n\\n"
        f"<blockquote>{esc(message_chunks)}</blockquote>\\n\\n"
        "Review before sending. You send it manually outside this bot.",
        reply_markup=action_buttons(),
    )


def _fallback_brief(company: dict) -> str:
    parts = [f"Company: {company['name']}"]
    for key in ("industry", "description", "products_services", "ai_relevance",
                "opportunity", "personalization_angle", "location", "website"):
        if company.get(key):
            parts.append(f"{key.replace('_', ' ').title()}: {company[key]}")
    return "\n".join(parts)


async def _rewrite(update: Update, context: ContextTypes.DEFAULT_TYPE, style_key: str, instruction: str = "") -> None:
    services = get_services(context)
    draft = context.user_data.get("draft")
    if not draft:
        await reply(update, "No draft yet. Use /email or /message first.")
        return
    style = instruction or STYLES.get(style_key, "improved")
    status = await update.effective_message.reply_text("Rewriting...")
    
    import time
    message_chunks = ""
    last_update = time.time()
    
    try:
        async for chunk in services.outreach.rewrite_stream(draft, style):
            message_chunks += chunk
            now = time.time()
            if now - last_update >= 1.0:
                try:
                    await status.edit_text(f"Rewriting...\\n\\n<blockquote>{esc(message_chunks)}</blockquote>", parse_mode="HTML")
                    last_update = now
                except Exception:
                    pass
    except RuntimeError as exc:
        await status.edit_text(f"❌ {esc(str(exc))}")
        return
        
    context.user_data["draft"] = message_chunks
    try:
        await status.delete()
    except Exception:
        pass
    await reply(
        update,
        f"📝 <b>Updated {esc(context.user_data.get('draft_channel', ''))} draft</b>\\n\\n"
        f"<blockquote>{esc(message_chunks)}</blockquote>",
        reply_markup=action_buttons(),
    )


async def _save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    services = get_services(context)
    draft = context.user_data.get("draft")
    if not draft:
        await reply(update, "No draft to save. Use /email or /message first.")
        return
    company_id = context.user_data.get("company_id")
    if not company_id:
        await reply(update, "No company selected. Use /company first.")
        return
    outreach_id = await services.repository.add_outreach(
        company_id=company_id,
        contact_id=context.user_data.get("contact_id"),
        channel=context.user_data.get("draft_channel", "Email"),
        message=draft,
        status=STATUS_DRAFTED,
    )
    context.user_data["last_outreach_id"] = outreach_id
    await reply(
        update,
        f"💾 Saved as outreach <b>#{outreach_id}</b> (Drafted).\n"
        f"After you send it manually, use /mark_sent {outreach_id}.",
    )


# ---------------------------------------------------------------------------
# command entries
# ---------------------------------------------------------------------------

@guard
async def email_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _generate(update, context, "Email")


@guard
async def message_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _generate(update, context, "LinkedIn")


@guard
async def rewrite_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    instruction = " ".join(context.args).strip() if context.args else ""
    await _rewrite(update, context, "rewrite", instruction or "clearer and more engaging")


@guard
async def short_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _rewrite(update, context, "short")


@guard
async def formal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _rewrite(update, context, "formal")


@guard
async def human_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _rewrite(update, context, "human")


@guard
async def save_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _save(update, context)


@guard
async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data == "gen:email":
        await _generate(update, context, "Email")
    elif data == "gen:linkedin":
        await _generate(update, context, "LinkedIn")
    elif data.startswith("rw:"):
        await _rewrite(update, context, data.split(":", 1)[1])
    elif data == "act:save":
        await _save(update, context)
    elif data.startswith("act:mark_sent"):
        from app.handlers.tracking import mark_sent_by_id

        oid = int(data.split(":", 2)[2])
        await mark_sent_by_id(update, context, oid)


@guard
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route free-text input based on the conversation state."""
    from app.handlers.company import process_company_input
    from app.handlers.person import process_person_input

    state = context.user_data.get("state")
    if state == "awaiting_company":
        await process_company_input(update, context)
    elif state == "awaiting_person":
        await process_person_input(update, context)
    else:
        await reply(
            update,
            truncate(
                "Send a command — /company to research a company, /person to "
                "add a contact, /help for everything else.",
                4000,
            ),
        )
