"""Company research handlers."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.common import guard, get_services, reply
from app.utils.formatting import company_card, contact_card, esc, truncate

ASK_COMPANY = (
    "🔎 <b>Company research</b>\n\n"
    "Send one of:\n"
    "• LinkedIn company URL\n"
    "• Company website URL\n"
    "• Company name + any information you have\n\n"
    "Only information you provide or public website text is used — "
    "nothing is scraped from LinkedIn."
)

ASK_PERSON = (
    "👤 <b>Add a contact</b>\n\n"
    "Send the person's information, e.g.:\n"
    "<code>Name: Priya Sharma\nRole: HR Manager\n"
    "LinkedIn: https://linkedin.com/in/priya-sharma\n"
    "Email: priya@company.com</code>\n\n"
    "Lines can be in any order; URLs and emails are picked up automatically."
)


@guard
async def company_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["state"] = "awaiting_company"
    await reply(update, ASK_COMPANY)


async def process_company_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Validate → research → normalize → dedupe → AI analysis → save."""
    services = get_services(context)
    text = update.effective_message.text
    context.user_data["state"] = None

    busy = await update.effective_message.reply_text("Researching company…")
    try:
        result = await services.outreach.research_company(text)
    except ValueError as exc:
        await busy.edit_text(f"⚠️ {esc(str(exc))}")
        return
    except RuntimeError as exc:
        await busy.edit_text(f"⚠️ {esc(str(exc))}")
        return
    except Exception:
        await busy.edit_text(
            "⚠️ Research failed. Check the input and try again."
        )
        raise

    context.user_data["company_id"] = result.company_id
    context.user_data["brief"] = result.brief
    
    # Try to extract a contact person from the same message
    person = services.outreach.parse_person(text)
    has_contact = bool(person.email or person.linkedin_url or person.role or (person.name and person.name != "Unknown Contact"))
    
    if has_contact:
        contact_id, _ = await services.outreach.save_contact(result.company_id, person)
        context.user_data["contact_id"] = contact_id
    else:
        context.user_data.pop("contact_id", None)

    header = "✅ Saved new company" if result.is_new else "♻️ Existing company updated"
    
    contacts = await services.repository.list_contacts(result.company_id)
    contacts_text = ""
    if contacts:
        contacts_text = "\n\n<b>Contacts Found:</b>\n" + "\n\n".join(
            contact_card(c) for c in contacts
        )
        
    await busy.edit_text(
        truncate(f"{header}\n\n{company_card(result.company)}{contacts_text}", 4000),
        parse_mode="HTML",
    )
    from app.handlers.outreach import draft_buttons  # local import: no cycle at load

    await update.effective_message.reply_text(
        "What would you like to generate?",
        reply_markup=draft_buttons(),
    )


@guard
async def companies_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    services = get_services(context)
    companies = await services.repository.list_companies()
    if not companies:
        await reply(update, "No companies saved yet. Use /company to add one.")
        return
    lines = ["<b>📋 Saved companies</b>\n"]
    for c in companies[:60]:
        industry = f" — {c['industry']}" if c.get("industry") else ""
        lines.append(f"<b>#{c['id']}</b> {esc(c['name'])}{industry}")
    await reply(update, "\n".join(lines))


@guard
async def company_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show a company and make it the active one for drafting."""
    services = get_services(context)
    args = context.args or []
    company = None
    if args and args[0].isdigit():
        company = await services.repository.get_company(int(args[0]))
    elif args:
        company = await services.repository.find_company_by_name(" ".join(args))
    else:
        cid = context.user_data.get("company_id")
        if cid:
            company = await services.repository.get_company(cid)
    if not company:
        await reply(update, "Usage: /company_info <id | name> (see /companies)")
        return

    context.user_data["company_id"] = company["id"]
    context.user_data.pop("contact_id", None)
    
    contacts = await services.repository.list_contacts(company["id"])
    contacts_text = ""
    if contacts:
        contacts_text = "\n\n<b>Contacts:</b>\n" + "\n\n".join(
            contact_card(c) for c in contacts
        )
        
    await reply(update, truncate(f"{company_card(company)}{contacts_text}", 4000))
    await reply(update, "Selected for drafting. Use /email, /message or /person.")
