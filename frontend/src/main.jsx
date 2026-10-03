import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Inbox, BookOpen, Package, BarChart3, Settings, Search, UserRound, Bot } from 'lucide-react';
import './styles.css';
import KnowledgeBase, { Citations } from './KnowledgeBase';
import Widget from './Widget';
import Workspace from './Workspace';
import './admin-theme.css';
import AuthLayout, { AuthInput } from './AuthLayout';

const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '');
const statuses = { open: 'Đang mở', handoff_requested: 'Chờ nhân viên', assigned: 'Đã tiếp nhận', closed: 'Đã đóng', resolved: 'Đã giải quyết' };
const priorities = { normal: 'Bình thường', high: 'Cao', urgent: 'Khẩn cấp', low: 'Thấp' };
const slaStatuses = { on_track: 'Trong hạn', overdue: 'Quá hạn chờ phản hồi', met: 'Đã phản hồi đúng hạn', breached: 'Đã phản hồi trễ', cancelled: 'Kết thúc trước phản hồi', none: 'Chưa có SLA' };
const senders = { customer: 'Khách hàng', ai: 'RAG AI', assistant: 'RAG AI', agent: 'Nhân viên', system: 'Hệ thống' };
const pages = [[Inbox, 'Tổng quan', 'overview'], [Inbox, 'Hội thoại', 'inbox'], [UserRound, 'Khách hàng', 'customers'], [Package, 'Đơn hàng', 'orders'], [BookOpen, 'Kho tri thức', 'knowledge'], [BarChart3, 'Phân tích', 'analytics'], [Settings, 'Cài đặt', 'settings']];
const nameOf = c => c.customer_name || c.customer_id;
const initials = name => name.trim().split(/\s+/).slice(-2).map(word => word[0]).join('').toUpperCase();
function timeOf(value) {
  if (!value) return '';
  const date = new Date(/[zZ]$|[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`);
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString('vi-VN');
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}/api/v1${path}`, { ...options, credentials: 'same-origin', headers: { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), 'X-CSRF-Protection': '1', ...options.headers } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(response.status === 401 ? 'Phiên đăng nhập hết hạn hoặc thông tin đăng nhập không đúng.' : response.status === 403 ? 'Tài khoản không có quyền thực hiện thao tác.' : response.status === 429 ? 'Thử đăng nhập quá nhiều lần. Chờ một phút rồi thử lại.' : typeof data.detail === 'string' ? data.detail : `Yêu cầu thất bại (HTTP ${response.status}).`);
    error.status = response.status;
    throw error;
  }
  if (!response.headers.get('content-type')?.includes('application/json')) throw new Error('API trả về sai định dạng. Kiểm tra cấu hình proxy.');
  return data;
}

const getInbox = (path, signal) => request(`/inbox/conversations${path}`, { signal, cache: 'no-store' });
function SlaBadge({ value }) {
  return <span className={`slaBadge sla-${value?.status || 'none'}`}>{slaStatuses[value?.status || 'none']}</span>;
}

function ToolTrace({ trace }) {
  if (!trace || typeof trace !== 'object' || Array.isArray(trace)) return null;
  const states = {
    __proto__: null,
    pending: ['Chưa có kết quả', 'Tin khách đã lưu. Xử lý có thể đang chạy hoặc đã bị gián đoạn; đọc lịch sử trước khi thử lại.'],
    clarification: ['Cần chọn một mã đơn', 'Tin nhắn có nhiều mã đơn; chưa gọi công cụ tra cứu.'],
    executed: ['Đã xử lý công cụ', 'Kết quả bên dưới thuộc lượt xử lý tin này, không phải trạng thái đơn hiện tại.'],
    rag: ['Chuyển sang hỏi chính sách', 'Đã chọn luồng RAG; xem câu trả lời và nguồn trong lịch sử để biết kết quả.'],
    provider_error: ['Lỗi dịch vụ AI', 'Tin khách đã lưu nhưng lượt chọn công cụ hoặc hỏi chính sách gặp lỗi.'],
    skipped: ['Bỏ qua lượt xử lý cũ', 'Có tin mới hoặc trạng thái hội thoại đã đổi trước khi thực thi công cụ.'],
  };
  const [status, note] = states[trace.status] || ['Chưa xác định', 'Chưa có mô tả cho trạng thái nhật ký này.'];
  const tool = ({__proto__:null, lookup_order:'Tra cứu đơn hàng', handoff:'Chuyển nhân viên', rag:'Hỏi chính sách'})[trace.tool];
  const outcome = ({__proto__:null, found:'Tìm thấy đơn trong phạm vi được phép', not_found_or_not_owned:'Không tìm thấy đơn hoặc chưa có quyền tra cứu; chuyển nhân viên'})[trace.outcome];
  return <details className="toolTrace"><summary>Nhật ký công cụ · {status}</summary>
    <p>{note}</p><dl>
      {typeof trace.order_id === 'string' && <><dt>Mã đơn</dt><dd>{trace.order_id.slice(0, 64)}</dd></>}
      {tool && <><dt>Hành động</dt><dd>{tool}</dd></>}
      {outcome && <><dt>Kết quả</dt><dd>{outcome}</dd></>}
    </dl><small>Chỉ nhân viên xem được. Mục này không chạy lại công cụ.</small>
  </details>;
}

function DeliveryState({ message, canRetry, onExpired, onRetried }) {
  const [confirmed, setConfirmed] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const delivery = message.delivery;
  if (!delivery) return null;
  const uncertain = delivery.state === 'uncertain';
  async function retry(action) {
    setBusy(true); setError('');
    try {
      await request(`/inbox/messages/${encodeURIComponent(message.id)}/retry-delivery`, {method:'POST', body:JSON.stringify({confirm_uncertain:confirmed,action})});
      setConfirmed(false); onRetried();
    } catch (e) { setError(e.message); if (e.status === 401) onExpired(); }
    finally { setBusy(false); }
  }
  return <div className="deliveryState"><small>{({pending:'Chờ gửi Telegram',sending:'Đang gửi Telegram',sent:'Telegram đã nhận',failed:'Gửi Telegram thất bại',uncertain:'Chưa rõ Telegram đã nhận hay chưa',skipped:'Đã bỏ qua gửi Telegram'})[delivery.state]}</small>
    {canRetry && ['failed','uncertain'].includes(delivery.state) && <>{uncertain && <label><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)} />Đã kiểm tra; chấp nhận nguy cơ gửi trùng.</label>}<button disabled={busy || uncertain && !confirmed} onClick={()=>retry('retry')}>Gửi lại Telegram</button><button disabled={busy} onClick={()=>retry('skip')}>Bỏ qua gửi</button></>}
    {error && <p role="alert">{error}</p>}
  </div>;
}

function SessionGate() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    request('/auth/me', { signal: controller.signal }).then(setUser)
      .catch(error => { if (!controller.signal.aborted && error.status !== 401) setError(error.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, []);
  async function login(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    setBusy(true); setError('');
    try {
      const data = await request('/auth/login', { method: 'POST', body: JSON.stringify({ username: values.get('username'), password: values.get('password') }) });
      form.reset(); setUser(data);
    } catch (error) { setError(error.message); }
    finally { setBusy(false); }
  }
  async function logout() {
    setBusy(true); setError('');
    try { await request('/auth/logout', { method: 'POST' }); setUser(null); }
    catch (error) { setError(error.message); }
    finally { setBusy(false); }
  }
  if (loading) return <p className="state" role="status">Đang kiểm tra phiên đăng nhập...</p>;
  if (user) return <App user={user} onExpired={(message = '') => { setUser(null); setError(message); }} onLogout={logout} logoutBusy={busy} sessionError={error} />;
  return <AuthLayout staff><h1>Chào mừng trở lại!</h1><p className="authLead">Đăng nhập để tiếp tục sử dụng nền tảng AI hỗ trợ khách hàng.</p>
    <form onSubmit={login} aria-busy={busy}><fieldset disabled={busy}><AuthInput label="Tên đăng nhập" name="username" autoComplete="username" required maxLength={64} pattern="[a-zA-Z0-9_.-]+" placeholder="Nhập tên đăng nhập nhân viên" /><AuthInput label="Mật khẩu" name="password" type="password" autoComplete="current-password" required maxLength={128} placeholder="Nhập mật khẩu" />
      {error && <p className="authFeedback" role="alert">{error}</p>}<button className="authSubmit">{busy ? 'Đang đăng nhập...' : 'Đăng nhập'}</button></fieldset></form>
    <details className="authHelp"><summary>Quên mật khẩu?</summary><p>Liên hệ quản trị viên để được đặt lại mật khẩu tài khoản nhân viên.</p></details>
    <div className="authNote"><UserRound size={22} /><div>Chưa có tài khoản?<small>Liên hệ quản trị viên để được cấp quyền truy cập.</small></div></div>
  </AuthLayout>;
}

function App({ user, onExpired, onLogout, logoutBusy, sessionError }) {
  const [page, setPage] = useState('inbox');
  const [customerFilter, setCustomerFilter] = useState('');
  const [conversations, setConversations] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [messageHistory, setMessageHistory] = useState({ id: null, cursors: [] });
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [sla, setSla] = useState('');
  const [search, setSearch] = useState('');
  const [offset, setOffset] = useState(0);
  const [listMeta, setListMeta] = useState({ total: 0, has_more: false });
  const pageSize = 25;
  const [listLoading, setListLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [listError, setListError] = useState('');
  const [detailError, setDetailError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [detailRetry, setDetailRetry] = useState(0);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState('');
  const [drafts, setDrafts] = useState({});
  const [completionNotes, setCompletionNotes] = useState({});
  const [lastUpdated, setLastUpdated] = useState(null);
  const pendingReplies = useRef({});

  useEffect(() => {
    if (page !== 'inbox' || actionLoading) return;
    const controller = new AbortController();
    let timer;
    setListLoading(true);
    setListError('');
    async function load(first = false) {
      if (first || !document.hidden) {
        try {
          const data = await getInbox(`?${new URLSearchParams({ offset, limit: pageSize, q: search.trim(), ...(status && { status }), ...(priority && { priority }), ...(sla && { sla }) })}`, controller.signal);
          if (controller.signal.aborted) return;
          if (!Array.isArray(data.conversations) || !Number.isInteger(data.total) || data.total < 0 || data.conversations.some(c => typeof c.conversation_id !== 'string' || typeof c.customer_id !== 'string')) throw new Error('Dữ liệu danh sách không hợp lệ.');
          if (offset > 0 && offset >= data.total) {
            setOffset(Math.max(0, Math.floor((data.total - 1) / pageSize) * pageSize));
            return;
          }
          setConversations(data.conversations);
          setListMeta({ total: data.total, has_more: data.has_more });
          setSelectedId(id => id || data.conversations[0]?.conversation_id || null);
          setListError(''); setLastUpdated(new Date().toISOString());
        } catch (error) {
          if (!controller.signal.aborted) { if (error.status === 401) onExpired(); setListError(error.message || 'Không kết nối được backend.'); }
        } finally { if (!controller.signal.aborted) setListLoading(false); }
      }
      if (!controller.signal.aborted) timer = setTimeout(load, 3000);
    }
    load(true);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [status, priority, sla, search, offset, refresh, page, actionLoading]);

  const visibleChats = conversations;
  const activeId = selectedId;
  const messageCursors = messageHistory.id === activeId ? messageHistory.cursors : [];
  const messageBefore = messageCursors.at(-1) || null;
  const selected = conversations.find(c => c.conversation_id === activeId) || (detail?.conversation_id === activeId ? detail : null);
  const draft = drafts[activeId] || '';

  useEffect(() => {
    if (page !== 'inbox' || actionLoading) return;
    const controller = new AbortController();
    let timer;
    setDetail(previous => previous?.conversation_id === activeId && previous.message_page.before === messageBefore ? previous : null);
    setDetailError('');
    setDetailLoading(Boolean(activeId));
    async function load(first = false) {
      if (first || !document.hidden) {
        try {
          const data = await getInbox(`/${encodeURIComponent(activeId)}?${new URLSearchParams({ limit: 50, ...(messageBefore && { before: messageBefore }) })}`, controller.signal);
          if (controller.signal.aborted) return;
          if (data.conversation_id !== activeId || !Array.isArray(data.messages) || !Array.isArray(data.tickets) || data.message_page?.before !== messageBefore) throw new Error('Dữ liệu hội thoại không hợp lệ.');
          setDetail(data); setDetailError('');
        } catch (error) {
          if (!controller.signal.aborted) { if (error.status === 401) onExpired(); setDetailError(error.message || 'Không tải được hội thoại.'); }
        } finally { if (!controller.signal.aborted) setDetailLoading(false); }
      }
      if (!controller.signal.aborted) timer = setTimeout(load, 3000);
    }
    if (activeId) load(true);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [activeId, messageBefore, detailRetry, page, actionLoading]);

  // Ignore previous customer's detail before effect cleanup runs.
  const current = detail?.conversation_id === activeId && detail.message_page.before === messageBefore ? detail : null;
  const canReply = current?.status === 'assigned' && current.assigned_agent_id === user.id;
  const activeTicket = current?.tickets.find(ticket => ['open', 'assigned'].includes(ticket.status));
  const completionNote = completionNotes[activeId] || '';
  async function postAction(path, body) {
    const targetId = activeId;
    setActionLoading(true); setActionError('');
    try {
      const data = await request(`/inbox/conversations/${encodeURIComponent(targetId)}${path}`, { method: 'POST', body: JSON.stringify(body) });
      setDetailRetry(n => n + 1); setRefresh(n => n + 1); return data;
    } catch (error) { if (error.status === 401) onExpired(); setActionError({ id: targetId, message: error.message || 'Không thể thực hiện thao tác.' }); if (error.status === 409) { setDetailRetry(n => n + 1); setRefresh(n => n + 1); } return null; }
    finally { setActionLoading(false); }
  }
  async function acceptConversation() { await postAction('/accept', undefined); }
  async function finishConversation(event) {
    event.preventDefault();
    if (!canReply || !activeTicket || actionLoading || messageBefore || !completionNote.trim()) return;
    const nextStatus = event.nativeEvent.submitter?.value || 'resolved';
    const message = nextStatus === 'resolved'
      ? 'Đánh dấu đã giải quyết? Khách nhắn tiếp sẽ tạo ticket mới vào hàng chờ. AI vẫn dừng.'
      : 'Đóng hội thoại? Khách không thể nhắn tiếp trong hội thoại này, nhưng có thể bắt đầu phiên mới. Lịch sử được giữ.';
    if (!window.confirm(message)) return;
    const targetId = activeId;
    const result = await postAction('/finish', { status: nextStatus, ticket_id: activeTicket.id,
      last_customer_message_id: current.last_customer_message_id, note: completionNote.trim() });
    if (result) setCompletionNotes(previous => previous[targetId] === completionNote ? { ...previous, [targetId]: '' } : previous);
  }
  async function sendReply(event) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || !activeId || !canReply || actionLoading) return;
    const targetId = activeId;
    if (pendingReplies.current[targetId]?.content !== content) pendingReplies.current[targetId] = {content, client_message_id:crypto.randomUUID()};
    if (await postAction('/messages', pendingReplies.current[targetId])) {
      delete pendingReplies.current[targetId];
      setMessageHistory({ id: targetId, cursors: [] });
      setDrafts(previous => previous[targetId] === draft ? { ...previous, [targetId]: '' } : previous);
    }
  }
  const counts = [listMeta.total, visibleChats.filter(c => c.status === 'open').length, visibleChats.filter(c => c.status === 'handoff_requested').length, visibleChats.filter(c => c.sla?.status === 'overdue').length];
  function changeFilter(setter, value) { setter(value); setOffset(0); }
  function navigate(target) { setCustomerFilter(''); setPage(target); }
  function openInbox(id) { setStatus(''); setPriority(''); setSla(''); setSearch(''); setOffset(0); setSelectedId(id); setPage('inbox'); }
  return <div className="shell">
    <aside aria-label="Điều hướng chính">
      <div className="brand"><span className="brandLogo"><Bot aria-hidden="true" /></span><b>RAG</b><small>Support Hub</small></div>
      {pages.map(([Icon, label, target]) =>
        <button key={target} className={`nav ${page === target ? 'active' : ''}`} onClick={() => navigate(target)} aria-current={page === target ? 'page' : undefined}><Icon size={17} />{label}{target === 'inbox' && <em>{listLoading || listError ? '—' : listMeta.total}</em>}</button>)}
      <div className="agent"><div className="avatar"><UserRound size={18} /></div><div><b>{user.display_name}</b><small>{user.role === 'admin' ? 'Quản trị viên' : 'Nhân viên hỗ trợ'}</small></div></div>
    </aside>
    <main>
      <div className="sessionBar"><span>{user.display_name}</span><button onClick={onLogout} disabled={logoutBusy}>{logoutBusy ? 'Đang đăng xuất...' : 'Đăng xuất'}</button></div>
      {sessionError && <p role="alert">{sessionError}</p>}
      <nav className="mobileNav" aria-label="Điều hướng">{pages.map(([, label, target]) => <button key={target} aria-pressed={page === target} onClick={() => navigate(target)}>{label}</button>)}</nav>
      {page === 'knowledge' ? <KnowledgeBase user={user} request={request} onExpired={onExpired} /> : page !== 'inbox' ? <Workspace key={`${page}-${customerFilter}`} page={page} user={user} request={request} onExpired={onExpired} navigate={navigate} openInbox={openInbox} customerFilter={customerFilter} openOrders={id => { setCustomerFilter(id); setPage('orders'); }} /> : <>
      <header><div><h1>Hộp thư đa kênh</h1><p>Quản lý hội thoại, tin nhắn và yêu cầu hỗ trợ tập trung</p></div><label className="search"><Search size={16} /><input aria-label="Tìm kiếm hội thoại" placeholder="Tìm khách hàng, kênh..." maxLength={160} value={search} onChange={e => changeFilter(setSearch, e.target.value)} /></label></header>
      <p className="syncNote">Tự cập nhật mỗi 3 giây khi đang xem Inbox. Giữ hội thoại đang xem khi đổi trang hoặc bộ lọc.{lastUpdated && ` Danh sách cập nhật: ${timeOf(lastUpdated)}.`}</p>
      <div className="stats">{['Tổng hội thoại trong bộ lọc', 'Đang mở · trang này', 'Chờ nhân viên · trang này', 'Quá hạn · trang này'].map((label, i) => <div key={label}><b>{listLoading || listError ? '—' : counts[i]}</b><small>{label}</small></div>)}</div>
      <section className="workspace">
        <div className="list" aria-label="Danh sách hội thoại" aria-busy={listLoading}>
          <div className="listHead"><b>Hội thoại</b><button onClick={() => { setRefresh(n => n + 1); setDetailRetry(n => n + 1); }} disabled={listLoading || actionLoading}>Làm mới</button></div>
          <div className="filters"><label>Trạng thái<select value={status} onChange={e => changeFilter(setStatus, e.target.value)}><option value="">Tất cả</option>{Object.entries(statuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Ưu tiên<select value={priority} onChange={e => changeFilter(setPriority, e.target.value)}><option value="">Tất cả</option>{Object.entries(priorities).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div>
          <label className="slaFilter">SLA phản hồi đầu tiên<select value={sla} onChange={e => changeFilter(setSla, e.target.value)}><option value="">Tất cả</option>{Object.entries(slaStatuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <nav className="inboxPages" aria-label="Phân trang hội thoại">
            <span role="status">{listLoading || listError ? 'Đang cập nhật danh sách' : `${listMeta.total ? offset + 1 : 0}–${offset + conversations.length} / ${listMeta.total} hội thoại`}</span>
            <button disabled={!offset || listLoading || actionLoading} onClick={() => setOffset(n => Math.max(0, n - pageSize))}>Trang trước</button>
            <button disabled={!listMeta.has_more || listLoading || actionLoading || Boolean(listError)} onClick={() => setOffset(n => n + pageSize)}>Trang sau</button>
          </nav>
          {listError && <div className="state" role="alert"><p>{listError} Dữ liệu có thể đã cũ; đang thử kết nối lại.</p><button onClick={() => setRefresh(n => n + 1)}>Thử lại</button></div>}
          {listLoading ? <p className="state" role="status">Đang tải danh sách...</p> : !visibleChats.length ? !listError && <p className="state" role="status">Không có hội thoại phù hợp.</p> : visibleChats.map(c =>
            <button key={c.conversation_id} aria-pressed={activeId === c.conversation_id} onClick={() => setSelectedId(c.conversation_id)} className={`chat ${activeId === c.conversation_id ? 'selected' : ''}`}><span className="avatar">{initials(nameOf(c))}</span><span className="chatText"><b>{nameOf(c)}</b><small>{c.channel} · {statuses[c.status] || c.status}</small><i>{priorities[c.priority] || c.priority}</i><SlaBadge value={c.sla} /><small>{timeOf(c.created_at)}</small></span></button>)}
        </div>
        <div className="conversation" aria-label="Chi tiết hội thoại" aria-busy={detailLoading}>
          {selected && <div className="convHead"><div className="avatar big">{initials(nameOf(selected))}</div><div><b>{nameOf(selected)}</b><small>{selected.channel} · {statuses[current?.status || selected.status]}</small></div>{current?.status === 'handoff_requested' && <button onClick={acceptConversation} disabled={actionLoading || listLoading}>Tiếp nhận</button>}</div>}
          {current && ['handoff_requested', 'assigned'].includes(current.status) && <p className="handoff" role="status">AI đã dừng. {current.status === 'handoff_requested' ? 'Đang chờ nhân viên tiếp nhận.' : canReply ? 'Bạn đang phụ trách hội thoại.' : 'Nhân viên khác đang phụ trách hội thoại.'}</p>}
          {current?.sla && <p className="slaSummary"><SlaBadge value={current.sla} /> Hạn phản hồi: {timeOf(current.sla.due_at)} · {current.sla.target_minutes} phút từ lúc tạo ticket (24/7).</p>}
          {detailError && <div className="state" role="alert"><p>{detailError} Dữ liệu có thể đã cũ; đang thử kết nối lại.</p><button onClick={() => setDetailRetry(n => n + 1)}>Thử lại</button></div>}
          {activeId && <nav className="messagePagination" aria-label="Phân trang tin nhắn">
            <span role="status">{messageBefore ? 'Đang xem tin cũ' : 'Tin gần nhất'}{current && ` · ${current.messages.length} tin`}</span>
            <button disabled={!current?.message_page.has_more || detailLoading || actionLoading} onClick={() => setMessageHistory({ id: activeId, cursors: [...messageCursors, current.message_page.next_before] })}>Tin cũ hơn</button>
            <button disabled={messageCursors.length < 2 || detailLoading || actionLoading} onClick={() => setMessageHistory({ id: activeId, cursors: messageCursors.slice(0, -1) })}>Tin mới hơn</button>
            {messageBefore && <button onClick={() => setMessageHistory({ id: activeId, cursors: [] })}>Về tin mới nhất</button>}
          </nav>}
          <div className="messages" key={`${activeId}:${messageBefore || ''}`} tabIndex={0} role="region" aria-label="Lịch sử tin nhắn">
            {!activeId ? <p className="state">Chọn hội thoại để xem nội dung.</p> : !current ? <p className="state" role="status">{detailError ? 'Chưa tải được hội thoại.' : 'Đang tải hội thoại...'}</p> : <>
              {!current.messages.length && <p className="state">Hội thoại chưa có tin nhắn.</p>}
              {current.messages.map(m => <div key={m.id} className={`bubble ${m.sender_type === 'customer' ? 'customer' : m.sender_type === 'agent' ? 'staff' : 'ai'}`}><b>{senders[m.sender_type] || m.sender_type}</b><div className="messageContent">{m.content}</div>{m.citations?.length > 0 && <Citations citations={m.citations} request={request} />}<time>{timeOf(m.created_at)}</time><ToolTrace trace={m.tool_trace} /><DeliveryState message={m} canRetry={current.assigned_agent_id === user.id} onExpired={onExpired} onRetried={() => setDetailRetry(n=>n+1)} /></div>)}
              <section className="tickets" aria-label="Ticket hỗ trợ"><h3>Ticket hỗ trợ ({current.tickets.length})</h3>{!current.tickets.length ? <p>Chưa có ticket hỗ trợ.</p> : current.tickets.map(t => <article key={t.id} className="ticket"><b>{statuses[t.status] || t.status} · {priorities[t.priority] || t.priority}</b><p>{t.summary || 'Chưa có tóm tắt.'}</p><SlaBadge value={t.sla} />{t.sla && <p>Hạn: {timeOf(t.sla.due_at)}{t.sla.responded_at && <><br />Phản hồi đầu: {timeOf(t.sla.responded_at)}</>}</p>}{t.completed_at && <p>Hoàn tất: {timeOf(t.completed_at)} · {t.completed_by_name || 'Khách hàng'}</p>}{t.completion_note && <p className="completionNote"><b>Ghi chú nội bộ:</b> {t.completion_note}</p>}<small>#{t.id} · {timeOf(t.created_at)}</small></article>)}</section>
            </>}
          </div>
          {current && <form className="composer" onSubmit={sendReply}><input aria-label="Tin nhắn nhân viên" value={draft} onChange={e => setDrafts(previous => ({ ...previous, [activeId]: e.target.value }))} disabled={!canReply || actionLoading} placeholder={canReply ? 'Nhập phản hồi cho khách hàng...' : 'Chỉ nhân viên phụ trách được trả lời'} maxLength={4000} /><button type="submit" disabled={!canReply || !draft.trim() || actionLoading}>Gửi</button></form>}
          {canReply && activeTicket && <form className="completionForm" onSubmit={finishConversation}>
            <label htmlFor="completionNote">Ghi chú hoàn tất (nội bộ)</label>
            <textarea id="completionNote" rows={2} maxLength={2000} required value={completionNote} onChange={e => setCompletionNotes(previous => ({ ...previous, [activeId]: e.target.value }))} disabled={actionLoading} />
            <small>{messageBefore ? 'Về tin mới nhất và đọc trước khi hoàn tất.' : 'Áp dụng cho các ticket đang xử lý. Khách chỉ nhận thông báo trạng thái.'}</small>
            <div><button value="resolved" disabled={actionLoading || Boolean(messageBefore) || !completionNote.trim()}>Giải quyết</button><button value="closed" disabled={actionLoading || Boolean(messageBefore) || !completionNote.trim()}>Đóng hội thoại</button></div>
          </form>}
          {actionError?.id === activeId && <p className="state" role="alert">{actionError.message}</p>}
        </div>
        <div className="profile"><h3>Thông tin khách hàng</h3>{current ? <><div className="profileUser"><div className="avatar big">{initials(nameOf(current))}</div><div><b>{nameOf(current)}</b><small>{current.customer_id}</small></div></div><p>{current.customer_email || 'Chưa có email'}</p><hr /><h4>Hội thoại</h4><p>Kênh: {current.channel}</p><p>Trạng thái: {statuses[current.status] || current.status}</p><p>Ưu tiên: {priorities[current.priority] || current.priority}</p><h4>Ticket hỗ trợ</h4><p>{current.tickets.length} ticket</p></> : <p>Thông tin xuất hiện khi tải xong hội thoại.</p>}</div>
      </section>
      </>}
    </main>
  </div>;
}

createRoot(document.getElementById('root')).render(window.location.pathname === '/chat' ? <Widget /> : <SessionGate />);
