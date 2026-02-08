export const ensurePermission = async (): Promise<boolean> => {
  if (!('Notification' in window)) {
    console.warn('Browser notifications not supported');
    return false;
  }

  if (Notification.permission === 'granted') {
    return true;
  }

  if (Notification.permission === 'denied') {
    return false;
  }

  try {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  } catch (error) {
    console.error('Failed to request notification permission:', error);
    return false;
  }
};

export const notify = async (title: string, body: string): Promise<void> => {
  if (!('Notification' in window)) {
    return;
  }

  const hasPermission = await ensurePermission();
  if (!hasPermission) {
    return;
  }

  try {
    new Notification(title, {
      body,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
    });
  } catch (error) {
    console.error('Failed to show notification:', error);
  }
};
