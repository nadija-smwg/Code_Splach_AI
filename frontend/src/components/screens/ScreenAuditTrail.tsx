import { useState } from 'react';

interface Props { onTriggerToast: (t: { title: string; message: string }) => void; }

export function ScreenAuditTrail({ onTriggerToast }: Props) {
  const [selectedEvent, setSelectedEvent] = useState('EV-9021-01');

  const events = [
    { id: 'EV-9021-01', ref: 'CLX-8A31F4D2', event: 'Tare Weight Auto-Harmonization (+12.50 kg)', hash: 'e3b0c44...a9f1', status: 'Sealed' },
    { id: 'EV-4491-02', ref: 'CLX-7F19B8C1', event: 'ASYCUDA CUSDEC-EX Green Lane Approval', hash: '94ae8f8...92e9', status: 'Green Lane' },
    { id: 'EV-1834-03', ref: 'CLX-99B224E0', event: 'Freight Term Discord Reconciled (FOB)', hash: '7f49aa1...cd08', status: 'Verified' },
  ];

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="text-xs text-primary font-semibold uppercase tracking-wider">Page 08 / 10 • Audit Ledger</div>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">Cryptographic Audit & AI Provenance Trail</h1>
          <p className="text-xs md:text-sm text-on-surface-variant mt-1">Immutable SHA-256 event sequencing, model inference receipts, and customs inspector sign-offs across Colombo corridors.</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => onTriggerToast({ title: 'Enclave Validated 100%', message: 'Root merkle tree matches Sri Lanka Customs HSM seal.' })}
            className="px-3 py-2 rounded-lg bg-surface-container-lowest hover:bg-surface-container text-xs font-semibold flex items-center gap-1.5 border border-outline-variant/30 shadow-sm">
            <span className="material-symbols-outlined text-secondary text-[16px]">verified_user</span>
            <span>Verify SLC Enclave</span>
          </button>
          <button onClick={() => onTriggerToast({ title: 'Ledger Exported', message: 'RFC 3161 proof receipt downloaded.' })}
            className="px-3 py-2 rounded-lg bg-primary text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm">
            <span className="material-symbols-outlined text-[16px]">download</span>
            <span>Export Ledger (.JSON)</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start text-xs">
        <div className="xl:col-span-8 bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/20 overflow-hidden flex flex-col">
          <div className="p-3 bg-surface-container-low flex items-center justify-between font-bold border-b border-outline-variant/20">
            <span>Ledger Sequence Buffer</span>
            <span className="font-mono text-outline font-normal">Block #1,894,229</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-surface-container-low text-outline uppercase font-semibold text-[10px]">
                  <th className="py-2.5 px-3">Consignment</th>
                  <th className="py-2.5 px-3">Event Summary</th>
                  <th className="py-2.5 px-3">Provenance Hash</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-container-high/30">
                {events.map((row) => (
                  <tr key={row.id} onClick={() => setSelectedEvent(row.id)}
                    className={`hover:bg-surface-container-low/60 cursor-pointer transition-colors ${selectedEvent === row.id ? 'bg-primary/5' : ''}`}>
                    <td className="py-3 px-3 font-mono font-bold text-primary">{row.ref}</td>
                    <td className="py-3 px-3 text-on-surface">{row.event}</td>
                    <td className="py-3 px-3 font-mono text-outline">{row.hash}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded-full bg-secondary-container/30 text-secondary font-semibold text-[10px]">{row.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="xl:col-span-4 bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-outline-variant/30 flex flex-col gap-4">
          <div className="border-b border-outline-variant/20 pb-2 flex items-center justify-between">
            <span className="font-bold text-on-surface">Proof Certificate</span>
            <span className="px-2 py-0.5 rounded bg-secondary-container text-on-secondary-container font-mono text-[10px]">SEALED</span>
          </div>
          <div className="space-y-3">
            <div className="bg-surface-container-low p-2.5 rounded-lg space-y-1">
              <div className="text-[10px] text-outline uppercase">Target Payload</div>
              <div className="font-bold text-on-surface font-mono">CLX-8A31F4D2</div>
              <div className="text-[11px] text-on-surface-variant">CustomsLLM v4.2 Inference Signed</div>
            </div>
            <div>
              <div className="text-[10px] text-outline uppercase mb-1">SHA-256 Root State</div>
              <div className="p-2 bg-surface-container rounded font-mono text-[10px] break-all select-all leading-normal text-on-surface">
                e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
              </div>
            </div>
            <div className="p-2.5 bg-secondary-container/30 rounded-lg flex items-center gap-2">
              <span className="material-symbols-outlined text-secondary text-[20px]">workspace_premium</span>
              <div className="text-[11px]">
                <span className="font-bold block">Sri Lanka Customs Certified</span>
                <span className="text-outline">Timestamp: 2025-05-18T14:32:08.412+05:30</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
