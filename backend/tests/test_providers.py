"""Tests for Greenhouse and Lever provider parsing with fixture data."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.providers.greenhouse import GreenhouseProvider
from app.providers.lever import LeverProvider

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def gh_fixture():
    return json.loads((FIXTURES / "greenhouse_jobs.json").read_text())


@pytest.fixture
def lever_fixture():
    return json.loads((FIXTURES / "lever_jobs.json").read_text())


class MockResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data


class TestGreenhouseProvider:
    @pytest.mark.asyncio
    async def test_parse_jobs_from_fixture(self, gh_fixture):
        provider = GreenhouseProvider()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=MockResponse(gh_fixture))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.providers.greenhouse.httpx.AsyncClient", return_value=mock_client):
            cards = await provider.search(
                board_url="https://boards.greenhouse.io/testco",
                company="TestCo",
                track="Backend",
                posted_within="7d",
                limit=50,
            )

        assert len(cards) == 2

        # First job: fully populated
        c1 = cards[0]
        assert c1.company == "TestCo"
        assert c1.title == "Senior Backend Engineer"
        assert c1.location == "San Francisco, CA"
        assert c1.platform == "greenhouse"
        assert "testco/jobs/12345" in c1.source_url
        assert c1.apply_url is not None
        assert "#app" in c1.apply_url
        assert c1.apply_url_status == "direct"
        assert c1.posted_date is not None
        assert c1.posted_age_hours is not None
        assert c1.jd_raw_text is not None
        assert "Senior Backend Engineer" in c1.jd_raw_text
        assert len(c1.evidence) == 0  # No missing fields

        # Second job: missing apply_url, posted_date, jd_text
        c2 = cards[1]
        assert c2.title == "Frontend Developer"
        assert c2.apply_url is None
        assert c2.apply_url_status == "unknown"
        evidence_types = [e["type"] for e in c2.evidence]
        assert "apply_url_unknown" in evidence_types
        assert "jd_text_unavailable" in evidence_types
        assert "posted_date_unknown" in evidence_types

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        provider = GreenhouseProvider()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=MockResponse({}, status_code=404))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.providers.greenhouse.httpx.AsyncClient", return_value=mock_client):
            cards = await provider.search(
                board_url="https://boards.greenhouse.io/nonexist",
                company="NonExist",
                track="Backend",
                posted_within="7d",
                limit=50,
            )

        assert cards == []

    def test_extract_board_token(self):
        from app.providers.greenhouse import _extract_board_token

        assert _extract_board_token("https://boards.greenhouse.io/stripe") == "stripe"
        assert _extract_board_token("https://boards.greenhouse.io/stripe/") == "stripe"
        assert _extract_board_token("https://boards.greenhouse.io/Stripe") == "Stripe"


class TestLeverProvider:
    @pytest.mark.asyncio
    async def test_parse_jobs_from_fixture(self, lever_fixture):
        provider = LeverProvider()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=MockResponse(lever_fixture))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.providers.lever.httpx.AsyncClient", return_value=mock_client):
            cards = await provider.search(
                board_url="https://jobs.lever.co/testco",
                company="TestCo",
                track="Backend",
                posted_within="7d",
                limit=50,
            )

        assert len(cards) == 2

        # First job: fully populated
        c1 = cards[0]
        assert c1.company == "TestCo"
        assert c1.title == "Staff Platform Engineer"
        assert c1.location == "New York, NY"
        assert c1.platform == "lever"
        assert "testco/abc-123" in c1.source_url
        assert c1.apply_url is not None
        assert "apply" in c1.apply_url
        assert c1.apply_url_status == "direct"
        assert c1.posted_date is not None
        assert c1.posted_age_hours is not None
        assert c1.jd_raw_text is not None
        assert "platform team" in c1.jd_raw_text
        assert len(c1.evidence) == 0

        # Second job: missing fields
        c2 = cards[1]
        assert c2.title == "Data Analyst"
        assert c2.apply_url is None
        assert c2.apply_url_status == "unknown"
        evidence_types = [e["type"] for e in c2.evidence]
        assert "apply_url_unknown" in evidence_types
        assert "jd_text_unavailable" in evidence_types
        assert "posted_date_unknown" in evidence_types

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        provider = LeverProvider()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=MockResponse({}, status_code=500))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.providers.lever.httpx.AsyncClient", return_value=mock_client):
            cards = await provider.search(
                board_url="https://jobs.lever.co/nonexist",
                company="NonExist",
                track="Backend",
                posted_within="7d",
                limit=50,
            )

        assert cards == []
