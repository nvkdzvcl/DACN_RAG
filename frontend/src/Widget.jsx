import React, { useEffect, useRef, useState } from 'react';
import { Bot, Send, UserRound } from 'lucide-react';
import './widget.css';

const statuses = { open: 'Trợ lý hỗ trợ', handoff_requested: 'Đang chờ nhân viên', assigned: 'Nhân viên đã tiếp nhận', closed: 'Hội thoại đã đóng', resolved: 'Hội thoại đã giải quyết' };
const senders = { customer: 'Bạn', ai: 'Trợ lý AI', agent: 'Nhân viên', system: 'Thông báo' };
async function request(path, options = {}) {
  const response = await fetch(`/api/v1/widget${path}`, { ...options, credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Protection': '1' } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(typeof data.detail === 'string' ? data.detail : `Không gửi được yêu cầu (HTTP ${response.status}).`);
    error.status = response.status; throw error;
  }
  if (!response.headers.get('content-type')?.includes('application/json')) throw new Error('Không kết nối được dịch vụ hỗ trợ.');
  return data;
}

export default function Widget() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [handoffBusy, setHandoffBusy] = useState(false);
  const [name, setName] = useState('');
  const [draft, setDraft] = useState('');
  const [error, setError] = useState('');
  const [connectionError, setConnectionError] = useState('');
  const [notice, setNotice] = useState('');
  const [retry, setRetry] = useState(0);
  const sequence = useRef(0);
  const pending = useRef(null);
  const handoffId = useRef(null);
  const log = useRef(null);
  const nearBottom = useRef(true);
  const closed = session?.status === 'closed';

  function apply(data, version) {
    if (typeof data.conversation_id !== 'string' || !Array.isArray(data.messages)) throw new Error('Dữ liệu hội thoại không hợp lệ.');
    if (version === sequence.current) setSession(data);
  }
  function fail(error, version) {
    if (version !== sequence.current) return;
    if (error.status === 401) { setSession(null); pending.current = null; handoffId.current = null; }
    setError(error.message || 'Mất kết nối. Tin nhắn trong ô soạn vẫn được giữ.');
  }
  useEffect(() => {
    const controller = new AbortController();
    const version = ++sequence.current;
    setLoading(true);
    request('/session', { signal: controller.signal }).then(data => { if (!controller.signal.aborted) apply(data, version); })
      .catch(error => { if (!controller.signal.aborted && error.status !== 401) fail(error, version); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [retry]);

  useEffect(() => {
    if (!session || busy || handoffBusy || loading) return;
    const controller = new AbortController();
    let timer;
    async function poll() {
      if (!document.hidden) {
        const version = ++sequence.current;
        try {
          const data = await request('/session', { signal: controller.signal });
          if (!controller.signal.aborted && version === sequence.current) { apply(data, version); setConnectionError(''); }
        } catch (error) {
          if (!controller.signal.aborted && version === sequence.current) {
            if (error.status === 401) fail(error, version);
            else setConnectionError('Mất kết nối. Đang thử kết nối lại...');
          }
        }
      }
      if (!controller.signal.aborted) timer = setTimeout(poll, 3000);
    }
    timer = setTimeout(poll, 3000);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [session?.conversation_id, busy, handoffBusy, loading]);

  useEffect(() => { if (log.current && nearBottom.current) log.current.scrollTop = log.current.scrollHeight; }, [session?.messages.length, busy, notice]);

  async function start(event) {
    event.preventDefault(); setBusy(true); setError(''); setConnectionError(''); setNotice('');
    const version = ++sequence.current;
    try { apply(await request('/session', { method: 'POST', body: JSON.stringify({ display_name: name.trim() }) }), version); }
    catch (error) { fail(error, version); }
    finally { setBusy(false); }
  }
  async function send(event) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || busy || !session || closed) return;
    if (pending.current?.content !== content) pending.current = { content, client_message_id: crypto.randomUUID() };
    const submitted = draft;
    const version = ++sequence.current;
    setBusy(true); setError(''); setNotice(''); nearBottom.current = true;
    try {
      const data = await request('/messages', { method: 'POST', body: JSON.stringify(pending.current) });
      apply(data, version); setDraft(value => value === submitted ? '' : value); pending.current = null;
      if (data.ai_error) setNotice('Tin nhắn đã được lưu nhưng AI chưa trả lời được. Bạn có thể chọn Gặp nhân viên.');
    } catch (error) { fail(error, version); }
    finally { setBusy(false); }
  }
  async function handoff() {
    if (handoffBusy) return;
    handoffId.current ||= crypto.randomUUID();
    const version = ++sequence.current;
    setHandoffBusy(true); setError(''); setNotice('');
    try { apply(await request('/handoff', { method: 'POST', body: JSON.stringify({ client_message_id: handoffId.current }) }), version); handoffId.current = null; }
    catch (error) { fail(error, version); }
    finally { setHandoffBusy(false); }
  }
  async function end() {
    if (!window.confirm('Kết thúc hội thoại? Bạn sẽ không xem lại được lịch sử này trong widget. Nhân viên vẫn giữ lịch sử để hỗ trợ.')) return;
    const version = ++sequence.current; setBusy(true); setError('');
    try { await request('/session', { method: 'DELETE' }); setSession(null); setDraft(''); setNotice('Hội thoại đã kết thúc.'); pending.current = null; }
    catch (error) { fail(error, version); }
    finally { setBusy(false); }
  }

  return <main className="customerWidget">
    <header className="widgetHeader"><span className="widgetMark"><Bot aria-hidden="true" /></span><div><h1>Hỗ trợ khách hàng</h1><p>{statuses[session?.status] || 'Cùng bạn tìm câu trả lời'}</p></div>
      {session && <button className="widgetEnd" onClick={end} disabled={busy || handoffBusy}>Kết thúc</button>}</header>
    {loading ? <p className="widgetState" role="status">Đang kết nối...</p> : !session ? <section className="widgetWelcome">
      <span className="widgetEyebrow">CHÀO BẠN</span><h2>Bạn cần<br />hỗ trợ điều gì?</h2><p>Hỏi về chính sách cửa hàng hoặc kết nối với nhân viên hỗ trợ.</p>
      <form onSubmit={start}><label htmlFor="widgetName">Tên bạn</label><input id="widgetName" autoComplete="given-name" maxLength={80} required value={name} onChange={e => setName(e.target.value)} disabled={busy} />
        <button disabled={busy || !name.trim()}>{busy ? 'Đang kết nối...' : 'Bắt đầu trò chuyện'}</button></form>
      <small>Phiên trò chuyện được giữ trong trình duyệt tối đa 24 giờ.</small>
      {notice && <p role="status">{notice}</p>}{error && <div className="widgetError" role="alert"><p>{error}</p><button onClick={() => { setError(''); setRetry(n => n + 1); }} disabled={busy}>Thử kết nối lại</button></div>}
    </section> : <>
      <div className="widgetLog" ref={log} role="log" aria-label="Tin nhắn hỗ trợ" aria-live="polite" aria-relevant="additions" onScroll={e => { const el = e.currentTarget; nearBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80; }}>
        <p className="widgetIntro">Chào {session.display_name}. Bạn có thể hỏi về chính sách hoặc chọn Gặp nhân viên.</p>
        {session.history_truncated && <p className="widgetIntro">Đang hiển thị 200 tin nhắn gần nhất.</p>}
        {session.messages.map(message => <article key={message.id} className={`widgetMessage ${message.sender_type === 'customer' ? 'widgetOwn' : ''}`}>
          <b>{senders[message.sender_type] || 'Hỗ trợ'}</b><p>{message.content}</p>
          {message.citations?.map((citation, index) => <details key={index}><summary>Nguồn: {citation.source}{citation.location && ` · ${citation.location}`}</summary><blockquote>{citation.quote}</blockquote></details>)}
        </article>)}
        {busy && pending.current && !session.messages.some(m => m.client_message_id === pending.current.client_message_id) && <article className="widgetMessage widgetOwn"><b>Bạn · Đang gửi</b><p>{pending.current.content}</p></article>}
        {busy && <p className="widgetIntro" role="status">Đang xử lý tin nhắn...</p>}
      </div>
      <footer className="widgetFooter">
        {session.status === 'open' ? <button className="widgetHandoff" onClick={handoff} disabled={handoffBusy}><UserRound size={16} aria-hidden="true" />{handoffBusy ? 'Đang chuyển...' : 'Gặp nhân viên'}</button> : <p className="widgetStatus" role="status">{closed ? 'Hội thoại đã đóng. Chọn Kết thúc để bắt đầu phiên mới.' : session.status === 'resolved' ? 'Yêu cầu đã giải quyết. Nhắn tiếp nếu cần hỗ trợ thêm; yêu cầu mới sẽ chuyển vào hàng chờ nhân viên.' : session.status === 'assigned' ? 'Nhân viên đã nhận hội thoại. Bạn có thể nhắn tiếp.' : 'Đã chuyển yêu cầu. Bạn có thể để lại thêm thông tin.'} AI đã dừng trả lời.</p>}
        {notice && <p className="widgetStatus" role="status">{notice}</p>}{error && <p className="widgetError" role="alert">{error}</p>}
        {connectionError && <p className="widgetError" role="status">{connectionError}</p>}
        <form onSubmit={send}><label htmlFor="widgetDraft" className="widgetLabel">Tin nhắn của bạn</label><div className="widgetComposer"><textarea id="widgetDraft" rows={2} maxLength={4000} value={draft} onChange={e => setDraft(e.target.value)} disabled={busy || closed} placeholder={closed ? 'Hội thoại đã đóng' : 'Nhập tin nhắn...'} /><button aria-label="Gửi tin nhắn" disabled={busy || closed || !draft.trim()}><Send size={20} aria-hidden="true" /></button></div></form>
      </footer>
    </>}
  </main>;
}
