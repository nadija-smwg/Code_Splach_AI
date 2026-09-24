# backend/reasoning/counterfactual.py
"""
Phase 08 — Layer 4: Counterfactual Generator
==============================================
XAI Layer 4: For each discrepancy, answers the question:
  "What would need to change for this to pass?"

This is a 2026-trend XAI technique. Instead of just flagging what's wrong,
we give the user concrete, minimal, actionable fixes — directly mapped to
Sri Lankan apparel export customs context.

Output contract (matches Kaveen's Counterfactual TypeScript interface):
  {
    "options": [str, ...],          # max 4, specific to documents + values
    "recommendation": str           # domain-specific expert guidance
  }

Consumed by:
  - DiscrepancyEngine.process() attaches this to each discrepancy["counterfactual"]
  - Kaveen's DiscrepancyList component renders the counterfactual cards

Author: Aloka (Phase 08)
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Optional


class CounterfactualGenerator:
    """
    Layer 4 XAI: Generates minimal counterfactual changes that would resolve each discrepancy.

    For each conflict, answers: "What would need to change for this to pass?"
    Includes domain-specific recommendations for Sri Lankan apparel customs context.

    Usage
    -----
        gen = CounterfactualGenerator()
        cf = gen.generate(discrepancy)
        # cf = {"options": [...], "recommendation": "..."}

        # Attach to discrepancy record:
        discrepancy["counterfactual"] = cf
    """

    # ── Domain-specific recommendations (Sri Lankan apparel exports) ──────────
    DOMAIN_RECOMMENDATIONS: dict[str, str] = {
        "GROSS_WEIGHT": (
            "Verify actual weight at factory scale. The Packing List is typically "
            "the most accurate source for BOI apparel shipments. "
            "Differences > 5% will trigger a CUSDEC flag."
        ),
        "NET_WEIGHT": (
            "Net weight should be calculated as gross weight minus tare weight. "
            "Check for rounding differences across documents. "
            "Ensure the same weighing standard (metric kg) is used throughout."
        ),
        "TARE_WEIGHT": (
            "Tare weight is the container/carton weight. "
            "Verify this is consistent with the Packing List carton specifications."
        ),
        "PACKAGE_COUNT": (
            "Verify physical count at warehouse. Package unit terminology "
            "(cartons vs pieces) may differ but refer to the same items. "
            "Ensure units are consistent — do not compare 'cartons' with 'pieces'."
        ),
        "CONSIGNEE_NAME": (
            "Use the exact name as it appears in the Letter of Credit. "
            "Minor variations (Ltd. vs Limited, Inc. vs Incorporated) may cause "
            "LC rejection by the issuing bank."
        ),
        "SHIPPER_NAME": (
            "Shipper name must match exactly across Invoice, Packing List, and B/L. "
            "Check for abbreviations or subsidiary company name differences."
        ),
        "INCOTERM": (
            "Incoterm must be consistent across all documents. "
            "Invoice Incoterm is the contractual reference. "
            "FOB and CFR are the most common terms for Sri Lankan apparel exports."
        ),
        "TOTAL_AMOUNT": (
            "Invoice amount must match LC value exactly. "
            "Any discrepancy will cause bank rejection under UCP 600 rules. "
            "Check for currency conversion errors or missing charges."
        ),
        "INVOICE_NUMBER": (
            "Invoice number must be identical across all referencing documents. "
            "Check for typos, prefix differences, or leading zeros."
        ),
        "CURRENCY": (
            "Currency must be consistent across all documents. "
            "USD is standard for Sri Lankan apparel exports to US/EU markets."
        ),
        "AWB_NUMBER": (
            "AWB number must match exactly across all freight documents. "
            "Verify with the airline carrier directly if there is doubt."
        ),
        "BL_NUMBER": (
            "Bill of Lading number must match exactly across all documents. "
            "Any mismatch will block cargo release at the destination port."
        ),
        "CONTAINER_NUMBER": (
            "Container number is an ISO standard 11-character code (4 letters + 7 digits). "
            "Verify directly with the shipping line."
        ),
        "VESSEL_NAME": (
            "Vessel name must match the shipping line's official name. "
            "Abbreviations may differ — use the name on the Arrival Notice."
        ),
        "PORT_LOADING": (
            "Port of loading must match the physical export port used. "
            "For Sri Lanka, this is typically Colombo (CMB) or Hambantota."
        ),
        "PORT_DISCHARGE": (
            "Port of discharge must match the destination as stated in the LC. "
            "Verify with the freight forwarder for transshipment details."
        ),
        "WEIGHT_CONSISTENCY": (
            "Internal weight consistency: net weight + tare weight must equal gross weight "
            "within each document. This is a fundamental sanity check before submission."
        ),
        "VOLUME": (
            "Volume (CBM) must be consistent with the carton dimensions stated in the "
            "Packing List. Recalculate: L × W × H × carton_count / 1,000,000."
        ),
    }

    _DEFAULT_RECOMMENDATION = (
        "Review the source documents carefully and select the correct value. "
        "When in doubt, contact your customs broker or freight forwarder."
    )

    # ── Numeric tolerance for 'effectively equal' ─────────────────────────────
    _NUMERIC_TOLERANCE = 0.001   # absolute difference below which values are treated as equal
    _SIMILARITY_HIGH   = 0.90   # SequenceMatcher ratio above which we flag as typo
    _SIMILARITY_CLOSE  = 0.70   # Above which we flag as close match

    # ── Public API ─────────────────────────────────────────────────────────────

    def generate(self, discrepancy: dict) -> dict:
        """
        Generate counterfactual options and domain recommendation for one discrepancy.

        Parameters
        ----------
        discrepancy : dict
            A discrepancy record as produced by DiscrepancyEngine.process().
            Must have: "field", "sources", "conflict_type".
            Optional: "detail" (for internal_inconsistency).

        Returns
        -------
        dict  {"options": list[str], "recommendation": str}
        """
        field        = discrepancy.get("field", "UNKNOWN")
        sources      = discrepancy.get("sources", [])
        conflict_type = discrepancy.get("conflict_type", "unknown")

        # Route to the correct generator
        if conflict_type == "numeric_variance":
            options = self._numeric_counterfactual(field, sources)
        elif conflict_type == "text_mismatch":
            options = self._text_counterfactual(field, sources)
        elif conflict_type == "internal_inconsistency":
            options = self._internal_counterfactual(discrepancy)
        else:
            options = self._generic_counterfactual(field, sources)

        # Always guarantee at least 1 option
        if not options:
            options = [f"Verify the {field.replace('_', ' ').lower()} value across all documents."]

        # Cap at 4 to avoid overwhelming the user
        options = options[:4]

        recommendation = self.DOMAIN_RECOMMENDATIONS.get(field, self._DEFAULT_RECOMMENDATION)

        return {"options": options, "recommendation": recommendation}

    def generate_batch(self, discrepancies: list) -> list:
        """
        Attach counterfactual data to every discrepancy in a list (in-place + return).

        Parameters
        ----------
        discrepancies : list  Output from DiscrepancyEngine.process()

        Returns
        -------
        list  Same list with each item's "counterfactual" field populated.
        """
        for disc in discrepancies:
            disc["counterfactual"] = self.generate(disc)
        return discrepancies

    # ── Internal generators ────────────────────────────────────────────────────

    def _numeric_counterfactual(self, field: str, sources: list) -> list[str]:
        """
        Generate counterfactuals for numeric value conflicts.

        For each pair of documents with different values, suggests what one would
        need to become to match the other.  Also adds a percentage difference note.
        """
        options: list[str] = []
        field_label = field.replace("_", " ").lower()

        # Parse each source value to float for comparison
        parsed: list[tuple[str, str, float]] = []  # (doc_name, raw_value, float_value)
        for src in sources:
            doc = src.get("document_type", "Unknown").replace("_", " ").title()
            raw = str(src.get("value", "")).strip()
            num = self._parse_numeric(raw)
            parsed.append((doc, raw, num))

        # Build pairwise options
        seen: set[str] = set()
        for i, (doc_a, raw_a, num_a) in enumerate(parsed):
            for j, (doc_b, raw_b, num_b) in enumerate(parsed):
                if i >= j:
                    continue
                if raw_a == raw_b:
                    continue  # same value — not a conflict

                opt_ab = (
                    f"If {doc_a} {field_label} were {raw_b} "
                    f"(instead of {raw_a}), this discrepancy would resolve."
                )
                opt_ba = (
                    f"If {doc_b} {field_label} were {raw_a} "
                    f"(instead of {raw_b}), this discrepancy would resolve."
                )
                for opt in (opt_ab, opt_ba):
                    if opt not in seen:
                        seen.add(opt)
                        options.append(opt)

                # Add percentage note for numeric values
                if num_a is not None and num_b is not None and num_b != 0:
                    pct = abs(num_a - num_b) / num_b * 100
                    if pct >= 0.01:
                        note = f"Difference between {doc_a} and {doc_b}: {pct:.2f}%."
                        if note not in seen:
                            seen.add(note)
                            options.append(note)

        return options[:4]

    def _text_counterfactual(self, field: str, sources: list) -> list[str]:
        """
        Generate counterfactuals for text mismatch conflicts.

        Shows exactly what each document's text would need to become,
        and adds a similarity hint so the user knows if it's likely a typo.
        """
        if len(sources) < 2:
            field_label = field.replace("_", " ").lower()
            return [f"Only one source found for {field_label} — cannot generate comparison."]

        options: list[str] = []
        field_label = field.replace("_", " ").lower()

        # Generate pairwise options for all source combinations
        seen: set[str] = set()
        for i in range(len(sources)):
            for j in range(i + 1, len(sources)):
                val_a = str(sources[i].get("value", "")).strip()
                val_b = str(sources[j].get("value", "")).strip()
                doc_a = sources[i].get("document_type", "Unknown").replace("_", " ").title()
                doc_b = sources[j].get("document_type", "Unknown").replace("_", " ").title()

                if val_a == val_b:
                    continue

                opt1 = f"If {doc_b} {field_label} were '{val_a}', values would match exactly."
                opt2 = f"If {doc_a} {field_label} were '{val_b}', values would match exactly."
                for opt in (opt1, opt2):
                    if opt not in seen:
                        seen.add(opt)
                        options.append(opt)

                # Similarity hint
                sim = SequenceMatcher(None, val_a.lower(), val_b.lower()).ratio()
                if sim >= self._SIMILARITY_HIGH:
                    note = (
                        f"'{val_a}' and '{val_b}' are {sim:.0%} similar — "
                        f"likely a minor typographical or abbreviation difference."
                    )
                elif sim >= self._SIMILARITY_CLOSE:
                    note = (
                        f"'{val_a}' and '{val_b}' are {sim:.0%} similar — "
                        f"check for name abbreviation or formatting difference."
                    )
                else:
                    note = None

                if note and note not in seen:
                    seen.add(note)
                    options.append(note)

        return options[:4]

    def _internal_counterfactual(self, discrepancy: dict) -> list[str]:
        """
        Generate counterfactuals for internal document inconsistencies.

        These occur when a single document's own fields are self-contradictory
        (e.g. net + tare ≠ gross within the same Packing List).
        """
        detail = discrepancy.get("detail", "weight values are internally inconsistent.")
        doc = discrepancy.get("sources", [{}])[0].get("document_type", "the document")
        doc_label = doc.replace("_", " ").title() if isinstance(doc, str) else "the document"

        return [
            f"Within {doc_label}, correct values so that net weight + tare weight = gross weight.",
            f"Specific issue detected: {detail}",
            "Reweigh the shipment at the factory and update all documents consistently.",
        ]

    def _generic_counterfactual(self, field: str, sources: list) -> list[str]:
        """
        Fallback counterfactual for unrecognised conflict types.
        Shows each source's value so the user can manually compare.
        """
        options: list[str] = []
        field_label = field.replace("_", " ").lower()
        seen: set[str] = set()

        for src in sources:
            doc = src.get("document_type", "Unknown").replace("_", " ").title()
            val = str(src.get("value", "N/A")).strip()
            opt = f"Verify {field_label} value in {doc}: '{val}'"
            if opt not in seen:
                seen.add(opt)
                options.append(opt)

        if not options:
            options = [f"Manually review the {field_label} field across all submitted documents."]

        return options[:4]

    # ── Utility ────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_numeric(raw: str) -> Optional[float]:
        """
        Extract the first numeric value from a raw string.
        e.g. "450.00 KG" -> 450.0, "25 Cartons" -> 25.0, "USD 49,740.00" -> 49740.0
        Returns None if no number can be parsed.
        """
        # Remove commas used as thousands separators
        cleaned = raw.replace(",", "")
        match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None
