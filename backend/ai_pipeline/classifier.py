# backend/ai_pipeline/classifier.py
"""
Phase 04 — Document Classifier
================================
Identifies what TYPE of shipping document a PDF is.

Why we need this:
  - Different documents have different fields. A Commercial Invoice has "Unit Price",
    an Airway Bill has "Flight Number". The entity extractor (Phase 05) needs to know
    WHICH schema to use before it can extract the right data.
  - Classification confidence feeds into Aloka's Layer 3 XAI (decomposed confidence).
  - If the AI says "I'm 55% sure this is an AWB", the user knows to double-check.

Strategy (two-layer approach):
  Layer 1 — Keyword Heuristic   (fast, ~80% accuracy, always runs first)
  Layer 2 — Gemini Vision API   (slow, ~95% accuracy, only runs if Layer 1 score < 0.70)

Author: Nadija
"""

import os
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

# python-dotenv lets us read the GEMINI_API_KEY from the .env file
from dotenv import load_dotenv

# Load .env from the backend/ folder (two levels up from this file)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Import our OcrOutput dataclass so we can accept it as input
from ai_pipeline.ocr_engine import OcrOutput

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT CONTRACT  (what this module promises to return)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ClassificationResult:
    """
    Everything downstream (entity extractor, reasoning engine, frontend) needs
    to know about which document type was detected and how confident we are.

    Fields
    ------
    document_type  : canonical snake_case key  e.g. "commercial_invoice"
    confidence     : float 0.0–1.0 for the WINNING type (normalised)
    all_scores     : scores for EVERY document type so the frontend can show
                     a full breakdown (used in XAI Layer 3)
    evidence       : the keywords/patterns that actually drove the decision
                     (XAI Layer 1 — human-readable explanation)
    method         : "keyword" or "gemini" — tells Aloka which approach was used
    """
    document_type: str
    confidence: float
    all_scores: dict
    evidence: list
    method: str = "keyword"


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT SIGNATURES  (keyword dictionary for Layer 1)
# ─────────────────────────────────────────────────────────────────────────────

# Each document type has:
#   "keywords" — a list of strings we search for inside the OCR text
#   "weight"   — a multiplier. 1.0 = full confidence boost.
#                0.8 = slightly weaker signal (freight_invoice and delivery_order
#                often share generic words like "charges" with other docs)

DOCUMENT_SIGNATURES = {
    "commercial_invoice": {
        "keywords": [
            "invoice", "unit price", "total amount", "commercial invoice",
            "inv no", "invoice no", "invoice number", "amount due",
            "payment terms", "description of goods"
        ],
        "weight": 1.0
    },
    "packing_list": {
        "keywords": [
            "packing list", "carton", "net weight", "gross weight",
            "bale", "roll", "packing", "no of cartons", "dimensions",
            "cbm", "cubic"
        ],
        "weight": 1.0
    },
    "awb": {
        # AWB = Air Waybill. MAWB = Master AWB, HAWB = House AWB
        "keywords": [
            "air waybill", "airway bill", "mawb", "hawb", "flight",
            "iata", "awb", "airport of departure", "airport of destination",
            "chargeable weight", "pieces"
        ],
        "weight": 1.0
    },
    "bl": {
        # BL = Bill of Lading (sea freight equivalent of an AWB)
        "keywords": [
            "bill of lading", "b/l", "vessel", "port of loading",
            "port of discharge", "shipper", "notify party",
            "container", "seal no", "freight prepaid", "freight collect"
        ],
        "weight": 1.0
    },
    "freight_invoice": {
        "keywords": [
            "freight", "charges", "thc", "documentation fee",
            "handling", "terminal handling", "freight charges",
            "bl fee", "awb fee"
        ],
        "weight": 0.8  # "freight" and "charges" appear in other docs too
    },
    "delivery_order": {
        "keywords": [
            "delivery order", "freight arrival", "do no",
            "arrival notice", "fan", "release", "cargo release",
            "collect cargo"
        ],
        "weight": 0.8
    },
    "letter_of_credit": {
        "keywords": [
            "letter of credit", "l/c", "documentary credit",
            "issuing bank", "beneficiary", "lc number",
            "credit number", "expiry date", "place of expiry",
            "partial shipment"
        ],
        "weight": 1.0
    }
}

# Confidence threshold below which we call Gemini Vision for a second opinion
GEMINI_FALLBACK_THRESHOLD = 0.70


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 1 — KEYWORD HEURISTIC CLASSIFIER
# ─────────────────────────────────────────────────────────────────────────────

class KeywordClassifier:
    """
    Fast, deterministic classifier using keyword matching.

    How it works
    ------------
    1. Take the OCR text from the first 2 pages (headers/titles appear early).
    2. Convert everything to lowercase so "Invoice" matches "invoice".
    3. For each document type, count how many of its keywords appear in the text.
    4. score = (matched_count / total_keywords) * weight
       → e.g. if 6 out of 10 AWB keywords matched, score = 0.60 * 1.0 = 0.60
    5. Normalise all scores so they sum to 1.0 (turns them into probabilities).
    6. The type with the highest normalised score wins.
    """

    def classify(self, ocr_output: OcrOutput) -> ClassificationResult:
        # ── Step 1: Combine text from first 2 pages ──────────────────────────
        # We only look at the first 2 pages because the document type heading
        # (e.g. "COMMERCIAL INVOICE") is almost always in the header.
        full_text = ""
        for page in ocr_output.pages[:2]:
            # Each page has a list of OcrToken objects. We join their .text fields.
            full_text += " ".join([token.text for token in page.tokens]) + " "

        full_text_lower = full_text.lower()

        # ── Step 2: Score each document type ─────────────────────────────────
        raw_scores = {}
        evidence_map = {}

        for doc_type, sig in DOCUMENT_SIGNATURES.items():
            # Find which keywords from this type's list appear in the text
            matched = [kw for kw in sig["keywords"] if kw in full_text_lower]

            # Score = fraction of keywords matched × weight multiplier
            score = (len(matched) / len(sig["keywords"])) * sig["weight"]

            raw_scores[doc_type] = round(score, 4)
            evidence_map[doc_type] = matched  # save evidence for XAI

        # ── Step 3: Find the winner (before normalisation) ───────────────────
        best_type = max(raw_scores, key=raw_scores.get)
        best_raw_score = raw_scores[best_type]

        # ── Step 4: Normalise so all scores sum to 1.0 ───────────────────────
        # This converts raw keyword-match ratios into something that looks like
        # probability scores.  E.g.  {awb: 0.5, invoice: 0.3, ...} → {awb: 0.56, ...}
        total = sum(raw_scores.values()) or 1.0  # guard against all-zero
        normalised = {k: round(v / total, 4) for k, v in raw_scores.items()}

        # ── Step 5: Handle "no match at all" edge case ───────────────────────
        # If NOTHING matched (e.g. a blank or image-only PDF), best_raw_score = 0.
        # We still return a result but with very low confidence so Gemini is called.
        if best_raw_score == 0:
            logger.warning("No keywords matched — document may be blank or image-only.")
            # Return uniform "unknown" signal
            even = round(1 / len(DOCUMENT_SIGNATURES), 4)
            normalised = {k: even for k in DOCUMENT_SIGNATURES}
            return ClassificationResult(
                document_type="unknown",
                confidence=even,
                all_scores=normalised,
                evidence=[],
                method="keyword"
            )

        return ClassificationResult(
            document_type=best_type,
            confidence=normalised[best_type],
            all_scores=normalised,
            evidence=evidence_map[best_type],
            method="keyword"
        )


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2 — GEMINI VISION CLASSIFIER  (fallback)
# ─────────────────────────────────────────────────────────────────────────────

class GeminiClassifier:
    """
    Uses the Gemini Vision API to look at the FIRST PAGE IMAGE of the PDF
    and classify it — like a human would by reading the header.

    When is this called?
    --------------------
    Only when the KeywordClassifier returns a confidence < 0.70. That means
    the keyword approach wasn't sure — maybe the document is scanned at an
    angle, the header is missing, or keywords appear in an unusual order.

    How it works
    ------------
    1. Convert page 1 of the PDF to a PIL Image using pdf2image.
    2. Send the image + a detailed prompt to gemini-2.0-flash.
    3. Parse the JSON response it returns.
    4. Return a ClassificationResult exactly like the keyword classifier does.

    Requires: GEMINI_API_KEY in backend/.env
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_key_here":
            raise EnvironmentError(
                "GEMINI_API_KEY is not set in backend/.env. "
                "Add it before using GeminiClassifier."
            )
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"GeminiClassifier initialised with {model_name}")

    def classify(self, pdf_path: str) -> Optional[ClassificationResult]:
        """
        Classify a document by looking at its first page image.
        Returns None if the API call fails (so caller can handle gracefully).
        """
        try:
            from pdf2image import convert_from_path

            # Convert only page 1 to a PIL Image (fast, low memory)
            images = convert_from_path(pdf_path, first_page=1, last_page=1)
            if not images:
                logger.warning(f"Could not convert {pdf_path} to image")
                return None

            first_page_image = images[0]

            # ── Prompt engineering ────────────────────────────────────────
            # We give Gemini the EXACT list of valid type keys so it can't
            # hallucinate something like "shipping_document".
            # Asking for JSON output makes parsing reliable.
            prompt = """You are an expert customs document classifier.
Look at this shipping/trade document and classify it into EXACTLY ONE of these types:

  - commercial_invoice
  - packing_list
  - awb          (Air Waybill — HAWB or MAWB)
  - bl           (Bill of Lading)
  - freight_invoice
  - delivery_order
  - letter_of_credit

Respond with ONLY valid JSON (no markdown, no extra text):
{
  "document_type": "<one of the types above>",
  "confidence": <float between 0.0 and 1.0>,
  "evidence": ["<keyword or feature you saw>", "..."]
}"""

            # ── Call Gemini ───────────────────────────────────────────────
            response = self.model.generate_content([prompt, first_page_image])
            raw_text = response.text.strip()

            # Strip markdown code fences if Gemini wraps in ```json ... ```
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```[a-z]*\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text)

            parsed = json.loads(raw_text)

            doc_type   = parsed.get("document_type", "unknown")
            confidence = float(parsed.get("confidence", 0.5))
            evidence   = parsed.get("evidence", [])

            # Build all_scores: winner gets its stated confidence,
            # rest share what's left equally (Gemini only returns the winner)
            remaining = max(0.0, 1.0 - confidence)
            others = [k for k in DOCUMENT_SIGNATURES if k != doc_type]
            per_other = round(remaining / len(others), 4) if others else 0.0
            all_scores = {k: per_other for k in DOCUMENT_SIGNATURES}
            if doc_type in all_scores:
                all_scores[doc_type] = round(confidence, 4)

            return ClassificationResult(
                document_type=doc_type,
                confidence=round(confidence, 4),
                all_scores=all_scores,
                evidence=evidence,
                method="gemini"
            )

        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned non-JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"GeminiClassifier failed: {e}")
            return None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CLASSIFIER  (combines both layers — this is what you import everywhere)
# ─────────────────────────────────────────────────────────────────────────────

class DocumentClassifier:
    """
    The public-facing classifier.

    Usage
    -----
        from ai_pipeline.classifier import DocumentClassifier
        from ai_pipeline.ocr_engine import OcrEngine

        ocr    = OcrEngine()
        clf    = DocumentClassifier()

        ocr_out = ocr.extract("path/to/document.pdf")
        result  = clf.classify(ocr_out, pdf_path="path/to/document.pdf")

        print(result.document_type)   # e.g. "commercial_invoice"
        print(result.confidence)      # e.g. 0.82
        print(result.evidence)        # e.g. ["invoice", "unit price", "total amount"]
        print(result.method)          # "keyword" or "gemini"

    Decision Flow
    -------------
    1. Always run KeywordClassifier first (fast, free).
    2. If confidence >= 0.70  →  trust the keyword result, done.
    3. If confidence <  0.70  →  call GeminiClassifier (slower, paid API).
    4. If Gemini fails (API error, no key)  →  fall back to keyword result anyway.
    """

    def __init__(self, use_gemini_fallback: bool = True):
        """
        Parameters
        ----------
        use_gemini_fallback : bool
            Set to False during testing if you don't want to use API credits.
        """
        self.keyword_clf = KeywordClassifier()
        self.use_gemini_fallback = use_gemini_fallback
        self._gemini_clf = None  # lazy-loaded on first use

    def _get_gemini(self) -> Optional[GeminiClassifier]:
        """Initialise Gemini lazily — only when actually needed."""
        if self._gemini_clf is None:
            try:
                self._gemini_clf = GeminiClassifier()
            except EnvironmentError as e:
                logger.warning(f"Gemini unavailable: {e}")
                self._gemini_clf = False  # mark as failed so we don't retry
        return self._gemini_clf if self._gemini_clf else None

    def classify(
        self,
        ocr_output: OcrOutput,
        pdf_path: Optional[str] = None
    ) -> ClassificationResult:
        """
        Classify a document.

        Parameters
        ----------
        ocr_output  : OcrOutput from Phase 02 OcrEngine
        pdf_path    : original PDF file path — needed only for Gemini Vision fallback
        """
        # ── Layer 1: Keyword Heuristic ────────────────────────────────────
        result = self.keyword_clf.classify(ocr_output)

        logger.info(
            f"[Keyword] '{result.document_type}' confidence={result.confidence:.2%} "
            f"evidence={result.evidence}"
        )

        # ── Check if we need Layer 2 ──────────────────────────────────────
        if result.confidence >= GEMINI_FALLBACK_THRESHOLD:
            # Keyword was confident enough — return immediately
            return result

        # Keyword confidence was LOW — try Gemini
        if not self.use_gemini_fallback:
            logger.info("Gemini fallback disabled — returning keyword result.")
            return result

        if pdf_path is None:
            logger.warning("Low keyword confidence but no pdf_path given — cannot call Gemini.")
            return result

        # ── Layer 2: Gemini Vision ────────────────────────────────────────
        logger.info(
            f"Keyword confidence {result.confidence:.2%} < {GEMINI_FALLBACK_THRESHOLD} "
            f"— calling Gemini Vision for '{pdf_path}'"
        )

        gemini_clf = self._get_gemini()
        if gemini_clf is None:
            logger.warning("Gemini not available — returning keyword result as-is.")
            return result

        gemini_result = gemini_clf.classify(pdf_path)
        if gemini_result is None:
            logger.warning("Gemini call failed — falling back to keyword result.")
            return result

        logger.info(
            f"[Gemini] '{gemini_result.document_type}' confidence={gemini_result.confidence:.2%}"
        )
        return gemini_result
