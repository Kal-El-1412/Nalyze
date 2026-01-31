import { useState, useEffect } from 'react';
import { X, Database, Table, Hash, Type, Loader2 } from 'lucide-react';
import { connectorApi, DatasetCatalogResponse } from '../services/connectorApi';

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
  const [catalog, setCatalog] = useState<DatasetCatalogResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
          setCatalog(connectorApi.getMockCatalog());
        }
      } else {
        setCatalog(connectorApi.getMockCatalog());
      }
    } catch (err) {
      setError('Failed to load dataset schema');
      setCatalog(connectorApi.getMockCatalog());
    } finally {
      setLoading(false);
    }
  };

  const getTotalRows = () => {
    return catalog?.tables.reduce((sum, table) => sum + table.rowCount, 0) || 0;
  };

  const getTotalColumns = () => {
    return catalog?.tables.reduce((sum, table) => sum + table.columns.length, 0) || 0;
  };

  const getTypeColor = (type: string): string => {
    const upperType = type.toUpperCase();
    if (upperType.includes('INT')) return 'text-blue-600 bg-blue-50';
    if (upperType.includes('TEXT') || upperType.includes('VARCHAR')) return 'text-green-600 bg-green-50';
    if (upperType.includes('REAL') || upperType.includes('FLOAT') || upperType.includes('DECIMAL')) return 'text-purple-600 bg-purple-50';
    if (upperType.includes('DATE') || upperType.includes('TIME')) return 'text-amber-600 bg-amber-50';
    return 'text-slate-600 bg-slate-50';
  };

  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/20 z-40 transition-opacity"
        onClick={onClose}
      />
      <div className="fixed right-0 top-0 bottom-0 w-full max-w-2xl bg-white shadow-2xl z-50 flex flex-col">
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
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Table className="w-4 h-4 text-blue-600" />
                    <span className="text-xs font-medium text-blue-900">Tables</span>
                  </div>
                  <p className="text-2xl font-bold text-blue-900">{catalog.tables.length}</p>
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Type className="w-4 h-4 text-purple-600" />
                    <span className="text-xs font-medium text-purple-900">Columns</span>
                  </div>
                  <p className="text-2xl font-bold text-purple-900">{getTotalColumns()}</p>
                </div>
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Hash className="w-4 h-4 text-emerald-600" />
                    <span className="text-xs font-medium text-emerald-900">Rows</span>
                  </div>
                  <p className="text-2xl font-bold text-emerald-900">{getTotalRows().toLocaleString()}</p>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-slate-900">Tables & Columns</h3>
                {catalog.tables.map((table, tableIdx) => (
                  <div
                    key={tableIdx}
                    className="bg-slate-50 border border-slate-200 rounded-lg overflow-hidden"
                  >
                    <div className="bg-white border-b border-slate-200 px-4 py-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Table className="w-4 h-4 text-slate-600" />
                          <span className="font-mono font-semibold text-slate-900">{table.name}</span>
                        </div>
                        <span className="text-xs text-slate-500">
                          {table.rowCount.toLocaleString()} rows
                        </span>
                      </div>
                    </div>
                    <div className="p-4">
                      <div className="grid grid-cols-1 gap-2">
                        {table.columns.map((column, colIdx) => (
                          <div
                            key={colIdx}
                            className="flex items-center justify-between p-2 bg-white rounded border border-slate-100 hover:border-slate-300 transition-colors"
                          >
                            <span className="font-mono text-sm text-slate-900">{column.name}</span>
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-medium ${getTypeColor(column.type)}`}
                            >
                              {column.type}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        <div className="p-6 border-t border-slate-200 bg-slate-50">
          <p className="text-xs text-slate-600 text-center">
            This schema represents the structure of your dataset. Use it to understand what data is available for analysis.
          </p>
        </div>
      </div>
    </>
  );
}
