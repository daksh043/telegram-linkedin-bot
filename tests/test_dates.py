"""Tests for date helpers."""

from app.utils.dates import add_days, fmt, today_iso


def test_add_days():
    assert add_days("2026-10-01", 7) == "2026-10-08"
    assert add_days("2026-10-31", 1) == "2026-11-01"
    assert add_days("2026-10-08", -8) == "2026-09-30"


def test_fmt():
    assert fmt("2026-10-08") == "08 Oct 2026"
    assert fmt(None) == ""
    assert fmt("") == ""
    assert fmt("not-a-date") == "not-a-date"


def test_today_iso():
    assert today_iso().count("-") == 2
