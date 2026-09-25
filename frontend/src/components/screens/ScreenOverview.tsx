import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listDossiers } from '../../utils/api';
import { useShipment } from '../../hooks/useShipment';

interface Props { onTriggerToast: (t: { title: string; message: string; type?: 'error' | 'info' | 'success' }) => void; }

interface DossierDoc {
  document_id: string;
  original_name: string;
  document_type: string | null;
  status: string;
}

interface DossierItem {
  dossier_id: string;
  status: string;
  created_at: string | null;
  document_count: number;
  documents: DossierDoc[];
}

const NAVY = '#0d1b3e';

function statusBadge(status: string) {
  switch (status) {
    case 'done':
      return { label: 'Completed', bg: 'bg-green-500/20', text: 'text-green-400', dot: 'bg-green-400' };
    case 'processing':
      return { label: 'Processing', bg: 'bg-amber-500/20', text: 'text-amber-400', dot: 'bg-amber-400 animate-pulse' };
    case 'error':
      return { label: 'Error', bg: 'bg-red-500/20', text: 'text-red-400', dot: 'bg-red-400' };
    default:
      return { label: 'Pending', bg: 'bg-gray-500/20', text: 'text-gray-400', dot: 'bg-gray-400' };
  }
}

function channelBadge(channel: string) {
  switch (channel) {
    case 'green':
      return { label: 'Green Lane', bg: 'bg-green-500/15', text: 'text-green-400', dot: 'bg-green-400' };
    case 'review':
      return { label: 'Under Review', bg: 'bg-amber-500/15', text: 'text-amber-400', dot: 'bg-amber-400' };
    case 'hold':
      return { label: 'Customs Hold', bg: 'bg-red-500/15', text: 'text-red-400', dot: 'bg-red-400' };
    default:
      return { label: 'Queued', bg: 'bg-gray-500/15', text: 'text-gray-400', dot: 'bg-gray-400' };
  }
}

export function ScreenOverview({ onTriggerToast }: Props) {
  const navigate = useNavigate();
  const { setShipmentId } = useShipment();
  const [dossiers, setDossiers] = useState<DossierItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [channelOverrides, setChannelOverrides] = useState<Record<string, string>>({});

  const fetchDossiers = () => {
    setLoading(true);
    listDossiers()
      .then(res => setDossiers(res.dossiers || []))
      .catch(() => setDossiers([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchDossiers(); }, []);

  const handleInspect = (dossierId: string) => {
    setShipmentId(dossierId);
    navigate('/discrepancies');
  };

  const getChannel = (d: DossierItem): string => {
    if (channelOverrides[d.dossier_id]) return channelOverrides[d.dossier_id];
    return d.status === 'done' ? 'green' : d.status === 'error' ? 'hold' : d.status === 'processing' ? 'review' : 'pending';
  };

  const toggleChannel = (dossierId: string, currentChannel: string) => {
    const next = currentChannel === 'green' ? 'review' : 'green';
    setChannelOverrides(prev => ({ ...prev, [dossierId]: next }));
    onTriggerToast({
      title: 'Clearance Channel Updated',
      message: `Dossier ${dossierId.slice(0, 8)}... → ${next === 'green' ? 'Green Lane' : 'Under Review'}.`,
      type: next === 'green' ? 'success' : 'info',
    });
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      {/* ── Hero Banner ───────────────────────────────────────────── */}
      <section className="relative w-full rounded-xl overflow-hidden shadow-sm bg-surface-container">
        <div className="relative w-full min-h-[360px] md:min-h-[380px] flex flex-col justify-end p-6 md:p-10">
          <img alt="ClearanceX Intelligence Hub" className="absolute inset-0 w-full h-full object-cover object-center"
            src="/screen.png" />
          <div className="absolute inset-0 bg-gradient-to-t from-on-surface/90 via-on-surface/50 to-transparent"></div>
          <div className="absolute inset-0" style={{ backgroundColor: 'rgba(13,27,62,0.15)' }}></div>
          <div className="relative z-10 max-w-4xl flex flex-col gap-4">
            {/* System Status */}
            <div className="inline-flex items-center self-start gap-2 bg-surface-container-lowest/90 backdrop-blur-md px-3 py-1 rounded-full shadow-sm text-xs">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-secondary"></span>
              </span>
              <span className="text-secondary font-semibold uppercase tracking-wider">System Online</span>
              <span className="text-outline">•</span>
              <span className="text-on-surface-variant font-mono">ASYCUDA Connected</span>
            </div>

            {/* Title */}
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
                Clearance<span style={{ color: '#5b8fd4', fontWeight: 900 }}>X</span> Intelligence Hub
              </h1>
              <p className="text-white/90 text-sm md:text-base max-w-2xl mt-1 leading-relaxed">
                AI-powered customs document verification &amp; ASYCUDA clearance pipeline for Sri Lankan apparel &amp; transshipment exports.
              </p>
            </div>

            {/* Buttons */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button onClick={() => navigate('/dossiers')}
                style={{ backgroundColor: NAVY }}
                className="inline-flex items-center justify-center gap-2.5 text-white px-7 py-3 rounded-lg text-sm font-semibold shadow-lg hover:opacity-90 transition-all active:scale-95">
                <span className="material-symbols-outlined text-[20px]">add</span>
                <span>+ Ingest New Dossier</span>
              </button>
              <button onClick={() => onTriggerToast({ title: 'Batch Manifest Assembled', message: 'Downloading encrypted EDIFACT XML package for active export cycle.' })}
                className="inline-flex items-center justify-center gap-2.5 bg-surface-container-lowest/90 hover:bg-surface-container-lowest text-on-surface px-7 py-3 rounded-lg text-sm font-semibold shadow-sm transition-all">
                <span className="material-symbols-outlined text-[20px] text-on-surface-variant">file_download</span>
                <span>Download Batch Manifest</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── Active Consignment Pipeline ────────────────────────────── */}
      <section
        className="rounded-xl shadow-md overflow-hidden"
        style={{ background: `linear-gradient(145deg, ${NAVY}0A 0%, ${NAVY}05 100%)`, border: `1.5px solid ${NAVY}20` }}
      >
        <div className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3" style={{ borderBottom: `1px solid ${NAVY}18` }}>
          <div>
            <h2 className="text-base font-semibold text-on-surface">Active Consignment Pipeline</h2>
            <p className="text-xs text-outline">Live dossier tracking &amp; clearance channel management</p>
          </div>
          <button onClick={fetchDossiers}
            style={{ backgroundColor: NAVY }}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-white text-xs font-semibold transition-all hover:opacity-90">
            <span className="material-symbols-outlined text-[15px]">sync</span>
            <span>Refresh</span>
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="p-6 space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 rounded-lg bg-surface-container-lowest animate-pulse"></div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && dossiers.length === 0 && (
          <div className="p-10 text-center">
            <span className="material-symbols-outlined text-[44px] text-outline">inbox</span>
            <p className="text-sm font-semibold text-on-surface mt-3">No Consignments Yet</p>
            <p className="text-xs text-on-surface-variant mt-1 max-w-md mx-auto">
              Upload your first shipping dossier to begin automated document cross-examination.
            </p>
            <button onClick={() => navigate('/dossiers')}
              style={{ backgroundColor: NAVY }}
              className="mt-4 inline-flex items-center gap-2 text-white px-5 py-2.5 rounded-lg text-xs font-semibold shadow-sm hover:opacity-90 transition-all">
              <span className="material-symbols-outlined text-[16px]">add</span>
              <span>Ingest First Dossier</span>
            </button>
          </div>
        )}

        {/* Table */}
        {!loading && dossiers.length > 0 && (
          <>
            <div className="w-full overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-surface-container-low text-outline font-semibold uppercase tracking-wider">
                    <th className="py-3 px-4">Consignment ID</th>
                    <th className="py-3 px-4">Documents</th>
                    <th className="py-3 px-4">AI Status</th>
                    <th className="py-3 px-4">Clearance Channel</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-container-high/30">
                  {dossiers.map(d => {
                    const sb = statusBadge(d.status);
                    const channel = getChannel(d);
                    const cb = channelBadge(channel);
                    return (
                      <tr key={d.dossier_id} className="hover:bg-surface-container-low/50 transition-colors">
                        {/* Consignment ID */}
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-1.5">
                            <span className="material-symbols-outlined text-[16px] text-outline">inventory</span>
                            <span className="font-semibold text-on-surface font-mono">CLX-{d.dossier_id.slice(0, 8).toUpperCase()}</span>
                          </div>
                          <span className="text-[11px] text-outline font-mono">
                            {d.created_at ? new Date(d.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                          </span>
                        </td>

                        {/* Documents */}
                        <td className="py-3.5 px-4">
                          <div className="space-y-0.5">
                            {d.documents.slice(0, 3).map(doc => (
                              <div key={doc.document_id} className="flex items-center gap-1 text-[11px]">
                                <span className="material-symbols-outlined text-[13px] text-outline">description</span>
                                <span className="text-on-surface-variant truncate max-w-[180px]">{doc.original_name}</span>
                              </div>
                            ))}
                            {d.documents.length > 3 && (
                              <span className="text-[10px] text-outline">+{d.documents.length - 3} more</span>
                            )}
                          </div>
                          <span className="inline-flex items-center gap-1 mt-1 px-2 py-0.5 rounded bg-surface-container font-mono text-on-surface-variant text-[10px]">
                            <span className="material-symbols-outlined text-[12px]">description</span> {d.document_count} doc{d.document_count !== 1 ? 's' : ''}
                          </span>
                        </td>

                        {/* AI Status */}
                        <td className="py-3.5 px-4">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full font-semibold text-[11px] ${sb.bg} ${sb.text}`}>
                            <span className={`h-1.5 w-1.5 rounded-full ${sb.dot}`}></span> {sb.label}
                          </span>
                        </td>

                        {/* Clearance Channel */}
                        <td className="py-3.5 px-4">
                          <button
                            onClick={() => toggleChannel(d.dossier_id, channel)}
                            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold cursor-pointer hover:opacity-80 transition-opacity ${cb.bg} ${cb.text}`}
                            title="Click to toggle clearance channel"
                          >
                            <span className={`h-1.5 w-1.5 rounded-full ${cb.dot}`}></span>
                            {cb.label}
                            <span className="material-symbols-outlined text-[12px]">swap_horiz</span>
                          </button>
                        </td>

                        {/* Actions */}
                        <td className="py-3.5 px-4 text-right">
                          <button onClick={() => handleInspect(d.dossier_id)}
                            style={{ backgroundColor: NAVY }}
                            className="inline-flex items-center gap-1 text-white px-3 py-1.5 rounded-lg font-medium text-[11px] transition-all hover:opacity-90">
                            <span>Inspect</span>
                            <span className="material-symbols-outlined text-[15px]">chevron_right</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="p-3 bg-surface-container-low/50 flex flex-col sm:flex-row items-center justify-between text-xs text-outline" style={{ borderTop: `1px solid ${NAVY}18` }}>
              <span>Showing {dossiers.length} consignment{dossiers.length !== 1 ? 's' : ''}</span>
              <div className="flex items-center gap-1.5 text-secondary">
                <span className="h-2 w-2 rounded-full bg-secondary"></span>
                <span>Pipeline Active</span>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
