import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface Props { onTriggerToast: (t: { title: string; message: string }) => void; }

export function ScreenDiscrepancies({ onTriggerToast }: Props) {
  const navigate = useNavigate();
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [resolvedItems, setResolvedItems] = useState<Record<string, boolean>>({});

  const discrepancies = [
    { id: 'DISC-8821', category: 'weight', title: 'Gross Weight Mismatch Detected', consignee: 'MAS Holdings (Pvt) Ltd', buyer: 'Marks & Spencer PLC', invoiceVal: '450.00 kg', otherVal: '462.50 kg (HAWB)', delta: '+12.50 kg (+2.78%)', riskNote: 'Breaches Sri Lanka Customs Rule TR-LK-44 (±0.50% buffer). Halts direct Green Channel routing.', actionTarget: 'UPDATE Box 38 [Net Mass: 450.00kg, Gross: 462.50kg, Tare Code: PL-01]' },
    { id: 'DISC-7731', category: 'valuation', title: 'Incoterm Freight Disconnect', consignee: 'Hirdaramani Industries Ltd', buyer: 'Patagonia Inc.', invoiceVal: 'FOB Colombo', otherVal: 'CFR Rotterdam (B/L)', delta: 'Freight Unapportioned', riskNote: 'Declaring CFR under unadjusted FOB invoice risks Inland Revenue withholding assessment.', actionTarget: 'Reconcile profile to FOB Colombo with attached ocean freight voucher ($1,420.00).' },
    { id: 'DISC-6409', category: 'weight', title: 'Carton Count Variance', consignee: 'Brandix Apparel Solutions', buyer: "Victoria's Secret", invoiceVal: '118 ctns', otherVal: '120 ctns (PL)', delta: '+2 ctns (Samples)', riskNote: 'Line 42 annotates 2x Garment Quality Control Swatch Cartons (NVD).', actionTarget: "Attach Non-Commercial Sample Endorsement under Gazette 2024/09." },
  ];

  const handleResolve = (id: string) => {
    setResolvedItems({ ...resolvedItems, [id]: true });
    onTriggerToast({ title: 'Harmonization Applied', message: `Ref #${id} synchronized with ASYCUDA clearance cache.` });
  };

  const filtered = discrepancies.filter((d) => {
    const matchesCat = filter === 'all' || d.category === filter;
    const matchesSearch = d.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.consignee.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary">
            <span>Operations</span><span className="text-outline-variant">/</span>
            <span>Discrepancy Reconciliation Stream</span>
            <span className="px-2 py-0.5 rounded-full bg-primary-fixed text-primary text-[10px]">Active Triage</span>
          </div>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">Active Discrepancies & Conflict Center</h1>
          <p className="text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">Automated cross-document verification engine pre-empting customs fines, green-channel delays, and cargo holds.</p>
        </div>
        <button onClick={() => onTriggerToast({ title: 'Integrity Scan Complete', message: 'Scanned 14 active shipping manifests. No new anomalies detected.' })}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary text-white text-xs font-semibold hover:bg-primary-container shadow-sm transition-all">
          <span className="material-symbols-outlined text-[16px]">sync</span>
          <span>Run Integrity Scan</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-surface-container-lowest p-3 rounded-xl shadow-sm border border-outline-variant/20 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-1 overflow-x-auto w-full sm:w-auto">
          {[['all', 'All (3)'], ['weight', 'Weight & Mass (2)'], ['valuation', 'Valuation (1)']].map(([cat, label]) => (
            <button key={cat} onClick={() => setFilter(cat)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${filter === cat ? 'bg-primary text-white' : 'text-on-surface-variant hover:bg-surface-container'}`}>
              {label}
            </button>
          ))}
        </div>
        <div className="relative w-full sm:w-72">
          <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-outline text-[16px]">search</span>
          <input type="text" placeholder="Search Ref, Consignee..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-surface-container-low rounded-lg text-xs text-on-surface placeholder:text-outline focus:outline-none focus:bg-surface-container-lowest" />
        </div>
      </div>

      {/* Stream Cards */}
      <div className="space-y-4">
        {filtered.map((item) => (
          <div key={item.id} className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/20 overflow-hidden flex flex-col">
            <div className="bg-primary/5 px-4 py-2.5 flex flex-wrap items-center justify-between gap-2 border-b border-outline-variant/20 text-xs">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${resolvedItems[item.id] ? 'bg-secondary' : 'bg-primary animate-pulse'}`}></span>
                <span className="font-bold text-on-surface">{item.title}</span>
                <span className="text-outline">•</span>
                <span className="font-mono text-outline">{item.id}</span>
                <span className="text-outline">•</span>
                <span className="text-on-surface-variant">{item.consignee}</span>
              </div>
              <span className={`px-2.5 py-0.5 rounded-full font-semibold text-[10px] uppercase ${resolvedItems[item.id] ? 'bg-secondary-container/30 text-secondary' : 'bg-primary-fixed text-primary'}`}>
                {resolvedItems[item.id] ? 'Reconciled & Sealed' : 'Attention Required'}
              </span>
            </div>
            <div className="p-4 grid grid-cols-1 xl:grid-cols-12 gap-4 text-xs">
              <div className="xl:col-span-7 space-y-3">
                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-surface-container-low p-2.5 rounded-lg">
                    <div className="text-[10px] text-outline uppercase">Invoice Metric</div>
                    <div className="text-sm font-bold text-on-surface font-mono mt-0.5">{item.invoiceVal}</div>
                  </div>
                  <div className="bg-surface-container-low p-2.5 rounded-lg">
                    <div className="text-[10px] text-outline uppercase">Secondary Doc</div>
                    <div className="text-sm font-bold text-on-surface font-mono mt-0.5">{item.otherVal}</div>
                  </div>
                  <div className="bg-primary-fixed/30 p-2.5 rounded-lg">
                    <div className="text-[10px] text-primary uppercase font-bold">Variance Delta</div>
                    <div className="text-sm font-bold text-primary font-mono mt-0.5">{item.delta}</div>
                  </div>
                </div>
                <div className="p-2.5 bg-surface-container rounded-lg flex items-start gap-2">
                  <span className="material-symbols-outlined text-primary text-[18px] shrink-0">shield</span>
                  <p className="text-[11px] text-on-surface-variant">{item.riskNote}</p>
                </div>
              </div>
              <div className="xl:col-span-5 bg-surface-container-low/50 p-3 rounded-lg flex flex-col justify-between gap-3">
                <div>
                  <div className="text-[10px] font-bold text-primary uppercase flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">auto_awesome</span> Directive Action
                  </div>
                  <div className="mt-1 font-mono text-[11px] text-on-surface bg-surface-container-lowest p-2 rounded border border-outline-variant/30">{item.actionTarget}</div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => handleResolve(item.id)} disabled={resolvedItems[item.id]}
                    className={`flex-1 py-2 px-3 rounded-lg font-semibold flex items-center justify-center gap-1.5 transition-all shadow-sm ${resolvedItems[item.id] ? 'bg-secondary-container/40 text-secondary cursor-default' : 'bg-primary text-white hover:bg-primary/90'}`}>
                    <span className="material-symbols-outlined text-[16px]">{resolvedItems[item.id] ? 'check_circle' : 'done_all'}</span>
                    <span>{resolvedItems[item.id] ? 'Resolved & Transmitted' : 'Auto-Resolve & Update Box 38'}</span>
                  </button>
                  <button onClick={() => navigate('/review-workspace')} className="px-3 py-2 rounded-lg bg-surface-container text-on-surface hover:bg-surface-variant font-medium">Inspect</button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
