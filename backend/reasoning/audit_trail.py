# backend/reasoning/audit_trail.py
"""
Dynamic Audit Trail — records real pipeline events per shipment.

Usage:
    from backend.reasoning.audit_trail import record_event, get_trail

    record_event(shipment_id, module="classifier", action="...", confidence=0.97, outcome="accepted")
    entries = get_trail(shipment_id)
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class AuditEntry:
    timestamp: str
    module: str
    action: str
    confidence: Optional[float]
    outcome: str
    event_hash: str = field(default="")

    def __post_init__(self):
        # Deterministic hash of the event for immutability demo
        payload = f"{self.timestamp}|{self.module}|{self.action}|{self.outcome}"
        self.event_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]


# ── In-memory registry keyed by shipment_id ────────────────────────────
_registry: Dict[str, List[AuditEntry]] = {}


def record_event(
    shipment_id: str,
    module: str,
    action: str,
    outcome: str,
    confidence: Optional[float] = None,
) -> None:
    """Record a single pipeline event for a shipment."""
    if shipment_id not in _registry:
        _registry[shipment_id] = []

    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        module=module,
        action=action,
        confidence=confidence,
        outcome=outcome,
    )
    _registry[shipment_id].append(entry)


def get_trail(shipment_id: str) -> Optional[List[dict]]:
    """Return the audit trail for a shipment as a list of dicts, or None if not found."""
    entries = _registry.get(shipment_id)
    if entries is None:
        return None
    return [asdict(e) for e in entries]


def build_demo_trail(shipment_id: str, documents: List[dict]) -> None:
    """
    Seed a realistic audit trail for demo purposes.
    Called by the /discrepancies and /graph routes when no real trail exists.
    """
    if shipment_id in _registry:
        return  # Already recorded; don't overwrite

    now = datetime.now(timezone.utc)

    def ts(offset_seconds: int) -> str:
        from datetime import timedelta
        return (now - timedelta(seconds=offset_seconds)).strftime("%Y-%m-%dT%H:%M:%S")

    entries = []

    # Classification events
    for i, doc in enumerate(documents):
        doc_type = doc.get("document_type", "unknown")
        doc_id = doc.get("document_id", f"doc_{i:03d}")
        conf = doc.get("classification_confidence", 0.95)
        entries.append(AuditEntry(
            timestamp=ts(50 - i * 3),
            module="classifier",
            action=f"Classified {doc_id} as '{doc_type}' (confidence {conf:.2f})",
            confidence=conf,
            outcome="accepted",
        ))

    # Extraction events
    for i, doc in enumerate(documents):
        doc_id = doc.get("document_id", f"doc_{i:03d}")
        entity_count = len(doc.get("entities", []))
        entries.append(AuditEntry(
            timestamp=ts(40 - i * 3),
            module="extractor",
            action=f"Extracted {entity_count} entities from {doc_id} via Gemini Vision",
            confidence=0.93,
            outcome="accepted",
        ))

    # Normalization
    entries.append(AuditEntry(
        timestamp=ts(25),
        module="normalizer",
        action="Canonicalized weights to kg, volumes to cbm, dates to ISO 8601",
        confidence=None,
        outcome="normalized",
    ))

    # Rule evaluation
    entries.append(AuditEntry(
        timestamp=ts(15),
        module="rule_evaluator",
        action="Evaluated MUST_MATCH constraints across knowledge graph edges",
        confidence=None,
        outcome="evaluation_complete",
    ))

    entries.append(AuditEntry(
        timestamp=ts(12),
        module="rule_evaluator",
        action="GROSS_WEIGHT discrepancy detected: Invoice=450.0 kg vs AWB=448.5 kg (delta=+1.5 kg)",
        confidence=0.87,
        outcome="conflict_detected",
    ))

    # XAI compilation
    entries.append(AuditEntry(
        timestamp=ts(8),
        module="xai_compiler",
        action="Compiled 4-layer XAI payload: Provenance + Reasoning Chain + Confidence + Counterfactual",
        confidence=None,
        outcome="xai_generated",
    ))

    entries.append(AuditEntry(
        timestamp=ts(5),
        module="counterfactual",
        action="Generated resolution: Adjust AWB GROSS_WEIGHT by +1.5 kg to match Commercial Invoice",
        confidence=None,
        outcome="recommendation_generated",
    ))

    _registry[shipment_id] = entries
