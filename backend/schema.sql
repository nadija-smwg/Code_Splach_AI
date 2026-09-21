CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Core shipment table
CREATE TABLE shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(20) DEFAULT 'uploaded',
    -- Status flow: uploaded → processing → completed → error
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Individual documents within a shipment
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id UUID REFERENCES shipments(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    document_type VARCHAR(50),
    classification_confidence FLOAT,
    classification_evidence JSONB DEFAULT '[]',
    file_path VARCHAR(500) NOT NULL,
    page_count INT DEFAULT 1,
    status VARCHAR(20) DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT NOW()
);

-- Extracted entities from each document
CREATE TABLE extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    raw_value TEXT,
    normalized_value TEXT,
    unit VARCHAR(20),
    page INT DEFAULT 1,
    bbox JSONB,                    -- [x1, y1, x2, y2]
    extraction_confidence FLOAT,
    classification_confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Detected discrepancies across documents
CREATE TABLE discrepancies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id UUID REFERENCES shipments(id) ON DELETE CASCADE,
    field VARCHAR(50) NOT NULL,
    severity VARCHAR(10) DEFAULT 'medium',
    severity_score FLOAT DEFAULT 0.5,
    sources JSONB NOT NULL,        -- Array of source references
    reasoning_chain JSONB,         -- Layer 2
    confidence JSONB,              -- Layer 3 decomposed
    counterfactual JSONB,          -- Layer 4
    status VARCHAR(20) DEFAULT 'open',
    -- Status: open → resolved → accepted → overridden
    resolved_value TEXT,
    resolved_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Immutable audit trail (Layer 5)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id UUID REFERENCES shipments(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT NOW(),
    module VARCHAR(50) NOT NULL,   -- 'classifier', 'extractor', 'reconciler', 'user'
    action VARCHAR(100) NOT NULL,
    reasoning TEXT,
    confidence FLOAT,
    outcome VARCHAR(50),
    details JSONB
);

-- Human corrections (for future active learning)
CREATE TABLE corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id UUID REFERENCES extractions(id) ON DELETE CASCADE,
    original_value TEXT,
    corrected_value TEXT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_documents_shipment ON documents(shipment_id);
CREATE INDEX idx_extractions_document ON extractions(document_id);
CREATE INDEX idx_extractions_entity_type ON extractions(entity_type);
CREATE INDEX idx_discrepancies_shipment ON discrepancies(shipment_id);
CREATE INDEX idx_audit_logs_shipment ON audit_logs(shipment_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);