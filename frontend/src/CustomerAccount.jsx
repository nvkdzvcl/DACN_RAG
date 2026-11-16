import React, { useEffect, useState } from 'react';
import { RichText, plainText } from './RichText';
import { UserRound } from 'lucide-react';
import { EmailVerification } from './CustomerEmail';
import PasswordRules from './PasswordRules';
import { conversationStatuses, formatDateTime } from './shared';

const labels = conversationStatuses;
const senderLabels = { customer: 'Bạn', ai: 'Trợ lý AI', agent: 'Nhân viên', system: 'Thông báo' };
const date = formatDateTime;

export function CustomerHistory({ request, onExpired, currentId }) {
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
  return <section className="portalPage customerHistory"><div className="portalPageHead"><div><h1>Lịch sử trò chuyện</h1><p>Lịch sử được lưu theo tài khoản và xem được trên mọi thiết bị.</p></div></div>
    {error && <p role="alert" className="widgetError">{error} <button onClick={() => setRefresh(n => n + 1)}>Thử lại</button></p>}
    {!list && !error && <p role="status">Đang tải lịch sử...</p>}
    <div className="historyFilters"><label>Tìm trong lịch sử<input type="search" value={search} maxLength={100} onChange={event => setSearch(event.target.value)} placeholder="Nhập từ khóa trong tin nhắn..." /></label>
      <label>Trạng thái<select value={status} onChange={event => setStatus(event.target.value)}><option value="">Tất cả</option>{Object.entries(labels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div>
    {list && <><div className="accountHistoryList">{list.items.map(item => <button key={item.id} aria-pressed={selected === item.id} onClick={() => { setSelected(item.id); setCursors([]); }}><b>{item.preview ? plainText(item.preview) : 'Chưa có tin nhắn'}</b><span>{date(item.created_at)} · {labels[item.status] || item.status}{item.id === currentId ? ' · Phiên hiện tại' : ''}</span><small>#{item.id.slice(0, 8)}</small></button>)}</div>
      <div className="accountPager"><button disabled={!offset} onClick={() => setOffset(n => Math.max(0, n - 20))}>Trang trước</button><span>{list.total} hội thoại</span><button disabled={!list.has_more} onClick={() => setOffset(n => n + 20)}>Trang sau</button></div>
      {!list.items.length && <p>{status || query ? 'Không có hội thoại khớp bộ lọc. Thử từ khóa khác hoặc chọn Tất cả.' : 'Chưa có hội thoại.'}</p>}</>}
    {loading && <p role="status">Đang tải tin nhắn...</p>}
    {detail && <div className="accountHistoryDetail"><h2>Nội dung hội thoại</h2><p>Chế độ xem lịch sử. Vào Tin nhắn để tiếp tục phiên hiện tại.</p><div className="accountPager"><button disabled={loading || !detail.message_page.has_more} onClick={() => setCursors(values => [...values, detail.message_page.next_before])}>Tin cũ hơn</button><button disabled={loading || !cursors.length} onClick={() => setCursors(values => values.slice(0, -1))}>Tin mới hơn</button></div>
      <div className="accountMessages">{detail.messages.map(message => <article className={'widgetMessage ' + (message.sender_type === 'customer' ? 'widgetOwn' : '')} key={message.id}><b>{senderLabels[message.sender_type] || 'Hỗ trợ'}</b><p><RichText text={message.content} /></p>{message.citations?.map((citation, index) => <details key={index}><summary>Nguồn: {citation.source}{citation.location && ' · ' + citation.location}</summary><blockquote>{citation.quote}</blockquote></details>)}</article>)}{!detail.messages.length && <p>Hội thoại chưa có tin nhắn.</p>}</div></div>}
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
