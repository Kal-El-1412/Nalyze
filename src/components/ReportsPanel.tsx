import { FileText, Calendar, CheckCircle, ArrowLeft, Eye, RefreshCw, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { ReportSummary, Report, connectorApi } from '../services/connectorApi';

interface ReportsPanelProps {
  reports: ReportSummary[];
  datasets: Array<{ id: string; name: string }>;
  onRefresh?: () => void;
}

export default function ReportsPanel({ reports, datasets, onRefresh }: ReportsPanelProps) {
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [isLoadingReport, setIsLoadingReport] = useState(false);

  const handleSelectReport = async (summary: ReportSummary) => {
    setIsLoadingReport(true);
    try {
      const fullReport = await connectorApi.getReport(summary.id);
      if (fullReport) {
        setSelectedReport(fullReport);
      }
    } catch (error) {
      console.error('Failed to load report:', error);
    } finally {
      setIsLoadingReport(false);
    }
  };

  const getDatasetName = (datasetId: string) => {
    const dataset = datasets.find(d => d.id === datasetId);
    return dataset?.name || datasetId;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return 'Unknown date';
    }
    return date.toLocaleString();
  };

  if (selectedReport) {
    return (
      <div className="h-full flex flex-col bg-white dark:bg-slate-950">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800">
          <button
            onClick={() => setSelectedReport(null)}
            className="flex items-center gap-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100 transition-colors mb-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back to Reports</span>
          </button>
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
            <FileText className="w-4 h-4" />
            <span className="text-sm font-medium">{getDatasetName(selectedReport.dataset_id)}</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mt-1">
            <Calendar className="w-3 h-3" />
            {formatDate(selectedReport.created_at)}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {selectedReport.question && (
              <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <h3 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">Question</h3>
                <p className="text-sm text-blue-800 dark:text-blue-200">{selectedReport.question}</p>
              </div>
            )}

            {(selectedReport.analysis_type || selectedReport.time_period) && (
              <div className="flex gap-4">
                {selectedReport.analysis_type && (
                  <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-3 flex-1">
                    <div className="text-xs text-slate-600 dark:text-slate-300 mb-1">Analysis Type</div>
                    <div className="text-sm font-medium text-slate-900 dark:text-slate-100">{selectedReport.analysis_type}</div>
                  </div>
                )}
                {selectedReport.time_period && (
                  <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-3 flex-1">
                    <div className="text-xs text-slate-600 dark:text-slate-300 mb-1">Time Period</div>
                    <div className="text-sm font-medium text-slate-900 dark:text-slate-100">{selectedReport.time_period}</div>
                  </div>
                )}
              </div>
            )}

            {selectedReport.summary_markdown && (
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-4">
                <h3 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">Summary</h3>
                <div className="text-sm text-slate-700 dark:text-slate-200 whitespace-pre-wrap">{selectedReport.summary_markdown}</div>
              </div>
            )}

            {selectedReport.tables && selectedReport.tables.length > 0 && (
              <div className="space-y-4">
                {selectedReport.tables.map((table, idx) => (
                  <div key={idx} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                    <div className="bg-slate-50 dark:bg-slate-800 px-4 py-2 border-b border-slate-200 dark:border-slate-700">
                      <h3 className="text-sm font-medium text-slate-900 dark:text-slate-100">{table.name}</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
                          <tr>
                            {table.columns.map((col, colIdx) => (
                              <th key={colIdx} className="px-4 py-2 text-left font-medium text-slate-700 dark:text-slate-200">
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                          {table.rows.map((row, rowIdx) => (
                            <tr key={rowIdx} className="hover:bg-slate-50 dark:hover:bg-slate-800">
                              {row.map((cell, cellIdx) => (
                                <td key={cellIdx} className="px-4 py-2 text-slate-700 dark:text-slate-200">
                                  {cell}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {selectedReport.audit_log && selectedReport.audit_log.length > 0 && (
              <div className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-4">
                <h3 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">Privacy Audit</h3>
                <ul className="space-y-1">
                  {selectedReport.audit_log.map((log, idx) => (
                    <li key={idx} className="text-xs text-slate-600 dark:text-slate-300 flex items-center gap-2">
                      <CheckCircle className="w-3 h-3 text-emerald-600 flex-shrink-0" />
                      <span>{log}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-slate-900">
      <div className="p-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
            <FileText className="w-4 h-4" />
            <span className="text-sm font-medium">Saved Reports ({reports.length})</span>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-1.5 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors"
              title="Refresh reports"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {isLoadingReport ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
          </div>
        ) : reports.length === 0 ? (
          <div className="text-center py-12 text-slate-500 dark:text-slate-400">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No reports yet</p>
            <p className="text-xs mt-1">Complete an analysis to create a report</p>
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((report) => (
              <button
                key={report.id}
                onClick={() => handleSelectReport(report)}
                className="w-full p-4 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-emerald-300 dark:hover:border-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950 bg-white dark:bg-slate-800 transition-all group text-left"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <div className="w-8 h-8 bg-emerald-50 dark:bg-emerald-950 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900">
                      <FileText className="w-4 h-4 text-emerald-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-slate-900 dark:text-slate-100 truncate">{report.datasetName}</h3>
                      <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300 mt-1">
                        <Calendar className="w-3 h-3" />
                        {formatDate(report.createdAt)}
                      </div>
                    </div>
                  </div>
                  <Eye className="w-4 h-4 text-slate-400 dark:text-slate-500 group-hover:text-emerald-600 flex-shrink-0 ml-2" />
                </div>

                <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-2">{report.title}</p>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
