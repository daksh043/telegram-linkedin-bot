# Implementation Plan

Build OutreachAI in small phases.

## Phase 1 — Telegram foundation

Create the Python project, virtual environment, dependencies, `.env`, Telegram bot, `/start`, and `/help`.

Success: `/start` receives a response.

## Phase 2 — Database

Create SQLite connection, companies, contacts, outreach tables, CRUD repository, and duplicate detection.

Success: records can be saved and retrieved.

## Phase 3 — Excel

Use openpyxl to create tracker, contacts, dashboard, settings, and export/update logic.

Success: saved outreach appears correctly in Excel.

## Phase 4 — AI

Connect OpenAI API, create prompts, validate structured responses, add company analysis, email generation, LinkedIn generation, and rewrite modes.

Success: verified information produces a personalized draft without invented facts.

## Phase 5 — Research

Add URL validation, company/person identification, user-pasted information, permitted enrichment, and normalization.

## Phase 6 — Outreach management

Add saving drafts, review, mark sent, mark replied, follow-up dates, notes, and follow-up list.

## Phase 7 — Analytics

Add response rate, interest rate, meetings, follow-ups, and dashboard.

## Phase 8 — Deployment

Secure environment variables, restrict Telegram access, configure backups, deploy, and monitor errors.

## Recommended order

```text
Telegram → SQLite → Excel → AI → Research → Outreach tracking → Analytics → Deployment
```
