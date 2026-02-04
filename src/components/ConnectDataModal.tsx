import { X, Upload, Info, CheckCircle, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import { useState } from 'react';

interface ConnectDataModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnect: (type: 'local' | 'cloud', data: { name?: string; filePath?: string; file?: File }) => void;
}

export default function ConnectDataModal({ isOpen, onClose, onConnect }: ConnectDataModalProps) {
  const [uploadMode, setUploadMode] = useState<'upload' | 'path'>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState('');
  const [manualPath, setManualPath] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      if (!datasetName) {
        const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '');
        setDatasetName(nameWithoutExt);
      }
    }
  };

  const handleConnect = () => {
    if (uploadMode === 'upload' && selectedFile && datasetName) {
      onConnect('local', { name: datasetName, file: selectedFile });
    } else if (uploadMode === 'path' && manualPath && datasetName) {
      onConnect('local', { name: datasetName, filePath: manualPath });
    }
    onClose();
    setUploadMode('upload');
    setSelectedFile(null);
    setDatasetName('');
    setManualPath('');
    setShowAdvanced(false);
  };

  const isValid = uploadMode === 'upload'
    ? selectedFile && datasetName
    : manualPath && datasetName;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-slate-200 sticky top-0 bg-white z-10">
          <h2 className="text-2xl font-bold text-slate-900">Connect Data Source</h2>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex gap-3">
            <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-900">
              <p className="font-medium mb-1">Privacy-First Design</p>
              <p className="text-blue-700">
                Your data stays on your device. Files are processed locally by the connector.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">
                Dataset Name
              </label>
              <input
                type="text"
                value={datasetName}
                onChange={(e) => setDatasetName(e.target.value)}
                placeholder="e.g., Sales Data 2024"
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-900"
              />
              <p className="text-xs text-slate-500 mt-2">
                Give your dataset a descriptive name
              </p>
            </div>

            <div className="border-2 border-slate-200 rounded-xl p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                  <Upload className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-slate-900">Choose File</h3>
                  <p className="text-sm text-slate-600">Select a file from your device</p>
                </div>
              </div>

              <div className="space-y-3">
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls,.parquet"
                  onChange={handleFileChange}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="block cursor-pointer border-2 border-dashed border-slate-300 rounded-lg p-6 hover:border-emerald-500 hover:bg-emerald-50/50 transition-colors text-center"
                >
                  <FileText className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <p className="text-sm font-medium text-slate-700 mb-1">
                    Click to browse files
                  </p>
                  <p className="text-xs text-slate-500">
                    CSV preferred • XLSX limited support
                  </p>
                </label>

                {selectedFile && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-emerald-900 truncate">
                          {selectedFile.name}
                        </p>
                        <p className="text-xs text-emerald-700">
                          {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
            >
              {showAdvanced ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
              <span className="font-medium">Advanced: Manual File Path</span>
            </button>

            {showAdvanced && (
              <div className="border-2 border-slate-200 rounded-xl p-5 space-y-4 bg-slate-50">
                <div className="flex items-start gap-2">
                  <Info className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-slate-600">
                    For advanced users: Enter the full path to a file on your system. The connector must have read access to this location.
                  </p>
                </div>

                <div className="flex gap-3 mb-3">
                  <button
                    onClick={() => setUploadMode('upload')}
                    className={`flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                      uploadMode === 'upload'
                        ? 'bg-emerald-600 text-white'
                        : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    Upload File
                  </button>
                  <button
                    onClick={() => setUploadMode('path')}
                    className={`flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                      uploadMode === 'path'
                        ? 'bg-emerald-600 text-white'
                        : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    File Path
                  </button>
                </div>

                {uploadMode === 'path' && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      File Path
                    </label>
                    <input
                      type="text"
                      value={manualPath}
                      onChange={(e) => setManualPath(e.target.value)}
                      placeholder="/path/to/your/data.csv"
                      className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-900 bg-white font-mono text-sm"
                    />
                    <p className="text-xs text-slate-500 mt-2">
                      Example: /Users/name/Documents/data.csv or C:\Users\name\Documents\data.csv
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-3 p-6 border-t border-slate-200 bg-slate-50 sticky bottom-0">
          <button
            onClick={onClose}
            className="flex-1 px-6 py-3 border border-slate-300 text-slate-700 font-medium rounded-lg hover:bg-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConnect}
            disabled={!isValid}
            className="flex-1 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-semibold rounded-lg hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            Connect Dataset
          </button>
        </div>
      </div>
    </div>
  );
}
