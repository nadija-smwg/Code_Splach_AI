import { useNavigate } from 'react-router-dom';

interface Props { onTriggerToast: (t: { title: string; message: string }) => void; }

export function ScreenOverview({ onTriggerToast }: Props) {
  const navigate = useNavigate();
  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      {/* Hero Banner */}
      <section className="relative w-full rounded-xl overflow-hidden shadow-sm bg-surface-container">
        <div className="relative w-full min-h-[360px] md:min-h-[380px] flex flex-col justify-end p-6 md:p-10">
          <img alt="Colombo International Trade and Logistics Terminal" className="absolute inset-0 w-full h-full object-cover object-center"
            src="/screen.png" />
          <div className="absolute inset-0 bg-gradient-to-t from-on-surface/90 via-on-surface/50 to-transparent"></div>
          <div className="absolute inset-0 bg-primary-container/10 mix-blend-overlay"></div>
          <div className="relative z-10 max-w-4xl flex flex-col gap-4">
            <div className="inline-flex items-center self-start gap-2 bg-surface-container-lowest/90 backdrop-blur-md px-3 py-1 rounded-full shadow-sm text-xs">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-secondary"></span>
              </span>
              <span className="text-secondary font-semibold uppercase tracking-wider">ASYCUDA 4.2.1 Connected</span>
              <span className="text-outline">•</span>
              <span className="text-on-surface-variant font-mono">2ms latency</span>
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">Colombo Customs Intelligence Corridor</h1>
              <p className="text-white/90 text-sm md:text-base max-w-2xl mt-1 leading-relaxed">
                Automated AI document cross-examination & ASYCUDA clearance stream for Sri Lankan apparel & transshipment exports.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button onClick={() => navigate('/dossiers')} className="inline-flex items-center justify-center gap-2 bg-primary-container text-white px-5 py-2.5 rounded-lg text-xs font-semibold shadow-md hover:bg-primary transition-all active:scale-95">
                <span className="material-symbols-outlined text-[18px]">add</span>
                <span>+ Ingest New Dossier</span>
              </button>
              <button onClick={() => onTriggerToast({ title: 'Batch Manifest Assembled', message: 'Downloading encrypted EDIFACT XML package for active export cycle.' })}
                className="inline-flex items-center justify-center gap-2 bg-surface-container-lowest/90 hover:bg-surface-container-lowest text-on-surface px-4 py-2.5 rounded-lg text-xs font-semibold shadow-sm transition-all">
                <span className="material-symbols-outlined text-[18px] text-on-surface-variant">file_download</span>
                <span>Download Batch Manifest</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* KPI Cards */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
            <span>Total Processed</span>
            <span className="material-symbols-outlined text-outline text-[20px]">inventory_2</span>
          </div>
          <div className="mt-4">
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-on-surface">1,428</span>
              <span className="text-xs text-outline">dossiers</span>
            </div>
            <div className="mt-2 flex items-center gap-1.5 text-xs">
              <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-secondary-container/20 text-secondary font-mono">
                <span className="material-symbols-outlined text-[14px]">arrow_upward</span> 18.4%
              </span>
              <span className="text-outline">vs prior month cycle</span>
            </div>
          </div>
        </div>
        <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
            <span>Autonomous Green Lane</span>
            <span className="material-symbols-outlined text-secondary text-[20px]">verified</span>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold text-secondary">95.2%</div>
            <div className="mt-2 flex items-center justify-between text-xs text-outline">
              <span>Zero-touch auto-certified</span>
              <div className="w-16 bg-surface-container-high h-1.5 rounded-full overflow-hidden">
                <div className="bg-secondary h-full rounded-full" style={{ width: '95.2%' }}></div>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
            <span>Action Required</span>
            <span className="material-symbols-outlined text-tertiary-container text-[20px]">rule</span>
          </div>
          <div className="mt-4">
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-on-surface">3</span>
              <span className="text-xs text-outline">consignments</span>
            </div>
            <div className="mt-2 flex items-center gap-1.5 text-xs">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary-fixed text-primary font-semibold">
                <span className="h-1.5 w-1.5 rounded-full bg-primary"></span> Review Pending
              </span>
              <span className="text-outline">Tolerance check</span>
            </div>
          </div>
        </div>
        <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
            <span>Avg Clearance Speed</span>
            <span className="material-symbols-outlined text-outline text-[20px]">speed</span>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold text-on-surface font-mono">1m 42s</div>
            <div className="mt-2 flex items-center gap-1.5 text-xs">
              <span className="text-secondary font-semibold">8.8x faster</span>
              <span className="text-outline">than manual broker queue</span>
            </div>
          </div>
        </div>
      </section>

      {/* Active Pipeline Table */}
      <section className="bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden border border-outline-variant/20">
        <div className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-outline-variant/20">
          <div>
            <h2 className="text-base font-semibold text-on-surface">Active Consignment Pipeline</h2>
            <p className="text-xs text-outline">Live ASYCUDA clearing corridor: Katunayake (CMB) & Colombo Port CICT</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-outline font-semibold uppercase">Channel:</span>
            <div className="inline-flex bg-surface-container-low p-1 rounded-lg text-xs font-medium">
              <button className="px-2.5 py-1 rounded bg-surface-container-lowest text-on-surface shadow-sm font-semibold">All (4)</button>
              <button className="px-2.5 py-1 rounded text-on-surface-variant hover:text-on-surface">Green Lane</button>
              <button className="px-2.5 py-1 rounded text-on-surface-variant hover:text-on-surface">Flags</button>
            </div>
          </div>
        </div>
        <div className="w-full overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-surface-container-low text-outline font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Consignment ID</th>
                <th className="py-3 px-4">Consignee & Buyer</th>
                <th className="py-3 px-4">Documents</th>
                <th className="py-3 px-4">AI Status</th>
                <th className="py-3 px-4">Clearance Channel</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container-high/30">
              {[
                { id: 'CLX-8A31F4D2', ref: 'AWB 603-8821-4901', consignee: 'MAS Holdings (Pvt) Ltd', buyer: 'Marks & Spencer UK', type: 'Apparel Knits', docs: 5, status: 'Review Required (Weight Delta)', statusColor: 'bg-primary-fixed text-primary', channel: 'Green Lane', pct: '88.4%', barColor: 'bg-primary-container', action: 'Inspect' },
                { id: 'CLX-7F19B8C1', ref: 'BL COSU630198421', consignee: 'Brandix Apparel Solutions', buyer: "Victoria's Secret US", type: 'Woven Undergarments', docs: 4, status: 'Reconciled • Certified', statusColor: 'bg-secondary-container/20 text-secondary', channel: 'Expedited Green', pct: '100%', barColor: 'bg-secondary', action: 'Export XML' },
                { id: 'CLX-99B224E0', ref: 'BL ONEYCMB992140', consignee: 'Hirdaramani Industries', buyer: 'Patagonia Inc.', type: 'Organic Fleeces', docs: 6, status: 'Verification Pending', statusColor: 'bg-surface-container-high text-on-surface-variant', channel: 'Standard Green', pct: 'Queued', barColor: 'bg-outline-variant', action: 'Inspect' },
              ].map((row) => (
                <tr key={row.id} className="hover:bg-surface-container-low/50 transition-colors">
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[16px] text-outline">inventory</span>
                      <span className="font-semibold text-on-surface font-mono">{row.id}</span>
                    </div>
                    <span className="text-[11px] text-outline font-mono">{row.ref}</span>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="font-medium text-on-surface">{row.consignee}</div>
                    <div className="text-[11px] text-outline">→ {row.buyer} • {row.type}</div>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container font-mono text-on-surface-variant">
                      <span className="material-symbols-outlined text-[13px]">description</span> {row.docs} docs
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full font-semibold text-[11px] ${row.statusColor}`}>
                      <span className="h-1.5 w-1.5 rounded-full bg-current"></span> {row.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-on-surface">{row.channel}</span>
                      <span className="text-outline font-mono">{row.pct}</span>
                    </div>
                    <div className="w-24 bg-surface-container-high h-1 rounded-full overflow-hidden mt-1">
                      <div className={`${row.barColor} h-full rounded-full`} style={{ width: row.pct === 'Queued' ? '45%' : row.pct }}></div>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button onClick={() => row.action === 'Inspect' ? navigate('/review-workspace') : onTriggerToast({ title: 'SAD XML Exported', message: 'Signed ASYCUDA payload dispatched to downloads cache.' })}
                      className="inline-flex items-center gap-1 bg-surface-container-high hover:bg-surface-container text-on-surface px-3 py-1.5 rounded-lg font-medium transition-colors">
                      <span>{row.action}</span>
                      <span className="material-symbols-outlined text-[15px]">chevron_right</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="p-3 bg-surface-container-low/50 flex flex-col sm:flex-row items-center justify-between text-xs text-outline border-t border-outline-variant/20">
          <span>Showing 4 active consignments under live supervision</span>
          <div className="flex items-center gap-1.5 text-secondary">
            <span className="h-2 w-2 rounded-full bg-secondary"></span>
            <span>Real-time ASYCUDA sync stream active</span>
          </div>
        </div>
      </section>

      {/* Bottom Telemetry Strip */}
      <section className="bg-surface-container-lowest rounded-xl p-4 sm:p-5 shadow-sm border border-outline-variant/20 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-surface-container text-primary-container shrink-0">
            <span className="material-symbols-outlined text-[22px]">policy</span>
          </div>
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-on-surface">
              <span>Sri Lanka Customs Gazette 2024/09 Compliant</span>
              <span className="bg-surface-container px-2 py-0.5 rounded text-on-surface-variant text-[10px] font-mono">HS Rev 2024-V2</span>
            </div>
            <p className="text-xs text-outline mt-0.5">Automated export validation rules active across Katunayake Air Terminal & Colombo CICT.</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 bg-surface-container-low px-3 py-1.5 rounded-lg">
            <span className="material-symbols-outlined text-[16px] text-outline">flight_takeoff</span>
            <span>BIA Air Cargo</span>
            <span className="text-secondary font-mono font-bold">2ms</span>
          </div>
          <div className="flex items-center gap-1.5 bg-surface-container-low px-3 py-1.5 rounded-lg">
            <span className="material-symbols-outlined text-[16px] text-outline">sailing</span>
            <span>Colombo Port CICT</span>
            <span className="text-secondary font-mono font-bold">5ms</span>
          </div>
          <div className="flex items-center gap-1.5 bg-surface-container-low px-3 py-1.5 rounded-lg text-secondary">
            <span className="material-symbols-outlined text-[16px]">encrypted</span>
            <span>TLS 1.3 Strict</span>
          </div>
        </div>
      </section>
    </div>
  );
}
