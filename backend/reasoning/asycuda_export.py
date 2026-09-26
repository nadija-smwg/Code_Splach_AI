"""Guard for the future ASYCUDA XML serializer.

The previous implementation emitted a custom XML shape with invented defaults
and labelled it as a CUSDEC. That is unsafe for a customs declaration. This
module deliberately refuses generation until an official message schema and a
schema-backed serializer are added.
"""
from __future__ import annotations

import networkx as nx


class CusdecExportError(RuntimeError):
    """Raised when a submission-ready CUSDEC cannot be generated safely."""


def generate_cusdec_xml(graph: nx.Graph, shipment_id: str) -> str:
    """Refuse to produce non-validated XML that could be submitted as CUSDEC."""
    del graph, shipment_id
    raise CusdecExportError(
        "An official ASYCUDA XML schema and serializer must be configured before CUSDEC export is enabled."
    )
