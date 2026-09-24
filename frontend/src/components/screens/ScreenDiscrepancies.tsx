import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDiscrepancies } from '../../utils/api';
import { useShipment } from '../../hooks/useShipment';

interface Props { onTriggerToast: (t: { title: string; message: string; type?: 'error' | 'info' | 'success' }) => void; }

interface XAIBlock {
  layer2: { failed_rule_id: string; logical_steps: string[]; conclusion: string; };
  layer3: { overall_confidence: number; confidence_level: string; confidence_explanation: string; };
  layer4: { recommended_action: string; delta_required: string; };
}

interface ApiDiscrepancy {
  discrepancy_id: string;
  rule_id: string;
  severity: string;
  severity_score: number;
  status: string;
  value_a: string;
  value_b: string;
  delta: string;
  xai_block: XAIBlock;
}

function ConfidencePill({ level, score }: { level: string; score: number }) {
  const colors: Record<string, string> = {
    high: 'bg-green-500/20 text-green-400 border-green-500/30',
    medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    low: 'bg-red-500/20 text-red-400 border-red-500/30',
  };
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border uppercase ${colors[level] || colors.medium}`}>
      {Math.round(score * 100)}% {level}
    </span>
  );
}

export function ScreenDiscrepancies({ onTriggerToast }: Props) {
  const navigate = useNavigate();
  const { shipmentId } = useShipment();
  const [discrepancies, setDiscrepancies] = useState<ApiDiscrepancy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [resolvedItems, setResolvedItems] = useState<Record<string, boolean>>({});
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const activeId = shipmentId ?? 'demo-shipment';

  useEffect(() => {
    setLoading(true);
    setError(null);
    getDiscrepancies(activeId)
      .then(res => {
        setDiscrepancies((res as { discrepancies: ApiDiscrepancy[] }).discrepancies ?? []);
      })
      .catch(err => {
        setError(err.message || 'Failed to load discrepancies from backend.');
      })
      .finally(() => setLoading(false));
  }, [activeId]);

  const handleResolve = (id: string) => {
    setResolvedItems(prev => ({ ...prev, [id]: true }));
    onTriggerToast({ title: 'Harmonization Applied', message: `Discrepancy ${id.slice(0, 20)}... synchronized.`, type: 'success' });
  };

  const filtered = discrepancies.filter(d => {
    const matchesCat = filter === 'all' || d.severity === filter;
    const matchesSearch = d.rule_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.delta.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary">
            <span>Operations</span><span className="text-outline-variant">/</span>
            <span>Discrepancy Reconciliation Stream</span>
            {!loading && <span className="px-2 py-0.5 rounded-full bg-primary-fixed text-primary text-[10px]">{discrepancies.length} Active</span>}
          </div>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">Active Discrepancies &amp; Conflict Center</h1>
          <p className="text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Neuro-symbolic XAI engine pre-empting customs fines, green-channel delays, and cargo holds.
          </p>
        </div>
        <button
          onClick={() => { setLoading(true); getDiscrepancies(activeId).then(r => setDiscrepancies((r as { discrepancies: ApiDiscrepancy[] }).discrepancies ?? [])).finally(() => setLoading(false)); }}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary text-white text-xs font-semibold hover:bg-primary-container shadow-sm transition-all"
        >
          <span className="material-symbols-outlined text-[16px]">sync</span>
          <span>Re-run Evaluation</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-surface-container-lowest p-3 rounded-xl shadow-sm border border-outline-variant/20 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
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
          <input type="text" placeholder="Search rule, delta..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
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
            const isExpanded = expandedId === item.discrepancy_id;
            const isResolved = resolvedItems[item.discrepancy_id];
            return (
              <div key={item.discrepancy_id} className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/20 overflow-hidden">
                {/* Header row */}
                <div className="bg-primary/5 px-4 py-2.5 flex flex-wrap items-center justify-between gap-2 border-b border-outline-variant/20 text-xs">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${isResolved ? 'bg-secondary' : 'bg-primary animate-pulse'}`}></span>
                    <span className="font-bold text-on-surface">{xai.layer2.failed_rule_id}</span>
                    <span className="text-outline">•</span>
                    <span className="font-mono text-outline text-[10px]">{item.discrepancy_id.slice(0, 24)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <ConfidencePill level={xai.layer3.confidence_level} score={xai.layer3.overall_confidence} />
                    <span className={`px-2.5 py-0.5 rounded-full font-semibold text-[10px] uppercase ${isResolved ? 'bg-secondary-container/30 text-secondary' : 'bg-primary-fixed text-primary'}`}>
                      {isResolved ? 'Reconciled' : 'Attention Required'}
                    </span>
                  </div>
                </div>

                {/* Main body */}
                <div className="p-4 grid grid-cols-1 xl:grid-cols-12 gap-4 text-xs">
                  <div className="xl:col-span-7 space-y-3">
                    {/* Values */}
                    <div className="grid grid-cols-3 gap-2">
                      <div className="bg-surface-container-low p-2.5 rounded-lg">
                        <div className="text-[10px] text-outline uppercase">Document A</div>
                        <div className="text-sm font-bold text-on-surface font-mono mt-0.5">{item.value_a}</div>
                      </div>
                      <div className="bg-surface-container-low p-2.5 rounded-lg">
                        <div className="text-[10px] text-outline uppercase">Document B</div>
                        <div className="text-sm font-bold text-on-surface font-mono mt-0.5">{item.value_b}</div>
                      </div>
                      <div className="bg-primary-fixed/30 p-2.5 rounded-lg">
                        <div className="text-[10px] text-primary uppercase font-bold">Variance</div>
                        <div className="text-sm font-bold text-primary font-mono mt-0.5">{item.delta}</div>
                      </div>
                    </div>

                    {/* XAI Layer 2 — Reasoning steps (expandable) */}
                    <div className="p-2.5 bg-surface-container rounded-lg">
                      <button className="flex items-center gap-2 w-full text-left" onClick={() => setExpandedId(isExpanded ? null : item.discrepancy_id)}>
                        <span className="material-symbols-outlined text-primary text-[16px]">account_tree</span>
                        <span className="font-semibold text-on-surface">XAI Reasoning Chain</span>
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
                  <div className="xl:col-span-5 bg-surface-container-low/50 p-3 rounded-lg flex flex-col justify-between gap-3">
                    <div>
                      <div className="text-[10px] font-bold text-primary uppercase flex items-center gap-1">
                        <span className="material-symbols-outlined text-[14px]">auto_awesome</span> AI Directive Action
                      </div>
                      <div className="mt-1 font-mono text-[11px] text-on-surface bg-surface-container-lowest p-2 rounded border border-outline-variant/30 leading-relaxed">
                        {xai.layer4.recommended_action}
                      </div>
                      <div className="mt-2 text-[10px] text-on-surface-variant">
                        <span className="text-outline">Confidence explanation: </span>{xai.layer3.confidence_explanation}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button onClick={() => handleResolve(item.discrepancy_id)} disabled={isResolved}
                        className={`flex-1 py-2 px-3 rounded-lg font-semibold flex items-center justify-center gap-1.5 transition-all shadow-sm text-xs ${isResolved ? 'bg-secondary-container/40 text-secondary cursor-default' : 'bg-primary text-white hover:bg-primary/90'}`}>
                        <span className="material-symbols-outlined text-[16px]">{isResolved ? 'check_circle' : 'done_all'}</span>
                        <span>{isResolved ? 'Resolved' : 'Auto-Resolve'}</span>
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
