import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Inbox, BookOpen, Package, BarChart3, Settings, Search, UserRound, Bot, LayoutDashboard, MessageSquare, PanelRight, SlidersHorizontal, RefreshCw, ChevronLeft, ChevronRight, LogOut, Send, CheckCheck, X, Globe, Clock3, ArrowUpRight, ShieldCheck } from 'lucide-react';
import './styles.css';
import KnowledgeBase, { Citations } from './KnowledgeBase';
import Widget from './Widget';
import MessageInput from './MessageInput';
import Workspace from './Workspace';
import './admin-theme.css';
import AuthLayout, { AuthInput } from './AuthLayout';
import { ThemeProvider, ThemeToggle, useTheme } from './Theme';
import { useNavigation } from './navigation';
import { clearDrafts, useDrafts } from './drafts';
import { Mail } from 'lucide-react';

const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '');
const statuses = { open: 'Đang mở', handoff_requested: 'Chờ nhân viên', assigned: 'Đã tiếp nhận', closed: 'Đã đóng', resolved: 'Đã giải quyết' };
const priorities = { normal: 'Bình thường', high: 'Cao', urgent: 'Khẩn cấp', low: 'Thấp' };
const slaStatuses = { on_track: 'Trong hạn', overdue: 'Quá hạn chờ phản hồi', met: 'Đã phản hồi đúng hạn', breached: 'Đã phản hồi trễ', cancelled: 'Kết thúc trước phản hồi', none: 'Chưa có SLA' };
const senders = { customer: 'Khách hàng', ai: 'RAG AI', assistant: 'RAG AI', agent: 'Nhân viên', system: 'Hệ thống' };
const pages = [[LayoutDashboard, 'Tổng quan', 'overview'], [Inbox, 'Hội thoại', 'inbox'], [UserRound, 'Khách hàng', 'customers'], [Package, 'Đơn hàng', 'orders'], [BookOpen, 'Kho tri thức', 'knowledge'], [BarChart3, 'Phân tích', 'analytics'], [Settings, 'Cài đặt', 'settings']];
const channelName = channel => ({ website: 'Website', telegram: 'Telegram' })[channel] || channel;
const nameOf = c => c.customer_name || c.customer_id;
const initials = name => name.trim().split(/\s+/).slice(-2).map(word => word[0]).join('').toUpperCase();
function timeOf(value) {
  if (!value) return '';
  const date = new Date(/[zZ]$|[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`);
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString('vi-VN');
}

function shortTime(value) {
  if (!value) return '';
  const date = new Date(/[zZ]$|[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`);
  if (Number.isNaN(date.getTime())) return '';
  return date.toDateString() === new Date().toDateString()
    ? date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
    : date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
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
    try { await request('/auth/logout', { method: 'POST' }); clearDrafts(`staff:${user.id}`); setUser(null); }
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
  const { theme } = useTheme();
  const themeButton = <ThemeToggle />;
  const [route, updateNavigation] = useNavigation();
  const { page, customerFilter, selectedId, status, assignment, mobileConversation, priority, sla, search, offset, unreadOnly } = route;
  const [conversations, setConversations] = useState([]);
  const [detail, setDetail] = useState(null);
  const setSelectedId = value => updateNavigation({ selectedId: value });
  const setStatus = value => updateNavigation({ status: value });
  const setAssignment = value => updateNavigation({ assignment: value });
  const setPriority = value => updateNavigation({ priority: value });
  const setSla = value => updateNavigation({ sla: value });
  const setSearch = value => updateNavigation({ search: value });
  const setOffset = value => updateNavigation({ offset: value });
  const [messageHistory, setMessageHistory] = useState({ id: null, cursors: [] });
  const [profileOpen, setProfileOpen] = useState(() => window.matchMedia('(min-width: 1280px)').matches);
  const messageLog = useRef(null);
  const profileToggle = useRef(null);
  const profilePanel = useRef(null);
  const [profileModal, setProfileModal] = useState(() => window.matchMedia('(max-width: 1279px)').matches);
  const ProfilePanel = profileModal ? 'dialog' : 'section';
  const followMessages = useRef(true);
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
  const [savedDrafts, saveDrafts, draftError] = useDrafts(`staff:${user.id}`);
  const drafts = savedDrafts.drafts, completionNotes = savedDrafts.notes;
  const setDrafts = change => saveDrafts(previous => ({ ...previous, drafts: typeof change === 'function' ? change(previous.drafts) : change }));
  const setCompletionNotes = change => saveDrafts(previous => ({ ...previous, notes: typeof change === 'function' ? change(previous.notes) : change }));
  const [lastUpdated, setLastUpdated] = useState(null);
  const pendingReplies = useRef({ ...savedDrafts.pending });
  const readMessages = useRef({});
  const readInFlight = useRef({});
  const readPaused = useRef(null);
  const [readError, setReadError] = useState('');
  const [atLatest, setAtLatest] = useState(true);

  useEffect(() => {
    const media = window.matchMedia('(max-width: 1279px)');
    const change = () => { setProfileModal(media.matches); if (media.matches) setProfileOpen(false); };
    media.addEventListener('change', change);
    return () => media.removeEventListener('change', change);
  }, []);
  useEffect(() => {
    const panel = profilePanel.current;
    if (!profileModal || !profileOpen || page !== 'inbox' || !panel ||
        (window.matchMedia('(max-width: 760px)').matches && !mobileConversation)) return;
    panel.showModal();
    return () => { panel.close(); profileToggle.current?.focus(); };
  }, [profileModal, profileOpen, page, mobileConversation]);

  useEffect(() => {
    if (![...Object.values(drafts), ...Object.values(completionNotes)].some(value => value.trim())) return;
    const warn = event => { event.preventDefault(); event.returnValue = ''; };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [drafts, completionNotes]);

  useEffect(() => {
    if (page !== 'inbox' || actionLoading) return;
    const controller = new AbortController();
    let timer;
    setListLoading(true);
    setListError('');
    async function load(first = false) {
      if (first || !document.hidden) {
        try {
          const data = await getInbox(`?${new URLSearchParams({ offset, limit: pageSize, assignment, unread_only: unreadOnly, q: search.trim(), ...(status && { status }), ...(priority && { priority }), ...(sla && { sla }) })}`, controller.signal);
          if (controller.signal.aborted) return;
          if (!Array.isArray(data.conversations) || !Number.isInteger(data.total) || data.total < 0 || data.conversations.some(c => typeof c.conversation_id !== 'string' || typeof c.customer_id !== 'string')) throw new Error('Dữ liệu danh sách không hợp lệ.');
          if (offset > 0 && offset >= data.total) {
            setOffset(Math.max(0, Math.floor((data.total - 1) / pageSize) * pageSize));
            return;
          }
          setConversations(data.conversations);
          setListMeta({ total: data.total, has_more: data.has_more });
          setSelectedId(id => id || (!unreadOnly && data.conversations[0]?.conversation_id) || null);
          setListError(''); setLastUpdated(new Date().toISOString());
        } catch (error) {
          if (!controller.signal.aborted) { if (error.status === 401) onExpired(); setListError(error.message || 'Không kết nối được backend.'); }
        } finally { if (!controller.signal.aborted) setListLoading(false); }
      }
      if (!controller.signal.aborted) timer = setTimeout(load, 3000);
    }
    load(true);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [status, assignment, priority, sla, search, offset, unreadOnly, refresh, page, actionLoading]);

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
  useLayoutEffect(() => {
    followMessages.current = true;
    setAtLatest(true);
  }, [activeId, page, messageBefore]);
  useLayoutEffect(() => {
    const log = messageLog.current;
    if (log && current && followMessages.current) log.scrollTop = messageBefore ? 0 : log.scrollHeight;
  }, [current?.messages.at(-1)?.id, activeId, page, messageBefore, mobileConversation]);
  useEffect(() => {
    setReadError('');
    const log = messageLog.current;
    const messageId = current?.messages.at(-1)?.id;
    if (page !== 'inbox' || messageBefore || !messageId || !log) return;
    const controller = new AbortController();
    let pending = false;
    async function markRead() {
      if (pending || readInFlight.current[activeId] || readPaused.current === activeId || controller.signal.aborted || document.hidden || readMessages.current[activeId] === messageId ||
          !log.clientHeight || log.scrollHeight - log.scrollTop - log.clientHeight > 20 ||
          (window.matchMedia('(max-width: 760px)').matches && !mobileConversation) ||
          (window.matchMedia('(max-width: 1279px)').matches && profileOpen)) return;
      pending = true;
      try {
        readInFlight.current[activeId] = request(`/inbox/conversations/${encodeURIComponent(activeId)}/read`, {
          method: 'POST', body: JSON.stringify({ message_id: messageId }),
        });
        await readInFlight.current[activeId];
        if (!controller.signal.aborted) { readMessages.current[activeId] = messageId; setReadError(''); setRefresh(value => value + 1); }
      } catch (error) {
        if (!controller.signal.aborted) { if (error.status === 401) onExpired(); setReadError('Chưa lưu được trạng thái đã đọc. Đang thử lại.'); }
      } finally { pending = false; delete readInFlight.current[activeId]; }
    }
    const start = setTimeout(markRead, 300);
    const timer = setInterval(markRead, 3000);
    log.addEventListener('scroll', markRead);
    document.addEventListener('visibilitychange', markRead);
    return () => { controller.abort(); clearTimeout(start); clearInterval(timer); log.removeEventListener('scroll', markRead); document.removeEventListener('visibilitychange', markRead); };
  }, [current?.messages.at(-1)?.id, activeId, page, messageBefore, mobileConversation, profileOpen]);
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
  async function markUnread() {
    if (actionLoading || !current?.last_customer_message_id) return;
    const targetId = activeId, messageId = current.last_customer_message_id;
    readPaused.current = targetId; setActionLoading(true); setActionError('');
    try {
      await readInFlight.current[targetId]?.catch(() => {});
      await request(`/inbox/conversations/${encodeURIComponent(targetId)}/unread`, { method: 'POST', body: JSON.stringify({ message_id: messageId }) });
      delete readMessages.current[targetId];
      updateNavigation({ unreadOnly: true, selectedId: null, mobileConversation: false, offset: 0 }, false);
      setRefresh(n => n + 1);
    } catch (error) {
      if (error.status === 401) onExpired();
      setActionError({ id: targetId, message: error.message });
    } finally { readPaused.current = null; setActionLoading(false); }
  }
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
  async function sendReply(event, retryPending = false) {
    event.preventDefault();
    const content = retryPending ? pendingReplies.current[activeId]?.content : draft.trim();
    if (!content || !activeId || !canReply || actionLoading) return;
    const targetId = activeId;
    if (pendingReplies.current[targetId]?.content !== content) pendingReplies.current[targetId] = {content, client_message_id:crypto.randomUUID()};
    saveDrafts(previous => ({ ...previous, pending: { ...pendingReplies.current } }));
    if (await postAction('/messages', pendingReplies.current[targetId])) {
      delete pendingReplies.current[targetId];
      saveDrafts(previous => ({ ...previous, pending: { ...pendingReplies.current } }));
      setMessageHistory({ id: targetId, cursors: [] });
      setDrafts(previous => previous[targetId] === draft && draft.trim() === content ? { ...previous, [targetId]: '' } : previous);
    }
  }
  function changeFilter(setter, value) { setter(value); setOffset(0); }
  function navigate(target, filters = {}) {
    updateNavigation({ page: target, customerFilter: '', mobileConversation: false,
      ...(target !== page && { recordSearch: '', recordStatus: '', recordOffset: 0, recordId: null }),
      ...(target === 'inbox' && Object.keys(filters).length && {
        assignment: 'all', status: '', sla: '', priority: '', search: '', offset: 0, selectedId: null, unreadOnly: false, ...filters,
      }),
    }, false);
  }
  function openInbox(id) {
    updateNavigation({ page: 'inbox', assignment: 'all', mobileConversation: true, status: '', priority: '',
      sla: '', search: '', offset: 0, selectedId: id, unreadOnly: false }, false);
  }
  function openOrders(id) {
    updateNavigation({ page: 'orders', customerFilter: id, recordSearch: '', recordStatus: '', recordOffset: 0, recordId: null }, false);
  }
  return <div data-theme={theme} className={`shell ${page === 'inbox' ? 'inboxShell' : ''}`}>
    <aside aria-label="Điều hướng chính">
      <div className="brand"><span className="brandLogo"><MessageSquare aria-hidden="true" /></span><b>RAG Support</b><small>Không gian làm việc</small></div>
      <span className="navCaption">KHÔNG GIAN HỖ TRỢ</span>
      {pages.map(([Icon, label, target]) =>
        <button key={target} title={label} aria-label={label} className={`nav ${page === target ? 'active' : ''}`} onClick={() => navigate(target)} aria-current={page === target ? 'page' : undefined}><Icon size={18} aria-hidden="true" />{label}</button>)}
      <div className="sidebarNote"><ShieldCheck size={18} aria-hidden="true" /><span>{user.role === 'admin' ? 'Quyền quản trị' : 'Nhân viên hỗ trợ'}<small>{user.role === 'admin' ? 'Quản lý và hỗ trợ khách hàng' : 'Tiếp nhận và xử lý hội thoại'}</small></span></div>
      {themeButton}
      <div className="agent"><div className="avatar">{initials(user.display_name)}</div><div><b>{user.display_name}</b><small>{user.role === 'admin' ? 'Quản trị viên' : 'Nhân viên hỗ trợ'}</small></div><button className="iconButton" aria-label="Đăng xuất" title="Đăng xuất" onClick={onLogout} disabled={logoutBusy || actionLoading}><LogOut size={17} /></button></div>
    </aside>
    <main>
      <nav className="mobileNav" aria-label="Điều hướng">{themeButton}{pages.map(([Icon, label, target]) => <button key={target} aria-pressed={page === target} onClick={() => navigate(target)}><Icon size={16} aria-hidden="true" />{label}</button>)}<button onClick={onLogout} disabled={logoutBusy || actionLoading}>Đăng xuất</button></nav>
      {sessionError && <p className="state" role="alert">{sessionError}</p>}
      {page === 'knowledge' ? <KnowledgeBase user={user} request={request} onExpired={onExpired} /> : page !== 'inbox' ? <Workspace key={`${page}-${customerFilter}`} page={page} user={user} request={request} onExpired={onExpired} navigate={navigate} openInbox={openInbox} customerFilter={customerFilter} openOrders={openOrders} route={route} updateNavigation={updateNavigation} /> : <>
      <header className="inboxHeader"><div><Inbox size={21} aria-hidden="true" /><h1>Hội thoại</h1><span className="headerDivider" /><span className="headerSubtitle">Hộp thư hỗ trợ</span></div><span className={`syncStatus ${listError ? 'syncError' : ''}`} title={lastUpdated ? `Cập nhật: ${timeOf(lastUpdated)}. Tự làm mới mỗi 3 giây.` : 'Đang kết nối'}><span />{listError ? 'Mất kết nối' : listLoading ? 'Đang cập nhật' : 'Đã đồng bộ'}</span></header>
      <section className={`workspace ${profileOpen ? 'profileVisible' : ''} ${mobileConversation ? 'showConversation' : ''}`}>
        <div className="list" aria-label="Danh sách hội thoại" aria-busy={listLoading}>
          <div className="listHead"><div><h2>Hộp thư</h2><span className="inboxCount">{listError ? '—' : listMeta.total}</span></div><button className="iconButton" aria-label="Làm mới hội thoại" title="Làm mới" onClick={() => { setRefresh(n => n + 1); setDetailRetry(n => n + 1); }} disabled={listLoading || actionLoading}><RefreshCw size={16} /></button></div>
          <nav className="assignmentTabs" aria-label="Lọc người phụ trách">{[['all', 'Tất cả'], ['mine', 'Của tôi'], ['unassigned', 'Chưa nhận']].map(([value, label]) => <button key={value} title={value === 'unassigned' ? 'Chưa có người phụ trách, gồm cả hội thoại AI đang hỗ trợ' : label} aria-pressed={assignment === value} onClick={() => changeFilter(setAssignment, value)}>{label}</button>)}</nav>
          <label className="search"><Search size={16} aria-hidden="true" /><input aria-label="Tìm kiếm hội thoại" placeholder="Tìm khách hàng, kênh..." maxLength={160} value={search} onChange={e => changeFilter(setSearch, e.target.value)} /></label>
          <label className="unreadFilter"><input type="checkbox" checked={unreadOnly} onChange={event => updateNavigation({ unreadOnly: event.target.checked, offset: 0 })} />Chỉ tin khách chưa đọc</label>
          {unreadOnly && <p className="unreadHint">Đọc xong sẽ rời danh sách; hội thoại đang mở vẫn được giữ.</p>}
          <details className="inboxFilters"><summary><SlidersHorizontal size={14} aria-hidden="true" />Bộ lọc<span>{[status, priority, sla, unreadOnly].filter(Boolean).length || ''}</span></summary><div className="filters"><label>Trạng thái<select value={status} onChange={e => changeFilter(setStatus, e.target.value)}><option value="">Tất cả</option>{Object.entries(statuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Ưu tiên<select value={priority} onChange={e => changeFilter(setPriority, e.target.value)}><option value="">Tất cả</option>{Object.entries(priorities).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div>
          <label className="slaFilter">SLA phản hồi đầu tiên<select value={sla} onChange={e => changeFilter(setSla, e.target.value)}><option value="">Tất cả</option>{Object.entries(slaStatuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>{(status || priority || sla || unreadOnly) && <button className="clearFilters" onClick={() => updateNavigation({ status: '', priority: '', sla: '', unreadOnly: false, offset: 0 })}>Xóa bộ lọc</button>}</details>
          <div className="conversationList">
          {listError && <div className="state" role="alert"><p>{listError} Dữ liệu có thể đã cũ; đang thử kết nối lại.</p><button onClick={() => setRefresh(n => n + 1)}>Thử lại</button></div>}
          {listLoading ? <p className="state" role="status">Đang tải danh sách...</p> : !visibleChats.length ? !listError && <p className="state" role="status">{unreadOnly ? 'Không còn tin khách chưa đọc trong bộ lọc này.' : 'Không có hội thoại phù hợp.'}</p> : visibleChats.map(c =>
            <button key={c.conversation_id} aria-pressed={activeId === c.conversation_id} onClick={() => updateNavigation({ selectedId: c.conversation_id, mobileConversation: true }, false)} className={`chat ${activeId === c.conversation_id ? 'selected' : ''} ${c.unread_count ? 'unread' : ''}`}><span className="avatar">{initials(nameOf(c))}</span><span className="chatText"><b>{nameOf(c)}</b><small className="chatPreview">{c.last_message ? `${senders[c.last_message.sender_type] || 'Tin nhắn'}: ${c.last_message.content}` : 'Chưa có tin nhắn'}</small><span className="chatMeta"><span className={`statusDot status-${c.status}`} aria-hidden="true" /><span>{statuses[c.status] || c.status} · {channelName(c.channel)}</span>{c.priority !== 'normal' && <i>{priorities[c.priority] || c.priority}</i>}</span>{c.sla && ['overdue', 'breached'].includes(c.sla.status) && <SlaBadge value={c.sla} />}</span><span className="chatActivity"><time title={`Hoạt động gần nhất: ${timeOf(c.last_activity_at || c.created_at)}`}>{shortTime(c.last_activity_at || c.created_at)}</time>{c.unread_count > 0 && <span className="unreadBadge" aria-label={`${c.unread_count} tin khách chưa đọc`}>{c.unread_count > 99 ? '99+' : c.unread_count}</span>}</span></button>)}
          </div>
          <nav className="inboxPages" aria-label="Phân trang hội thoại"><span role="status">{listLoading || listError ? 'Đang cập nhật' : `${listMeta.total ? offset + 1 : 0}–${offset + conversations.length} / ${listMeta.total}`}</span><button className="iconButton" aria-label="Trang hội thoại trước" disabled={!offset || listLoading || actionLoading} onClick={() => setOffset(n => Math.max(0, n - pageSize))}><ChevronLeft size={16} /></button><button className="iconButton" aria-label="Trang hội thoại sau" disabled={!listMeta.has_more || listLoading || actionLoading || Boolean(listError)} onClick={() => setOffset(n => n + pageSize)}><ChevronRight size={16} /></button></nav>
        </div>
        <div className="conversation" aria-label="Chi tiết hội thoại" aria-busy={detailLoading}>
          <div className="convHead"><button className="iconButton backToList" aria-label="Về danh sách hội thoại" onClick={() => updateNavigation({ mobileConversation: false }, false)}><ChevronLeft size={20} /></button>{selected ? <><div className="avatar big">{initials(nameOf(selected))}</div><div className="conversationIdentity"><b>{nameOf(selected)}</b><small><Globe size={12} aria-hidden="true" />{channelName(selected.channel)}<span>·</span>{statuses[current?.status || selected.status]}</small></div></> : <b>Chi tiết hội thoại</b>}<div className="conversationActions">{current?.status === 'handoff_requested' && <button className="acceptButton" onClick={acceptConversation} disabled={actionLoading || listLoading}><UserRound size={15} aria-hidden="true" />Tiếp nhận</button>}<button className="iconButton" aria-label="Đánh dấu chưa đọc" title="Đánh dấu chưa đọc" onClick={markUnread} disabled={actionLoading || !current?.last_customer_message_id}><Mail size={18} aria-hidden="true" /></button><button ref={profileToggle} className="iconButton" aria-label={profileOpen ? 'Ẩn thông tin khách hàng' : 'Hiện thông tin khách hàng'} title="Thông tin khách hàng" aria-expanded={profileOpen} aria-controls="customerInfo" onClick={() => setProfileOpen(value => !value)}><PanelRight size={19} /></button></div></div>
          {current && ['handoff_requested', 'assigned'].includes(current.status) && <p className="handoff" role="status">AI đã dừng. {current.status === 'handoff_requested' ? 'Đang chờ nhân viên tiếp nhận.' : canReply ? 'Bạn đang phụ trách hội thoại.' : 'Nhân viên khác đang phụ trách hội thoại.'}</p>}
          {current?.sla && <p className="slaSummary"><SlaBadge value={current.sla} /><button className="slaDetails" onClick={() => setProfileOpen(true)}>Chi tiết SLA</button></p>}
          {readError && <p className="readNotice" role="status">{readError}</p>}
          {detailError && <div className="state" role="alert"><p>{detailError} Dữ liệu có thể đã cũ; đang thử kết nối lại.</p><button onClick={() => setDetailRetry(n => n + 1)}>Thử lại</button></div>}
          {activeId && <nav className="messagePagination" aria-label="Phân trang tin nhắn">
            <span role="status">{messageBefore ? 'Đang xem tin cũ' : 'Tin gần nhất'}{current && ` · ${current.messages.length} tin`}</span>
            <button disabled={!current?.message_page.has_more || detailLoading || actionLoading} onClick={() => setMessageHistory({ id: activeId, cursors: [...messageCursors, current.message_page.next_before] })}>Tin cũ hơn</button>
            <button disabled={messageCursors.length < 2 || detailLoading || actionLoading} onClick={() => setMessageHistory({ id: activeId, cursors: messageCursors.slice(0, -1) })}>Tin mới hơn</button>
            {messageBefore && <button onClick={() => setMessageHistory({ id: activeId, cursors: [] })}>Về tin mới nhất</button>}
          </nav>}
          <div className="messages" ref={messageLog} onScroll={event => { const e = event.currentTarget; followMessages.current = e.scrollHeight - e.scrollTop - e.clientHeight < 20; setAtLatest(followMessages.current); }} key={`${activeId}:${messageBefore || ''}`} tabIndex={0} role="log" aria-live={messageBefore ? 'off' : 'polite'} aria-relevant="additions" aria-label="Lịch sử tin nhắn">
            {!activeId ? <div className="inboxEmpty"><span><MessageSquare size={30} aria-hidden="true" /></span><h2>Sẵn sàng hỗ trợ</h2><p>Chọn hội thoại bên trái để xem lịch sử<br />và tiếp tục hỗ trợ khách hàng.</p></div> : !current ? <p className="state" role="status">{detailError ? 'Chưa tải được hội thoại.' : 'Đang tải hội thoại...'}</p> : <>
              {!current.messages.length && <p className="state">Hội thoại chưa có tin nhắn.</p>}
              {current.messages.map(m => <div key={m.id} className={`bubble ${m.sender_type === 'customer' ? 'customer' : m.sender_type === 'agent' ? 'staff' : m.sender_type === 'system' ? 'system' : 'ai'}`}><b>{m.sender_type === 'ai' && <Bot size={13} aria-hidden="true" />}{senders[m.sender_type] || m.sender_type}</b><div className="messageContent">{m.content}</div>{m.citations?.length > 0 && <Citations citations={m.citations} request={request} />}<time title={timeOf(m.created_at)}>{shortTime(m.created_at)}</time><ToolTrace trace={m.tool_trace} /><DeliveryState message={m} canRetry={current.assigned_agent_id === user.id} onExpired={onExpired} onRetried={() => setDetailRetry(n=>n+1)} /></div>)}

            </>}
          </div>
          {!atLatest && !messageBefore && <button className="jumpLatest" onClick={() => { if (messageLog.current) messageLog.current.scrollTop = messageLog.current.scrollHeight; }}>Về tin mới nhất</button>}
          {draftError && <p className="readNotice" role="alert">Không lưu hoặc khôi phục được nháp. Giữ tab mở và sao chép nội dung trước khi tải lại.</p>}{canReply && !actionLoading && savedDrafts.pending[activeId] && <p className="readNotice" role="status">Tin trước chưa xác nhận. Xem lịch sử hoặc <button onClick={event => sendReply(event, true)}>Gửi lại tin chưa xác nhận</button>.</p>}{current && <><form className="composer" onSubmit={sendReply}><MessageInput aria-label="Tin nhắn nhân viên" value={draft} onChange={e => setDrafts(previous => ({ ...previous, [activeId]: e.target.value }))} disabled={!canReply || actionLoading} placeholder={canReply ? 'Nhập phản hồi cho khách hàng...' : 'Chỉ nhân viên phụ trách được trả lời'} maxLength={4000} /><button type="submit" disabled={!canReply || !draft.trim() || actionLoading}><Send size={16} aria-hidden="true" />Gửi</button></form><div className="composerHint"><span>Enter để gửi · Shift+Enter xuống dòng</span><span>Phản hồi công khai</span></div></>}
          {canReply && activeTicket && <details className="finishPanel" key={activeId}><summary><CheckCheck size={15} aria-hidden="true" />Hoàn tất hội thoại</summary><form className="completionForm" onSubmit={finishConversation}>
            <label htmlFor="completionNote">Ghi chú hoàn tất (nội bộ)</label>
            <textarea id="completionNote" rows={2} maxLength={2000} required value={completionNote} onChange={e => setCompletionNotes(previous => ({ ...previous, [activeId]: e.target.value }))} disabled={actionLoading} />
            <small>{messageBefore ? 'Về tin mới nhất và đọc trước khi hoàn tất.' : 'Áp dụng cho các ticket đang xử lý. Khách chỉ nhận thông báo trạng thái.'}</small>
            <div><button value="resolved" disabled={actionLoading || Boolean(messageBefore) || !completionNote.trim()}>Giải quyết</button><button value="closed" disabled={actionLoading || Boolean(messageBefore) || !completionNote.trim()}>Đóng hội thoại</button></div>
          </form></details>}
          {actionError?.id === activeId && <p className="state" role="alert">{actionError.message}</p>}
        </div>
        {profileOpen && <ProfilePanel ref={profilePanel} onCancel={() => setProfileOpen(false)} id="customerInfo" className="profile" aria-label="Thông tin khách hàng" onKeyDown={event => { if (event.key === 'Escape') { setProfileOpen(false); profileToggle.current?.focus(); } }}><div className="profileHeading"><h2>Thông tin liên hệ</h2><button className="iconButton" aria-label="Đóng thông tin khách hàng" onClick={() => { setProfileOpen(false); profileToggle.current?.focus(); }}><X size={17} /></button></div>{current ? <><div className="profileUser"><div className="avatar big">{initials(nameOf(current))}</div><h3>{nameOf(current)}</h3><p>{current.customer_email || 'Chưa có email'}</p><button className="profileLink" onClick={() => openOrders(current.customer_id)}><Package size={14} aria-hidden="true" />Xem đơn hàng<ArrowUpRight size={13} aria-hidden="true" /></button></div><dl className="conversationFacts"><dt>Kênh hỗ trợ</dt><dd>{channelName(current.channel)}</dd><dt>Trạng thái</dt><dd>{statuses[current.status] || current.status}</dd><dt>Người phụ trách</dt><dd>{current.assigned_agent_id === user.id ? `${user.display_name} (bạn)` : current.assigned_agent_id ? 'Nhân viên khác' : 'Chưa phân công'}</dd><dt>Ưu tiên</dt><dd>{priorities[current.priority] || current.priority}</dd><dt>Mã khách hàng</dt><dd className="customerIdentifier">{current.customer_id}</dd></dl><details className="profileTickets" open><summary><Clock3 size={15} aria-hidden="true" />Ticket hỗ trợ<span>{current.tickets.length}</span></summary>
              <section className="tickets" aria-label="Ticket hỗ trợ"><h3>Ticket hỗ trợ ({current.tickets.length})</h3>{!current.tickets.length ? <p>Chưa có ticket hỗ trợ.</p> : current.tickets.map(t => <article key={t.id} className="ticket"><b>{statuses[t.status] || t.status} · {priorities[t.priority] || t.priority}</b><p>{t.summary || 'Chưa có tóm tắt.'}</p><SlaBadge value={t.sla} />{t.sla && <p>Hạn: {timeOf(t.sla.due_at)}{t.sla.responded_at && <><br />Phản hồi đầu: {timeOf(t.sla.responded_at)}</>}</p>}{t.completed_at && <p>Hoàn tất: {timeOf(t.completed_at)} · {t.completed_by_name || 'Khách hàng'}</p>}{t.completion_note && <p className="completionNote"><b>Ghi chú nội bộ:</b> {t.completion_note}</p>}<small>#{t.id} · {timeOf(t.created_at)}</small></article>)}</section></details><div className="profileFootnote"><ShieldCheck size={15} aria-hidden="true" /><p>Thông tin nội bộ dành cho đội hỗ trợ.</p></div></> : <p className="state">Chọn hội thoại để xem thông tin khách hàng.</p>}</ProfilePanel>}

      </section>
      </>}
    </main>
  </div>;
}

createRoot(document.getElementById('root')).render(<ThemeProvider>{window.location.pathname === '/chat' ? <Widget /> : <SessionGate />}</ThemeProvider>);
