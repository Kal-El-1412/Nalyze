import { diagnostics } from './diagnostics';

export interface HealthResponse {
  status: string;
  version: string;
}

export interface Dataset {
  datasetId: string;
  name: string;
  createdAt: string;
  lastIngestedAt?: string;
  status: string;
}

export interface RegisterDatasetRequest {
  name: string;
  sourceType: 'local_file';
  filePath: string;
}

export interface RegisterDatasetResponse {
  datasetId: string;
}

export interface IngestResponse {
  jobId: string;
}

export interface Job {
  jobId: string;
  type: string;
  datasetId: string;
  status: 'queued' | 'running' | 'done' | 'error';
  stage?: 'queued' | 'scanning_headers' | 'ingesting_rows' | 'building_catalog' | 'done' | 'error';
  startedAt: string;
  finishedAt?: string;
  updatedAt?: string;
  error?: string;
}

export interface QueryResult {
  name: string;
  columns: string[];
  rows: any[][];
  rowCount: number;
}

export interface ChatRequest {
  datasetId: string;
  conversationId?: string;
  message?: string;
  intent?: string;
  value?: any;
  privacyMode?: boolean;
  safeMode?: boolean;
  aiAssist?: boolean;
  resultsContext?: {
    results: QueryResult[];
  };
  defaultsContext?: {
    dateColumn?: string;
    metricColumn?: string;
    categoryColumn?: string;
    segmentColumn?: string;
    stageColumn?: string;
    [key: string]: string | undefined;
  };
}

export interface ExecuteQueriesRequest {
  datasetId: string;
  queries: Array<{
    name: string;
    sql: string;
  }>;
}

export interface ExecuteQueriesResponse {
  results: QueryResult[];
}

export interface ClarificationResponse {
  type: 'needs_clarification';
  question: string;
  choices: string[];
  intent?: string;
  allowFreeText: boolean;
}

export interface RunQueriesResponse {
  type: 'run_queries';
  queries: Array<{
    name: string;
    sql: string;
  }>;
  explanation?: string;
  audit?: {
    sharedWithAI: string[];
  };
}

export interface ExecutedQuery {
  name: string;
  sql: string;
  rowCount: number;
}

export interface AuditMetadata {
  datasetId: string;
  datasetName: string;
  analysisType: string;
  timePeriod: string;
  aiAssist: boolean;
  safeMode: boolean;
  privacyMode: boolean;
  executedQueries: ExecutedQuery[];
  generatedAt: string;
  reportId?: string;
}

export interface FinalAnswerResponse {
  type: 'final_answer';
  summaryMarkdown: string;
  tables: Array<{
    name: string;
    columns: string[];
    rows: any[][];
  }>;
  audit: AuditMetadata;
}

export interface IntentAcknowledgmentResponse {
  type: 'intent_acknowledged';
  intent: string;
  value: any;
  state: {
    conversation_id: string;
    context: Record<string, any>;
  };
}

export type ChatResponse = ClarificationResponse | RunQueriesResponse | FinalAnswerResponse | IntentAcknowledgmentResponse;

export interface DatasetColumn {
  name: string;
  type: string;
}

export interface ColumnStats {
  min?: any;
  max?: any;
  avg?: number;
  nullPct: number;
  approxDistinct?: number;
}

export interface PIIColumnInfo {
  name: string;
  type: 'email' | 'phone' | 'name';
  confidence: number;
}

export interface DatasetCatalog {
  table: string;
  rowCount: number;
  columns: DatasetColumn[];
  basicStats: Record<string, ColumnStats>;
  detectedDateColumns: string[];
  detectedNumericColumns: string[];
  piiColumns: PIIColumnInfo[];
}

export interface DatasetTable {
  name: string;
  rowCount: number;
  columns: DatasetColumn[];
}

export interface DatasetCatalogResponse {
  tables: DatasetTable[];
}

export interface ReportSummary {
  id: string;
  title: string;
  datasetId: string;
  datasetName: string;
  createdAt: string;
}

export interface Report {
  id: string;
  dataset_id: string;
  dataset_name?: string;
  conversation_id: string;
  question: string;
  analysis_type: string;
  time_period: string;
  summary_markdown: string;
  tables: Array<{
    name: string;
    columns: string[];
    rows: any[][];
  }>;
  audit_log: string[];
  created_at: string;
  privacy_mode: boolean;
  safe_mode: boolean;
}

export interface ApiError {
  status: number;
  statusText: string;
  url: string;
  method: string;
  message: string;
  raw?: string;
}

export type ApiResult<T> =
  | { success: true; data: T }
  | { success: false; error: ApiError };

class ConnectorAPI {
  private baseUrl: string;
  private isAvailable: boolean = false;

  constructor() {
    this.baseUrl = this.getBaseUrl();
  }

  private getBaseUrl(): string {
    const saved = localStorage.getItem('connectorBaseUrl');
    return saved || 'http://localhost:7337';
  }

  private getPrivacyMode(): boolean {
    const saved = localStorage.getItem('privacyMode');
    if (saved !== null) {
      return saved === 'true';
    }
    return true;
  }

  private getSafeMode(): boolean {
    const saved = localStorage.getItem('safeMode');
    if (saved !== null) {
      return saved === 'true';
    }
    return false;
  }

  private getAiAssist(): boolean {
    const saved = localStorage.getItem('aiAssist');
    return saved === 'true';
  }

  private getPrivacyHeaders(): Record<string, string> {
    const privacyMode = this.getPrivacyMode();
    const safeMode = this.getSafeMode();
    const aiAssist = this.getAiAssist();
    return {
      'X-Privacy-Mode': privacyMode ? 'on' : 'off',
      'X-Safe-Mode': safeMode ? 'on' : 'off',
      'X-AI-Assist': aiAssist ? 'on' : 'off',
    };
  }

  setBaseUrl(url: string) {
    this.baseUrl = url;
    localStorage.setItem('connectorBaseUrl', url);
  }

  getConnectorUrl(): string {
    return this.baseUrl;
  }

  private async parseError(
    response: Response,
    method: string,
    url: string
  ): Promise<ApiError> {
    let message = response.statusText;
    let raw: string | undefined;

    try {
      const text = await response.text();
      raw = text;

      try {
        const json = JSON.parse(text);
        message = json.detail || json.error || json.message || message;
      } catch {
        message = text || message;
      }
    } catch {
      // If reading response fails, use statusText
    }

    return {
      status: response.status,
      statusText: response.statusText,
      url,
      method,
      message,
      raw,
    };
  }

  private async handleApiError(
    error: unknown,
    method: string,
    url: string
  ): Promise<ApiError> {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return {
        status: 0,
        statusText: 'Network Error',
        url,
        method,
        message: 'Cannot connect to connector. Is it running?',
      };
    }

    return {
      status: 0,
      statusText: 'Unknown Error',
      url,
      method,
      message: error instanceof Error ? error.message : String(error),
    };
  }

  async testAiConnection(): Promise<{
    status: 'connected' | 'error' | 'disabled';
    message: string;
    details: string;
  } | null> {
    try {
      const response = await fetch(`${this.baseUrl}/test-ai-connection`, {
        method: 'GET',
        headers: {
          ...this.getPrivacyHeaders(),
        },
        signal: AbortSignal.timeout(10000),
      });

      if (!response.ok) {
        return null;
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error testing AI connection:', error);
      return null;
    }
  }

  async checkHealth(retries: number = 2): Promise<HealthResponse | null> {
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(`${this.baseUrl}/health`, {
          method: 'GET',
          headers: {
            ...this.getPrivacyHeaders(),
          },
          signal: AbortSignal.timeout(5000),
        });

        if (!response.ok) {
          if (attempt < retries) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            continue;
          }
          this.isAvailable = false;
          return null;
        }

        const data = await response.json();
        this.isAvailable = true;
        return data;
      } catch (error) {
        if (attempt < retries) {
          await new Promise(resolve => setTimeout(resolve, 1000));
          continue;
        }
        this.isAvailable = false;
        return null;
      }
    }
    this.isAvailable = false;
    return null;
  }

  async registerDataset(request: RegisterDatasetRequest): Promise<ApiResult<RegisterDatasetResponse>> {
    const url = `${this.baseUrl}/datasets/register`;
    const method = 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...this.getPrivacyHeaders(),
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await this.parseError(response, method, url);
        return { success: false, error };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      const apiError = await this.handleApiError(error, method, url);
      return { success: false, error: apiError };
    }
  }

  async uploadDataset(file: File, name: string): Promise<ApiResult<RegisterDatasetResponse>> {
    const url = `${this.baseUrl}/datasets/upload`;
    const method = 'POST';

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', name);

      const response = await fetch(url, {
        method,
        headers: {
          ...this.getPrivacyHeaders(),
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await this.parseError(response, method, url);
        return { success: false, error };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      const apiError = await this.handleApiError(error, method, url);
      return { success: false, error: apiError };
    }
  }

  async getDatasets(): Promise<Dataset[]> {
    try {
      const response = await fetch(`${this.baseUrl}/datasets`, {
        method: 'GET',
        headers: {
          ...this.getPrivacyHeaders(),
        },
      });

      if (!response.ok) {
        return [];
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching datasets:', error);
      return [];
    }
  }

  async ingestDataset(datasetId: string): Promise<ApiResult<IngestResponse>> {
    const url = `${this.baseUrl}/datasets/${datasetId}/ingest`;
    const method = 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: {
          ...this.getPrivacyHeaders(),
        },
      });

      if (!response.ok) {
        const error = await this.parseError(response, method, url);
        return { success: false, error };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      const apiError = await this.handleApiError(error, method, url);
      return { success: false, error: apiError };
    }
  }

  async getJobs(): Promise<Job[]> {
    try {
      const response = await fetch(`${this.baseUrl}/jobs`, {
        method: 'GET',
        headers: {
          ...this.getPrivacyHeaders(),
        },
      });

      if (!response.ok) {
        return [];
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching jobs:', error);
      return [];
    }
  }

  async getReports(datasetId?: string): Promise<ReportSummary[]> {
    try {
      const url = datasetId
        ? `${this.baseUrl}/reports?dataset_id=${datasetId}`
        : `${this.baseUrl}/reports`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          ...this.getPrivacyHeaders(),
        },
      });

      if (!response.ok) {
        return [];
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching reports:', error);
      return [];
    }
  }

  async getReport(reportId: string): Promise<Report | null> {
    try {
      const response = await fetch(`${this.baseUrl}/reports/${reportId}`, {
        method: 'GET',
        headers: {
          ...this.getPrivacyHeaders(),
        },
      });

      if (!response.ok) {
        return null;
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching report:', error);
      return null;
    }
  }

  async sendChatMessage(request: ChatRequest): Promise<ApiResult<ChatResponse>> {
    const url = `${this.baseUrl}/chat`;
    const method = 'POST';

    try {
      const privacyMode = request.privacyMode !== undefined ? request.privacyMode : this.getPrivacyMode();
      const safeMode = request.safeMode !== undefined ? request.safeMode : this.getSafeMode();
      const aiAssist = request.aiAssist !== undefined ? request.aiAssist : this.getAiAssist();

      diagnostics.info(
        'Chat API',
        `Sending request to ${url}`,
        `privacyMode=${privacyMode}, safeMode=${safeMode}, aiAssist=${aiAssist}\nrequest.aiAssist=${request.aiAssist}, localStorage=${this.getAiAssist()}`
      );

      // Normalize the request to match backend contract
      let normalizedPayload: any;

      if (request.intent !== undefined) {
        // Intent-based request: only include intent/value fields
        normalizedPayload = {
          datasetId: request.datasetId,
          conversationId: request.conversationId,
          intent: request.intent,
          value: request.value,
          privacyMode,
          safeMode,
          aiAssist,
          resultsContext: request.resultsContext,
        };
      } else if (request.message !== undefined) {
        // Message-based request: only include message field
        normalizedPayload = {
          datasetId: request.datasetId,
          conversationId: request.conversationId,
          message: request.message,
          privacyMode,
          safeMode,
          aiAssist,
          resultsContext: request.resultsContext,
          defaultsContext: request.defaultsContext,
        };
      } else {
        // Neither intent nor message present - throw error
        const errorMsg = 'Invalid chat request: must provide either "message" or "intent" field';
        diagnostics.error('Chat API', errorMsg, JSON.stringify(request, null, 2));
        throw new Error(errorMsg);
      }

      diagnostics.info('Chat API', 'Sending fetch request...', JSON.stringify(normalizedPayload, null, 2));

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...this.getPrivacyHeaders(),
        },
        body: JSON.stringify(normalizedPayload),
      });

      diagnostics.info('Chat API', `Received response: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const error = await this.parseError(response, method, url);

        // Log 422 errors to diagnostics with full response body
        if (response.status === 422) {
          diagnostics.error(
            'Chat API Validation',
            `422 Unprocessable Entity: ${error.message}`,
            `Request: ${JSON.stringify(normalizedPayload, null, 2)}\n\nResponse: ${error.raw || 'No response body'}`
          );
        }

        return { success: false, error };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      const apiError = await this.handleApiError(error, method, url);
      return { success: false, error: apiError };
    }
  }

  async executeQueries(request: ExecuteQueriesRequest): Promise<ApiResult<ExecuteQueriesResponse>> {
    const url = `${this.baseUrl}/queries/execute`;
    const method = 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...this.getPrivacyHeaders(),
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await this.parseError(response, method, url);
        return { success: false, error };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      const apiError = await this.handleApiError(error, method, url);
      return { success: false, error: apiError };
    }
  }

  async getDatasetCatalog(datasetId: string): Promise<DatasetCatalog | null> {
    try {
      const response = await fetch(`${this.baseUrl}/datasets/${datasetId}/catalog`, {
        method: 'GET',
        headers: {
          ...this.getPrivacyHeaders(),
        },
      });

      if (!response.ok) {
        return null;
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching dataset catalog:', error);
      return null;
    }
  }

  isConnectorAvailable(): boolean {
    return this.isAvailable;
  }

  getMockDatasets(): Dataset[] {
    return [
      {
        datasetId: 'mock-1',
        name: 'Sample Sales Data',
        createdAt: new Date(Date.now() - 86400000).toISOString(),
        lastIngestedAt: new Date(Date.now() - 3600000).toISOString(),
        status: 'ready',
      },
    ];
  }

  getMockJobs(): Job[] {
    return [
      {
        jobId: 'mock-job-1',
        type: 'ingest',
        datasetId: 'mock-1',
        status: 'done',
        startedAt: new Date(Date.now() - 3600000).toISOString(),
        finishedAt: new Date(Date.now() - 3000000).toISOString(),
      },
    ];
  }

  getMockChatResponse(message: string, hasResultsContext: boolean = false): ChatResponse {
    if (hasResultsContext) {
      // Generate a dynamic summary based on the returned tables
      // (Demo mode: use simple heuristics so it feels responsive to the question)
      const summaryFromTables = (() => {
        // Try to detect row_count table result
        // Expected shape from /queries/execute: results[0].rows[0][0]
        // But in demo flow, we don't have direct access to those results here,
        // so keep this summary generic-but-grounded.
        // The UI tables pane will still show the row_count value.
        if (message.toLowerCase().includes('row') || message.toLowerCase().includes('count')) {
          return '## Row count\n\nI counted the total number of rows in your dataset. See the **Tables** tab for the exact value.';
        }
        if (message.toLowerCase().includes('categor')) {
          return '## Category analysis\n\nI computed category totals and ranked the largest groups. See the **Tables** tab for the breakdown.';
        }
        if (message.toLowerCase().includes('trend')) {
          return '## Trend analysis\n\nI aggregated values over time and calculated changes between periods. See the **Tables** tab for the time series.';
        }
        return '## Analysis complete\n\nI ran the requested queries and summarized the results. See the **Tables** tab for the outputs.';
      })();

      return {
        type: 'final_answer',
        summaryMarkdown: summaryFromTables,
        tables: [
          {
            name: 'Summary Statistics',
            columns: ['Metric', 'Value'],
            rows: [
              ['Total Records', '1,234'],
              ['Unique Values', '456'],
              ['Average', '78.9'],
            ],
          },
        ],
        audit: {
          datasetId: 'mock-1',
          datasetName: 'Mock Dataset',
          analysisType: 'general',
          timePeriod: 'all_time',
          aiAssist: false,
          safeMode: false,
          privacyMode: true,
          executedQueries: [
            {
              name: 'summary_statistics',
              sql: 'SELECT COUNT(*) as total, COUNT(DISTINCT col) as unique FROM data',
              rowCount: 1
            }
          ],
          generatedAt: new Date().toISOString()
        },
      };
    }

    if (message.toLowerCase().includes('trend')) {
      return {
        type: 'run_queries',
        queries: [
          {
            name: 'Monthly Aggregation',
            sql: 'SELECT strftime("%Y-%m", date) as month, SUM(revenue) as total_revenue, COUNT(*) as transaction_count FROM transactions GROUP BY month ORDER BY month',
          },
          {
            name: 'Growth Calculation',
            sql: 'SELECT month, total_revenue, LAG(total_revenue) OVER (ORDER BY month) as prev_revenue FROM monthly_totals',
          },
        ],
      };
    }

    if (message.toLowerCase().includes('outlier')) {
      return {
        type: 'run_queries',
        queries: [
          {
            name: 'Statistical Bounds',
            sql: 'SELECT AVG(value) as mean, STDEV(value) as std_dev FROM dataset',
          },
          {
            name: 'Detect Outliers',
            sql: 'SELECT id, value, ABS(value - (SELECT AVG(value) FROM dataset)) / (SELECT STDEV(value) FROM dataset) as z_score FROM dataset WHERE ABS(z_score) > 3',
          },
        ],
      };
    }

    if (message.toLowerCase().includes('categor')) {
      return {
        type: 'final_answer',
        summaryMarkdown: '## Category Analysis\n\nThe top 5 categories by volume are:\n\n- Electronics: **32%** of total\n- Clothing: **24%** of total\n- Home & Garden: **18%** of total\n- Sports: **15%** of total\n- Books: **11%** of total',
        tables: [
          {
            name: 'Top Categories',
            columns: ['Category', 'Count', 'Revenue', 'Growth'],
            rows: [
              ['Electronics', '1,245', '$342,100', '+12%'],
              ['Clothing', '932', '$198,400', '+8%'],
              ['Home & Garden', '687', '$156,200', '+15%'],
              ['Sports', '543', '$127,800', '+5%'],
              ['Books', '421', '$89,300', '+3%'],
            ],
          },
        ],
        audit: {
          datasetId: 'mock-1',
          datasetName: 'Mock Dataset',
          analysisType: 'category_analysis',
          timePeriod: 'all_time',
          aiAssist: false,
          safeMode: false,
          privacyMode: true,
          executedQueries: [
            {
              name: 'category_summary',
              sql: 'SELECT category, COUNT(*) as count, SUM(revenue) as revenue FROM data GROUP BY category',
              rowCount: 5
            }
          ],
          generatedAt: new Date().toISOString()
        },
      };
    }

    // Row count
    if (message.toLowerCase().includes('row count') || message.toLowerCase().includes('count rows') || message.toLowerCase().includes('how many rows')) {
      return {
        type: 'run_queries',
        queries: [
          {
            name: 'row_count',
            sql: 'SELECT COUNT(*) AS row_count FROM data',
          },
        ],
        explanation: 'Counting total rows in the dataset.',
      };
    }

    return {
      type: 'needs_clarification',
      question: 'What analysis would you like to run?',
      choices: ['Row count', 'Top categories', 'Trend'],
      allowFreeText: true,
      intent: 'set_analysis_type',
    } as any;
  }

  getMockQueryResults(): ExecuteQueriesResponse {
    return {
      results: [
        {
          name: 'Monthly Aggregation',
          columns: ['month', 'total_revenue', 'transaction_count'],
          rows: [
            ['2024-01', '45200', '234'],
            ['2024-02', '49100', '267'],
            ['2024-03', '54800', '289'],
            ['2024-04', '61200', '312'],
            ['2024-05', '68500', '345'],
            ['2024-06', '76700', '378'],
          ],
          rowCount: 6,
        },
        {
          name: 'Growth Calculation',
          columns: ['month', 'total_revenue', 'prev_revenue'],
          rows: [
            ['2024-01', '45200', null],
            ['2024-02', '49100', '45200'],
            ['2024-03', '54800', '49100'],
            ['2024-04', '61200', '54800'],
            ['2024-05', '68500', '61200'],
            ['2024-06', '76700', '68500'],
          ],
          rowCount: 6,
        },
      ],
    };
  }

  getMockCatalog(): DatasetCatalogResponse {
    return {
      tables: [
        {
          name: 'sales',
          rowCount: 15420,
          columns: [
            { name: 'transaction_id', type: 'INTEGER' },
            { name: 'date', type: 'TEXT' },
            { name: 'customer_id', type: 'INTEGER' },
            { name: 'product_id', type: 'INTEGER' },
            { name: 'amount', type: 'REAL' },
            { name: 'quantity', type: 'INTEGER' },
            { name: 'region', type: 'TEXT' },
            { name: 'category', type: 'TEXT' },
          ],
        },
        {
          name: 'customers',
          rowCount: 3240,
          columns: [
            { name: 'customer_id', type: 'INTEGER' },
            { name: 'name', type: 'TEXT' },
            { name: 'email', type: 'TEXT' },
            { name: 'signup_date', type: 'TEXT' },
            { name: 'tier', type: 'TEXT' },
          ],
        },
        {
          name: 'products',
          rowCount: 568,
          columns: [
            { name: 'product_id', type: 'INTEGER' },
            { name: 'name', type: 'TEXT' },
            { name: 'category', type: 'TEXT' },
            { name: 'price', type: 'REAL' },
            { name: 'stock', type: 'INTEGER' },
          ],
        },
      ],
    };
  }

  async fetchReports(datasetId?: string): Promise<ApiResult<Report[]>> {
    try {
      const url = datasetId
        ? `${this.baseUrl}/reports?dataset_id=${encodeURIComponent(datasetId)}`
        : `${this.baseUrl}/reports`;

      const response = await fetch(url, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        return {
          success: false,
          error: {
            status: response.status,
            statusText: response.statusText,
            url: response.url,
            method: 'GET',
            message: `Failed to fetch reports: ${response.statusText}`,
          },
        };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return {
        success: false,
        error: {
          status: 0,
          statusText: 'Network Error',
          url: `${this.baseUrl}/reports`,
          method: 'GET',
          message: error instanceof Error ? error.message : 'Unknown error',
        },
      };
    }
  }

  async fetchReportById(reportId: string): Promise<ApiResult<Report>> {
    try {
      const url = `${this.baseUrl}/reports/${reportId}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        return {
          success: false,
          error: {
            status: response.status,
            statusText: response.statusText,
            url: response.url,
            method: 'GET',
            message: `Failed to fetch report: ${response.statusText}`,
          },
        };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return {
        success: false,
        error: {
          status: 0,
          statusText: 'Network Error',
          url: `${this.baseUrl}/reports/${reportId}`,
          method: 'GET',
          message: error instanceof Error ? error.message : 'Unknown error',
        },
      };
    }
  }
}

export const connectorApi = new ConnectorAPI();
