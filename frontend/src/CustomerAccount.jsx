import React, { useEffect, useState } from 'react';
import { RichText, plainText } from './RichText';
import { LockKeyhole, Search as SearchIcon, UserRound } from 'lucide-react';
import { EmailVerification } from './CustomerEmail';
import PasswordRules from './PasswordRules';
import { citationLabel, conversationStatuses, formatDateTime } from './shared';

const labels = conversationStatuses;
const senderLabels = { customer: 'Bạn', ai: 'Trợ lý AI', agent: 'Nhân viên', system: 'Thông báo' };
const date = formatDateTime;
const vnDay = value => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Ho_Chi_Minh' }).format(new Date(value));
function dayGroup(value) {
  const days = Math.round((Date.parse(vnDay(Date.now())) - Date.parse(vnDay(value))) / 86400000);
  return days <= 0 ? 'Hôm nay' : days < 7 ? '7 ngày qua' : 'Trước đó';
}

export function CustomerHistory({ request, onExpired, currentId, onOpenChat }) {
  const [offset, setOffset] = useState(0), [list, setList] = useState(null), [selected, setSelected] = useState(null);
  const [cursors, setCursors] = useState([]), [detail, setDetail] = useState(null), [error, setError] = useState('');
  const [loading, setLoading] = useState(false), [refresh, setRefresh] = useState(0);
  const [status, setStatus] = useState(''), [search, setSearch] = useState(''), [query, setQuery] = useState('');
  const before = cursors.at(-1) || null;
  // Wait for a pause in typing before searching; a new filter always starts from the first page.
  useEffect(() => { const timer = setTimeout(() => setQuery(search.trim()), 350); return () => clearTimeout(timer); }, [search]);
  useEffect(() => setOffset(0), [status, query]);
  useEffect(() => {
    const controller = new AbortController(); setList(null); setError(''); setSelected(null); setDetail(null); setCursors([]);
    const params = new URLSearchParams({ offset, ...(status && { status }), ...(query && { q: query }) });
    request('/account/conversations?' + params, { signal: controller.signal }).then(data => {
      if (controller.signal.aborted) return;
      if (!Array.isArray(data.items)) throw new Error('Dữ liệu lịch sử không hợp lệ.');
      setList(data); setSelected(data.items[0]?.id || null);
    }).catch(e => { if (!controller.signal.aborted) { if (e.status === 401) onExpired(); else setError(e.message); } });
    return () => controller.abort();
  }, [offset, refresh, status, query]);
  useEffect(() => {
    if (!selected) return;
    const controller = new AbortController(); setLoading(true); setError(''); setDetail(null);
    const query = new URLSearchParams({ limit: 50, ...(before && { before }) });
    request('/account/conversations/' + encodeURIComponent(selected) + '?' + query, { signal: controller.signal }).then(data => {
      if (controller.signal.aborted) return;
      if (data.conversation_id !== selected || !Array.isArray(data.messages) || data.message_page?.before !== before) throw new Error('Dữ liệu hội thoại không hợp lệ.');
      setDetail(data);
    }).catch(e => { if (!controller.signal.aborted) { if (e.status === 401) onExpired(); else setError(e.message); } })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [selected, before, refresh]);
  const groups = [];
  for (const item of list?.items || []) {
    const name = dayGroup(item.created_at), last = groups.at(-1);
    if (last?.name === name) last.items.push(item); else groups.push({ name, items: [item] });
  }
  const current = list?.items.find(item => item.id === selected);
  return <section className="portalPage historyPage">
    <div className="historyPane">
      <div className="portalPageHead"><div><h1>Lịch sử trò chuyện</h1><p>Lưu theo tài khoản, xem được trên mọi thiết bị.</p></div></div>
      <label className="historySearch"><span className="srOnly">Tìm trong lịch sử</span><SearchIcon size={16} aria-hidden="true" /><input type="search" value={search} maxLength={100} onChange={event => setSearch(event.target.value)} placeholder="Tìm trong tin nhắn..." /></label>
      <div className="historyChips" role="group" aria-label="Trạng thái">{[['', 'Tất cả'], ...Object.entries(labels)].map(([value, label]) => <button type="button" key={value} aria-pressed={status === value} onClick={() => setStatus(value)}>{label}</button>)}</div>
      {error && <p role="alert" className="widgetError">{error} <button onClick={() => setRefresh(n => n + 1)}>Thử lại</button></p>}
      {!list && !error && <p className="historyState" role="status">Đang tải lịch sử...</p>}
      {list && <div className="accountHistoryList">{groups.map(group => <div className="historyGroup" key={group.name} role="group" aria-label={group.name}><h2>{group.name}</h2>
        {group.items.map(item => <button key={item.id} aria-pressed={selected === item.id} onClick={() => { setSelected(item.id); setCursors([]); }}><b>{item.preview ? plainText(item.preview) : 'Chưa có tin nhắn'}</b><span><em className={`statusPill status-${item.status}`}>{labels[item.status] || item.status}</em>{date(item.created_at)}{item.id === currentId ? ' · phiên hiện tại' : ''}</span></button>)}</div>)}
        {!list.items.length && <p className="historyState">{status || query ? 'Không có hội thoại khớp bộ lọc. Thử từ khóa khác hoặc chọn Tất cả.' : 'Chưa có hội thoại.'}</p>}</div>}
      {list && (offset > 0 || list.has_more) && <div className="accountPager"><button disabled={!offset} onClick={() => setOffset(n => Math.max(0, n - 20))}>Trang trước</button><span>{list.total} hội thoại</span><button disabled={!list.has_more} onClick={() => setOffset(n => n + 20)}>Trang sau</button></div>}
    </div>
    <div className="historyDetail" aria-busy={loading}>
      {current && <header className="historyDetailHead"><div><h2>{current.preview ? plainText(current.preview) : 'Hội thoại chưa có tin nhắn'}</h2><p>{date(current.created_at)} · Website{detail && !detail.message_page.has_more && !before ? ` · ${detail.messages.length} tin nhắn` : ''}</p></div><span className={`statusPill status-${current.status}`}>{labels[current.status] || current.status}</span></header>}
      {detail && (detail.message_page.has_more || cursors.length > 0) && <div className="accountPager"><button disabled={loading || !detail.message_page.has_more} onClick={() => setCursors(values => [...values, detail.message_page.next_before])}>Tin cũ hơn</button><button disabled={loading || !cursors.length} onClick={() => setCursors(values => values.slice(0, -1))}>Tin mới hơn</button></div>}
      <div className="accountMessages" role="log" aria-label="Nội dung hội thoại" tabIndex={0}>
        {loading && <p className="historyState" role="status">Đang tải tin nhắn...</p>}
        {detail?.messages.map(message => <article className={`widgetMessage from-${message.sender_type} ${message.sender_type === 'customer' ? 'widgetOwn' : ''}`} key={message.id}><b>{senderLabels[message.sender_type] || 'Hỗ trợ'} · <time dateTime={message.created_at}>{date(message.created_at)}</time></b><p><RichText text={message.content} /></p>{message.citations?.map((citation, index) => <details key={index}><summary><span className="srOnly">Nguồn: </span>{citationLabel(citation)}</summary><blockquote><RichText text={citation.quote} /></blockquote></details>)}</article>)}
        {detail && !detail.messages.length && <p className="historyState">Hội thoại chưa có tin nhắn.</p>}
        {list && !list.items.length && <p className="historyState">Chọn một hội thoại để xem lại.</p>}
      </div>
      {current && <footer className="historyFoot"><LockKeyhole size={15} aria-hidden="true" /><span>{current.id === currentId ? 'Đây là cuộc trò chuyện hiện tại.' : 'Chỉ xem lại. Cần hỗ trợ tiếp?'}</span>{onOpenChat && <button type="button" onClick={onOpenChat}>{current.id === currentId ? 'Tiếp tục trò chuyện' : 'Vào trò chuyện'}</button>}</footer>}
    </div>
  </section>;
}

export function CustomerProfile({ account, request, onExpired, onPasswordChanged, onLogout, logoutDisabled }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [newPassword, setNewPassword] = useState('');
  async function save(event) {
    event.preventDefault(); const fields = new FormData(event.currentTarget); setError('');
    if (fields.get('new_password') !== fields.get('confirm')) { setError('Mật khẩu nhập lại chưa khớp.'); return; }
    setBusy(true);
    try { await request('/account/password', { method: 'POST', body: JSON.stringify({ current_password: fields.get('current_password'), new_password: fields.get('new_password') }) }); onPasswordChanged(); }
    catch (e) { if (e.status === 401) onExpired(); else setError(e.message); }
    finally { setBusy(false); }
  }
  return <section className="portalPage customerProfile"><div className="portalPageHead"><div><h1>Tài khoản khách hàng</h1><p>{account.email}</p></div>{onLogout && <button type="button" className="profileLogout" onClick={onLogout} disabled={logoutDisabled}>Đăng xuất</button>}</div><div className="profileLayout"><div className="profileCard"><div className="profileAvatar"><UserRound size={26} /></div><div><h2>{account.email}</h2><p>Tài khoản khách hàng</p></div><span className={account.email_verified ? 'profileStatus verified' : 'profileStatus'}>{account.email_verified ? 'Đã xác minh' : 'Chưa xác minh'}</span></div><form className="portalOrderForm profilePassword" onSubmit={save}><fieldset disabled={busy}><h2>Đổi mật khẩu</h2><label>Mật khẩu hiện tại<input name="current_password" type="password" required maxLength={128} autoComplete="current-password" /></label><label>Mật khẩu mới<input name="new_password" type="password" required minLength={8} maxLength={128} pattern="(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9\s]).{8,128}" autoComplete="new-password" onChange={event => setNewPassword(event.target.value)} /></label><PasswordRules value={newPassword} /><label>Nhập lại mật khẩu mới<input name="confirm" type="password" required minLength={8} maxLength={128} pattern="(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9\s]).{8,128}" autoComplete="new-password" /></label><p>Tối thiểu 8 ký tự, gồm chữ hoa, chữ thường, số và ký tự đặc biệt. Đổi thành công sẽ đăng xuất tài khoản trên mọi thiết bị.</p>{error && <p role="alert" className="widgetError">{error}</p>}<button>{busy ? 'Đang đổi...' : 'Đổi mật khẩu'}</button></fieldset></form><div className="profileVerify"><EmailVerification account={account} request={request} onExpired={onExpired} /></div></div></section>;
}
