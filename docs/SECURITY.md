# Security and Compliance

## API keys

Store secrets only in `.env`. Never commit, print, or send API keys through Telegram.

## Telegram

Use a Telegram user allowlist:

```env
TELEGRAM_ALLOWED_USER_IDS=
```

## LinkedIn

Do not bypass access controls or perform unauthorized scraping. Use user-provided information, permitted public information, authorized APIs, company websites, or supplied text.

## AI

Send only information needed for the requested task. Never send passwords, API keys, or unnecessary private information.

## Outreach

Generate drafts rather than automatically sending messages. The user should review and manually send them.

## Database and Excel

Protect and back up `data/outreach.db` and `data/Outreach_Tracker.xlsx`. Do not expose the workbook publicly.

## Logging

Logs must not contain API keys, passwords, authentication tokens, or sensitive private information.

## Compliance

The system should support professional outreach while respecting platform rules, privacy, and applicable laws.
