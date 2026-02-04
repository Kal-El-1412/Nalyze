import { useState, useEffect, useRef } from 'react';
import { CheckCircle, XCircle, ChevronDown, Plus, RefreshCw, ShieldCheck, PlayCircle } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import DatasetsPanel from '../components/DatasetsPanel';
import JobsPanel from '../components/JobsPanel';
import ReportsPanel from '../components/ReportsPanel';
import ChatPanel from '../components/ChatPanel';
import ResultsPanel from '../components/ResultsPanel';
import ConnectDataModal from '../components/ConnectDataModal';
import DatasetSummary from '../components/DatasetSummary';
import DisconnectedBanner from '../components/DisconnectedBanner';
import DiagnosticsPanel from '../components/DiagnosticsPanel';
import ErrorToast from '../components/ErrorToast';
import Toast from '../components/Toast';
import { connectorApi, Dataset, Job, ChatResponse, ApiError, DatasetCatalog } from '../services/connectorApi';
import { generateHTMLReport, generateJSONBundle, downloadHTMLReport, downloadJSONBundle, downloadAsZIP, extractSummaryText, copyToClipboard } from '../utils/reportGenerator';
import { loadTelegramSettings, sendJobCompletionNotification } from '../utils/telegramNotifications';
import { diagnostics } from '../services/diagnostics';
import { getDatasetDefaults } from '../utils/datasetDefaults';

interface LocalDataset {
  id: string;
  name: string;
  rows: number;
  lastUsed: string;
}

interface LocalJob {
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

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'clarification' | 'waiting';
  content: string;
  timestamp: string;
  pinned?: boolean;
  answered?: boolean;
  clarificationData?: {
    question: string;
    choices: string[];
    allowFreeText: boolean;
    intent?: string;
  };
  queriesData?: Array<{ name: string; sql: string }>;
}

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

export default function AppLayout() {
  const [activeSection, setActiveSection] = useState<'datasets' | 'jobs' | 'reports' | 'diagnostics' | 'settings'>('datasets');
  const [datasets, setDatasets] = useState<LocalDataset[]>([]);
  const [activeDataset, setActiveDataset] = useState<string | null>(null);
  const [catalog, setCatalog] = useState<DatasetCatalog | null>(null);
  const [jobs, setJobs] = useState<LocalJob[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [connectorStatus, setConnectorStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [connectorVersion, setConnectorVersion] = useState<string>('');
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [errorToast, setErrorToast] = useState<ApiError | null>(null);
  const [conversationId] = useState(() => `conv-${Date.now()}`);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(false);
  const [privacySettings, setPrivacySettings] = useState({
    allowSampleRows: false,
    maskPII: true,
  });
  const [privacyMode, setPrivacyMode] = useState(true);
  const [safeMode, setSafeMode] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [errorCount, setErrorCount] = useState(0);
  const [showDisconnectedBanner, setShowDisconnectedBanner] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  const [resultsData, setResultsData] = useState({
    summary: '',
    tableData: [] as any[],
    auditLog: [] as string[],
  });

  const [showDatasetSummary, setShowDatasetSummary] = useState(false);

  const completedJobsRef = useRef<Set<string>>(new Set());
  const notificationSentRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    const savedDemoMode = localStorage.getItem('demoMode');
    if (savedDemoMode) {
      setDemoMode(savedDemoMode === 'true');
    }

    const savedPrivacy = localStorage.getItem('privacySettings');
    if (savedPrivacy) {
      setPrivacySettings(JSON.parse(savedPrivacy));
    }

    const savedPrivacyMode = localStorage.getItem('privacyMode');
    if (savedPrivacyMode !== null) {
      setPrivacyMode(savedPrivacyMode === 'true');
    }

    const savedSafeMode = localStorage.getItem('safeMode');
    if (savedSafeMode !== null) {
      setSafeMode(savedSafeMode === 'true');
    }

    const handleStorageChange = () => {
      const updatedPrivacyMode = localStorage.getItem('privacyMode');
      if (updatedPrivacyMode !== null) {
        setPrivacyMode(updatedPrivacyMode === 'true');
      }

      const updatedSafeMode = localStorage.getItem('safeMode');
      if (updatedSafeMode !== null) {
        setSafeMode(updatedSafeMode === 'true');
      }
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('privacyModeChange', handleStorageChange);
    window.addEventListener('safeModeChange', handleStorageChange);

    const unsubscribe = diagnostics.subscribe((events) => {
      const errors = events.filter(e => e.type === 'error').length;
      setErrorCount(errors);
    });

    checkConnectorHealth();
    loadDatasetsFromConnector();
    loadJobsFromConnector();
    loadReports();

    const healthInterval = setInterval(checkConnectorHealth, 30000);

    return () => {
      unsubscribe();
      clearInterval(healthInterval);
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('privacyModeChange', handleStorageChange);
      window.removeEventListener('safeModeChange', handleStorageChange);
    };
  }, []);

  useEffect(() => {
    const hasRunningJobs = jobs.some(job => job.status === 'running');
    const pollInterval = hasRunningJobs ? 2000 : 5000;

    const jobsInterval = setInterval(loadJobsFromConnector, pollInterval);

    return () => {
      clearInterval(jobsInterval);
    };
  }, [jobs]);

  useEffect(() => {
    if (activeDataset && connectorStatus === 'connected') {
      loadCatalog();
    } else {
      setCatalog(null);
    }
  }, [activeDataset, connectorStatus]);

  const loadCatalog = async () => {
    if (!activeDataset) return;

    try {
      const catalogData = await connectorApi.getDatasetCatalog(activeDataset);
      setCatalog(catalogData);
    } catch (error) {
      console.error('Failed to load catalog:', error);
      setCatalog(null);
    }
  };

  const loadReports = () => {
    const savedReports = localStorage.getItem('reports');
    if (savedReports) {
      setReports(JSON.parse(savedReports));
    }
  };

  const saveReportsToStorage = (reportsToSave: Report[]) => {
    localStorage.setItem('reports', JSON.stringify(reportsToSave));
    setReports(reportsToSave);
  };

  const checkConnectorHealth = async () => {
    const savedDemoMode = localStorage.getItem('demoMode') === 'true';

    if (savedDemoMode) {
      setConnectorStatus('disconnected');
      setConnectorVersion('');
      setDemoMode(true);
      diagnostics.info('Connector', 'Demo Mode enabled - using mock data');
      setShowDisconnectedBanner(false);
      return;
    }

    setConnectorStatus('checking');
    const health = await connectorApi.checkHealth();

    if (health) {
      setConnectorStatus('connected');
      setConnectorVersion(health.version);
      setShowDisconnectedBanner(false);
      diagnostics.success('Connector', `Connected to connector v${health.version}`);
    } else {
      setConnectorStatus('disconnected');
      setConnectorVersion('');
      setShowDisconnectedBanner(true);
      diagnostics.warning('Connector', 'Unable to connect to connector', `Attempted connection to ${connectorApi.getConnectorUrl()}`);
    }
  };

  const loadDatasetsFromConnector = async () => {
    setIsLoadingDatasets(true);

    try {
      if (demoMode || connectorStatus === 'disconnected') {
        const mockDatasets = connectorApi.getMockDatasets().map((ds: Dataset) => ({
          id: ds.datasetId,
          name: ds.name,
          rows: 0,
          lastUsed: ds.lastIngestedAt || ds.createdAt,
        }));
        setDatasets(mockDatasets);
        if (!activeDataset && mockDatasets.length > 0) {
          setActiveDataset(mockDatasets[0].id);
        }
        setIsLoadingDatasets(false);
        return;
      }

      const apiDatasets = await connectorApi.getDatasets();

      if (apiDatasets.length > 0) {
        const localDatasets: LocalDataset[] = apiDatasets.map((ds: Dataset) => ({
          id: ds.datasetId,
          name: ds.name,
          rows: 0,
          lastUsed: ds.lastIngestedAt || ds.createdAt,
        }));
        setDatasets(localDatasets);
        if (!activeDataset && localDatasets.length > 0) {
          setActiveDataset(localDatasets[0].id);
        }
      } else {
        const mockDatasets = connectorApi.getMockDatasets().map((ds: Dataset) => ({
          id: ds.datasetId,
          name: ds.name,
          rows: Math.floor(Math.random() * 5000) + 1000,
          lastUsed: 'Mock data',
        }));
        setDatasets(mockDatasets);
        if (!activeDataset && mockDatasets.length > 0) {
          setActiveDataset(mockDatasets[0].id);
        }
      }
    } catch (error) {
      diagnostics.error('Datasets', 'Failed to load datasets', error instanceof Error ? error.message : String(error));
      const mockDatasets = connectorApi.getMockDatasets().map((ds: Dataset) => ({
        id: ds.datasetId,
        name: ds.name,
        rows: 0,
        lastUsed: 'Mock data',
      }));
      setDatasets(mockDatasets);
    } finally {
      setIsLoadingDatasets(false);
    }
  };

  const loadJobsFromConnector = async () => {
    const apiJobs = await connectorApi.getJobs();

    if (apiJobs.length > 0) {
      const localJobs: LocalJob[] = apiJobs.map((job: Job) => ({
        id: job.jobId,
        title: `${job.type} - ${job.datasetId}`,
        status: job.status === 'done' ? 'completed' : job.status === 'error' ? 'failed' : 'running',
        stage: job.stage || undefined,
        timestamp: new Date(job.startedAt || Date.now()).toLocaleTimeString(),
        duration: job.finishedAt ? calculateDuration(job.startedAt, job.finishedAt) : undefined,
        startedAt: job.startedAt || undefined,
        finishedAt: job.finishedAt || undefined,
        updatedAt: job.updatedAt || undefined,
        error: job.error || undefined,
      }));

      for (const job of localJobs) {
        if (job.status === 'completed' && !completedJobsRef.current.has(job.id)) {
          completedJobsRef.current.add(job.id);

          if (!notificationSentRef.current.has(job.id)) {
            await sendTelegramNotificationIfEnabled(job.title);
            notificationSentRef.current.add(job.id);
          }
        }
      }

      setJobs(localJobs);
    } else if (connectorStatus === 'disconnected') {
      const mockJobs = connectorApi.getMockJobs().map((job: Job) => ({
        id: job.jobId,
        title: `${job.type} - ${job.datasetId}`,
        status: 'completed' as const,
        stage: 'done' as const,
        timestamp: new Date(job.startedAt).toLocaleTimeString(),
        duration: '2.3s',
        startedAt: job.startedAt,
        finishedAt: job.finishedAt,
      }));
      setJobs(mockJobs);
    }
  };

  const sendTelegramNotificationIfEnabled = async (jobTitle: string) => {
    try {
      const telegramSettings = loadTelegramSettings();

      if (!telegramSettings.notifyOnCompletion) {
        return;
      }

      if (!telegramSettings.botToken || !telegramSettings.chatId) {
        return;
      }

      const datasetName = activeDataset
        ? datasets.find(d => d.id === activeDataset)?.name || jobTitle
        : jobTitle;

      const result = await sendJobCompletionNotification(
        telegramSettings.botToken,
        telegramSettings.chatId,
        datasetName
      );

      if (!result.success) {
        console.error('Failed to send Telegram notification:', result.error);
      }
    } catch (error) {
      console.error('Error sending Telegram notification:', error);
    }
  };

  const calculateDuration = (start: string, end: string): string => {
    const duration = new Date(end).getTime() - new Date(start).getTime();
    return `${(duration / 1000).toFixed(1)}s`;
  };

  const showToastMessage = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const handleExportReport = () => {
    const datasetName = activeDataset
      ? datasets.find(d => d.id === activeDataset)?.name || 'Unknown Dataset'
      : 'No Dataset';

    const reportData = {
      datasetId: activeDataset || undefined,
      datasetName,
      timestamp: new Date().toLocaleString(),
      conversationId,
      messages,
      summary: resultsData.summary,
      tableData: resultsData.tableData,
      auditLog: resultsData.auditLog,
      tables: resultsData.tables || [],
    };

    const htmlContent = generateHTMLReport(reportData);
    const jsonContent = generateJSONBundle(reportData);

    const newReport: Report = {
      id: `report-${Date.now()}`,
      datasetId: activeDataset || undefined,
      datasetName,
      timestamp: new Date().toLocaleString(),
      conversationId,
      htmlContent,
      jsonContent,
      summary: resultsData.summary,
      messages,
      tables: resultsData.tables || [],
      auditLog: resultsData.auditLog,
    };

    const updatedReports = [newReport, ...reports];
    saveReportsToStorage(updatedReports);
    showToastMessage('Report ready ✅');
  };

  const handleCopySummary = async () => {
    try {
      await copyToClipboard(resultsData.summary);
      showToastMessage('Summary copied to clipboard');
    } catch (error) {
      showToastMessage('Failed to copy summary');
    }
  };

  const handleDownloadReport = (report: Report) => {
    const filename = `${report.datasetName.replace(/\s+/g, '-')}-${Date.now()}.html`;
    downloadHTMLReport(report.htmlContent, filename);
    showToastMessage('HTML report downloaded');
  };

  const handleDownloadJSONReport = (report: Report) => {
    if (!report.jsonContent) {
      showToastMessage('JSON data not available for this report');
      return;
    }
    const filename = `${report.datasetName.replace(/\s+/g, '-')}-${Date.now()}.json`;
    downloadJSONBundle(report.jsonContent, filename);
    showToastMessage('JSON report downloaded');
  };

  const handleDownloadZIPReport = async (report: Report) => {
    if (!report.jsonContent) {
      showToastMessage('JSON data not available for this report');
      return;
    }
    try {
      await downloadAsZIP(report.htmlContent, report.jsonContent, report.datasetName);
      showToastMessage('ZIP archive downloaded');
    } catch (error) {
      showToastMessage('ZIP export failed. Please download HTML and JSON separately.');
    }
  };

  const handleCopyReportSummary = async (report: Report) => {
    if (!report.summary) {
      showToastMessage('Summary not available for this report');
      return;
    }
    try {
      await copyToClipboard(report.summary);
      showToastMessage('Summary copied to clipboard');
    } catch (error) {
      showToastMessage('Failed to copy summary');
    }
  };

  const handleDeleteReport = (id: string) => {
    const updatedReports = reports.filter(r => r.id !== id);
    saveReportsToStorage(updatedReports);
    showToastMessage('Report deleted');
  };

  const handleConnectData = async (
    type: 'local' | 'cloud',
    data: { name?: string; filePath?: string; file?: File }
  ) => {
    if (type === 'local' && data.name) {
      let result;

      if (data.file) {
        showToastMessage(`Uploading ${data.name}...`);
        result = await connectorApi.uploadDataset(data.file, data.name);
      } else if (data.filePath) {
        result = await connectorApi.registerDataset({
          name: data.name,
          sourceType: 'local_file',
          filePath: data.filePath,
        });
      } else {
        return;
      }

      if (result.success) {
        showToastMessage(`Successfully registered ${data.name}`);
        diagnostics.success('Dataset', `Registered dataset: ${data.name}`);

        const ingestResult = await connectorApi.ingestDataset(result.data.datasetId);
        if (ingestResult.success) {
          showToastMessage(`Started ingesting dataset`);
          diagnostics.info('Dataset', `Started ingesting dataset: ${data.name}`);
        } else {
          const errorDetails = `${ingestResult.error.method} ${ingestResult.error.url}\n${ingestResult.error.status} ${ingestResult.error.statusText}\n${ingestResult.error.message}`;
          diagnostics.error('Ingest', `Failed to ingest dataset: ${data.name}`, errorDetails);
          setErrorToast(ingestResult.error);
        }

        await loadDatasetsFromConnector();
        setActiveDataset(result.data.datasetId);
        setConnectorStatus('connected');
      } else {
        const errorDetails = `${result.error.method} ${result.error.url}\n${result.error.status} ${result.error.statusText}\n${result.error.message}`;
        diagnostics.error('Dataset Registration', `Failed to register dataset: ${data.name}`, errorDetails);

        setErrorToast(result.error);

        const newDataset: LocalDataset = {
          id: Date.now().toString(),
          name: data.name,
          rows: Math.floor(Math.random() * 10000) + 1000,
          lastUsed: 'Just now',
        };
        setDatasets([...datasets, newDataset]);
        setActiveDataset(newDataset.id);
        setDemoMode(true);
        showToastMessage('⚠️ Using demo mode with mock data');
      }
    } else if (type === 'cloud' && data.file) {
      const newDataset: LocalDataset = {
        id: Date.now().toString(),
        name: data.file.name,
        rows: Math.floor(Math.random() * 10000) + 1000,
        lastUsed: 'Just now',
      };
      setDatasets([...datasets, newDataset]);
      setActiveDataset(newDataset.id);
      showToastMessage(`Successfully uploaded ${data.file.name}`);
    }
  };

  const handleDeleteDataset = (id: string) => {
    setDatasets(datasets.filter(d => d.id !== id));
    if (activeDataset === id) {
      const remaining = datasets.filter(d => d.id !== id);
      setActiveDataset(remaining.length > 0 ? remaining[0].id : null);
      if (remaining.length === 0) {
        setConnectorStatus('disconnected');
      }
    }
    showToastMessage('Dataset removed');
  };

  const handleSendMessage = async (content: string) => {
    if (!activeDataset) {
      showToastMessage('Please select a dataset first');
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages([...messages, userMessage]);

    if (connectorStatus === 'connected') {
      const waitingMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'waiting',
        content: 'Processing your request...',
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages(prev => [...prev, waitingMessage]);

      const dataset = datasets.find(d => d.datasetId === activeDataset);
      const datasetName = dataset?.name || activeDataset;
      const defaults = getDatasetDefaults(datasetName);

      const result = await connectorApi.sendChatMessage({
        datasetId: activeDataset,
        conversationId,
        message: content,
        privacyMode,
        safeMode,
        defaultsContext: Object.keys(defaults).length > 0 ? defaults : undefined,
      });

      setMessages(prev => prev.filter(m => m.id !== waitingMessage.id));

      if (result.success) {
        await handleChatResponse(result.data);
      } else {
        const errorDetails = `${result.error.method} ${result.error.url}\n${result.error.status} ${result.error.statusText}\n${result.error.message}`;
        diagnostics.error('Chat', 'Failed to send chat message', errorDetails);
        setErrorToast(result.error);

        showToastMessage('Failed to get response. Using mock data.');
        const mockResponse = connectorApi.getMockChatResponse(content);
        await handleChatResponse(mockResponse);
      }
    } else {
      setTimeout(async () => {
        const mockResponse = connectorApi.getMockChatResponse(content);
        await handleChatResponse(mockResponse);
      }, 1000);
    }
  };

  const detectIntentFromQuestion = (question: string): string | undefined => {
    const lowerQuestion = question.toLowerCase();

    if (lowerQuestion.includes('type of analysis') || lowerQuestion.includes('analysis would you like')) {
      return 'set_analysis_type';
    }

    if (lowerQuestion.includes('time period') || lowerQuestion.includes('time range')) {
      return 'set_time_period';
    }

    return undefined;
  };

  const handleChatResponse = async (response: ChatResponse) => {
    if (response.type === 'needs_clarification') {
      const intent = detectIntentFromQuestion(response.question);

      const clarificationMessage: Message = {
        id: Date.now().toString(),
        type: 'clarification',
        content: response.question,
        timestamp: new Date().toLocaleTimeString(),
        clarificationData: {
          question: response.question,
          choices: response.choices,
          allowFreeText: response.allowFreeText,
          intent,
        },
      };
      setMessages(prev => [...prev, clarificationMessage]);
    } else if (response.type === 'intent_acknowledged') {
      // Intent was acknowledged, no message needed in chat
      // The state has been updated on the backend
      console.log(`Intent ${response.intent} acknowledged with value:`, response.value);

      // Mark the corresponding clarification message as answered
      setMessages(prev => {
        // Find the last unanswered clarification with matching intent
        const lastClarificationIndex = [...prev].reverse().findIndex(
          m => m.type === 'clarification' &&
               m.clarificationData?.intent === response.intent &&
               !m.answered
        );

        if (lastClarificationIndex === -1) return prev;

        // Convert back to original index
        const actualIndex = prev.length - 1 - lastClarificationIndex;

        // Mark as answered
        return prev.map((msg, idx) =>
          idx === actualIndex ? { ...msg, answered: true } : msg
        );
      });
    } else if (response.type === 'run_queries') {
      const queriesMessageId = Date.now().toString();
      const queriesMessage: Message = {
        id: queriesMessageId,
        type: 'waiting',
        content: response.explanation || 'Running local queries...',
        timestamp: new Date().toLocaleTimeString(),
        queriesData: response.queries,
      };
      setMessages(prev => [...prev, queriesMessage]);

      setResultsData(prev => ({
        ...prev,
        auditLog: [
          ...prev.auditLog,
          `${new Date().toLocaleTimeString()} - Planning: Generated ${response.queries.length} SQL queries`,
          ...response.queries.map(q => `  📝 ${q.name}`),
          ...response.queries.map(q => `     SQL: ${q.sql}`),
        ],
      }));

      if (!activeDataset) return;

      let queryResults;
      if (connectorStatus === 'connected') {
        const result = await connectorApi.executeQueries({
          datasetId: activeDataset,
          queries: response.queries,
        });

        if (result.success) {
          queryResults = result.data;
        } else {
          const errorDetails = `${result.error.method} ${result.error.url}\n${result.error.status} ${result.error.statusText}\n${result.error.message}`;
          diagnostics.error('Query Execution', 'Failed to execute queries', errorDetails);
          setErrorToast(result.error);

          showToastMessage('Failed to execute queries. Using mock data.');
          queryResults = connectorApi.getMockQueryResults();
        }
      } else {
        await new Promise(resolve => setTimeout(resolve, 1500));
        queryResults = connectorApi.getMockQueryResults();
      }

      const privacyMessage = privacySettings.allowSampleRows
        ? privacySettings.maskPII
          ? `${new Date().toLocaleTimeString()} - ⚠️ Sample rows sent with PII masking enabled`
          : `${new Date().toLocaleTimeString()} - ⚠️ Sample rows sent (PII masking disabled)`
        : `${new Date().toLocaleTimeString()} - ✓ No raw data rows shared with AI (aggregates only)`;

      setResultsData(prev => ({
        ...prev,
        auditLog: [
          ...prev.auditLog,
          `${new Date().toLocaleTimeString()} - Executed ${queryResults.results.length} queries locally`,
          privacyMessage,
        ],
      }));

      setMessages(prev =>
        prev.map(m =>
          m.id === queriesMessageId
            ? { ...m, content: 'Writing summary...' }
            : m
        )
      );

      const dataset = datasets.find(d => d.datasetId === activeDataset);
      const datasetName = dataset?.name || activeDataset;
      const defaults = getDatasetDefaults(datasetName);

      const followUpResponse = connectorStatus === 'connected'
        ? await connectorApi.sendChatMessage({
            datasetId: activeDataset,
            conversationId,
            message: 'Here are the query results.',
            privacyMode,
            safeMode,
            resultsContext: { results: queryResults.results },
            defaultsContext: Object.keys(defaults).length > 0 ? defaults : undefined,
          })
        : connectorApi.getMockChatResponse('results', true);

      setMessages(prev => prev.filter(m => m.id !== queriesMessageId));

      if (followUpResponse) {
        await handleChatResponse(followUpResponse);
      }
    } else if (response.type === 'final_answer') {
      const assistantMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: response.message,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages(prev => [...prev, assistantMessage]);

      setResultsData({
        summary: response.message,
        tableData: response.tables || [],
        auditLog: [
          ...resultsData.auditLog,
          `${new Date().toLocaleTimeString()} - ✅ Analysis completed`,
          `${new Date().toLocaleTimeString()} - Shared with AI: ${response.audit.sharedWithAI.join(', ')}`,
        ],
      });
    }
  };

  const handleClarificationResponse = async (choice: string, intent?: string) => {
    if (!activeDataset) {
      showToastMessage('Please select a dataset first');
      return;
    }

    // If we have an intent, send structured intent request
    if (intent) {
      const userMessage: Message = {
        id: Date.now().toString(),
        type: 'user',
        content: choice,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages(prev => [...prev, userMessage]);

      if (connectorStatus === 'connected') {
        const result = await connectorApi.sendChatMessage({
          datasetId: activeDataset,
          conversationId,
          intent,
          value: choice,
          privacyMode,
          safeMode,
        });

        if (result.success) {
          await handleChatResponse(result.data);

          // After acknowledging the intent, send a follow-up message to continue the conversation
          const followUpResult = await connectorApi.sendChatMessage({
            datasetId: activeDataset,
            conversationId,
            message: 'continue',
            privacyMode,
            safeMode,
          });

          if (followUpResult.success) {
            await handleChatResponse(followUpResult.data);
          }
        } else {
          const errorDetails = `${result.error.method} ${result.error.url}\n${result.error.status} ${result.error.statusText}\n${result.error.message}`;
          diagnostics.error('Intent', 'Failed to send intent', errorDetails);
          setErrorToast(result.error);
        }
      } else {
        // Demo mode fallback
        setTimeout(async () => {
          const mockResponse = connectorApi.getMockChatResponse(choice);
          await handleChatResponse(mockResponse);
        }, 500);
      }
    } else {
      // No intent, send as regular message
      handleSendMessage(choice);
    }
  };

  const handleTogglePin = (messageId: string) => {
    setMessages(prevMessages =>
      prevMessages.map(msg =>
        msg.id === messageId ? { ...msg, pinned: !msg.pinned } : msg
      )
    );
  };

  const handleShowDatasetSummary = () => {
    setShowDatasetSummary(true);
  };

  const handleTestConnector = async () => {
    showToastMessage('Testing connector...');
    await checkConnectorHealth();
    if (connectorStatus === 'connected') {
      showToastMessage(`Connection successful! Version ${connectorVersion}`);
    } else {
      showToastMessage('Connection failed. Check if connector is running.');
    }
  };

  const handleRetryConnection = async () => {
    setIsRetrying(true);
    diagnostics.info('Connector', 'Retrying connection to connector...');

    const health = await connectorApi.checkHealth();

    if (health) {
      setConnectorStatus('connected');
      setConnectorVersion(health.version);
      diagnostics.success('Connector', `Successfully connected to connector v${health.version}`);
      showToastMessage(`Connected to connector v${health.version}`);
    } else {
      setConnectorStatus('disconnected');
      diagnostics.error('Connector', 'Failed to connect to connector', `Unable to reach ${connectorApi.getConnectorUrl()}/health`);
      showToastMessage('Connection failed. Check if connector is running.');
    }

    setIsRetrying(false);
  };

  const handleDismissBanner = () => {
    setShowDisconnectedBanner(false);
    diagnostics.info('UI', 'Disconnected banner dismissed');
  };

  const isConnectorReady = demoMode || connectorStatus === 'connected';

  return (
    <div className="flex h-screen bg-slate-50">
      <Sidebar
        activeSection={activeSection}
        onSectionChange={setActiveSection}
        reportCount={reports.length}
        errorCount={errorCount}
      />

      <div className="flex-1 flex flex-col lg:flex-row">
        <div className="w-full lg:w-80 bg-white border-r border-slate-200">
          {activeSection === 'datasets' && (
            <DatasetsPanel
              datasets={datasets}
              activeDataset={activeDataset}
              onSelectDataset={setActiveDataset}
              onAddDataset={() => setShowConnectModal(true)}
              onDeleteDataset={handleDeleteDataset}
              isConnected={connectorStatus === 'connected'}
              catalog={catalog}
              privacyMode={privacyMode}
            />
          )}
          {activeSection === 'jobs' && <JobsPanel jobs={jobs} />}
          {activeSection === 'reports' && (
            <ReportsPanel
              reports={reports}
              onDownloadReport={handleDownloadReport}
              onDownloadJSON={handleDownloadJSONReport}
              onDownloadZIP={handleDownloadZIPReport}
              onCopySummary={handleCopyReportSummary}
              onDeleteReport={handleDeleteReport}
            />
          )}
          {activeSection === 'diagnostics' && (
            <DiagnosticsPanel
              connectorStatus={connectorStatus}
              connectorVersion={connectorVersion}
              onRetryConnection={handleRetryConnection}
            />
          )}
        </div>

        <div className="flex-1 flex flex-col">
          {showDisconnectedBanner && !demoMode && connectorStatus === 'disconnected' && (
            <DisconnectedBanner
              connectorUrl={connectorApi.getConnectorUrl()}
              onRetry={handleRetryConnection}
              onDismiss={handleDismissBanner}
              isRetrying={isRetrying}
            />
          )}
          <div className="bg-white border-b border-slate-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <button className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
                    <span className="text-sm font-medium text-slate-700">
                      {activeDataset
                        ? datasets.find(d => d.id === activeDataset)?.name
                        : 'No dataset selected'}
                    </span>
                    <ChevronDown className="w-4 h-4 text-slate-500" />
                  </button>
                </div>

                <div className="flex items-center gap-2 text-sm">
                  {connectorStatus === 'connected' ? (
                    <>
                      <CheckCircle className="w-4 h-4 text-emerald-600" />
                      <span className="text-emerald-600 font-medium">
                        Connected {connectorVersion && `(v${connectorVersion})`}
                      </span>
                    </>
                  ) : connectorStatus === 'checking' ? (
                    <>
                      <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />
                      <span className="text-blue-600">Checking...</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4 text-slate-400" />
                      <span className="text-slate-500">Disconnected</span>
                    </>
                  )}
                </div>

                {demoMode && (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200">
                    <PlayCircle className="w-3.5 h-3.5" />
                    Demo Mode
                  </div>
                )}

                <div
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium ${
                    privacySettings.allowSampleRows
                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                      : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  }`}
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  {privacySettings.allowSampleRows ? 'Samples Enabled' : 'Local-Only'}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleTestConnector}
                  className="flex items-center gap-2 px-4 py-2 text-sm border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Test Connector
                </button>
                <button
                  onClick={() => setShowConnectModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-sm font-medium rounded-lg hover:shadow-lg transition-all"
                >
                  <Plus className="w-4 h-4" />
                  Connect Data Source
                </button>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
            <div className="flex-1 min-h-[400px] lg:min-h-0">
              <ChatPanel
                messages={messages}
                onSendMessage={handleSendMessage}
                onClarificationResponse={handleClarificationResponse}
                onTogglePin={handleTogglePin}
                onShowDatasetSummary={activeDataset ? handleShowDatasetSummary : undefined}
                activeDataset={activeDataset}
                datasetName={activeDataset ? datasets.find(d => d.id === activeDataset)?.name : undefined}
                catalog={catalog}
                privacyMode={privacyMode}
                safeMode={safeMode}
              />
            </div>
            <div className="w-full lg:w-[500px] max-h-[400px] lg:max-h-none">
              <ResultsPanel
                summary={resultsData.summary}
                tableData={resultsData.tableData}
                auditLog={resultsData.auditLog}
                onExportReport={handleExportReport}
                onCopySummary={handleCopySummary}
                hasContent={resultsData.summary !== '' || resultsData.tableData.length > 0}
              />
            </div>
          </div>
        </div>
      </div>

      <ConnectDataModal
        isOpen={showConnectModal}
        onClose={() => setShowConnectModal(false)}
        onConnect={handleConnectData}
      />

      {activeDataset && (
        <DatasetSummary
          datasetId={activeDataset}
          datasetName={datasets.find(d => d.id === activeDataset)?.name || 'Unknown Dataset'}
          isOpen={showDatasetSummary}
          onClose={() => setShowDatasetSummary(false)}
          connectorStatus={connectorStatus}
        />
      )}

      {showToast && (
        <Toast
          message={toastMessage}
          variant="success"
          onClose={() => setShowToast(false)}
        />
      )}

      {errorToast && (
        <ErrorToast
          error={errorToast}
          onClose={() => setErrorToast(null)}
        />
      )}
    </div>
  );
}
