import { AlertTriangle, X, RefreshCw } from 'lucide-react';

interface DisconnectedBannerProps {
  connectorUrl: string;
  onRetry: () => void;
  onDismiss: () => void;
  isRetrying: boolean;
}

export default function DisconnectedBanner({
  connectorUrl,
  onRetry,
  onDismiss,
  isRetrying,
}: DisconnectedBannerProps) {
  return (
    <div className="bg-amber-50 border-b border-amber-200">
      <div className="px-6 py-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-amber-900">Connector Disconnected</h3>
              <button
                onClick={onDismiss}
                className="p-1 hover:bg-amber-100 rounded transition-colors"
              >
                <X className="w-4 h-4 text-amber-700" />
              </button>
            </div>
            <p className="text-sm text-amber-800 mb-3">
              Unable to connect to the data connector. The app is running in demo mode with mock data.
            </p>
            <div className="bg-white border border-amber-200 rounded-lg p-3 mb-3">
              <p className="text-xs font-semibold text-amber-900 mb-2">Troubleshooting Steps:</p>
              <ol className="text-xs text-amber-800 space-y-1 list-decimal list-inside">
                <li>Ensure the connector is running on <code className="bg-amber-100 px-1 py-0.5 rounded text-amber-900">{connectorUrl}</code></li>
                <li>Check if the connector port is accessible and not blocked by firewall</li>
                <li>Verify the connector URL in Settings matches your setup</li>
                <li>Try restarting the connector service</li>
              </ol>
            </div>
            <button
              onClick={onRetry}
              disabled={isRetrying}
              className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              <RefreshCw className={`w-4 h-4 ${isRetrying ? 'animate-spin' : ''}`} />
              {isRetrying ? 'Retrying...' : 'Retry Connection'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
