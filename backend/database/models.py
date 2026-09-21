from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text
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
