interface Message {
  type: string;
  content: string;
  timestamp: string;
  pinned?: boolean;
  clarificationData?: any;
  queriesData?: any;
}

interface TableData {
  name: string;
  columns: string[];
  rows: any[][];
}

interface ReportData {
  datasetId?: string;
  datasetName: string;
  timestamp: string;
  conversationId: string;
  messages: Message[];
  summary: string;
  tableData: any[];
  auditLog: string[];
  tables?: TableData[];
}

const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  if (isNaN(date.getTime())) {
    return 'Unknown time';
  }
  return date.toLocaleString();
};

export function generateHTMLReport(data: ReportData): string {
  const { datasetName, timestamp, messages, summary, tableData, auditLog } = data;

  const messagesHTML = messages
    .filter(m => m.type === 'user' || m.type === 'assistant')
    .map(
      (m) => `
    <div class="message ${m.type}">
      <div class="message-header">
        <span class="message-type">${m.type === 'user' ? 'User' : 'Assistant'}</span>
        <span class="message-time">${formatTimestamp(m.timestamp)}</span>
      </div>
      <div class="message-content">${escapeHtml(m.content)}</div>
    </div>
  `
    )
    .join('');

  const tableHTML =
    tableData.length > 0
      ? `
    <div class="section">
      <h2>Query Results</h2>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              ${Object.keys(tableData[0])
                .map((key) => `<th>${escapeHtml(key)}</th>`)
                .join('')}
            </tr>
          </thead>
          <tbody>
            ${tableData
              .map(
                (row) => `
              <tr>
                ${Object.values(row)
                  .map((val) => `<td>${escapeHtml(String(val))}</td>`)
                  .join('')}
              </tr>
            `
              )
              .join('')}
          </tbody>
        </table>
      </div>
    </div>
  `
      : '';

  const auditLogHTML =
    auditLog.length > 0
      ? `
    <div class="section">
      <h2>Audit Log</h2>
      <div class="audit-log">
        ${auditLog.map((log) => `<div class="audit-entry">${escapeHtml(log)}</div>`).join('')}
      </div>
    </div>
  `
      : '';

  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Data Analysis Report - ${escapeHtml(datasetName)}</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      line-height: 1.6;
      color: #1e293b;
      background: #f8fafc;
      padding: 20px;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      overflow: hidden;
    }

    .header {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: white;
      padding: 40px;
      text-align: center;
    }

    .header h1 {
      font-size: 32px;
      font-weight: 700;
      margin-bottom: 8px;
    }

    .header .meta {
      font-size: 14px;
      opacity: 0.9;
    }

    .content {
      padding: 40px;
    }

    .section {
      margin-bottom: 40px;
    }

    .section h2 {
      font-size: 24px;
      font-weight: 600;
      color: #0f172a;
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 2px solid #e2e8f0;
    }

    .summary {
      background: #f1f5f9;
      padding: 24px;
      border-radius: 8px;
      border-left: 4px solid #10b981;
      white-space: pre-wrap;
    }

    .conversation {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .message {
      padding: 16px;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
    }

    .message.user {
      background: #f0fdf4;
      border-left: 4px solid #10b981;
    }

    .message.assistant {
      background: #f8fafc;
      border-left: 4px solid #3b82f6;
    }

    .message-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 12px;
    }

    .message-type {
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .message.user .message-type {
      color: #10b981;
    }

    .message.assistant .message-type {
      color: #3b82f6;
    }

    .message-time {
      color: #64748b;
    }

    .message-content {
      color: #334155;
      white-space: pre-wrap;
      word-wrap: break-word;
    }

    .table-container {
      overflow-x: auto;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }

    th {
      background: #f8fafc;
      color: #475569;
      font-weight: 600;
      text-align: left;
      padding: 12px 16px;
      border-bottom: 2px solid #e2e8f0;
      white-space: nowrap;
    }

    td {
      padding: 12px 16px;
      border-bottom: 1px solid #f1f5f9;
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:hover {
      background: #f8fafc;
    }

    .audit-log {
      background: #fefce8;
      border: 1px solid #fde047;
      border-radius: 8px;
      padding: 16px;
      font-size: 13px;
      font-family: 'Courier New', monospace;
    }

    .audit-entry {
      padding: 4px 0;
      color: #713f12;
    }

    .footer {
      background: #f8fafc;
      padding: 24px 40px;
      text-align: center;
      color: #64748b;
      font-size: 13px;
      border-top: 1px solid #e2e8f0;
    }

    @media print {
      body {
        padding: 0;
        background: white;
      }

      .container {
        box-shadow: none;
      }
    }

    @media (max-width: 768px) {
      body {
        padding: 10px;
      }

      .header, .content {
        padding: 20px;
      }

      .header h1 {
        font-size: 24px;
      }

      table {
        font-size: 12px;
      }

      th, td {
        padding: 8px 12px;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Data Analysis Report</h1>
      <div class="meta">
        <div>Dataset: ${escapeHtml(datasetName)}</div>
        <div>Generated: ${formatTimestamp(timestamp)}</div>
      </div>
    </div>

    <div class="content">
      ${
        summary
          ? `
      <div class="section">
        <h2>Summary</h2>
        <div class="summary">${escapeHtml(summary)}</div>
      </div>
      `
          : ''
      }

      <div class="section">
        <h2>Conversation</h2>
        <div class="conversation">
          ${messagesHTML}
        </div>
      </div>

      ${tableHTML}
      ${auditLogHTML}
    </div>

    <div class="footer">
      <p>Generated by DataFlex Analytics Platform</p>
      <p>Report ID: ${escapeHtml(data.conversationId)}</p>
    </div>
  </div>
</body>
</html>
  `.trim();
}

export function downloadHTMLReport(html: string, filename: string): void {
  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function copyToClipboard(text: string): Promise<void> {
  return navigator.clipboard.writeText(text);
}

export interface JSONReportBundle {
  datasetId?: string;
  datasetName: string;
  timestamp: string;
  conversationId: string;
  conversation: {
    messages: Message[];
  };
  finalAnswers: {
    summary: string;
    tables: TableData[];
  };
  audit: {
    sharedWithAI: string[];
  };
  metadata: {
    exportedAt: string;
    version: string;
  };
}

export function generateJSONBundle(data: ReportData): string {
  const bundle: JSONReportBundle = {
    datasetId: data.datasetId,
    datasetName: data.datasetName,
    timestamp: data.timestamp,
    conversationId: data.conversationId,
    conversation: {
      messages: data.messages.map(m => ({
        type: m.type,
        content: m.content,
        timestamp: m.timestamp,
        pinned: m.pinned,
      })),
    },
    finalAnswers: {
      summary: data.summary,
      tables: data.tables || [],
    },
    audit: {
      sharedWithAI: data.auditLog,
    },
    metadata: {
      exportedAt: new Date().toISOString(),
      version: '1.0.0',
    },
  };

  return JSON.stringify(bundle, null, 2);
}

export function downloadJSONBundle(json: string, filename: string): void {
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function downloadAsZIP(
  htmlContent: string,
  jsonContent: string,
  datasetName: string
): Promise<void> {
  try {
    const JSZip = (await import('jszip')).default;
    const zip = new JSZip();

    zip.file('report.html', htmlContent);
    zip.file('report.json', jsonContent);

    const blob = await zip.generateAsync({ type: 'blob' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${datasetName.replace(/\s+/g, '-')}-${Date.now()}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('ZIP creation failed:', error);
    throw new Error('ZIP export is not available. Please export HTML and JSON separately.');
  }
}

export function extractSummaryText(data: ReportData): string {
  return data.summary || 'No summary available';
}

function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
