# OutreachAI

AI-powered Telegram assistant for company research, personalized student-industry outreach, and outreach tracking.

## Purpose

OutreachAI helps Daksh Khandagale research companies/contacts, generate personalized outreach drafts, and track outreach progress in SQLite and Excel.

## Core flow

Find Company → Research → AI Understands Company → Personalize Message → Review → Send Manually → Mark Sent → Update Tracker → Follow-up → Response → Meeting/Opportunity → Analytics

## Important principle

The bot drafts and organizes outreach. The user remains responsible for reviewing and sending messages externally.

## Technology

- Python 3.11+
- Telegram Bot API
- OpenAI API
- SQLite
- openpyxl
- python-dotenv
- Pydantic
- httpx
- python-telegram-bot

## Setup

1. Create a Python virtual environment.
2. Install dependencies from `requirements.txt`.
3. Create a Telegram bot using BotFather.
4. Add credentials to `.env`.
5. Run `python -m app.bot`.

## Rules

- Do not use unauthorized LinkedIn scraping.
- Use user-provided text, permitted public information, or authorized APIs.
- Never log API keys.
- Never invent company facts.
- Review AI-generated messages before sending.
