import { useState, useRef, useEffect } from 'react';
import { Send, TrendingUp, AlertTriangle, BarChart3, Bot, User, Loader2, Code, Copy, Pin, Download, ChevronDown } from 'lucide-react';
import DatasetSummaryCard from './DatasetSummaryCard';
import { DatasetCatalog } from '../services/connectorApi';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'clarification' | 'waiting';
  content: string;
  timestamp: string;
  pinned?: boolean;
  clarificationData?: {
    question: string;
    choices: string[];
    allowFreeText: boolean;
  };
  queriesData?: Array<{ name: string; sql: string }>;
}

interface ChatPanelProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  onClarificationResponse: (choice: string) => void;
  onTogglePin?: (messageId: string) => void;
  onShowDatasetSummary?: () => void;
  activeDataset?: string | null;
  datasetName?: string;
  catalog?: DatasetCatalog | null;
}

const quickTemplates = [
  { icon: TrendingUp, text: 'Show me trends over time in this data', label: 'Trend analysis', color: 'text-blue-600 bg-blue-50 hover:bg-blue-100' },
  { icon: AlertTriangle, text: 'Find outliers and anomalies in the data', label: 'Outlier detection', color: 'text-amber-600 bg-amber-50 hover:bg-amber-100' },
  { icon: BarChart3, text: 'Compare different cohorts or segments', label: 'Cohort comparison', color: 'text-purple-600 bg-purple-50 hover:bg-purple-100' },
  { icon: BarChart3, text: 'Break down data by category', label: 'Category breakdown', color: 'text-emerald-600 bg-emerald-50 hover:bg-emerald-100' },
];

const suggestions = [
  { icon: TrendingUp, text: 'Monthly trend', color: 'text-blue-600 bg-blue-50' },
  { icon: AlertTriangle, text: 'Find outliers', color: 'text-amber-600 bg-amber-50' },
  { icon: BarChart3, text: 'Top categories', color: 'text-emerald-600 bg-emerald-50' },
];

export default function ChatPanel({ messages, onSendMessage, onClarificationResponse, onTogglePin, onShowDatasetSummary, activeDataset, datasetName, catalog }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const [showTemplates, setShowTemplates] = useState(false);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
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

  const handleTemplateSelect = (template: typeof quickTemplates[0]) => {
    setInput(template.text);
    setShowTemplates(false);
  };

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
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderMessage = (message: Message) => {
    if (message.type === 'clarification') {
      return (
        <div key={message.id} className="flex gap-3 justify-start">
          <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div className="max-w-2xl rounded-2xl px-4 py-3 bg-slate-100 text-slate-900">
            <p className="text-sm leading-relaxed mb-3">{message.content}</p>
            <div className="space-y-2">
              {message.clarificationData?.choices.map((choice, idx) => (
                <button
                  key={idx}
                  onClick={() => onClarificationResponse(choice)}
                  className="block w-full text-left px-4 py-2 bg-white border border-slate-200 rounded-lg hover:border-emerald-500 hover:bg-emerald-50 transition-all text-sm"
                >
                  {choice}
                </button>
              ))}
              {message.clarificationData?.allowFreeText && (
                <div className="pt-2 border-t border-slate-200">
                  <p className="text-xs text-slate-500 mb-2">Or type your own response</p>
                </div>
              )}
            </div>
            <p className="text-xs mt-3 text-slate-500">{message.timestamp}</p>
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
          <div className="max-w-2xl rounded-2xl px-4 py-3 bg-amber-50 text-amber-900 border border-amber-200">
            <div className="flex items-center gap-3 mb-2">
              <Loader2 className="w-5 h-5 animate-spin text-amber-600" />
              <p className="text-sm font-medium">{message.content}</p>
            </div>
            {message.queriesData && message.queriesData.length > 0 && (
              <div className="mt-3 space-y-2">
                <div className="flex items-center gap-2 text-xs text-amber-700">
                  <Code className="w-4 h-4" />
                  <span className="font-medium">Queries to execute:</span>
                </div>
                {message.queriesData.map((query, idx) => (
                  <div key={idx} className="bg-white/50 rounded px-3 py-2 border border-amber-200">
                    <p className="text-xs font-medium text-amber-900">{query.name}</p>
                    <p className="text-xs text-amber-700 font-mono mt-1">{query.sql}</p>
                  </div>
                ))}
              </div>
            )}
            <p className="text-xs mt-3 text-amber-600">{message.timestamp}</p>
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
                : 'bg-slate-100 text-slate-900'
            }`}
          >
            <div className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </div>
          </div>
          <div className="flex items-center gap-2 mt-1 px-2">
            <span
              className={`text-xs ${
                message.type === 'user' ? 'text-slate-500' : 'text-slate-500'
              }`}
            >
              {formatTimestamp(message.timestamp)}
            </span>
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => handleCopyMessage(message)}
                className="p-1 hover:bg-slate-200 rounded transition-colors"
                title="Copy message"
              >
                {copiedMessageId === message.id ? (
                  <span className="text-xs text-emerald-600 font-medium">Copied!</span>
                ) : (
                  <Copy className="w-3.5 h-3.5 text-slate-500" />
                )}
              </button>
              {onTogglePin && (
                <button
                  onClick={() => onTogglePin(message.id)}
                  className={`p-1 hover:bg-slate-200 rounded transition-colors ${
                    message.pinned ? 'text-amber-600' : 'text-slate-500'
                  }`}
                  title={message.pinned ? 'Unpin message' : 'Pin message'}
                >
                  <Pin className="w-3.5 h-3.5" />
                </button>
              )}
              <button
                onClick={() => handleExportMessage(message)}
                className="p-1 hover:bg-slate-200 rounded transition-colors"
                title="Export message"
              >
                <Download className="w-3.5 h-3.5 text-slate-500" />
              </button>
            </div>
          </div>
        </div>
        {message.type === 'user' && (
          <div className="w-7 h-7 bg-slate-200 rounded-lg flex items-center justify-center flex-shrink-0">
            <User className="w-4 h-4 text-slate-600" />
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center mb-4">
              <Bot className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-slate-900 mb-2">
              Start analyzing your data
            </h3>
            <p className="text-slate-600 mb-6 max-w-md">
              Ask questions about your spreadsheet in natural language. Try one of the suggestions below.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(suggestion.text)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 hover:border-slate-300 transition-all ${suggestion.color}`}
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

      <div className="p-4 border-t border-slate-200 bg-slate-50">
        {activeDataset && catalog && datasetName && onShowDatasetSummary && (
          <div className="mb-3">
            <DatasetSummaryCard
              catalog={catalog}
              datasetName={datasetName}
              onViewSchema={onShowDatasetSummary}
            />
          </div>
        )}
        <div className="flex gap-2 relative">
          <div className="relative" ref={templatesRef}>
            <button
              onClick={() => setShowTemplates(!showTemplates)}
              className="px-3 py-3 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
              title="Quick templates"
            >
              <ChevronDown className={`w-5 h-5 text-slate-600 transition-transform ${showTemplates ? 'rotate-180' : ''}`} />
            </button>
            {showTemplates && (
              <div className="absolute bottom-full left-0 mb-2 w-64 bg-white border border-slate-200 rounded-lg shadow-lg overflow-hidden z-10">
                <div className="p-2 border-b border-slate-200 bg-slate-50">
                  <p className="text-xs font-semibold text-slate-700">Quick Templates</p>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {quickTemplates.map((template, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleTemplateSelect(template)}
                      className={`w-full text-left px-3 py-2.5 hover:bg-slate-50 transition-colors border-b border-slate-100 last:border-b-0`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <template.icon className={`w-3.5 h-3.5 ${template.color.split(' ')[0]}`} />
                        <span className="text-xs font-medium text-slate-900">{template.label}</span>
                      </div>
                      <p className="text-xs text-slate-600">{template.text}</p>
                    </button>
                  ))}
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
            className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white"
          />
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
