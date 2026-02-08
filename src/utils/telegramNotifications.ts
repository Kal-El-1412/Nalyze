export interface TelegramSettings {
  botToken: string;
  chatId: string;
  notifyOnCompletion: boolean;
}

export interface TelegramResponse {
  ok: boolean;
  result?: any;
  description?: string;
}

export async function sendTelegramMessage(
  botToken: string,
  chatId: string,
  message: string
): Promise<{ success: boolean; error?: string }> {
  if (!botToken || !chatId) {
    return { success: false, error: 'Bot token and chat ID are required' };
  }

  try {
    const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chat_id: chatId,
        text: message,
        parse_mode: 'HTML',
      }),
    });

    const data: TelegramResponse = await response.json();

    if (!response.ok || !data.ok) {
      return {
        success: false,
        error: data.description || 'Failed to send message',
      };
    }

    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
    };
  }
}

export async function sendJobCompletionNotification(
  botToken: string,
  chatId: string,
  datasetName: string
): Promise<{ success: boolean; error?: string }> {
  const message = `🔒 <b>CloakedSheets AI</b>\n\nYour analysis is ready for <b>${datasetName}</b>.\n\nOpen the app to view results.`;
  return sendTelegramMessage(botToken, chatId, message);
}

export async function sendTestNotification(
  botToken: string,
  chatId: string
): Promise<{ success: boolean; error?: string }> {
  const message = `🔒 <b>CloakedSheets AI</b>\n\nTest notification successful! Your Telegram integration is working correctly.`;
  return sendTelegramMessage(botToken, chatId, message);
}

export async function sendErrorNotification(
  botToken: string,
  chatId: string,
  errorMessage: string
): Promise<{ success: boolean; error?: string }> {
  const truncatedError = errorMessage.length > 200
    ? errorMessage.substring(0, 200) + '...'
    : errorMessage;
  const message = `⚠️ <b>CloakedSheets AI - Error</b>\n\n${truncatedError}\n\nCheck the app for details.`;
  return sendTelegramMessage(botToken, chatId, message);
}

export async function sendInsightsNotification(
  botToken: string,
  chatId: string,
  datasetName: string,
  shortSummary: string
): Promise<{ success: boolean; error?: string }> {
  const truncatedSummary = shortSummary.length > 150
    ? shortSummary.substring(0, 150) + '...'
    : shortSummary;
  const message = `💡 <b>CloakedSheets AI - New Insights</b>\n\nDataset: <b>${datasetName}</b>\n\n${truncatedSummary}\n\nOpen the app to explore.`;
  return sendTelegramMessage(botToken, chatId, message);
}

export function validateTelegramSettings(settings: TelegramSettings): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!settings.botToken.trim()) {
    errors.push('Bot token is required');
  } else if (!settings.botToken.match(/^\d+:[A-Za-z0-9_-]+$/)) {
    errors.push('Invalid bot token format (should be like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)');
  }

  if (!settings.chatId.trim()) {
    errors.push('Chat ID is required');
  } else if (!settings.chatId.match(/^-?\d+$/)) {
    errors.push('Invalid chat ID format (should be a number)');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

export function loadTelegramSettings(): TelegramSettings {
  const saved = localStorage.getItem('telegramSettings');
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch (error) {
      console.error('Failed to parse Telegram settings:', error);
    }
  }
  return {
    botToken: '',
    chatId: '',
    notifyOnCompletion: false,
  };
}

export function saveTelegramSettings(settings: TelegramSettings): void {
  localStorage.setItem('telegramSettings', JSON.stringify(settings));
}
