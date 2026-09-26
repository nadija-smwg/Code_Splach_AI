import { useState, useRef, useEffect, type DragEvent, type ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadShipment, getActiveRules, type RuleCheck } from '../../utils/api';
import { useShipment } from '../../hooks/useShipment';

interface Props { onTriggerToast: (t: { title: string; message: string; type?: 'error' | 'info' | 'success' }) => void; }

interface QueuedFile { name: string; size: string; file: File; status: string; icon: string; }

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function docIcon(name: string): string {
  const n = name.toLowerCase();
  if (n.includes('invoice')) return 'receipt';
  if (n.includes('awb') || n.includes('airway')) return 'flight_takeoff';
  if (n.includes('packing') || n.includes('pack')) return 'format_list_numbered';
  if (n.includes('bill') || n.includes('lading')) return 'directions_boat';
  if (n.includes('delivery')) return 'local_shipping';
  return 'description';
}

export function ScreenDossiers({ onTriggerToast }: Props) {
  const navigate = useNavigate();
  const { setShipmentId } = useShipment();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [fileStack, setFileStack] = useState<QueuedFile[]>([]);
  const [progress, setProgress] = useState(0);
  const [activeChecks, setActiveChecks] = useState<RuleCheck[]>([]);
  const [isLoadingChecks, setIsLoadingChecks] = useState(true);

  useEffect(() => {
    getActiveRules().then(setActiveChecks).catch(() => {}).finally(() => setIsLoadingChecks(false));
  }, []);

  const addFiles = (incoming: File[]) => {
    const pdfs = incoming.filter(f => f.name.toLowerCase().endsWith('.pdf'));
    if (pdfs.length !== incoming.length) {
      onTriggerToast({ title: 'Invalid File Type', message: 'Only PDF files are accepted.', type: 'error' });
    }
    setFileStack(prev => {
      const names = new Set(prev.map(f => f.name));
      const novel = pdfs.filter(f => !names.has(f.name)).map(f => ({
        name: f.name,
        size: formatBytes(f.size),
        file: f,
        status: 'Queued for OCR',
        icon: docIcon(f.name),
      }));
      return [...prev, ...novel];
    });
    if (pdfs.length > 0) {
      onTriggerToast({ title: `${pdfs.length} File${pdfs.length > 1 ? 's' : ''} Queued`, message: 'Ready for OCR ingestion pipeline.' });
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    addFiles(Array.from(e.dataTransfer.files));
  };

  const handleBrowse = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) addFiles(Array.from(e.target.files));
  };

  const handleProcessDossier = async () => {
    if (fileStack.length === 0) {
      onTriggerToast({ title: 'No Files', message: 'Please add PDF files before processing.', type: 'error' });
      return;
    }

    setIsProcessing(true);
    setProgress(10);

    try {
      const files = fileStack.map(f => f.file);
      setProgress(30);

      const response = await uploadShipment(files);
      setProgress(50);

      setShipmentId(response.shipment_id);
      
      // We must WAIT for the AI pipeline to finish processing the documents in the background.
      // Otherwise, if we navigate immediately, the database won't have the results yet,
      // and the next screen will fall back to the demo data.
      let isDone = false;
      while (!isDone) {
        // Wait 3 seconds between polls
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        try {
          const { api } = await import('../../utils/api');
          const { data: statusRes } = await api.get(`/upload/${response.shipment_id}/status`);
          
          if (statusRes.status === 'completed' || (statusRes.status as string) === 'done') {
            isDone = true;
            setProgress(100);
          } else if (statusRes.status === 'error') {
            throw new Error('AI Pipeline encountered an error during extraction.');
          } else {
            // Still processing, maybe update progress slightly to show activity
            setProgress(p => Math.min(p + 5, 95));
          }
        } catch (pollErr) {
          console.warn("Polling error (might be temporary):", pollErr);
        }
      }

      onTriggerToast({
        title: 'Dossier Transmitted & Processed',
        message: `Shipment ${response.shipment_id.slice(0, 8)}... AI Extraction Complete.`,
        type: 'success',
      });

      setTimeout(() => navigate('/discrepancies'), 800);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed. Is the backend running?';
      onTriggerToast({ title: 'Upload Failed', message: msg, type: 'error' });
      setIsProcessing(false);
      setProgress(0);
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-1.5 text-primary text-xs font-semibold uppercase tracking-wider">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary animate-ping"></span>
            Ingestion Pipeline • Node CMB-04
          </div>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">Dossier Ingestion &amp; Automated Multi-Doc Parser</h1>
          <p className="text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Drop shipping dossiers to auto-extract structured line items, verify against Sri Lanka Customs schedules, and audit for cross-document consistency.
          </p>
        </div>

      </div>

      {/* Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative rounded-xl bg-surface-container-lowest p-8 md:p-10 shadow-sm border-2 border-dashed transition-all cursor-pointer text-center ${isDragging ? 'border-primary bg-primary-fixed/20' : 'border-outline-variant/40 hover:border-primary/50'}`}
      >
        <input ref={fileInputRef} type="file" multiple accept=".pdf" className="hidden" onChange={handleBrowse} />
        <div className="w-16 h-16 rounded-full bg-primary-fixed/50 flex items-center justify-center mx-auto mb-4 text-primary shadow-sm">
          <span className="material-symbols-outlined text-[32px]">cloud_upload</span>
        </div>
        <h2 className="text-base font-semibold text-on-surface">Drag &amp; drop shipping dossiers or click to browse</h2>
        <p className="text-xs text-on-surface-variant mt-1 mb-5 max-w-md mx-auto">Multi-page PDF supported. Parallel OCR stream starts instantly.</p>
        <div className="flex flex-wrap items-center justify-center gap-2 max-w-2xl mx-auto mb-6 text-xs text-on-surface-variant">
          {[
            { icon: 'description',             label: 'Commercial Invoice' },
            { icon: 'inventory_2',             label: 'Packing List' },
            { icon: 'flight_takeoff',          label: 'Air Waybill (AWB)' },
            { icon: 'directions_boat',         label: 'Bill of Lading (B/L)' },
          ].map((t) => (
            <span key={t.label} className="px-3 py-1 rounded-full bg-surface-container-high flex items-center gap-1">
              <span className="material-symbols-outlined text-primary text-[14px]">{t.icon}</span> {t.label}
            </span>
          ))}
        </div>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3" onClick={e => e.stopPropagation()}>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="bg-primary text-white hover:bg-primary-container px-5 py-2.5 rounded-lg text-xs font-semibold flex items-center gap-2 shadow-md transition-all active:scale-95"
          >
            <span className="material-symbols-outlined text-[16px]">folder_open</span> Browse Files
          </button>
        </div>
      </div>

      {/* Queued Stack + Process Button */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Pre-Check Matrix */}
        <div className="lg:col-span-6 bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-outline-variant/20 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-outline-variant/20 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-secondary-container/30 flex items-center justify-center text-secondary">
                <span className="material-symbols-outlined text-[18px]">fact_check</span>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-on-surface">Pre-Check Matrix Engine</h3>
                <p className="text-[11px] text-on-surface-variant">Automated validation against Sri Lanka Customs rules</p>
              </div>
            </div>
            <span className="bg-secondary-container/20 text-on-secondary-container text-xs px-2.5 py-1 rounded-full font-semibold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span> 4 Checks
            </span>
          </div>
          <div className="space-y-2 text-xs">
            {isLoadingChecks ? (
              <div className="p-3 text-on-surface-variant animate-pulse">Loading checks from backend...</div>
            ) : (
              activeChecks.map((item) => (
                <div key={item.id} className="bg-surface-container-low rounded-lg p-3 flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2">
                    <span className="material-symbols-outlined text-secondary text-[18px]">check_circle</span>
                    <div>
                      <div className="font-semibold text-on-surface">{item.label}</div>
                      <p className="text-on-surface-variant mt-0.5">{item.description}</p>
                    </div>
                  </div>
                  <span className="text-secondary font-semibold bg-secondary-container/20 px-2 py-0.5 rounded shrink-0">{item.status}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* File Stack + Submit */}
        <div className="lg:col-span-6 bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-outline-variant/20 flex flex-col gap-4">
          {isProcessing ? (
            <div className="flex flex-col items-center justify-center h-full flex-1 gap-5 py-8">
              <div className="relative w-32 h-32 flex items-center justify-center">
                <svg className="absolute inset-0 w-full h-full text-surface-container-highest" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="none" strokeWidth="8" stroke="currentColor" />
                </svg>
                <svg className="absolute inset-0 w-full h-full text-primary drop-shadow-md" viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
                  <circle cx="50" cy="50" r="45" fill="none" strokeWidth="8" stroke="currentColor" strokeDasharray="283" strokeDashoffset={283 - (progress / 100) * 283} className="transition-all duration-500 ease-out" strokeLinecap="round" />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-primary">
                  <span className="text-2xl font-mono font-bold tracking-tighter">{Math.round(progress)}%</span>
                </div>
              </div>
              <div className="text-center animate-pulse">
                <h3 className="text-base font-semibold text-on-surface mb-1">AI Pipeline Processing</h3>
                <p className="text-xs text-on-surface-variant max-w-[250px] mx-auto">
                  Extracting entities, normalizing data, and cross-examining {fileStack.length} document{fileStack.length !== 1 ? 's' : ''}...
                </p>
              </div>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between border-b border-outline-variant/20 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-primary-fixed/40 flex items-center justify-center text-primary">
                    <span className="material-symbols-outlined text-[18px]">layers</span>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-on-surface">Queued Dossier Stack</h3>
                    <p className="text-[11px] text-on-surface-variant">{fileStack.length} document{fileStack.length !== 1 ? 's' : ''} queued</p>
                  </div>
                </div>
                <button onClick={() => setFileStack([])} className="text-xs text-outline hover:text-on-surface transition-colors">Clear All</button>
              </div>

              {fileStack.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-xs text-on-surface-variant gap-2">
                  <span className="material-symbols-outlined text-[32px] text-outline">inbox</span>
                  <span>No files queued. Drop PDFs above to begin.</span>
                </div>
              ) : (
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
                      <button onClick={() => setFileStack(prev => prev.filter((_, i) => i !== idx))}
                        className="p-1 hover:bg-surface-container rounded text-outline hover:text-error">
                        <span className="material-symbols-outlined text-[16px]">close</span>
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <button
                onClick={handleProcessDossier}
                disabled={fileStack.length === 0}
                className="w-full bg-primary hover:bg-primary-container text-white py-3 px-4 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-md transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed mt-auto"
              >
                <span className="material-symbols-outlined text-[18px]">bolt</span>
                <span>Process Dossier ({fileStack.length} Document{fileStack.length !== 1 ? 's' : ''})</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
