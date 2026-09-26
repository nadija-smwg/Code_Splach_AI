import { useState } from 'react';

interface Props { onTriggerToast: (t: { title: string; message: string }) => void; }

export function ScreenSettings({ onTriggerToast }: Props) {
  const [tolerance, setTolerance] = useState(2.5);
  const [autoSubmit, setAutoSubmit] = useState(true);

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-outline-variant/20 pb-4">
        <div>
          <div className="text-xs text-primary font-semibold">Workspace settings</div>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">Review settings</h1>
          <p className="text-xs md:text-sm text-on-surface-variant mt-1">Set the discrepancy tolerance used when comparing extracted CUSDEC fields.</p>
        </div>
        <button onClick={() => onTriggerToast({ title: 'Settings saved', message: 'Your review settings have been updated.' })}
          className="px-4 py-2 rounded-lg bg-primary hover:bg-primary/90 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm">
          <span className="material-symbols-outlined text-[16px]">save</span>
          <span>Save Changes</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 text-xs">
        {/* Export information */}
        <div className="bg-surface-container-lowest p-5 rounded-xl border border-outline-variant/30 shadow-sm flex flex-col justify-between gap-4">
          <div>
            <div className="flex items-center justify-between border-b border-outline-variant/20 pb-3">
              <h3 className="text-sm font-semibold text-on-surface">CUSDEC export</h3>
              <span className="px-2 py-0.5 rounded-full bg-secondary-container/60 text-secondary font-semibold text-[10px]">Available</span>
            </div>
            <div className="space-y-3 mt-4">
              <div>
                <label className="text-[10px] text-outline block mb-1">Export format</label>
                <input type="text" readOnly value="CUSDEC XML"
                  className="w-full px-3 py-1.5 bg-surface-container-low rounded-lg font-mono text-[11px]" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-outline block mb-1">Source</label>
                  <input type="text" readOnly value="Resolved dossier fields" className="w-full px-3 py-1.5 bg-surface-container-low rounded-lg text-[11px]" />
                </div>
                <div>
                  <label className="text-[10px] text-outline block mb-1">Submission</label>
                  <input type="text" readOnly value="Manual after export" className="w-full px-3 py-1.5 bg-surface-container-low rounded-lg text-[11px]" />
                </div>
              </div>
            </div>
          </div>
          <div className="pt-3 border-t border-outline-variant/20 flex items-center justify-between">
            <span className="text-outline">Review the XML before submission.</span>
            <button onClick={() => onTriggerToast({ title: 'Export information checked', message: 'CUSDEC XML is generated from resolved fields.' })}
              className="px-3 py-1 rounded bg-surface-container hover:bg-surface-container-high font-semibold">
              Check export
            </button>
          </div>
        </div>

        {/* AI Tolerance Card */}
        <div className="bg-surface-container-lowest p-5 rounded-xl border border-outline-variant/30 shadow-sm flex flex-col justify-between gap-4">
          <div>
            <div className="flex items-center justify-between border-b border-outline-variant/20 pb-3">
              <h3 className="text-sm font-semibold text-on-surface">Discrepancy tolerance</h3>
              <span className="px-2 py-0.5 rounded bg-primary-fixed text-primary text-[10px] font-bold">Active</span>
            </div>
            <div className="space-y-4 mt-4">
              <div>
                <div className="flex justify-between font-semibold mb-1">
                  <span>Weight Variance Tolerance</span>
                  <span className="font-mono text-primary">{tolerance}% max</span>
                </div>
                <input type="range" min="0" max="10" step="0.1" value={tolerance} onChange={(e) => setTolerance(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-surface-container-highest rounded-lg appearance-none cursor-pointer accent-primary" />
              </div>
              <div className="flex items-center justify-between pt-2">
                <div>
                  <div className="font-medium text-on-surface">Automatically mark matching fields</div>
                  <div className="text-[11px] text-outline">Fields with no differences are left unflagged.</div>
                </div>
                <input type="checkbox" checked={autoSubmit} onChange={() => setAutoSubmit(!autoSubmit)} className="w-4 h-4 accent-primary cursor-pointer" />
              </div>
            </div>
          </div>
          <div className="pt-3 border-t border-outline-variant/20 text-[11px] text-secondary font-medium">
            These settings apply to document comparison in this workspace.
          </div>
        </div>
      </div>
    </div>
  );
}
