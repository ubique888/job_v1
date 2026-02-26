"""Tests for deduplication and normalization."""

from app.dedupe import compute_pk_hash, normalize_text


class TestNormalize:
    def test_lowercase_and_whitespace(self):
        assert normalize_text("  Senior  Backend  Engineer  ") == "senior backend engineer"

    def test_strips_punctuation(self):
        assert normalize_text("Sr. Engineer, Backend (Remote)") == "senior engineer backend remote"

    def test_abbreviation_mapping(self):
        assert normalize_text("NYC") == "new york city"
        assert normalize_text("SF") == "san francisco"
        assert normalize_text("Sr Eng") == "senior engineer"

    def test_empty_input(self):
        assert normalize_text("") == ""
        assert normalize_text(None) == ""


class TestPkHash:
    def test_same_input_same_hash(self):
        h1 = compute_pk_hash("Stripe", "Backend Engineer", "San Francisco")
        h2 = compute_pk_hash("Stripe", "Backend Engineer", "San Francisco")
        assert h1 == h2

    def test_different_input_different_hash(self):
        h1 = compute_pk_hash("Stripe", "Backend Engineer", "San Francisco")
        h2 = compute_pk_hash("Stripe", "Frontend Engineer", "San Francisco")
        assert h1 != h2

    def test_normalization_makes_equivalent(self):
        h1 = compute_pk_hash("stripe", "Sr Backend Eng", "NYC")
        h2 = compute_pk_hash("STRIPE", "Sr Backend Eng", "nyc")
        assert h1 == h2

    def test_none_location(self):
        h = compute_pk_hash("Co", "Role", None)
        assert isinstance(h, str) and len(h) == 32
