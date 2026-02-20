import React from 'react';
import { X, Database, Hash, Type, AlertTriangle, Calendar, Shield, ShieldCheck, Eye, LayoutList } from 'lucide-react';
import { DatasetCatalog } from '../services/connectorApi';
import DatasetSummaryCard from './DatasetSummaryCard';

interface DatasetSummaryDrawerProps {
  catalog: DatasetCatalog | null;
  datasetName?: string;
  privacyMode?: boolean;
  safeMode?: boolean;
  onViewSchema?: () => void;
}

const STORAGE_KEY = 'cs:datasetSummaryDrawerOpen';

export default function DatasetSummaryDrawer({
  catalog,
  datasetName,
  privacyMode = true,
  safeMode = false,
  onViewSchema,
}: DatasetSummaryDrawerProps) {
  const [open, setOpen] = React.useState<boolean>(() => {
    const v = localStorage.getItem(STORAGE_KEY);
    return v === 'true';
  });

  React.useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(open));
  }, [open]);

  if (!catalog || !datasetName) return null;

  const rows = catalog.rowCount;
  const columns = catalog.columns.length;

  return (
    <>
      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open dataset summary"
          className="fixed right-0 top-1/2 z-50 -translate-y-1/2 flex flex-col items-center gap-1.5 px-2 py-4 rounded-l-xl border border-r-0 border-slate-200 dark:border-slate-700 bg-white/95 dark:bg-slate-950/95 backdrop-blur-sm shadow-lg text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-900/70 transition-colors"
        >
          <LayoutList className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          <span
            className="text-xs font-semibold tracking-wide text-slate-600 dark:text-slate-300"
            style={{ writingMode: 'vertical-rl', textOrientation: 'mixed', transform: 'rotate(180deg)' }}
          >
            Dataset
          </span>
        </button>
      )}

      <div
        className={`fixed top-16 right-0 bottom-0 z-50 w-[340px] max-w-[calc(100vw-3rem)] transition-transform duration-200 ease-in-out ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="h-full flex flex-col rounded-tl-2xl border-l border-t border-slate-200 dark:border-slate-700 bg-white/97 dark:bg-slate-950/97 backdrop-blur-sm shadow-2xl shadow-slate-900/15 dark:shadow-slate-900/50">
          <div className="flex items-center justify-between gap-2 px-4 py-3 border-b border-slate-200 dark:border-slate-700 flex-shrink-0">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-7 h-7 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <Database className="w-3.5 h-3.5 text-white" />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide leading-none mb-0.5">
                  Dataset Summary
                </div>
                <div className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                  {datasetName}
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close dataset summary"
              className="w-8 h-8 flex items-center justify-center rounded-lg border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex-shrink-0"
            >
              <X size={15} />
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-1.5 px-4 py-2.5 border-b border-slate-200 dark:border-slate-700 flex-shrink-0">
            <span className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 bg-slate-50 dark:bg-slate-900">
              <Hash className="w-3 h-3 text-emerald-600" />
              {rows.toLocaleString()} rows
            </span>
            <span className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 bg-slate-50 dark:bg-slate-900">
              <Type className="w-3 h-3 text-blue-600" />
              {columns} cols
            </span>
            {catalog.piiColumns.length > 0 && (
              <span className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-950/40">
                <AlertTriangle className="w-3 h-3" />
                {catalog.piiColumns.length} PII
              </span>
            )}
            {catalog.detectedDateColumns.length > 0 && (
              <span className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40">
                <Calendar className="w-3 h-3" />
                {catalog.detectedDateColumns.length} dates
              </span>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-1.5 px-4 py-2 border-b border-slate-200 dark:border-slate-700 flex-shrink-0">
            <span className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold border ${
              privacyMode
                ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                : 'bg-slate-50 dark:bg-slate-900 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700'
            }`}>
              <ShieldCheck className="w-3 h-3" />
              Privacy {privacyMode ? 'ON' : 'OFF'}
            </span>
            <span className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold border ${
              safeMode
                ? 'bg-sky-50 dark:bg-sky-900/20 text-sky-700 dark:text-sky-300 border-sky-200 dark:border-sky-800'
                : 'bg-slate-50 dark:bg-slate-900 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700'
            }`}>
              <Shield className="w-3 h-3" />
              Safe Mode {safeMode ? 'ON' : 'OFF'}
            </span>
            {onViewSchema && (
              <button
                type="button"
                onClick={onViewSchema}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/40 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition-colors ml-auto"
              >
                <Eye className="w-3 h-3" />
                View Schema
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-3">
            <DatasetSummaryCard
              catalog={catalog}
              datasetName={datasetName}
              onViewSchema={onViewSchema ?? (() => {})}
              privacyMode={privacyMode}
              safeMode={safeMode}
            />
          </div>
        </div>
      </div>
    </>
  );
}
