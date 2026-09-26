import { useCallback, useEffect, useState } from 'react';
import { exportAsycuda, downloadBlob, getCusdecReadiness } from '../../utils/api';
import { useShipment } from '../../hooks/useShipment';
import type { CusdecReadiness } from '../../types';

interface Props {
  onTriggerToast: (t: { title: string; message: string; type?: 'error' | 'info' | 'success' }) => void;
}

const friendlyField = (field: string) => field
  .replace(/_/g, ' ')
  .replace(/\b\w/g, (letter) => letter.toUpperCase());

export function ScreenAsycudaGateway({ onTriggerToast }: Props) {
  const { shipmentId } = useShipment();
  const activeId = shipmentId ?? 'demo-shipment';
  const [readiness, setReadiness] = useState<CusdecReadiness | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const refreshReadiness = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      setReadiness(await getCusdecReadiness(activeId));
    } catch {
      setReadiness(null);
      setLoadError('CUSDEC readiness could not be checked. Process the dossier documents and try again.');
    } finally {
      setIsLoading(false);
    }
  }, [activeId]);

  useEffect(() => {
    void refreshReadiness();
  }, [refreshReadiness]);

  const handleDownloadCusdec = async () => {
    if (!readiness?.export_allowed) return;
    setIsDownloading(true);
    try {
      const blob = await exportAsycuda(activeId);
      downloadBlob(blob, `CUSDEC_${activeId.slice(0, 8)}.xml`);
      onTriggerToast({ title: 'CUSDEC XML downloaded', message: 'The declaration passed the readiness checks.', type: 'success' });
    } catch {
      onTriggerToast({ title: 'Export blocked', message: 'The declaration is not approved for XML export.', type: 'error' });
      void refreshReadiness();
    } finally {
      setIsDownloading(false);
    }
  };

  const isReady = readiness?.export_allowed === true;
  const visibleBlockers = readiness?.blockers.slice(0, 8) ?? [];

  return (
    <div className="w-full max-w-5xl mx-auto px-4 sm:px-8 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <p className="text-xs font-semibold text-primary uppercase tracking-wide">Declaration readiness</p>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">CUSDEC export</h1>
          <p className="text-sm text-on-surface-variant mt-1">Only validated declarations can be exported. Placeholder and demo values are never used.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => void refreshReadiness()} disabled={isLoading}
            className="px-3.5 py-2 rounded-lg border border-outline-variant text-on-surface hover:bg-surface-container-low text-xs font-semibold disabled:opacity-60">
            {isLoading ? 'Checking…' : 'Refresh checks'}
          </button>
          <button onClick={handleDownloadCusdec} disabled={!isReady || isDownloading}
            className="px-3.5 py-2 rounded-lg bg-primary text-white text-xs font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
            {isDownloading ? 'Preparing XML…' : 'Download CUSDEC XML'}
          </button>
        </div>
      </div>

      {loadError ? (
        <div className="rounded-xl border border-error/30 bg-error-container/20 p-5 text-sm text-on-surface">
          {loadError}
        </div>
      ) : (
        <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest shadow-sm overflow-hidden">
          <div className="p-5 border-b border-outline-variant/20 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className={`material-symbols-outlined text-[24px] ${isReady ? 'text-secondary' : 'text-error'}`}>
                {isReady ? 'verified' : 'gpp_maybe'}
              </span>
              <div>
                <h2 className="font-bold text-on-surface">{isLoading ? 'Checking declaration' : isReady ? 'Ready for export' : 'Export blocked'}</h2>
                <p className="text-xs text-on-surface-variant mt-0.5">
                  {isLoading ? 'Reviewing source evidence and declaration requirements.' : readiness?.notice}
                </p>
              </div>
            </div>
            {!isLoading && readiness && (
              <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${isReady ? 'bg-secondary-container/35 text-secondary' : 'bg-error-container/35 text-error'}`}>
                {isReady ? 'All checks passed' : `${readiness.blocker_count} item${readiness.blocker_count === 1 ? '' : 's'} need attention`}
              </span>
            )}
          </div>

          <div className="p-5 grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="md:col-span-2">
              <h3 className="text-sm font-bold text-on-surface">Required actions</h3>
              {isLoading ? (
                <div className="mt-3 text-sm text-on-surface-variant">Loading readiness results…</div>
              ) : visibleBlockers.length ? (
                <ul className="mt-3 divide-y divide-outline-variant/20 border border-outline-variant/20 rounded-lg overflow-hidden">
                  {visibleBlockers.map((blocker, index) => (
                    <li key={`${blocker.code}-${blocker.field}-${index}`} className="px-3.5 py-3 flex gap-3 bg-surface-container-low/30">
                      <span className="material-symbols-outlined text-error text-[18px] mt-0.5">error_outline</span>
                      <div>
                        <p className="text-sm font-semibold text-on-surface">{friendlyField(blocker.field)}</p>
                        <p className="text-xs text-on-surface-variant mt-0.5">{blocker.message}</p>
                        <p className="text-[11px] text-outline mt-1">Source: {blocker.source}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-3 text-sm text-secondary">No blocking issues were found.</p>
              )}
            </div>

            <aside className="rounded-lg bg-surface-container-low p-4">
              <h3 className="text-sm font-bold text-on-surface">Current dossier</h3>
              <dl className="mt-3 space-y-3 text-xs">
                <div>
                  <dt className="text-outline">Resolved fields</dt>
                  <dd className="font-semibold text-on-surface mt-0.5">{readiness?.resolved_field_count ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-outline">Required extracted fields</dt>
                  <dd className="font-semibold text-on-surface mt-0.5">{readiness?.required_extracted_field_count ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-outline">Dossier ID</dt>
                  <dd className="font-mono text-[11px] text-on-surface mt-0.5 break-all">{activeId}</dd>
                </div>
              </dl>
            </aside>
          </div>
        </div>
      )}
    </div>
  );
}
