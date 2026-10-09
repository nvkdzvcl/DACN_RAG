import { useEffect, useRef, useState } from 'react';

const defaults = { page: 'inbox', selectedId: null, customerFilter: '', assignment: 'all', status: '',
  priority: '', sla: '', search: '', offset: 0, unreadOnly: false, mobileConversation: false,
  recordSearch: '', recordStatus: '', recordOffset: 0, recordId: null };
const choices = { page: ['inbox', 'overview', 'customers', 'orders', 'knowledge', 'analytics', 'settings'],
  assignment: ['all', 'mine', 'unassigned'], status: ['', 'open', 'handoff_requested', 'assigned', 'resolved', 'closed'],
  priority: ['', 'normal', 'high', 'urgent', 'low'], sla: ['', 'on_track', 'overdue', 'met', 'breached', 'cancelled', 'none'],
  recordStatus: ['', 'processing', 'paid', 'shipping', 'shipped', 'delivered', 'cancelled'] };

export function readNavigation(url = window.location.href) {
  const params = new URL(url).searchParams;
  return Object.fromEntries(Object.entries(defaults).map(([key, fallback]) => {
    const value = params.get(key);
    if (value === null) return [key, fallback];
    if (choices[key]) return [key, choices[key].includes(value) ? value : fallback];
    if (typeof fallback === 'boolean') return [key, value === '1'];
    if (typeof fallback === 'number') return [key, /^\d+$/.test(value) && Number(value) <= 2 ** 31 - 1 ? Number(value) : fallback];
    return [key, value.length <= (key.toLowerCase().includes('search') ? 160 : 64) ? value || fallback : fallback];
  }));
}

export function useNavigation() {
  const [route, setRoute] = useState(readNavigation);
  const current = useRef(route);
  useEffect(() => {
    const restore = () => { current.current = readNavigation(); setRoute(current.current); };
    window.addEventListener('popstate', restore);
    return () => window.removeEventListener('popstate', restore);
  }, []);
  function update(patch, replace = true) {
    const next = { ...current.current };
    for (const [key, value] of Object.entries(patch)) next[key] = typeof value === 'function' ? value(next[key]) : value;
    const url = new URL(window.location.href);
    for (const [key, fallback] of Object.entries(defaults)) {
      if (next[key] === fallback) url.searchParams.delete(key);
      else url.searchParams.set(key, typeof next[key] === 'boolean' ? Number(next[key]) : next[key]);
    }
    if (url.href !== window.location.href) window.history[replace ? 'replaceState' : 'pushState'](null, '', url);
    current.current = next; setRoute(next);
  }
  return [route, update];
}
