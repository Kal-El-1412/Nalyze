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
  startedAt: string;
  finishedAt?: string;
  error?: string;
}

export interface QueryResult {
  name: string;
  columns: string[];
  rows: any[][];
}

export interface ChatRequest {
  datasetId: string;
  conversationId: string;
  message: string;
  resultsContext?: {
    results: QueryResult[];
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
  allowFreeText: boolean;
}

export interface RunQueriesResponse {
  type: 'run_queries';
  queries: Array<{
    name: string;
    sql: string;
  }>;
}

export interface FinalAnswerResponse {
  type: 'final_answer';
  summaryMarkdown: string;
  tables: Array<{
    name: string;
    columns: string[];
    rows: any[][];
  }>;
  audit: {
    sharedWithAI: string[];
  };
}

export type ChatResponse = ClarificationResponse | RunQueriesResponse | FinalAnswerResponse;

export interface DatasetColumn {
  name: string;
  type: string;
}

export interface DatasetTable {
  name: string;
  rowCount: number;
  columns: DatasetColumn[];
}

export interface DatasetCatalogResponse {
  tables: DatasetTable[];
}

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

  setBaseUrl(url: string) {
    this.baseUrl = url;
    localStorage.setItem('connectorBaseUrl', url);
  }

  getConnectorUrl(): string {
    return this.baseUrl;
  }

  async checkHealth(retries: number = 2): Promise<HealthResponse | null> {
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(`${this.baseUrl}/health`, {
          method: 'GET',
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

  async registerDataset(request: RegisterDatasetRequest): Promise<RegisterDatasetResponse | null> {
    try {
      const response = await fetch(`${this.baseUrl}/datasets/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Failed to register dataset: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error registering dataset:', error);
      return null;
    }
  }

  async uploadDataset(file: File, name: string): Promise<RegisterDatasetResponse | null> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', name);

      const response = await fetch(`${this.baseUrl}/datasets/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Failed to upload dataset: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error uploading dataset:', error);
      return null;
    }
  }

  async getDatasets(): Promise<Dataset[]> {
    try {
      const response = await fetch(`${this.baseUrl}/datasets`, {
        method: 'GET',
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

  async ingestDataset(datasetId: string): Promise<IngestResponse | null> {
    try {
      const response = await fetch(`${this.baseUrl}/datasets/${datasetId}/ingest`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to ingest dataset: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error ingesting dataset:', error);
      return null;
    }
  }

  async getJobs(): Promise<Job[]> {
    try {
      const response = await fetch(`${this.baseUrl}/jobs`, {
        method: 'GET',
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

  async sendChatMessage(request: ChatRequest): Promise<ChatResponse | null> {
    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Failed to send chat message: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending chat message:', error);
      return null;
    }
  }

  async executeQueries(request: ExecuteQueriesRequest): Promise<ExecuteQueriesResponse | null> {
    try {
      const response = await fetch(`${this.baseUrl}/queries/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Failed to execute queries: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error executing queries:', error);
      return null;
    }
  }

  async getDatasetCatalog(datasetId: string): Promise<DatasetCatalogResponse | null> {
    try {
      const response = await fetch(`${this.baseUrl}/datasets/${datasetId}/catalog`, {
        method: 'GET',
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
      return {
        type: 'final_answer',
        summaryMarkdown: '## Analysis Complete\n\nBased on the query results, here are the key findings:\n\n- Dataset contains diverse data patterns\n- Statistical analysis shows normal distribution\n- No significant anomalies detected in the processed subset',
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
          sharedWithAI: ['Aggregated statistics only', 'No raw data rows shared'],
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
          sharedWithAI: ['Category aggregations', 'Revenue totals by category'],
        },
      };
    }

    return {
      type: 'needs_clarification',
      question: 'What time period would you like to analyze?',
      choices: ['Last 7 days', 'Last 30 days', 'Last 90 days', 'All time'],
      allowFreeText: true,
    };
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
}

export const connectorApi = new ConnectorAPI();
