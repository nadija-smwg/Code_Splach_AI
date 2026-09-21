import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface Props { onTriggerToast: (t: { title: string; message: string }) => void; }

export function ScreenDossiers({ onTriggerToast }: Props) {
  const navigate = useNavigate();
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [fileStack, setFileStack] = useState([
    { name: 'Commercial_Invoice_CI-9942.pdf', size: '1.4 MB', status: 'OCR Parsed (14 Lines)', icon: 'receipt' },
    { name: 'HAWB-88190.pdf', size: '820 KB', status: 'OCR Parsed (Flight UL302)', icon: 'flight_takeoff' },
    { name: 'Packing_List_PL-402.pdf', size: '1.1 MB', status: '24 Pallets Mapped', icon: 'format_list_numbered' },
    { name: 'Certificate_of_Origin.pdf', size: '640 KB', status: 'GSP Form A Verified', icon: 'verified' }
  ]);

  const handleProcessDossier = () => {
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
      onTriggerToast({ title: 'Dossier Transmitted', message: 'Forwarded to Review Workspace with 99.4% confidence.' });
      navigate('/review-workspace');
    }, 1200);
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-1.5 text-primary text-xs font-semibold uppercase tracking-wider">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary animate-ping"></span>
            Ingestion Pipeline • Node CMB-04
          </div>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">Dossier Ingestion & Automated Multi-Doc Parser</h1>
          <p className="text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Drop shipping dossiers to auto-extract structured line items, verify against Sri Lanka Customs schedules, and audit for cross-document consistency.
          </p>
        </div>
        <div className="bg-surface-container px-4 py-2 rounded-lg flex items-center gap-3 shadow-sm">
          <span className="material-symbols-outlined text-secondary text-[20px]">security</span>
          <div>
            <div className="text-[10px] text-on-surface-variant uppercase">ASYCUDA Gateway</div>
            <div className="text-xs font-semibold font-mono">Direct Enclave Ready</div>
          </div>
        </div>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => { e.preventDefault(); setIsDragging(false); onTriggerToast({ title: 'Files Queued', message: 'Initiating Vision Transformer OCR stream...' }); }}
        className={`relative rounded-xl bg-surface-container-lowest p-8 md:p-10 shadow-sm border-2 border-dashed transition-all cursor-pointer text-center ${isDragging ? 'border-primary bg-primary-fixed/20' : 'border-outline-variant/40 hover:border-primary/50'}`}
      >
        <div className="w-16 h-16 rounded-full bg-primary-fixed/50 flex items-center justify-center mx-auto mb-4 text-primary shadow-sm">
          <span className="material-symbols-outlined text-[32px]">cloud_upload</span>
        </div>
        <h2 className="text-base font-semibold text-on-surface">Drag & drop shipping dossiers or browse workstation files</h2>
        <p className="text-xs text-on-surface-variant mt-1 mb-5 max-w-md mx-auto">Multi-page PDF, Scanned TIFF, and EDIFACT manifests supported. Parallel OCR stream starts instantly.</p>
        <div className="flex flex-wrap items-center justify-center gap-2 max-w-2xl mx-auto mb-6 text-xs text-on-surface-variant">
          {[
            { icon: 'description', label: 'Commercial Invoice' },
            { icon: 'inventory_2', label: 'Packing List' },
            { icon: 'flight_takeoff', label: 'House Airway Bill (HAWB)' },
            { icon: 'directions_boat', label: 'Bill of Lading (B/L)' },
          ].map((t) => (
            <span key={t.label} className="px-3 py-1 rounded-full bg-surface-container-high flex items-center gap-1">
              <span className="material-symbols-outlined text-primary text-[14px]">{t.icon}</span> {t.label}
            </span>
          ))}
        </div>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button onClick={() => onTriggerToast({ title: 'Native File Picker', message: 'Select your export paperwork from desktop.' })}
            className="bg-primary text-white hover:bg-primary-container px-5 py-2.5 rounded-lg text-xs font-semibold flex items-center gap-2 shadow-md transition-all active:scale-95">
            <span className="material-symbols-outlined text-[16px]">folder_open</span> Browse Files
          </button>
          <button onClick={() => onTriggerToast({ title: 'MAS LK-7704 Ingested', message: 'Loaded 4 high-res export documents into OCR pipeline.' })}
            className="bg-surface-container-low hover:bg-surface-container text-on-surface px-5 py-2.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all shadow-sm">
            <span className="material-symbols-outlined text-secondary text-[16px]">auto_stories</span>
            Load Sample Dossier (MAS Holdings LK-7704)
          </button>
        </div>
      </div>

      {/* Pre-Check Matrix + Queued Stack */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-6 bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-outline-variant/20 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-outline-variant/20 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-secondary-container/30 flex items-center justify-center text-secondary">
                <span className="material-symbols-outlined text-[18px]">fact_check</span>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-on-surface">Pre-Check Matrix Engine</h3>
                <p className="text-[11px] text-on-surface-variant">Automated validation against Sri Lanka Customs Regulatory rules</p>
              </div>
            </div>
            <span className="bg-secondary-container/20 text-on-secondary-container text-xs px-2.5 py-1 rounded-full font-semibold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span> 4 Passed
            </span>
          </div>
          <div className="space-y-2 text-xs">
            {[
              { label: 'HS Code 6109.10 Concordance', desc: 'Cotton apparel harmonized between Commercial Invoice and HAWB cargo description.' },
              { label: 'Incoterms & Apportionment', desc: 'Ocean freight breakdown mapped without duty base variance (CIF Colombo).' },
              { label: 'TIN/EORI Registry Live', desc: 'Declarant TIN LK-1029482910 validated with Inland Revenue Department.' },
              { label: 'Tare Weight Tolerance', desc: 'Gross weight 14,820 kg aligns with container VGM within SOLAS margin.' },
            ].map((item) => (
              <div key={item.label} className="bg-surface-container-low rounded-lg p-3 flex items-start justify-between gap-3">
                <div className="flex items-start gap-2">
                  <span className="material-symbols-outlined text-secondary text-[18px]">check_circle</span>
                  <div>
                    <div className="font-semibold text-on-surface">{item.label}</div>
                    <p className="text-on-surface-variant mt-0.5">{item.desc}</p>
                  </div>
                </div>
                <span className="text-secondary font-semibold bg-secondary-container/20 px-2 py-0.5 rounded shrink-0">Verified</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-6 bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-outline-variant/20 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-outline-variant/20 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-primary-fixed/40 flex items-center justify-center text-primary">
                <span className="material-symbols-outlined text-[18px]">layers</span>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-on-surface">Queued Dossier Stack</h3>
                <p className="text-[11px] text-on-surface-variant">Batch LK-7704-EXPORT • MAS Holdings Ltd</p>
              </div>
            </div>
            <button onClick={() => { setFileStack([]); onTriggerToast({ title: 'Stack Cleared', message: 'Ready for new paperwork ingest.' }); }}
              className="text-xs text-outline hover:text-on-surface transition-colors">Clear All</button>
          </div>
          <div className="space-y-2">
            {fileStack.map((file, idx) => (
              <div key={idx} className="bg-surface-container-low rounded-lg p-2.5 px-3 flex items-center justify-between text-xs shadow-sm">
                <div className="flex items-center gap-3 truncate">
                  <div className="w-8 h-8 rounded bg-primary-fixed/30 text-primary flex items-center justify-center shrink-0">
                    <span className="material-symbols-outlined text-[18px]">{file.icon}</span>
                  </div>
                  <div className="truncate">
                    <div className="font-semibold text-on-surface truncate">{file.name}</div>
                    <div className="text-[11px] text-on-surface-variant flex items-center gap-1.5 mt-0.5">
                      <span>{file.size}</span><span>•</span>
                      <span className="text-secondary font-medium">{file.status}</span>
                    </div>
                  </div>
                </div>
                <button onClick={() => navigate('/review-workspace')} className="p-1 hover:bg-surface-container rounded text-outline hover:text-on-surface">
                  <span className="material-symbols-outlined text-[16px]">visibility</span>
                </button>
              </div>
            ))}
          </div>
          <div className="p-3 bg-surface-container-low rounded-lg flex flex-col gap-1 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-medium text-on-surface flex items-center gap-1">
                <span className="material-symbols-outlined text-secondary text-[16px]">shield</span> Overall Confidence
              </span>
              <span className="font-bold text-secondary font-mono">99.4% Cross-Audit</span>
            </div>
            <div className="w-full bg-surface-container-highest rounded-full h-2 overflow-hidden mt-1">
              <div className="bg-secondary h-2 rounded-full" style={{ width: '99.4%' }}></div>
            </div>
          </div>
          <button onClick={handleProcessDossier} disabled={isProcessing}
            className="w-full bg-primary hover:bg-primary-container text-white py-3 px-4 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-md transition-all active:scale-95">
            <span className={`material-symbols-outlined text-[18px] ${isProcessing ? 'animate-spin' : ''}`}>
              {isProcessing ? 'sync' : 'bolt'}
            </span>
            <span>{isProcessing ? 'Transmitting to ASYCUDA Enclave...' : `Process Dossier (${fileStack.length} Documents)`}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
