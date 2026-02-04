import { FileText, Calendar, CheckCircle, ArrowLeft, Eye } from 'lucide-react';
import { useState } from 'react';
import { Report } from '../services/connectorApi';

interface ReportsPanelProps {
  reports: Report[];
  datasets: Array<{ id: string; name: string }>;
}

export default function ReportsPanel({ reports, datasets }: ReportsPanelProps) {
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  const getDatasetName = (datasetId: string) => {
    const dataset = datasets.find(d => d.id === datasetId);
    return dataset?.name || datasetId;
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch {
      return dateString;
    }
  };

  if (selectedReport) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-4 border-b border-slate-200">
          <button
            onClick={() => setSelectedReport(null)}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors mb-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back to Reports</span>
          </button>
          <div className="flex items-center gap-2 text-slate-600">
            <FileText className="w-4 h-4" />
            <span className="text-sm font-medium">{getDatasetName(selectedReport.dataset_id)}</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mt-1">
            <Calendar className="w-3 h-3" />
            {formatDate(selectedReport.created_at)}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {selectedReport.question && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-blue-900 mb-1">Question</h3>
                <p className="text-sm text-blue-800">{selectedReport.question}</p>
              </div>
            )}

            {(selectedReport.analysis_type || selectedReport.time_period) && (
              <div className="flex gap-4">
                {selectedReport.analysis_type && (
                  <div className="bg-slate-50 rounded-lg p-3 flex-1">
                    <div className="text-xs text-slate-600 mb-1">Analysis Type</div>
                    <div className="text-sm font-medium text-slate-900">{selectedReport.analysis_type}</div>
                  </div>
                )}
                {selectedReport.time_period && (
                  <div className="bg-slate-50 rounded-lg p-3 flex-1">
                    <div className="text-xs text-slate-600 mb-1">Time Period</div>
                    <div className="text-sm font-medium text-slate-900">{selectedReport.time_period}</div>
                  </div>
                )}
              </div>
            )}

            {selectedReport.summary_markdown && (
              <div className="bg-white border border-slate-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-slate-900 mb-2">Summary</h3>
                <div className="text-sm text-slate-700 whitespace-pre-wrap">{selectedReport.summary_markdown}</div>
              </div>
            )}

            {selectedReport.tables && selectedReport.tables.length > 0 && (
              <div className="space-y-4">
                {selectedReport.tables.map((table, idx) => (
                  <div key={idx} className="bg-white border border-slate-200 rounded-lg overflow-hidden">
                    <div className="bg-slate-50 px-4 py-2 border-b border-slate-200">
                      <h3 className="text-sm font-medium text-slate-900">{table.name}</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-slate-50 border-b border-slate-200">
                          <tr>
                            {table.columns.map((col, colIdx) => (
                              <th key={colIdx} className="px-4 py-2 text-left font-medium text-slate-700">
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {table.rows.map((row, rowIdx) => (
                            <tr key={rowIdx} className="hover:bg-slate-50">
                              {row.map((cell, cellIdx) => (
                                <td key={cellIdx} className="px-4 py-2 text-slate-700">
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
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-slate-900 mb-2">Privacy Audit</h3>
                <ul className="space-y-1">
                  {selectedReport.audit_log.map((log, idx) => (
                    <li key={idx} className="text-xs text-slate-600 flex items-center gap-2">
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
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-slate-200">
        <div className="flex items-center gap-2 text-slate-600">
          <FileText className="w-4 h-4" />
          <span className="text-sm font-medium">Saved Reports ({reports.length})</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {reports.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No reports yet</p>
            <p className="text-xs mt-1">Complete an analysis to create a report</p>
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((report) => (
              <button
                key={report.id}
                onClick={() => setSelectedReport(report)}
                className="w-full p-4 rounded-lg border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50 bg-white transition-all group text-left"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <div className="w-8 h-8 bg-emerald-50 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-emerald-100">
                      <FileText className="w-4 h-4 text-emerald-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-slate-900 truncate">{getDatasetName(report.dataset_id)}</h3>
                      <div className="flex items-center gap-2 text-xs text-slate-600 mt-1">
                        <Calendar className="w-3 h-3" />
                        {formatDate(report.created_at)}
                      </div>
                    </div>
                  </div>
                  <Eye className="w-4 h-4 text-slate-400 group-hover:text-emerald-600 flex-shrink-0 ml-2" />
                </div>

                {report.question && (
                  <p className="text-xs text-slate-600 line-clamp-2 mb-2">{report.question}</p>
                )}

                <div className="flex items-center gap-2 text-xs">
                  {report.analysis_type && (
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded">
                      {report.analysis_type}
                    </span>
                  )}
                  {report.time_period && (
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded">
                      {report.time_period}
                    </span>
                  )}
                  {report.privacy_mode && (
                    <CheckCircle className="w-3 h-3 text-emerald-600" title="Privacy Mode" />
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
