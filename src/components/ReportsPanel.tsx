import { FileText, Download, Trash2, Calendar, CheckCircle, FileJson, FileArchive, Copy, ChevronDown } from 'lucide-react';
import { useState, useEffect } from 'react';

interface Report {
  id: string;
  datasetId?: string;
  datasetName: string;
  timestamp: string;
  conversationId: string;
  htmlContent: string;
  jsonContent?: string;
  summary?: string;
  messages?: any[];
  tables?: any[];
  auditLog?: string[];
}

interface ReportsPanelProps {
  reports: Report[];
  onDownloadReport: (report: Report) => void;
  onDownloadJSON: (report: Report) => void;
  onDownloadZIP: (report: Report) => void;
  onCopySummary: (report: Report) => void;
  onDeleteReport: (id: string) => void;
}

export default function ReportsPanel({
  reports,
  onDownloadReport,
  onDownloadJSON,
  onDownloadZIP,
  onCopySummary,
  onDeleteReport,
}: ReportsPanelProps) {
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.relative')) {
        setOpenMenuId(null);
      }
    };

    if (openMenuId) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [openMenuId]);

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
                  <div className="flex items-center gap-1">
                    <div className="relative">
                      <button
                        onClick={() => setOpenMenuId(openMenuId === report.id ? null : report.id)}
                        className="p-1.5 text-slate-600 hover:bg-slate-100 rounded transition-colors flex items-center gap-1"
                        title="Export Options"
                      >
                        <Download className="w-4 h-4" />
                        <ChevronDown className="w-3 h-3" />
                      </button>
                      {openMenuId === report.id && (
                        <div className="absolute right-0 mt-1 w-56 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-10">
                          <button
                            onClick={() => {
                              onDownloadReport(report);
                              setOpenMenuId(null);
                            }}
                            className="w-full px-4 py-2 text-left text-sm hover:bg-slate-50 flex items-center gap-2"
                          >
                            <FileText className="w-4 h-4 text-emerald-600" />
                            <span>Download HTML</span>
                          </button>
                          {report.jsonContent && (
                            <>
                              <button
                                onClick={() => {
                                  onDownloadJSON(report);
                                  setOpenMenuId(null);
                                }}
                                className="w-full px-4 py-2 text-left text-sm hover:bg-slate-50 flex items-center gap-2"
                              >
                                <FileJson className="w-4 h-4 text-blue-600" />
                                <span>Download JSON</span>
                              </button>
                              <button
                                onClick={() => {
                                  onDownloadZIP(report);
                                  setOpenMenuId(null);
                                }}
                                className="w-full px-4 py-2 text-left text-sm hover:bg-slate-50 flex items-center gap-2"
                              >
                                <FileArchive className="w-4 h-4 text-purple-600" />
                                <span>Download ZIP Bundle</span>
                              </button>
                            </>
                          )}
                          {report.summary && (
                            <>
                              <div className="border-t border-slate-200 my-1"></div>
                              <button
                                onClick={() => {
                                  onCopySummary(report);
                                  setOpenMenuId(null);
                                }}
                                className="w-full px-4 py-2 text-left text-sm hover:bg-slate-50 flex items-center gap-2"
                              >
                                <Copy className="w-4 h-4 text-slate-600" />
                                <span>Copy Summary</span>
                              </button>
                            </>
                          )}
                        </div>
                      )}
                    </div>
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
                  <span className="text-slate-600">Report ready</span>
                  {report.jsonContent && (
                    <span className="text-slate-400">• HTML + JSON available</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
