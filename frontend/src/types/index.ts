// frontend/src/types/index.ts

// ============================================
// ENTITY & EXTRACTION
// ============================================
export interface Entity {
  entity_type: string;
  value: string;
  normalized_value: number | string;
  unit: string | null;
  page: number;
  bbox: number[];                   // [x1, y1, x2, y2]
  extraction_confidence: number;    // 0.0–1.0
  classification_confidence: number;
}

export interface DocumentExtraction {
  document_id: string;
  document_type: DocumentType;
  classification_confidence: number;
  entities: Entity[];
}

export type DocumentType =
  | 'commercial_invoice'
  | 'packing_list'
  | 'awb'
  | 'bl'
  | 'freight_invoice'
  | 'delivery_order'
  | 'letter_of_credit'
  | 'unknown';

// ============================================
// DISCREPANCY & XAI LAYERS
// ============================================
export interface DiscrepancySource {
  document_id: string;
  document_type: string;
  value: string;
  page: number;
  bbox: number[];
}

export interface ReasoningChain {
  steps: string[];
  conclusion: string;
}

export interface DecomposedConfidence {
  extraction: number;
  classification: number;
  matching: number;
  overall: number;
  explanation?: string;
  level?: 'green' | 'yellow' | 'red';
}

export interface Counterfactual {
  options: string[];
  recommendation: string;
}

export interface Discrepancy {
  discrepancy_id: string;
  field: string;
  severity: 'high' | 'medium' | 'low';
  severity_score: number;
  status: 'open' | 'resolved' | 'accepted' | 'overridden';
  sources: DiscrepancySource[];
  reasoning_chain: ReasoningChain;
  confidence: DecomposedConfidence;
  counterfactual: Counterfactual;
}

// ============================================
// KNOWLEDGE GRAPH
// ============================================
export interface GraphNode {
  id: string;
  label: string;
  type: 'document' | 'entity';
  color: string | { background: string; border: string };
  status?: 'conflict' | 'match' | 'warning' | 'pending';
  document_type?: string;
  size?: number;
  shape?: string;
  shadow?: boolean;
  font?: { color: string };
}

export interface GraphEdge {
  from: string;
  to: string;
  label: string;
  confidence: number;
  width?: number;
  color?: { color: string };
  font?: { color: string; size: number };
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ============================================
// SHIPMENT
// ============================================
export interface ShipmentDocument {
  document_id: string;
  filename: string;
  document_type: DocumentType;
  classification_confidence: number;
}

export interface ShipmentStatus {
  shipment_id: string;
  status: 'uploaded' | 'processing' | 'completed' | 'error';
  progress: number;
  documents: ShipmentDocument[];
  processing_time_ms: number;
}

export interface UploadResponse {
  shipment_id: string;
  status: string;
  // Legacy /shipments/upload shape
  documents?: { document_id: string; filename: string; status: string }[];
  // Dossier /api/upload shape
  document_count?: number;
  document_ids?: string[];
  status_url?: string;
}

// ============================================
// AUDIT TRAIL
// ============================================
export interface AuditEntry {
  timestamp: string;
  module: string;
  action: string;
  reasoning?: string;
  confidence: number | null;
  outcome: string;
  details?: Record<string, unknown>;
}

// ============================================
// HELPER FUNCTIONS
// ============================================
export type ConfidenceLevel = 'green' | 'yellow' | 'red';

export function getConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= 0.9) return 'green';
  if (score >= 0.7) return 'yellow';
  return 'red';
}

export function getConfidenceColor(level: ConfidenceLevel): string {
  switch (level) {
    case 'green':  return '#10b981';
    case 'yellow': return '#f59e0b';
    case 'red':    return '#ef4444';
  }
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'high':   return '#ef4444';
    case 'medium': return '#f59e0b';
    case 'low':    return '#6366f1';
    default:       return '#94a3b8';
  }
}

export function getDocTypeLabel(type: DocumentType): string {
  const labels: Record<string, string> = {
    commercial_invoice: 'Commercial Invoice',
    packing_list:       'Packing List',
    awb:                'Air Waybill',
    bl:                 'Bill of Lading',
    freight_invoice:    'Freight Invoice',
    delivery_order:     'Delivery Order',
    letter_of_credit:   'Letter of Credit',
    unknown:            'Unknown',
  };
  return labels[type] || type;
}

export function getDocTypeColor(type: DocumentType): string {
  const colors: Record<string, string> = {
    commercial_invoice: '#4A90D9',
    packing_list:       '#50C878',
    awb:                '#FFB347',
    bl:                 '#DDA0DD',
    freight_invoice:    '#F0E68C',
    delivery_order:     '#87CEEB',
    letter_of_credit:   '#CD853F',
    unknown:            '#CCCCCC',
  };
  return colors[type] || '#CCCCCC';
}
