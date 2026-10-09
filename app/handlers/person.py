"""Contact (person) handlers."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.common import guard, get_services, reply
from app.handlers.company import ASK_PERSON
from app.utils.formatting import contact_card, esc


@guard
async def person_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["state"] = "awaiting_person"
    await reply(update, ASK_PERSON)


async def process_person_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    services = get_services(context)
    text = update.effective_message.text
    context.user_data["state"] = None

    try:
        person = services.outreach.parse_person(text)
    except ValueError as exc:
        await reply(update, f"⚠️ {esc(str(exc))}")
        return

    # Attach to the active company, or resolve from the pasted company name.
    company_id = context.user_data.get("company_id")
    company = None
    if company_id:
        company = await services.repository.get_company(company_id)
    if company is None and person.company_name:
        company = await services.repository.find_company_by_name(person.company_name)
        if company is None:
            company_id = await services.repository.add_company(
                name=person.company_name,
            )
            company = await services.repository.get_company(company_id)
    if company is None:
        context.user_data["state"] = "awaiting_person"
        await reply(
            update,
            "⚠️ No active company. First send the company name (one line), "
            "or use /company before /person.",
        )
        return

    contact_id, is_new = await services.outreach.save_contact(company["id"], person)
    contact = await services.repository.get_contact(contact_id)

    context.user_data["company_id"] = company["id"]
    context.user_data["contact_id"] = contact_id

    header = "✅ Saved new contact" if is_new else "♻️ Existing contact"
    await reply(update, f"{header}\n\n{contact_card(contact, company['name'])}")
    await reply(update, "Ready to draft. Use /email or /message.")
