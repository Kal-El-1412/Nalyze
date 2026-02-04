import { Clock, CheckCircle, AlertCircle, Loader2, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import JobDetailsPanel from './JobDetailsPanel';

interface Job {
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

interface JobsPanelProps {
  jobs: Job[];
}

export default function JobsPanel({ jobs }: JobsPanelProps) {
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  const getStatusIcon = (status: Job['status']) => {
    switch (status) {
      case 'running':
        return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-emerald-600" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
    }
  };

  const getStatusColor = (status: Job['status']) => {
    switch (status) {
      case 'running':
        return 'border-blue-200 bg-blue-50';
      case 'completed':
        return 'border-emerald-200 bg-emerald-50';
      case 'failed':
        return 'border-red-200 bg-red-50';
    }
  };

  const getStageLabel = (stage?: string) => {
    switch (stage) {
      case 'queued':
        return 'Queued';
      case 'scanning_headers':
        return 'Scanning headers';
      case 'ingesting_rows':
        return 'Ingesting rows';
      case 'building_catalog':
        return 'Building catalog';
      case 'done':
        return 'Complete';
      case 'error':
        return 'Error';
      default:
        return null;
    }
  };

  const calculateElapsedTime = (job: Job) => {
    if (!job.startedAt) return null;

    try {
      const start = new Date(job.startedAt).getTime();
      const end = job.finishedAt ? new Date(job.finishedAt).getTime() : Date.now();
      const elapsed = Math.floor((end - start) / 1000);

      if (elapsed < 60) return `${elapsed}s`;
      if (elapsed < 3600) return `${Math.floor(elapsed / 60)}m`;
      return `${Math.floor(elapsed / 3600)}h ${Math.floor((elapsed % 3600) / 60)}m`;
    } catch {
      return null;
    }
  };

  return (
    <>
      <div className="h-full flex flex-col">
        <div className="p-4 border-b border-slate-200">
          <h2 className="font-semibold text-slate-900">Recent Jobs</h2>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {jobs.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <Clock className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">No jobs yet</p>
              <p className="text-xs mt-1">Analysis jobs will appear here</p>
            </div>
          ) : (
            jobs.map((job) => (
              <button
                key={job.id}
                onClick={() => setSelectedJob(job)}
                className={`w-full p-4 rounded-lg border ${getStatusColor(
                  job.status
                )} transition-all hover:shadow-md text-left group`}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-0.5">{getStatusIcon(job.status)}</div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-slate-900 text-sm mb-1 truncate">
                      {job.title}
                    </h3>
                    {job.stage && job.status === 'running' && (
                      <p className="text-xs text-blue-700 font-medium mb-1">
                        {getStageLabel(job.stage)}
                      </p>
                    )}
                    <div className="flex items-center gap-3 text-xs text-slate-600">
                      {calculateElapsedTime(job) && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {calculateElapsedTime(job)}
                        </span>
                      )}
                      {job.updatedAt && (
                        <span>
                          Updated{' '}
                          {new Date(job.updatedAt).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-slate-600 transition-colors flex-shrink-0 mt-0.5" />
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {selectedJob && (
        <JobDetailsPanel job={selectedJob} onClose={() => setSelectedJob(null)} />
      )}
    </>
  );
}
