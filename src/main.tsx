import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';

function applyTheme(pref: 'system' | 'light' | 'dark') {
  const root = document.documentElement;
  const systemDark = window.matchMedia?.('(prefers-color-scheme: dark)')?.matches ?? false;

  const shouldDark = pref === 'dark' || (pref === 'system' && systemDark);
  root.classList.toggle('dark', shouldDark);
}

const saved = (localStorage.getItem('themePreference') as any) || 'system';
applyTheme(saved);

if (window.matchMedia) {
  const mq = window.matchMedia('(prefers-color-scheme: dark)');
  mq.addEventListener?.('change', () => {
    const pref = (localStorage.getItem('themePreference') as any) || 'system';
    if (pref === 'system') applyTheme('system');
  });
}

window.addEventListener('themeChange', () => {
  const pref = (localStorage.getItem('themePreference') as any) || 'system';
  applyTheme(pref);
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
