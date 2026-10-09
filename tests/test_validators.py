"""Tests for input validation and extraction."""

from app.utils import validators


class TestUserInput:
    def test_empty_input_rejected(self):
        ok, error = validators.validate_user_input("   ")
        assert not ok
        assert error

    def test_none_rejected(self):
        ok, _ = validators.validate_user_input("")
        assert not ok

    def test_normal_input_accepted(self):
        ok, error = validators.validate_user_input("https://linkedin.com/company/acme")
        assert ok and error == ""

    def test_too_long_rejected(self):
        ok, _ = validators.validate_user_input("x" * (validators.MAX_INPUT_LENGTH + 1))
        assert not ok


class TestUrls:
    def test_is_http_url(self):
        assert validators.is_http_url("https://acme.com")
        assert validators.is_http_url("http://acme.io/about")
        assert not validators.is_http_url("acme.com")
        assert not validators.is_http_url("not a url")

    def test_linkedin_company_url(self):
        text = "Check https://www.linkedin.com/company/acme-corp/about/"
        assert validators.extract_linkedin_company_slug(text) == "acme-corp"
        assert (
            validators.extract_linkedin_company_url(text)
            == "https://www.linkedin.com/company/acme-corp"
        )

    def test_linkedin_person_url(self):
        text = "https://in.linkedin.com/in/priya-sharma-123"
        assert validators.extract_linkedin_person_url(text).startswith(
            "https://in.linkedin.com/in/priya-sharma-123"
        )

    def test_website_url_excludes_linkedin(self):
        text = "https://linkedin.com/company/acme and https://acme.com"
        assert validators.extract_website_url(text) == "https://acme.com"

    def test_website_url_none(self):
        assert validators.extract_website_url("no urls here") == ""


class TestEmail:
    def test_extract(self):
        text = "Contact: priya.sharma@acme.co.in, thanks"
        assert validators.extract_email(text) == "priya.sharma@acme.co.in"

    def test_missing(self):
        assert validators.extract_email("no email") == ""
