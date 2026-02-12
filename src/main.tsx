import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { applyTheme, getSavedThemePreference } from './utils/theme';

applyTheme(getSavedThemePreference());

// If user chose "system", update theme live when OS theme changes
if (window.matchMedia) {
  const mq = window.matchMedia('(prefers-color-scheme: dark)');
  const handler = () => {
    const pref = getSavedThemePreference();
    if (pref === 'system') applyTheme('system');
  };
  mq.addEventListener?.('change', handler);
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
