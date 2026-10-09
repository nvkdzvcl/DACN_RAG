import React, { createContext, useContext, useEffect, useLayoutEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';

const Theme = createContext(null);
export const useTheme = () => useContext(Theme);

export function ThemeProvider({ children }) {
  const [preference, setPreference] = useState(() => {
    try { const value = localStorage.getItem('rag-staff-theme'); return ['light', 'dark'].includes(value) ? value : null; }
    catch { return null; }
  });
  const [systemDark, setSystemDark] = useState(() => matchMedia('(prefers-color-scheme: dark)').matches);
  useEffect(() => {
    const media = matchMedia('(prefers-color-scheme: dark)');
    const change = () => setSystemDark(media.matches);
    const storage = event => { if (event.key === 'rag-staff-theme' || event.key === null) setPreference(['light', 'dark'].includes(event.newValue) ? event.newValue : null); };
    media.addEventListener('change', change); window.addEventListener('storage', storage);
    return () => { media.removeEventListener('change', change); window.removeEventListener('storage', storage); };
  }, []);
  const theme = preference || (systemDark ? 'dark' : 'light');
  useLayoutEffect(() => { document.documentElement.dataset.theme = theme; }, [theme]);
  useEffect(() => {
    const viewport = window.visualViewport;
    const resize = () => {
      document.documentElement.style.setProperty('--chat-height', `${viewport?.height || window.innerHeight}px`);
      document.documentElement.style.setProperty('--chat-top', `${viewport?.offsetTop || 0}px`);
    };
    resize(); viewport?.addEventListener('resize', resize); viewport?.addEventListener('scroll', resize);
    window.addEventListener('resize', resize);
    return () => { viewport?.removeEventListener('resize', resize); viewport?.removeEventListener('scroll', resize); window.removeEventListener('resize', resize); };
  }, []);
  function toggle() {
    const next = theme === 'dark' ? 'light' : 'dark'; setPreference(next);
    try { localStorage.setItem('rag-staff-theme', next); } catch { /* Blocked storage: keep session choice. */ }
  }
  return <Theme.Provider value={{ theme, toggle }}>{children}</Theme.Provider>;
}

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const label = theme === 'dark' ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối';
  return <button type="button" className="themeToggle" onClick={toggle} aria-label={label} title={label}>
    {theme === 'dark' ? <Sun size={17} aria-hidden="true" /> : <Moon size={17} aria-hidden="true" />}<span>{theme === 'dark' ? 'Giao diện sáng' : 'Giao diện tối'}</span>
  </button>;
}
