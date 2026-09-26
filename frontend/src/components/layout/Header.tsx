import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';

const primaryNavItems = [
  { path: '/', label: 'Overview' },
  { path: '/dossiers', label: 'Dossiers' },
  { path: '/review-workspace', label: 'Review Workspace' },
  { path: '/discrepancies', label: 'Discrepancies' },
  { path: '/knowledge-graph', label: 'Knowledge Graph' },
  { path: '/batch-filing', label: 'Batch Filing' },
  { path: '/asycuda-gateway', label: 'CUSDEC Export' },
  { path: '/audit-trail', label: 'Audit Trail' },
  { path: '/tariff-directory', label: 'Tariff Directory' },
];

export function Header() {
  const location = useLocation();
  const currentPath = location.pathname;
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const isOverview = currentPath === '/';
  const useTransparentStyle = isOverview && !isScrolled;

  return (
    <>
      <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        useTransparentStyle
          ? 'bg-transparent border-b border-white/0 shadow-none'
          : 'bg-surface-container-lowest/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.03)] border-b border-outline-variant/30'
      }`}>
        <div className="h-20 w-full px-4 sm:px-8 flex items-center justify-between gap-4">
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
        className={`fixed top-0 left-0 bottom-0 w-72 bg-surface-container-lowest z-[70] shadow-2xl transform transition-transform duration-300 ease-in-out border-r border-outline-variant/30 flex flex-col ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-20 px-4 flex items-center justify-between border-b border-outline-variant/30 shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary-container flex items-center justify-center text-white shadow-sm">
              <span className="material-symbols-outlined text-[20px]">token</span>
            </div>
            <span className="text-lg tracking-tight font-semibold text-on-surface">
              Clearance<span className="text-primary-container">X</span>
            </span>
          </div>
          <button 
            onClick={() => setIsSidebarOpen(false)}
            className="p-1.5 text-on-surface-variant hover:text-on-surface rounded-lg hover:bg-surface-container-low transition-colors"
          >
            <span className="material-symbols-outlined text-[24px]">close</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-4 px-3 flex flex-col gap-1">
          <div className="px-3 pb-2 text-xs font-semibold text-outline">
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
                className={`flex items-center px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-primary-fixed text-primary font-semibold shadow-sm'
                    : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface font-medium'
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
        
        <div className="p-4 border-t border-outline-variant/30 shrink-0">
           <div className="bg-surface-container-low rounded-xl p-3 flex flex-col gap-2">
             <div className="flex items-center gap-2 text-xs font-semibold text-on-surface">
               <span className="material-symbols-outlined text-secondary text-[16px]">verified_user</span>
               Demo workspace
             </div>
             <p className="text-[10px] text-on-surface-variant">Review extracted document data before preparing a declaration.</p>
           </div>
        </div>
      </div>
    </>
  );
}
