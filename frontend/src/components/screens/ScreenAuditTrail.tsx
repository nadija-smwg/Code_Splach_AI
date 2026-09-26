import { useState, useEffect } from 'react';
import { getAuditTrail } from '../../utils/api';
import { useShipment } from '../../hooks/useShipment';
import type { AuditEntry } from '../../types';

interface Props { onTriggerToast: (t: { title: string; message: string; type?: 'error' | 'info' | 'success' }) => void; }

const MODULE_ICON: Record<string, string> = {
  classifier:     'category',
  extractor:      'manage_search',
  normalizer:     'tune',
  rule_evaluator: 'account_tree',
  xai_compiler:   'layers',
  counterfactual: 'lightbulb',
};

const OUTCOME_STYLE: Record<string, string> = {
  accepted:              'bg-secondary-container/30 text-secondary',
  normalized:            'bg-secondary-container/20 text-secondary',
  evaluation_complete:   'bg-primary-fixed text-primary',
  conflict_detected:     'bg-red-500/20 text-red-400',
  xai_generated:         'bg-purple-500/20 text-purple-400',
  recommendation_generated: 'bg-amber-500/20 text-amber-400',
};

export function ScreenAuditTrail({ onTriggerToast }: Props) {
  const { shipmentId } = useShipment();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  const activeId = shipmentId ?? 'demo-shipment';

  useEffect(() => {
    setLoading(true);
    setError(null);
    getAuditTrail(activeId)
      .then(res => {
        setEntries(res.entries as AuditEntry[]);
        if (res.entries.length > 0) setSelectedIdx(0);
      })
      .catch(err => setError(err.message || 'Failed to load audit trail.'))
      .finally(() => setLoading(false));
  }, [activeId]);

  const handleExport = () => {
    const blob = new Blob([JSON.stringify({ shipment_id: activeId, entries }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `audit_trail_${activeId.slice(0, 8)}.json`;
    a.click(); URL.revokeObjectURL(url);
    onTriggerToast({ title: 'Audit trail exported', message: 'The audit trail was downloaded as JSON.', type: 'success' });
  };

  const selected = selectedIdx !== null ? entries[selectedIdx] : null;

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="text-xs text-primary font-semibold">Review history</div>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">Audit trail</h1>
          <p className="text-xs md:text-sm text-on-surface-variant mt-1">
            A timestamped record of document processing, field resolution, and discrepancy review.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onTriggerToast({ title: 'Audit trail checked', message: 'The displayed events are available for export.' })}
            className="px-3 py-2 rounded-lg bg-surface-container-lowest hover:bg-surface-container text-xs font-semibold flex items-center gap-1.5 border border-outline-variant/30 shadow-sm"
          >
            <span className="material-symbols-outlined text-secondary text-[16px]">verified_user</span>
            <span>Check audit trail</span>
          </button>
          <button onClick={handleExport}
            className="px-3 py-2 rounded-lg bg-primary text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm">
            <span className="material-symbols-outlined text-[16px]">download</span>
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start text-xs">
        {/* Event Table */}
        <div className="xl:col-span-8 bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/20 overflow-hidden flex flex-col">
          <div className="p-3 bg-surface-container-low flex items-center justify-between font-bold border-b border-outline-variant/20">
            <span>Recorded events</span>
            <span className="font-mono text-outline font-normal">{entries.length} events</span>
          </div>

          {loading && (
            <div className="p-8 flex items-center justify-center gap-3 text-on-surface-variant">
              <span className="material-symbols-outlined animate-spin text-primary">sync</span>
              <span>Loading audit trail...</span>
            </div>
          )}

          {error && (
            <div className="p-8 text-center">
              <span className="material-symbols-outlined text-error text-[32px]">error</span>
              <p className="text-sm text-on-surface mt-2">{error}</p>
            </div>
          )}

          {!loading && !error && (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-surface-container-low text-outline uppercase font-semibold text-[10px]">
                    <th className="py-2.5 px-3">Module</th>
                    <th className="py-2.5 px-3">Event</th>
                    <th className="py-2.5 px-3">Confidence</th>
                    <th className="py-2.5 px-3">Outcome</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-container-high/30">
                  {entries.map((row, idx) => (
                    <tr key={idx} onClick={() => setSelectedIdx(idx)}
                      className={`hover:bg-surface-container-low/60 cursor-pointer transition-colors ${selectedIdx === idx ? 'bg-primary/5' : ''}`}>
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-1.5">
                          <span className="material-symbols-outlined text-primary text-[14px]">{MODULE_ICON[row.module] || 'circle'}</span>
                          <span className="font-semibold font-mono text-primary">{row.module}</span>
                        </div>
                      </td>
                      <td className="py-3 px-3 text-on-surface max-w-xs truncate">{row.action}</td>
                      <td className="py-3 px-3 font-mono text-on-surface-variant">
                        {row.confidence != null ? `${Math.round(row.confidence * 100)}%` : '—'}
                      </td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded-full font-semibold text-[10px] ${OUTCOME_STYLE[row.outcome] || 'bg-surface-container text-outline'}`}>
                          {row.outcome}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Proof Certificate */}
        <div className="xl:col-span-4 bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-outline-variant/30 flex flex-col gap-4">
          <div className="border-b border-outline-variant/20 pb-2 flex items-center justify-between">
            <span className="font-bold text-on-surface">Event Detail</span>
            {selected && (
              <span className={`px-2 py-0.5 rounded bg-surface-container font-mono text-[10px] ${OUTCOME_STYLE[selected.outcome] || ''}`}>
                {selected.outcome}
              </span>
            )}
          </div>
          {selected ? (
            <div className="space-y-3">
              <div className="bg-surface-container-low p-2.5 rounded-lg space-y-1">
                <div className="text-[10px] text-outline uppercase">Module</div>
                <div className="font-bold text-primary font-mono">{selected.module}</div>
              </div>
              <div className="bg-surface-container-low p-2.5 rounded-lg space-y-1">
                <div className="text-[10px] text-outline uppercase">Timestamp</div>
                <div className="font-mono text-[11px] text-on-surface">{selected.timestamp}</div>
              </div>
              <div className="bg-surface-container-low p-2.5 rounded-lg space-y-1">
                <div className="text-[10px] text-outline uppercase">Action</div>
                <div className="text-on-surface leading-relaxed">{selected.action}</div>
              </div>
              {(selected as AuditEntry & { event_hash?: string }).event_hash && (
                <div>
                  <div className="text-[10px] text-outline uppercase mb-1">SHA-256 Event Hash</div>
                  <div className="p-2 bg-surface-container rounded font-mono text-[10px] break-all select-all text-on-surface">
                    {(selected as AuditEntry & { event_hash?: string }).event_hash}...
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 gap-2 text-on-surface-variant">
              <span className="material-symbols-outlined text-[32px] text-outline">touch_app</span>
              <p className="text-center text-[11px]">Select an event to view its detail and hash.</p>
            </div>
          )}
          <div className="p-2.5 bg-secondary-container/30 rounded-lg flex items-center gap-2">
            <span className="material-symbols-outlined text-secondary text-[20px]">workspace_premium</span>
            <div>
              <span className="font-bold block text-[11px]">Current dossier</span>
              <span className="text-outline text-[10px]">Shipment: {activeId.slice(0, 16)}...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
