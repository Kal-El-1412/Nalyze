import { useState, useEffect } from 'react';
import {
  X,
  Database,
  Table,
  Hash,
  Type,
  Loader2,
  Search,
  Copy,
  Calendar,
  AlertTriangle,
  Mail,
  Phone,
  User,
} from 'lucide-react';
import { connectorApi, DatasetCatalog } from '../services/connectorApi';

interface DatasetSummaryProps {
  datasetId: string;
  datasetName: string;
  isOpen: boolean;
  onClose: () => void;
  connectorStatus: 'connected' | 'disconnected' | 'checking';
}

export default function DatasetSummary({
  datasetId,
  datasetName,
  isOpen,
  onClose,
  connectorStatus,
}: DatasetSummaryProps) {
  const [catalog, setCatalog] = useState<DatasetCatalog | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isOpen && datasetId) {
      loadCatalog();
    }
  }, [isOpen, datasetId]);

  const loadCatalog = async () => {
    setLoading(true);
    setError(null);

    try {
      if (connectorStatus === 'connected') {
        const data = await connectorApi.getDatasetCatalog(datasetId);
        if (data) {
          setCatalog(data);
        } else {
          setError('No catalog available');
        }
      } else {
        setError('Connector not available');
      }
    } catch (err) {
      setError('Failed to load dataset schema');
    } finally {
      setLoading(false);
    }
  };

  const getTypeColor = (type: string): string => {
    const upperType = type.toUpperCase();
    if (upperType.includes('INT')) return 'text-blue-600 bg-blue-50';
    if (upperType.includes('TEXT') || upperType.includes('VARCHAR'))
      return 'text-green-600 bg-green-50';
    if (
      upperType.includes('REAL') ||
      upperType.includes('FLOAT') ||
      upperType.includes('DECIMAL')
    )
      return 'text-orange-600 bg-orange-50';
    if (upperType.includes('DATE') || upperType.includes('TIME'))
      return 'text-amber-600 bg-amber-50';
    return 'text-slate-600 bg-slate-50';
  };

  const getPIIIcon = (type: string) => {
    switch (type) {
      case 'email':
        return <Mail className="w-3 h-3" />;
      case 'phone':
        return <Phone className="w-3 h-3" />;
      case 'name':
        return <User className="w-3 h-3" />;
      default:
        return <AlertTriangle className="w-3 h-3" />;
    }
  };

  const filteredColumns = catalog
    ? catalog.columns.filter((col) =>
        col.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : [];

  const copySchemaToClipboard = () => {
    if (!catalog) return;

    const summary = `Dataset: ${datasetName}
Table: ${catalog.table}
Total Rows: ${catalog.rowCount.toLocaleString()}
Total Columns: ${catalog.columns.length}

Columns:
${catalog.columns
  .map((col) => {
    const stats = catalog.basicStats[col.name];
    const nullPct = stats ? `${stats.nullPct.toFixed(1)}% null` : '';
    return `  - ${col.name} (${col.type}) ${nullPct}`;
  })
  .join('\n')}

${
  catalog.detectedDateColumns.length > 0
    ? `Date Columns: ${catalog.detectedDateColumns.join(', ')}\n`
    : ''
}${
      catalog.detectedNumericColumns.length > 0
        ? `Numeric Columns: ${catalog.detectedNumericColumns.join(', ')}\n`
        : ''
    }${
      catalog.piiColumns.length > 0
        ? `\nSensitive Columns Detected:\n${catalog.piiColumns
            .map(
              (pii) =>
                `  - ${pii.name} (${pii.type}, ${(pii.confidence * 100).toFixed(0)}% confidence)`
            )
            .join('\n')}`
        : ''
    }`;

    navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/20 z-40 transition-opacity"
        onClick={onClose}
      />
      <div className="fixed right-0 top-0 bottom-0 w-full max-w-3xl bg-white shadow-2xl z-50 flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-slate-200 bg-gradient-to-r from-emerald-50 to-teal-50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
              <Database className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Dataset Schema</h2>
              <p className="text-sm text-slate-600">{datasetName}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-600" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
                <p className="text-sm text-slate-600">Loading schema...</p>
              </div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-900">{error}</p>
            </div>
          ) : catalog ? (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Hash className="w-4 h-4 text-emerald-600" />
                    <span className="text-xs font-medium text-emerald-900">Rows</span>
                  </div>
                  <p className="text-2xl font-bold text-emerald-900">
                    {catalog.rowCount.toLocaleString()}
                  </p>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Type className="w-4 h-4 text-blue-600" />
                    <span className="text-xs font-medium text-blue-900">Columns</span>
                  </div>
                  <p className="text-2xl font-bold text-blue-900">{catalog.columns.length}</p>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Table className="w-4 h-4 text-slate-600" />
                    <span className="text-xs font-medium text-slate-900">Table</span>
                  </div>
                  <p className="text-lg font-bold text-slate-900 font-mono truncate">
                    {catalog.table}
                  </p>
                </div>
              </div>

              {catalog.piiColumns.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                    <h3 className="font-semibold text-red-900">Sensitive Columns Detected</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {catalog.piiColumns.map((pii, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-2 px-3 py-1.5 bg-white border border-red-200 rounded-lg"
                      >
                        <div className="text-red-600">{getPIIIcon(pii.type)}</div>
                        <span className="font-mono text-sm text-red-900">{pii.name}</span>
                        <span className="text-xs text-red-600">
                          {pii.type} ({(pii.confidence * 100).toFixed(0)}%)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {(catalog.detectedDateColumns.length > 0 ||
                catalog.detectedNumericColumns.length > 0) && (
                <div className="grid grid-cols-2 gap-4">
                  {catalog.detectedDateColumns.length > 0 && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Calendar className="w-4 h-4 text-amber-600" />
                        <h4 className="text-sm font-semibold text-amber-900">Date Columns</h4>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {catalog.detectedDateColumns.map((col, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-white border border-amber-200 rounded text-xs font-mono text-amber-900"
                          >
                            {col}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {catalog.detectedNumericColumns.length > 0 && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Hash className="w-4 h-4 text-blue-600" />
                        <h4 className="text-sm font-semibold text-blue-900">Numeric Columns</h4>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {catalog.detectedNumericColumns.map((col, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-white border border-blue-200 rounded text-xs font-mono text-blue-900"
                          >
                            {col}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-900">All Columns</h3>
                  <button
                    onClick={copySchemaToClipboard}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                  >
                    <Copy className="w-4 h-4" />
                    {copied ? 'Copied!' : 'Copy Schema Summary'}
                  </button>
                </div>

                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search columns..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-lg overflow-hidden">
                  <div className="max-h-96 overflow-y-auto">
                    {filteredColumns.length === 0 ? (
                      <div className="p-8 text-center text-slate-500">
                        <p className="text-sm">No columns found</p>
                      </div>
                    ) : (
                      <div className="divide-y divide-slate-200">
                        {filteredColumns.map((column, idx) => {
                          const stats = catalog.basicStats[column.name];
                          const isPII = catalog.piiColumns.some((pii) => pii.name === column.name);
                          return (
                            <div
                              key={idx}
                              className="p-3 bg-white hover:bg-slate-50 transition-colors"
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="font-mono text-sm text-slate-900 font-medium">
                                      {column.name}
                                    </span>
                                    {isPII && (
                                      <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-medium rounded">
                                        PII
                                      </span>
                                    )}
                                  </div>
                                  {stats && (
                                    <div className="flex items-center gap-3 text-xs text-slate-600">
                                      <span>{stats.nullPct.toFixed(1)}% null</span>
                                      {stats.approxDistinct && (
                                        <span>~{stats.approxDistinct.toLocaleString()} distinct</span>
                                      )}
                                    </div>
                                  )}
                                </div>
                                <span
                                  className={`px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap ${getTypeColor(
                                    column.type
                                  )}`}
                                >
                                  {column.type}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>

        <div className="p-6 border-t border-slate-200 bg-slate-50">
          <p className="text-xs text-slate-600 text-center">
            This schema represents the structure of your dataset. Use it to understand what data is
            available for analysis.
          </p>
        </div>
      </div>
    </>
  );
}
