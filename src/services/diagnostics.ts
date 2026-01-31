export interface DiagnosticEvent {
  id: string;
  timestamp: string;
  type: 'error' | 'warning' | 'info' | 'success';
  category: string;
  message: string;
  details?: string;
}

class DiagnosticsService {
  private events: DiagnosticEvent[] = [];
  private maxEvents = 50;
  private listeners: Array<(events: DiagnosticEvent[]) => void> = [];

  log(type: DiagnosticEvent['type'], category: string, message: string, details?: string) {
    const event: DiagnosticEvent = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      type,
      category,
      message,
      details,
    };

    this.events.unshift(event);

    if (this.events.length > this.maxEvents) {
      this.events = this.events.slice(0, this.maxEvents);
    }

    this.notifyListeners();

    if (type === 'error') {
      console.error(`[${category}] ${message}`, details);
    } else if (type === 'warning') {
      console.warn(`[${category}] ${message}`, details);
    } else {
      console.log(`[${category}] ${message}`, details);
    }
  }

  error(category: string, message: string, details?: string) {
    this.log('error', category, message, details);
  }

  warning(category: string, message: string, details?: string) {
    this.log('warning', category, message, details);
  }

  info(category: string, message: string, details?: string) {
    this.log('info', category, message, details);
  }

  success(category: string, message: string, details?: string) {
    this.log('success', category, message, details);
  }

  getEvents(): DiagnosticEvent[] {
    return [...this.events];
  }

  clearEvents() {
    this.events = [];
    this.notifyListeners();
  }

  subscribe(listener: (events: DiagnosticEvent[]) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners() {
    this.listeners.forEach(listener => listener([...this.events]));
  }
}

export const diagnostics = new DiagnosticsService();
