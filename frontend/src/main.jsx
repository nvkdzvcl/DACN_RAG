import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Inbox, BookOpen, Package, BarChart3, Settings, Search, UserRound, Bot } from 'lucide-react';
import './styles.css';
import KnowledgeBase, { Citations } from './KnowledgeBase';
import Widget from './Widget';

const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '');
const statuses = { open: 'Đang mở', handoff_requested: 'Chờ nhân viên', assigned: 'Đã tiếp nhận', closed: 'Đã đóng', resolved: 'Đã giải quyết' };
const priorities = { normal: 'Bình thường', high: 'Cao', urgent: 'Khẩn cấp', low: 'Thấp' };
const slaStatuses = { on_track: 'Trong hạn', overdue: 'Quá hạn chờ phản hồi', met: 'Đã phản hồi đúng hạn', breached: 'Đã phản hồi trễ', cancelled: 'Kết thúc trước phản hồi', none: 'Chưa có SLA' };
const senders = { customer: 'Khách hàng', ai: 'RAG AI', assistant: 'RAG AI', agent: 'Nhân viên', system: 'Hệ thống' };
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
  if (user) return <App user={user} onExpired={() => setUser(null)} onLogout={logout} logoutBusy={busy} sessionError={error} />;
  return <main className="loginPage"><form className="loginCard" onSubmit={login} aria-busy={busy}>
    <Bot size={40} aria-hidden="true" /><p>RAG Support Hub</p><h1>Đăng nhập nhân viên</h1>
    <label>Tên đăng nhập<input name="username" autoComplete="username" required maxLength={64} pattern="[a-zA-Z0-9_.-]+" /></label>
    <label>Mật khẩu<input name="password" type="password" autoComplete="current-password" required maxLength={128} /></label>
    {error && <p role="alert">{error}</p>}<button disabled={busy}>{busy ? 'Đang đăng nhập...' : 'Đăng nhập'}</button>
    <small>Tài khoản do quản trị viên cấp.</small>
  </form></main>;
}

function App({ user, onExpired, onLogout, logoutBusy, sessionError }) {
  const [page, setPage] = useState('inbox');
  const [conversations, setConversations] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [sla, setSla] = useState('');
  const [search, setSearch] = useState('');
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

  useEffect(() => {
    if (page !== 'inbox' || actionLoading) return;
    const controller = new AbortController();
    let timer;
    setListLoading(true);
    setListError('');
    async function load(first = false) {
      if (first || !document.hidden) {
        try {
          const data = await getInbox(`?${new URLSearchParams({ ...(status && { status }), ...(priority && { priority }), ...(sla && { sla }) })}`, controller.signal);
          if (controller.signal.aborted) return;
          if (!Array.isArray(data.conversations) || data.conversations.some(c => typeof c.conversation_id !== 'string' || typeof c.customer_id !== 'string')) throw new Error('Dữ liệu danh sách không hợp lệ.');
          setConversations(data.conversations);
          setSelectedId(id => data.conversations.some(c => c.conversation_id === id) ? id : data.conversations[0]?.conversation_id || null);
          setListError(''); setLastUpdated(new Date().toISOString());
        } catch (error) {
          if (!controller.signal.aborted) { if (error.status === 401) onExpired(); setListError(error.message || 'Không kết nối được backend.'); }
        } finally { if (!controller.signal.aborted) setListLoading(false); }
      }
      if (!controller.signal.aborted) timer = setTimeout(load, 3000);
    }
    load(true);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [status, priority, sla, refresh, page, actionLoading]);

  const query = search.trim().toLocaleLowerCase('vi');
  const visibleChats = conversations.filter(c => `${nameOf(c)} ${c.customer_id} ${c.channel}`.toLocaleLowerCase('vi').includes(query));
  const activeId = visibleChats.some(c => c.conversation_id === selectedId) ? selectedId : visibleChats[0]?.conversation_id;
  const selected = visibleChats.find(c => c.conversation_id === activeId);
  const draft = drafts[activeId] || '';

  useEffect(() => {
    if (page !== 'inbox' || actionLoading) return;
    const controller = new AbortController();
    let timer;
    setDetail(null);
    setDetailError('');
    setDetailLoading(Boolean(activeId));
    async function load(first = false) {
      if (first || !document.hidden) {
        try {
          const data = await getInbox(`/${encodeURIComponent(activeId)}`, controller.signal);
          if (controller.signal.aborted) return;
          if (data.conversation_id !== activeId || !Array.isArray(data.messages) || !Array.isArray(data.tickets)) throw new Error('Dữ liệu hội thoại không hợp lệ.');
          setDetail(data); setDetailError('');
        } catch (error) {
          if (!controller.signal.aborted) { if (error.status === 401) onExpired(); setDetailError(error.message || 'Không tải được hội thoại.'); }
        } finally { if (!controller.signal.aborted) setDetailLoading(false); }
      }
      if (!controller.signal.aborted) timer = setTimeout(load, 3000);
    }
    if (activeId) load(true);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [activeId, detailRetry, page, actionLoading]);

  // Ignore previous customer's detail before effect cleanup runs.
  const current = detail?.conversation_id === activeId ? detail : null;
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
    if (!canReply || !activeTicket || actionLoading || !completionNote.trim()) return;
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
    if (await postAction('/messages', { content })) setDrafts(previous => previous[targetId] === draft ? { ...previous, [targetId]: '' } : previous);
  }
  const counts = [visibleChats.length, visibleChats.filter(c => c.status === 'open').length, visibleChats.filter(c => c.status === 'handoff_requested').length, visibleChats.filter(c => c.sla?.status === 'overdue').length];
  return <div className="shell">
    <aside aria-label="Điều hướng chính">
      <div className="brand"><span className="brandLogo"><Bot aria-hidden="true" /></span><b>RAG</b><small>Support Hub</small></div>
      {[[Inbox, 'Tổng quan'], [Inbox, 'Hội thoại'], [UserRound, 'Khách hàng'], [Package, 'Đơn hàng'], [BookOpen, 'Kho tri thức'], [BarChart3, 'Phân tích'], [Settings, 'Cài đặt']].map(([Icon, label], i) =>
        <button key={label} className={`nav ${(i === 1 && page === 'inbox') || (i === 4 && page === 'knowledge') ? 'active' : ''}`} disabled={i !== 1 && i !== 4} onClick={() => setPage(i === 4 ? 'knowledge' : 'inbox')} aria-current={(i === 1 && page === 'inbox') || (i === 4 && page === 'knowledge') ? 'page' : undefined}><Icon size={17} />{label}{i === 1 && <em>{listLoading || listError ? '—' : conversations.length}</em>}</button>)}
      <div className="agent"><div className="avatar"><UserRound size={18} /></div><div><b>{user.display_name}</b><small>{user.role === 'admin' ? 'Quản trị viên' : 'Nhân viên hỗ trợ'}</small></div></div>
    </aside>
    <main>
      <div className="sessionBar"><span>{user.display_name}</span><button onClick={onLogout} disabled={logoutBusy}>{logoutBusy ? 'Đang đăng xuất...' : 'Đăng xuất'}</button></div>
      {sessionError && <p role="alert">{sessionError}</p>}
      <nav className="mobileNav" aria-label="Điều hướng"><button aria-pressed={page === 'inbox'} onClick={() => setPage('inbox')}>Hội thoại</button><button aria-pressed={page === 'knowledge'} onClick={() => setPage('knowledge')}>Kho tri thức</button></nav>
      {page === 'knowledge' ? <KnowledgeBase user={user} request={request} onExpired={onExpired} /> : <>
      <header><div><h1>Hộp thư đa kênh</h1><p>Quản lý hội thoại, tin nhắn và yêu cầu hỗ trợ tập trung</p></div><label className="search"><Search size={16} /><input aria-label="Tìm kiếm hội thoại" placeholder="Tìm khách hàng, kênh..." value={search} onChange={e => setSearch(e.target.value)} /></label></header>
      <p className="syncNote">Tự cập nhật mỗi 3 giây khi đang xem Inbox.{lastUpdated && ` Danh sách cập nhật: ${timeOf(lastUpdated)}.`}</p>
      <div className="stats">{['Hội thoại trong bộ lọc', 'Đang mở', 'Chờ nhân viên', 'Quá hạn chờ phản hồi'].map((label, i) => <div key={label}><b>{listLoading || listError ? '—' : counts[i]}</b><small>{label}</small></div>)}</div>
      <section className="workspace">
        <div className="list" aria-label="Danh sách hội thoại" aria-busy={listLoading}>
          <div className="listHead"><b>Hội thoại</b><button onClick={() => { setRefresh(n => n + 1); setDetailRetry(n => n + 1); }} disabled={listLoading || actionLoading}>Làm mới</button></div>
          <div className="filters"><label>Trạng thái<select value={status} onChange={e => setStatus(e.target.value)}><option value="">Tất cả</option>{Object.entries(statuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Ưu tiên<select value={priority} onChange={e => setPriority(e.target.value)}><option value="">Tất cả</option>{Object.entries(priorities).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div>
          <label className="slaFilter">SLA phản hồi đầu tiên<select value={sla} onChange={e => setSla(e.target.value)}><option value="">Tất cả</option>{Object.entries(slaStatuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          {listError && <div className="state" role="alert"><p>{listError} Dữ liệu có thể đã cũ; đang thử kết nối lại.</p><button onClick={() => setRefresh(n => n + 1)}>Thử lại</button></div>}
          {listLoading ? <p className="state" role="status">Đang tải danh sách...</p> : !visibleChats.length ? !listError && <p className="state" role="status">Không có hội thoại phù hợp.</p> : visibleChats.map(c =>
            <button key={c.conversation_id} aria-pressed={activeId === c.conversation_id} onClick={() => setSelectedId(c.conversation_id)} className={`chat ${activeId === c.conversation_id ? 'selected' : ''}`}><span className="avatar">{initials(nameOf(c))}</span><span className="chatText"><b>{nameOf(c)}</b><small>{c.channel} · {statuses[c.status] || c.status}</small><i>{priorities[c.priority] || c.priority}</i><SlaBadge value={c.sla} /><small>{timeOf(c.created_at)}</small></span></button>)}
        </div>
        <div className="conversation" aria-label="Chi tiết hội thoại" aria-busy={detailLoading}>
          {selected && <div className="convHead"><div className="avatar big">{initials(nameOf(selected))}</div><div><b>{nameOf(selected)}</b><small>{selected.channel} · {statuses[current?.status || selected.status]}</small></div>{current?.status === 'handoff_requested' && <button onClick={acceptConversation} disabled={actionLoading || listLoading}>Tiếp nhận</button>}</div>}
          {current && ['handoff_requested', 'assigned'].includes(current.status) && <p className="handoff" role="status">AI đã dừng. {current.status === 'handoff_requested' ? 'Đang chờ nhân viên tiếp nhận.' : canReply ? 'Bạn đang phụ trách hội thoại.' : 'Nhân viên khác đang phụ trách hội thoại.'}</p>}
          {current?.sla && <p className="slaSummary"><SlaBadge value={current.sla} /> Hạn phản hồi: {timeOf(current.sla.due_at)} · {current.sla.target_minutes} phút từ lúc tạo ticket (24/7).</p>}
          {detailError && <div className="state" role="alert"><p>{detailError} Dữ liệu có thể đã cũ; đang thử kết nối lại.</p><button onClick={() => setDetailRetry(n => n + 1)}>Thử lại</button></div>}
          <div className="messages">
            {!selected ? <p className="state">Chọn hội thoại để xem nội dung.</p> : !current ? <p className="state" role="status">{detailError ? 'Chưa tải được hội thoại.' : 'Đang tải hội thoại...'}</p> : <>
              {!current.messages.length && <p className="state">Hội thoại chưa có tin nhắn.</p>}
              {current.messages.map(m => <div key={m.id} className={`bubble ${m.sender_type === 'customer' ? 'customer' : m.sender_type === 'agent' ? 'staff' : 'ai'}`}><b>{senders[m.sender_type] || m.sender_type}</b><div className="messageContent">{m.content}</div>{m.citations?.length > 0 && <Citations citations={m.citations} request={request} />}<time>{timeOf(m.created_at)}</time></div>)}
              <section className="tickets" aria-label="Ticket hỗ trợ"><h3>Ticket hỗ trợ ({current.tickets.length})</h3>{!current.tickets.length ? <p>Chưa có ticket hỗ trợ.</p> : current.tickets.map(t => <article key={t.id} className="ticket"><b>{statuses[t.status] || t.status} · {priorities[t.priority] || t.priority}</b><p>{t.summary || 'Chưa có tóm tắt.'}</p><SlaBadge value={t.sla} />{t.sla && <p>Hạn: {timeOf(t.sla.due_at)}{t.sla.responded_at && <><br />Phản hồi đầu: {timeOf(t.sla.responded_at)}</>}</p>}{t.completed_at && <p>Hoàn tất: {timeOf(t.completed_at)} · {t.completed_by_name || 'Khách hàng'}</p>}{t.completion_note && <p className="completionNote"><b>Ghi chú nội bộ:</b> {t.completion_note}</p>}<small>#{t.id} · {timeOf(t.created_at)}</small></article>)}</section>
            </>}
          </div>
          {current && <form className="composer" onSubmit={sendReply}><input aria-label="Tin nhắn nhân viên" value={draft} onChange={e => setDrafts(previous => ({ ...previous, [activeId]: e.target.value }))} disabled={!canReply || actionLoading} placeholder={canReply ? 'Nhập phản hồi cho khách hàng...' : 'Chỉ nhân viên phụ trách được trả lời'} maxLength={4000} /><button type="submit" disabled={!canReply || !draft.trim() || actionLoading}>Gửi</button></form>}
          {canReply && activeTicket && <form className="completionForm" onSubmit={finishConversation}>
            <label htmlFor="completionNote">Ghi chú hoàn tất (nội bộ)</label>
            <textarea id="completionNote" rows={2} maxLength={2000} required value={completionNote} onChange={e => setCompletionNotes(previous => ({ ...previous, [activeId]: e.target.value }))} disabled={actionLoading} />
            <small>Áp dụng cho các ticket đang xử lý. Khách chỉ nhận thông báo trạng thái.</small>
            <div><button value="resolved" disabled={actionLoading || !completionNote.trim()}>Giải quyết</button><button value="closed" disabled={actionLoading || !completionNote.trim()}>Đóng hội thoại</button></div>
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
