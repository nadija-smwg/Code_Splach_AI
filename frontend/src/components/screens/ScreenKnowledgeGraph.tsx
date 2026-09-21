import { useState } from 'react';

interface Props { onTriggerToast: (t: { title: string; message: string }) => void; }

export function ScreenKnowledgeGraph({ onTriggerToast }: Props) {
  // selectedNode state reserved for future topology highlight feature
  const [_selectedNode, setSelectedNode] = useState('conflict');

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-semibold text-primary uppercase tracking-wider">Topology Live • Core Relational Map</div>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">Customs Entity Knowledge Graph & Relational Map</h1>
          <p className="text-xs md:text-sm text-on-surface-variant mt-1">Multi-document cross-reference & declaration lineage graph under active Sri Lanka ASYCUDA clearance dossier.</p>
        </div>
        <button onClick={() => onTriggerToast({ title: 'Graph Exported', message: 'Full node JSON-LD downloaded.' })}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold bg-primary text-white rounded-lg shadow-sm hover:bg-primary/90">
          <span className="material-symbols-outlined text-[16px]">download</span>
          <span>Export Graph JSON</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-10 gap-6 items-start">
        {/* Graph Canvas */}
        <div className="lg:col-span-7 bg-surface-container-lowest rounded-xl border border-outline-variant/30 shadow-sm relative overflow-hidden min-h-[580px] flex flex-col">
          <div className="p-3 border-b border-outline-variant/30 bg-surface-container-low/50 flex items-center justify-between text-xs">
            <span className="font-semibold text-on-surface">7 Nodes • 8 Edges • 1 Conflict Flag</span>
            <div className="flex items-center gap-3 text-[11px] text-on-surface-variant font-medium">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-primary"></span> Document</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-secondary"></span> Entity</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500"></span> Conflict</span>
            </div>
          </div>
          <div className="relative flex-1 w-full h-[500px] p-6 overflow-hidden"
            style={{ backgroundImage: 'radial-gradient(#dcd9dc 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
              <line stroke="#3525cd" strokeWidth="2" x1="100" y1="80" x2="260" y2="80" />
              <line stroke="#006c4a" strokeWidth="2" x1="390" y1="80" x2="520" y2="80" />
              <path d="M 320 120 C 320 180, 140 180, 140 240" fill="none" stroke="#cbd5e1" strokeDasharray="4,4" strokeWidth="1.5" />
              <path d="M 340 120 C 340 180, 480 180, 480 240" fill="none" stroke="#cbd5e1" strokeDasharray="4,4" strokeWidth="1.5" />
              <path d="M 200 280 C 280 340, 380 340, 440 280" fill="none" stroke="#b45309" strokeDasharray="5,5" strokeWidth="2" />
            </svg>
            {/* Conflict badge */}
            <div onClick={() => setSelectedNode('conflict')}
              className="absolute top-[280px] left-[260px] z-20 bg-amber-50 px-3 py-1 rounded-full text-[11px] font-semibold text-amber-800 border border-amber-300 shadow-sm flex items-center gap-1 cursor-pointer hover:scale-105 transition-transform">
              <span className="material-symbols-outlined text-[14px] text-amber-700">warning</span>
              <span>Gross Weight Discrepancy (+12.8 kg)</span>
            </div>
            {/* Node 1 */}
            <div className="absolute top-[40px] left-[20px] z-10 w-40 bg-surface-container-lowest rounded-xl border border-secondary/40 p-3 shadow-md">
              <div className="text-[10px] font-bold text-secondary uppercase">Manufacturer</div>
              <div className="text-xs font-bold text-on-surface truncate">MAS Holdings Ltd</div>
              <div className="text-[10px] text-outline font-mono">TIN: 1029482910</div>
            </div>
            {/* Node 2 */}
            <div className="absolute top-[35px] left-[240px] z-10 w-44 bg-primary-fixed/40 rounded-xl border-2 border-primary p-3 shadow-md ring-4 ring-primary/10">
              <div className="text-[10px] font-bold text-primary uppercase">Primary Dossier</div>
              <div className="text-xs font-bold text-on-surface font-mono">CLX-8A31F4D2</div>
              <div className="text-[10px] text-outline">Colombo Port Berth 04</div>
            </div>
            {/* Node 3 */}
            <div className="absolute top-[40px] left-[480px] z-10 w-40 bg-surface-container-lowest rounded-xl border border-secondary/40 p-3 shadow-md">
              <div className="text-[10px] font-bold text-secondary uppercase">Consignee</div>
              <div className="text-xs font-bold text-on-surface truncate">Marks & Spencer UK</div>
              <div className="text-[10px] text-outline font-mono">EORI: GB982736154</div>
            </div>
            {/* Node 4 */}
            <div onClick={() => setSelectedNode('conflict')}
              className="absolute top-[220px] left-[40px] z-10 w-44 bg-surface-container-lowest rounded-xl border-2 border-amber-500 p-3 shadow-md cursor-pointer hover:scale-105 transition-transform">
              <div className="text-[10px] font-bold text-amber-700 uppercase">Invoice CI-99201</div>
              <div className="text-xs font-bold text-on-surface mt-0.5">Gross Wt: 485.0 kg</div>
              <div className="text-[10px] text-outline">Net Wt: 440.0 kg</div>
            </div>
            {/* Node 5 */}
            <div onClick={() => setSelectedNode('conflict')}
              className="absolute top-[220px] left-[420px] z-10 w-44 bg-surface-container-lowest rounded-xl border-2 border-amber-500 p-3 shadow-md cursor-pointer hover:scale-105 transition-transform">
              <div className="text-[10px] font-bold text-amber-700 uppercase">Packing List PL-4801</div>
              <div className="text-xs font-bold text-on-surface mt-0.5">Gross Wt: 472.2 kg</div>
              <div className="text-[10px] text-outline">Net Wt: 440.0 kg</div>
            </div>
          </div>
        </div>

        {/* Inspector Panel */}
        <div className="lg:col-span-3 bg-surface-container-lowest p-5 rounded-xl border border-outline-variant/30 shadow-sm flex flex-col gap-4 text-xs">
          <div className="border-b border-outline-variant/20 pb-3 flex items-center justify-between">
            <div>
              <span className="text-[10px] uppercase text-outline">Topology Inspector</span>
              <h2 className="text-sm font-bold text-on-surface">Variance Conflict</h2>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">Review Req.</span>
          </div>
          <div className="bg-surface-container-low p-3 rounded-lg space-y-1.5">
            <div className="flex justify-between"><span className="text-outline">Source:</span><span className="font-semibold text-primary font-mono">Invoice CI-99201</span></div>
            <div className="flex justify-between"><span className="text-outline">Target:</span><span className="font-semibold text-primary font-mono">Packing List PL-4801</span></div>
            <div className="flex justify-between pt-1 border-t border-outline-variant/20">
              <span className="text-outline">Match Confidence:</span><span className="font-semibold text-secondary">98.6%</span>
            </div>
          </div>
          <div className="border border-outline-variant/30 rounded-lg overflow-hidden">
            <table className="w-full text-left text-[11px]">
              <thead className="bg-surface-container-low text-outline font-semibold">
                <tr><th className="p-2">Field</th><th className="p-2">CI</th><th className="p-2">PL</th><th className="p-2 text-right">Delta</th></tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/20 font-mono">
                <tr className="bg-amber-50/60"><td className="p-2 font-sans font-medium">Gross</td><td className="p-2">485.0</td><td className="p-2">472.2</td><td className="p-2 text-right text-amber-700 font-bold">+12.8kg</td></tr>
                <tr><td className="p-2 font-sans font-medium">Net</td><td className="p-2">440.0</td><td className="p-2">440.0</td><td className="p-2 text-right text-secondary">0.0</td></tr>
                <tr><td className="p-2 font-sans font-medium">Cartons</td><td className="p-2">24</td><td className="p-2">24</td><td className="p-2 text-right text-secondary">Match</td></tr>
              </tbody>
            </table>
          </div>
          <button onClick={() => onTriggerToast({ title: 'Auto-Reconciled', message: 'Tare offset generated in Knowledge Graph cache.' })}
            className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary/90 text-white font-semibold flex items-center justify-center gap-1.5 shadow-sm">
            <span className="material-symbols-outlined text-[16px]">sync</span>
            <span>Auto-Reconcile Variance</span>
          </button>
        </div>
      </div>
    </div>
  );
}
