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

-- =====================================================================
-- Phase 09 — Canonical Normalization Cache (Tier 2)
-- Shared persistent cache for semantic entity canonicalization.
-- Replaces backend/data/norm_cache.json
-- =====================================================================
CREATE TABLE IF NOT EXISTS norm_cache (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Tier 1 deterministic key: "ENTITY_TYPE:sorted tokens"
    cache_key   VARCHAR(255) NOT NULL UNIQUE,

    entity_type VARCHAR(50)  NOT NULL,
    raw_value   TEXT         NOT NULL,
    canonical   TEXT         NOT NULL,

    -- 'rule' = deterministic pre-seed, 'llm' = Gemini output, 'manual' = human correction
    source      VARCHAR(20)  NOT NULL DEFAULT 'llm'
                    CHECK (source IN ('rule', 'llm', 'manual')),

    hit_count   INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_used   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_norm_cache_key
    ON norm_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_norm_cache_entity
    ON norm_cache(entity_type);
CREATE INDEX IF NOT EXISTS idx_norm_cache_last_used
    ON norm_cache(last_used);

-- Pre-seed common values to avoid unnecessary Gemini calls during demo
INSERT INTO norm_cache (cache_key, entity_type, raw_value, canonical, source) VALUES
    ('CONSIGNEE_NAME:burlington inc industries', 'CONSIGNEE_NAME', 'Burlington Industries Inc.', 'Burlington Industries Inc.', 'rule'),
    ('PORT_LOADING:cmb colombo',                 'PORT_LOADING',   'Colombo (CMB)',              'Colombo Port (LKCMB)',       'rule'),
    ('PORT_DISCHARGE:angeles lax los',           'PORT_DISCHARGE', 'Los Angeles (LAX)',          'Los Angeles (USLAX)',        'rule'),
    ('INCOTERM:fob',                             'INCOTERM',       'FOB',                        'FOB',                       'rule'),
    ('INCOTERM:cif',                             'INCOTERM',       'CIF',                        'CIF',                       'rule')
ON CONFLICT (cache_key) DO NOTHING;

-- =====================================================================
-- Phase 09 — Dossier Upload Tables
-- One dossier = one shipment upload (groups 1-N documents)
-- =====================================================================
CREATE TABLE IF NOT EXISTS dossiers (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at  TIMESTAMPTZ NOT NULL    DEFAULT NOW(),
    status      VARCHAR(20) NOT NULL    DEFAULT 'pending'
                    CHECK (status IN ('pending', 'processing', 'done', 'error'))
);

-- One row per PDF file within a dossier
CREATE TABLE IF NOT EXISTS dossier_documents (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    dossier_id      UUID        NOT NULL REFERENCES dossiers(id) ON DELETE CASCADE,
    original_name   TEXT        NOT NULL,
    file_path       TEXT        NOT NULL,

    -- Set by AI pipeline after classification
    document_type   VARCHAR(50),

    -- Lifecycle status
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'processing', 'done', 'error')),
    error_message   TEXT,

    -- Full ExtractionResult JSON stored here when status = 'done'
    extraction_json JSONB,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dossier_documents_dossier
    ON dossier_documents(dossier_id);
CREATE INDEX IF NOT EXISTS idx_dossier_documents_status
    ON dossier_documents(status);