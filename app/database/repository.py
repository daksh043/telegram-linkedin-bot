"""CRUD repository over SQLite with duplicate detection."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Optional

from app.database import connection as db
from app.database.models import (
    STATUS_FOLLOWUP,
    STATUS_SENT,
)
from app.utils.dates import today_iso

_LEGAL_SUFFIXES = (
    "private",
    "pvt",
    "ltd",
    "limited",
    "llp",
    "inc",
    "llc",
    "co",
    "corp",
    "corporation",
    "technologies",
    "technology",
    "solutions",
    "labs",
    "software",
)

_TS = datetime.now().isoformat(timespec="seconds")


def normalize_name(name: str) -> str:
    """Normalize a company/person name for duplicate detection."""
    lowered = name.lower().strip()
    lowered = re.sub(r"[^\w\s]", " ", lowered)
    words = [w for w in lowered.split() if w not in _LEGAL_SUFFIXES]
    return " ".join(words) if words else lowered


class Repository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    async def init(self) -> None:
        await db.init_schema(self.db_path)

    # ------------------------------------------------------------------
    # companies
    # ------------------------------------------------------------------

    async def add_company(self, **fields: Any) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        cols = list(fields.keys())
        sql = (
            f"INSERT INTO companies (name, created_at, updated_at, "
            f"{', '.join(cols)}) VALUES (?, ?, ?, "
            f"{', '.join('?' for _ in cols)})"
        )
        params = [fields.get("name", "Unknown"), now, now] + [
            fields[c] for c in cols
        ]
        conn = await db.connect(self.db_path)
        try:
            cur = await conn.execute(sql, params)
            await conn.commit()
            return int(cur.lastrowid)
        finally:
            await conn.close()

    async def update_company(self, company_id: int, **fields: Any) -> None:
        if not fields:
            return
        now = datetime.now().isoformat(timespec="seconds")
        sets = ", ".join(f"{c} = ?" for c in fields)
        sql = f"UPDATE companies SET {sets}, updated_at = ? WHERE id = ?"
        conn = await db.connect(self.db_path)
        try:
            await conn.execute(sql, [*fields.values(), now, company_id])
            await conn.commit()
        finally:
            await conn.close()

    async def get_company(self, company_id: int) -> Optional[dict]:
        conn = await db.connect(self.db_path)
        try:
            cur = await conn.execute(
                "SELECT * FROM companies WHERE id = ?", (company_id,)
            )
            row = await cur.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()

    async def find_company_by_name(self, name: str) -> Optional[dict]:
        conn = await db.connect(self.db_path)
        try:
            cur = await conn.execute(
                "SELECT * FROM companies WHERE LOWER(TRIM(name)) = ?",
                (name.strip().lower(),),
            )
            row = await cur.fetchone()
            if row:
                return dict(row)
            cur = await conn.execute("SELECT * FROM companies")
            rows = await cur.fetchall()
            target = normalize_name(name)
            for r in rows:
                if normalize_name(r["name"]) == target:
                    return dict(r)
            return None
        finally:
            await conn.close()

    async def list_companies(self) -> list[dict]:
        conn = await db.connect(self.db_path)
        try:
            cur = await conn.execute(
                "SELECT * FROM companies ORDER BY created_at DESC"
            )
            return [dict(r) for r in await cur.fetchall()]
        finally:
            await conn.close()

    # ------------------------------------------------------------------
    # contacts
    # ------------------------------------------------------------------

    async def add_contact(self, company_id: int, **fields: Any) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        conn = await db.connect(self.db_path)
        try:
            cur = await conn.execute(
                "INSERT INTO contacts (company_id, name, role, linkedin_url,"
                " email, notes, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    company_id,
                    fields.get("name", "Unknown"),
                    fields.get("role", ""),
                    fields.get("linkedin_url", ""),
                    fields.get("email", ""),
                    fields.get("notes", ""),
                    now,
                    now,
                ),
            )
            await conn.commit()
            return int(cur.lastrowid)
        finally:
            await conn.close()

    async def find_contact(
        self, company_id: int, name: str
    ) -> Optional[dict]:
        conn = await db.connect(self.db_path)
        try:
            cur = await conn.execute(
                "SELECT * FROM contacts WHERE company_id = ?", (company_id,)
            )
            rows = await cur.fetchall()
            target = normalize_name(name)
            for r in rows:
                if normalize_name(r["name"]) == target:
                    return dict(r)
            return None
        finally:
            await conn.close()

    async def get_contact(self, contact_id: int) -> Optional[dict]:
        conn = await db.connect(self.db_path)
        try:
            cur = await conn.execute(
                "SELECT * FROM contacts WHERE id = ?", (contact_id,)
            )
            row = await cur.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()

    async def list_contacts(self, company_id: Optional[int] = None) -> list[dict]:
        conn = await db.connect(self.db_path)
        try:
            if company_id is None:
                cur = await conn.execute(
                    "SELECT * FROM contacts ORDER BY created_at DESC"
                )
            else:
                cur = await conn.execute(
                    "SELECT * FROM contacts WHERE company_id = ?"
                    " ORDER BY created_at DESC",
                    (company_id,),
                )
            return [dict(r) for r in await cur.fetchall()]
        finally:
            await conn.close()

    # ------------------------------------------------------------------
    # outreach
    # ------------------------------------------------------------------

    async def add_outreach(
        self,
        company_id: int,
        contact_id: Optional[int],
        channel: str,
        message: str,
        status: str,
        notes: str = "",
    ) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        conn = await db.connect(self.db_path)
        try:
            cur = await conn.execute(
                "INSERT INTO outreach (company_id, contact_id, channel,"
                " message, status, date_added, notes, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    company_id,
                    contact_id,
                    channel,
                    message,
                    status,
                    today_iso(),
                    notes,
                    now,
                    now,
                ),
            )
            await conn.commit()
            return int(cur.lastrowid)
        finally:
            await conn.close()

    async def get_outreach(self, outreach_id: int) -> Optional[dict]:
        conn = await db.connect(self.db_path)
        try:
            cur = await conn.execute(
                "SELECT * FROM outreach WHERE id = ?", (outreach_id,)
            )
            row = await cur.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()

    async def update_outreach(
        self, outreach_id: int, **fields: Any
    ) -> Optional[dict]:
        if not fields:
            return await self.get_outreach(outreach_id)
        now = datetime.now().isoformat(timespec="seconds")
        sets = ", ".join(f"{c} = ?" for c in fields)
        sql = f"UPDATE outreach SET {sets}, updated_at = ? WHERE id = ?"
        conn = await db.connect(self.db_path)
        try:
            await conn.execute(sql, [*fields.values(), now, outreach_id])
            await conn.commit()
        finally:
            await conn.close()
        return await self.get_outreach(outreach_id)

    async def list_outreach(self) -> list[dict]:
        conn = await db.connect(self.db_path)
        try:
            cur = await conn.execute(
                "SELECT * FROM outreach ORDER BY id DESC"
            )
            return [dict(r) for r in await cur.fetchall()]
        finally:
            await conn.close()

    async def due_followups(self, on_date: Optional[date] = None) -> list[dict]:
        day = (on_date or date.today()).isoformat()
        conn = await db.connect(self.db_path)
        try:
            cur = await conn.execute(
                "SELECT * FROM outreach WHERE status IN (?, ?)"
                " AND follow_up_date IS NOT NULL AND follow_up_date <= ?"
                " ORDER BY follow_up_date ASC",
                (STATUS_SENT, STATUS_FOLLOWUP, day),
            )
            return [dict(r) for r in await cur.fetchall()]
        finally:
            await conn.close()

    # ------------------------------------------------------------------
    # analytics
    # ------------------------------------------------------------------

    async def status_counts(self) -> dict[str, int]:
        conn = await db.connect(self.db_path)
        try:
            cur = await conn.execute(
                "SELECT status, COUNT(*) AS n FROM outreach GROUP BY status"
            )
            return {row["status"]: int(row["n"]) for row in await cur.fetchall()}
        finally:
            await conn.close()

    async def totals(self) -> dict[str, int]:
        conn = await db.connect(self.db_path)
        try:
            out: dict[str, int] = {}
            for table in ("companies", "contacts"):
                cur = await conn.execute(f"SELECT COUNT(*) AS n FROM {table}")
                row = await cur.fetchone()
                out[f"total_{table}"] = int(row["n"])
            return out
        finally:
            await conn.close()
