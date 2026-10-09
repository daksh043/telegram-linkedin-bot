"""Tests for AI response parsing, enrichment, LinkedIn parsing, outreach service."""

import asyncio
from types import SimpleNamespace

import pytest
from openai import InternalServerError, RateLimitError

from app.config import Config
from app.database.repository import Repository
from app.services import enrichment, linkedin
from app.services import ai as ai_module
from app.services.ai import AIService, parse_company_analysis
from app.services.outreach import OutreachService


class TestCompanyAnalysisParsing:
    def test_clean_json(self):
        analysis = parse_company_analysis(
            '{"company_summary": "AI startup", "industry": "Fintech", '
            '"unknown_fields": ["location"]}'
        )
        assert analysis.company_summary == "AI startup"
        assert analysis.industry == "Fintech"
        assert analysis.unknown_fields == ["location"]

    def test_json_in_code_fence(self):
        raw = '```json\n{"company_summary": "OK"}\n```'
        assert parse_company_analysis(raw).company_summary == "OK"

    def test_json_with_prose(self):
        raw = 'Here is the analysis:\n{"industry": "Health"}\nHope that helps.'
        assert parse_company_analysis(raw).industry == "Health"

    def test_missing_optional_fields_default(self):
        analysis = parse_company_analysis('{"company_summary": "x"}')
        assert analysis.products_services == ""
        assert analysis.unknown_fields == []

    def test_no_json_raises(self):
        with pytest.raises(ValueError):
            parse_company_analysis("Sorry, I cannot help with that.")


class TestEnrichment:
    def test_html_to_text(self):
        html = (
            "<html><head><style>body{}</style></head>"
            "<body><script>evil()</script><h1>Acme</h1><p>Builds robots.</p></body></html>"
        )
        text = enrichment.html_to_text(html)
        assert "Acme" in text and "robots" in text
        assert "evil" not in text and "body{}" not in text

    def test_fetch_invalid_url_returns_empty(self):
        assert asyncio.run(enrichment.fetch_website_text("")) == ""

    def test_build_research_brief(self):
        brief = enrichment.build_research_brief(
            user_text="Acme builds robots",
            linkedin_url="https://linkedin.com/company/acme",
            website_url="https://acme.com",
            website_text="Acme robotics homepage",
        )
        assert "linkedin.com/company/acme" in brief
        assert "Acme robotics homepage" in brief
        assert "Acme builds robots" in brief


class TestLinkedInParse:
    def test_company(self):
        result = linkedin.parse("see https://linkedin.com/company/acme-corp/")
        assert result.kind == "company"
        assert result.slug == "acme-corp"
        assert result.display_name == "Acme Corp"

    def test_person(self):
        result = linkedin.parse("https://linkedin.com/in/priya-sharma")
        assert result.kind == "person"
        assert result.display_name == "Priya Sharma"

    def test_none(self):
        assert linkedin.parse("hello world").kind == ""


def make_service(tmp_path, ai_enabled=False) -> OutreachService:
    config = Config(
        telegram_bot_token="x",
        ai_api_key="sk-test" if ai_enabled else "",
        ai_model="gemini-3.8-flash",
        ai_base_url=None,
        database_path=str(tmp_path / "t.db"),
        excel_path=str(tmp_path / "t.xlsx"),
        student_name="Daksh Khandagale",
        student_college="Universal AI University",
        student_role="Student",
        default_followup_days=7,
        log_level="INFO",
    )
    repo = Repository(config.database_path)
    asyncio.run(repo.init())
    return OutreachService(config, repo)


class TestPersonParsing:
    def test_structured_lines(self, tmp_path):
        service = make_service(tmp_path)
        person = service.parse_person(
            "Name: Priya Sharma\n"
            "Role: HR Manager\n"
            "LinkedIn: https://linkedin.com/in/priya-sharma\n"
            "Email: priya@acme.com"
        )
        assert person.name == "Priya Sharma"
        assert person.role == "HR Manager"
        assert person.linkedin_url.endswith("/priya-sharma")
        assert person.email == "priya@acme.com"

    def test_free_text(self, tmp_path):
        service = make_service(tmp_path)
        person = service.parse_person(
            "Priya Sharma\nHR Manager at Acme\nhttps://linkedin.com/in/priya"
        )
        assert person.name == "Priya Sharma"
        assert person.linkedin_url == "https://linkedin.com/in/priya"

    def test_save_contact_dedupes(self, tmp_path):
        service = make_service(tmp_path)
        cid = asyncio.run(service.repository.add_company(name="Acme"))
        person = service.parse_person("Name: Priya Sharma\nRole: HR")
        first, is_new = asyncio.run(service.save_contact(cid, person))
        second, is_new2 = asyncio.run(service.save_contact(cid, person))
        assert is_new and not is_new2
        assert first == second


class TestCompanyResearchNoAI:
    def test_saves_company_with_website(self, tmp_path, monkeypatch):
        service = make_service(tmp_path)
        # No network in tests: website fetch returns nothing.
        async def fake_fetch(url):
            return ""
        monkeypatch.setattr(enrichment, "fetch_website_text", fake_fetch)

        result = asyncio.run(
            service.research_company(
                "https://linkedin.com/company/infoloom-labs plus https://infoloom.io"
            )
        )
        assert result.is_new
        assert result.company["name"] == "Infoloom Labs"
        assert result.company["linkedin_url"].endswith("/company/infoloom-labs")
        assert result.company["website"] == "https://infoloom.io"

    def test_duplicate_company_updated_not_duplicated(self, tmp_path, monkeypatch):
        service = make_service(tmp_path)
        monkeypatch.setattr(
            enrichment, "fetch_website_text", lambda url: _noop()
        )
        first = asyncio.run(
            service.research_company("https://linkedin.com/company/infoloom-labs")
        )
        second = asyncio.run(
            service.research_company("Infoloom Labs — AI data company")
        )
        assert first.company_id == second.company_id
        assert not second.is_new
        companies = asyncio.run(service.repository.list_companies())
        assert len(companies) == 1

    def test_ai_disabled_still_saves_minimal_record(self, tmp_path, monkeypatch):
        service = make_service(tmp_path)
        monkeypatch.setattr(enrichment, "fetch_website_text", lambda url: _noop())
        result = asyncio.run(service.research_company("Globex Corporation"))
        assert result.is_new
        assert result.company["name"] == "Globex Corporation"


async def _noop():
    return ""


class _FakeCompletions:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    async def create(self, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class _FakeClient:
    def __init__(self, outcomes):
        self.chat = SimpleNamespace(completions=_FakeCompletions(outcomes))


def _ok_response(text="draft text"):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))]
    )


def _api_error(cls, message, status):
    import httpx
    response = httpx.Response(
        status_code=status, headers={},
        request=httpx.Request("POST", "https://example.com/v1/chat/completions"),
    )
    return cls(message, response=response, body=None)


@pytest.fixture
def fast_sleep(monkeypatch):
    async def _instant(_seconds):
        return None
    monkeypatch.setattr(ai_module.asyncio, "sleep", _instant)


class TestRetry:
    def test_retries_transient_errors_then_succeeds(self, tmp_path, monkeypatch, fast_sleep):
        service = make_service(tmp_path, ai_enabled=True)
        fake = _FakeClient([
            _api_error(InternalServerError, "503 high demand", 503),
            _api_error(RateLimitError, "429", 429),
            _ok_response("the draft"),
        ])
        monkeypatch.setattr(service.ai, "_get_client", lambda: fake)
        result = asyncio.run(service.ai._complete("sys", "user"))
        assert result == "the draft"
        assert fake.chat.completions.calls == 3

    def test_raises_friendly_error_after_exhaustion(self, tmp_path, monkeypatch, fast_sleep):
        service = make_service(tmp_path, ai_enabled=True)
        fake = _FakeClient([
            _api_error(InternalServerError, "503", 503),
            _api_error(InternalServerError, "503", 503),
            _api_error(InternalServerError, "503", 503),
        ])
        monkeypatch.setattr(service.ai, "_get_client", lambda: fake)
        with pytest.raises(RuntimeError, match="busy"):
            asyncio.run(service.ai._complete("sys", "user"))
        assert fake.chat.completions.calls == 3

    def test_non_retryable_error_fails_fast(self, tmp_path, monkeypatch):
        from openai import BadRequestError
        service = make_service(tmp_path, ai_enabled=True)
        fake = _FakeClient([_api_error(BadRequestError, "400 bad", 400)])
        monkeypatch.setattr(service.ai, "_get_client", lambda: fake)
        with pytest.raises(BadRequestError):
            asyncio.run(service.ai._complete("sys", "user"))
        assert fake.chat.completions.calls == 1
