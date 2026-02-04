import { X, Copy, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { useState } from 'react';

interface JobDetails {
  id: string;
  title: string;
  status: 'running' | 'completed' | 'failed';
  stage?: 'queued' | 'scanning_headers' | 'ingesting_rows' | 'building_catalog' | 'done' | 'error';
  timestamp: string;
  duration?: string;
  startedAt?: string;
  finishedAt?: string;
  updatedAt?: string;
  error?: string;
}

interface JobDetailsPanelProps {
  job: JobDetails;
  onClose: () => void;
}

export default function JobDetailsPanel({ job, onClose }: JobDetailsPanelProps) {
  const [copied, setCopied] = useState(false);

  const copyError = () => {
    if (job.error) {
      navigator.clipboard.writeText(job.error);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getStageLabel = (stage?: string) => {
    switch (stage) {
      case 'queued':
        return 'Queued';
      case 'scanning_headers':
        return 'Scanning Headers';
      case 'ingesting_rows':
        return 'Ingesting Rows';
      case 'building_catalog':
        return 'Building Catalog';
      case 'done':
        return 'Complete';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  const stages = [
    { id: 'queued', label: 'Queued' },
    { id: 'scanning_headers', label: 'Scanning Headers' },
    { id: 'ingesting_rows', label: 'Ingesting Rows' },
    { id: 'building_catalog', label: 'Building Catalog' },
    { id: 'done', label: 'Complete' }
  ];

  const getCurrentStageIndex = () => {
    const index = stages.findIndex(s => s.id === job.stage);
    return index !== -1 ? index : 0;
  };

  const currentStageIndex = getCurrentStageIndex();

  const formatTime = (isoString?: string) => {
    if (!isoString) return 'N/A';
    try {
      return new Date(isoString).toLocaleString();
    } catch {
      return isoString;
    }
  };

  const calculateElapsedTime = () => {
    if (!job.startedAt) return null;

    const start = new Date(job.startedAt).getTime();
    const end = job.finishedAt ? new Date(job.finishedAt).getTime() : Date.now();
    const elapsed = Math.floor((end - start) / 1000);

    if (elapsed < 60) return `${elapsed}s`;
    if (elapsed < 3600) return `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`;
    return `${Math.floor(elapsed / 3600)}h ${Math.floor((elapsed % 3600) / 60)}m`;
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-3xl w-full shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-slate-200 sticky top-0 bg-white z-10">
          <h2 className="text-xl font-bold text-slate-900">Job Details</h2>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div>
            <h3 className="text-sm font-medium text-slate-500 mb-2">Job Title</h3>
            <p className="text-lg font-semibold text-slate-900">{job.title}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-slate-500 mb-2">Status</h3>
              <div className="flex items-center gap-2">
                {job.status === 'completed' && (
                  <>
                    <CheckCircle className="w-5 h-5 text-emerald-600" />
                    <span className="text-emerald-700 font-medium">Completed</span>
                  </>
                )}
                {job.status === 'running' && (
                  <>
                    <Clock className="w-5 h-5 text-blue-600" />
                    <span className="text-blue-700 font-medium">Running</span>
                  </>
                )}
                {job.status === 'failed' && (
                  <>
                    <AlertCircle className="w-5 h-5 text-red-600" />
                    <span className="text-red-700 font-medium">Failed</span>
                  </>
                )}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-slate-500 mb-2">Elapsed Time</h3>
              <p className="text-slate-900 font-medium">{calculateElapsedTime() || 'Not started'}</p>
            </div>
          </div>

          {job.status !== 'failed' && (
            <div>
              <h3 className="text-sm font-medium text-slate-500 mb-4">Progress</h3>
              <div className="space-y-3">
                {stages.map((stage, index) => (
                  <div key={stage.id} className="flex items-center gap-3">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                        index < currentStageIndex
                          ? 'bg-emerald-500 border-emerald-500'
                          : index === currentStageIndex && job.status === 'running'
                          ? 'bg-blue-500 border-blue-500 animate-pulse'
                          : index === currentStageIndex && job.status === 'completed'
                          ? 'bg-emerald-500 border-emerald-500'
                          : 'bg-white border-slate-300'
                      }`}
                    >
                      {index <= currentStageIndex ? (
                        <CheckCircle className="w-5 h-5 text-white" />
                      ) : (
                        <span className="text-xs font-medium text-slate-400">{index + 1}</span>
                      )}
                    </div>
                    <div className="flex-1">
                      <p
                        className={`font-medium ${
                          index === currentStageIndex
                            ? 'text-slate-900'
                            : index < currentStageIndex
                            ? 'text-emerald-700'
                            : 'text-slate-400'
                        }`}
                      >
                        {stage.label}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-200">
            <div>
              <h3 className="text-sm font-medium text-slate-500 mb-1">Started At</h3>
              <p className="text-sm text-slate-700">{formatTime(job.startedAt)}</p>
            </div>
            {job.finishedAt && (
              <div>
                <h3 className="text-sm font-medium text-slate-500 mb-1">Finished At</h3>
                <p className="text-sm text-slate-700">{formatTime(job.finishedAt)}</p>
              </div>
            )}
            {job.updatedAt && (
              <div>
                <h3 className="text-sm font-medium text-slate-500 mb-1">Last Updated</h3>
                <p className="text-sm text-slate-700">{formatTime(job.updatedAt)}</p>
              </div>
            )}
          </div>

          {job.error && (
            <div className="pt-4 border-t border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-red-600">Error Details</h3>
                <button
                  onClick={copyError}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  <Copy className="w-4 h-4" />
                  {copied ? 'Copied!' : 'Copy Error'}
                </button>
              </div>
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-900 font-mono whitespace-pre-wrap break-words">
                  {job.error}
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end p-6 border-t border-slate-200 bg-slate-50">
          <button
            onClick={onClose}
            className="px-6 py-2.5 bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
