import { FileText, Download, Trash2, Calendar, CheckCircle } from 'lucide-react';

interface Report {
  id: string;
  datasetName: string;
  timestamp: string;
  conversationId: string;
  htmlContent: string;
}

interface ReportsPanelProps {
  reports: Report[];
  onDownloadReport: (report: Report) => void;
  onDeleteReport: (id: string) => void;
}

export default function ReportsPanel({
  reports,
  onDownloadReport,
  onDeleteReport,
}: ReportsPanelProps) {
  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-slate-200">
        <div className="flex items-center gap-2 text-slate-600">
          <FileText className="w-4 h-4" />
          <span className="text-sm font-medium">Generated Reports ({reports.length})</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {reports.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No reports yet</p>
            <p className="text-xs mt-1">Export a report to see it here</p>
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((report) => (
              <div
                key={report.id}
                className="p-4 rounded-lg border border-slate-200 hover:border-slate-300 bg-white transition-all group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <div className="w-8 h-8 bg-emerald-50 rounded-lg flex items-center justify-center flex-shrink-0">
                      <FileText className="w-4 h-4 text-emerald-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-slate-900 truncate">{report.datasetName}</h3>
                      <div className="flex items-center gap-2 text-xs text-slate-600 mt-1">
                        <Calendar className="w-3 h-3" />
                        {report.timestamp}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => onDownloadReport(report)}
                      className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded transition-colors"
                      title="Download Report"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => onDeleteReport(report.id)}
                      className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Delete Report"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <CheckCircle className="w-3 h-3 text-emerald-600" />
                  <span className="text-slate-600">Report ready to download</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
