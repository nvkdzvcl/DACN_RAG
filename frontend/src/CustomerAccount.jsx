import React, { useEffect, useState } from 'react';
import { EmailVerification } from './CustomerEmail';

const labels = { open: 'AI hỗ trợ', handoff_requested: 'Chờ nhân viên', assigned: 'Nhân viên hỗ trợ', resolved: 'Đã giải quyết', closed: 'Đã kết thúc' };
const senderLabels = { customer: 'Bạn', ai: 'Trợ lý AI', agent: 'Nhân viên', system: 'Thông báo' };
function date(value) {
  const parsed = new Date(/[zZ]$|[+-]\d{2}:\d{2}$/.test(value) ? value : value + 'Z');
  return Number.isNaN(parsed.getTime()) ? '' : parsed.toLocaleString('vi-VN');
}

export function CustomerHistory({ request, onExpired, currentId }) {
  const [offset, setOffset] = useState(0), [list, setList] = useState(null), [selected, setSelected] = useState(null);
  const [cursors, setCursors] = useState([]), [detail, setDetail] = useState(null), [error, setError] = useState('');
  const [loading, setLoading] = useState(false), [refresh, setRefresh] = useState(0);
  const before = cursors.at(-1) || null;
  useEffect(() => {
    const controller = new AbortController(); setList(null); setError(''); setSelected(null); setDetail(null); setCursors([]);
    request('/account/conversations?offset=' + offset, { signal: controller.signal }).then(data => {
      if (controller.signal.aborted) return;
      if (!Array.isArray(data.items)) throw new Error('Dữ liệu lịch sử không hợp lệ.');
      setList(data); setSelected(data.items[0]?.id || null);
    }).catch(e => { if (!controller.signal.aborted) { if (e.status === 401) onExpired(); else setError(e.message); } });
    return () => controller.abort();
  }, [offset, refresh]);
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
  return <section className="portalPage customerHistory"><div className="portalPageHead"><div><h1>Lịch sử trò chuyện</h1><p>Lịch sử được lưu theo tài khoản. Phiên khách vãng lai không tự ghép vào đây.</p></div></div>
    {error && <p role="alert" className="widgetError">{error} <button onClick={() => setRefresh(n => n + 1)}>Thử lại</button></p>}
    {!list && !error && <p role="status">Đang tải lịch sử...</p>}
    {list && <><div className="accountHistoryList">{list.items.map(item => <button key={item.id} aria-pressed={selected === item.id} onClick={() => { setSelected(item.id); setCursors([]); }}><b>{date(item.created_at)}</b><span>{labels[item.status] || item.status}{item.id === currentId ? ' · Phiên hiện tại' : ''}</span><small>#{item.id.slice(0, 8)}</small></button>)}</div>
      <div className="accountPager"><button disabled={!offset} onClick={() => setOffset(n => Math.max(0, n - 20))}>Trang trước</button><span>{list.total} hội thoại</span><button disabled={!list.has_more} onClick={() => setOffset(n => n + 20)}>Trang sau</button></div>
      {!list.items.length && <p>Chưa có hội thoại.</p>}</>}
    {loading && <p role="status">Đang tải tin nhắn...</p>}
    {detail && <div className="accountHistoryDetail"><h2>Nội dung hội thoại</h2><p>Chế độ xem lịch sử. Vào Tin nhắn để tiếp tục phiên hiện tại.</p><div className="accountPager"><button disabled={loading || !detail.message_page.has_more} onClick={() => setCursors(values => [...values, detail.message_page.next_before])}>Tin cũ hơn</button><button disabled={loading || !cursors.length} onClick={() => setCursors(values => values.slice(0, -1))}>Tin mới hơn</button></div>
      <div className="accountMessages">{detail.messages.map(message => <article className={'widgetMessage ' + (message.sender_type === 'customer' ? 'widgetOwn' : '')} key={message.id}><b>{senderLabels[message.sender_type] || 'Hỗ trợ'}</b><p>{message.content}</p>{message.citations?.map((citation, index) => <details key={index}><summary>Nguồn: {citation.source}{citation.location && ' · ' + citation.location}</summary><blockquote>{citation.quote}</blockquote></details>)}</article>)}{!detail.messages.length && <p>Hội thoại chưa có tin nhắn.</p>}</div></div>}
  </section>;
}

export function CustomerProfile({ account, request, onExpired, onPasswordChanged }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function save(event) {
    event.preventDefault(); const fields = new FormData(event.currentTarget); setError('');
    if (fields.get('new_password') !== fields.get('confirm')) { setError('Mật khẩu nhập lại chưa khớp.'); return; }
    setBusy(true);
    try { await request('/account/password', { method: 'POST', body: JSON.stringify({ current_password: fields.get('current_password'), new_password: fields.get('new_password') }) }); onPasswordChanged(); }
    catch (e) { if (e.status === 401) onExpired(); else setError(e.message); }
    finally { setBusy(false); }
  }
  return <section className="portalPage"><div className="portalPageHead"><div><h1>Tài khoản khách hàng</h1><p>{account.email}</p></div></div><EmailVerification account={account} request={request} onExpired={onExpired} /><form className="portalOrderForm" onSubmit={save}><fieldset disabled={busy}><h2>Đổi mật khẩu</h2><label>Mật khẩu hiện tại<input name="current_password" type="password" required maxLength={128} autoComplete="current-password" /></label><label>Mật khẩu mới<input name="new_password" type="password" required minLength={15} maxLength={128} autoComplete="new-password" /></label><label>Nhập lại mật khẩu mới<input name="confirm" type="password" required minLength={15} maxLength={128} autoComplete="new-password" /></label><p>15–128 ký tự. Đổi thành công sẽ đăng xuất tài khoản trên mọi thiết bị.</p>{error && <p role="alert" className="widgetError">{error}</p>}<button>{busy ? 'Đang đổi...' : 'Đổi mật khẩu'}</button></fieldset></form></section>;
}
