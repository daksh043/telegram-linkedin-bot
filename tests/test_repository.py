"""Tests for the SQLite repository: CRUD, duplicates, follow-ups."""

import asyncio
from datetime import date, timedelta

import pytest

from app.database.models import (
    STATUS_DRAFTED,
    STATUS_FOLLOWUP,
    STATUS_INTERESTED,
    STATUS_REPLIED,
    STATUS_SENT,
)
from app.database.repository import Repository, normalize_name


@pytest.fixture
def repo(tmp_path):
    repository = Repository(str(tmp_path / "test.db"))
    asyncio.run(repository.init())
    return repository


def test_normalize_name_strips_suffixes():
    assert normalize_name("Acme Technologies Pvt. Ltd.") == "acme"
    assert normalize_name("Acme Pvt Ltd") == normalize_name("ACME Ltd.")


def test_company_crud_and_duplicates(repo):
    cid = asyncio.run(
        repo.add_company(name="Acme Pvt Ltd", industry="AI", location="Mumbai")
    )
    fetched = asyncio.run(repo.get_company(cid))
    assert fetched["name"] == "Acme Pvt Ltd"
    assert fetched["industry"] == "AI"

    # Duplicate detection across legal suffixes and casing.
    duplicate = asyncio.run(repo.find_company_by_name("ACME LTD."))
    assert duplicate is not None and duplicate["id"] == cid

    distinct = asyncio.run(repo.find_company_by_name("Globex"))
    assert distinct is None

    asyncio.run(repo.update_company(cid, industry="Robotics"))
    fetched = asyncio.run(repo.get_company(cid))
    assert fetched["industry"] == "Robotics"


def test_contact_crud_and_duplicates(repo):
    cid = asyncio.run(repo.add_company(name="Acme"))
    contact_id = asyncio.run(
        repo.add_contact(cid, name="Priya Sharma", role="HR Manager")
    )
    existing = asyncio.run(repo.find_contact(cid, "priya sharma"))
    assert existing is not None and existing["id"] == contact_id
    other = asyncio.run(repo.find_contact(cid, "Someone Else"))
    assert other is None
    contacts = asyncio.run(repo.list_contacts(cid))
    assert len(contacts) == 1


def test_outreach_lifecycle(repo):
    cid = asyncio.run(repo.add_company(name="Acme"))
    contact_id = asyncio.run(repo.add_contact(cid, name="Priya Sharma"))
    oid = asyncio.run(
        repo.add_outreach(
            company_id=cid,
            contact_id=contact_id,
            channel="Email",
            message="Hello...",
            status=STATUS_DRAFTED,
        )
    )
    record = asyncio.run(repo.get_outreach(oid))
    assert record["status"] == STATUS_DRAFTED
    assert record["date_added"] == date.today().isoformat()

    record = asyncio.run(
        repo.update_outreach(
            oid, status=STATUS_SENT, date_contacted="2026-10-01",
            follow_up_date="2026-10-08",
        )
    )
    assert record["status"] == STATUS_SENT

    # Not due before the follow-up date.
    due = asyncio.run(repo.due_followups(on_date=date(2026, 10, 7)))
    assert due == []
    # Due on the follow-up date and after.
    due = asyncio.run(repo.due_followups(on_date=date(2026, 10, 8)))
    assert [d["id"] for d in due] == [oid]

    asyncio.run(repo.update_outreach(oid, status=STATUS_FOLLOWUP,
                                     follow_up_date="2026-10-15"))
    assert asyncio.run(repo.due_followups(on_date=date(2026, 10, 14))) == []
    assert len(asyncio.run(repo.due_followups(on_date=date(2026, 10, 15)))) == 1


def test_status_counts_and_totals(repo):
    cid = asyncio.run(repo.add_company(name="Acme"))
    for status in (STATUS_DRAFTED, STATUS_SENT, STATUS_SENT, STATUS_REPLIED,
                   STATUS_INTERESTED):
        asyncio.run(
            repo.add_outreach(cid, None, "Email", "msg", status)
        )
    counts = asyncio.run(repo.status_counts())
    assert counts[STATUS_SENT] == 2
    assert counts[STATUS_REPLIED] == 1
    totals = asyncio.run(repo.totals())
    assert totals["total_companies"] == 1
    assert totals["total_contacts"] == 0


def test_due_followups_boundary(repo):
    """A follow-up scheduled for tomorrow is not due today."""
    cid = asyncio.run(repo.add_company(name="Acme"))
    oid = asyncio.run(repo.add_outreach(cid, None, "Email", "m", STATUS_SENT))
    asyncio.run(
        repo.update_outreach(
            oid,
            date_contacted=date.today().isoformat(),
            follow_up_date=(date.today() + timedelta(days=1)).isoformat(),
        )
    )
    assert asyncio.run(repo.due_followups()) == []
