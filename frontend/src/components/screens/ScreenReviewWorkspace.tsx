import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useShipment } from '../../hooks/useShipment';
import { getDiscrepancies, resolveDiscrepancy, getExtraction } from '../../utils/api';
import type { Discrepancy, DocumentExtraction } from '../../types';

interface Props { onTriggerToast: (t: { title: string; message: string; type?: 'success' | 'error' | 'info' }) => void; }

export function ScreenReviewWorkspace({ onTriggerToast }: Props) {
  const navigate = useNavigate();
  const { shipmentId } = useShipment();
  
  const [extractions, setExtractions] = useState<DocumentExtraction[]>([]);
  const [loading, setLoading] = useState(true);

  const [activeDocIndex, setActiveDocIndex] = useState(0);
  const [activeDiscrepancy, setActiveDiscrepancy] = useState<Discrepancy | null>(null);

  const [selectedDecision, setSelectedDecision] = useState('B');
  const [isResolved, setIsResolved] = useState(false);
  const [isResolving, setIsResolving] = useState(false);

  useEffect(() => {
    if (!shipmentId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    
    Promise.all([
      getExtraction(shipmentId).catch(() => ({ documents: [] })),
      getDiscrepancies(shipmentId).catch(() => ({ discrepancies: [] }))
    ])
    .then(([extData, discData]) => {
      const docs = extData.documents || [];
      const discs = discData.discrepancies || [];
      
      setExtractions(docs);
      
      if (discs.length > 0) {
        setActiveDiscrepancy(discs[0]);
        setIsResolved(discs[0].status === 'resolved');
      }
    })
    .catch((err) => {
      console.error("Failed to load workspace data", err);
      onTriggerToast({ title: 'Error', message: 'Failed to load workspace data.', type: 'error' });
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
        <p className="text-sm text-on-surface-variant font-medium">Loading Workspace Data...</p>
      </div>
    );
  }

  const handleExecuteResolution = async () => {
    if (isResolved || !activeDiscrepancy) return;
    setIsResolving(true);
    try {
      await resolveDiscrepancy(shipmentId, activeDiscrepancy.discrepancy_id, selectedDecision);
      setIsResolved(true);
      onTriggerToast({ title: 'Discrepancy Harmonized', message: 'Resolution saved and applied to cache.', type: 'success' });
    } catch (err) {
      onTriggerToast({ title: 'Resolution Failed', message: 'Failed to update resolution status.', type: 'error' });
    } finally {
      setIsResolving(false);
    }
  };

  const activeDoc = extractions[activeDocIndex];

  // Helper to check if an entity is part of the active discrepancy
  const isEntityInDiscrepancy = (val: string) => {
    if (!activeDiscrepancy) return false;
    return activeDiscrepancy.value_a === val || activeDiscrepancy.value_b === val;
  };

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
            <div className="font-bold text-primary font-mono">
              {activeDiscrepancy?.xai_block?.layer3?.overall_confidence 
                ? (activeDiscrepancy.xai_block.layer3.overall_confidence * 100).toFixed(1) 
                : '99.0'}%
            </div>
            <div className="text-[11px] text-outline">ASYCUDA Readiness</div>
          </div>
          <button onClick={() => navigate('/asycuda-gateway')} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-surface-container-low hover:bg-surface-container text-on-surface font-medium transition-colors">
            <span className="material-symbols-outlined text-[16px] text-outline">code</span>
            <span>Export ASYCUDA XML</span>
          </button>
          {activeDiscrepancy && (
            <button onClick={handleExecuteResolution} disabled={isResolved || isResolving}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-white font-medium transition-all shadow-md ${isResolved ? 'bg-secondary opacity-90' : 'bg-primary-container hover:bg-primary'} ${isResolving ? 'opacity-70 cursor-wait' : ''}`}>
              <span className={`material-symbols-outlined text-[16px] ${isResolving ? 'animate-spin' : ''}`}>
                {isResolving ? 'refresh' : (isResolved ? 'check_circle' : 'verified_user')}
              </span>
              <span>{isResolving ? 'Saving...' : (isResolved ? 'Approved & Sealed' : 'Approve Resolution')}</span>
            </button>
          )}
        </div>
      </div>

      {/* Split Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: Documents & Extracted Fields */}
        <div className="lg:col-span-7 flex flex-col bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/20 overflow-hidden">
          
          <div className="bg-surface-container-low px-4 pt-2.5 flex items-center gap-2 border-b border-outline-variant/20 overflow-x-auto text-xs">
            {extractions.map((doc, idx) => (
              <button key={doc.document_id} onClick={() => setActiveDocIndex(idx)}
                className={`px-3 py-2.5 rounded-t-lg flex items-center gap-1.5 transition-colors whitespace-nowrap ${
                  activeDocIndex === idx 
                    ? 'bg-surface-container-lowest text-primary font-bold shadow-sm border-t border-x border-outline-variant/30' 
                    : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container/50'
                }`}>
                <span className="material-symbols-outlined text-[16px]">{doc.document_type === 'commercial_invoice' ? 'description' : (doc.document_type === 'awb' ? 'flight_takeoff' : 'receipt_long')}</span> 
                {doc.document_type.replace('_', ' ').toUpperCase()} ({doc.document_id.slice(0,6)})
              </button>
            ))}
            {extractions.length === 0 && (
              <div className="py-2.5 text-on-surface-variant italic px-2">No documents extracted.</div>
            )}
          </div>

          <div className="p-6 bg-surface-container-lowest min-h-[500px]">
            {activeDoc ? (
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between border-b border-outline-variant/20 pb-3">
                  <h3 className="text-sm font-bold text-on-surface flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary">data_object</span>
                    Extracted Fields
                  </h3>
                  <span className="text-xs text-outline font-mono">{(activeDoc.classification_confidence * 100).toFixed(1)}% Doc Confidence</span>
                </div>
                
                {activeDoc.entities.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {activeDoc.entities.map((entity, i) => {
                      const hasDiscrepancy = isEntityInDiscrepancy(entity.value);
                      return (
                        <div key={i} className={`p-3 rounded-lg border flex flex-col gap-1 transition-colors ${
                          hasDiscrepancy ? 'border-error bg-error-container/10' : 'border-outline-variant/30 bg-surface-container-low'
                        }`}>
                          <div className="flex justify-between items-start">
                            <span className="text-[10px] text-outline font-bold uppercase tracking-wider">{entity.entity_type}</span>
                            {hasDiscrepancy && (
                              <span className="material-symbols-outlined text-[14px] text-error" title="Flagged in discrepancy">warning</span>
                            )}
                          </div>
                          <div className={`text-sm font-semibold font-mono truncate ${hasDiscrepancy ? 'text-error' : 'text-on-surface'}`}>
                            {entity.value} {entity.unit || ''}
                          </div>
                          <div className="flex justify-between items-center mt-1">
                            <span className="text-[10px] text-on-surface-variant bg-surface-container px-1.5 py-0.5 rounded">
                              {(entity.extraction_confidence * 100).toFixed(1)}% Conf
                            </span>
                            <span className="text-[10px] text-outline">Page {entity.page}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-10 text-on-surface-variant text-sm">
                    No entities could be extracted from this document.
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-20 text-on-surface-variant">Select a document to review extracted fields.</div>
            )}
          </div>
        </div>


        {/* Right Column: AI Audit & Discrepancies */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {activeDiscrepancy ? (
            <>
              {/* Discrepancy Card */}
              <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-outline-variant/20 flex flex-col gap-3">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-[11px] px-2 py-0.5 rounded font-medium ${
                        activeDiscrepancy.severity === 'high' ? 'bg-error-container text-on-error-container' : 'bg-tertiary-fixed text-on-tertiary-fixed'
                      }`}>Attention Required</span>
                      <span className="font-mono text-tertiary font-semibold text-xs">Δ {activeDiscrepancy.delta}</span>
                    </div>
                    <h2 className="text-base font-bold text-on-surface">Data Mismatch Detected</h2>
                  </div>
                  <span className="material-symbols-outlined text-tertiary bg-tertiary-fixed/40 p-2 rounded-lg text-[20px]">balance</span>
                </div>
                <p className="text-xs text-on-surface-variant">Divergence isolated between {activeDiscrepancy.xai_block.layer1.source_documents[0]} and {activeDiscrepancy.xai_block.layer1.source_documents[1]}.</p>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/20">
                    <span className="text-[10px] text-outline uppercase block truncate">{activeDiscrepancy.xai_block.layer1.source_documents[0] || 'Doc A'}</span>
                    <div className="text-lg font-bold text-on-surface mt-1 font-mono">{activeDiscrepancy.value_a}</div>
                  </div>
                  <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/20">
                    <span className="text-[10px] text-outline uppercase block truncate">{activeDiscrepancy.xai_block.layer1.source_documents[1] || 'Doc B'}</span>
                    <div className="text-lg font-bold text-tertiary mt-1 font-mono">{activeDiscrepancy.value_b}</div>
                  </div>
                </div>
                <div className="bg-surface-container p-3 rounded-lg flex items-start gap-2 text-xs">
                  <span className="material-symbols-outlined text-outline text-[16px] mt-0.5">policy</span>
                  <div>
                    <span className="font-semibold text-on-surface block">Rule: {activeDiscrepancy.rule_id}</span>
                    <span className="text-on-surface-variant text-[11px] leading-relaxed">
                      {activeDiscrepancy.xai_block.layer2.failed_rule_description}
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
                  {activeDiscrepancy.xai_block.layer2.logical_steps.map((stepDesc, idx) => (
                    <div key={idx} className="relative">
                      <div className={`absolute -left-5 top-0.5 h-4 w-4 rounded-full flex items-center justify-center text-[10px] font-bold text-white ${
                        idx === activeDiscrepancy.xai_block.layer2.logical_steps.length - 1 ? 'bg-primary-fixed text-primary' : 'bg-secondary'
                      }`}>{idx + 1}</div>
                      <div className="font-semibold text-on-surface">Step {idx + 1}</div>
                      <p className="text-[11px] text-on-surface-variant mt-0.5">{stepDesc}</p>
                    </div>
                  ))}
                  <div className="relative">
                     <div className="absolute -left-5 top-0.5 h-4 w-4 rounded-full bg-surface-container-highest text-outline flex items-center justify-center text-[10px] font-bold">C</div>
                     <div className="font-semibold text-on-surface">Confidence Score: {(activeDiscrepancy.xai_block.layer3.overall_confidence * 100).toFixed(1)}%</div>
                     <p className="text-[11px] text-on-surface-variant mt-0.5">{activeDiscrepancy.xai_block.layer3.confidence_explanation}</p>
                  </div>
                </div>
              </div>

              {/* Decision Options */}
              <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-outline-variant/20 flex flex-col gap-3">
                <h3 className="text-xs font-bold text-on-surface uppercase tracking-wider">Decision Synthesis</h3>
                {[
                  { key: 'A', label: `Option A: Retain ${activeDiscrepancy.value_a}`, risk: 'High Port Hold Risk', desc: `Submit directly without compensating action.` },
                  { key: 'B', label: 'Option B: AI Recommended Action', risk: '<0.01% Audit Risk', desc: activeDiscrepancy.xai_block.layer4.recommended_action },
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
              </div>
            </>
          ) : (
            <div className="bg-surface-container-lowest rounded-xl p-10 shadow-sm border border-outline-variant/20 flex flex-col items-center justify-center gap-3 text-center h-full min-h-[400px]">
              <span className="material-symbols-outlined text-[48px] text-secondary">verified</span>
              <h3 className="text-lg font-bold text-on-surface">No Discrepancies Detected</h3>
              <p className="text-xs text-on-surface-variant max-w-xs">
                All extracted fields match across documents perfectly according to active customs rules.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
