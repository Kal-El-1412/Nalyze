import { X, Wifi, Cloud, Info, CheckCircle } from 'lucide-react';
import { useState } from 'react';

interface ConnectDataModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnect: (type: 'local' | 'cloud', data: { name?: string; filePath?: string; file?: File }) => void;
}

export default function ConnectDataModal({ isOpen, onClose, onConnect }: ConnectDataModalProps) {
  const [selectedType, setSelectedType] = useState<'local' | 'cloud' | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [localFile, setLocalFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState('');
  const [filePath, setFilePath] = useState('');

  if (!isOpen) return null;

  const handleLocalFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setLocalFile(selectedFile);

      const inputElement = e.target as HTMLInputElement;
      let extractedPath = '';

      if ((selectedFile as any).path) {
        extractedPath = (selectedFile as any).path;
      } else if (inputElement.value) {
        extractedPath = inputElement.value.replace(/^C:\\fakepath\\/, '');
      } else {
        extractedPath = selectedFile.name;
      }

      setFilePath(extractedPath);

      if (!datasetName) {
        const nameWithoutExt = selectedFile.name.replace(/\.[^/.]+$/, '');
        setDatasetName(nameWithoutExt);
      }
    }
  };

  const handleConnect = () => {
    if (selectedType === 'cloud' && file) {
      onConnect('cloud', { file });
    } else if (selectedType === 'local' && datasetName && (filePath || localFile)) {
      onConnect('local', { name: datasetName, filePath: filePath || localFile?.name || '' });
    }
    onClose();
    setSelectedType(null);
    setFile(null);
    setLocalFile(null);
    setDatasetName('');
    setFilePath('');
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl">
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <h2 className="text-2xl font-bold text-slate-900">Connect Data Source</h2>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex gap-3">
            <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-900">
              <p className="font-medium mb-1">Privacy-First Approach</p>
              <p className="text-blue-700">
                Local Connector keeps your data on your device. Cloud upload is only recommended for
                small, non-sensitive files.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <button
              onClick={() => setSelectedType('local')}
              className={`w-full p-6 rounded-xl border-2 transition-all text-left ${
                selectedType === 'local'
                  ? 'border-emerald-500 bg-emerald-50'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Wifi className="w-6 h-6 text-emerald-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-semibold text-slate-900">
                      Local Connector
                    </h3>
                    <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full">
                      Recommended
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 mb-3">
                    Securely connect to spreadsheets on your device. Data never leaves your computer.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-white border border-slate-200 rounded text-xs text-slate-600">
                      <CheckCircle className="w-3 h-3 text-emerald-600" />
                      Zero upload
                    </span>
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-white border border-slate-200 rounded text-xs text-slate-600">
                      <CheckCircle className="w-3 h-3 text-emerald-600" />
                      Maximum privacy
                    </span>
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-white border border-slate-200 rounded text-xs text-slate-600">
                      <CheckCircle className="w-3 h-3 text-emerald-600" />
                      Unlimited size
                    </span>
                  </div>
                </div>
              </div>
            </button>

            <button
              onClick={() => setSelectedType('cloud')}
              className={`w-full p-6 rounded-xl border-2 transition-all text-left ${
                selectedType === 'cloud'
                  ? 'border-emerald-500 bg-emerald-50'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Cloud className="w-6 h-6 text-slate-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">
                    Cloud Upload
                  </h3>
                  <p className="text-sm text-slate-600 mb-3">
                    Upload small files directly. Only use for non-sensitive data.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <span className="px-2 py-1 bg-white border border-slate-200 rounded text-xs text-slate-600">
                      Max 10MB
                    </span>
                    <span className="px-2 py-1 bg-white border border-slate-200 rounded text-xs text-slate-600">
                      CSV, XLSX
                    </span>
                  </div>
                </div>
              </div>
            </button>

            {selectedType === 'local' && (
              <div className="pt-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Choose File
                  </label>
                  <input
                    type="file"
                    accept=".csv,.xlsx,.xls,.parquet"
                    onChange={handleLocalFileChange}
                    className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 file:cursor-pointer"
                  />
                  {localFile && (
                    <div className="mt-2 p-2 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-700">
                      Selected: {localFile.name} ({(localFile.size / 1024 / 1024).toFixed(2)} MB)
                    </div>
                  )}
                  <p className="text-xs text-slate-500 mt-2">
                    Browse and select your spreadsheet file (CSV, XLSX, XLS, Parquet)
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Dataset Name
                  </label>
                  <input
                    type="text"
                    value={datasetName}
                    onChange={(e) => setDatasetName(e.target.value)}
                    placeholder="e.g., Sales Data 2024"
                    className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                  <p className="text-xs text-slate-500 mt-2">
                    Auto-filled from filename, but you can customize it
                  </p>
                </div>
              </div>
            )}

            {selectedType === 'cloud' && (
              <div className="pt-4">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Upload File
                </label>
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-3 p-6 border-t border-slate-200">
          <button
            onClick={onClose}
            className="flex-1 px-6 py-3 border border-slate-300 text-slate-700 font-medium rounded-lg hover:bg-slate-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConnect}
            disabled={
              !selectedType ||
              (selectedType === 'cloud' && !file) ||
              (selectedType === 'local' && (!datasetName || !localFile))
            }
            className="flex-1 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-semibold rounded-lg hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            Connect
          </button>
        </div>
      </div>
    </div>
  );
}
