"""SQLite connection helpers (aiosqlite)."""

from __future__ import annotations

import os
from pathlib import Path

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    linkedin_url TEXT,
    website TEXT,
    industry TEXT,
    description TEXT,
    location TEXT,
    size TEXT,
    products_services TEXT,
    ai_relevance TEXT,
    opportunity TEXT,
    personalization_angle TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    name TEXT NOT NULL,
    role TEXT,
    linkedin_url TEXT,
    email TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outreach (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    contact_id INTEGER REFERENCES contacts(id),
    channel TEXT NOT NULL,
    message TEXT,
    status TEXT NOT NULL,
    date_added TEXT NOT NULL,
    date_contacted TEXT,
    follow_up_date TEXT,
    response TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_outreach_company ON outreach(company_id);
CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach(status);
"""


async def connect(db_path: str) -> aiosqlite.Connection:
    """Open a connection with dict-like row access and foreign keys on."""
    os.makedirs(Path(db_path).parent, exist_ok=True)
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    return conn


async def init_schema(db_path: str) -> None:
    conn = await connect(db_path)
    try:
        await conn.executescript(SCHEMA)
        await conn.commit()
    finally:
        await conn.close()
