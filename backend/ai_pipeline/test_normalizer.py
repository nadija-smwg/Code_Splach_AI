# backend/ai_pipeline/test_normalizer.py
# Phase 09 — EntityNormalizer test suite
# Covers ALL acceptance criteria from Phase_09_Normalization.md
#
# Run:  pytest backend/ai_pipeline/test_normalizer.py -v
#
# Requires: pytest, pytest-mock
# pip install pytest pytest-mock

import pytest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Fixture — normalizer with DB and Gemini disabled (unit tests, no I/O)
# ---------------------------------------------------------------------------

@pytest.fixture
def normalizer():
    """EntityNormalizer with no DB pool and no Gemini client."""
    with patch("os.getenv", side_effect=_env_no_db_no_gemini):
        from ai_pipeline.normalizer import EntityNormalizer
        n = EntityNormalizer()
    # Ensure pool and gemini are None so tests stay unit-level
    n._db_pool = None
    n._gemini = None
    return n


def _env_no_db_no_gemini(key, default=None):
    # Suppress DB and Gemini initialization
    if key == "DATABASE_URL":
        return None
    if key == "GEMINI_API_KEY":
        return ""
    return default


# ===========================================================================
# DETERMINISTIC — WEIGHTS
# ===========================================================================

class TestWeights:

    def test_kg_plain(self, normalizer):
        r = normalizer.normalize("GROSS_WEIGHT", "450 KG")
        assert r["normalized_value"] == 450.0
        assert r["unit"] == "kg"
        assert r["warn"] is False

    def test_kg_decimal(self, normalizer):
        r = normalizer.normalize("GROSS_WEIGHT", "450.00 Kilograms")
        assert r["normalized_value"] == 450.0
        assert r["unit"] == "kg"

    def test_lbs_to_kg(self, normalizer):
        r = normalizer.normalize("GROSS_WEIGHT", "1,000.00 LBS")
        assert round(r["normalized_value"], 3) == 453.592
        assert r["unit"] == "kg"

    def test_mt_to_kg(self, normalizer):
        r = normalizer.normalize("GROSS_WEIGHT", "2 MT")
        assert r["normalized_value"] == 2000.0
        assert r["unit"] == "kg"

    def test_grams_to_kg(self, normalizer):
        r = normalizer.normalize("GROSS_WEIGHT", "500 g")
        assert r["normalized_value"] == pytest.approx(0.5, rel=1e-4)
        assert r["unit"] == "kg"

    def test_missing_unit_warns(self, normalizer):
        r = normalizer.normalize("GROSS_WEIGHT", "450")
        assert r["normalized_value"] == 450.0
        assert r["unit"] == "kg"
        assert r["warn"] is True

    def test_unparseable_warns(self, normalizer):
        r = normalizer.normalize("GROSS_WEIGHT", "45O.OO KG")   # letter O
        assert r["normalized_value"] is None
        assert r["warn"] is True


# ===========================================================================
# DETERMINISTIC — VOLUMES
# ===========================================================================

class TestVolumes:

    def test_cbm(self, normalizer):
        r = normalizer.normalize("VOLUME", "12.5 CBM")
        assert r["normalized_value"] == 12.5
        assert r["unit"] == "cbm"

    def test_liters_to_cbm(self, normalizer):
        r = normalizer.normalize("VOLUME", "12500 liters")
        assert r["normalized_value"] == pytest.approx(12.5, rel=1e-4)
        assert r["unit"] == "cbm"


# ===========================================================================
# DETERMINISTIC — PACKAGE COUNTS
# ===========================================================================

class TestPackageCount:

    def test_ctns(self, normalizer):
        r = normalizer.normalize("PACKAGE_COUNT", "25 CTNS")
        assert r["normalized_value"] == 25
        assert r["unit"] == "cartons"

    def test_cartons(self, normalizer):
        r = normalizer.normalize("PACKAGE_COUNT", "25 Cartons")
        assert r["normalized_value"] == 25
        assert r["unit"] == "cartons"

    def test_pieces(self, normalizer):
        r = normalizer.normalize("PACKAGE_COUNT", "25 Pieces")
        assert r["normalized_value"] == 25
        assert r["unit"] == "pieces"


# ===========================================================================
# DETERMINISTIC — DATES
# ===========================================================================

class TestDates:

    def test_aug_format(self, normalizer):
        r = normalizer.normalize("INVOICE_DATE", "15-Aug-2026")
        assert r["normalized_value"] == "2026-08-15"

    def test_slash_format(self, normalizer):
        r = normalizer.normalize("INVOICE_DATE", "08/15/2026")
        assert r["normalized_value"] == "2026-08-15"

    def test_dot_format(self, normalizer):
        r = normalizer.normalize("INVOICE_DATE", "2026.08.15")
        assert r["normalized_value"] == "2026-08-15"

    def test_unparseable_returns_none(self, normalizer):
        r = normalizer.normalize("INVOICE_DATE", "31-FOO-2026")
        assert r["normalized_value"] is None
        assert r["warn"] is True


# ===========================================================================
# DETERMINISTIC — NUMBERS & LOCALE FORMATS
# ===========================================================================

class TestNumbers:

    def test_us_format(self, normalizer):
        r = normalizer.normalize("TOTAL_AMOUNT", "1,250.50")
        assert r["normalized_value"] == pytest.approx(1250.5)

    def test_european_format(self, normalizer):
        r = normalizer.normalize("TOTAL_AMOUNT", "1.250,50")
        assert r["normalized_value"] == pytest.approx(1250.5)

    def test_thousands_only(self, normalizer):
        r = normalizer.normalize("TOTAL_AMOUNT", "1,250")
        assert r["normalized_value"] == pytest.approx(1250.0)

    def test_decimal_comma(self, normalizer):
        r = normalizer.normalize("TOTAL_AMOUNT", "450,00")
        assert r["normalized_value"] == pytest.approx(450.0)

    def test_currency_prefix_stripped(self, normalizer):
        r = normalizer.normalize("TOTAL_AMOUNT", "USD 49,740.00")
        assert r["normalized_value"] == pytest.approx(49740.0)


# ===========================================================================
# DETERMINISTIC — IDENTIFIERS
# ===========================================================================

class TestIdentifiers:

    def test_container_spaces_removed(self, normalizer):
        r = normalizer.normalize("CONTAINER_NUMBER", "MAEU 123 456 789")
        assert r["normalized_value"] == "MAEU123456789"

    def test_awb_dashes_removed(self, normalizer):
        r = normalizer.normalize("AWB_NUMBER", "631-12345678")
        assert r["normalized_value"] == "63112345678"

    def test_hs_dots_removed(self, normalizer):
        r = normalizer.normalize("HS_CODE", "8516.72.00.00")
        assert r["normalized_value"] == "85167200"


# ===========================================================================
# DETERMINISTIC — INCOTERMS
# ===========================================================================

class TestIncoterms:

    def test_fob_with_port(self, normalizer):
        r = normalizer.normalize("INCOTERM", "FOB Colombo")
        assert r["normalized_value"] == "FOB"

    def test_free_on_board(self, normalizer):
        r = normalizer.normalize("INCOTERM", "Free On Board")
        assert r["normalized_value"] == "FOB"

    def test_cif(self, normalizer):
        r = normalizer.normalize("INCOTERM", "CIF London")
        assert r["normalized_value"] == "CIF"


# ===========================================================================
# DETERMINISTIC — CURRENCY
# ===========================================================================

class TestCurrency:

    def test_usd_lowercase(self, normalizer):
        r = normalizer.normalize("CURRENCY_CODE", "usd")
        assert r["normalized_value"] == "USD"

    def test_us_dollar_phrase(self, normalizer):
        r = normalizer.normalize("CURRENCY_CODE", "US Dollar")
        assert r["normalized_value"] == "USD"

    def test_lkr(self, normalizer):
        r = normalizer.normalize("CURRENCY_CODE", "Sri Lankan Rupee")
        assert r["normalized_value"] == "LKR"


# ===========================================================================
# SEMANTIC — Tier 1/2/3 path (mocked DB + Gemini)
# ===========================================================================

class TestSemanticNormalization:

    def _make_normalizer_with_mocks(self):
        """Return a normalizer whose DB and Gemini are mockable."""
        from ai_pipeline.normalizer import EntityNormalizer
        n = EntityNormalizer.__new__(EntityNormalizer)
        n._db_pool = None
        n._gemini = None
        n._gemini_model = "test-model"
        return n

    def test_tier1_key_is_sorted(self):
        from ai_pipeline.normalizer import EntityNormalizer
        n = EntityNormalizer.__new__(EntityNormalizer)
        n._db_pool = None
        n._gemini = None
        n._gemini_model = "test-model"
        key_a = n._tier1_key("PORT_OF_LOADING", "Colombo Custom Port")
        key_b = n._tier1_key("PORT_OF_LOADING", "Port Custom Colombo")
        assert key_a == key_b  # token-sort produces same key

    def test_cache_hit_returns_canonical(self, mocker):
        from ai_pipeline.normalizer import EntityNormalizer
        n = EntityNormalizer.__new__(EntityNormalizer)
        n._db_pool = MagicMock()
        n._gemini = None
        n._gemini_model = "test-model"

        # Simulate DB returning a cached value
        mocker.patch.object(n, "_db_get", return_value="Colombo Port (LKCMB)")
        mocker.patch.object(n, "_db_increment_hit")

        r = n._normalize_semantic("PORT_OF_LOADING", "Colombo Custom Port")
        assert r["normalized_value"] == "Colombo Port (LKCMB)"
        n._db_increment_hit.assert_called_once()

    def test_cache_miss_calls_gemini_then_saves(self, mocker):
        from ai_pipeline.normalizer import EntityNormalizer
        n = EntityNormalizer.__new__(EntityNormalizer)
        n._db_pool = MagicMock()
        n._gemini = MagicMock()
        n._gemini_model = "test-model"

        mocker.patch.object(n, "_db_get", return_value=None)
        mocker.patch.object(n, "_llm_canonicalize", return_value="Colombo Port (LKCMB)")
        mocker.patch.object(n, "_db_set")

        r = n._normalize_semantic("PORT_OF_LOADING", "Port Custom Colombo")

        n._llm_canonicalize.assert_called_once_with("PORT_OF_LOADING", "Port Custom Colombo")
        n._db_set.assert_called_once()
        assert r["normalized_value"] == "Colombo Port (LKCMB)"

    def test_raw_value_always_preserved(self, mocker):
        from ai_pipeline.normalizer import EntityNormalizer
        n = EntityNormalizer.__new__(EntityNormalizer)
        n._db_pool = None
        n._gemini = None
        n._gemini_model = "test-model"

        mocker.patch.object(n, "_db_get", return_value=None)
        mocker.patch.object(n, "_llm_canonicalize", return_value="Normalized")
        mocker.patch.object(n, "_db_set")

        raw = "Port Custom Colombo"
        r = n._normalize_semantic("PORT_OF_LOADING", raw)
        assert r["original_value"] == raw

    def test_gemini_unavailable_returns_raw(self):
        from ai_pipeline.normalizer import EntityNormalizer
        n = EntityNormalizer.__new__(EntityNormalizer)
        n._db_pool = None
        n._gemini = None  # Gemini disabled
        n._gemini_model = "test-model"

        result = n._llm_canonicalize("PORT_OF_LOADING", "Unknown Port XYZ")
        assert result == "Unknown Port XYZ"


# ===========================================================================
# ERROR HANDLING
# ===========================================================================

class TestErrorHandling:

    def test_normalize_never_raises(self, normalizer):
        # Should return a warn=True dict, not raise
        r = normalizer.normalize("GROSS_WEIGHT", None)
        assert isinstance(r, dict)
        assert "normalized_value" in r

    def test_db_unavailable_does_not_crash(self, normalizer):
        # normalizer fixture already has _db_pool=None
        r = normalizer.normalize("PORT_OF_LOADING", "Colombo Port")
        assert isinstance(r, dict)

    def test_zero_is_valid_normalized_value(self, normalizer):
        """0 is a valid normalized_value — must not be treated as falsy."""
        r = normalizer.normalize("TOTAL_AMOUNT", "0.00")
        # normalized_value should be 0.0, not None
        assert r["normalized_value"] is not None
        assert r["normalized_value"] == pytest.approx(0.0)
