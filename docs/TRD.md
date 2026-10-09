# Technical Requirements Document (TRD)

## 1. Architecture

```text
Telegram User
     |
     v
Telegram Bot
     |
     +--> Input Validation
     +--> Data Acquisition
     +--> Normalization
     +--> SQLite
     +--> AI Service
     +--> Outreach Generator
     +--> Excel Service
     +--> Analytics
```

## 2. Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Interface | Telegram Bot |
| Bot | python-telegram-bot |
| AI | OpenAI API |
| Database | SQLite |
| Async DB | aiosqlite |
| Excel | openpyxl |
| Configuration | python-dotenv |
| Validation | Pydantic |
| HTTP | httpx |
| Testing | pytest |

## 3. Project structure

```text
outreach-ai/
├── app/
│   ├── bot.py
│   ├── config.py
│   ├── handlers/
│   │   ├── start.py
│   │   ├── company.py
│   │   ├── person.py
│   │   ├── outreach.py
│   │   ├── tracking.py
│   │   └── settings.py
│   ├── services/
│   │   ├── linkedin.py
│   │   ├── enrichment.py
│   │   ├── ai.py
│   │   ├── outreach.py
│   │   ├── excel.py
│   │   └── analytics.py
│   ├── database/
│   │   ├── connection.py
│   │   ├── models.py
│   │   └── repository.py
│   ├── prompts/
│   │   ├── company_analysis.txt
│   │   ├── outreach_email.txt
│   │   ├── linkedin_message.txt
│   │   └── rewrite.txt
│   └── utils/
│       ├── validators.py
│       ├── formatting.py
│       └── dates.py
├── data/
├── tests/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 4. Environment variables

```env
TELEGRAM_BOT_TOKEN=
OPENAI_API_KEY=
DATABASE_PATH=data/outreach.db
EXCEL_PATH=data/Outreach_Tracker.xlsx
STUDENT_NAME=Daksh Khandagale
STUDENT_COLLEGE=Universal AI University, Karjat
STUDENT_ROLE=Student involved in student-industry engagement
LOG_LEVEL=INFO
```

## 5. Database

### companies

`id`, `name`, `linkedin_url`, `website`, `industry`, `description`, `location`, `size`, `products_services`, `ai_relevance`, `opportunity`, `personalization_angle`, `created_at`, `updated_at`

### contacts

`id`, `company_id`, `name`, `role`, `linkedin_url`, `email`, `notes`, `created_at`, `updated_at`

### outreach

`id`, `company_id`, `contact_id`, `channel`, `message`, `status`, `date_added`, `date_contacted`, `follow_up_date`, `response`, `notes`, `created_at`, `updated_at`

## 6. Data acquisition

Use user-provided LinkedIn information, permitted public information, authorized APIs, company websites, or supplied text. Do not depend on unauthorized LinkedIn scraping.

## 7. AI output

Required fields: `company_summary`, `why_relevant`, `opportunity`, `personalization_angle`, `email`, `linkedin_message`.

The AI must never invent company facts, people, products, partnerships, funding, technologies, or job openings.

## 8. Outreach workflow

```text
Input → Validate → Research → Normalize → Duplicate Check → AI Analysis → Personalize → Generate Drafts → User Review → Manual Send → Mark Sent → SQLite + Excel → Follow-up → Response → Outcome
```

## 9. Excel columns

`ID`, `Company`, `Contact Person`, `Role`, `LinkedIn`, `Email`, `Industry`, `Opportunity`, `Personalization Angle`, `Message`, `Channel`, `Status`, `Date Added`, `Date Contacted`, `Follow-up Date`, `Response`, `Notes`

## 10. Testing

Test URL validation, duplicate detection, database CRUD, Excel creation/update, AI response validation, Telegram commands, and follow-up calculations.

## 11. Deployment

Initial target: Windows + VS Code. Later: VPS, cloud container, or managed application platform. Back up SQLite and Excel regularly.
