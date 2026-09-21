import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface Props { onTriggerToast: (t: { title: string; message: string }) => void; }

export function ScreenBatchFiling({ onTriggerToast }: Props) {
  const navigate = useNavigate();
  const [selectedRows, setSelectedRows] = useState<Record<number, boolean>>({ 1: true, 2: true, 3: true, 4: true });
  const [isTransmitting, setIsTransmitting] = useState(false);

  const toggleRow = (id: number) => setSelectedRows((prev) => ({ ...prev, [id]: !prev[id] }));
  const selectedCount = Object.values(selectedRows).filter(Boolean).length;

  const handleTransmit = () => {
    setIsTransmitting(true);
    setTimeout(() => {
      setIsTransmitting(false);
      onTriggerToast({ title: 'Batch Dispatched to ASYCUDA World', message: `${selectedCount} Declarations queued for automated customs seal at Times Building node.` });
      navigate('/asycuda-gateway');
    }, 1200);
  };

  const rows = [
    { id: 1, name: 'MAS Holdings', tin: '104829910', desc: '8,240 Pcs Knitted Cotton Polos', hs: '6109.10.00', mass: '450.00 kg', status: 'Cryptographically Sealed' },
    { id: 2, name: 'Brandix Apparel', tin: '108392114', desc: '6,120 Units Synthetic Activewear', hs: '6104.43.00', mass: '780.00 kg', status: 'Pre-Cleared Form A' },
    { id: 3, name: 'Hirdaramani Ind.', tin: '102947118', desc: '14,000 Pcs Cotton Trousers', hs: '6203.42.00', mass: '1,420.00 kg', status: 'Tare Adjusted (TR-LK-44)' },
    { id: 4, name: 'Teejay Lanka', tin: '105649931', desc: '12,400 Kg Knitted Fabric Rolls', hs: '6006.22.00', mass: '12,400.00 kg', status: 'BOI Sec 17 Active' },
  ];

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="text-xs text-primary font-semibold uppercase tracking-wider">Page 05 / 10 • Batch Filing</div>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">Batch Declaration Filing & Customs Submission</h1>
          <p className="text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">Pre-flight cryptographic validation, multi-dossier compilation, and real-time dispatch to Sri Lanka Customs corridor.</p>
        </div>
        <span className="px-3 py-1.5 rounded-lg bg-surface-container text-xs font-semibold flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[16px] text-primary">verified_user</span>
          Cert: LK-EDI-9042
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
        {[
          { label: 'Ready for Transmission', value: '8 Declarations', sub: '100% Pre-Validated', subColor: 'text-secondary' },
          { label: 'Total Declared FOB Value', value: '$684,200 USD', sub: 'CBSL Peg @ LKR 301.25', subColor: 'text-outline' },
          { label: 'Duty Exemption Value', value: '$82,450 USD', sub: 'BOI Sec. 17 Verified', subColor: 'text-secondary' },
          { label: 'Corridor Gateway', value: 'Colombo CICT & BIA', sub: 'Live EDI Pipe Operational', subColor: 'text-secondary' },
        ].map((kpi) => (
          <div key={kpi.label} className="bg-surface-container-lowest p-4 rounded-xl shadow-sm border border-outline-variant/20">
            <span className="text-outline uppercase font-semibold text-[10px]">{kpi.label}</span>
            <div className="text-xl font-bold text-on-surface mt-1">{kpi.value}</div>
            <div className={`${kpi.subColor} font-medium mt-1`}>{kpi.sub}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-8 bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/20 overflow-hidden flex flex-col">
          <div className="p-4 flex items-center justify-between border-b border-outline-variant/20">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-on-surface">Pre-Flight Batch Staging Manifest</h2>
              <span className="px-2 py-0.5 rounded-full bg-surface-container text-xs font-semibold text-primary">{selectedCount} of 4 Selected</span>
            </div>
          </div>
          <div className="overflow-x-auto text-xs">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-surface-container-low text-outline uppercase font-semibold text-[10px] tracking-wider">
                  <th className="py-2.5 px-3 w-8"></th>
                  <th className="py-2.5 px-3">Consignor / Exporter</th>
                  <th className="py-2.5 px-3">Cargo Description</th>
                  <th className="py-2.5 px-3">HS Code</th>
                  <th className="py-2.5 px-3 text-right">Net Mass</th>
                  <th className="py-2.5 px-3 text-right">Cryptographic State</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-container-high/30">
                {rows.map((row) => (
                  <tr key={row.id} className="hover:bg-surface-container-low/50 transition-colors">
                    <td className="py-3 px-3">
                      <input type="checkbox" checked={!!selectedRows[row.id]} onChange={() => toggleRow(row.id)} className="accent-primary cursor-pointer" />
                    </td>
                    <td className="py-3 px-3">
                      <div className="font-semibold text-on-surface">{row.name}</div>
                      <div className="text-[10px] text-outline font-mono">TIN: {row.tin}</div>
                    </td>
                    <td className="py-3 px-3 text-on-surface">{row.desc}</td>
                    <td className="py-3 px-3"><span className="font-mono font-semibold text-primary">{row.hs}</span></td>
                    <td className="py-3 px-3 text-right font-mono font-bold text-on-surface">{row.mass}</td>
                    <td className="py-3 px-3 text-right">
                      <span className="px-2 py-0.5 rounded-full bg-secondary-container/30 text-secondary text-[10px] font-semibold">{row.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="lg:col-span-4 bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-outline-variant/20 flex flex-col gap-4 text-xs">
          <div className="border-b border-outline-variant/20 pb-3">
            <span className="text-[10px] text-outline uppercase">Live Staging Context</span>
            <h3 className="text-sm font-bold text-on-surface">Pre-Flight Compilation</h3>
          </div>
          <div className="space-y-3">
            <div className="flex items-start gap-2.5">
              <span className="material-symbols-outlined text-primary text-[18px]">key</span>
              <div>
                <div className="text-[10px] text-outline">Broker Digital Signature</div>
                <div className="font-semibold font-mono text-on-surface">LK-CB-9021 (Secp256k1)</div>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <span className="material-symbols-outlined text-on-surface-variant text-[18px]">inventory_2</span>
              <div>
                <div className="text-[10px] text-outline">CUSDEC Bundle Size</div>
                <div className="font-semibold text-on-surface">248 KB (WCO Model v3.8)</div>
              </div>
            </div>
          </div>
          <div className="p-3 bg-surface-container-low rounded-lg space-y-1">
            <div className="flex justify-between font-semibold">
              <span>Filing Integrity Score</span>
              <span className="text-secondary font-mono">99.8%</span>
            </div>
            <div className="w-full bg-surface-container-highest rounded-full h-1.5 overflow-hidden">
              <div className="bg-secondary h-full rounded-full" style={{ width: '99.8%' }}></div>
            </div>
          </div>
          <button onClick={handleTransmit} disabled={isTransmitting || selectedCount === 0}
            className="w-full py-3 rounded-lg bg-primary hover:bg-primary-container text-white font-bold flex items-center justify-center gap-2 shadow-md transition-all active:scale-95">
            <span className={`material-symbols-outlined text-[18px] ${isTransmitting ? 'animate-spin' : ''}`}>
              {isTransmitting ? 'sync' : 'bolt'}
            </span>
            <span>{isTransmitting ? 'Transmitting Bundle...' : `Transmit Batch (${selectedCount} Declarations)`}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
