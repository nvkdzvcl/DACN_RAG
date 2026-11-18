import { useEffect, useRef, useState } from 'react';

// Loads a staff API path; refreshes on focus when asked, keeps the last good data on error.
export default function useData(path, request, onExpired, refreshOnFocus = false) {
  const [data, setData] = useState(null), [error, setError] = useState(''), [loading, setLoading] = useState(true);
  const [version, setVersion] = useState(0);
  const [updatedAt, setUpdatedAt] = useState(null);
  const loadedPath = useRef(null);
  useEffect(() => {
    if (!refreshOnFocus || !path) return;
    let timer;
    const refresh = () => {
      if (!document.hidden) { clearTimeout(timer); timer = setTimeout(() => setVersion(n => n + 1), 150); }
    };
    window.addEventListener('focus', refresh); document.addEventListener('visibilitychange', refresh);
    return () => { clearTimeout(timer); window.removeEventListener('focus', refresh); document.removeEventListener('visibilitychange', refresh); };
  }, [path, refreshOnFocus]);
  useEffect(() => {
    if (!path) { setData(null); setUpdatedAt(null); setError(''); setLoading(false); loadedPath.current = null; return; }
    const controller = new AbortController();
    if (loadedPath.current !== path) { setData(null); setUpdatedAt(null); }
    loadedPath.current = path; setError(''); setLoading(true);
    request(path, { signal: controller.signal, cache: 'no-store' }).then(value => {
      if (!controller.signal.aborted) { setData(value); setUpdatedAt(new Date().toISOString()); }
    }).catch(e => {
      if (!controller.signal.aborted) { setError(e.message); if (e.status === 401) onExpired(); }
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [path, version]);
  return { data, error, loading, updatedAt, reload: () => setVersion(n => n + 1) };
}
