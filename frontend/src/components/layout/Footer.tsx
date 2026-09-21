
export function Footer() {
  return (
    <footer className="w-full bg-surface-container-lowest py-6 border-t border-outline-variant/30 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-center sm:text-left text-xs text-on-surface-variant">
        <div>© 2025 ClearanceX Ltd. • ASYCUDA Customs Intelligence Gateway • Sri Lanka</div>
        <div className="flex items-center gap-4 font-medium text-outline">
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-secondary"></span> Colombo Port Customs Core V3.14
          </span>
          <span>•</span>
          <span className="text-secondary font-medium">SLC-WCO Compliant</span>
        </div>
      </div>
    </footer>
  );
}
