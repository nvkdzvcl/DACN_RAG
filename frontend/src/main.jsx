import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Inbox, BookOpen, Package, BarChart3, Settings, Search, UserRound, Bot } from 'lucide-react';
import './styles.css';

const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '');
const statuses = { open: 'Đang mở', handoff_requested: 'Chờ nhân viên', assigned: 'Đã tiếp nhận', closed: 'Đã đóng', resolved: 'Đã giải quyết' };
const priorities = { normal: 'Bình thường', high: 'Cao', urgent: 'Khẩn cấp', low: 'Thấp' };
const senders = { customer: 'Khách hàng', ai: 'RAG AI', assistant: 'RAG AI', agent: 'Nhân viên', system: 'Hệ thống' };
const nameOf = c => c.customer_name || c.customer_id;
const initials = name => name.trim().split(/\s+/).slice(-2).map(word => word[0]).join('').toUpperCase();
function timeOf(value) {
  if (!value) return '';
  const date = new Date(/[zZ]$|[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`);
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString('vi-VN');
}

async function getInbox(path, signal) {
  const response = await fetch(`${API_BASE}/api/v1/inbox/conversations${path}`, { signal });
  if (!response.ok) throw new Error(response.status === 404 ? 'Hội thoại không còn tồn tại.' : `Không tải được dữ liệu (HTTP ${response.status}).`);
  if (!response.headers.get('content-type')?.includes('application/json')) throw new Error('API trả về sai định dạng. Hãy khởi động lại frontend và kiểm tra cấu hình proxy.');
  return response.json();
}

function App() {
  const [conversations, setConversations] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [search, setSearch] = useState('');
  const [listLoading, setListLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [listError, setListError] = useState('');
  const [detailError, setDetailError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [detailRetry, setDetailRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setListLoading(true);
    setListError('');
    setConversations([]);
    setSelectedId(null);
    setDetail(null);
    getInbox(`?${new URLSearchParams({ ...(status && { status }), ...(priority && { priority }) })}`, controller.signal)
      .then(data => {
        if (controller.signal.aborted) return;
        if (!Array.isArray(data.conversations) || data.conversations.some(c => typeof c.conversation_id !== 'string' || typeof c.customer_id !== 'string')) throw new Error('Dữ liệu danh sách không hợp lệ.');
        setConversations(data.conversations);
      })
      .catch(error => { if (!controller.signal.aborted) setListError(error.message || 'Không kết nối được backend.'); })
      .finally(() => { if (!controller.signal.aborted) setListLoading(false); });
    return () => controller.abort();
  }, [status, priority, refresh]);

  const query = search.trim().toLocaleLowerCase('vi');
  const visibleChats = conversations.filter(c => `${nameOf(c)} ${c.customer_id} ${c.channel}`.toLocaleLowerCase('vi').includes(query));
  const activeId = visibleChats.some(c => c.conversation_id === selectedId) ? selectedId : visibleChats[0]?.conversation_id;
  const selected = visibleChats.find(c => c.conversation_id === activeId);

  useEffect(() => {
    const controller = new AbortController();
    setDetail(null);
    setDetailError('');
    setDetailLoading(Boolean(activeId));
    if (activeId) getInbox(`/${encodeURIComponent(activeId)}`, controller.signal)
      .then(data => {
        if (controller.signal.aborted) return;
        if (data.conversation_id !== activeId || !Array.isArray(data.messages) || !Array.isArray(data.tickets)) throw new Error('Dữ liệu hội thoại không hợp lệ.');
        setDetail(data);
      })
      .catch(error => { if (!controller.signal.aborted) setDetailError(error.message || 'Không tải được hội thoại.'); })
      .finally(() => { if (!controller.signal.aborted) setDetailLoading(false); });
    return () => controller.abort();
  }, [activeId, detailRetry]);

  // Ignore previous customer's detail before effect cleanup runs.
  const current = detail?.conversation_id === activeId ? detail : null;
  const counts = [visibleChats.length, visibleChats.filter(c => c.status === 'open').length, visibleChats.filter(c => c.status === 'handoff_requested').length, visibleChats.filter(c => ['high', 'urgent'].includes(c.priority)).length];
  return <div className="shell">
    <aside aria-label="Điều hướng chính">
      <div className="brand"><span className="brandLogo"><Bot aria-hidden="true" /></span><b>RAG</b><small>Support Hub</small></div>
      {[[Inbox, 'Tổng quan'], [Inbox, 'Hội thoại'], [UserRound, 'Khách hàng'], [Package, 'Đơn hàng'], [BookOpen, 'Kho tri thức'], [BarChart3, 'Phân tích'], [Settings, 'Cài đặt']].map(([Icon, label], i) =>
        <button key={label} className={`nav ${i === 1 ? 'active' : ''}`} disabled={i !== 1} aria-current={i === 1 ? 'page' : undefined}><Icon size={17} />{label}{i === 1 && <em>{listLoading || listError ? '—' : conversations.length}</em>}</button>)}
      <div className="agent"><div className="avatar"><UserRound size={18} /></div><div><b>Unified Inbox</b><small>Không gian hỗ trợ</small></div></div>
    </aside>
    <main>
      <header><div><h1>Hộp thư đa kênh</h1><p>Quản lý hội thoại, tin nhắn và yêu cầu hỗ trợ tập trung</p></div><label className="search"><Search size={16} /><input aria-label="Tìm kiếm hội thoại" placeholder="Tìm khách hàng, kênh..." value={search} onChange={e => setSearch(e.target.value)} /></label></header>
      <div className="stats">{['Hội thoại trong bộ lọc', 'Đang mở', 'Chờ nhân viên', 'Ưu tiên cao / khẩn cấp'].map((label, i) => <div key={label}><b>{listLoading || listError ? '—' : counts[i]}</b><small>{label}</small></div>)}</div>
      <section className="workspace">
        <div className="list" aria-label="Danh sách hội thoại" aria-busy={listLoading}>
          <div className="listHead"><b>Hội thoại</b><button onClick={() => setRefresh(n => n + 1)} disabled={listLoading}>Làm mới</button></div>
          <div className="filters"><label>Trạng thái<select value={status} onChange={e => setStatus(e.target.value)}><option value="">Tất cả</option>{Object.entries(statuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Ưu tiên<select value={priority} onChange={e => setPriority(e.target.value)}><option value="">Tất cả</option>{Object.entries(priorities).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div>
          {listLoading ? <p className="state" role="status">Đang tải danh sách...</p> : listError ? <div className="state" role="alert"><p>{listError}</p><button onClick={() => setRefresh(n => n + 1)}>Thử lại</button></div> : !visibleChats.length ? <p className="state" role="status">Không có hội thoại phù hợp.</p> : visibleChats.map(c =>
            <button key={c.conversation_id} aria-pressed={activeId === c.conversation_id} onClick={() => setSelectedId(c.conversation_id)} className={`chat ${activeId === c.conversation_id ? 'selected' : ''}`}><span className="avatar">{initials(nameOf(c))}</span><span className="chatText"><b>{nameOf(c)}</b><small>{c.channel} · {statuses[c.status] || c.status}</small><i>{priorities[c.priority] || c.priority}</i><small>{timeOf(c.created_at)}</small></span></button>)}
        </div>
        <div className="conversation" aria-label="Chi tiết hội thoại" aria-busy={detailLoading}>
          {selected && <div className="convHead"><div className="avatar big">{initials(nameOf(selected))}</div><div><b>{nameOf(selected)}</b><small>{selected.channel} · {statuses[selected.status] || selected.status}</small></div></div>}
          <div className="messages">
            {!selected ? <p className="state">Chọn hội thoại để xem nội dung.</p> : detailError ? <div className="state" role="alert"><p>{detailError}</p><button onClick={() => setDetailRetry(n => n + 1)}>Thử lại</button></div> : !current ? <p className="state" role="status">Đang tải hội thoại...</p> : <>
              {!current.messages.length && <p className="state">Hội thoại chưa có tin nhắn.</p>}
              {current.messages.map(m => <div key={m.id} className={`bubble ${m.sender_type === 'customer' ? 'customer' : m.sender_type === 'agent' ? 'staff' : 'ai'}`}><b>{senders[m.sender_type] || m.sender_type}</b><div className="messageContent">{m.content}</div><time>{timeOf(m.created_at)}</time></div>)}
              <section className="tickets" aria-label="Ticket hỗ trợ"><h3>Ticket hỗ trợ ({current.tickets.length})</h3>{!current.tickets.length ? <p>Chưa có ticket hỗ trợ.</p> : current.tickets.map(t => <article key={t.id} className="ticket"><b>{statuses[t.status] || t.status} · {priorities[t.priority] || t.priority}</b><p>{t.summary || 'Chưa có tóm tắt.'}</p><small>#{t.id} · {timeOf(t.created_at)}</small></article>)}</section>
            </>}
          </div>
          {current && <div className="composer"><p>Chế độ xem hội thoại</p></div>}
        </div>
        <div className="profile"><h3>Thông tin khách hàng</h3>{current ? <><div className="profileUser"><div className="avatar big">{initials(nameOf(current))}</div><div><b>{nameOf(current)}</b><small>{current.customer_id}</small></div></div><p>{current.customer_email || 'Chưa có email'}</p><hr /><h4>Hội thoại</h4><p>Kênh: {current.channel}</p><p>Trạng thái: {statuses[current.status] || current.status}</p><p>Ưu tiên: {priorities[current.priority] || current.priority}</p><h4>Ticket hỗ trợ</h4><p>{current.tickets.length} ticket</p></> : <p>Thông tin xuất hiện khi tải xong hội thoại.</p>}</div>
      </section>
    </main>
  </div>;
}

createRoot(document.getElementById('root')).render(<App />);
