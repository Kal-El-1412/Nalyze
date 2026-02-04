import { Database, Plus, Trash2, Calendar, ShieldCheck } from 'lucide-react';
import PIIScanResults from './PIIScanResults';
import { DatasetCatalog } from '../services/connectorApi';

interface Dataset {
  id: string;
  name: string;
  rows: number;
  lastUsed: string;
}

interface DatasetsPanelProps {
  datasets: Dataset[];
  activeDataset: string | null;
  onSelectDataset: (id: string) => void;
  onAddDataset: () => void;
  onDeleteDataset: (id: string) => void;
  isConnected?: boolean;
  catalog?: DatasetCatalog | null;
  privacyMode?: boolean;
}

export default function DatasetsPanel({
  datasets,
  activeDataset,
  onSelectDataset,
  onAddDataset,
  onDeleteDataset,
  isConnected = false,
  catalog = null,
  privacyMode = true,
}: DatasetsPanelProps) {
  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-slate-200 space-y-3">
        <button
          onClick={onAddDataset}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors font-medium shadow-sm"
        >
          <Plus className="w-4 h-4" />
          Add Dataset
        </button>
        {isConnected && (
          <div className="flex items-center gap-2 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded-lg">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span className="text-xs font-medium text-emerald-700">Local-only privacy</span>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {activeDataset && datasets.length > 0 && catalog && (
          <div className="mb-4">
            <PIIScanResults catalog={catalog} privacyMode={privacyMode} />
          </div>
        )}
        {datasets.length === 0 ? (
          <div className="text-center py-16 px-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-slate-100 rounded-2xl mb-4">
              <Database className="w-8 h-8 text-slate-400" />
            </div>
            <h3 className="text-base font-semibold text-slate-900 mb-1">No datasets yet</h3>
            <p className="text-sm text-slate-500 mb-6">Connect a data source to start analyzing</p>
            <button
              onClick={onAddDataset}
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-medium rounded-lg hover:bg-slate-800 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Your First Dataset
            </button>
          </div>
        ) : (
          datasets.map((dataset) => (
            <div
              key={dataset.id}
              className={`p-4 rounded-xl border-2 transition-all cursor-pointer group ${
                activeDataset === dataset.id
                  ? 'border-emerald-500 bg-emerald-50 shadow-sm'
                  : 'border-slate-200 hover:border-slate-300 bg-white hover:shadow-sm'
              }`}
              onClick={() => onSelectDataset(dataset.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      activeDataset === dataset.id ? 'bg-emerald-100' : 'bg-slate-100'
                    }`}>
                      <Database className={`w-4 h-4 ${
                        activeDataset === dataset.id ? 'text-emerald-600' : 'text-slate-600'
                      }`} />
                    </div>
                    <h3 className="font-semibold text-slate-900 truncate">{dataset.name}</h3>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-600 ml-10">
                    <span className="font-medium">{dataset.rows.toLocaleString()} rows</span>
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {dataset.lastUsed}
                    </span>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteDataset(dataset.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
