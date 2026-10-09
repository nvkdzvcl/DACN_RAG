import { useRef, useState } from 'react';

const empty = () => ({ drafts: {}, notes: {}, pending: {} });
// ponytail: drafts stay in this tab; use server storage when cross-device recovery is required.
const storageKey = scope => `rag-drafts:${scope}`;
const validId = value => typeof value === 'string' && value.length > 0 && value.length <= 64;
const validPending = value => value && typeof value.content === 'string' && value.content.trim() && value.content.length <= 4000 &&
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value.client_message_id);

function load(scope) {
  try {
    const raw = sessionStorage.getItem(storageKey(scope));
    if (!raw) return { value: empty(), error: false };
    const data = JSON.parse(raw);
    if (!Number.isFinite(data.savedAt) || data.savedAt > Date.now() + 60000) throw new Error('Invalid draft timestamp');
    if (Date.now() - data.savedAt > 86400000) { clearDrafts(scope); return { value: empty(), error: false }; }
    const value = empty();
    for (const [field, limit] of [['drafts', 4000], ['notes', 2000], ['pending', 4000]]) {
      const entries = data[field];
      if (!entries || typeof entries !== 'object' || Array.isArray(entries) || Object.keys(entries).length > 200) throw new Error('Invalid draft entries');
      for (const [id, item] of Object.entries(entries)) {
        if (!validId(id) || ['__proto__', 'constructor', 'prototype'].includes(id) ||
            (field === 'pending' ? !validPending(item) : typeof item !== 'string' || item.length > limit)) throw new Error('Invalid draft');
        value[field][id] = field === 'pending' ? { content: item.content, client_message_id: item.client_message_id } : item;
      }
    }
    return { value, error: false };
  } catch { return { value: empty(), error: true }; }
}

export function clearDrafts(scope) {
  try { sessionStorage.removeItem(storageKey(scope)); } catch { /* Storage blocked: no saved draft can be cleared. */ }
}

export function useDrafts(scope) {
  const [initial] = useState(() => load(scope));
  const [value, setValue] = useState(initial.value);
  const [error, setError] = useState(initial.error);
  const current = useRef(value);
  function update(change) {
    const next = typeof change === 'function' ? change(current.current) : change;
    current.current = next; setValue(next);
    try {
      const saved = Object.fromEntries(Object.entries(next).map(([field, entries]) =>
        [field, Object.fromEntries(Object.entries(entries).filter(([, item]) => item !== ''))]));
      if (Object.values(saved).some(entries => Object.keys(entries).length > 200)) throw new Error('Draft storage full');
      sessionStorage.setItem(storageKey(scope), JSON.stringify({ ...saved, savedAt: Date.now() }));
      setError(false);
    } catch { setError(true); }
  }
  return [value, update, error];
}
