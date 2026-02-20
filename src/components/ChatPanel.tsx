import { useState, useRef, useEffect } from 'react';
import { Send, TrendingUp, AlertTriangle, BarChart3, Bot, User, Loader2, Code, Copy, Pin, Download, ChevronDown, LineChart, Activity, Users, Filter, FileText, Zap, Check, Sparkles } from 'lucide-react';
import { DatasetCatalog } from '../services/connectorApi';
import { saveDatasetDefault, inferDefaultKeyFromQuestion } from '../utils/datasetDefaults';

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
    intent?: string;  // The intent type for this clarification (e.g., 'set_analysis_type', 'set_time_period')
  };
  queriesData?: Array<{ name: string; sql: string }>;
}

interface ChatPanelProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  onClarificationResponse: (choice: string, intent?: string) => void;
  onTogglePin?: (messageId: string) => void;
  onShowDatasetSummary?: () => void;
  activeDataset?: string | null;
  datasetName?: string;
  catalog?: DatasetCatalog | null;
  privacyMode?: boolean;
  safeMode?: boolean;
  aiAssist?: boolean;
  onAiAssistChange?: (value: boolean) => void;
}

interface AnalysisTemplate {
  id: string;
  icon: any;
  label: string;
  description: string;
  analysisType: string;
  getPrompt: (catalog: DatasetCatalog | null) => string;
  color: string;
  defaults?: {
    timeBucket?: string;
  };
}

const getAnalysisTemplates = (): AnalysisTemplate[] => [
  {
    id: 'trend-monthly',
    icon: LineChart,
    label: 'Trend over time (monthly)',
    description: 'Analyze how metrics change month by month',
    analysisType: 'trend',
    defaults: { timeBucket: 'month' },
    getPrompt: (catalog) => {
      const dateCol = catalog?.detectedDateColumns[0] || 'date';
      const numericCol = catalog?.detectedNumericColumns[0] || 'value';
      return `Show me the monthly trend of ${numericCol} over time using ${dateCol}. Include the total for each month and calculate the month-over-month change.`;
    },
    color: 'text-blue-600 bg-blue-50 hover:bg-blue-100',
  },
  {
    id: 'week-over-week',
    icon: Activity,
    label: 'Week-over-week change',
    description: 'Compare performance across consecutive weeks',
    analysisType: 'trend',
    defaults: { timeBucket: 'week' },
    getPrompt: (catalog) => {
      const dateCol = catalog?.detectedDateColumns[0] || 'date';
      const numericCol = catalog?.detectedNumericColumns[0] || 'value';
      return `Calculate week-over-week change for ${numericCol} using ${dateCol}. Show the absolute change and percentage change for each week.`;
    },
    color: 'text-emerald-600 bg-emerald-50 hover:bg-emerald-100',
  },
  {
    id: 'outliers',
    icon: AlertTriangle,
    label: 'Outliers and anomalies',
    description: 'Identify unusual patterns or extreme values',
    analysisType: 'outliers',
    getPrompt: (catalog) => {
      const numericCol = catalog?.detectedNumericColumns[0] || 'values';
      return `Find outliers and anomalies in ${numericCol}. Show me values that are significantly different from the norm, including statistical outliers beyond 2 standard deviations.`;
    },
    color: 'text-amber-600 bg-amber-50 hover:bg-amber-100',
  },
  {
    id: 'top-categories',
    icon: BarChart3,
    label: 'Top categories contributing to metric',
    description: 'Rank categories by their contribution',
    analysisType: 'top_categories',
    getPrompt: (catalog) => {
      const numericCol = catalog?.detectedNumericColumns[0] || 'value';
      const textCols = catalog?.columns.filter(c =>
        c.type.toUpperCase().includes('TEXT') || c.type.toUpperCase().includes('VARCHAR')
      ) || [];
      const categoryCol = textCols[0]?.name || 'category';
      return `Show me the top 10 ${categoryCol} ranked by total ${numericCol}. Include percentage contribution for each.`;
    },
    color: 'text-violet-600 bg-violet-50 hover:bg-violet-100',
  },
  {
    id: 'cohort-comparison',
    icon: Users,
    label: 'Cohort comparison',
    description: 'Compare different customer segments',
    analysisType: 'top_categories',
    getPrompt: (catalog) => {
      const textCols = catalog?.columns.filter(c =>
        c.type.toUpperCase().includes('TEXT') || c.type.toUpperCase().includes('VARCHAR')
      ) || [];
      const segmentCol = textCols[0]?.name || 'segment';
      const numericCol = catalog?.detectedNumericColumns[0] || 'value';
      return `Compare different ${segmentCol} cohorts. Show average ${numericCol} for each cohort and highlight the key differences between them.`;
    },
    color: 'text-pink-600 bg-pink-50 hover:bg-pink-100',
  },
  {
    id: 'funnel-dropoff',
    icon: Filter,
    label: 'Funnel-style drop-offs',
    description: 'Analyze conversion rates across stages',
    analysisType: 'top_categories',
    getPrompt: (catalog) => {
      const textCols = catalog?.columns.filter(c =>
        c.type.toUpperCase().includes('TEXT') || c.type.toUpperCase().includes('VARCHAR')
      ) || [];
      const stageCol = textCols.find(c => c.name.toLowerCase().includes('stage') || c.name.toLowerCase().includes('status'))?.name || textCols[0]?.name || 'stage';
      return `Analyze the conversion funnel showing drop-off rates between ${stageCol}. Calculate the percentage of users progressing through each stage.`;
    },
    color: 'text-cyan-600 bg-cyan-50 hover:bg-cyan-100',
  },
  {
    id: 'data-quality',
    icon: Zap,
    label: 'Data quality report',
    description: 'Check completeness and consistency',
    analysisType: 'data_quality',
    getPrompt: (catalog) => {
      return `Generate a data quality report showing: (1) missing values per column, (2) duplicate rows, (3) data type inconsistencies, and (4) potential data entry errors.`;
    },
    color: 'text-orange-600 bg-orange-50 hover:bg-orange-100',
  },
  {
    id: 'row-count',
    icon: FileText,
    label: 'Row count',
    description: 'Count total rows in dataset',
    analysisType: 'row_count',
    getPrompt: (catalog) => {
      return `Count the total number of rows in the dataset.`;
    },
    color: 'text-slate-600 bg-slate-50 hover:bg-slate-100',
  },
];

const suggestions = [
  { icon: TrendingUp, text: 'Monthly trend', color: 'text-blue-600 bg-blue-50' },
  { icon: AlertTriangle, text: 'Find outliers', color: 'text-amber-600 bg-amber-50' },
  { icon: BarChart3, text: 'Top categories', color: 'text-emerald-600 bg-emerald-50' },
];

export default function ChatPanel({ messages, onSendMessage, onClarificationResponse, onTogglePin, onShowDatasetSummary, activeDataset, datasetName, catalog, privacyMode = true, safeMode = false, aiAssist = false, onAiAssistChange }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const [showTemplates, setShowTemplates] = useState(false);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [saveAsDefaultMap, setSaveAsDefaultMap] = useState<Record<string, boolean>>({});
  const templatesRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (templatesRef.current && !templatesRef.current.contains(event.target as Node)) {
        setShowTemplates(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleAiAssist = () => {
    if (onAiAssistChange) {
      onAiAssistChange(!aiAssist);
    }
  };

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input.trim());
      setInput('');
      setShowTemplates(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTemplateSelect = (template: AnalysisTemplate) => {
    setShowTemplates(false);

    // Send the template's generated prompt as a normal chat message
    onSendMessage(template.getPrompt(catalog));
  };

  const analysisTemplates = getAnalysisTemplates();

  const handleCopyMessage = (message: Message) => {
    navigator.clipboard.writeText(message.content);
    setCopiedMessageId(message.id);
    setTimeout(() => setCopiedMessageId(null), 2000);
  };

  const handleExportMessage = (message: Message) => {
    const blob = new Blob([message.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `message-${message.id}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) {
      return 'Unknown time';
    }

    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleClarificationChoice = (message: Message, choice: string) => {
    if (datasetName && saveAsDefaultMap[message.id]) {
      const defaultKey = inferDefaultKeyFromQuestion(message.content);
      if (defaultKey) {
        saveDatasetDefault(datasetName, defaultKey, choice);
      }
    }
    onClarificationResponse(choice, message.clarificationData?.intent);
  };

  const renderMessage = (message: Message) => {
    if (message.type === 'clarification') {
      const saveAsDefault = saveAsDefaultMap[message.id] || false;
      const canSaveDefault = !!datasetName && !!inferDefaultKeyFromQuestion(message.content);
      const isAnswered = message.answered || false;

      return (
        <div key={message.id} className="flex gap-3 justify-start">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
            isAnswered
              ? 'bg-slate-300'
              : 'bg-gradient-to-br from-emerald-500 to-teal-600'
          }`}>
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div className={`max-w-2xl rounded-2xl px-4 py-3 ${
            isAnswered
              ? 'bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-300'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100'
          }`}>
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm leading-relaxed flex-1">{message.content}</p>
              {isAnswered && (
                <span className="ml-3 flex items-center gap-1.5 px-2.5 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 rounded-full text-xs font-medium">
                  <Check className="w-3.5 h-3.5" />
                  Answered
                </span>
              )}
            </div>
            <div className="space-y-2">
              {message.clarificationData?.choices.map((choice, idx) => (
                <button
                  key={idx}
                  onClick={() => !isAnswered && handleClarificationChoice(message, choice)}
                  disabled={isAnswered}
                  className={`block w-full text-left px-4 py-2 border rounded-lg transition-all text-sm font-medium ${
                    isAnswered
                      ? 'bg-slate-100 dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-400 dark:text-slate-500 cursor-not-allowed'
                      : 'bg-white dark:bg-slate-950 border-slate-200 dark:border-slate-800 hover:border-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-950 dark:hover:border-emerald-600 text-slate-900 dark:text-slate-100'
                  }`}
                >
                  {choice}
                </button>
              ))}
              {message.clarificationData?.allowFreeText && !isAnswered && (
                <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
                  <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">Or type your own response</p>
                </div>
              )}
            </div>
            {canSaveDefault && !isAnswered && (
              <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-800">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <button
                    onClick={() => setSaveAsDefaultMap(prev => ({ ...prev, [message.id]: !saveAsDefault }))}
                    className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-all ${
                      saveAsDefault
                        ? 'bg-emerald-500 border-emerald-500'
                        : 'bg-white dark:bg-slate-950 border-slate-300 dark:border-slate-700 group-hover:border-emerald-400'
                    }`}
                  >
                    {saveAsDefault && <Check className="w-3 h-3 text-white" />}
                  </button>
                  <span className="text-xs text-slate-600 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-slate-100">
                    Use this as default for <span className="font-semibold">{datasetName}</span>
                  </span>
                </label>
              </div>
            )}
            <p className="text-xs mt-3 text-slate-500 dark:text-slate-400">{formatTimestamp(message.timestamp)}</p>
          </div>
        </div>
      );
    }

    if (message.type === 'waiting') {
      return (
        <div key={message.id} className="flex gap-3 justify-start">
          <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div className="max-w-2xl rounded-2xl px-4 py-3 bg-amber-50 dark:bg-amber-950 text-amber-900 dark:text-amber-100 border border-amber-200 dark:border-amber-800">
            <div className="flex items-center gap-3 mb-2">
              <Loader2 className="w-5 h-5 animate-spin text-amber-600" />
              <p className="text-sm font-medium">{message.content}</p>
            </div>
            {message.queriesData && message.queriesData.length > 0 && (
              <div className="mt-3 space-y-2">
                <div className="flex items-center gap-2 text-xs text-amber-700 dark:text-amber-300">
                  <Code className="w-4 h-4" />
                  <span className="font-medium">Queries to execute:</span>
                </div>
                {message.queriesData.map((query, idx) => (
                  <div key={idx} className="bg-white/50 dark:bg-slate-900/50 rounded px-3 py-2 border border-amber-200 dark:border-amber-700">
                    <p className="text-xs font-medium text-amber-900 dark:text-amber-200">{query.name}</p>
                    <p className="text-xs text-amber-700 dark:text-amber-300 font-mono mt-1">{query.sql}</p>
                  </div>
                ))}
              </div>
            )}
            <p className="text-xs mt-3 text-amber-600 dark:text-amber-400">{formatTimestamp(message.timestamp)}</p>
          </div>
        </div>
      );
    }

    return (
      <div
        key={message.id}
        className={`group flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
      >
        {message.type === 'assistant' && (
          <div className="w-7 h-7 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <Bot className="w-4 h-4 text-white" />
          </div>
        )}
        <div className="flex flex-col max-w-2xl">
          {message.pinned && (
            <div className="flex items-center gap-1 text-xs text-amber-600 mb-1 px-2">
              <Pin className="w-3 h-3" />
              <span className="font-medium">Pinned</span>
            </div>
          )}
          <div
            className={`rounded-xl px-4 py-2.5 ${
              message.type === 'user'
                ? 'bg-emerald-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100'
            }`}
          >
            <div className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </div>
          </div>
          <div className="flex items-center gap-2 mt-1 px-2">
            <span
              className={`text-xs ${
                message.type === 'user' ? 'text-slate-500 dark:text-slate-400' : 'text-slate-500 dark:text-slate-400'
              }`}
            >
              {formatTimestamp(message.timestamp)}
            </span>
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => handleCopyMessage(message)}
                className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors"
                title="Copy message"
              >
                {copiedMessageId === message.id ? (
                  <span className="text-xs text-emerald-600 font-medium">Copied!</span>
                ) : (
                  <Copy className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
                )}
              </button>
              {onTogglePin && (
                <button
                  onClick={() => onTogglePin(message.id)}
                  className={`p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors ${
                    message.pinned ? 'text-amber-600' : 'text-slate-500 dark:text-slate-400'
                  }`}
                  title={message.pinned ? 'Unpin message' : 'Pin message'}
                >
                  <Pin className="w-3.5 h-3.5" />
                </button>
              )}
              <button
                onClick={() => handleExportMessage(message)}
                className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors"
                title="Export message"
              >
                <Download className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
              </button>
            </div>
          </div>
        </div>
        {message.type === 'user' && (
          <div className="w-7 h-7 bg-slate-200 dark:bg-slate-800 rounded-lg flex items-center justify-center flex-shrink-0">
            <User className="w-4 h-4 text-slate-600 dark:text-slate-400" />
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-950">
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center mb-4">
              <Bot className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
              Start analyzing your data
            </h3>
            <p className="text-slate-600 dark:text-slate-300 mb-6 max-w-md">
              Ask questions about your spreadsheet in natural language. Try one of the suggestions below.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(suggestion.text)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 transition-all ${suggestion.color}`}
                >
                  <suggestion.icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{suggestion.text}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map(renderMessage)}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {messages.length === 0 && (
        <div className="px-6 pb-4">
          <div className="flex gap-2 overflow-x-auto pb-2">
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => setInput(suggestion.text)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 hover:border-slate-300 whitespace-nowrap transition-all ${suggestion.color}`}
              >
                <suggestion.icon className="w-4 h-4" />
                <span className="text-sm font-medium">{suggestion.text}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
        <div className="flex gap-2 relative">
          <div className="relative" ref={templatesRef}>
            <button
              onClick={() => setShowTemplates(!showTemplates)}
              className="px-3 py-3 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
              title="Analysis Templates - Context-aware prompts for your data"
            >
              <ChevronDown className={`w-5 h-5 text-slate-600 dark:text-slate-300 transition-transform ${showTemplates ? 'rotate-180' : ''}`} />
            </button>
            {showTemplates && (
              <div className="absolute bottom-full left-0 mb-2 w-80 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-2xl overflow-hidden z-10">
                <div className="p-3 border-b border-slate-200 dark:border-slate-800 bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-850">
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Analysis Templates</p>
                  <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5">Click to fill prompt with context</p>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {analysisTemplates.map((template) => (
                    <button
                      key={template.id}
                      onClick={() => handleTemplateSelect(template)}
                      className="group w-full text-left px-3 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all border-b border-slate-100 dark:border-slate-800 last:border-b-0"
                      title={template.description}
                    >
                      <div className="flex items-start gap-2.5">
                        <div className={`mt-0.5 p-1.5 rounded-lg ${template.color} dark:bg-opacity-20`}>
                          <template.icon className="w-3.5 h-3.5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-semibold text-slate-900 dark:text-slate-100 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                              {template.label}
                            </span>
                          </div>
                          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                            {template.description}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
                <div className="p-2 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                  <p className="text-xs text-slate-500 dark:text-slate-400 text-center">
                    Templates auto-fill based on your dataset schema
                  </p>
                </div>
              </div>
            )}
          </div>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about your data..."
            className="flex-1 px-4 py-3 border border-slate-300 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
          />
          <button
            onClick={toggleAiAssist}
            className={`flex items-center gap-2 px-4 py-3 rounded-lg border transition-all duration-200 ${
              aiAssist
                ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white border-violet-600 shadow-md'
                : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-300 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600'
            }`}
            title={`AI Assist: ${aiAssist ? 'ON' : 'OFF'}`}
          >
            <Sparkles className={`w-4 h-4 ${aiAssist ? 'animate-pulse' : ''}`} />
            <span className="text-sm font-medium">AI Assist</span>
            <span className={`text-xs font-bold px-2 py-0.5 rounded ${
              aiAssist
                ? 'bg-white/20'
                : 'bg-slate-100 dark:bg-slate-800'
            }`}>
              {aiAssist ? 'ON' : 'OFF'}
            </span>
          </button>
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-lg hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
