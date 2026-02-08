import { useState, useEffect, useRef } from 'react';
import { CheckCircle, XCircle, ChevronDown, Plus, RefreshCw, ShieldCheck, PlayCircle, Sun, Moon, Monitor } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import DatasetsPanel from '../components/DatasetsPanel';
import ReportsPanel from '../components/ReportsPanel';
import ChatPanel from '../components/ChatPanel';
import ResultsPanel from '../components/ResultsPanel';
import ConnectDataModal from '../components/ConnectDataModal';
import DatasetSummary from '../components/DatasetSummary';
import DisconnectedBanner from '../components/DisconnectedBanner';
import DiagnosticsPanel from '../components/DiagnosticsPanel';
import ErrorToast from '../components/ErrorToast';
import Toast from '../components/Toast';
import { connectorApi, Dataset, ChatResponse, ApiError, DatasetCatalog, ReportSummary } from '../services/connectorApi';
import { copyToClipboard } from '../utils/reportGenerator';
import { diagnostics } from '../services/diagnostics';
import { getDatasetDefaults } from '../utils/datasetDefaults';
import { notify } from '../utils/browserNotifications';
import { loadTelegramSettings, sendJobCompletionNotification, sendErrorNotification, sendInsightsNotification, TelegramSettings } from '../utils/telegramNotifications';

interface LocalDataset {
  id: string;
  name: string;
  rows: number;
  lastUsed: string;
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

export default function AppLayout() {
  const [activeSection, setActiveSection] = useState<'datasets' | 'reports' | 'diagnostics'>('datasets');
  const [datasets, setDatasets] = useState<LocalDataset[]>([]);
  const [activeDataset, setActiveDataset] = useState<string | null>(null);
  const [catalog, setCatalog] = useState<DatasetCatalog | null>(null);
  const [reports, setReports] = useState<ReportSummary[]>([]);
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
  const [aiAssist, setAiAssist] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [errorCount, setErrorCount] = useState(0);
  const [showDisconnectedBanner, setShowDisconnectedBanner] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const [notifications, setNotifications] = useState({
    jobComplete: true,
    errors: true,
    insights: true,
  });
  const [telegramSettings, setTelegramSettings] = useState<TelegramSettings>({
    botToken: '',
    chatId: '',
    notifyOnCompletion: false,
  });

  const [resultsData, setResultsData] = useState({
    summary: '',
    tableData: [] as any[],
    auditLog: [] as string[],
    auditMetadata: null as any,
  });

  const [lastRoutingMetadata, setLastRoutingMetadata] = useState<any>(null);
  const [showDatasetSummary, setShowDatasetSummary] = useState(false);
  const [themeMode, setThemeMode] = useState<'light' | 'dark'>('light');
  const [themePreference, setThemePreference] = useState<'system' | 'light' | 'dark'>(
    (localStorage.getItem('themePreference') as any) || 'system'
  );

  const cycleThemePreference = () => {
    const current = (localStorage.getItem('themePreference') as any) || 'system';
    const next = current === 'system' ? 'light' : current === 'light' ? 'dark' : 'system';
    localStorage.setItem('themePreference', next);
    setThemePreference(next);
    window.dispatchEvent(new Event('themeChange'));
  };

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

    const savedAiAssist = localStorage.getItem('aiAssist');
    if (savedAiAssist !== null) {
      setAiAssist(savedAiAssist === 'true');
    }

    const savedNotifications = localStorage.getItem('notifications');
    if (savedNotifications) {
      try {
        setNotifications(JSON.parse(savedNotifications));
      } catch (error) {
        console.error('Failed to parse notifications:', error);
      }
    }

    const savedTelegram = loadTelegramSettings();
    setTelegramSettings(savedTelegram);

    const handleStorageChange = () => {
      const updatedPrivacyMode = localStorage.getItem('privacyMode');
      if (updatedPrivacyMode !== null) {
        setPrivacyMode(updatedPrivacyMode === 'true');
      }

      const updatedSafeMode = localStorage.getItem('safeMode');
      if (updatedSafeMode !== null) {
        setSafeMode(updatedSafeMode === 'true');
      }

      const updatedAiAssist = localStorage.getItem('aiAssist');
      if (updatedAiAssist !== null) {
        setAiAssist(updatedAiAssist === 'true');
      }

      const updatedDemoMode = localStorage.getItem('demoMode');
      if (updatedDemoMode !== null) {
        const newDemoMode = updatedDemoMode === 'true';
        setDemoMode(newDemoMode);

        if (newDemoMode) {
          setConnectorStatus('disconnected');
          setConnectorVersion('');
          setShowDisconnectedBanner(false);
          diagnostics.info('Connector', 'Demo Mode enabled - using mock data');
        } else {
          checkConnectorHealth();
        }
      }

      const updatedPrivacySettings = localStorage.getItem('privacySettings');
      if (updatedPrivacySettings) {
        try {
          setPrivacySettings(JSON.parse(updatedPrivacySettings));
        } catch (error) {
          console.error('Failed to parse privacy settings:', error);
        }
      }

      const updatedNotifications = localStorage.getItem('notifications');
      if (updatedNotifications) {
        try {
          setNotifications(JSON.parse(updatedNotifications));
        } catch (error) {
          console.error('Failed to parse notifications:', error);
        }
      }

      const updatedTelegram = loadTelegramSettings();
      setTelegramSettings(updatedTelegram);
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('privacyModeChange', handleStorageChange);
    window.addEventListener('safeModeChange', handleStorageChange);
    window.addEventListener('aiAssistChange', handleStorageChange);
    window.addEventListener('demoModeChange', handleStorageChange);
    window.addEventListener('privacySettingsChange', handleStorageChange);
    window.addEventListener('notificationsChange', handleStorageChange);

    const unsubscribe = diagnostics.subscribe((events) => {
      const errors = events.filter(e => e.type === 'error').length;
      setErrorCount(errors);
    });

    checkConnectorHealth();
    loadDatasetsFromConnector();
    loadReports();

    const healthInterval = setInterval(checkConnectorHealth, 30000);

    return () => {
      unsubscribe();
      clearInterval(healthInterval);
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('privacyModeChange', handleStorageChange);
      window.removeEventListener('safeModeChange', handleStorageChange);
      window.removeEventListener('aiAssistChange', handleStorageChange);
      window.removeEventListener('demoModeChange', handleStorageChange);
      window.removeEventListener('privacySettingsChange', handleStorageChange);
      window.removeEventListener('notificationsChange', handleStorageChange);
    };
  }, []);

  useEffect(() => {
    if (activeDataset && connectorStatus === 'connected') {
      loadCatalog();
    } else {
      setCatalog(null);
    }
  }, [activeDataset, connectorStatus]);

  useEffect(() => {
    if (activeSection === 'reports' && connectorStatus === 'connected') {
      loadReports();
    }
  }, [activeSection, connectorStatus]);

  useEffect(() => {
    const compute = () => {
      const isDark = document.documentElement.classList.contains('dark');
      setThemeMode(isDark ? 'dark' : 'light');
    };
    compute();

    const handler = () => {
      compute();
      const pref = (localStorage.getItem('themePreference') as any) || 'system';
      setThemePreference(pref);
    };
    window.addEventListener('themeChange', handler);
    return () => window.removeEventListener('themeChange', handler);
  }, []);

  const loadCatalog = async () => {
    if (!activeDataset) return;

    const savedDemoMode = localStorage.getItem('demoMode') === 'true';
    if (savedDemoMode || demoMode) {
      const mockCatalog = connectorApi.getMockCatalog();
      setCatalog(mockCatalog);
      return;
    }

    try {
      const catalogData = await connectorApi.getDatasetCatalog(activeDataset);
      setCatalog(catalogData);
    } catch (error) {
      console.error('Failed to load catalog:', error);
      setCatalog(null);
    }
  };

  const loadReports = async () => {
    const savedDemoMode = localStorage.getItem('demoMode') === 'true';
    if (savedDemoMode || demoMode) {
      setReports([]);
      return;
    }

    try {
      const apiReports = await connectorApi.getReports();
      console.log('Loaded reports from API:', apiReports);
      setReports(apiReports);
    } catch (error) {
      console.error('Error loading reports:', error);
      setReports([]);
    }
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
      const savedDemoMode = localStorage.getItem('demoMode') === 'true';
      if (savedDemoMode || demoMode || connectorStatus === 'disconnected') {
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

  const showToastMessage = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const handleCopySummary = async () => {
    try {
      await copyToClipboard(resultsData.summary);
      showToastMessage('Summary copied to clipboard');
    } catch (error) {
      showToastMessage('Failed to copy summary');
    }
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
          displayError(ingestResult.error);
        }

        await loadDatasetsFromConnector();
        setActiveDataset(result.data.datasetId);
        setConnectorStatus('connected');
      } else {
        const errorDetails = `${result.error.method} ${result.error.url}\n${result.error.status} ${result.error.statusText}\n${result.error.message}`;
        diagnostics.error('Dataset Upload/Register', `Failed to add dataset: ${data.name}`, errorDetails);

        displayError(result.error);

        // Do NOT auto-enable demo mode or create a fake dataset.
        // If user wants Demo Mode, they must turn it on explicitly in Settings.
        showToastMessage('Failed to add dataset. Please check connector and try again.');
        return;
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
      timestamp: new Date().toISOString(),
    };

    setMessages([...messages, userMessage]);

    if (connectorStatus === 'connected') {
      const waitingMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'waiting',
        content: 'Processing your request...',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, waitingMessage]);

      const dataset = datasets.find(d => d.id === activeDataset);
      const datasetName = dataset?.name || activeDataset;
      const defaults = getDatasetDefaults(datasetName);

      try {
        const result = await connectorApi.sendChatMessage({
          datasetId: activeDataset,
          conversationId,
          message: content,
          privacyMode,
          safeMode,
          aiAssist,
          defaultsContext: Object.keys(defaults).length > 0 ? defaults : undefined,
        });

        setMessages(prev => prev.filter(m => m.id !== waitingMessage.id));

        if (result.success) {
          await handleChatResponse(result.data);
        } else {
          // Connector returned error response
          const errorDetails = `${result.error.method} ${result.error.url}\n${result.error.status} ${result.error.statusText}\n${result.error.message}`;
          diagnostics.error('Chat', 'Failed to send chat message', errorDetails);

          // Show error in chat as assistant message
          const errorMessage: Message = {
            id: Date.now().toString(),
            type: 'assistant',
            content: `**Connector Error:** ${result.error.status} ${result.error.statusText}\n\nCould not reach the connector at \`/chat\` endpoint. Please check:\n- Is the connector running?\n- Check the connector URL in settings\n- View Diagnostics tab for details`,
            timestamp: new Date().toISOString(),
          };
          setMessages(prev => [...prev, errorMessage]);

          // Only fallback to mock if demo mode is enabled
          if (demoMode) {
            showToastMessage('Failed to get response. Using mock data.');
            const mockResponse = connectorApi.getMockChatResponse(content);
            await handleChatResponse(mockResponse);
          }
        }
      } catch (error) {
        // Network error, timeout, or other exception
        setMessages(prev => prev.filter(m => m.id !== waitingMessage.id));

        const errorMsg = error instanceof Error ? error.message : String(error);
        const errorDetails = `Network error or timeout\n${errorMsg}`;
        diagnostics.error('Chat', 'Network error during chat request', errorDetails);

        // Show error in chat as assistant message
        const errorMessage: Message = {
          id: Date.now().toString(),
          type: 'assistant',
          content: `**Connection Error:** ${errorMsg}\n\nCould not connect to the connector. Please check:\n- Is the connector running?\n- Network connectivity\n- View Diagnostics tab for details`,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, errorMessage]);

        // Only fallback to mock if demo mode is enabled
        if (demoMode) {
          showToastMessage('Connection failed. Using mock data.');
          const mockResponse = connectorApi.getMockChatResponse(content);
          await handleChatResponse(mockResponse);
        }
      }
    } else if (demoMode) {
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

  const maskPIIInValue = (value: any): any => {
    if (typeof value !== 'string') return value;

    let masked = value;

    masked = masked.replace(
      /([a-zA-Z0-9._-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g,
      '***@$2'
    );

    masked = masked.replace(
      /(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{2}(\d{2})/g,
      (match, prefix, lastTwo) => {
        const maskedLength = match.length - 2;
        return 'X'.repeat(maskedLength) + lastTwo;
      }
    );

    return masked;
  };

  const applyPrivacyFiltering = (results: any[]): any[] => {
    if (!privacySettings.allowSampleRows) {
      return results.map(result => ({
        ...result,
        rows: [],
      }));
    }

    return results.map(result => {
      const limitedRows = result.rows.slice(0, 20);

      if (!privacySettings.maskPII) {
        return {
          ...result,
          rows: limitedRows,
        };
      }

      const maskedRows = limitedRows.map((row: any[]) =>
        row.map(cell => maskPIIInValue(cell))
      );

      return {
        ...result,
        rows: maskedRows,
      };
    });
  };

  const displayError = (error: ApiError) => {
    // show toast UI
    setErrorToast(error);

    // diagnostics log
    diagnostics.error(
      'Connector',
      `${error.status} ${error.statusText}: ${error.message}`,
      error.details ? JSON.stringify(error.details, null, 2) : undefined
    );

    // optional notifications
    if (notifications.errors) {
      const errorMessage = `${error.status} ${error.statusText}: ${error.message}`;
      notify('Connector Error', errorMessage);

      if (telegramSettings.botToken && telegramSettings.chatId) {
        sendErrorNotification(
          telegramSettings.botToken,
          telegramSettings.chatId,
          errorMessage
        ).catch(err => {
          console.error('Failed to send Telegram error notification:', err);
        });
      }
    }
  };

  const handleChatResponse = async (response: ChatResponse) => {
    // Store routing metadata for diagnostics
    if ((response as any).routing_metadata) {
      setLastRoutingMetadata((response as any).routing_metadata);
      diagnostics.info('Routing', `Decision: ${(response as any).routing_metadata.routing_decision}`,
        JSON.stringify((response as any).routing_metadata, null, 2));
    }

    if (response.type === 'needs_clarification') {
      // Use intent from backend if provided, otherwise detect from question
      const intent = response.intent || detectIntentFromQuestion(response.question);

      // Check if this exact same clarification was just asked
      // Prevent duplicate clarification messages
      const isDuplicate = messages.some(msg =>
        msg.type === 'clarification' &&
        msg.content === response.question &&
        !msg.answered
      );

      if (isDuplicate) {
        diagnostics.warning('Chat', 'Duplicate clarification detected', `Question: "${response.question}"`);
        console.warn('Prevented duplicate clarification message:', response.question);
        return;
      }

      const clarificationMessage: Message = {
        id: Date.now().toString(),
        type: 'clarification',
        content: response.question,
        timestamp: new Date().toISOString(),
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
      // Note: The clarification is already marked as answered in handleClarificationResponse
      console.log(`Intent ${response.intent} acknowledged with value:`, response.value);
    } else if (response.type === 'run_queries') {
      const queriesMessageId = Date.now().toString();
      const queriesMessage: Message = {
        id: queriesMessageId,
        type: 'waiting',
        content: response.explanation || 'Running local queries...',
        timestamp: new Date().toISOString(),
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
          displayError(result.error);

          if (demoMode) {
            showToastMessage('Failed to execute queries. Using mock data.');
            queryResults = connectorApi.getMockQueryResults();
          } else {
            return;
          }
        }
      } else if (demoMode) {
        await new Promise(resolve => setTimeout(resolve, 1500));
        queryResults = connectorApi.getMockQueryResults();
      } else {
        return;
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

      const dataset = datasets.find(d => d.id === activeDataset);
      const datasetName = dataset?.name || activeDataset;
      const defaults = getDatasetDefaults(datasetName);

      if (connectorStatus === 'connected') {
        try {
          const filteredResults = applyPrivacyFiltering(queryResults.results);
          const result = await connectorApi.sendChatMessage({
            datasetId: activeDataset,
            conversationId,
            message: 'Here are the query results.',
            privacyMode,
            safeMode,
            aiAssist,
            resultsContext: { results: filteredResults },
            defaultsContext: Object.keys(defaults).length > 0 ? defaults : undefined,
          });

          setMessages(prev => prev.filter(m => m.id !== queriesMessageId));

          if (result.success) {
            await handleChatResponse(result.data);
          } else {
            // Connector returned error response
            const errorDetails = `${result.error.method} ${result.error.url}\n${result.error.status} ${result.error.statusText}\n${result.error.message}`;
            diagnostics.error('Final Answer', 'Failed to generate summary', errorDetails);

            // Show error in chat as assistant message
            const errorMessage: Message = {
              id: Date.now().toString(),
              type: 'assistant',
              content: `**Connector Error:** ${result.error.status} ${result.error.statusText}\n\nFailed to generate summary from query results. Please check:\n- Connector is running properly\n- View Diagnostics tab for details`,
              timestamp: new Date().toISOString(),
            };
            setMessages(prev => [...prev, errorMessage]);

            // Only fallback to mock if demo mode is enabled
            if (demoMode) {
              const mockResponse = connectorApi.getMockChatResponse('results', true);
              await handleChatResponse(mockResponse);
            }
          }
        } catch (error) {
          // Network error, timeout, or other exception
          setMessages(prev => prev.filter(m => m.id !== queriesMessageId));

          const errorMsg = error instanceof Error ? error.message : String(error);
          const errorDetails = `Network error or timeout\n${errorMsg}`;
          diagnostics.error('Final Answer', 'Network error generating summary', errorDetails);

          // Show error in chat as assistant message
          const errorMessage: Message = {
            id: Date.now().toString(),
            type: 'assistant',
            content: `**Connection Error:** ${errorMsg}\n\nFailed to connect to connector for summary generation. Please check:\n- Connector is running\n- Network connectivity\n- View Diagnostics tab for details`,
            timestamp: new Date().toISOString(),
          };
          setMessages(prev => [...prev, errorMessage]);

          // Only fallback to mock if demo mode is enabled
          if (demoMode) {
            const mockResponse = connectorApi.getMockChatResponse('results', true);
            await handleChatResponse(mockResponse);
          }
        }
      } else if (demoMode) {
        setMessages(prev => prev.filter(m => m.id !== queriesMessageId));
        const mockResponse = connectorApi.getMockChatResponse('results', true);
        await handleChatResponse(mockResponse);
      } else {
        setMessages(prev => prev.filter(m => m.id !== queriesMessageId));
      }
    } else if (response.type === 'final_answer') {
      const assistantMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: response.summaryMarkdown,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Build audit log from new audit metadata structure
      const auditLogEntries = [
        ...resultsData.auditLog,
        `${new Date().toLocaleTimeString()} - ✅ Analysis completed`,
        `${new Date().toLocaleTimeString()} - Analysis Type: ${response.audit.analysisType}`,
        `${new Date().toLocaleTimeString()} - Time Period: ${response.audit.timePeriod}`,
        `${new Date().toLocaleTimeString()} - AI Assist: ${response.audit.aiAssist ? 'ON' : 'OFF'}`,
        `${new Date().toLocaleTimeString()} - Safe Mode: ${response.audit.safeMode ? 'ON' : 'OFF'}`,
        `${new Date().toLocaleTimeString()} - Privacy Mode: ${response.audit.privacyMode ? 'ON' : 'OFF'}`,
      ];

      // Add executed queries to audit log with SQL and rowCount
      response.audit.executedQueries.forEach(query => {
        auditLogEntries.push(`${new Date().toLocaleTimeString()} - Query: ${query.name} (${query.rowCount} rows)`);
        auditLogEntries.push(`  SQL: ${query.sql}`);
      });

      setResultsData(prev => ({
        ...prev,
        summary: response.summaryMarkdown || '',
        tableData: response.tables || [],
        auditLog: auditLogEntries,
        auditMetadata: response.audit || null,
      }));

      // Fetch updated reports list after final_answer
      if (response.audit.reportId) {
        console.log(`Report saved with ID: ${response.audit.reportId}`);
      }
      loadReports();

      const dataset = datasets.find(d => d.id === activeDataset);
      const datasetName = dataset?.name || 'dataset';

      if (notifications.jobComplete) {
        showToastMessage('Analysis complete');
        notify('Analysis Complete', `Your analysis for ${datasetName} is ready.`);

        if (telegramSettings.notifyOnCompletion && telegramSettings.botToken && telegramSettings.chatId) {
          sendJobCompletionNotification(
            telegramSettings.botToken,
            telegramSettings.chatId,
            datasetName
          ).catch(error => {
            console.error('Failed to send Telegram notification:', error);
          });
        }
      }

      if (notifications.insights) {
        const insightKeywords = ['insight', 'anomaly', 'spike', 'outlier', 'unusual', 'significant'];
        const summaryLower = response.summaryMarkdown.toLowerCase();
        const hasInsights = insightKeywords.some(keyword => summaryLower.includes(keyword));
        const hasAnomalies = response.audit?.anomalies && response.audit.anomalies.length > 0;

        if (hasInsights || hasAnomalies) {
          const shortSummary = response.summaryMarkdown.substring(0, 150);
          notify('New Insights Found', `Interesting findings detected in ${datasetName}`);

          if (telegramSettings.botToken && telegramSettings.chatId) {
            sendInsightsNotification(
              telegramSettings.botToken,
              telegramSettings.chatId,
              datasetName,
              shortSummary
            ).catch(error => {
              console.error('Failed to send Telegram insights notification:', error);
            });
          }
        }
      }
    }
  };

  const normalizeTimePeriod = (choice: string): string => {
    const timePeriodMap: Record<string, string> = {
      'Last 7 days': 'last_7_days',
      'Last 30 days': 'last_30_days',
      'Last 90 days': 'last_90_days',
      'All time': 'all_time',
    };
    return timePeriodMap[choice] || choice;
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
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, userMessage]);

      // Normalize time period values
      const normalizedValue = intent === 'set_time_period'
        ? normalizeTimePeriod(choice)
        : choice;

      if (connectorStatus === 'connected') {
        try {
          const result = await connectorApi.sendChatMessage({
            datasetId: activeDataset,
            conversationId,
            intent,
            value: normalizedValue,
            privacyMode,
            safeMode,
            aiAssist,
          });

          if (result.success) {
            // Mark the clarification as answered BEFORE handling the response
            setMessages(prev => {
              // Find the last unanswered clarification with matching intent
              const lastClarificationIndex = [...prev].reverse().findIndex(
                m => m.type === 'clarification' &&
                     m.clarificationData?.intent === intent &&
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

            await handleChatResponse(result.data);

            // Only send follow-up if backend returned intent_acknowledged
            // If backend already progressed (run_queries, needs_clarification), don't send continue
            if (result.data.type === 'intent_acknowledged') {
              try {
                const followUpResult = await connectorApi.sendChatMessage({
                  datasetId: activeDataset,
                  conversationId,
                  message: 'continue',
                  privacyMode,
                  safeMode,
                  aiAssist,
                });

                if (followUpResult.success) {
                  await handleChatResponse(followUpResult.data);
                } else {
                  // Follow-up failed
                  const errorDetails = `${followUpResult.error.method} ${followUpResult.error.url}\n${followUpResult.error.status} ${followUpResult.error.statusText}\n${followUpResult.error.message}`;
                  diagnostics.error('Follow-up', 'Failed to send follow-up', errorDetails);

                  const errorMessage: Message = {
                    id: Date.now().toString(),
                    type: 'assistant',
                    content: `**Connector Error:** ${followUpResult.error.status} ${followUpResult.error.statusText}\n\nFailed to continue processing after intent. Check Diagnostics tab for details.`,
                    timestamp: new Date().toISOString(),
                  };
                  setMessages(prev => [...prev, errorMessage]);
                }
              } catch (error) {
                const errorMsg = error instanceof Error ? error.message : String(error);
                const errorDetails = `Network error or timeout\n${errorMsg}`;
                diagnostics.error('Follow-up', 'Network error sending follow-up', errorDetails);

                const errorMessage: Message = {
                  id: Date.now().toString(),
                  type: 'assistant',
                  content: `**Connection Error:** ${errorMsg}\n\nFailed to continue processing. Check connector is running.`,
                  timestamp: new Date().toISOString(),
                };
                setMessages(prev => [...prev, errorMessage]);
              }
            }
          } else {
            // Connector returned error response
            const errorDetails = `${result.error.method} ${result.error.url}\n${result.error.status} ${result.error.statusText}\n${result.error.message}`;
            diagnostics.error('Intent', 'Failed to send intent', errorDetails);

            // Show error in chat as assistant message
            const errorMessage: Message = {
              id: Date.now().toString(),
              type: 'assistant',
              content: `**Connector Error:** ${result.error.status} ${result.error.statusText}\n\nFailed to process clarification response. Please check:\n- Connector is running properly\n- View Diagnostics tab for details`,
              timestamp: new Date().toISOString(),
            };
            setMessages(prev => [...prev, errorMessage]);

            // Only fallback to mock if demo mode is enabled
            if (demoMode) {
              setTimeout(async () => {
                const mockResponse = connectorApi.getMockChatResponse(choice);
                await handleChatResponse(mockResponse);
              }, 500);
            }
          }
        } catch (error) {
          // Network error, timeout, or other exception
          const errorMsg = error instanceof Error ? error.message : String(error);
          const errorDetails = `Network error or timeout\n${errorMsg}`;
          diagnostics.error('Intent', 'Network error sending intent', errorDetails);

          // Show error in chat as assistant message
          const errorMessage: Message = {
            id: Date.now().toString(),
            type: 'assistant',
            content: `**Connection Error:** ${errorMsg}\n\nFailed to connect to connector. Please check:\n- Connector is running\n- Network connectivity\n- View Diagnostics tab for details`,
            timestamp: new Date().toISOString(),
          };
          setMessages(prev => [...prev, errorMessage]);

          // Only fallback to mock if demo mode is enabled
          if (demoMode) {
            setTimeout(async () => {
              const mockResponse = connectorApi.getMockChatResponse(choice);
              await handleChatResponse(mockResponse);
            }, 500);
          }
        }
      } else if (demoMode) {
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
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <Sidebar
        activeSection={activeSection}
        onSectionChange={setActiveSection}
        reportCount={reports.length}
        errorCount={errorCount}
      />

      <div className="flex-1 flex flex-col lg:flex-row">
        <div className="w-full lg:w-80 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800">
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
          {activeSection === 'reports' && (
            <ReportsPanel
              reports={reports}
              datasets={datasets}
              onRefresh={loadReports}
            />
          )}
          {activeSection === 'diagnostics' && (
            <DiagnosticsPanel
              connectorStatus={connectorStatus}
              connectorVersion={connectorVersion}
              onRetryConnection={handleRetryConnection}
              lastRoutingMetadata={lastRoutingMetadata}
              privacyMode={privacyMode}
              safeMode={safeMode}
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
          <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 py-4">
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

                <button
                  onClick={cycleThemePreference}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-100 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                  title="Cycle theme: System → Light → Dark"
                >
                  {themePreference === 'system' ? <Monitor className="w-3.5 h-3.5" /> : themePreference === 'light' ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
                  <span className="hidden sm:inline">
                    {themePreference.charAt(0).toUpperCase() + themePreference.slice(1)}
                  </span>
                </button>

                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium ${
                  themeMode === 'dark'
                    ? 'bg-slate-900 text-slate-100 border border-slate-700'
                    : 'bg-white text-slate-700 border border-slate-200'
                }`}>
                  {themeMode === 'dark' ? 'Dark' : 'Light'}
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
                aiAssist={aiAssist}
                onAiAssistChange={async (value) => {
                  setAiAssist(value);
                  localStorage.setItem('aiAssist', String(value));
                  window.dispatchEvent(new Event('aiAssistChange'));
                  diagnostics.info('Settings', `AI Assist turned ${value ? 'ON' : 'OFF'}`);

                  // Skip connection test in Demo Mode
                  if (value && !demoMode) {
                    diagnostics.info('AI Connection', 'Testing OpenAI API connection...');
                    const testResult = await connectorApi.testAiConnection();

                    if (!testResult) {
                      displayError({
                        status: 0,
                        statusText: 'Network Error',
                        url: '/test-ai-connection',
                        method: 'GET',
                        message: 'Could not reach backend to test AI connection',
                      });
                      diagnostics.error('AI Connection', 'Failed to reach backend');
                    } else if (testResult.status === 'connected') {
                      showToastMessage(testResult.message);
                      diagnostics.info('AI Connection', `✓ ${testResult.message}`, testResult.details);
                    } else if (testResult.status === 'error') {
                      displayError({
                        status: 400,
                        statusText: 'AI Configuration Error',
                        url: '/test-ai-connection',
                        method: 'GET',
                        message: testResult.message,
                        raw: testResult.details,
                      });
                      diagnostics.error('AI Connection', testResult.message, testResult.details);
                    } else if (testResult.status === 'disabled') {
                      displayError({
                        status: 400,
                        statusText: 'AI Mode Disabled',
                        url: '/test-ai-connection',
                        method: 'GET',
                        message: testResult.message,
                        raw: testResult.details,
                      });
                      diagnostics.error('AI Connection', testResult.message, testResult.details);
                    }
                  }
                }}
              />
            </div>
            <div className="w-full lg:w-[500px] max-h-[400px] lg:max-h-none">
              <ResultsPanel
                summary={resultsData.summary}
                tableData={resultsData.tableData}
                auditLog={resultsData.auditLog}
                auditMetadata={resultsData.auditMetadata}
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
