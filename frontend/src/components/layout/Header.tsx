import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const primaryNavItems = [
  { path: '/', label: 'Overview' },
  { path: '/dossiers', label: 'Dossiers' },
  { path: '/review-workspace', label: 'Review Workspace' },
  { path: '/discrepancies', label: 'Discrepancies' },
  { path: '/knowledge-graph', label: 'Knowledge Graph' },
  { path: '/batch-filing', label: 'Batch Filing' },
  { path: '/asycuda-gateway', label: 'ASYCUDA Gateway' },
  { path: '/audit-trail', label: 'Audit Trail' },
  { path: '/tariff-directory', label: 'Tariff Directory' },
];

export function Header() {
  const location = useLocation();
  const currentPath = location.pathname;
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-50 bg-surface-container-lowest/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.03)] border-b border-outline-variant/30">
        <div className="h-20 w-full px-4 sm:px-8 flex items-center justify-between gap-4">
          {/* Left Section: Menu & Logo */}
          <div className="flex items-center gap-3 shrink-0">
            <button 
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 -ml-2 text-on-surface-variant hover:text-on-surface rounded-lg hover:bg-surface-container-low transition-colors"
            >
              <span className="material-symbols-outlined text-[24px]">menu</span>
            </button>

            <Link to="/" className="flex items-center gap-1.5 group">
              <div className="w-8 h-8 rounded-lg bg-primary-container flex items-center justify-center text-white shadow-sm transition-transform group-hover:scale-105">
                <span className="material-symbols-outlined text-[20px]">token</span>
              </div>
              <span className="text-lg tracking-tight font-semibold text-on-surface">
                Clearance<span className="text-primary-container">X</span>
              </span>
              <span className="text-[11px] text-secondary bg-secondary-container/20 px-1.5 py-0.5 rounded font-semibold ml-1 hidden sm:inline-block">
                LK-ASYCUDA
              </span>
            </Link>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center gap-2 shrink-0">
            <div className="relative hidden xl:block">
              <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-outline text-[18px]">search</span>
              <input
                type="text"
                placeholder="Search manifests, HS codes..."
                className="w-60 bg-surface-container-low pl-9 pr-8 py-1.5 rounded-lg text-xs text-on-surface placeholder:text-outline focus:outline-none focus:bg-surface-container-lowest focus:shadow-[0_0_0_2px_rgba(79,70,229,0.15)] transition-all"
              />
              <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-mono text-outline px-1 rounded bg-surface-container border border-outline-variant/30">⌘K</span>
            </div>





            {/* Profile & Dropdown */}
            <div className="relative ml-1">
              <button 
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="flex items-center focus:outline-none"
              >
                <div className="w-8 h-8 rounded-full bg-primary-container/10 border border-primary-container/20 flex items-center justify-center text-xs font-bold text-primary shadow-sm hover:scale-105 transition-transform">
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
                      <div className="text-on-surface font-semibold">Authorized Broker</div>
                      <div className="text-xs text-on-surface-variant mt-0.5 font-mono">ID: LK-CMB-ASY-0091</div>
                    </div>
                    <Link to="/settings" onClick={() => setIsDropdownOpen(false)} className="flex items-center gap-2 px-3 py-2 text-on-surface hover:bg-surface-container-low transition-colors">
                      <span className="material-symbols-outlined text-[18px] text-on-surface-variant">settings</span>
                      Settings
                    </Link>
                    <Link to="/auth/signin" onClick={() => setIsDropdownOpen(false)} className="flex items-center gap-2 px-3 py-2 text-on-surface hover:bg-surface-container-low transition-colors">
                      <span className="material-symbols-outlined text-[18px] text-on-surface-variant">login</span>
                      Sign In
                    </Link>
                    <Link to="/auth/signup" onClick={() => setIsDropdownOpen(false)} className="flex items-center gap-2 px-3 py-2 text-on-surface hover:bg-surface-container-low transition-colors">
                      <span className="material-symbols-outlined text-[18px] text-on-surface-variant">person_add</span>
                      Onboard CHB
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
          <div className="px-3 pb-2 text-[10px] font-bold text-outline uppercase tracking-wider">
            Main Navigation
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
               HSM Enclave Protected
             </div>
             <p className="text-[10px] text-on-surface-variant">Connected to Sri Lanka Customs API Gateway.</p>
           </div>
        </div>
      </div>
    </>
  );
}
