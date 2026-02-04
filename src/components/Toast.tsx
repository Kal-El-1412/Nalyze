import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { useEffect } from 'react';

type ToastVariant = 'success' | 'error' | 'info';

interface ToastProps {
  message: string;
  variant?: ToastVariant;
  onClose: () => void;
  duration?: number;
}

export default function Toast({ message, variant = 'info', onClose, duration = 3000 }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [onClose, duration]);

  const variants = {
    success: {
      icon: CheckCircle,
      bgColor: 'bg-white',
      borderColor: 'border-emerald-200',
      iconColor: 'text-emerald-600',
      textColor: 'text-slate-900',
      closeColor: 'text-slate-400 hover:text-slate-600',
    },
    error: {
      icon: AlertCircle,
      bgColor: 'bg-white',
      borderColor: 'border-red-200',
      iconColor: 'text-red-600',
      textColor: 'text-slate-900',
      closeColor: 'text-slate-400 hover:text-slate-600',
    },
    info: {
      icon: Info,
      bgColor: 'bg-white',
      borderColor: 'border-blue-200',
      iconColor: 'text-blue-600',
      textColor: 'text-slate-900',
      closeColor: 'text-slate-400 hover:text-slate-600',
    },
  };

  const config = variants[variant];
  const Icon = config.icon;

  return (
    <div
      className={`fixed bottom-6 right-6 ${config.bgColor} rounded-xl shadow-lg border ${config.borderColor} max-w-md z-50 animate-slide-up`}
      style={{
        animation: 'slideUp 0.3s ease-out',
      }}
    >
      <div className="p-4 flex items-start gap-3">
        <div className="flex-shrink-0">
          <Icon className={`w-5 h-5 ${config.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-medium ${config.textColor}`}>{message}</p>
        </div>
        <button
          onClick={onClose}
          className={`flex-shrink-0 p-0.5 ${config.closeColor} rounded transition-colors`}
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
