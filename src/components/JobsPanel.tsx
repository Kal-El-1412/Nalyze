import { Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface Job {
  id: string;
  title: string;
  status: 'running' | 'completed' | 'failed';
  timestamp: string;
  duration?: string;
}

interface JobsPanelProps {
  jobs: Job[];
}

export default function JobsPanel({ jobs }: JobsPanelProps) {
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

  return (
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
            <div
              key={job.id}
              className={`p-4 rounded-lg border ${getStatusColor(job.status)} transition-all`}
            >
              <div className="flex items-start gap-3">
                {getStatusIcon(job.status)}
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-slate-900 text-sm mb-1">{job.title}</h3>
                  <div className="flex items-center gap-3 text-xs text-slate-600">
                    <span>{job.timestamp}</span>
                    {job.duration && <span>• {job.duration}</span>}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
