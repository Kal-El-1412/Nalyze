import React from 'react';
import { ChevronUp, ChevronDown, Database, Hash, Type, AlertTriangle, Calendar, Shield, ShieldCheck, Eye } from 'lucide-react';
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
    <div className="fixed bottom-4 left-1/2 z-40 w-[min(860px,calc(100vw-2rem))] -translate-x-1/2">
      <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white/95 dark:bg-slate-950/95 backdrop-blur-sm shadow-xl shadow-slate-900/10 dark:shadow-slate-900/40">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors"
          aria-expanded={open}
          aria-controls="dataset-summary-drawer-content"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-7 h-7 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <Database className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="min-w-0">
              <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide leading-none mb-0.5">
                Dataset Summary
              </div>
              <div className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
                {datasetName}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="hidden sm:flex items-center gap-1.5">
              <span className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 bg-slate-50 dark:bg-slate-900">
                <Hash className="w-3 h-3 text-emerald-600" />
                {rows.toLocaleString()}
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
                <span className="hidden md:flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40">
                  <Calendar className="w-3 h-3" />
                  {catalog.detectedDateColumns.length} dates
                </span>
              )}
            </div>

            <div className="flex items-center gap-1.5 pl-2 border-l border-slate-200 dark:border-slate-700">
              <span className={`hidden sm:flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold ${
                privacyMode
                  ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                  : 'bg-slate-50 dark:bg-slate-900 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700'
              }`}>
                <ShieldCheck className="w-3 h-3" />
                Privacy {privacyMode ? 'ON' : 'OFF'}
              </span>
              <span className={`hidden sm:flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold ${
                safeMode
                  ? 'bg-sky-50 dark:bg-sky-900/20 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800'
                  : 'bg-slate-50 dark:bg-slate-900 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700'
              }`}>
                <Shield className="w-3 h-3" />
                Safe {safeMode ? 'ON' : 'OFF'}
              </span>
              {onViewSchema && (
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); onViewSchema(); }}
                  className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/40 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition-colors"
                >
                  <Eye className="w-3 h-3" />
                  Schema
                </button>
              )}
            </div>

            <div className="w-7 h-7 flex items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 ml-1">
              {open ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
            </div>
          </div>
        </button>

        <div
          id="dataset-summary-drawer-content"
          className={`overflow-hidden transition-all duration-250 ease-in-out ${
            open ? 'max-h-[55vh] opacity-100' : 'max-h-0 opacity-0'
          }`}
        >
          <div className="border-t border-slate-200 dark:border-slate-700 px-4 pb-4 pt-3 overflow-y-auto max-h-[55vh]">
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
    </div>
  );
}
