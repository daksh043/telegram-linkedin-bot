# Product Requirements Document (PRD)

## Product

**OutreachAI — AI-Powered Company Research & Student Outreach Assistant**

## 1. Overview

OutreachAI is a Telegram-based assistant that helps students research companies, identify relevant contacts, create personalized outreach, and track outreach progress.

## 2. Problem

Students manually research companies, find contacts, write messages, track responses, and remember follow-ups. This is repetitive and difficult to manage at scale.

## 3. Goal

Create one Telegram workflow that reduces repetitive research and writing while keeping the student in control of actual outreach.

## 4. Target user

A student involved in student-industry engagement who is exploring internships, live projects, mentorships, workshops, company visits, industry collaborations, and campus hiring.

## 5. Core journey

1. User sends company/person information.
2. Bot validates the input.
3. Bot identifies company/person.
4. Bot gathers permitted information.
5. Bot normalizes the data.
6. Bot checks duplicates.
7. AI analyzes the information.
8. AI identifies opportunity areas.
9. AI creates personalized email and LinkedIn drafts.
10. User reviews.
11. User manually sends the message.
12. User marks it as sent.
13. SQLite and Excel are updated.
14. Follow-up is recorded.
15. Response/outcome is tracked.

## 6. Functional requirements

### Telegram

`/start`, `/help`, `/company`, `/person`, `/companies`, `/company_info`, `/email`, `/message`, `/rewrite`, `/short`, `/formal`, `/human`, `/mark_sent`, `/mark_replied`, `/followups`, `/status`, `/export`

### Company research

Output: company name, industry, description, products/services, location, website, AI/technology relevance, potential student opportunities, and personalization angle.

### Contact research

Output: name, job title, company, LinkedIn, relevant professional context, and outreach angle.

### Outreach

Generate email, LinkedIn message, short version, formal version, human version, and rewrites.

### Tracking

Track company, contact, role, LinkedIn, email, industry, opportunity, personalization angle, message, channel, status, dates, response, and notes.

## 7. Status values

- Not Contacted
- Drafted
- Sent
- Replied
- Interested
- Follow-up
- Meeting Scheduled
- Not Interested
- Closed

## 8. Excel

Workbook sheets: Outreach Tracker, Contacts, Dashboard, Settings.

## 9. Analytics

Track total companies, total contacts, drafted, sent, replies, interested, meetings, follow-ups, response rate, and interest rate.

## 10. Security

Secrets are stored in `.env`; Telegram access is restricted; API keys are never logged; unauthorized LinkedIn scraping is prohibited; users review drafts before sending.

## 11. Future features

Automated reminders, Gmail/calendar integrations, CRM integrations, company scoring, contact prioritization, reply classification, and a web dashboard.
