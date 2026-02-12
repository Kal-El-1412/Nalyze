export type ThemePreference = 'system' | 'light' | 'dark';

export function getSystemPrefersDark() {
  return window.matchMedia?.('(prefers-color-scheme: dark)')?.matches ?? false;
}

export function applyTheme(pref: ThemePreference) {
  const root = document.documentElement;
  const shouldDark = pref === 'dark' || (pref === 'system' && getSystemPrefersDark());
  root.classList.toggle('dark', shouldDark);
}

export function getSavedThemePreference(): ThemePreference {
  const v = localStorage.getItem('themePreference');
  if (v === 'light' || v === 'dark' || v === 'system') return v;
  return 'system';
}

export function setSavedThemePreference(pref: ThemePreference) {
  localStorage.setItem('themePreference', pref);
  applyTheme(pref);
  window.dispatchEvent(new Event('themeChange'));
}
