import { useState } from 'react';
import { FileText, Table, Shield, Download, Copy, CheckCircle } from 'lucide-react';
import { TableSkeleton } from './LoadingSkeleton';

interface TableData {
  title?: string;
  name?: string;
  columns?: string[];
  rows?: any[][];
}

interface ResultsPanelProps {
  summary: string;
  tableData: TableData[] | any[];
  auditLog: string[];
  onExportReport?: () => void;
  onCopySummary?: () => void;
  hasContent?: boolean;
  isLoading?: boolean;
}

function renderMarkdown(markdown: string) {
  const lines = markdown.split('\n');
  const elements: JSX.Element[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith('## ')) {
      elements.push(
        <h2 key={i} className="text-xl font-bold text-slate-900 mt-6 mb-3 first:mt-0">
          {line.replace('## ', '')}
        </h2>
      );
    } else if (line.startsWith('# ')) {
      elements.push(
        <h1 key={i} className="text-2xl font-bold text-slate-900 mt-6 mb-4 first:mt-0">
          {line.replace('# ', '')}
        </h1>
      );
    } else if (line.startsWith('- ')) {
      elements.push(
        <li key={i} className="ml-4 text-slate-700 leading-relaxed">
          {renderInlineMarkdown(line.replace('- ', ''))}
        </li>
      );
    } else if (line.trim()) {
      elements.push(
        <p key={i} className="text-slate-700 leading-relaxed mb-3">
          {renderInlineMarkdown(line)}
        </p>
      );
    }
  }

  return elements;
}

function renderInlineMarkdown(text: string) {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={idx} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

function isNewTableFormat(data: any): data is TableData {
  return data && typeof data === 'object' && 'columns' in data && 'rows' in data;
}

export default function ResultsPanel({
  summary,
  tableData,
  auditLog,
  onExportReport,
  onCopySummary,
  hasContent = false,
  isLoading = false
}: ResultsPanelProps) {
  const [activeTab, setActiveTab] = useState<'summary' | 'tables' | 'audit'>('summary');
  const [copied, setCopied] = useState(false);

  const tabs = [
    { id: 'summary' as const, label: 'Summary', icon: FileText },
    { id: 'tables' as const, label: 'Tables', icon: Table },
    { id: 'audit' as const, label: 'Audit', icon: Shield },
  ];

  const handleCopySummary = () => {
    if (onCopySummary) {
      onCopySummary();
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const renderNewFormatTable = (table: TableData, index: number) => {
    if (!table.columns || !table.rows) return null;

    const tableTitle = table.title || table.name;

    const truncateCell = (value: any, maxLength: number = 100) => {
      const str = String(value ?? '');
      if (str.length <= maxLength) return str;
      return str.slice(0, maxLength) + '...';
    };

    return (
      <div key={index} className="mb-6 last:mb-0">
        {tableTitle && (
          <h3 className="text-lg font-semibold text-slate-900 mb-3 px-1">{tableTitle}</h3>
        )}
        <div className="overflow-auto rounded-lg border border-slate-200 max-h-[500px]">
          <table className="w-full border-collapse">
            <thead className="sticky top-0 z-10">
              <tr className="bg-slate-50">
                {table.columns.map((col, idx) => (
                  <th
                    key={idx}
                    className="px-4 py-3 text-left text-sm font-semibold text-slate-900 border-b border-slate-200 whitespace-nowrap"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, rowIdx) => (
                <tr
                  key={rowIdx}
                  className="hover:bg-slate-50 transition-colors border-b border-slate-100 last:border-0"
                >
                  {row.map((cell, cellIdx) => {
                    const cellValue = cell ?? '';
                    const displayValue = truncateCell(cellValue);
                    const isTruncated = String(cellValue).length > 100;

                    return (
                      <td
                        key={cellIdx}
                        className="px-4 py-3 text-sm text-slate-700 max-w-xs"
                        title={isTruncated ? String(cellValue) : undefined}
                      >
                        {displayValue}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderOldFormatTable = (data: any[]) => {
    if (data.length === 0) return null;

    const truncateCell = (value: any, maxLength: number = 100) => {
      const str = String(value ?? '');
      if (str.length <= maxLength) return str;
      return str.slice(0, maxLength) + '...';
    };

    return (
      <div className="overflow-auto rounded-lg border border-slate-200 max-h-[500px]">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 z-10">
            <tr className="bg-slate-50">
              {Object.keys(data[0]).map((key) => (
                <th
                  key={key}
                  className="px-4 py-3 text-left text-sm font-semibold text-slate-900 border-b border-slate-200 whitespace-nowrap"
                >
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr
                key={idx}
                className="hover:bg-slate-50 transition-colors border-b border-slate-100 last:border-0"
              >
                {Object.values(row).map((value: any, cellIdx) => {
                  const cellValue = value ?? '';
                  const displayValue = truncateCell(cellValue);
                  const isTruncated = String(cellValue).length > 100;

                  return (
                    <td
                      key={cellIdx}
                      className="px-4 py-3 text-sm text-slate-700 max-w-xs"
                      title={isTruncated ? String(cellValue) : undefined}
                    >
                      {displayValue}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-white border-l border-slate-200">
      <div className="flex items-center justify-between border-b border-slate-200">
        <div className="flex">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors relative ${
                  activeTab === tab.id
                    ? 'text-emerald-600'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
                {activeTab === tab.id && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-600" />
                )}
              </button>
            );
          })}
        </div>

        {hasContent && (
          <div className="flex items-center gap-2 px-4">
            <button
              onClick={handleCopySummary}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
            >
              {copied ? (
                <>
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  <span className="text-emerald-600">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Copy Summary
                </>
              )}
            </button>
            <button
              onClick={onExportReport}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-emerald-500 text-white hover:bg-emerald-600 rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              Export Report
            </button>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'summary' && (
          <div>
            {isLoading ? (
              <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
                <div className="animate-pulse space-y-3">
                  <div className="h-6 bg-slate-200 rounded w-3/4"></div>
                  <div className="h-4 bg-slate-100 rounded w-full"></div>
                  <div className="h-4 bg-slate-100 rounded w-5/6"></div>
                  <div className="h-4 bg-slate-100 rounded w-4/6"></div>
                </div>
              </div>
            ) : summary ? (
              <div className="prose max-w-none">
                <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
                  {renderMarkdown(summary)}
                </div>
              </div>
            ) : (
              <div className="text-center py-16 px-4">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-slate-100 rounded-2xl mb-4">
                  <FileText className="w-8 h-8 text-slate-400" />
                </div>
                <h3 className="text-base font-semibold text-slate-900 mb-1">No summary yet</h3>
                <p className="text-sm text-slate-500">Ask a question to see analysis results here</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'tables' && (
          <div>
            {isLoading ? (
              <TableSkeleton />
            ) : tableData.length > 0 ? (
              <div>
                {Array.isArray(tableData) && tableData.length > 0 && isNewTableFormat(tableData[0])
                  ? tableData.map((table, idx) => renderNewFormatTable(table as TableData, idx))
                  : renderOldFormatTable(tableData)}
              </div>
            ) : (
              <div className="text-center py-16 px-4">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-slate-100 rounded-2xl mb-4">
                  <Table className="w-8 h-8 text-slate-400" />
                </div>
                <h3 className="text-base font-semibold text-slate-900 mb-1">No tables returned for this analysis</h3>
                <p className="text-sm text-slate-500">Ask a different question to see tabular results</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'audit' && (
          <div>
            {auditLog.length > 0 ? (
              <div className="space-y-2">
                {auditLog.map((entry, idx) => {
                  const isSQL = entry.includes('SQL:');
                  const isSuccess = entry.includes('✅') || entry.includes('✓');
                  const isPlanning = entry.includes('📝') || entry.includes('Planning:');
                  const isHeader = entry.includes(' - ') && !entry.startsWith('  ');
                  const isSubItem = entry.startsWith('  ');

                  return (
                    <div
                      key={idx}
                      className={`rounded-lg text-sm ${
                        isSQL
                          ? 'px-4 py-3 bg-blue-50 border border-blue-200 text-blue-900 font-mono'
                          : isSuccess
                          ? 'px-4 py-3 bg-emerald-50 border border-emerald-200 text-emerald-900 font-medium'
                          : isPlanning
                          ? 'px-4 py-3 bg-amber-50 border border-amber-200 text-amber-900'
                          : isSubItem
                          ? 'px-4 py-2 ml-4 bg-slate-50 border border-slate-200 text-slate-700 font-mono'
                          : 'px-4 py-3 bg-slate-50 border border-slate-200 text-slate-700'
                      }`}
                    >
                      {entry}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-16 px-4">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-slate-100 rounded-2xl mb-4">
                  <Shield className="w-8 h-8 text-slate-400" />
                </div>
                <h3 className="text-base font-semibold text-slate-900 mb-1">No audit logs yet</h3>
                <p className="text-sm text-slate-500">Data operations will be logged here</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
