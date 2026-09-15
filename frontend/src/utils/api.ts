// frontend/src/utils/api.ts
import axios from 'axios';
import type {
  UploadResponse, ShipmentStatus, DocumentExtraction,
  GraphData, Discrepancy, AuditEntry,
} from '../types';
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});
export async function uploadShipment(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  const { data } = await api.post<UploadResponse>('/shipments/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
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
export async function getAuditTrail(id: string): Promise<{ shipment_id: string; entries: AuditEntry[] }> {
  const { data } = await api.get(`/shipments/${id}/audit-trail`);
  return data;
}
export async function exportAsycuda(id: string): Promise<Blob> {
  const { data } = await api.get(`/shipments/${id}/asycuda-export`, {
    responseType: 'blob',
  });
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
