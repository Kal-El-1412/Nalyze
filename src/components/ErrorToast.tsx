import { X, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react';
import { useState, useEffect } from 'react';
import { ApiError } from '../services/connectorApi';

interface ErrorToastProps {
  error: ApiError;
  onClose: () => void;
}

export default function ErrorToast({ error, onClose }: ErrorToastProps) {
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 10000);

    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className="fixed bottom-6 right-6 bg-white rounded-xl shadow-2xl border-2 border-red-200 max-w-md z-50 animate-slide-up">
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <AlertCircle className="w-5 h-5 text-red-600" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-2">
              <h3 className="text-sm font-semibold text-red-900">
                {(() => {
                  const url = (error.url || '').toLowerCase();
                  if (url.includes('/datasets/upload')) return 'Dataset Upload Failed';
                  if (url.includes('/datasets/register')) return 'Dataset Registration Failed';
                  if (url.includes('/datasets/ingest')) return 'Dataset Ingest Failed';
                  if (url.includes('/chat')) return 'Chat Request Failed';
                  if (url.includes('/queries/execute')) return 'Query Execution Failed';
                  return 'Connector Error';
                })()}
              </h3>
              <button
                onClick={onClose}
                className="flex-shrink-0 p-0.5 text-red-400 hover:text-red-600 rounded transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex items-center gap-2 text-slate-600">
                <span className="font-medium">{error.method}</span>
                <span className="truncate">{error.url}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded font-mono font-medium">
                  {error.status} {error.statusText}
                </span>
              </div>
              <p className="text-slate-700 mt-2">{error.message}</p>
            </div>
            {error.raw && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center gap-1 mt-2 text-xs text-slate-600 hover:text-slate-900 transition-colors"
              >
                {expanded ? (
                  <ChevronDown className="w-3 h-3" />
                ) : (
                  <ChevronRight className="w-3 h-3" />
                )}
                <span>Raw response</span>
              </button>
            )}
            {expanded && error.raw && (
              <pre className="mt-2 p-2 bg-slate-50 rounded text-xs font-mono overflow-x-auto max-h-32 border border-slate-200">
                {error.raw}
              </pre>
            )}
          </div>
        </div>
      </div>
      <div className="px-4 pb-4">
        <button
          onClick={onClose}
          className="w-full px-3 py-2 bg-red-50 hover:bg-red-100 text-red-700 text-sm font-medium rounded-lg transition-colors"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
