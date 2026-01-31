import { Database, Plus, Trash2, Calendar } from 'lucide-react';
import PIIScanResults from './PIIScanResults';

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
}

export default function DatasetsPanel({
  datasets,
  activeDataset,
  onSelectDataset,
  onAddDataset,
  onDeleteDataset,
}: DatasetsPanelProps) {
  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-slate-200">
        <button
          onClick={onAddDataset}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Dataset
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {activeDataset && datasets.length > 0 && (
          <div className="mb-4">
            <PIIScanResults />
          </div>
        )}
        {datasets.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <Database className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No datasets yet</p>
            <p className="text-xs mt-1">Connect a data source to get started</p>
          </div>
        ) : (
          datasets.map((dataset) => (
            <div
              key={dataset.id}
              className={`p-4 rounded-lg border transition-all cursor-pointer group ${
                activeDataset === dataset.id
                  ? 'border-emerald-500 bg-emerald-50'
                  : 'border-slate-200 hover:border-slate-300 bg-white'
              }`}
              onClick={() => onSelectDataset(dataset.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <Database className="w-4 h-4 text-slate-400 flex-shrink-0" />
                    <h3 className="font-medium text-slate-900 truncate">{dataset.name}</h3>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-600">
                    <span>{dataset.rows.toLocaleString()} rows</span>
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
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-600 transition-all"
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
