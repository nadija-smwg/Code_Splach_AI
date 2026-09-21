import { Link } from 'react-router-dom';
import { useLocation } from 'react-router-dom';

interface HeaderProps {
  onTriggerToast: (toast: { title: string; message: string }) => void;
}

const navItems = [
  { path: '/', label: 'Overview' },
  { path: '/dossiers', label: 'Dossiers' },
  { path: '/review-workspace', label: 'Review Workspace' },
  { path: '/discrepancies', label: 'Discrepancies' },
  { path: '/knowledge-graph', label: 'Knowledge Graph' },
  { path: '/batch-filing', label: 'Batch Filing' },
  { path: '/asycuda-gateway', label: 'ASYCUDA Gateway' },
  { path: '/audit-trail', label: 'Audit Trail' },
  { path: '/tariff-directory', label: 'Tariff Directory' },
  { path: '/settings', label: 'Settings' },
  { path: '/auth/signin', label: 'Sign In' },
  { path: '/auth/signup', label: 'Onboard CHB' },
];

export function Header({ onTriggerToast }: HeaderProps) {
  const location = useLocation();
  const currentPath = location.pathname;

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-surface-container-lowest/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.03)] border-b border-outline-variant/30">
      <div className="h-20 w-full px-4 sm:px-8 flex items-center justify-between gap-4">
        {/* Logo */}
        <div className="flex items-center gap-4 shrink-0">
          <Link to="/" className="flex items-center gap-1.5 group">
            <div className="w-8 h-8 rounded-lg bg-primary-container flex items-center justify-center text-white shadow-sm transition-transform group-hover:scale-105">
              <span className="material-symbols-outlined text-[20px]">token</span>
            </div>
            <span className="text-lg tracking-tight font-semibold text-on-surface">
              Clearance<span className="text-primary-container">X</span>
            </span>
            <span className="text-[11px] text-secondary bg-secondary-container/20 px-1.5 py-0.5 rounded font-semibold ml-1">
              LK-ASYCUDA
            </span>
          </Link>
        </div>

        {/* Nav Links */}
        <nav className="hidden xl:flex items-center gap-1 overflow-x-auto py-1 mx-2 text-xs font-medium">
          {navItems.map((item) => {
            const isActive = (item.path === '/' && currentPath === '/') ||
              (item.path !== '/' && currentPath.startsWith(item.path));
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors ${
                  isActive
                    ? 'bg-primary-fixed text-primary font-semibold shadow-sm'
                    : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Quick Actions */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="relative hidden lg:block">
            <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-outline text-[18px]">search</span>
            <input
              type="text"
              placeholder="Search manifests, HS codes..."
              className="w-56 xl:w-60 bg-surface-container-low pl-9 pr-8 py-1.5 rounded-lg text-xs text-on-surface placeholder:text-outline focus:outline-none focus:bg-surface-container-lowest focus:shadow-[0_0_0_2px_rgba(79,70,229,0.15)] transition-all"
            />
            <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-mono text-outline px-1 rounded bg-surface-container border border-outline-variant/30">⌘K</span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 bg-surface-container-low px-2.5 py-1.5 rounded-full text-xs font-medium">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-secondary"></span>
            </span>
            <span className="text-on-surface">Sync Active</span>
            <span className="text-outline">•</span>
            <span className="text-secondary font-semibold font-mono">2ms</span>
          </div>

          <button
            aria-label="Notifications"
            onClick={() => onTriggerToast({ title: 'ASYCUDA Synchronized', message: 'All Colombo port terminals responding with 100% telemetry pass.' })}
            className="relative p-2 text-on-surface-variant hover:text-on-surface rounded-lg hover:bg-surface-container-low transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">notifications</span>
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-primary-container"></span>
          </button>

          <Link to="/settings" className="flex items-center pl-1">
            <div className="w-8 h-8 rounded-full bg-primary-container/10 border border-primary-container/20 flex items-center justify-center text-xs font-bold text-primary shadow-sm hover:scale-105 transition-transform">
              SL
            </div>
          </Link>
        </div>
      </div>
    </header>
  );
}
