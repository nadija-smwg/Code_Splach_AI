import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useShipment } from '../../hooks/useShipment';
import { getDiscrepancies, resolveDiscrepancy } from '../../utils/api';
import type { Discrepancy } from '../../types';

interface Props { onTriggerToast: (t: { title: string; message: string; type?: 'success' | 'error' | 'info' }) => void; }

export function ScreenReviewWorkspace({ onTriggerToast }: Props) {
  const navigate = useNavigate();
  const { shipmentId } = useShipment();
  const [discrepancy, setDiscrepancy] = useState<Discrepancy | null>(null);
  const [loading, setLoading] = useState(true);

  const [selectedDecision, setSelectedDecision] = useState('B');
  const [isHawbView, setIsHawbView] = useState(false);
  const [isOcrActive, setIsOcrActive] = useState(true);
  const [isResolved, setIsResolved] = useState(false);
  const [isResolving, setIsResolving] = useState(false);

  useEffect(() => {
    if (!shipmentId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    getDiscrepancies(shipmentId)
      .then((data) => {
        if (data.discrepancies && data.discrepancies.length > 0) {
          setDiscrepancy(data.discrepancies[0]);
          setIsResolved(data.discrepancies[0].status === 'resolved');
        }
      })
      .catch((err) => {
        console.error("Failed to load discrepancies", err);
        onTriggerToast({ title: 'Error', message: 'Failed to load discrepancy data.', type: 'error' });
      })
      .finally(() => {
        setLoading(false);
      });
  }, [shipmentId, onTriggerToast]);

  if (!shipmentId) {
    return (
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-20 flex flex-col items-center justify-center gap-4">
        <span className="material-symbols-outlined text-[64px] text-outline">description</span>
        <h2 className="text-xl font-bold text-on-surface">No Document Selected</h2>
        <p className="text-sm text-on-surface-variant max-w-md text-center">
          Please select or upload a dossier from the main dashboard to begin the review process.
        </p>
        <button onClick={() => navigate('/dossiers')} className="mt-4 bg-primary text-white px-6 py-2.5 rounded-lg text-sm font-semibold shadow-sm hover:bg-primary-container transition-colors">
          Go to Dossiers
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-20 flex flex-col items-center justify-center gap-4">
        <span className="material-symbols-outlined text-[48px] text-primary animate-spin">refresh</span>
        <p className="text-sm text-on-surface-variant font-medium">Loading AI Audit Trace...</p>
      </div>
    );
  }

  if (!discrepancy) {
    return (
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-20 flex flex-col items-center justify-center gap-4">
        <span className="material-symbols-outlined text-[64px] text-secondary">check_circle</span>
        <h2 className="text-xl font-bold text-on-surface">No Discrepancies Found</h2>
        <p className="text-sm text-on-surface-variant text-center max-w-md">
          The AI engine found zero discrepancies for this dossier. It is ready for ASYCUDA export.
        </p>
        <button onClick={() => navigate('/asycuda-gateway')} className="mt-4 bg-secondary text-white px-6 py-2.5 rounded-lg text-sm font-semibold shadow-sm hover:opacity-90 transition-colors">
          Proceed to Gateway
        </button>
      </div>
    );
  }

  const handleExecuteResolution = async () => {
    if (isResolved) return;
    setIsResolving(true);
    try {
      await resolveDiscrepancy(shipmentId, discrepancy.discrepancy_id, selectedDecision);
      setIsResolved(true);
      onTriggerToast({ title: 'Discrepancy Harmonized', message: 'Resolution saved and applied to cache.', type: 'success' });
    } catch (err) {
      onTriggerToast({ title: 'Resolution Failed', message: 'Failed to update resolution status.', type: 'error' });
    } finally {
      setIsResolving(false);
    }
  };

  const { layer1, layer2, layer3, layer4 } = discrepancy.xai_block;
  
  // Safe document names
  const docA = layer1?.source_documents?.[0] || 'Document A';
  const docB = layer1?.source_documents?.[1] || 'Document B';

  const valA = discrepancy.value_a;
  const valB = discrepancy.value_b;

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      {/* Top Context Bar */}
      <div className="bg-surface-container-lowest rounded-xl p-4 shadow-sm border border-outline-variant/20 flex flex-col xl:flex-row items-start xl:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 bg-surface-container-low px-3 py-1.5 rounded-lg text-xs">
            <span className="material-symbols-outlined text-primary text-[18px]">inventory_2</span>
            <div>
              <span className="text-[10px] text-outline uppercase block">Ref ID</span>
              <span className="font-bold text-on-surface font-mono">CLX-{shipmentId.slice(0, 8).toUpperCase()}</span>
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-on-surface-variant">
            <span className="font-medium text-on-surface">MAS Holdings</span>
            <span className="material-symbols-outlined text-outline text-[14px]">arrow_forward</span>
            <span className="font-medium text-on-surface">Marks & Spencer UK</span>
            <span className="text-outline">•</span>
            <span className="bg-surface-container px-2 py-0.5 rounded text-[11px]">LKCMB Air Cargo</span>
          </div>
          <div className="flex items-center gap-1.5 bg-primary-fixed/30 text-tertiary px-3 py-1 rounded-full text-xs font-semibold">
            <span className={`h-2 w-2 rounded-full ${isResolved ? 'bg-secondary' : 'bg-primary-container animate-pulse'}`}></span>
            <span>{isResolved ? 'Review Complete' : 'Review Active'}</span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 w-full xl:w-auto justify-between xl:justify-end text-xs">
          <div className="flex items-center gap-2 bg-surface-container-low px-3 py-1.5 rounded-lg">
            <div className="font-bold text-primary font-mono">{layer3?.overall_confidence ? (layer3.overall_confidence * 100).toFixed(1) : '88.4'}%</div>
            <div className="text-[11px] text-outline">ASYCUDA Readiness</div>
          </div>
          <button onClick={() => navigate('/asycuda-gateway')} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-surface-container-low hover:bg-surface-container text-on-surface font-medium transition-colors">
            <span className="material-symbols-outlined text-[16px] text-outline">code</span>
            <span>Export ASYCUDA XML</span>
          </button>
          <button onClick={handleExecuteResolution} disabled={isResolved || isResolving}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-white font-medium transition-all shadow-md ${isResolved ? 'bg-secondary opacity-90' : 'bg-primary-container hover:bg-primary'} ${isResolving ? 'opacity-70 cursor-wait' : ''}`}>
            <span className={`material-symbols-outlined text-[16px] ${isResolving ? 'animate-spin' : ''}`}>
              {isResolving ? 'refresh' : (isResolved ? 'check_circle' : 'verified_user')}
            </span>
            <span>{isResolving ? 'Saving...' : (isResolved ? 'Approved & Sealed' : 'Approve Resolution')}</span>
          </button>
        </div>
      </div>

      {/* Split Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left AI Column */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {/* Discrepancy Card */}
          <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-outline-variant/20 flex flex-col gap-3">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-[11px] px-2 py-0.5 rounded font-medium ${
                    discrepancy.severity === 'high' ? 'bg-error-container text-on-error-container' : 'bg-tertiary-fixed text-on-tertiary-fixed'
                  }`}>Attention Required</span>
                  <span className="font-mono text-tertiary font-semibold text-xs">Δ {discrepancy.delta}</span>
                </div>
                <h2 className="text-base font-bold text-on-surface">Data Mismatch Detected</h2>
              </div>
              <span className="material-symbols-outlined text-tertiary bg-tertiary-fixed/40 p-2 rounded-lg text-[20px]">balance</span>
            </div>
            <p className="text-xs text-on-surface-variant">Divergence isolated between {docA} and {docB}.</p>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-surface-container-low p-3 rounded-lg">
                <span className="text-[10px] text-outline uppercase block truncate">{docA}</span>
                <div className="text-lg font-bold text-on-surface mt-1 font-mono">{valA}</div>
                <span className="text-[11px] text-on-surface-variant">Extracted Value</span>
              </div>
              <div className="bg-surface-container-low p-3 rounded-lg">
                <span className="text-[10px] text-outline uppercase block truncate">{docB}</span>
                <div className="text-lg font-bold text-tertiary mt-1 font-mono">{valB}</div>
                <span className="text-[11px] text-on-surface-variant">Extracted Value</span>
              </div>
            </div>
            <div className="bg-surface-container p-3 rounded-lg flex items-start gap-2 text-xs">
              <span className="material-symbols-outlined text-outline text-[16px] mt-0.5">policy</span>
              <div>
                <span className="font-semibold text-on-surface block">Rule: {discrepancy.rule_id}</span>
                <span className="text-on-surface-variant text-[11px] leading-relaxed">
                  {layer2?.failed_rule_description}
                </span>
              </div>
            </div>
          </div>

          {/* XAI Trace */}
          <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-outline-variant/20 flex flex-col gap-3">
            <div className="flex items-center justify-between border-b border-outline-variant/20 pb-2">
              <h3 className="text-xs font-bold text-on-surface uppercase tracking-wider flex items-center gap-1.5">
                <span className="material-symbols-outlined text-primary text-[18px]">account_tree</span>
                Explainable AI Audit Trace
              </h3>
              <span className="text-[10px] text-outline font-mono">Deterministic Path</span>
            </div>
            <div className="relative pl-5 flex flex-col gap-4 text-xs mt-1">
              <div className="absolute left-2 top-2 bottom-2 w-0.5 bg-surface-container-highest"></div>
              {layer2?.logical_steps?.map((stepDesc, idx) => (
                <div key={idx} className="relative">
                  <div className={`absolute -left-5 top-0.5 h-4 w-4 rounded-full flex items-center justify-center text-[10px] font-bold text-white ${
                    idx === layer2.logical_steps.length - 1 ? 'bg-primary-fixed text-primary' : 'bg-secondary'
                  }`}>{idx + 1}</div>
                  <div className="font-semibold text-on-surface">Step {idx + 1}</div>
                  <p className="text-[11px] text-on-surface-variant mt-0.5">{stepDesc}</p>
                </div>
              ))}
              <div className="relative">
                 <div className="absolute -left-5 top-0.5 h-4 w-4 rounded-full bg-surface-container-highest text-outline flex items-center justify-center text-[10px] font-bold">C</div>
                 <div className="font-semibold text-on-surface">Confidence Score: {(layer3?.overall_confidence ? layer3.overall_confidence * 100 : 0).toFixed(1)}%</div>
                 <p className="text-[11px] text-on-surface-variant mt-0.5">{layer3?.confidence_explanation}</p>
              </div>
            </div>
          </div>

          {/* Decision Options */}
          <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-outline-variant/20 flex flex-col gap-3">
            <h3 className="text-xs font-bold text-on-surface uppercase tracking-wider">Counterfactual Decision Synthesis</h3>
            {[
              { key: 'A', label: `Option A: Retain ${valA}`, risk: 'High Port Hold Risk', desc: `Submit ${valA} directly without compensating action.` },
              { key: 'B', label: 'Option B: AI Recommended Action', risk: '<0.01% Audit Risk', desc: layer4?.recommended_action },
            ].map((opt) => (
              <div key={opt.key} onClick={() => !isResolved && setSelectedDecision(opt.key)}
                className={`p-3 rounded-lg text-xs border transition-all ${isResolved ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'} ${selectedDecision === opt.key ? 'border-primary bg-primary-fixed/20 shadow-sm' : 'border-outline-variant/30 bg-surface-container-low'}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <input type="radio" checked={selectedDecision === opt.key} readOnly className="accent-primary" />
                    <span className="font-semibold text-on-surface">{opt.label}</span>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded ${opt.key === 'B' ? 'bg-secondary-container/20 text-secondary font-semibold' : 'text-outline bg-surface-container'}`}>{opt.risk}</span>
                </div>
                <p className="text-[11px] text-on-surface-variant mt-1 pl-5">{opt.desc}</p>
              </div>
            ))}
            <button onClick={handleExecuteResolution} disabled={isResolved || isResolving}
              className={`w-full mt-2 py-2.5 px-4 rounded-lg text-white text-xs font-semibold shadow-md flex items-center justify-center gap-2 transition-all ${isResolved ? 'bg-secondary' : 'bg-primary hover:bg-primary-container'}`}>
              <span className="material-symbols-outlined text-[16px]">{isResolved ? 'check' : 'auto_fix_high'}</span>
              <span>{isResolved ? 'Resolution Applied' : 'Auto-Apply Selection & Resolve'}</span>
            </button>
          </div>
        </div>

        {/* Right Document Viewer */}
        <div className="lg:col-span-7 flex flex-col bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/20 overflow-hidden">
          <div className="bg-surface-container-low px-4 pt-2.5 flex items-center justify-between border-b border-outline-variant/20 overflow-x-auto gap-3 text-xs">
            <div className="flex items-center gap-1">
              <button onClick={() => setIsHawbView(false)} className={`px-3 py-1.5 rounded-t-lg flex items-center gap-1.5 transition-colors ${!isHawbView ? 'bg-surface-container-lowest text-primary font-semibold shadow-sm border-t border-x border-outline-variant/30' : 'text-on-surface-variant hover:text-on-surface'}`}>
                <span className="material-symbols-outlined text-[14px]">description</span> {docA}
              </button>
              <button onClick={() => setIsHawbView(true)} className={`px-3 py-1.5 rounded-t-lg flex items-center gap-1.5 transition-colors ${isHawbView ? 'bg-surface-container-lowest text-primary font-semibold shadow-sm border-t border-x border-outline-variant/30' : 'text-on-surface-variant hover:text-on-surface'}`}>
                <span className="material-symbols-outlined text-[14px]">flight_takeoff</span> {docB}
              </button>
            </div>
            <button onClick={() => setIsOcrActive(!isOcrActive)}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all mb-1 ${isOcrActive ? 'bg-primary-fixed text-primary' : 'bg-surface-container text-outline'}`}>
              <span className="material-symbols-outlined text-[14px]">{isOcrActive ? 'layers' : 'layers_clear'}</span>
              <span>{isOcrActive ? 'OCR Active' : 'OCR Muted'}</span>
            </button>
          </div>

          <div className="p-6 bg-surface-container-low min-h-[500px] flex items-center justify-center overflow-auto">
            <div className="relative w-full max-w-[580px] bg-white p-6 rounded-lg shadow-md border border-slate-200 text-xs flex flex-col gap-4">
              <div className="flex justify-between items-start border-b pb-3">
                <div>
                  <div className="font-bold text-sm text-slate-900 tracking-tight">MAS HOLDINGS (PVT) LTD</div>
                  <div className="text-[11px] text-slate-500">Export Division • Colombo 02, Sri Lanka</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">TIN: LK-992019402 • EORI: GB982301928000</div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-bold text-indigo-700 uppercase">{isHawbView ? docB : docA}</div>
                  <div className="text-[10px] text-slate-400 mt-1">Date: 2025-05-18</div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 bg-slate-50 p-2.5 rounded text-[11px]">
                <div>
                  <span className="font-bold text-slate-600 block uppercase text-[9px]">Consignee</span>
                  <span className="font-semibold text-slate-900">Marks & Spencer PLC</span>
                  <span className="text-slate-500 block">London W2 1NW, United Kingdom</span>
                </div>
                <div>
                  <span className="font-bold text-slate-600 block uppercase text-[9px]">Shipment Details</span>
                  <span className="text-slate-700 block">Port: LKCMB (Bandaranaike Intl)</span>
                  <span className="text-slate-700 block">Destination: LHR (London Heathrow)</span>
                </div>
              </div>
              
              <div className="relative bg-slate-50 p-3 rounded-lg border border-slate-200 mt-4">
                <div className="flex justify-between text-[10px] text-slate-500 uppercase font-semibold mb-2">
                  <span>Target Extraction Zone</span><span>{discrepancy.field.replace('|', ' vs ')}</span>
                </div>
                <div className={`relative p-3 rounded-lg border-2 transition-all ${isHawbView ? 'border-tertiary bg-tertiary-container/10' : 'border-indigo-600 bg-indigo-50/80'}`}
                  style={{ opacity: isOcrActive ? 1 : 0.3 }}>
                  <div className="absolute -top-3 right-2 bg-indigo-700 text-white px-2 py-0.5 rounded text-[10px] font-semibold flex items-center gap-1 shadow-sm">
                    <span className="material-symbols-outlined text-[11px]">auto_awesome</span>
                    <span>{((layer3?.extraction_confidence || 1) * 100).toFixed(1)}% Conf</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-[10px] font-semibold uppercase text-indigo-900 block truncate max-w-[200px]">
                        {isHawbView ? docB : docA}
                      </span>
                      <span className="text-xl font-bold font-mono text-indigo-700">
                        {isHawbView ? valB : valA}
                      </span>
                    </div>
                    <span className="text-[11px] font-semibold px-2 py-1 rounded bg-white text-indigo-700 border border-indigo-200">Extracted Entity</span>
                  </div>
                </div>
              </div>
              <div className="flex justify-between text-[10px] text-slate-400 pt-2 border-t mt-auto">
                <span>Electronic Signature ID: LK-MAS-AUTH-7712</span>
                <span>Document ID: {isHawbView ? 'B22' : 'CI-9942'}</span>
              </div>
            </div>
          </div>

          <div className="p-3 bg-surface-container-low flex items-center justify-between text-xs text-outline border-t border-outline-variant/20">
            <button onClick={() => setIsHawbView(!isHawbView)} className="flex items-center gap-1 text-primary font-semibold hover:underline">
              <span className="material-symbols-outlined text-[16px]">swap_horiz</span>
              <span>{isHawbView ? `Switch to ${docA}` : `Switch to ${docB}`}</span>
            </button>
            <span className="text-[11px]">Document Parser v4.2 • WCO Certified</span>
          </div>
        </div>
      </div>
    </div>
  );
}
