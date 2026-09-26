import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useShipment } from '../../hooks/useShipment';
import { getDiscrepancies, getExtraction, getKeyFields, saveFieldResolution } from '../../utils/api';
import type { Discrepancy, DocumentExtraction, FieldAssertion, ResolvedKeyField } from '../../types';
import { KeyFieldReconciliationPanel } from '../review/KeyFieldReconciliationPanel';

interface Props { onTriggerToast: (t: { title: string; message: string; type?: 'success' | 'error' | 'info' }) => void; }

export function ScreenReviewWorkspace({ onTriggerToast }: Props) {
  const navigate = useNavigate();
  const { shipmentId } = useShipment();
  
  const [extractions, setExtractions] = useState<DocumentExtraction[]>([]);
  const [keyFields, setKeyFields] = useState<ResolvedKeyField[]>([]);
  const [selectedAssertion, setSelectedAssertion] = useState<FieldAssertion | null>(null);
  const [loading, setLoading] = useState(true);

  const [activeDocIndex, setActiveDocIndex] = useState(0);
  const [activeDiscrepancy, setActiveDiscrepancy] = useState<Discrepancy | null>(null);
  const [discrepancies, setDiscrepancies] = useState<Discrepancy[]>([]);

  const [resolvingFieldId, setResolvingFieldId] = useState<string | null>(null);

  useEffect(() => {
    if (!shipmentId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    
    Promise.all([
      getExtraction(shipmentId).catch(() => ({ documents: [] })),
      getDiscrepancies(shipmentId).catch(() => ({ discrepancies: [] })),
      getKeyFields(shipmentId).catch(() => ({ fields: [] }))
    ])
    .then(([extData, discData, fieldData]) => {
      const docs = extData.documents || [];
      const discs = discData.discrepancies || [];
      
      setExtractions(docs);
      setKeyFields(fieldData.fields || []);
      setDiscrepancies(discs);
      
      if (discs.length > 0) {
        setActiveDiscrepancy(discs[0]);
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
    if (!activeDiscrepancy) return;
    const field = keyFields.find(item => item.canonical_field_id === activeDiscrepancy.canonical_field_id);
    if (field) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      onTriggerToast({ title: 'Choose a resolution', message: `Use the source values or corrected-value form for ${field.label}.`, type: 'info' });
    }
  };

  const handleFieldResolution = async (
    field: ResolvedKeyField,
    resolution: { source_assertion_id?: string; manual_value?: string; reason?: string },
  ) => {
    if (!shipmentId) return;
    setResolvingFieldId(field.canonical_field_id);
    try {
      const result = await saveFieldResolution(shipmentId, {
        canonical_field_id: field.canonical_field_id,
        ...resolution,
      });
      setKeyFields(current => current.map(item =>
        item.canonical_field_id === field.canonical_field_id ? result.field : item,
      ));
      const refreshed = await getDiscrepancies(shipmentId);
      setDiscrepancies(refreshed.discrepancies || []);
      setActiveDiscrepancy(current => current?.canonical_field_id === field.canonical_field_id ? null : current);
      onTriggerToast({ title: 'Resolution saved', message: `${field.label} now uses the reviewer-approved value.`, type: 'success' });
    } catch {
      onTriggerToast({ title: 'Resolution failed', message: 'The reviewer decision could not be saved.', type: 'error' });
    } finally {
      setResolvingFieldId(null);
    }
  };

  const activeDoc = extractions[activeDocIndex];
  const unresolvedFieldCount = keyFields.filter(field =>
    field.status === 'conflict' || field.status === 'warning' || field.status === 'pending',
  ).length;

  const isEntityOutlier = (documentId: string, entity: { entity_type: string; value: string; page: number }) =>
    keyFields.some(field => field.assertions.some(assertion =>
      assertion.document_id === documentId && assertion.entity_type === entity.entity_type &&
      assertion.raw_value === entity.value && assertion.page === entity.page && assertion.is_outlier
    ));

  const selectAssertion = (assertion: FieldAssertion) => {
    setSelectedAssertion(assertion);
    const documentIndex = extractions.findIndex(doc => doc.document_id === assertion.document_id);
    if (documentIndex >= 0) setActiveDocIndex(documentIndex);
    const relatedDiscrepancy = discrepancies.find(discrepancy => discrepancy.canonical_field_id === assertion.canonical_field_id);
    if (relatedDiscrepancy) setActiveDiscrepancy(relatedDiscrepancy);
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      {/* Top Context Bar */}
      <div className="bg-surface-container-lowest rounded-xl p-4 shadow-sm border border-outline-variant/20 flex flex-col xl:flex-row items-start xl:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 bg-surface-container-low px-3 py-1.5 rounded-lg text-xs">
            <span className="material-symbols-outlined text-primary text-[18px]">inventory_2</span>
            <div>
              <span className="text-[10px] text-outline block">Dossier ID</span>
              <span className="font-bold text-on-surface font-mono">CLX-{shipmentId.slice(0, 8).toUpperCase()}</span>
            </div>
          </div>
          <div className="flex items-center gap-1.5 bg-primary-fixed/30 text-tertiary px-3 py-1 rounded-full text-xs font-semibold">
            <span className={`h-2 w-2 rounded-full ${unresolvedFieldCount ? 'bg-primary-container animate-pulse' : 'bg-secondary'}`}></span>
            <span>{unresolvedFieldCount ? 'In review' : 'Fields resolved'}</span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 w-full xl:w-auto justify-between xl:justify-end text-xs">
          <div className="flex items-center gap-2 bg-surface-container-low px-3 py-1.5 rounded-lg">
            <div className="font-bold text-primary font-mono">
              {activeDiscrepancy?.xai_block?.layer3?.overall_confidence 
                ? (activeDiscrepancy.xai_block.layer3.overall_confidence * 100).toFixed(1) 
                : '99.0'}%
            </div>
            <div className="text-[11px] text-outline">Match confidence</div>
          </div>
          <button onClick={() => navigate('/asycuda-gateway')} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-surface-container-low hover:bg-surface-container text-on-surface font-medium transition-colors">
            <span className="material-symbols-outlined text-[16px] text-outline">code</span>
            <span>Export CUSDEC XML</span>
          </button>
          {activeDiscrepancy && (
            <button onClick={handleExecuteResolution}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-white font-medium transition-all shadow-md bg-primary-container hover:bg-primary">
              <span className="material-symbols-outlined text-[16px]">rule</span>
              <span>Resolve selected field</span>
            </button>
          )}
        </div>
      </div>

      <KeyFieldReconciliationPanel
        fields={keyFields}
        onSelectAssertion={selectAssertion}
        onResolveField={handleFieldResolution}
        resolvingFieldId={resolvingFieldId}
      />

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
          
          {activeDoc?.warnings && activeDoc.warnings.length > 0 && (
            <div className="bg-error/10 text-error px-5 py-3.5 border-b border-error/20 flex flex-col gap-1.5 text-sm">
              <div className="flex items-center gap-2 font-bold">
                <span className="material-symbols-outlined text-[18px]">warning</span>
                Extraction Warning
              </div>
              <ul className="list-disc list-inside pl-1 text-xs opacity-90">
                {activeDoc.warnings.map((warn, i) => (
                  <li key={i}>{warn}</li>
                ))}
              </ul>
            </div>
          )}

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
                      const hasDiscrepancy = isEntityOutlier(activeDoc.document_id, entity);
                      const isSelected = selectedAssertion?.document_id === activeDoc.document_id &&
                        selectedAssertion.entity_type === entity.entity_type &&
                        selectedAssertion.raw_value === entity.value && selectedAssertion.page === entity.page;
                      return (
                        <div key={i} className={`p-3 rounded-lg border flex flex-col gap-1 transition-colors ${
                          hasDiscrepancy ? 'border-error bg-error-container/10' : isSelected ? 'border-primary bg-primary-fixed/15' : 'border-outline-variant/30 bg-surface-container-low'
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
                <h2 className="text-base font-bold text-on-surface">Field values differ</h2>
                  </div>
                  <span className="material-symbols-outlined text-tertiary bg-tertiary-fixed/40 p-2 rounded-lg text-[20px]">balance</span>
                </div>
                <p className="text-xs text-on-surface-variant">Compare the values found in these two source documents.</p>
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
                    How this was found
                  </h3>
                  <span className="text-[10px] text-outline">Review steps</span>
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

              <div className="bg-primary-fixed/15 rounded-xl p-4 border border-primary/20 text-xs">
                <h3 className="font-bold text-on-surface">Manual resolution</h3>
                <p className="text-on-surface-variant mt-1">Use the field panel above to select verified evidence or enter a corrected value with a reason. The decision is saved and remains traceable to the source documents.</p>
              </div>
            </>
          ) : (
            <div className="bg-surface-container-lowest rounded-xl p-10 shadow-sm border border-outline-variant/20 flex flex-col items-center justify-center gap-3 text-center h-full min-h-[400px]">
              <span className="material-symbols-outlined text-[48px] text-secondary">verified</span>
              <h3 className="text-lg font-bold text-on-surface">No Discrepancies Detected</h3>
              <p className="text-xs text-on-surface-variant max-w-xs">
                No differences were found in the available CUSDEC fields.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
