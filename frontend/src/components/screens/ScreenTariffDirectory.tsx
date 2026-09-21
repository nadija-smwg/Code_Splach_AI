import { useState } from 'react';

interface Props { onTriggerToast: (t: { title: string; message: string }) => void; }

export function ScreenTariffDirectory({ onTriggerToast }: Props) {
  const [search, setSearch] = useState('');
  const [selectedCat, setSelectedCat] = useState('all');
  const [simHs, setSimHs] = useState('6109.10.00');
  const [grossWt, setGrossWt] = useState(12450);
  const [pallets, setPallets] = useState(24);

  const netCalculated = Math.max(0, grossWt - pallets * 22.5);

  const tariffData = [
    { hs: '6109.10.00', name: "T-shirts & vests, cotton knit", duty: '0% (GSP+)', vat: '18% Exempt (Exp)', rule: 'Mandatory Form A & ASYCUDA LK-EXP validation', cat: 'Apparel' },
    { hs: '6104.43.00', name: 'Synthetic activewear & dresses', duty: '0% BOI Sec 17', vat: '18% Suspended', rule: 'Gazette 2024/09: Blend tolerance ±2.50%', cat: 'Apparel' },
    { hs: '6203.42.00', name: "Men's cotton denim trousers", duty: 'Duty Free (Pref)', vat: '18% Direct Exempt', rule: 'TR-LK-44 tare deduction for standard Euro-pallets', cat: 'Apparel' },
    { hs: '6006.22.00', name: 'Knitted dyed cotton fabrics', duty: '0% Export Cess', vat: 'RAMIS Clear', rule: 'RAMIS Inland Revenue PIN pre-validation required', cat: 'Textiles' },
  ];

  const filtered = tariffData.filter((t) => {
    const matchCat = selectedCat === 'all' || t.cat === selectedCat;
    const matchSearch = t.hs.includes(search) || t.name.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchSearch;
  });

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="text-xs text-primary font-semibold uppercase tracking-wider">Page 09 / 10 • Tariff Directory</div>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">Customs Tariff & Regulatory Rules Directory</h1>
          <p className="text-xs md:text-sm text-on-surface-variant mt-1">WCO HS nomenclature, Sri Lanka Customs gazette directives, and automated export duty calculators.</p>
        </div>
        <button onClick={() => onTriggerToast({ title: 'Schema Synchronized', message: 'Customs schedule rev 2025/02 loaded.' })}
          className="px-3.5 py-2 rounded-lg bg-primary text-white text-xs font-semibold flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[16px]">sync</span>
          <span>Re-Index Rules</span>
        </button>
      </div>

      <div className="bg-surface-container-lowest p-3 rounded-xl shadow-sm border border-outline-variant/20 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-1 overflow-x-auto w-full sm:w-auto">
          {['all', 'Apparel', 'Textiles'].map((c) => (
            <button key={c} onClick={() => setSelectedCat(c)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${selectedCat === c ? 'bg-primary text-white' : 'text-on-surface-variant hover:bg-surface-container'}`}>
              {c === 'all' ? 'All Sectors' : c}
            </button>
          ))}
        </div>
        <input type="text" placeholder="Search HS code or keyword..." value={search} onChange={(e) => setSearch(e.target.value)}
          className="w-full sm:w-72 px-3 py-1.5 bg-surface-container-low rounded-lg text-xs text-on-surface placeholder:text-outline focus:outline-none" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-7 bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/20 overflow-hidden flex flex-col text-xs">
          <div className="p-3 bg-surface-container-low flex items-center justify-between font-bold border-b border-outline-variant/20">
            <span>Active Classification Matrix</span>
            <span className="text-[10px] text-outline font-normal">WCO HS 2022/2024</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-surface-container-low text-outline uppercase font-semibold text-[10px]">
                  <th className="py-2.5 px-3">HS Code</th>
                  <th className="py-2.5 px-3">Nomenclature</th>
                  <th className="py-2.5 px-3">Duty / VAT</th>
                  <th className="py-2.5 px-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-container-high/30">
                {filtered.map((row) => (
                  <tr key={row.hs} onClick={() => { setSimHs(row.hs); onTriggerToast({ title: 'HS Loaded in Simulator', message: `${row.hs} queued for tare calculation.` }); }}
                    className="hover:bg-surface-container-low/60 cursor-pointer transition-colors">
                    <td className="py-3 px-3 font-mono font-bold text-primary">{row.hs}</td>
                    <td className="py-3 px-3">
                      <div className="font-semibold text-on-surface">{row.name}</div>
                      <div className="text-[10px] text-outline">{row.rule}</div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-on-surface font-semibold">{row.duty}</span>
                      <span className="block text-[10px] text-secondary">{row.vat}</span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="px-2 py-0.5 rounded-full bg-secondary-container/30 text-secondary text-[10px] font-semibold">Conforming</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="lg:col-span-5 bg-surface-container-lowest p-5 rounded-xl shadow-sm border border-outline-variant/30 flex flex-col gap-4 text-xs">
          <div className="border-b border-outline-variant/20 pb-2">
            <h3 className="text-sm font-bold text-on-surface">Rule Logic Validator</h3>
            <p className="text-[11px] text-outline">Simulate export tare compliance per Gazette 2378/42</p>
          </div>
          <div className="space-y-3">
            <div>
              <label className="text-[10px] text-outline uppercase block mb-1">Target HS Subheading</label>
              <input type="text" value={simHs} onChange={(e) => setSimHs(e.target.value)}
                className="w-full px-3 py-1.5 bg-surface-container-low rounded-lg font-mono font-semibold" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-outline uppercase block mb-1">Gross Mass (KG)</label>
                <input type="number" value={grossWt} onChange={(e) => setGrossWt(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-1.5 bg-surface-container-low rounded-lg font-mono font-semibold" />
              </div>
              <div>
                <label className="text-[10px] text-outline uppercase block mb-1">Euro Pallets</label>
                <input type="number" value={pallets} onChange={(e) => setPallets(parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-1.5 bg-surface-container-low rounded-lg font-mono font-semibold" />
              </div>
            </div>
            <div className="p-3 bg-surface-container-low rounded-lg space-y-1.5 border border-outline-variant/20">
              <div className="flex justify-between">
                <span className="text-outline">Tare Allowance (22.5kg/pal):</span>
                <span className="font-mono font-bold text-primary">{(pallets * 22.5).toFixed(2)} KG</span>
              </div>
              <div className="flex justify-between">
                <span className="text-outline">Computed Net Mass:</span>
                <span className="font-mono font-bold text-secondary">{netCalculated.toFixed(2)} KG</span>
              </div>
            </div>
            <button onClick={() => onTriggerToast({ title: 'Validation Complete', message: 'Invoice complies with zero-tariff ASYCUDA Green Channel.' })}
              className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary/90 text-white font-semibold flex items-center justify-center gap-1.5 shadow-sm">
              <span className="material-symbols-outlined text-[16px]">play_arrow</span>
              <span>Test Commercial Cargo Against Rules</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
