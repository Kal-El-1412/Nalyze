import { useState, useEffect } from 'react';
import { ArrowLeft, Key, Bell, Save, Eye, EyeOff, Wifi, ShieldCheck, Send, MessageSquare, PlayCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { connectorApi } from '../services/connectorApi';
import {
  loadTelegramSettings,
  saveTelegramSettings,
  validateTelegramSettings,
  sendTestNotification,
  TelegramSettings,
} from '../utils/telegramNotifications';

export default function Settings() {
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [showBotToken, setShowBotToken] = useState(false);
  const [connectorUrl, setConnectorUrl] = useState('http://localhost:7337');
  const [demoMode, setDemoMode] = useState(false);
  const [notifications, setNotifications] = useState({
    jobComplete: true,
    errors: true,
    insights: false,
  });
  const [privacyMode, setPrivacyMode] = useState(true);
  const [privacy, setPrivacy] = useState({
    allowSampleRows: false,
    maskPII: true,
  });
  const [telegram, setTelegram] = useState<TelegramSettings>({
    botToken: '',
    chatId: '',
    notifyOnCompletion: false,
  });
  const [saved, setSaved] = useState(false);
  const [testingTelegram, setTestingTelegram] = useState(false);
  const [telegramTestResult, setTelegramTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  useEffect(() => {
    const savedApiKey = localStorage.getItem('apiKey');
    if (savedApiKey) {
      setApiKey(savedApiKey);
    }

    const savedUrl = localStorage.getItem('connectorBaseUrl');
    if (savedUrl) {
      setConnectorUrl(savedUrl);
    }

    const savedNotifications = localStorage.getItem('notifications');
    if (savedNotifications) {
      setNotifications(JSON.parse(savedNotifications));
    }

    const savedPrivacy = localStorage.getItem('privacySettings');
    if (savedPrivacy) {
      setPrivacy(JSON.parse(savedPrivacy));
    }

    const savedDemoMode = localStorage.getItem('demoMode');
    if (savedDemoMode) {
      setDemoMode(savedDemoMode === 'true');
    }

    const savedPrivacyMode = localStorage.getItem('privacyMode');
    if (savedPrivacyMode !== null) {
      setPrivacyMode(savedPrivacyMode === 'true');
    } else {
      setPrivacyMode(true);
    }

    const savedTelegram = loadTelegramSettings();
    setTelegram(savedTelegram);
  }, []);

  const handleSave = () => {
    if (apiKey) {
      localStorage.setItem('apiKey', apiKey);
    }
    localStorage.setItem('notifications', JSON.stringify(notifications));
    localStorage.setItem('privacySettings', JSON.stringify(privacy));
    localStorage.setItem('privacyMode', privacyMode.toString());
    localStorage.setItem('demoMode', demoMode.toString());
    saveTelegramSettings(telegram);
    connectorApi.setBaseUrl(connectorUrl);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleTestTelegram = async () => {
    const validation = validateTelegramSettings(telegram);

    if (!validation.valid) {
      setTelegramTestResult({
        success: false,
        message: validation.errors.join(', '),
      });
      setTimeout(() => setTelegramTestResult(null), 5000);
      return;
    }

    setTestingTelegram(true);
    setTelegramTestResult(null);

    const result = await sendTestNotification(telegram.botToken, telegram.chatId);

    setTestingTelegram(false);
    setTelegramTestResult({
      success: result.success,
      message: result.success
        ? 'Test message sent successfully!'
        : result.error || 'Failed to send test message',
    });

    setTimeout(() => setTelegramTestResult(null), 5000);
  };

  const handleToggleTelegram = (enabled: boolean) => {
    if (enabled) {
      const validation = validateTelegramSettings(telegram);
      if (!validation.valid) {
        setTelegramTestResult({
          success: false,
          message: 'Please configure and test your settings first',
        });
        setTimeout(() => setTelegramTestResult(null), 3000);
        return;
      }
    }
    setTelegram({ ...telegram, notifyOnCompletion: enabled });
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-4xl mx-auto px-6 py-8">
        <Link
          to="/app"
          className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to App
        </Link>

        <h1 className="text-3xl font-bold text-slate-900 mb-8">Settings</h1>

        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-emerald-50 rounded-lg flex items-center justify-center">
                <Key className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">API Configuration</h2>
                <p className="text-sm text-slate-600">Configure your AI provider API key</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  OpenAI API Key
                </label>
                <div className="relative">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="w-full px-4 py-3 pr-12 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                  <button
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showApiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  Your API key is stored locally and never sent to our servers
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                <Wifi className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Local Connector</h2>
                <p className="text-sm text-slate-600">Configure your local connector endpoint</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Connector Base URL
                </label>
                <input
                  type="text"
                  value={connectorUrl}
                  onChange={(e) => setConnectorUrl(e.target.value)}
                  placeholder="http://localhost:7337"
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
                <p className="text-xs text-slate-500 mt-2">
                  The URL where your local connector is running (default: http://localhost:7337)
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
                <PlayCircle className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Demo Mode</h2>
                <p className="text-sm text-slate-600">Run the app with mock data for demonstrations</p>
              </div>
            </div>

            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-purple-900">
                <strong>Demo Mode:</strong> When enabled, the app will use mock data responses even if the connector
                is running. This is useful for demonstrations, presentations, or testing the UI without a live connector.
              </p>
            </div>

            <label className="flex items-center justify-between p-4 border border-slate-200 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
              <div>
                <div className="font-medium text-slate-900">Enable Demo Mode</div>
                <div className="text-sm text-slate-600">
                  Use mock data responses regardless of connector status
                </div>
              </div>
              <input
                type="checkbox"
                checked={demoMode}
                onChange={(e) => setDemoMode(e.target.checked)}
                className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
              />
            </label>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-emerald-50 rounded-lg flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Privacy & Data Sharing</h2>
                <p className="text-sm text-slate-600">Control what data is shared with AI</p>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-blue-900">
                <strong>Default behavior:</strong> Only schema information and aggregated query results are sent to AI.
                No raw data rows are shared unless you explicitly enable it below.
              </p>
            </div>

            <div className="space-y-4">
              <label className="flex items-center justify-between p-4 border-2 border-emerald-200 rounded-lg hover:bg-emerald-50 cursor-pointer transition-colors bg-emerald-50/50">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <div className="font-semibold text-slate-900">Privacy Mode (mask personal data)</div>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                      privacyMode
                        ? 'bg-emerald-100 text-emerald-700 border border-emerald-300'
                        : 'bg-slate-100 text-slate-600 border border-slate-300'
                    }`}>
                      {privacyMode ? 'ON' : 'OFF'}
                    </span>
                  </div>
                  <div className="text-sm text-slate-600">
                    When enabled, detected PII columns are masked in results and excluded from AI prompts.
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={privacyMode}
                  onChange={(e) => setPrivacyMode(e.target.checked)}
                  className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500 ml-4"
                />
              </label>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-200">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Advanced Privacy Settings</h3>
              <div className="space-y-4">
              <label className="flex items-center justify-between p-4 border border-slate-200 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
                <div>
                  <div className="font-medium text-slate-900">Allow sample rows to be sent to AI</div>
                  <div className="text-sm text-slate-600">
                    When enabled, small samples of actual data may be included in AI requests
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={privacy.allowSampleRows}
                  onChange={(e) =>
                    setPrivacy({ ...privacy, allowSampleRows: e.target.checked })
                  }
                  className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
                />
              </label>

              <label
                className={`flex items-center justify-between p-4 border border-slate-200 rounded-lg transition-colors ${
                  privacy.allowSampleRows
                    ? 'hover:bg-slate-50 cursor-pointer'
                    : 'opacity-50 cursor-not-allowed'
                }`}
              >
                <div>
                  <div className="font-medium text-slate-900">Mask emails and phone numbers</div>
                  <div className="text-sm text-slate-600">
                    Automatically redact PII like emails and phone numbers from samples
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={privacy.maskPII}
                  onChange={(e) =>
                    setPrivacy({ ...privacy, maskPII: e.target.checked })
                  }
                  disabled={!privacy.allowSampleRows}
                  className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500 disabled:opacity-50"
                />
              </label>
            </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-teal-50 rounded-lg flex items-center justify-center">
                <Bell className="w-5 h-5 text-teal-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Notifications</h2>
                <p className="text-sm text-slate-600">Manage your notification preferences</p>
              </div>
            </div>

            <div className="space-y-4">
              <label className="flex items-center justify-between p-4 border border-slate-200 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
                <div>
                  <div className="font-medium text-slate-900">Job Complete</div>
                  <div className="text-sm text-slate-600">Get notified when analysis jobs finish</div>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.jobComplete}
                  onChange={(e) =>
                    setNotifications({ ...notifications, jobComplete: e.target.checked })
                  }
                  className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
                />
              </label>

              <label className="flex items-center justify-between p-4 border border-slate-200 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
                <div>
                  <div className="font-medium text-slate-900">Error Alerts</div>
                  <div className="text-sm text-slate-600">Get notified when errors occur</div>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.errors}
                  onChange={(e) =>
                    setNotifications({ ...notifications, errors: e.target.checked })
                  }
                  className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
                />
              </label>

              <label className="flex items-center justify-between p-4 border border-slate-200 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
                <div>
                  <div className="font-medium text-slate-900">New Insights</div>
                  <div className="text-sm text-slate-600">Get notified about discovered insights</div>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.insights}
                  onChange={(e) =>
                    setNotifications({ ...notifications, insights: e.target.checked })
                  }
                  className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
                />
              </label>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                <MessageSquare className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Telegram Notifications</h2>
                <p className="text-sm text-slate-600">Get notified on Telegram when jobs complete</p>
              </div>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-amber-900">
                <strong>Setup Instructions:</strong>
              </p>
              <ol className="text-sm text-amber-900 mt-2 ml-4 space-y-1 list-decimal">
                <li>Create a bot with <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer" className="underline hover:text-amber-950">@BotFather</a> on Telegram</li>
                <li>Copy the bot token from BotFather</li>
                <li>Start a chat with your bot and send any message</li>
                <li>Get your chat ID from <a href="https://t.me/userinfobot" target="_blank" rel="noopener noreferrer" className="underline hover:text-amber-950">@userinfobot</a></li>
                <li>Enter both values below and test the connection</li>
              </ol>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Telegram Bot Token
                </label>
                <div className="relative">
                  <input
                    type={showBotToken ? 'text' : 'password'}
                    value={telegram.botToken}
                    onChange={(e) => setTelegram({ ...telegram, botToken: e.target.value })}
                    placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                    className="w-full px-4 py-3 pr-12 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                  <button
                    onClick={() => setShowBotToken(!showBotToken)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showBotToken ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Telegram Chat ID
                </label>
                <input
                  type="text"
                  value={telegram.chatId}
                  onChange={(e) => setTelegram({ ...telegram, chatId: e.target.value })}
                  placeholder="123456789"
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>

              <button
                onClick={handleTestTelegram}
                disabled={testingTelegram || !telegram.botToken || !telegram.chatId}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 border-2 border-blue-500 text-blue-600 font-medium rounded-lg hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
                {testingTelegram ? 'Sending test message...' : 'Send Test Message'}
              </button>

              {telegramTestResult && (
                <div
                  className={`p-4 rounded-lg border ${
                    telegramTestResult.success
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                      : 'bg-red-50 border-red-200 text-red-900'
                  }`}
                >
                  <p className="text-sm font-medium">{telegramTestResult.message}</p>
                </div>
              )}

              <label className="flex items-center justify-between p-4 border border-slate-200 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
                <div>
                  <div className="font-medium text-slate-900">Notify on job completion</div>
                  <div className="text-sm text-slate-600">
                    Send Telegram message when analysis jobs finish
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={telegram.notifyOnCompletion}
                  onChange={(e) => handleToggleTelegram(e.target.checked)}
                  className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
                />
              </label>
            </div>
          </div>

          <button
            onClick={handleSave}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-semibold rounded-lg hover:shadow-lg transition-all duration-200"
          >
            <Save className="w-5 h-5" />
            {saved ? 'Saved!' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
