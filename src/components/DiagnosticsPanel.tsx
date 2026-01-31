import { useState, useEffect } from 'react';
import { AlertTriangle, Info, CheckCircle, AlertCircle, Trash2, ChevronDown, ChevronRight } from 'lucide-react';
import { diagnostics, DiagnosticEvent } from '../services/diagnostics';

export default function DiagnosticsPanel() {
  const [events, setEvents] = useState<DiagnosticEvent[]>([]);
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'error' | 'warning' | 'info' | 'success'>('all');

  useEffect(() => {
    setEvents(diagnostics.getEvents());
    const unsubscribe = diagnostics.subscribe(setEvents);
    return unsubscribe;
  }, []);

  const filteredEvents = filter === 'all'
    ? events
    : events.filter(e => e.type === filter);

  const getIcon = (type: DiagnosticEvent['type']) => {
    switch (type) {
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-600" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-emerald-600" />;
      default:
        return <Info className="w-4 h-4 text-blue-600" />;
    }
  };

  const getTypeColor = (type: DiagnosticEvent['type']) => {
    switch (type) {
      case 'error':
        return 'bg-red-50 border-red-200 text-red-900';
      case 'warning':
        return 'bg-amber-50 border-amber-200 text-amber-900';
      case 'success':
        return 'bg-emerald-50 border-emerald-200 text-emerald-900';
      default:
        return 'bg-blue-50 border-blue-200 text-blue-900';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const errorCount = events.filter(e => e.type === 'error').length;
  const warningCount = events.filter(e => e.type === 'warning').length;

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="p-6 border-b border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Diagnostics</h2>
            <p className="text-sm text-slate-600 mt-1">
              Last {events.length} events
              {errorCount > 0 && <span className="text-red-600 ml-2">• {errorCount} errors</span>}
              {warningCount > 0 && <span className="text-amber-600 ml-2">• {warningCount} warnings</span>}
            </p>
          </div>
          <button
            onClick={() => {
              if (confirm('Clear all diagnostic events?')) {
                diagnostics.clearEvents();
              }
            }}
            className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Clear
          </button>
        </div>

        <div className="flex gap-2">
          {['all', 'error', 'warning', 'info', 'success'].map((filterType) => (
            <button
              key={filterType}
              onClick={() => setFilter(filterType as typeof filter)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                filter === filterType
                  ? 'bg-emerald-500 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {filterType.charAt(0).toUpperCase() + filterType.slice(1)}
              {filterType !== 'all' && (
                <span className="ml-1">
                  ({events.filter(e => e.type === filterType).length})
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {filteredEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Info className="w-12 h-12 text-slate-300 mb-3" />
            <p className="text-sm text-slate-600">No diagnostic events to show</p>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredEvents.map((event) => (
              <div
                key={event.id}
                className={`border rounded-lg overflow-hidden ${getTypeColor(event.type)}`}
              >
                <button
                  onClick={() => setExpandedEvent(expandedEvent === event.id ? null : event.id)}
                  className="w-full px-4 py-3 flex items-start gap-3 hover:opacity-80 transition-opacity"
                >
                  <div className="flex-shrink-0 mt-0.5">{getIcon(event.type)}</div>
                  <div className="flex-1 text-left">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold uppercase">{event.category}</span>
                      <span className="text-xs opacity-75">{formatTimestamp(event.timestamp)}</span>
                    </div>
                    <p className="text-sm font-medium">{event.message}</p>
                  </div>
                  <div className="flex-shrink-0">
                    {event.details ? (
                      expandedEvent === event.id ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )
                    ) : null}
                  </div>
                </button>
                {expandedEvent === event.id && event.details && (
                  <div className="px-4 pb-3 border-t border-current/10">
                    <pre className="text-xs font-mono mt-2 whitespace-pre-wrap break-words opacity-90">
                      {event.details}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
