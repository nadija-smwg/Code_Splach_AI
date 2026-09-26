// frontend/src/utils/api.ts
import axios from 'axios';
import type {
  UploadResponse, ShipmentStatus, DocumentExtraction,
  GraphData, Discrepancy, AuditEntry, KeyFieldResponse, CusdecReadiness,
} from '../types';
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});
export async function uploadShipment(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  // Override the default 'application/json' header — let axios auto-generate
  // the correct 'multipart/form-data' boundary for file uploads.
  const uploadHeaders = { headers: { 'Content-Type': undefined } };
  // Try the dossier upload endpoint first; fallback to legacy shipments/upload.
  try {
    const { data } = await api.post<UploadResponse>('/upload', formData, uploadHeaders);
    return data;
  } catch {
    const { data } = await api.post<UploadResponse>('/shipments/upload', formData, uploadHeaders);
    return data;
  }
}
export async function getShipmentStatus(id: string): Promise<ShipmentStatus> {
  const { data } = await api.get<ShipmentStatus>(`/shipments/${id}/status`);
  return data;
}
export async function getExtraction(id: string): Promise<{ shipment_id: string; documents: DocumentExtraction[] }> {
  const { data } = await api.get(`/shipments/${id}/extraction`);
  return data;
}
export async function getGraph(id: string): Promise<GraphData> {
  const { data } = await api.get<GraphData>(`/shipments/${id}/graph`);
  return data;
}
export async function getDiscrepancies(id: string): Promise<{ shipment_id: string; total_discrepancies: number; discrepancies: Discrepancy[] }> {
  const { data } = await api.get(`/shipments/${id}/discrepancies`);
  return data;
}
export async function getKeyFields(id: string): Promise<KeyFieldResponse> {
  const { data } = await api.get<KeyFieldResponse>(`/shipments/${id}/key-fields`);
  return data;
}
export async function getAuditTrail(id: string): Promise<{ shipment_id: string; total_events: number; entries: AuditEntry[] }> {
  const { data } = await api.get(`/shipments/${id}/audit-trail`);
  return data;
}
export async function exportAsycuda(id: string): Promise<Blob> {
  const { data } = await api.get(`/shipments/${id}/asycuda-export`, {
    responseType: 'blob',
  });
  return data;
}
export async function getCusdecReadiness(id: string): Promise<CusdecReadiness> {
  const { data } = await api.get<CusdecReadiness>(`/shipments/${id}/cusdec-readiness`);
  return data;
}
export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a);
  a.click(); a.remove();
  window.URL.revokeObjectURL(url);
}
export async function listDossiers(): Promise<{ dossiers: { dossier_id: string; status: string; created_at: string | null; document_count: number; documents: { document_id: string; original_name: string; document_type: string | null; status: string }[] }[] }> {
  const { data } = await api.get('/dossiers');
  return data;
}

export interface RuleCheck {
  id: string;
  label: string;
  description: string;
  status: string;
}

export async function getActiveRules(): Promise<RuleCheck[]> {
  const { data } = await api.get<RuleCheck[]>('/rules/active');
  return data;
}
export async function saveFieldResolution(
  shipmentId: string,
  resolution: {
    canonical_field_id: string;
    source_assertion_id?: string;
    manual_value?: string;
    reason?: string;
  },
): Promise<{ status: string; field: import('../types').ResolvedKeyField }> {
  const { data } = await api.post(`/shipments/${shipmentId}/field-resolutions`, resolution);
  return data;
}
