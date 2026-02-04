import { useState, useEffect } from 'react';
import { AlertTriangle, Info, CheckCircle, AlertCircle, Trash2, ChevronDown, ChevronRight, Copy, PlayCircle, Loader2, Server, Zap } from 'lucide-react';
import { diagnostics, DiagnosticEvent } from '../services/diagnostics';
import { connectorApi } from '../services/connectorApi';

interface TestResult {
  endpoint: string;
  method: string;
  status: number | null;
  statusText: string;
  response: string;
  timestamp: string;
  success: boolean;
}

interface DiagnosticsPanelProps {
  connectorStatus: 'connected' | 'disconnected' | 'checking';
  connectorVersion: string;
  onRetryConnection: () => Promise<void>;
}

export default function DiagnosticsPanel({ connectorStatus, connectorVersion, onRetryConnection }: DiagnosticsPanelProps) {
  const [events, setEvents] = useState<DiagnosticEvent[]>([]);
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'error' | 'warning' | 'info' | 'success'>('all');
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [runningTest, setRunningTest] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>('Never');
  const [activeTab, setActiveTab] = useState<'tests' | 'logs'>('tests');

  useEffect(() => {
    setEvents(diagnostics.getEvents());
    const unsubscribe = diagnostics.subscribe(setEvents);
    return unsubscribe;
  }, []);

  useEffect(() => {
    setLastChecked(new Date().toLocaleTimeString());
  }, [connectorStatus]);

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

  const testHealthEndpoint = async () => {
    setRunningTest('health');
    diagnostics.info('Test', 'Testing /health endpoint...');

    try {
      const response = await fetch(`${connectorApi.getConnectorUrl()}/health`);
      const text = await response.text();
      let parsedResponse = text;

      try {
        parsedResponse = JSON.stringify(JSON.parse(text), null, 2);
      } catch {
        // Keep as text
      }

      const result: TestResult = {
        endpoint: '/health',
        method: 'GET',
        status: response.status,
        statusText: response.statusText,
        response: parsedResponse,
        timestamp: new Date().toISOString(),
        success: response.ok,
      };

      setTestResults(prev => [result, ...prev]);

      if (response.ok) {
        diagnostics.success('Test', `✓ /health returned ${response.status}`);
      } else {
        diagnostics.error('Test', `✗ /health returned ${response.status}`, parsedResponse);
      }
    } catch (error) {
      const result: TestResult = {
        endpoint: '/health',
        method: 'GET',
        status: null,
        statusText: 'Network Error',
        response: error instanceof Error ? error.message : String(error),
        timestamp: new Date().toISOString(),
        success: false,
      };
      setTestResults(prev => [result, ...prev]);
      diagnostics.error('Test', '✗ /health failed', result.response);
    } finally {
      setRunningTest(null);
    }
  };

  const testDatasetsEndpoint = async () => {
    setRunningTest('datasets');
    diagnostics.info('Test', 'Testing /datasets endpoint...');

    try {
      const response = await fetch(`${connectorApi.getConnectorUrl()}/datasets`);
      const text = await response.text();
      let parsedResponse = text;

      try {
        parsedResponse = JSON.stringify(JSON.parse(text), null, 2);
      } catch {
        // Keep as text
      }

      const result: TestResult = {
        endpoint: '/datasets',
        method: 'GET',
        status: response.status,
        statusText: response.statusText,
        response: parsedResponse,
        timestamp: new Date().toISOString(),
        success: response.ok,
      };

      setTestResults(prev => [result, ...prev]);

      if (response.ok) {
        diagnostics.success('Test', `✓ /datasets returned ${response.status}`);
      } else {
        diagnostics.error('Test', `✗ /datasets returned ${response.status}`, parsedResponse);
      }
    } catch (error) {
      const result: TestResult = {
        endpoint: '/datasets',
        method: 'GET',
        status: null,
        statusText: 'Network Error',
        response: error instanceof Error ? error.message : String(error),
        timestamp: new Date().toISOString(),
        success: false,
      };
      setTestResults(prev => [result, ...prev]);
      diagnostics.error('Test', '✗ /datasets failed', result.response);
    } finally {
      setRunningTest(null);
    }
  };

  const testRegisterEndpoint = async () => {
    setRunningTest('register');
    diagnostics.info('Test', 'Testing /datasets/register with dummy data...');

    try {
      const dummyPayload = {
        name: 'test-dataset',
        sourceType: 'local_file',
        filePath: '/nonexistent/test.xlsx',
      };

      const response = await fetch(`${connectorApi.getConnectorUrl()}/datasets/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dummyPayload),
      });

      const text = await response.text();
      let parsedResponse = text;

      try {
        parsedResponse = JSON.stringify(JSON.parse(text), null, 2);
      } catch {
        // Keep as text
      }

      const result: TestResult = {
        endpoint: '/datasets/register',
        method: 'POST',
        status: response.status,
        statusText: response.statusText,
        response: parsedResponse,
        timestamp: new Date().toISOString(),
        success: response.status === 400 || response.status === 404,
      };

      setTestResults(prev => [result, ...prev]);

      if (response.status === 400 || response.status === 404) {
        diagnostics.success('Test', `✓ /datasets/register correctly returned ${response.status} (expected error)`);
      } else if (response.ok) {
        diagnostics.warning('Test', `⚠ /datasets/register unexpectedly succeeded with ${response.status}`, parsedResponse);
      } else {
        diagnostics.error('Test', `✗ /datasets/register returned ${response.status}`, parsedResponse);
      }
    } catch (error) {
      const result: TestResult = {
        endpoint: '/datasets/register',
        method: 'POST',
        status: null,
        statusText: 'Network Error',
        response: error instanceof Error ? error.message : String(error),
        timestamp: new Date().toISOString(),
        success: false,
      };
      setTestResults(prev => [result, ...prev]);
      diagnostics.error('Test', '✗ /datasets/register failed', result.response);
    } finally {
      setRunningTest(null);
    }
  };

  const runAllTests = async () => {
    await testHealthEndpoint();
    await testDatasetsEndpoint();
    await testRegisterEndpoint();
  };

  const copyDiagnostics = () => {
    const appVersion = '0.0.0';
    const connectorUrl = connectorApi.getConnectorUrl();
    const last20Events = events.slice(0, 20);

    const diagnosticsText = `
=== CloakSheets Diagnostics Report ===
Generated: ${new Date().toLocaleString()}

App Version: ${appVersion}
Connector URL: ${connectorUrl}
Connector Status: ${connectorStatus}
Connector Version: ${connectorVersion || 'Unknown'}
Last Checked: ${lastChecked}

=== Test Results (${testResults.length} tests) ===
${testResults.length === 0 ? 'No tests run yet' : testResults.map(test => `
${test.method} ${test.endpoint}
Status: ${test.status || 'N/A'} ${test.statusText}
Success: ${test.success ? 'Yes' : 'No'}
Timestamp: ${new Date(test.timestamp).toLocaleString()}
Response:
${test.response}
---`).join('\n')}

=== Last 20 Log Events ===
${last20Events.map(event => `
[${formatTimestamp(event.timestamp)}] ${event.type.toUpperCase()} - ${event.category}
${event.message}
${event.details ? `Details: ${event.details}` : ''}
---`).join('\n')}

=== End of Report ===
`.trim();

    navigator.clipboard.writeText(diagnosticsText);
    diagnostics.success('Diagnostics', 'Diagnostics report copied to clipboard');
  };

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="p-6 border-b border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Diagnostics</h2>
            <p className="text-sm text-slate-600 mt-1">
              Test connector endpoints and view system logs
            </p>
          </div>
          <button
            onClick={copyDiagnostics}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-lg transition-colors"
          >
            <Copy className="w-4 h-4" />
            Copy Diagnostics
          </button>
        </div>

        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setActiveTab('tests')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'tests'
                ? 'bg-emerald-500 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Connector Tests
            </div>
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'logs'
                ? 'bg-emerald-500 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4" />
              System Logs
              {(errorCount > 0 || warningCount > 0) && (
                <span className="px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">
                  {errorCount + warningCount}
                </span>
              )}
            </div>
          </button>
        </div>
      </div>

      {activeTab === 'tests' && (
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">
            <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
              <div className="flex items-center gap-2 mb-3">
                <Server className="w-5 h-5 text-slate-600" />
                <h3 className="font-semibold text-slate-900">Connector Information</h3>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-600">Base URL:</span>
                  <span className="font-mono text-slate-900">{connectorApi.getConnectorUrl()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Status:</span>
                  <span className={`font-medium ${
                    connectorStatus === 'connected' ? 'text-emerald-600' :
                    connectorStatus === 'checking' ? 'text-blue-600' : 'text-red-600'
                  }`}>
                    {connectorStatus === 'connected' ? '🟢 Connected' :
                     connectorStatus === 'checking' ? '🔵 Checking...' : '🔴 Disconnected'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Version:</span>
                  <span className="text-slate-900">{connectorVersion || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Last Checked:</span>
                  <span className="text-slate-900">{lastChecked}</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-slate-900 mb-3">Quick Tests</h3>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={testHealthEndpoint}
                  disabled={runningTest !== null}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-white border-2 border-slate-200 text-slate-700 rounded-lg hover:border-emerald-500 hover:bg-emerald-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {runningTest === 'health' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <PlayCircle className="w-4 h-4" />
                  )}
                  Test /health
                </button>
                <button
                  onClick={testDatasetsEndpoint}
                  disabled={runningTest !== null}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-white border-2 border-slate-200 text-slate-700 rounded-lg hover:border-emerald-500 hover:bg-emerald-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {runningTest === 'datasets' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <PlayCircle className="w-4 h-4" />
                  )}
                  Test /datasets
                </button>
                <button
                  onClick={testRegisterEndpoint}
                  disabled={runningTest !== null}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-white border-2 border-slate-200 text-slate-700 rounded-lg hover:border-emerald-500 hover:bg-emerald-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {runningTest === 'register' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <PlayCircle className="w-4 h-4" />
                  )}
                  Test /register
                </button>
                <button
                  onClick={onRetryConnection}
                  disabled={runningTest !== null}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-white border-2 border-slate-200 text-slate-700 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {runningTest !== null ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <PlayCircle className="w-4 h-4" />
                  )}
                  Retry Connection
                </button>
              </div>
              <button
                onClick={runAllTests}
                disabled={runningTest !== null}
                className="w-full mt-3 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-medium rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {runningTest !== null ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <PlayCircle className="w-4 h-4" />
                )}
                Run All Tests
              </button>
            </div>

            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-slate-900">Test Results</h3>
                {testResults.length > 0 && (
                  <button
                    onClick={() => setTestResults([])}
                    className="text-xs text-slate-600 hover:text-slate-900"
                  >
                    Clear results
                  </button>
                )}
              </div>
              {testResults.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <PlayCircle className="w-12 h-12 text-slate-300 mb-3" />
                  <p className="text-sm text-slate-600">No tests run yet</p>
                  <p className="text-xs text-slate-500 mt-1">Run a test to see results here</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {testResults.map((result, index) => (
                    <div
                      key={index}
                      className={`border rounded-lg overflow-hidden ${
                        result.success
                          ? 'bg-emerald-50 border-emerald-200'
                          : 'bg-red-50 border-red-200'
                      }`}
                    >
                      <div className="p-3">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            {result.success ? (
                              <CheckCircle className="w-4 h-4 text-emerald-600" />
                            ) : (
                              <AlertCircle className="w-4 h-4 text-red-600" />
                            )}
                            <span className="font-medium text-sm">
                              {result.method} {result.endpoint}
                            </span>
                          </div>
                          <span className={`text-xs font-mono px-2 py-1 rounded ${
                            result.success
                              ? 'bg-emerald-100 text-emerald-700'
                              : 'bg-red-100 text-red-700'
                          }`}>
                            {result.status || 'N/A'} {result.statusText}
                          </span>
                        </div>
                        <div className="text-xs text-slate-600 mb-2">
                          {new Date(result.timestamp).toLocaleString()}
                        </div>
                        <details className="text-xs">
                          <summary className="cursor-pointer text-slate-700 hover:text-slate-900">
                            View response
                          </summary>
                          <pre className="mt-2 p-2 bg-white rounded border border-slate-200 overflow-x-auto">
                            {result.response}
                          </pre>
                        </details>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'logs' && (
        <div className="flex-1 overflow-y-auto">
          <div className="p-6 border-b border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-slate-600">
                Last {events.length} events
                {errorCount > 0 && <span className="text-red-600 ml-2">• {errorCount} errors</span>}
                {warningCount > 0 && <span className="text-amber-600 ml-2">• {warningCount} warnings</span>}
              </p>
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

          <div className="p-6">
            {filteredEvents.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
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
      )}
    </div>
  );
}
