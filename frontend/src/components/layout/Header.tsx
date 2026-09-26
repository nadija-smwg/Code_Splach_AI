import { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { prefersReducedMotion } from '../../hooks/useScrollAnimations';

gsap.registerPlugin(ScrollTrigger);

const primaryNavItems = [
  { path: '/',                  label: 'Overview',          icon: 'home' },
  { path: '/dossiers',          label: 'Dossiers',          icon: 'folder_open' },
  { path: '/review-workspace',  label: 'Review Workspace',  icon: 'rate_review' },
  { path: '/discrepancies',     label: 'Discrepancies',     icon: 'difference' },
  { path: '/knowledge-graph',   label: 'Knowledge Graph',   icon: 'hub' },
  { path: '/batch-filing',      label: 'Batch Filing',      icon: 'stacks' },
  { path: '/asycuda-gateway',   label: 'CUSDEC Export',     icon: 'upload_file' },
  { path: '/audit-trail',       label: 'Audit Trail',       icon: 'history' },
  { path: '/tariff-directory',  label: 'Tariff Directory',  icon: 'menu_book' },
];

export function Header() {
  const location = useLocation();
  const currentPath = location.pathname;

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);

  const headerRef = useRef<HTMLElement>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);

  const isOverview = currentPath === '/';

  // ── Scroll listener: header state + progress bar ─────────────────────
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const threshold = isOverview ? window.innerHeight - 100 : 20;
      setIsScrolled(scrollY > threshold);

      // Progress bar: 0→1 over the full document height
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = docHeight > 0 ? Math.min(scrollY / docHeight, 1) : 0;
      setScrollProgress(progress);

      // GSAP smooth header height compaction
      if (!prefersReducedMotion && headerRef.current) {
        const inner = headerRef.current.querySelector('.header-inner') as HTMLElement | null;
        if (inner) {
          const compact = scrollY > threshold;
          gsap.to(inner, {
            height: compact ? 56 : 80,
            duration: 0.35,
            ease: 'power2.out',
            overwrite: true,
          });
        }
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [isOverview]);

  const useTransparentStyle = isOverview && !isScrolled;

  return (
    <>
      <header
        ref={headerRef}
        className={`fixed top-0 left-0 right-0 z-50 transition-colors duration-300 ${
          useTransparentStyle
            ? 'bg-transparent border-b border-white/0 shadow-none'
            : 'bg-surface-container-lowest/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.03)] border-b border-outline-variant/30'
        }`}
      >
        {/* ── Scroll Progress Bar ─────────────────────────────────────── */}
        <div
          ref={progressBarRef}
          className="absolute top-0 left-0 right-0 h-[2px] z-10 pointer-events-none"
          style={{ opacity: scrollProgress > 0.01 ? 1 : 0, transition: 'opacity 0.3s' }}
        >
          <div
            className="h-full"
            style={{
              width: `${scrollProgress * 100}%`,
              background: useTransparentStyle
                ? 'linear-gradient(90deg, rgba(91,143,212,0.5), rgba(91,143,212,0.9))'
                : 'linear-gradient(90deg, var(--color-primary-container), var(--color-primary))',
              transition: 'width 0.08s linear',
            }}
          />
        </div>

        <div className="header-inner h-20 w-full px-4 sm:px-8 flex items-center justify-between gap-4">
          {/* Left Section: Menu & Logo */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className={`p-2 -ml-2 rounded-lg transition-colors ${
                isOverview
                  ? 'text-white/80 hover:text-white hover:bg-white/10'
                  : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low'
              }`}
            >
              <span className="material-symbols-outlined text-[24px]">menu</span>
            </button>

            <Link to="/" className="flex items-center gap-1.5 group">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white shadow-sm transition-transform group-hover:scale-105 ${
                useTransparentStyle ? 'bg-white/20 backdrop-blur-md border border-white/30' : 'bg-primary-container'
              }`}>
                <span className="material-symbols-outlined text-[20px]">token</span>
              </div>
              <span className={`text-lg tracking-tight font-semibold ${
                useTransparentStyle ? 'text-white' : 'text-on-surface'
              }`}>
                Clearance<span className={useTransparentStyle ? 'text-[#5b8fd4]' : 'text-primary-container'}>X</span>
              </span>
              <span className={`text-[11px] px-1.5 py-0.5 rounded font-semibold ml-1 hidden sm:inline-block ${
                isOverview
                  ? 'text-emerald-300 bg-emerald-400/10 border border-emerald-400/20'
                  : 'text-secondary bg-secondary-container/20'
              }`}>
                Demo
              </span>
            </Link>
          </div>

          {/* Account menu */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Profile & Dropdown */}
            <div className="relative ml-1">
              <button
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="flex items-center focus:outline-none"
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shadow-sm hover:scale-105 transition-transform ${
                  isOverview
                    ? 'bg-white/15 backdrop-blur-md border border-white/25 text-white'
                    : 'bg-primary-container/10 border border-primary-container/20 text-primary'
                }`}>
                  SL
                </div>
              </button>

              {/* Dropdown Menu */}
              {isDropdownOpen && (
                <>
                  {/* Invisible overlay to catch clicks outside */}
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setIsDropdownOpen(false)}
                  ></div>

                  <div className="absolute right-0 mt-2 w-48 bg-surface-container-lowest rounded-xl shadow-lg border border-outline-variant/30 py-1.5 z-50 overflow-hidden text-sm font-medium">
                    <div className="px-3 py-2 border-b border-outline-variant/20 mb-1">
                      <div className="text-on-surface font-semibold">Demo workspace</div>
                      <div className="text-xs text-on-surface-variant mt-0.5">Document review</div>
                    </div>
                    <Link to="/settings" onClick={() => setIsDropdownOpen(false)} className="flex items-center gap-2 px-3 py-2 text-on-surface hover:bg-surface-container-low transition-colors">
                      <span className="material-symbols-outlined text-[18px] text-on-surface-variant">settings</span>
                      Settings
                    </Link>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar Drawer Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-[60] bg-black/40 backdrop-blur-sm transition-opacity"
          onClick={() => setIsSidebarOpen(false)}
        ></div>
      )}

      {/* Sidebar Drawer */}
      <div
        className={`fixed top-0 left-0 bottom-0 w-72 z-[70] shadow-2xl transform transition-transform duration-300 ease-in-out flex flex-col ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ background: 'linear-gradient(180deg, #0d1b3e 0%, #0f2044 18%, #f6f3f5 18%)' }}
      >
        {/* Sidebar Header — dark panel */}
        <div className="px-5 pt-6 pb-5 shrink-0 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-white/15 backdrop-blur-md border border-white/20 flex items-center justify-center shadow-lg">
              <span className="material-symbols-outlined text-[20px] text-white">token</span>
            </div>
            <div>
              <span className="text-lg tracking-tight font-bold text-white">
                Clearance<span style={{ color: '#5b8fd4' }}>X</span>
              </span>
              <div className="text-[10px] text-white/50 font-medium -mt-0.5">Document Review Platform</div>
            </div>
          </div>
          <button
            onClick={() => setIsSidebarOpen(false)}
            className="p-1.5 text-white/50 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
          >
            <span className="material-symbols-outlined text-[22px]">close</span>
          </button>
        </div>

        {/* Nav Items */}
        <div className="flex-1 overflow-y-auto px-3 pt-4 pb-3 flex flex-col gap-0.5">
          <div className="px-3 pb-2.5 text-[10px] font-bold text-outline uppercase tracking-widest">
            Navigation
          </div>
          {primaryNavItems.map((item) => {
            const isActive = (item.path === '/' && currentPath === '/') ||
              (item.path !== '/' && currentPath.startsWith(item.path));

            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsSidebarOpen(false)}
                className={`relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-150 ${
                  isActive
                    ? 'bg-primary/10 text-primary font-semibold'
                    : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-medium'
                }`}
              >
                {/* Active accent bar */}
                {isActive && (
                  <span
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-full"
                    style={{ background: 'var(--color-primary)' }}
                  />
                )}
                <span
                  className={`material-symbols-outlined text-[19px] shrink-0 ${
                    isActive ? 'text-primary' : 'text-outline'
                  }`}
                >
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Footer workspace card */}
        <div className="px-3 pb-4 shrink-0">
          <div className="rounded-xl border border-outline-variant/30 bg-surface-container-low overflow-hidden">
            <div className="px-4 py-3 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-secondary/10 border border-secondary/20 flex items-center justify-center shrink-0">
                <span className="material-symbols-outlined text-secondary text-[17px]">verified_user</span>
              </div>
              <div className="min-w-0">
                <div className="text-xs font-bold text-on-surface">Demo workspace</div>
                <div className="text-[10px] text-on-surface-variant truncate">Document review mode</div>
              </div>
            </div>
            <div className="px-4 pb-3">
              <div className="flex items-center gap-1.5">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span className="text-[10px] text-emerald-600 font-medium">System operational</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}



