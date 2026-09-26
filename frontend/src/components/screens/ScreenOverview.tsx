import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { listDossiers } from '../../utils/api';
import { useShipment } from '../../hooks/useShipment';
import { prefersReducedMotion, isMobile } from '../../hooks/useScrollAnimations';

gsap.registerPlugin(ScrollTrigger);

interface Props { onTriggerToast: (t: { title: string; message: string; type?: 'error' | 'info' | 'success' }) => void; }

interface DossierDoc {
  document_id: string;
  original_name: string;
  document_type: string | null;
  status: string;
}

interface DossierItem {
  dossier_id: string;
  status: string;
  created_at: string | null;
  document_count: number;
  documents: DossierDoc[];
}

const NAVY = '#0d1b3e';

function statusBadge(status: string) {
  switch (status) {
    case 'done':
      return { label: 'Completed', bg: 'bg-green-500/20', text: 'text-green-400', dot: 'bg-green-400' };
    case 'processing':
      return { label: 'Processing', bg: 'bg-amber-500/20', text: 'text-amber-400', dot: 'bg-amber-400 animate-pulse' };
    case 'error':
      return { label: 'Error', bg: 'bg-red-500/20', text: 'text-red-400', dot: 'bg-red-400' };
    default:
      return { label: 'Pending', bg: 'bg-gray-500/20', text: 'text-gray-400', dot: 'bg-gray-400' };
  }
}

function channelBadge(channel: string) {
  switch (channel) {
    case 'green':
      return { label: 'Ready', bg: 'bg-green-500/15', text: 'text-green-400', dot: 'bg-green-400' };
    case 'review':
      return { label: 'Needs review', bg: 'bg-amber-500/15', text: 'text-amber-400', dot: 'bg-amber-400' };
    case 'hold':
      return { label: 'Blocked', bg: 'bg-red-500/15', text: 'text-red-400', dot: 'bg-red-400' };
    default:
      return { label: 'Queued', bg: 'bg-gray-500/15', text: 'text-gray-400', dot: 'bg-gray-400' };
  }
}

export function ScreenOverview({ onTriggerToast }: Props) {
  const navigate = useNavigate();
  const { setShipmentId } = useShipment();
  const [dossiers, setDossiers] = useState<DossierItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [channelOverrides, setChannelOverrides] = useState<Record<string, string>>({});

  const heroRef       = useRef<HTMLElement>(null);
  const heroBgRef     = useRef<HTMLImageElement>(null);
  const heroContentRef = useRef<HTMLDivElement>(null);
  const statusBadgeRef = useRef<HTMLDivElement>(null);
  const titleRef      = useRef<HTMLHeadingElement>(null);
  const subtitleRef   = useRef<HTMLParagraphElement>(null);
  const buttonsRef    = useRef<HTMLDivElement>(null);
  // Dossier section
  const dossierWrapRef  = useRef<HTMLDivElement>(null);
  const tableRef        = useRef<HTMLElement>(null);
  const tableHeadRef    = useRef<HTMLDivElement>(null);
  const emptyStateRef   = useRef<HTMLDivElement>(null);
  const rowsRef         = useRef<HTMLTableSectionElement>(null);

  // ── Mount animation: cinematic hero entrance ─────────────────────────
  useEffect(() => {
    const ctx = gsap.context(() => {
      if (prefersReducedMotion) {
        // Instantly reveal everything, no animation
        gsap.set([heroRef.current, statusBadgeRef.current, titleRef.current,
                  subtitleRef.current, buttonsRef.current], { opacity: 1, y: 0, scale: 1 });
        return;
      }

      // 1. Background image: start zoomed in, settle to natural scale
      gsap.fromTo(heroBgRef.current,
        { scale: 1.08 },
        { scale: 1, duration: 2.2, ease: 'power2.out' }
      );

      // 2. Whole hero section fades in
      gsap.fromTo(heroRef.current,
        { opacity: 0 },
        { opacity: 1, duration: 0.6, ease: 'power2.out' }
      );

      // 3. Staggered content entrance
      const tl = gsap.timeline({ defaults: { ease: 'power3.out' }, delay: 0.2 });

      tl.fromTo(statusBadgeRef.current,
        { y: -14, opacity: 0, scale: 0.9 },
        { y: 0, opacity: 1, scale: 1, duration: 0.55, ease: 'back.out(1.4)' }
      );

      tl.fromTo(titleRef.current ? Array.from(titleRef.current.children) : [],
        { y: 24, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.65, stagger: 0.15 },
        '-=0.2'
      );

      tl.fromTo(subtitleRef.current,
        { y: 16, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.5 },
        '-=0.25'
      );

      tl.fromTo(
        buttonsRef.current ? Array.from(buttonsRef.current.children) : [],
        { y: 16, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.45, stagger: 0.1 },
        '-=0.2'
      );

      // 4. Hero scroll-out parallax — content scrolls up & fades; bg scrolls slower
      ScrollTrigger.create({
        trigger: heroRef.current,
        start: 'top top',
        end: 'bottom top',
        scrub: 1,
        onUpdate: (self) => {
          const p = self.progress;
          const mobile = isMobile();

          // Hero text content fades and drifts up as user scrolls
          if (heroContentRef.current) {
            gsap.set(heroContentRef.current, {
              y: p * (mobile ? 40 : 70),
              opacity: 1 - p * 1.4,
            });
          }

          // Background image parallax — moves at ~40% speed and very subtly zooms
          if (heroBgRef.current) {
            gsap.set(heroBgRef.current, {
              y: p * (mobile ? 30 : 55),
              scale: 1 + p * 0.04,
            });
          }
        },
      });
    });
    return () => ctx.revert();
  }, []);


  // -- ScrollTrigger: Full dossier section coordinated reveal --
  useEffect(() => {
    const ctx = gsap.context(() => {
      if (prefersReducedMotion) {
        gsap.set([dossierWrapRef.current, tableRef.current, tableHeadRef.current, emptyStateRef.current],
          { opacity: 1, y: 0, scale: 1 });
        return;
      }

      // 1. Outer wrapper slides up as it enters viewport
      gsap.fromTo(dossierWrapRef.current,
        { opacity: 0, y: 60 },
        {
          opacity: 1, y: 0,
          duration: 1.0,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: dossierWrapRef.current,
            start: 'top 92%',
            toggleActions: 'play none none none',
          },
        }
      );

      // 2. Card scales up subtly from 0.97
      gsap.fromTo(tableRef.current,
        { scale: 0.97, opacity: 0 },
        {
          scale: 1, opacity: 1,
          duration: 0.9,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: dossierWrapRef.current,
            start: 'top 90%',
            toggleActions: 'play none none none',
          },
        }
      );

      // 3. Header bar children stagger in
      if (tableHeadRef.current) {
        gsap.fromTo(Array.from(tableHeadRef.current.children),
          { opacity: 0, y: 12 },
          {
            opacity: 1, y: 0,
            duration: 0.55,
            stagger: 0.1,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: dossierWrapRef.current,
              start: 'top 88%',
              toggleActions: 'play none none none',
            },
          }
        );
      }

      // 4. Empty state items animate in sequence
      if (emptyStateRef.current) {
        gsap.fromTo(Array.from(emptyStateRef.current.children),
          { opacity: 0, y: 20 },
          {
            opacity: 1, y: 0,
            duration: 0.6,
            stagger: 0.12,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: dossierWrapRef.current,
              start: 'top 85%',
              toggleActions: 'play none none none',
            },
          }
        );
      }
    });
    return () => ctx.revert();
  }, []);

  // -- Animate table rows when dossiers load (ScrollTrigger) --
  useEffect(() => {
    if (!loading && dossiers.length > 0 && rowsRef.current) {
      if (prefersReducedMotion) {
        gsap.set(rowsRef.current.querySelectorAll('tr'), { opacity: 1, y: 0 });
        return;
      }
      gsap.fromTo(
        rowsRef.current.querySelectorAll('tr'),
        { opacity: 0, y: 18 },
        {
          opacity: 1, y: 0,
          duration: 0.5,
          stagger: 0.08,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: rowsRef.current,
            start: 'top 95%',
            toggleActions: 'play none none none',
          },
        }
      );
    }
  }, [loading, dossiers]);

  const fetchDossiers = () => {
    setLoading(true);
    listDossiers()
      .then(res => setDossiers(res.dossiers || []))
      .catch(() => setDossiers([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchDossiers(); }, []);

  const handleInspect = (dossierId: string) => {
    setShipmentId(dossierId);
    navigate('/discrepancies');
  };

  const getChannel = (d: DossierItem): string => {
    if (channelOverrides[d.dossier_id]) return channelOverrides[d.dossier_id];
    return d.status === 'done' ? 'green' : d.status === 'error' ? 'hold' : d.status === 'processing' ? 'review' : 'pending';
  };

  const toggleChannel = (dossierId: string, currentChannel: string) => {
    const next = currentChannel === 'green' ? 'review' : 'green';
    setChannelOverrides(prev => ({ ...prev, [dossierId]: next }));
    onTriggerToast({
      title: 'Review status updated',
      message: `Dossier ${dossierId.slice(0, 8)}... is ${next === 'green' ? 'ready' : 'marked for review'}.`,
      type: next === 'green' ? 'success' : 'info',
    });
  };

  // ── GSAP hover helpers ───────────────────────────────────────────────
  const onRowEnter = (e: React.MouseEvent<HTMLTableRowElement>) =>
    gsap.to(e.currentTarget, { x: 4, duration: 0.2, ease: 'power1.out' });
  const onRowLeave = (e: React.MouseEvent<HTMLTableRowElement>) =>
    gsap.to(e.currentTarget, { x: 0, duration: 0.25, ease: 'power1.inOut' });

  const onBtnEnter = (e: React.MouseEvent<HTMLButtonElement>) =>
    gsap.to(e.currentTarget, { scale: 1.045, duration: 0.18, ease: 'power1.out' });
  const onBtnLeave = (e: React.MouseEvent<HTMLButtonElement>) =>
    gsap.to(e.currentTarget, { scale: 1, duration: 0.2, ease: 'power1.inOut' });
  const onBtnClick = (e: React.MouseEvent<HTMLButtonElement>) =>
    gsap.fromTo(e.currentTarget, { scale: 0.93 }, { scale: 1, duration: 0.3, ease: 'elastic.out(1, 0.4)' });

  return (
    <div className="w-full flex flex-col">

      {/* ── Hero Banner ───────────────────────────────────────────── */}
      <section
        ref={heroRef}
        style={{ opacity: 0 }}
        className="relative w-full min-h-screen overflow-hidden shadow-2xl bg-surface-container"
      >
        <div className="relative w-full min-h-screen flex flex-col justify-center">
          <img
            ref={heroBgRef}
            alt="ClearanceX document review workspace"
            className="absolute inset-0 w-full h-full object-cover object-center"
            src="/screen.png"
          />
          {/* Deep layered overlays */}
          <div className="absolute inset-0 bg-gradient-to-t from-[#060d1f]/95 via-[#0d1b3e]/55 to-transparent" />
          
          {/* Top gradient for header contrast */}
          <div className="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-[#060d1f]/80 to-transparent" />
          <div
            className="absolute inset-0"
            style={{
              background:
                'radial-gradient(ellipse at 20% 80%, rgba(91,143,212,0.18) 0%, transparent 60%), radial-gradient(ellipse at 80% 20%, rgba(13,27,62,0.3) 0%, transparent 60%)',
            }}
          />
          {/* Shimmer line */}
          <div
            className="absolute top-0 left-0 right-0 h-px"
            style={{
              background: 'linear-gradient(90deg, transparent, rgba(91,143,212,0.6), transparent)',
              animation: 'shimmerLine 3s ease-in-out infinite',
            }}
          />

          {/* Content: pushed below the 80px transparent header */}
          <div ref={heroContentRef} className="relative z-10 max-w-7xl mx-auto w-full px-4 sm:px-8 pt-28 pb-10 flex flex-col gap-4">
            {/* System Status */}
            <div
              ref={statusBadgeRef}
              style={{ opacity: 0 }}
              className="inline-flex items-center self-start gap-2 bg-white/10 backdrop-blur-md px-3.5 py-1.5 rounded-full shadow-sm text-xs border border-white/15"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
              </span>
              <span className="text-emerald-400 font-semibold">Document review</span>
            </div>

            {/* Title — each child is animated independently for word-by-word reveal */}
            <div>
              <h1 ref={titleRef} className="text-4xl md:text-5xl lg:text-6xl font-black text-white tracking-tight leading-tight drop-shadow-lg">
                <span style={{ display: 'inline-block', opacity: 0 }}>Clearance<span style={{ color: '#5b8fd4' }}>X</span></span>{' '}
                <span style={{ display: 'inline-block', opacity: 0 }} className="font-light text-white/80">Document review</span>
              </h1>
              <p
                ref={subtitleRef}
                style={{ opacity: 0 }}
                className="text-white/75 text-sm md:text-base max-w-2xl mt-2 leading-relaxed"
              >
                Compare extracted CUSDEC fields across the documents in each dossier.
              </p>
            </div>

            {/* Buttons */}
            <div ref={buttonsRef} className="flex flex-wrap items-center gap-3 pt-1">
              <button
                onMouseEnter={onBtnEnter}
                onMouseLeave={onBtnLeave}
                onClick={(e) => { onBtnClick(e); navigate('/dossiers'); }}
                style={{ background: 'linear-gradient(135deg, #1a3a7a 0%, #0d1b3e 100%)' }}
                className="inline-flex items-center justify-center gap-2.5 text-white px-7 py-3 rounded-xl text-sm font-semibold shadow-lg border border-white/10"
              >
                <span className="material-symbols-outlined text-[20px]">add</span>
                <span>Add dossier</span>
              </button>
              <button
                onMouseEnter={onBtnEnter}
                onMouseLeave={onBtnLeave}
                onClick={(e) => { onBtnClick(e); navigate('/batch-filing'); }}
                className="inline-flex items-center justify-center gap-2.5 bg-white/10 hover:bg-white/15 backdrop-blur-md text-white px-7 py-3 rounded-xl text-sm font-semibold border border-white/15 transition-colors"
              >
                <span className="material-symbols-outlined text-[20px] text-white/70">file_download</span>
                <span>View batch filing</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── Active Consignment Pipeline ─ below hero, constrained ── */}
      <div ref={dossierWrapRef} className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-12 min-h-screen flex flex-col">
      <section
        ref={tableRef}
        style={{ background: `linear-gradient(145deg, ${NAVY}0A 0%, ${NAVY}05 100%)`, border: `1.5px solid ${NAVY}20` }}
        className="rounded-2xl shadow-lg overflow-hidden flex-1 flex flex-col"
      >
        <div
          ref={tableHeadRef}
          className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
          style={{ borderBottom: `1px solid ${NAVY}18` }}
        >
          <div className="flex items-center gap-3">
            <div
              className="flex items-center justify-center w-9 h-9 rounded-xl"
              style={{ background: `${NAVY}12`, border: `1px solid ${NAVY}25` }}
            >
              <span className="material-symbols-outlined text-[20px]" style={{ color: NAVY }}>route</span>
            </div>
            <div>
              <h2 className="text-base font-semibold text-on-surface">Dossiers</h2>
              <p className="text-xs text-outline">Review document extraction status and discrepancies.</p>
            </div>
          </div>
          <button
            onMouseEnter={onBtnEnter}
            onMouseLeave={onBtnLeave}
            onClick={(e) => { onBtnClick(e); fetchDossiers(); }}
            style={{ backgroundColor: NAVY }}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-white text-xs font-semibold hover:shadow-lg transition-shadow"
          >
            <span className="material-symbols-outlined text-[15px]">sync</span>
            <span>Refresh</span>
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="p-6 space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 rounded-lg bg-surface-container-lowest animate-pulse"></div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && dossiers.length === 0 && (
          <div className="p-10 text-center flex-1 flex flex-col items-center justify-center min-h-[400px]">
            <div ref={emptyStateRef}>
              <span className="material-symbols-outlined text-[44px] text-outline">inbox</span>
              <p className="text-sm font-semibold text-on-surface mt-3">No dossiers yet</p>
              <p className="text-xs text-on-surface-variant mt-1 max-w-md mx-auto">
                Add documents to compare the CUSDEC fields they contain.
              </p>
              <button onClick={() => navigate('/dossiers')}
                style={{ backgroundColor: NAVY }}
                className="mt-4 inline-flex items-center gap-2 text-white px-5 py-2.5 rounded-lg text-xs font-semibold shadow-sm hover:opacity-90 transition-all">
                <span className="material-symbols-outlined text-[16px]">add</span>
                <span>Add a dossier</span>
              </button>
            </div>
          </div>
        )}

        {/* Table */}
        {!loading && dossiers.length > 0 && (
          <>
            <div className="w-full overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-surface-container-low text-outline font-semibold uppercase tracking-wider">
                    <th className="py-3 px-4">Dossier ID</th>
                    <th className="py-3 px-4">Documents</th>
                    <th className="py-3 px-4">Processing status</th>
                    <th className="py-3 px-4">Review status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody
                  ref={rowsRef}
                  className="divide-y"
                  style={{ borderColor: `${NAVY}12` }}
                >
                  {dossiers.map(d => {
                    const sb = statusBadge(d.status);
                    const channel = getChannel(d);
                    const cb = channelBadge(channel);
                    return (
                      <tr
                        key={d.dossier_id}
                        className="transition-colors cursor-default"
                        onMouseEnter={onRowEnter}
                        onMouseLeave={onRowLeave}
                      >
                        {/* Consignment ID */}
                        <td className="py-4 px-5">
                          <div className="flex items-center gap-2">
                            <div
                              className="flex items-center justify-center w-7 h-7 rounded-lg shrink-0"
                              style={{ background: `${NAVY}12`, border: `1px solid ${NAVY}20` }}
                            >
                              <span className="material-symbols-outlined text-[14px]" style={{ color: NAVY }}>inventory</span>
                            </div>
                            <div>
                              <div className="font-bold text-on-surface font-mono text-[12px]">
                                CLX-{d.dossier_id.slice(0, 8).toUpperCase()}
                              </div>
                              <div className="text-[10px] text-outline font-mono">
                                {d.created_at ? new Date(d.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                              </div>
                            </div>
                          </div>
                        </td>

                        {/* Documents */}
                        <td className="py-4 px-5">
                          <div className="space-y-0.5">
                            {d.documents.slice(0, 3).map(doc => (
                              <div key={doc.document_id} className="flex items-center gap-1 text-[11px]">
                                <span className="material-symbols-outlined text-[12px] text-outline">description</span>
                                <span className="text-on-surface-variant truncate max-w-[180px]">{doc.original_name}</span>
                              </div>
                            ))}
                            {d.documents.length > 3 && (
                              <span className="text-[10px] text-outline">+{d.documents.length - 3} more</span>
                            )}
                          </div>
                          <span
                            className="inline-flex items-center gap-1 mt-1.5 px-2 py-0.5 rounded-lg font-mono text-on-surface-variant text-[10px]"
                            style={{ background: `${NAVY}0A`, border: `1px solid ${NAVY}15` }}
                          >
                            <span className="material-symbols-outlined text-[11px]">description</span>
                            {d.document_count} doc{d.document_count !== 1 ? 's' : ''}
                          </span>
                        </td>

                        {/* AI Status */}
                        <td className="py-4 px-5">
                          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-semibold text-[11px] ${sb.bg} ${sb.text}`}>
                            <span className={`h-1.5 w-1.5 rounded-full ${sb.dot}`} />
                            {sb.label}
                          </span>
                        </td>

                        {/* Clearance Channel */}
                        <td className="py-4 px-5">
                          <button
                            onMouseEnter={onBtnEnter}
                            onMouseLeave={onBtnLeave}
                            onClick={(e) => { onBtnClick(e); toggleChannel(d.dossier_id, channel); }}
                            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold cursor-pointer transition-opacity ${cb.bg} ${cb.text}`}
                            title="Change review status"
                          >
                            <span className={`h-1.5 w-1.5 rounded-full ${cb.dot}`} />
                            {cb.label}
                            <span className="material-symbols-outlined text-[11px]">swap_horiz</span>
                          </button>
                        </td>

                        {/* Actions */}
                        <td className="py-4 px-5 text-right">
                          <button
                            onMouseEnter={onBtnEnter}
                            onMouseLeave={onBtnLeave}
                            onClick={(e) => { onBtnClick(e); handleInspect(d.dossier_id); }}
                            style={{ background: `linear-gradient(135deg, #1a3a7a 0%, ${NAVY} 100%)` }}
                            className="inline-flex items-center gap-1 text-white px-3.5 py-1.5 rounded-lg font-semibold text-[11px] shadow-sm hover:shadow-lg transition-shadow"
                          >
                            <span>Inspect</span>
                            <span className="material-symbols-outlined text-[14px]">chevron_right</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div
              className="p-3 flex flex-col sm:flex-row items-center justify-between text-xs text-outline"
              style={{ borderTop: `1px solid ${NAVY}15`, background: `${NAVY}05` }}
            >
              <span>Showing {dossiers.length} dossier{dossiers.length !== 1 ? 's' : ''}</span>
              <div className="flex items-center gap-1.5 text-emerald-500">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>Review workspace</span>
              </div>
            </div>
          </>
        )}
      </section>
      </div>

      {/* Shimmer keyframe */}
      <style>{`
        @keyframes shimmerLine {
          0%   { transform: translateX(-100%); opacity: 0; }
          30%  { opacity: 1; }
          70%  { opacity: 1; }
          100% { transform: translateX(100%); opacity: 0; }
        }
      `}</style>
    </div>
  );
}
