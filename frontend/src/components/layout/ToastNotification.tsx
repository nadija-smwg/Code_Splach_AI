
interface Toast {
  title: string;
  message: string;
  type?: 'error' | 'info' | 'success';
}

interface ToastNotificationProps {
  toast: Toast | null;
  onClose: () => void;
}

export function ToastNotification({ toast, onClose }: ToastNotificationProps) {
  if (!toast) return null;
  return (
    <div className="fixed bottom-6 right-6 z-50 max-w-md bg-surface-container-lowest text-on-surface p-4 rounded-xl shadow-2xl border-l-4 border-secondary flex items-start gap-3 transition-all animate-bounce-in">
      <span className="material-symbols-outlined text-secondary text-[22px] shrink-0 mt-0.5">
        {toast.type === 'error' ? 'error' : toast.type === 'info' ? 'info' : 'task_alt'}
      </span>
      <div className="space-y-0.5">
        <div className="font-semibold text-sm">{toast.title}</div>
        <div className="text-xs text-on-surface-variant leading-relaxed">{toast.message}</div>
      </div>
      <button onClick={onClose} className="ml-auto text-outline hover:text-on-surface p-1">
        <span className="material-symbols-outlined text-[16px]">close</span>
      </button>
    </div>
  );
}
