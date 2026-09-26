import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDiscrepancies } from '../../utils/api';
import { useShipment } from '../../hooks/useShipment';

interface Props { onTriggerToast: (t: { title: string; message: string; type?: 'error' | 'info' | 'success' }) => void; }

interface XAIBlock {
  layer1: { source_documents: string[]; };
  layer2: { failed_rule_id: string; logical_steps: string[]; conclusion: string; };
  layer3: { overall_confidence: number; confidence_level: string; confidence_explanation: string; };
  layer4: { recommended_action: string; delta_required: string; };
}

interface DiscrepancySource {
  document_id: string;
  document_label: string;
  document_type: string;
  raw_value: string;
  normalized_value: string | number;
  page: number;
  bbox: number[];
  extraction_confidence: number;
}

interface ApiDiscrepancy {
  discrepancy_id: string;
  rule_id: string;
  severity: string;
  severity_score: number;
  status: string;
  field: string;
  field_label: string;
  value_a: string;
  value_b: string;
  delta: string;
  sources: DiscrepancySource[];
  xai_block: XAIBlock;
}

export function ScreenDiscrepancies(_props: Props) {
  const navigate = useNavigate();
  const { shipmentId } = useShipment();
  const [discrepancies, setDiscrepancies] = useState<ApiDiscrepancy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const activeId = shipmentId ?? 'demo-shipment';

  useEffect(() => {
    setLoading(true);
    setError(null);
    getDiscrepancies(activeId)
      .then(res => {
        setDiscrepancies((res as unknown as { discrepancies: ApiDiscrepancy[] }).discrepancies ?? []);
      })
      .catch(err => {
        setError(err.message || 'Failed to load discrepancies from backend.');
      })
      .finally(() => setLoading(false));
  }, [activeId]);

  const handleResolve = () => {
    navigate('/review-workspace');
  };

  const filtered = discrepancies.filter(d => {
    const matchesCat = filter === 'all' || d.severity === filter;
    const matchesSearch = (d.field_label || d.field || d.rule_id).toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.rule_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.delta.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="w-full max-w-6xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-5">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary">
            <span>Pre-filing review</span>
            {!loading && <span className="px-2 py-0.5 rounded-full bg-error-container/30 text-error text-[10px]">{discrepancies.length} needs review</span>}
          </div>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">Discrepancies</h1>
          <p className="text-xs md:text-sm text-on-surface-variant max-w-xl mt-1">
            Resolve differences in CUSDEC fields before preparing the declaration.
          </p>
        </div>
        <button
          onClick={() => { setLoading(true); getDiscrepancies(activeId).then(r => setDiscrepancies((r as unknown as { discrepancies: ApiDiscrepancy[] }).discrepancies ?? [])).finally(() => setLoading(false)); }}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary text-white text-xs font-semibold hover:bg-primary-container shadow-sm transition-all"
        >
          <span className="material-symbols-outlined text-[16px]">sync</span>
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-surface-container-lowest px-3 py-2 rounded-xl border border-outline-variant/20 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-1">
          {[['all', 'All'], ['high', 'High Severity'], ['medium', 'Medium']].map(([cat, label]) => (
            <button key={cat} onClick={() => setFilter(cat)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${filter === cat ? 'bg-primary text-white' : 'text-on-surface-variant hover:bg-surface-container'}`}>
              {label}
            </button>
          ))}
        </div>
        <div className="relative w-full sm:w-72">
          <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-outline text-[16px]">search</span>
          <input type="text" placeholder="Search field, rule, variance..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-surface-container-low rounded-lg text-xs text-on-surface placeholder:text-outline focus:outline-none" />
        </div>
      </div>

      {/* Content */}
      {loading && (
        <div className="flex flex-col gap-3">
          {[1, 2].map(i => (
            <div key={i} className="h-32 rounded-xl bg-surface-container-lowest animate-pulse border border-outline-variant/20"></div>
          ))}
        </div>
      )}

      {error && (
        <div className="bg-error/10 border border-error/30 rounded-xl p-6 text-center">
          <span className="material-symbols-outlined text-error text-[32px]">error</span>
          <p className="text-sm text-on-surface mt-2 font-semibold">Failed to load discrepancies</p>
          <p className="text-xs text-on-surface-variant mt-1">{error}</p>
          <p className="text-xs text-on-surface-variant mt-3">Make sure the backend is running: <code className="font-mono bg-surface-container px-1 rounded">uvicorn main:app --reload</code></p>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="bg-surface-container-lowest rounded-xl p-10 text-center border border-outline-variant/20">
          <span className="material-symbols-outlined text-secondary text-[40px]">check_circle</span>
          <p className="text-sm font-semibold text-on-surface mt-2">No Discrepancies Found</p>
          <p className="text-xs text-on-surface-variant mt-1">All cross-document fields are consistent.</p>
        </div>
      )}

      {!loading && !error && (
        <div className="space-y-4">
          {filtered.map(item => {
            const xai = item.xai_block;
            const sources = item.sources?.length ? item.sources : [
              { document_id: '', document_label: xai.layer1.source_documents[0] || 'Source A', document_type: 'unknown', raw_value: item.value_a, normalized_value: item.value_a, page: 1, bbox: [], extraction_confidence: 0 },
              { document_id: '', document_label: xai.layer1.source_documents[1] || 'Source B', document_type: 'unknown', raw_value: item.value_b, normalized_value: item.value_b, page: 1, bbox: [], extraction_confidence: 0 },
            ];
            const isExpanded = expandedId === item.discrepancy_id;
            const isResolved = false;
            return (
              <div key={item.discrepancy_id} className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/20 overflow-hidden border-l-4 border-l-error">
                {/* Header row */}
                <div className="bg-primary/5 px-4 py-2.5 flex flex-wrap items-center justify-between gap-2 border-b border-outline-variant/20 text-xs">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${isResolved ? 'bg-secondary' : 'bg-error'}`}></span>
                    <span className="font-bold text-on-surface">{item.field_label || item.field}</span>
                    <span className="text-outline">requires review</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded-full font-semibold text-[10px] uppercase ${isResolved ? 'bg-secondary-container/30 text-secondary' : 'bg-primary-fixed text-primary'}`}>
                      {isResolved ? 'Reviewed' : 'Open'}
                    </span>
                  </div>
                </div>

                {/* Main body */}
                <div className="p-4 flex flex-col gap-4 text-xs">
                  <div className="space-y-3">
                    <div>
                      <div className="text-[10px] text-outline font-bold uppercase tracking-wider">Compare source values</div>
                      <p className="text-xs text-on-surface-variant mt-1">Check the original document before choosing the declaration value.</p>
                    </div>
                    {/* Values */}
                    <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr] gap-2 items-stretch">
                      {sources.map((source, index) => (
                        <button key={`${source.document_id}-${index}`} onClick={() => navigate('/review-workspace')} className="bg-surface-container-low hover:bg-surface-container p-3 rounded-lg text-left transition-colors">
                          <div className="text-[10px] text-outline uppercase truncate" title={source.document_label}>{source.document_label}</div>
                          <div className="text-base font-bold text-on-surface font-mono mt-1 break-all">{source.raw_value}</div>
                          <div className="text-[10px] text-primary mt-2 font-semibold">Review page {source.page}</div>
                        </button>
                      ))}
                      <div className="bg-error/10 border border-error/20 p-3 rounded-lg flex flex-col justify-center min-w-28">
                        <div className="text-[10px] text-error uppercase font-bold">Difference</div>
                        <div className="text-sm font-bold text-error font-mono mt-1">{item.delta}</div>
                      </div>
                    </div>

                    {/* XAI Layer 2 — Reasoning steps (expandable) */}
                    <div className="p-2.5 bg-surface-container rounded-lg">
                      <button className="flex items-center gap-2 w-full text-left" onClick={() => setExpandedId(isExpanded ? null : item.discrepancy_id)}>
                        <span className="material-symbols-outlined text-primary text-[16px]">account_tree</span>
                        <span className="font-semibold text-on-surface">Why this was flagged</span>
                        <span className="material-symbols-outlined text-outline text-[16px] ml-auto">{isExpanded ? 'expand_less' : 'expand_more'}</span>
                      </button>
                      {isExpanded && (
                        <div className="mt-2 space-y-1.5 pl-6 border-l-2 border-primary/30">
                          {xai.layer2.logical_steps.map((step, i) => (
                            <div key={i} className="flex items-start gap-1.5">
                              <span className="text-primary font-mono text-[10px] shrink-0 mt-0.5">S{i + 1}</span>
                              <span className="text-on-surface-variant">{step}</span>
                            </div>
                          ))}
                          <div className="flex items-start gap-1.5 pt-1">
                            <span className="text-secondary font-mono text-[10px] shrink-0 mt-0.5">∴</span>
                            <span className="text-secondary font-semibold">{xai.layer2.conclusion}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* XAI Layer 4 — Counterfactual */}
                  <div className="bg-surface-container-low/50 p-3 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <div className="text-[10px] font-bold text-primary uppercase flex items-center gap-1">
                        <span className="material-symbols-outlined text-[14px]">auto_awesome</span> Suggested next step
                      </div>
                      <div className="mt-1 font-mono text-[11px] text-on-surface bg-surface-container-lowest p-2 rounded border border-outline-variant/30 leading-relaxed">
                        {xai.layer4.recommended_action}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button onClick={handleResolve}
                        className="flex-1 py-2 px-3 rounded-lg font-semibold flex items-center justify-center gap-1.5 transition-all shadow-sm text-xs bg-primary text-white hover:bg-primary/90">
                        <span className="material-symbols-outlined text-[16px]">rule</span>
                        <span>Resolve in workspace</span>
                      </button>
                      <button onClick={() => navigate('/knowledge-graph')} className="px-3 py-2 rounded-lg bg-surface-container text-on-surface hover:bg-surface-variant font-medium text-xs">Graph</button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
