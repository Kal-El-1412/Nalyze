import { useState, useEffect, useRef } from 'react';
import { CheckCircle, XCircle, ChevronDown, Plus, RefreshCw, ShieldCheck, PlayCircle } from 'lucide-react';
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
  const [demoMode, setDemoMode] = useState(false);
  const [errorCount, setErrorCount] = useState(0);
  const [showDisconnectedBanner, setShowDisconnectedBanner] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  const [resultsData, setResultsData] = useState({
    summary: '',
    tableData: [] as any[],
    auditLog: [] as string[],
    auditMetadata: null as any,
  });

  const [lastRoutingMetadata, setLastRoutingMetadata] = useState<any>(null);
  const [showDatasetSummary, setShowDatasetSummary] = useState(false);

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

  const loadReports = async () => {
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
    // Store routing metadata for diagnostics
    if ((response as any).routing_metadata) {
      setLastRoutingMetadata((response as any).routing_metadata);
      diagnostics.info('Routing', `Decision: ${(response as any).routing_metadata.routing_decision}`,
        JSON.stringify((response as any).routing_metadata, null, 2));
    }

    if (response.type === 'needs_clarification') {
      // Use intent from backend if provided, otherwise detect from question
      const intent = response.intent || detectIntentFromQuestion(response.question);

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

      setResultsData({
        summary: response.summaryMarkdown,
        tableData: response.tables,
        auditLog: auditLogEntries,
        auditMetadata: response.audit,
      });

      // Fetch updated reports list after final_answer
      if (response.audit.reportId) {
        console.log(`Report saved with ID: ${response.audit.reportId}`);
      }
      loadReports();
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
        const result = await connectorApi.sendChatMessage({
          datasetId: activeDataset,
          conversationId,
          intent,
          value: normalizedValue,
          privacyMode,
          safeMode,
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
