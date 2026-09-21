import { useState } from 'react';

interface Props { onTriggerToast: (t: { title: string; message: string }) => void; }

export function ScreenAsycudaGateway({ onTriggerToast }: Props) {
  const [payloadTab, setPayloadTab] = useState('structured');
  const [selectedDec, setSelectedDec] = useState('DEC-LK-2025-0891');

  const declarations = [
    { id: 'DEC-LK-2025-0891', awb: 'AWB-603-8821', consignee: 'MAS Holdings → M&S UK', channel: 'Green (Expedited)', status: 'Acknowledged' },
    { id: 'DEC-LK-2025-0892', awb: 'BL-COSU-6301', consignee: 'Brandix → Victoria Secret', channel: 'Green (Expedited)', status: 'Cleared' },
    { id: 'DEC-LK-2025-0893', awb: 'BL-ONEY-9921', consignee: 'Hirdaramani → Patagonia', channel: 'Yellow (Doc Audit)', status: 'Assessing' },
  ];

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs">
            <span className="px-2 py-0.5 rounded-full bg-secondary-container/30 text-secondary uppercase font-semibold text-[10px]">Direct Pipe Operational • 2.1ms</span>
            <span className="text-outline">ASYCUDA World 4.2.1</span>
          </div>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">ASYCUDA World EDI Gateway & Direct Transmission Corridor</h1>
          <p className="text-xs md:text-sm text-on-surface-variant mt-1">Live AS2/EDIFACT & XML customs declaration broker pipeline connected to Sri Lanka Customs Department (Times Building, Colombo 01).</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => onTriggerToast({ title: 'Gateway Ping Acknowledged', message: 'Node CMB-EDI-01 roundtrip response in 1.9ms.' })}
            className="px-3.5 py-2 rounded-lg bg-surface-container-lowest hover:bg-surface-container text-xs font-semibold flex items-center gap-1.5 shadow-sm border border-outline-variant/30">
            <span className="material-symbols-outlined text-primary text-[16px]">wifi_tethering</span>
            <span>Trigger Gateway Ping</span>
          </button>
          <button onClick={() => onTriggerToast({ title: 'Audit Certificate Generated', message: 'SHA-256 certificate downloaded.' })}
            className="px-3.5 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 text-xs font-semibold flex items-center gap-1.5 shadow-sm">
            <span className="material-symbols-outlined text-[16px]">download_for_offline</span>
            <span>Download Audit Cert</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Transmission Table */}
        <div className="lg:col-span-7 bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/20 overflow-hidden flex flex-col">
          <div className="p-4 bg-surface-container-low/50 flex items-center justify-between border-b border-outline-variant/20 text-xs font-bold text-on-surface">
            <span>Recent ASYCUDA XML Transmissions</span>
            <span className="text-[10px] text-outline font-normal">Auto-refresh 5s</span>
          </div>
          <div className="overflow-x-auto text-xs">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-surface-container-low text-outline uppercase font-semibold text-[10px]">
                  <th className="py-2.5 px-3">Declaration ID</th>
                  <th className="py-2.5 px-3">Consignment</th>
                  <th className="py-2.5 px-3">Consignee Flow</th>
                  <th className="py-2.5 px-3">Channel</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-container-high/30">
                {declarations.map((dec) => (
                  <tr key={dec.id} onClick={() => setSelectedDec(dec.id)}
                    className={`hover:bg-surface-container-low/60 cursor-pointer transition-colors ${selectedDec === dec.id ? 'bg-primary/5' : ''}`}>
                    <td className="py-3 px-3 font-mono font-bold text-primary">{dec.id}</td>
                    <td className="py-3 px-3 font-mono text-outline">{dec.awb}</td>
                    <td className="py-3 px-3 text-on-surface">{dec.consignee}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded-full bg-secondary-container/30 text-secondary text-[10px] font-semibold">{dec.channel}</span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button className="text-primary font-semibold hover:underline">Inspect</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Live Payload Preview */}
        <div className="lg:col-span-5 bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/30 overflow-hidden flex flex-col text-xs">
          <div className="p-3 bg-surface-container-low/60 border-b border-outline-variant/20 flex items-center justify-between">
            <div>
              <div className="font-bold text-on-surface">Live ASYCUDA Transmission Payload</div>
              <div className="text-[10px] font-mono text-outline">{selectedDec} • Schema SAD v4.2</div>
            </div>
            <div className="flex items-center gap-1 bg-surface-container-low p-0.5 rounded">
              <button onClick={() => setPayloadTab('structured')}
                className={`px-2 py-1 rounded text-[11px] font-semibold ${payloadTab === 'structured' ? 'bg-white shadow-sm text-primary' : 'text-outline'}`}>
                Structured
              </button>
              <button onClick={() => setPayloadTab('raw')}
                className={`px-2 py-1 rounded text-[11px] font-semibold ${payloadTab === 'raw' ? 'bg-white shadow-sm text-primary' : 'text-outline'}`}>
                Raw XML
              </button>
            </div>
          </div>
          <div className="p-4 max-h-[380px] overflow-y-auto">
            {payloadTab === 'structured' ? (
              <div className="space-y-3">
                <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/20">
                  <div className="font-semibold text-on-surface mb-2 text-[11px]">Declaration Header</div>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div><span className="text-outline block">Office Code</span><span className="font-mono font-semibold">LKCMB</span></div>
                    <div><span className="text-outline block">Customs Model</span><span className="font-mono font-semibold">EX-1 (Export)</span></div>
                    <div><span className="text-outline block">Declarant TIN</span><span className="font-mono font-semibold text-primary">102948271</span></div>
                    <div><span className="text-outline block">Consignee EORI</span><span className="font-mono font-semibold">GB982301928000</span></div>
                  </div>
                </div>
                <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/20">
                  <div className="font-semibold text-on-surface mb-2 text-[11px]">Valuation & Terms</div>
                  <div className="grid grid-cols-3 gap-2 text-[11px]">
                    <div><span className="text-outline block">Incoterm</span><span className="font-mono font-semibold">FCA Colombo</span></div>
                    <div><span className="text-outline block">Currency</span><span className="font-mono font-semibold">USD ($)</span></div>
                    <div><span className="text-outline block">Total Value</span><span className="font-mono font-semibold text-secondary">$18,600.00</span></div>
                  </div>
                </div>
              </div>
            ) : (
              <pre className="p-3 bg-slate-900 text-emerald-400 font-mono text-[10px] rounded-lg overflow-x-auto leading-relaxed">
{`<ASYCUDA_Declaration id="${selectedDec}">
  <Declaration_Header>
    <Office_Code>LKCMB</Office_Code>
    <Customs_Model>EX-1</Customs_Model>
    <Declarant_TIN>102948271</Declarant_TIN>
    <Consignee_EORI>GB982301928000</Consignee_EORI>
  </Declaration_Header>
  <Valuation>
    <Incoterm>FCA Colombo</Incoterm>
    <Currency>USD</Currency>
    <Total_Invoice_Value>18600.00</Total_Invoice_Value>
  </Valuation>
</ASYCUDA_Declaration>`}
              </pre>
            )}
          </div>
          <div className="p-3 bg-surface-container-low border-t border-outline-variant/20 flex items-center justify-between text-[11px]">
            <span className="text-secondary font-semibold flex items-center gap-1">
              <span className="material-symbols-outlined text-[15px]">verified</span> SHA-256 Digest Sealed
            </span>
            <button onClick={() => onTriggerToast({ title: 'Payload Re-sent', message: 'EDI AS2 transmission triggered to Sri Lanka Customs node.' })}
              className="px-2.5 py-1 rounded bg-primary text-white font-semibold">
              Re-Send AS2
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
