from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Shipment(Base):
    __tablename__ = 'shipments'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), default='uploaded')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Document(Base):
    __tablename__ = 'documents'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey('shipments.id', ondelete='CASCADE'))
    filename = Column(String(255), nullable=False)
    document_type = Column(String(50))
    classification_confidence = Column(Float)
    classification_evidence = Column(JSONB, default=[])
    file_path = Column(String(500), nullable=False)
    page_count = Column(Integer, default=1)
    status = Column(String(20), default='pending') # Your custom status column!
    created_at = Column(DateTime, server_default=func.now())

class Extraction(Base):
    __tablename__ = 'extractions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'))
    entity_type = Column(String(50), nullable=False)
    raw_value = Column(Text)
    normalized_value = Column(Text)
    unit = Column(String(20))
    page = Column(Integer, default=1)
    bbox = Column(JSONB)
    extraction_confidence = Column(Float)
    classification_confidence = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

class Discrepancy(Base):
    __tablename__ = 'discrepancies'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey('shipments.id', ondelete='CASCADE'))
    field = Column(String(50), nullable=False)
    severity = Column(String(10), default='medium')
    severity_score = Column(Float, default=0.5)
    sources = Column(JSONB, nullable=False)
    reasoning_chain = Column(JSONB)
    confidence = Column(JSONB)
    counterfactual = Column(JSONB)
    status = Column(String(20), default='open')
    resolved_value = Column(Text)
    resolved_by = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey('shipments.id', ondelete='CASCADE'))
    timestamp = Column(DateTime, server_default=func.now())
    module = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    reasoning = Column(Text)
    confidence = Column(Float)
    outcome = Column(String(50))
    details = Column(JSONB)

class Correction(Base):
    __tablename__ = 'corrections'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    extraction_id = Column(UUID(as_uuid=True), ForeignKey('extractions.id', ondelete='CASCADE'))
    original_value = Column(Text)
    corrected_value = Column(Text)
    reason = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────────────────────────────────────
# Phase 09 — Normalizer cache, Dossier upload tables
# Previously only defined in schema.sql; now added as SQLAlchemy models so
# Base.metadata.create_all() (called by init_db() on startup) creates them
# automatically in a fresh environment — no manual psql step needed.
# ─────────────────────────────────────────────────────────────────────────────

class NormCache(Base):
    __tablename__ = 'norm_cache'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(255), nullable=False, unique=True)
    entity_type = Column(String(50), nullable=False)
    raw_value = Column(Text, nullable=False)
    canonical = Column(Text, nullable=False)
    source = Column(String(20), nullable=False, default='llm')
    hit_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), server_default=func.now())


class Dossier(Base):
    """One dossier = one shipment upload (groups 1-N documents)."""
    __tablename__ = 'dossiers'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), nullable=False, default='pending')


class DossierDocument(Base):
    """One row per PDF file within a dossier."""
    __tablename__ = 'dossier_documents'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dossier_id = Column(UUID(as_uuid=True), ForeignKey('dossiers.id', ondelete='CASCADE'), nullable=False)
    original_name = Column(Text, nullable=False)
    file_path = Column(Text, nullable=False)
    document_type = Column(String(50))
    status = Column(String(20), nullable=False, default='pending')
    error_message = Column(Text)
    extraction_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class FieldResolution(Base):
    """A reviewer-approved override for one canonical shipment field."""
    __tablename__ = 'field_resolutions'
    __table_args__ = (UniqueConstraint('shipment_id', 'canonical_field_id', name='uq_field_resolution'),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(String(100), nullable=False)
    canonical_field_id = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)
    resolved_value = Column(JSONB, nullable=False)
    source_assertion_id = Column(String(255))
    reason = Column(Text)
    resolved_by = Column(String(100), nullable=False, default='reviewer')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DeclarationMetadata(Base):
    """Reviewer-entered declaration details required in addition to source documents."""
    __tablename__ = 'declaration_metadata'
    __table_args__ = (UniqueConstraint('shipment_id', 'field_name', name='uq_declaration_metadata'),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(String(100), nullable=False)
    field_name = Column(String(50), nullable=False)
    value = Column(Text, nullable=False)
    updated_by = Column(String(100), nullable=False, default='reviewer')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

