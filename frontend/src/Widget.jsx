import { ThemeToggle } from './Theme';
import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Bot, Send, UserRound, MessageSquare, PackageSearch, BookOpen, ArrowRight, ShieldCheck, History } from 'lucide-react';
import './widget.css';
import MessageInput from './MessageInput';
import './portal.css';
import { CustomerHistory, CustomerProfile } from './CustomerAccount';
import AuthLayout, { AuthInput } from './AuthLayout';
import CustomerEmail, { takeEmailLink } from './CustomerEmail';
import { clearDrafts, useDrafts } from './drafts';

const statuses = { open: 'Trợ lý hỗ trợ', handoff_requested: 'Đang chờ nhân viên', assigned: 'Nhân viên đã tiếp nhận', closed: 'Hội thoại đã đóng', resolved: 'Hội thoại đã giải quyết' };
const senders = { customer: 'Bạn', ai: 'Trợ lý AI', agent: 'Nhân viên', system: 'Thông báo' };
const orderStatuses = { processing: 'Đang xử lý', paid: 'Đã thanh toán', shipping: 'Đang giao', shipped: 'Đã gửi hàng', delivered: 'Đã giao', cancelled: 'Đã hủy' };
const suggestions = ['Chính sách đổi trả của cửa hàng là gì?', 'Làm thế nào để theo dõi đơn hàng?', 'Điều kiện bảo hành sản phẩm là gì?', 'Khi nào tôi cần gặp nhân viên hỗ trợ?'];
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
  const [emailAction, setEmailAction] = useState(takeEmailLink);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [handoffBusy, setHandoffBusy] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [messageCursors, setMessageCursors] = useState([]);
  const [name, setName] = useState('');
  const [savedDrafts, saveDrafts, draftError] = useDrafts('widget');
  const draft = savedDrafts.drafts[session?.conversation_id] || '';
  const setDraft = value => { if (session) saveDrafts(previous => ({ ...previous, drafts: { ...previous.drafts, [session.conversation_id]: value } })); };
  const [error, setError] = useState('');
  const [connectionError, setConnectionError] = useState('');
  const [notice, setNotice] = useState('');
  const [retry, setRetry] = useState(0);
  const [view, setView] = useState('messages');
  const [authMode, setAuthMode] = useState(() => new URLSearchParams(window.location.search).get('embed') === '1' ? 'guest' : 'login');
  const [orderId, setOrderId] = useState('');
  const [orderResult, setOrderResult] = useState(null);
  const [orderError, setOrderError] = useState('');
  const [orderLoading, setOrderLoading] = useState(false);
  const embedded = new URLSearchParams(window.location.search).get('embed') === '1';
  const sequence = useRef(0);
  const pending = savedDrafts.pending[session?.conversation_id];
  const handoffId = useRef(null);
  const log = useRef(null);
  const nearBottom = useRef(true);
  const [atLatest, setAtLatest] = useState(true);
  const [hasNewMessages, setHasNewMessages] = useState(false);
  const closed = session?.status === 'closed';
  const messageBefore = session?.message_page.before || null;
  const pendingBlocksSend = Boolean(pending && pending.content !== draft.trim());

  useEffect(() => {
    function readLink() { const action = takeEmailLink(); if (action) setEmailAction(action); }
    window.addEventListener('hashchange', readLink);
    return () => window.removeEventListener('hashchange', readLink);
  }, []);
  function emailComplete(mode, message) {
    if (mode === 'reset') clearIdentity(message);
    else setNotice(message);
    setEmailAction(null); setRetry(n => n + 1);
  }
  function apply(data, version) {
    if (typeof data.conversation_id !== 'string' || !Array.isArray(data.messages) || !data.message_page) throw new Error('Dữ liệu hội thoại không hợp lệ.');
    if (version === sequence.current) {
      setSession(data);
      if (!data.message_page.before) setMessageCursors([]);
    }
  }
  function fail(error, version) {
    if (version !== sequence.current) return;
    if (error.status === 401) clearIdentity();
    setError(error.message || 'Mất kết nối. Tin nhắn trong ô soạn vẫn được giữ.');
  }
  useEffect(() => {
    const controller = new AbortController();
    const version = ++sequence.current;
    setLoading(true);
    request('/session', { signal: controller.signal }).then(data => { if (!controller.signal.aborted) { apply(data, version); setAuthMode('guest'); } })
      .catch(error => { if (!controller.signal.aborted && error.status !== 401) fail(error, version); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [retry]);

  useEffect(() => {
    if (!session || busy || handoffBusy || loading || historyLoading) return;
    const controller = new AbortController();
    let timer;
    async function poll() {
      if (!document.hidden) {
        const version = ++sequence.current;
        try {
          const data = await request(`/session?${new URLSearchParams({ limit: 50, ...(messageBefore && { before: messageBefore }) })}`, { signal: controller.signal });
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
  }, [session?.conversation_id, messageBefore, busy, handoffBusy, loading, historyLoading]);

  useLayoutEffect(() => {
    nearBottom.current = !messageBefore;
    setAtLatest(!messageBefore); setHasNewMessages(false);
    if (log.current) log.current.scrollTop = messageBefore ? 0 : log.current.scrollHeight;
  }, [session?.conversation_id, messageBefore, loading, view]);
  useEffect(() => { if (log.current && nearBottom.current && !messageBefore) log.current.scrollTop = log.current.scrollHeight; }, [session?.messages.at(-1)?.id, busy, notice]);
  useEffect(() => {
    if (!messageBefore && !nearBottom.current) setHasNewMessages(true);
  }, [session?.messages.at(-1)?.id]);

  function jumpLatest() {
    if (log.current) { log.current.scrollTop = log.current.scrollHeight; log.current.focus({ preventScroll: true }); }
    nearBottom.current = true; setAtLatest(true); setHasNewMessages(false);
  }

  async function viewHistory(cursors) {
    if (busy || handoffBusy || historyLoading) return;
    const version = ++sequence.current;
    const before = cursors.at(-1) || null;
    setHistoryLoading(true); setError('');
    try {
      const data = await request(`/session?${new URLSearchParams({ limit: 50, ...(before && { before }) })}`);
      if (data.message_page?.before !== before) throw new Error('Dữ liệu trang tin nhắn không hợp lệ.');
      if (version === sequence.current) { apply(data, version); setMessageCursors(cursors); setConnectionError(''); }
    } catch (error) { fail(error, version); }
    finally { setHistoryLoading(false); }
  }

  async function start(event) {
    event.preventDefault(); setBusy(true); setError(''); setConnectionError(''); setNotice('');
    const version = ++sequence.current;
    try { apply(await request('/session', { method: 'POST', body: JSON.stringify({ display_name: name.trim() }) }), version); }
    catch (error) { fail(error, version); }
    finally { setBusy(false); }
  }
  async function send(event, retryPending = false) {
    event.preventDefault();
    const content = retryPending ? pending?.content : draft.trim();
    if (!content || busy || historyLoading || !session || closed || (!retryPending && pendingBlocksSend)) return;
    const targetId = session.conversation_id;
    const submission = pending?.content === content ? pending : { content, client_message_id: crypto.randomUUID() };
    saveDrafts(previous => ({ ...previous, pending: { ...previous.pending, [targetId]: submission } }));
    const submitted = draft.trim() === content ? draft : null;
    const version = ++sequence.current;
    setBusy(true); setError(''); setNotice(''); nearBottom.current = true;
    try {
      const data = await request('/messages', { method: 'POST', body: JSON.stringify(submission) });
      apply(data, version);
      saveDrafts(previous => {
        const nextPending = { ...previous.pending }; delete nextPending[targetId];
        return { ...previous, pending: nextPending, drafts: previous.drafts[targetId] === submitted ? { ...previous.drafts, [targetId]: '' } : previous.drafts };
      });
      if (version === sequence.current && data.ai_error) setNotice('Tin nhắn đã được lưu nhưng AI chưa trả lời được. Bạn có thể chọn Gặp nhân viên.');
    } catch (error) { fail(error, version); }
    finally { setBusy(false); }
  }
  async function handoff() {
    if (handoffBusy || historyLoading) return;
    handoffId.current ||= crypto.randomUUID();
    const version = ++sequence.current;
    setHandoffBusy(true); setError(''); setNotice('');
    try { apply(await request('/handoff', { method: 'POST', body: JSON.stringify({ client_message_id: handoffId.current }) }), version); handoffId.current = null; }
    catch (error) { fail(error, version); }
    finally { setHandoffBusy(false); }
  }
  function clearIdentity(message = '') {
    ++sequence.current; setSession(null); setMessageCursors([]); setView('messages');
    setOrderResult(null); setOrderId(''); setOrderError(''); setConnectionError(''); setNotice(message);
    handoffId.current = null; setAuthMode(embedded ? 'guest' : 'login');
  }
  function openAuth(mode) { setAuthMode(mode); setView('messages'); setError(''); }
  async function authenticate(event) {
    event.preventDefault(); const fields = new FormData(event.currentTarget); setError('');
    if (authMode === 'register' && fields.get('password') !== fields.get('confirm')) { setError('Mật khẩu nhập lại chưa khớp.'); return; }
    const version = ++sequence.current; setBusy(true); setNotice('');
    try {
      const data = await request('/account/' + authMode, { method: 'POST', body: JSON.stringify({
        email: fields.get('email').trim(), password: fields.get('password'),
        ...(authMode === 'register' && { display_name: fields.get('display_name').trim() })
      }) });
      apply(data, version); setAuthMode('guest'); setNotice(data.account?.email_verified ? '' : 'Đăng nhập thành công. Mở Tài khoản để xác minh email và bật khôi phục mật khẩu.'); setMessageCursors([]); setOrderResult(null); setOrderId(''); setConnectionError('');
      handoffId.current = null;
    } catch (error) { setError(error.message); }
    finally { setBusy(false); }
  }
  async function logout() {
    if (busy || handoffBusy || historyLoading) return;
    setBusy(true); setError('');
    try {
      await request('/account/logout', { method: 'POST' });
      saveDrafts({ drafts: {}, notes: {}, pending: {} }); clearDrafts('widget');
      clearIdentity('Đã đăng xuất. Lịch sử tài khoản vẫn được lưu.');
    }
    catch (error) { if (error.status === 401) clearIdentity(); else setError(error.message); }
    finally { setBusy(false); }
  }
  async function end() {
    const prompt = session?.account ? 'Bắt đầu cuộc trò chuyện mới? Hội thoại hiện tại sẽ kết thúc; lịch sử vẫn lưu trong tài khoản.' : 'Kết thúc hội thoại? Bạn sẽ không xem lại được lịch sử này trong widget. Nhân viên vẫn giữ lịch sử để hỗ trợ.';
    if (!window.confirm(prompt)) return;
    const version = ++sequence.current; setBusy(true); setError('');
    try {
      const data = await request('/session', { method: 'DELETE' });
      saveDrafts(previous => Object.fromEntries(Object.entries(previous).map(([field, entries]) => {
        const next = { ...entries }; delete next[session.conversation_id]; return [field, next];
      })));
      if (data.account) { apply(data, version); setOrderResult(null); setOrderId(''); setNotice('Đã bắt đầu cuộc trò chuyện mới.'); }
      else clearIdentity('Hội thoại đã kết thúc.');
    } catch (error) { fail(error, version); }
    finally { setBusy(false); }
  }

  async function redeem(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    const version = ++sequence.current;
    setBusy(true); setError(''); setNotice('');
    try {
      const data = await request('/order-access', { method: 'POST', body: JSON.stringify({
        order_id: fields.get('order_id').trim().toUpperCase(), code: fields.get('code').trim()
      }) });
      apply(data, version); form.reset();
      if (version === sequence.current) setNotice('Đã cấp quyền tra đơn cho phiên này. Gửi mã đơn trong tin nhắn để tra cứu; hội thoại đã chuyển nhân viên vẫn do nhân viên hỗ trợ.');
    } catch (error) { fail(error, version); }
    finally { setBusy(false); }
  }

  async function inspectOrder(id, code) {
    const normalized = id.trim().toUpperCase();
    if (!normalized || !session || busy) return;
    const version = ++sequence.current;
    setBusy(true); setOrderLoading(true); setOrderError(''); setOrderResult(null);
    try {
      const permitted = session.order_access?.some(access => access.order_id === normalized && access.expires_at > Date.now() / 1000);
      if (!permitted) {
        const updated = await request('/order-access', { method: 'POST', body: JSON.stringify({ order_id: normalized, code }) });
        apply(updated, version);
      }
      const result = await request(`/orders/${encodeURIComponent(normalized)}`);
      if (version === sequence.current) { setOrderResult(result); setOrderId(normalized); }
    } catch (error) {
      if (error.status === 401) fail(error, version);
      if (version === sequence.current) setOrderError(error.message);
    } finally { setBusy(false); setOrderLoading(false); }
  }
  function askSuggestion(question) { setDraft(question); setView('messages'); }
  const chat = <section className="customerWidget" role={embedded ? 'main' : undefined}>
    <header className="widgetHeader"><ThemeToggle /><span className="widgetMark"><Bot aria-hidden="true" /></span><div><h1>Hỗ trợ khách hàng</h1><p>{statuses[session?.status] || 'Cùng bạn tìm câu trả lời'}</p></div>
      {session && <button className="widgetEnd" onClick={end} disabled={busy || handoffBusy || historyLoading}>{session.account ? 'Chat mới' : 'Kết thúc'}</button>}</header>
    {session && <div className="widgetAccountBar"><span>{session.account ? session.account.email : 'Khách vãng lai'}{session.account && !session.account.email_verified && !embedded && <button onClick={() => setView('account')}>Xác minh email</button>}</span>{session.account ? <button onClick={logout} disabled={busy || handoffBusy || historyLoading}>Đăng xuất</button> : <button onClick={() => openAuth('login')} disabled={busy || handoffBusy || historyLoading}>Đăng nhập tài khoản</button>}</div>}
    {loading ? <p className="widgetState" role="status">Đang kết nối...</p> : !session || authMode !== 'guest' ? <section className="widgetWelcome">
      <span className="widgetEyebrow">RAG SUPPORT · KHÁCH HÀNG</span><h2>{authMode === 'register' ? 'Tạo tài khoản' : authMode === 'login' ? 'Chào mừng trở lại' : 'Bạn cần hỗ trợ điều gì?'}</h2>
      <p>{authMode === 'guest' ? 'Hỏi chính sách hoặc kết nối với nhân viên. Bạn có thể trò chuyện ngay mà không cần tài khoản.' : 'Đăng nhập để giữ lịch sử và tiếp tục trò chuyện trên nhiều thiết bị.'}</p>
      <div className="customerAuthTabs" aria-label="Cách bắt đầu">{[['guest', session ? 'Quay lại chat' : 'Khách vãng lai'], ['login', 'Đăng nhập'], ['register', 'Đăng ký']].map(([mode, label]) => <button type="button" key={mode} aria-pressed={authMode === mode} disabled={busy} onClick={() => openAuth(mode)}>{label}</button>)}</div>
      {authMode === 'guest' ? <form onSubmit={start}><label htmlFor="widgetName">Tên bạn</label><input id="widgetName" autoComplete="given-name" maxLength={80} required value={name} onChange={e => setName(e.target.value)} disabled={busy} /><button disabled={busy || !name.trim()}>{busy ? 'Đang kết nối...' : 'Bắt đầu trò chuyện'}</button><small>Tên hiển thị không xác minh danh tính. Phiên khách giữ tối đa 24 giờ.</small></form> : <form key={authMode} onSubmit={authenticate} aria-busy={busy}><fieldset disabled={busy}>
        {authMode === 'register' && <label>Tên hiển thị<input name="display_name" autoComplete="name" required maxLength={80} /></label>}
        <label>Email<input name="email" type="email" required maxLength={254} autoComplete="username" placeholder="ban@example.com" /></label>
        <label>Mật khẩu<input name="password" type="password" required minLength={authMode === 'register' ? 15 : 1} maxLength={128} autoComplete={authMode === 'register' ? 'new-password' : 'current-password'} /></label>
        {authMode === 'register' && <><label>Nhập lại mật khẩu<input name="confirm" type="password" required minLength={15} maxLength={128} autoComplete="new-password" /></label><small>Mật khẩu 15–128 ký tự. Email chưa được xác minh và không tự cấp quyền xem đơn.</small></>}
        <button>{busy ? 'Đang xử lý...' : authMode === 'register' ? 'Tạo tài khoản' : 'Đăng nhập'}</button>
      </fieldset></form>}
      {authMode === 'login' && <button type="button" onClick={() => setEmailAction({ mode: 'forgot' })}>Quên mật khẩu?</button>}{authMode !== 'guest' && <small>Xác minh email trong mục Tài khoản để dùng khôi phục mật khẩu. Lịch sử phiên khách không tự ghép vào tài khoản.</small>}
      {notice && <p role="status">{notice}</p>}{error && <div className="widgetError" role="alert"><p>{error}</p>{authMode === 'guest' && <button onClick={() => { setError(''); setRetry(n => n + 1); }} disabled={busy}>Thử kết nối lại</button>}</div>}
    </section> : <>
      <nav className="widgetHistory" aria-label="Phân trang tin nhắn" aria-busy={historyLoading}>
        <span role="status">{historyLoading ? 'Đang tải tin nhắn...' : `${messageBefore ? 'Đang xem tin cũ' : 'Tin gần nhất'} · ${session.messages.length} tin`}</span>
        <button disabled={busy || handoffBusy || historyLoading || !session.message_page.has_more} onClick={() => viewHistory([...messageCursors, session.message_page.next_before])}>Tin cũ hơn</button>
        <button disabled={busy || handoffBusy || historyLoading || messageCursors.length < 2} onClick={() => viewHistory(messageCursors.slice(0, -1))}>Tin mới hơn</button>
        {messageBefore && <button disabled={busy || handoffBusy || historyLoading} onClick={() => viewHistory([])}>Về tin mới nhất</button>}
      </nav>
      <div className="widgetLog" ref={log} role="log" tabIndex={0} aria-label="Tin nhắn hỗ trợ" aria-live={messageBefore ? 'off' : 'polite'} aria-relevant="additions" onScroll={e => {
        const el = e.currentTarget; nearBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
        setAtLatest(nearBottom.current); if (nearBottom.current) setHasNewMessages(false);
      }}>
        <p className="widgetIntro">Chào {session.display_name}. Bạn có thể hỏi về chính sách hoặc chọn Gặp nhân viên.</p>
        {session.messages.map(message => <article key={message.id} className={`widgetMessage ${message.sender_type === 'customer' ? 'widgetOwn' : ''}`}>
          <b>{senders[message.sender_type] || 'Hỗ trợ'}</b><p>{message.content}</p>
          {message.citations?.map((citation, index) => <details key={index}><summary>Nguồn: {citation.source}{citation.location && ` · ${citation.location}`}</summary><blockquote>{citation.quote}</blockquote></details>)}
        </article>)}
        {busy && pending && !session.messages.some(m => m.client_message_id === pending.client_message_id) && <article className="widgetMessage widgetOwn"><b>Bạn · Đang gửi</b><p>{pending.content}</p></article>}
        {busy && <p className="widgetIntro" role="status">Đang xử lý...</p>}
      </div>
      {!messageBefore && !atLatest && <div className="widgetLatest"><span role="status">{hasNewMessages ? 'Có tin mới' : 'Đang xem tin phía trên'}</span><button type="button" onClick={jumpLatest}>Về tin mới nhất</button></div>}
      <footer className="widgetFooter">
        <div className="widgetFooterTools" tabIndex={0} role="region" aria-label="Thao tác hội thoại">
        {!closed && <details className="widgetOrderAccess"><summary>Quyền tra cứu đơn</summary>
          <p>Nhập mã truy cập do cửa hàng cấp riêng. Không gửi mã truy cập trong tin nhắn.</p>
          {session.order_access?.map(access => <p key={access.order_id}>Đã cấp quyền: <strong>{access.order_id}</strong> đến {new Date(access.expires_at * 1000).toLocaleTimeString('vi-VN')}.</p>)}
          <form onSubmit={redeem}><fieldset disabled={busy || handoffBusy || historyLoading}><label>Mã đơn<input name="order_id" required maxLength={64} autoComplete="off" /></label>
            <label>Mã truy cập<input name="code" type="password" required minLength={43} maxLength={43} autoComplete="off" spellCheck={false} /></label>
            <button type="submit">Xác nhận quyền tra đơn</button></fieldset></form>
        </details>}
        {session.status === 'open' ? <button className="widgetHandoff" onClick={handoff} disabled={handoffBusy || historyLoading}><UserRound size={16} aria-hidden="true" />{handoffBusy ? 'Đang chuyển...' : 'Gặp nhân viên'}</button> : <p className="widgetStatus" role="status">{closed ? 'Hội thoại đã đóng. Chọn Kết thúc để bắt đầu phiên mới.' : session.status === 'resolved' ? 'Yêu cầu đã giải quyết. Nhắn tiếp nếu cần hỗ trợ thêm; yêu cầu mới sẽ chuyển vào hàng chờ nhân viên.' : session.status === 'assigned' ? 'Nhân viên đã nhận hội thoại. Bạn có thể nhắn tiếp.' : 'Đã chuyển yêu cầu. Bạn có thể để lại thêm thông tin.'} AI đã dừng trả lời.</p>}
        {notice && <p className="widgetStatus" role="status">{notice}</p>}{error && <p className="widgetError" role="alert">{error}</p>}
        {connectionError && <p className="widgetError" role="status">{connectionError}</p>}
        {!busy && pending && <div className="pendingNotice"><p className="widgetIntro" role="status">Tin trước chưa xác nhận. Gửi lại tin trước để xác nhận rồi gửi tin mới; nháp mới vẫn giữ.</p><details><summary>Xem tin chưa xác nhận</summary><p>{pending.content}</p></details><button type="button" onClick={event => send(event, true)} disabled={closed || historyLoading}>Gửi lại tin chưa xác nhận</button></div>}
        </div>
        {draftError && <p className="widgetError" role="alert">Không lưu hoặc khôi phục được nháp. Sao chép trước khi tải lại.</p>}
        <form onSubmit={send}><div className="widgetComposer"><MessageInput id="widgetDraft" aria-label="Tin nhắn của bạn" maxLength={4000} value={draft} onChange={e => setDraft(e.target.value)} disabled={closed} placeholder={closed ? 'Hội thoại đã đóng' : busy ? 'Soạn tin tiếp; chờ xử lý xong để gửi' : 'Nhập tin nhắn...'} /><button type="submit" aria-label="Gửi tin nhắn" disabled={busy || closed || historyLoading || pendingBlocksSend || !draft.trim()}><Send size={20} aria-hidden="true" /></button></div></form>
      </footer>
    </>}
  </section>;
  if (emailAction) return <CustomerEmail key={emailAction.mode + (emailAction.token || '')} action={emailAction} request={request} onBack={() => setEmailAction(null)} onComplete={emailComplete} />;
  if (embedded) return chat;
  if (!loading && (!session || authMode !== 'guest')) return <AuthLayout>
    <h1>{authMode === 'register' ? 'Tạo tài khoản của bạn' : authMode === 'login' ? 'Chào mừng trở lại!' : 'Bạn cần hỗ trợ điều gì?'}</h1>
    <p className="authLead">{authMode === 'guest' ? 'Bắt đầu trò chuyện với AI hoặc kết nối với nhân viên.' : 'Đăng nhập để lưu lịch sử và tiếp tục trò chuyện trên mọi thiết bị.'}</p>
    <div className="authTabs" aria-label="Cách bắt đầu">{[['login', 'Đăng nhập'], ['register', 'Đăng ký'], ['guest', session ? 'Quay lại chat' : 'Khách vãng lai']].map(([mode, label]) => <button type="button" key={mode} aria-pressed={authMode === mode} disabled={busy} onClick={() => openAuth(mode)}>{label}</button>)}</div>
    {authMode === 'guest' ? <form onSubmit={start}><fieldset disabled={busy}><AuthInput label="Tên bạn" name="display_name" autoComplete="given-name" maxLength={80} required value={name} onChange={e => setName(e.target.value)} placeholder="Bạn muốn được gọi là gì?" /><button className="authSubmit" disabled={busy || !name.trim()}><ArrowRight size={18} />{busy ? 'Đang kết nối...' : 'Bắt đầu trò chuyện'}</button><small>Tên hiển thị không xác minh danh tính. Phiên khách giữ tối đa 24 giờ.</small></fieldset></form> : <form key={authMode} onSubmit={authenticate} aria-busy={busy}><fieldset disabled={busy}>
      {authMode === 'register' && <AuthInput label="Tên hiển thị" name="display_name" autoComplete="name" required maxLength={80} placeholder="Nhập tên của bạn" />}
      <AuthInput label="Email" name="email" type="email" required maxLength={254} autoComplete="username" placeholder="Nhập địa chỉ email của bạn" />
      <AuthInput label="Mật khẩu" name="password" type="password" required minLength={authMode === 'register' ? 15 : 1} maxLength={128} autoComplete={authMode === 'register' ? 'new-password' : 'current-password'} placeholder={authMode === 'register' ? 'Từ 15 đến 128 ký tự' : 'Nhập mật khẩu'} />
      {authMode === 'register' && <><AuthInput label="Nhập lại mật khẩu" name="confirm" type="password" required minLength={15} maxLength={128} autoComplete="new-password" placeholder="Nhập lại mật khẩu của bạn" /><small>Email chưa được xác minh và không tự cấp quyền xem đơn. Lịch sử khách vãng lai không tự ghép vào tài khoản.</small></>}
      <button className="authSubmit"><ArrowRight size={18} />{busy ? 'Đang xử lý...' : authMode === 'register' ? 'Tạo tài khoản' : 'Đăng nhập'}</button>
    </fieldset></form>}
    {notice && <p className="authFeedback" role="status">{notice}</p>}{error && <p className="authFeedback" role="alert">{error}</p>}
    {authMode === 'login' && <button className="authBack" type="button" onClick={() => setEmailAction({ mode: 'forgot' })}>Quên mật khẩu?</button>}
    <div className="authNote"><ShieldCheck size={21} /><div>{authMode === 'guest' ? 'Trò chuyện nhanh, không cần tài khoản' : 'Lịch sử của bạn, luôn được kết nối'}<small>{authMode === 'guest' ? 'Đăng ký khi bạn muốn lưu lịch sử lâu dài và dùng trên nhiều thiết bị.' : 'Tài khoản lưu lịch sử trò chuyện. Tra cứu đơn hàng vẫn cần mã truy cập do cửa hàng cấp.'}</small></div></div>
    {authMode === 'register' && <p className="authHelp">Sau khi đăng ký, xác minh email trong mục Tài khoản để dùng khôi phục mật khẩu.</p>}
  </AuthLayout>;
  const pages = [[MessageSquare, 'Tin nhắn', 'messages'], [PackageSearch, 'Tra đơn', 'orders'], [BookOpen, 'Hỏi đáp', 'faq'], ...(session?.account ? [[History, 'Lịch sử', 'history'], [UserRound, 'Tài khoản', 'account']] : [])];
  const activeAccess = session?.order_access?.filter(access => access.expires_at > Date.now() / 1000) || [];
  return <div className="customerPortal">
    <div className="portalSide"><div className="portalBrand"><span><Bot size={19} /></span><div><b>RAG Support</b><small>Hỗ trợ khách hàng</small></div></div>
      <nav aria-label="Dịch vụ khách hàng">{pages.map(([Icon, label, key]) => <button key={key} className={view === key ? 'current' : ''} aria-current={view === key ? 'page' : undefined} onClick={() => setView(key)}><Icon size={17} />{label}</button>)}</nav>
      <div className="portalSideFoot"><ShieldCheck size={17} /><span>Tra đơn cần mã truy cập do cửa hàng cấp.</span></div>
    </div>
    <div className="portalMain" role="main"><nav className="portalMobileNav" aria-label="Dịch vụ khách hàng">{pages.map(([Icon, label, key]) => <button key={key} aria-current={view === key ? 'page' : undefined} onClick={() => setView(key)}><Icon size={16} />{label}</button>)}</nav>
      {view === 'messages' ? chat : view === 'history' && session?.account ? <CustomerHistory key={session.account.email} request={request} currentId={session.conversation_id} onExpired={() => clearIdentity('Phiên đăng nhập đã hết hạn.')} /> : view === 'account' && session?.account ? <CustomerProfile account={session.account} request={request} onExpired={() => clearIdentity('Phiên đăng nhập đã hết hạn.')} onPasswordChanged={() => clearIdentity('Đã đổi mật khẩu. Vui lòng đăng nhập lại.')} /> : view === 'orders' ? <section className="portalPage" aria-label="Tra cứu đơn hàng"><div className="portalPageHead"><span className="portalPageIcon"><PackageSearch size={22} /></span><div><h1>Tra cứu đơn hàng</h1><p>Xem trạng thái và mã vận đơn sau khi xác nhận quyền truy cập.</p></div></div>
        {!session ? <div className="portalEmpty"><p>Bắt đầu phiên trò chuyện để tra cứu đơn.</p><button onClick={() => setView('messages')}>Bắt đầu trò chuyện <ArrowRight size={16} /></button></div> : <><form className="portalOrderForm" onSubmit={event => { event.preventDefault(); inspectOrder(orderId, new FormData(event.currentTarget).get('code')); }}><label>Mã đơn<input value={orderId} onChange={event => { setOrderId(event.target.value); setOrderResult(null); }} placeholder="Ví dụ: DH12345" required minLength={6} maxLength={64} autoComplete="off" /></label>
          {!activeAccess.some(access => access.order_id === orderId.trim().toUpperCase()) && <label>Mã truy cập<input name="code" type="password" required minLength={43} maxLength={43} autoComplete="off" spellCheck={false} placeholder="Mã do cửa hàng cấp" /></label>}
          <p>Mã truy cập chỉ dùng để xác nhận quyền tra đơn. Không gửi mã trong tin nhắn.</p><button disabled={busy || orderLoading}>{orderLoading ? 'Đang tra cứu...' : 'Tra cứu đơn'}</button></form>
          {orderError && <p className="widgetError" role="alert">{orderError}</p>}
          {orderResult && activeAccess.some(access => access.order_id === orderResult.order_id) && <article className="portalOrderResult" role="status"><div><small>ĐƠN HÀNG</small><h2>{orderResult.order_id}</h2></div><span>{orderStatuses[orderResult.status] || orderResult.status}</span><dl><dt>Trạng thái</dt><dd>{orderStatuses[orderResult.status] || orderResult.status}</dd><dt>Mã vận đơn</dt><dd>{orderResult.tracking_code || 'Chưa có mã vận đơn'}</dd></dl></article>}
          {activeAccess.length > 0 && <div className="portalAccess"><h2>Đơn đã cấp quyền</h2>{activeAccess.map(access => <button key={access.order_id} onClick={() => { setOrderId(access.order_id); inspectOrder(access.order_id, ''); }}>{access.order_id}<ArrowRight size={16} /></button>)}</div>}</>}
      </section> : <section className="portalPage" aria-label="Hỏi đáp chính sách"><div className="portalPageHead"><span className="portalPageIcon"><BookOpen size={22} /></span><div><h1>Hỏi đáp chính sách</h1><p>Đặt câu hỏi cho trợ lý AI. Câu trả lời sẽ kèm trích nguồn khi tìm được tài liệu.</p></div></div><div className="portalQuestions"><h2>Gợi ý câu hỏi</h2>{suggestions.map(question => <button key={question} onClick={() => askSuggestion(question)}>{question}<ArrowRight size={17} /></button>)}</div><div className="portalEmpty"><p>Không thấy câu hỏi phù hợp? Nhập câu hỏi của bạn trong Tin nhắn.</p><button onClick={() => setView('messages')}>Mở trò chuyện <ArrowRight size={16} /></button></div></section>}
    </div>
    <div className="portalContext"><h2>Phiên hỗ trợ</h2><div className="portalPerson"><span><UserRound size={20} /></span><div><b>{session?.display_name || 'Khách hàng'}</b><small>{session?.account ? 'Đã đăng nhập tài khoản' : session ? 'Khách vãng lai · ' + statuses[session.status] : 'Chưa bắt đầu phiên'}</small></div></div><div className="portalContextBlock"><h3>Kênh hỗ trợ</h3><p>Website Chat</p></div><div className="portalContextBlock"><h3>Đơn được tra cứu</h3>{activeAccess.length ? activeAccess.map(access => <button key={access.order_id} onClick={() => { setOrderId(access.order_id); setView('orders'); inspectOrder(access.order_id, ''); }}>{access.order_id}<ArrowRight size={15} /></button>) : <p>Chưa có đơn được cấp quyền.</p>}</div><div className="portalContextBlock"><h3>Cần thêm hỗ trợ?</h3><p>Trò chuyện cùng AI hoặc yêu cầu gặp nhân viên.</p><button onClick={() => setView('messages')}>Vào Tin nhắn <ArrowRight size={15} /></button></div></div>
  </div>;
}
