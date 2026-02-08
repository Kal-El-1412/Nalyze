import { Database, Hash, Type, AlertTriangle, Eye, Calendar, ShieldCheck, Shield } from 'lucide-react';
import { DatasetCatalog } from '../services/connectorApi';

interface DatasetSummaryCardProps {
  catalog: DatasetCatalog | null;
  datasetName: string;
  onViewSchema: () => void;
  privacyMode?: boolean;
  safeMode?: boolean;
}

export default function DatasetSummaryCard({
  catalog,
  datasetName,
  onViewSchema,
  privacyMode = true,
  safeMode = false,
}: DatasetSummaryCardProps) {
  if (!catalog) return null;

  const hasPII = catalog.piiColumns.length > 0;
  const hasDateColumns = catalog.detectedDateColumns.length > 0;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm overflow-hidden">
      <div className="bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950 dark:to-teal-950 px-4 py-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
              <Database className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Dataset Summary</h3>
                {hasPII && (
                  <div
                    className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
                      privacyMode
                        ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-300 dark:border-slate-700'
                    }`}
                  >
                    <ShieldCheck className="w-3 h-3" />
                    <span>Privacy: {privacyMode ? 'ON' : 'OFF'}</span>
                  </div>
                )}
                <div
                  className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
                    safeMode
                      ? 'bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border border-blue-300 dark:border-blue-700'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-300 dark:border-slate-700'
                  }`}
                >
                  <Shield className="w-3 h-3" />
                  <span>Safe Mode: {safeMode ? 'ON' : 'OFF'}</span>
                </div>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300">{datasetName}</p>
            </div>
          </div>
          <button
            onClick={onViewSchema}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-300 bg-white dark:bg-slate-800 hover:bg-emerald-50 dark:hover:bg-emerald-950 border border-emerald-200 dark:border-emerald-700 rounded-lg transition-colors"
          >
            <Eye className="w-3.5 h-3.5" />
            View Schema
          </button>
        </div>
      </div>

      <div className="p-4">
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Hash className="w-3.5 h-3.5 text-emerald-600" />
              <span className="text-xs font-medium text-slate-600 dark:text-slate-300">Rows</span>
            </div>
            <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
              {catalog.rowCount.toLocaleString()}
            </p>
          </div>
          <div className="text-center border-l border-r border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Type className="w-3.5 h-3.5 text-blue-600" />
              <span className="text-xs font-medium text-slate-600 dark:text-slate-300">Columns</span>
            </div>
            <p className="text-lg font-bold text-slate-900 dark:text-slate-100">{catalog.columns.length}</p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Database className="w-3.5 h-3.5 text-slate-600 dark:text-slate-300" />
              <span className="text-xs font-medium text-slate-600 dark:text-slate-300">Table</span>
            </div>
            <p className="text-sm font-bold text-slate-900 dark:text-slate-100 font-mono truncate">
              {catalog.table}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {hasDateColumns && (
            <div className="flex items-center gap-1.5 px-2 py-1 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-lg">
              <Calendar className="w-3 h-3 text-amber-600" />
              <span className="text-xs font-medium text-amber-900 dark:text-amber-100">
                {catalog.detectedDateColumns.length} date column
                {catalog.detectedDateColumns.length !== 1 ? 's' : ''}
              </span>
            </div>
          )}
          {catalog.detectedNumericColumns.length > 0 && (
            <div className="flex items-center gap-1.5 px-2 py-1 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
              <Hash className="w-3 h-3 text-blue-600" />
              <span className="text-xs font-medium text-blue-900 dark:text-blue-100">
                {catalog.detectedNumericColumns.length} numeric
              </span>
            </div>
          )}
          {hasPII && (
            <div className="flex items-center gap-1.5 px-2 py-1 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg">
              <AlertTriangle className="w-3 h-3 text-red-600" />
              <span className="text-xs font-medium text-red-900 dark:text-red-100">
                {catalog.piiColumns.length} sensitive column
                {catalog.piiColumns.length !== 1 ? 's' : ''}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
