# backend/ai_pipeline/normalizer.py
# Phase 09 — Canonical Normalization (Three-Tier)
# Tier 1: deterministic cache-key   (token sort, zero cost)
# Tier 2: PostgreSQL norm_cache      (shared persistent cache)
# Tier 3: OpenAI semantic LLM        (cache-miss fallback only)

import logging
import os
import re
from pathlib import Path
from typing import Optional

from dateutil import parser as date_parser
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)


class EntityNormalizer:

    # ------------------------------------------------------------------
    # Entity-type classification sets
    # ------------------------------------------------------------------

    WEIGHT_TYPES = {"GROSS_WEIGHT", "NET_WEIGHT", "TARE_WEIGHT"}

    IDENTIFIER_TYPES = {
        "BL_NUMBER",
        "AWB_NUMBER",
        "CONTAINER_NUMBER",
        "INVOICE_NUMBER",
        "HS_CODE",
    }

    SEMANTIC_TYPES = {
        "CONSIGNEE_NAME",
        "SHIPPER_NAME",
        "PORT_LOADING",
        "PORT_DISCHARGE",
        "VESSEL_NAME",
    }

    # ------------------------------------------------------------------
    # Construction — wire up DB pool and OpenAI client
    # ------------------------------------------------------------------

    def __init__(self):

        # ── Tier 2 — PostgreSQL connection pool ────────────────────────
        self._db_pool = None

        try:
            from psycopg2.pool import ThreadedConnectionPool

            database_url = os.getenv("DATABASE_URL")

            if database_url:
                self._db_pool = ThreadedConnectionPool(
                    minconn=1,
                    maxconn=5,
                    dsn=database_url,
                )
                logger.info("EntityNormalizer: PostgreSQL cache enabled")
            else:
                logger.warning(
                    "DATABASE_URL not set — Tier 2 cache disabled"
                )

        except Exception as exc:
            logger.warning("PostgreSQL cache unavailable: %s", exc)

        # ── Tier 3 — OpenAI ────────────────────────────────────────────
        self._gemini = None
        self._gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

        api_key = os.getenv("GEMINI_API_KEY", "")

        if api_key and api_key not in ("", "your_key_here"):
            try:
                import google.generativeai as genai

                genai.configure(api_key=api_key)
                self._gemini = genai.GenerativeModel(self._gemini_model)
                logger.info(
                    "EntityNormalizer: OpenAI enabled model=%s",
                    self._gemini_model,
                )
            except Exception as exc:
                logger.warning("OpenAI init failed: %s", exc)

    # ==================================================================
    # PUBLIC API
    # normalize(entity_type, raw_value) → dict
    # ==================================================================

    def normalize(self, entity_type: str, raw_value: str) -> dict:
        """
        Normalize a single entity value.

        Returns:
            {
                "normalized_value": <float | str | None>,
                "unit":             <str | None>,
                "original_value":   <str>,
                "warn":             <bool>,
            }
        """
        try:
            raw_value = str(raw_value) if raw_value is not None else ""

            # WEIGHT ────────────────────────────────────────────────────
            if entity_type in self.WEIGHT_TYPES:
                number, unit, warn = self._normalize_weight(raw_value)
                return {
                    "normalized_value": number,
                    "unit": unit,
                    "original_value": raw_value,
                    "warn": warn,
                }

            # VOLUME ────────────────────────────────────────────────────
            if entity_type == "VOLUME":
                number, unit, warn = self._normalize_volume(raw_value)
                return {
                    "normalized_value": number,
                    "unit": unit,
                    "original_value": raw_value,
                    "warn": warn,
                }

            # PACKAGE COUNT ─────────────────────────────────────────────
            if entity_type == "PACKAGE_COUNT":
                number, unit, warn = self._normalize_package_count(raw_value)
                return {
                    "normalized_value": number,
                    "unit": unit,
                    "original_value": raw_value,
                    "warn": warn,
                }

            # INCOTERM ──────────────────────────────────────────────────
            if entity_type == "INCOTERM":
                return {
                    "normalized_value": self._normalize_incoterm(raw_value),
                    "unit": None,
                    "original_value": raw_value,
                    "warn": False,
                }

            # CURRENCY ──────────────────────────────────────────────────
            if entity_type == "CURRENCY_CODE" or entity_type == "CURRENCY":
                return {
                    "normalized_value": self._normalize_currency(raw_value),
                    "unit": None,
                    "original_value": raw_value,
                    "warn": False,
                }

            # NUMERIC AMOUNT ────────────────────────────────────────────
            if entity_type in {"TOTAL_AMOUNT", "UNIT_PRICE", "TOTAL_PRICE"}:
                number = self._normalize_number(raw_value)
                return {
                    "normalized_value": number,
                    "unit": None,
                    "original_value": raw_value,
                    "warn": number is None,
                }

            # DATE ──────────────────────────────────────────────────────
            if entity_type in {"INVOICE_DATE", "EXPIRY_DATE"}:
                normalized_date = self._normalize_date(raw_value)
                return {
                    "normalized_value": normalized_date,
                    "unit": None,
                    "original_value": raw_value,
                    "warn": normalized_date is None,
                }

            # IDENTIFIER ────────────────────────────────────────────────
            if entity_type in self.IDENTIFIER_TYPES:
                return {
                    "normalized_value": self._normalize_identifier(raw_value),
                    "unit": None,
                    "original_value": raw_value,
                    "warn": False,
                }

            # SEMANTIC TEXT ─────────────────────────────────────────────
            if entity_type in self.SEMANTIC_TYPES:
                return self._normalize_semantic(entity_type, raw_value)

            # UNKNOWN — strip and pass through ──────────────────────────
            return {
                "normalized_value": raw_value.strip(),
                "unit": None,
                "original_value": raw_value,
                "warn": False,
            }

        except Exception:
            logger.exception(
                "Normalization failed: entity_type=%s raw_value=%r",
                entity_type,
                raw_value,
            )
            return {
                "normalized_value": None,
                "unit": None,
                "original_value": raw_value,
                "warn": True,
            }

    # ==================================================================
    # TIER 1 — cache-key generation
    # ==================================================================

    def _tier1_key(self, entity_type: str, raw: str) -> str:
        cleaned = re.sub(r"[^a-z0-9\s]", " ", raw.lower())
        tokens = sorted(cleaned.split())
        return f"{entity_type}:{' '.join(tokens)}"

    # ==================================================================
    # SEMANTIC NORMALIZATION  (Tier 1 → Tier 2 → Tier 3)
    # ==================================================================

    def _normalize_semantic(self, entity_type: str, raw_value: str) -> dict:
        key = self._tier1_key(entity_type, raw_value)

        # Tier 2 — PostgreSQL cache ─────────────────────────────────────
        cached = self._db_get(key)
        if cached is not None:
            self._db_increment_hit(key)
            return {
                "normalized_value": cached,
                "unit": None,
                "original_value": raw_value,
                "warn": False,
            }

        # Tier 3 — OpenAI ───────────────────────────────────────────────
        canonical = self._llm_canonicalize(entity_type, raw_value)
        if not canonical:
            canonical = raw_value.strip()

        # Persist for next lookup
        self._db_set(
            key=key,
            entity_type=entity_type,
            raw_value=raw_value,
            canonical=canonical,
            source="llm",
        )

        return {
            "normalized_value": canonical,
            "unit": None,
            "original_value": raw_value,
            "warn": False,
        }

    # ==================================================================
    # DATABASE HELPERS
    # ==================================================================

    def _db_get(self, key: str) -> Optional[str]:
        if self._db_pool is None:
            return None
        conn = None
        try:
            conn = self._db_pool.getconn()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT canonical FROM norm_cache WHERE cache_key = %s LIMIT 1",
                    (key,),
                )
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as exc:
            logger.warning("DB cache read failed: %s", exc)
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            return None
        finally:
            if conn:
                self._db_pool.putconn(conn)

    def _db_set(
        self,
        key: str,
        entity_type: str,
        raw_value: str,
        canonical: str,
        source: str = "llm",
    ) -> None:
        if self._db_pool is None:
            return
        conn = None
        try:
            conn = self._db_pool.getconn()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO norm_cache (cache_key, entity_type, raw_value, canonical, source)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (cache_key)
                    DO UPDATE SET canonical = EXCLUDED.canonical, last_used = NOW()
                    """,
                    (key, entity_type, raw_value, canonical, source),
                )
            conn.commit()
        except Exception as exc:
            logger.warning("DB cache write failed: %s", exc)
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
        finally:
            if conn:
                self._db_pool.putconn(conn)

    def _db_increment_hit(self, key: str) -> None:
        if self._db_pool is None:
            return
        conn = None
        try:
            conn = self._db_pool.getconn()
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE norm_cache SET hit_count = hit_count + 1, last_used = NOW() WHERE cache_key = %s",
                    (key,),
                )
            conn.commit()
        except Exception as exc:
            logger.warning("DB hit update failed: %s", exc)
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
        finally:
            if conn:
                self._db_pool.putconn(conn)

    # ==================================================================
    # GEMINI — TIER 3
    # ==================================================================

    def _llm_canonicalize(self, entity_type: str, raw_value: str) -> str:
        if self._gemini is None:
            return raw_value.strip()

        prompt = f"""You are a customs document normalization assistant.

Entity type: {entity_type}
Raw value: {raw_value}

Task:
Return the canonical representation of this trade entity.

Rules:
1. Ports and locations:
   - Return a canonical location name.
   - Include UN/LOCODE only when confidently identifiable.
   - Never invent a UN/LOCODE.
2. Company names:
   - Normalize capitalization and common legal-name formatting.
   - Preserve the actual company identity.
3. Vessel names:
   - Normalize spacing and capitalization.
4. If a reliable canonical representation cannot be determined:
   - Return the original value with minimal formatting cleanup.

Return ONLY the canonical value. No explanation."""

        try:
            from pydantic import BaseModel
            import google.generativeai as genai

            class CanonicalizationResult(BaseModel):
                canonical: str

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self._gemini.generate_content(
                        prompt,
                        generation_config=genai.GenerationConfig(
                            response_mime_type="application/json",
                            response_schema=CanonicalizationResult,
                        ),
                    )
                    parsed = CanonicalizationResult.model_validate_json(response.text)
                    return parsed.canonical.strip()
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg and attempt < max_retries - 1:
                        import time, re
                        match = re.search(r"Please retry in ([\d\.]+)s", error_msg)
                        wait_sec = float(match.group(1)) + 1 if match else 20.0
                        logger.warning(f"OpenAI 429 Quota Exceeded in Normalizer. Waiting {wait_sec:.1f}s before retry (Attempt {attempt+1}/{max_retries})...")
                        time.sleep(wait_sec)
                    else:
                        logger.warning("OpenAI canonicalization failed after %d attempts: %s", attempt+1, e)
                        return raw_value.strip()

        except Exception as exc:
            logger.warning("OpenAI canonicalization setup failed: %s", exc)
            return raw_value.strip()

    # ==================================================================
    # DETERMINISTIC FIELD NORMALIZERS
    # ==================================================================

    def _normalize_weight(self, raw: str) -> tuple:
        text = raw.lower().strip()
        number = self._normalize_number(text)

        if number is None:
            return (None, None, True)

        if re.search(r"\b(kg|kgs|kilogram|kilograms)\b", text):
            return (number, "kg", False)

        if re.search(r"\b(lb|lbs|pound|pounds)\b", text):
            return (round(number * 0.453592, 3), "kg", False)

        if re.search(r"\b(mt|metric ton|metric tons|tonne|tonnes)\b", text):
            return (round(number * 1000.0, 3), "kg", False)

        if re.search(r"\b(g|gram|grams)\b", text):
            return (round(number / 1000.0, 6), "kg", False)

        # No unit found — default kg with warning
        return (number, "kg", True)

    def _normalize_volume(self, raw: str) -> tuple:
        text = raw.lower().strip()
        number = self._normalize_number(text)

        if number is None:
            return (None, None, True)

        if re.search(r"\b(cbm|m3|m³|cubic meter|cubic meters)\b", text):
            return (number, "cbm", False)

        if re.search(r"\b(l|liter|liters|litre|litres)\b", text):
            return (round(number * 0.001, 6), "cbm", False)

        return (number, "cbm", True)

    def _normalize_package_count(self, raw: str) -> tuple:
        text = raw.lower().strip()
        number = self._normalize_number(text)

        if number is None:
            return (None, None, True)

        if re.search(r"\b(ctn|ctns|carton|cartons)\b", text):
            return (int(number), "cartons", False)

        if re.search(r"\b(pc|pcs|piece|pieces)\b", text):
            return (int(number), "pieces", False)

        if re.search(r"\b(bale|bales)\b", text):
            return (int(number), "bales", False)

        if re.search(r"\b(roll|rolls)\b", text):
            return (int(number), "rolls", False)

        return (int(number), None, True)

    def _normalize_incoterm(self, raw: str) -> Optional[str]:
        text = raw.lower().strip()

        aliases = {
            "free on board": "FOB",
            "fob": "FOB",
            "cost insurance and freight": "CIF",
            "cost, insurance and freight": "CIF",
            "cif": "CIF",
            "cost and freight": "CFR",
            "cfr": "CFR",
            "ex works": "EXW",
            "exw": "EXW",
            "free carrier": "FCA",
            "fca": "FCA",
            "carriage paid to": "CPT",
            "cpt": "CPT",
            "carriage and insurance paid to": "CIP",
            "cip": "CIP",
            "delivered at place": "DAP",
            "dap": "DAP",
            "delivered at place unloaded": "DPU",
            "dpu": "DPU",
            "delivered duty paid": "DDP",
            "ddp": "DDP",
            "free alongside ship": "FAS",
            "fas": "FAS",
        }

        if text in aliases:
            return aliases[text]

        for code in ["EXW", "FCA", "CPT", "CIP", "DAP", "DPU", "DDP", "FAS", "FOB", "CFR", "CIF"]:
            if re.search(rf"\b{code.lower()}\b", text):
                return code

        return raw.strip().upper()

    def _normalize_currency(self, raw: str) -> Optional[str]:
        text = raw.lower().strip()

        aliases = {
            "usd": "USD",
            "us dollar": "USD",
            "us dollars": "USD",
            "u.s. dollar": "USD",
            "u.s. dollars": "USD",
            "eur": "EUR",
            "euro": "EUR",
            "euros": "EUR",
            "gbp": "GBP",
            "pound sterling": "GBP",
            "jpy": "JPY",
            "yen": "JPY",
            "lkr": "LKR",
            "sri lankan rupee": "LKR",
            "sri lankan rupees": "LKR",
        }

        if text in aliases:
            return aliases[text]

        if re.fullmatch(r"[A-Za-z]{3}", text):
            return text.upper()

        return raw.strip().upper()

    def _normalize_number(self, raw: str) -> Optional[float]:
        if not raw:
            return None

        s = str(raw).strip()

        # Strip leading currency code (e.g. "USD 1,250.00")
        s = re.sub(r"^[A-Z]{3}\s*", "", s.upper())

        has_comma = "," in s
        has_dot = "." in s

        if has_comma and has_dot:
            if s.rindex(",") > s.rindex("."):
                # European: 1.250,50 → 1250.50
                s = s.replace(".", "").replace(",", ".")
            else:
                # US/UK: 1,250.50 → 1250.50
                s = s.replace(",", "")

        elif has_comma:
            if re.search(r",\d{3}$", s):
                # Thousands separator: 1,250
                s = s.replace(",", "")
            else:
                # Decimal comma: 450,00
                s = s.replace(",", ".")

        match = re.search(r"[-+]?\d+(?:\.\d+)?", s)
        if not match:
            return None

        try:
            return float(match.group())
        except ValueError:
            return None

    def _normalize_date(self, raw: str) -> Optional[str]:
        try:
            parsed = date_parser.parse(raw, fuzzy=True)
            return parsed.strftime("%Y-%m-%d")
        except Exception:
            return None

    def _normalize_identifier(self, raw: str) -> str:
        return re.sub(r"[\s\-/\.]", "", raw).upper()
