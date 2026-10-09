import React, { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, Search, Plus, RefreshCw, X, MessagesSquare, UsersRound, ShoppingBag, BookOpen, TicketCheck, MessageCircle } from 'lucide-react';
import './workspace.css';

const orderLabels = { processing: 'Đang xử lý', paid: 'Đã thanh toán', shipping: 'Đang giao', shipped: 'Đã gửi hàng', delivered: 'Đã giao', cancelled: 'Đã hủy' };
const chatLabels = { open: 'AI đang hỗ trợ', handoff_requested: 'Chờ tiếp nhận', assigned: 'Nhân viên phụ trách', resolved: 'Đã giải quyết', closed: 'Đã đóng' };
const slaLabels = { met: 'Phản hồi đúng hạn', breached: 'Phản hồi trễ', on_track: 'Đang chờ, trong hạn', overdue: 'Đang chờ, quá hạn', cancelled: 'Kết thúc trước phản hồi' };
const fieldsOf = (event) => Object.fromEntries(new FormData(event.currentTarget));
const labelOf = (labels, value) => labels[value] || value;
const number = value => value == null ? 'Chưa có' : value.toLocaleString('vi-VN');

function useData(path, request, onExpired, refreshOnFocus = false) {
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

function LoadState({ state }) {
  return <>{state.loading && <p className="state" role="status">{state.data ? 'Đang cập nhật dữ liệu...' : 'Đang tải dữ liệu...'}</p>}{state.error && <div className="workspaceError" role="alert"><p>{state.error}{state.data && ' Dữ liệu hiển thị có thể đã cũ.'}</p><button onClick={state.reload}>Thử lại</button></div>}</>;
}

function Pager({ total, offset, setOffset }) {
  return <div className="pager"><span>{total ? `${offset + 1}–${Math.min(offset + 25, total)} / ${total}` : 'Không có kết quả'}</span><div><button disabled={!offset} onClick={() => setOffset(Math.max(0, offset - 25))}>Trước</button><button disabled={offset + 25 >= total} onClick={() => setOffset(offset + 25)}>Sau</button></div></div>;
}

function Badge({ value, labels = orderLabels }) {
  return <span className={`recordBadge record-${value}`}>{labelOf(labels, value)}</span>;
}

function Metrics({ page, request, onExpired, navigate }) {
  const [days, setDays] = useState(7);
  const state = useData(`/workspace/summary?days=${days}`, request, onExpired, true);
  const mine = useData(page === 'overview' ? '/inbox/conversations?assignment=mine&status=assigned&limit=1' : null, request, onExpired, true);
  const overdue = useData(page === 'overview' ? '/inbox/conversations?sla=overdue&limit=1' : null, request, onExpired, true);
  const data = state.data, period = data?.period;
  const overview = page === 'overview';
  const sources = overview ? [state, mine, overdue] : [state];
  const updatedAt = sources.every(source => source.updatedAt) ? sources.map(source => source.updatedAt).sort()[0] : null;
  return <section className="management"><header><div><p className="eyebrow">SUPPORT WORKSPACE</p><h1>{overview ? 'Tổng quan' : 'Phân tích hỗ trợ'}</h1><p>{overview ? 'Nắm tình hình và tiếp tục công việc trong ngày.' : 'Theo dõi lưu lượng hội thoại và phản hồi nhân viên.'}</p></div><div className="toolbar"><label>Khoảng thống kê<select value={days} onChange={e => setDays(Number(e.target.value))}>{[7, 30, 90].map(n => <option key={n} value={n}>{n} ngày</option>)}</select></label><button onClick={() => { state.reload(); mine.reload(); overdue.reload(); }} disabled={state.loading}><RefreshCw size={16} />Làm mới</button></div></header>
    <p className="dashboardSync" role="status">{sources.some(source => source.error) ? 'Cập nhật thất bại · Số liệu có thể đã cũ.' : sources.some(source => source.loading) ? 'Đang cập nhật...' : 'Đã cập nhật.'} {updatedAt ? <>Cập nhật gần nhất: <time dateTime={updatedAt}>{new Date(updatedAt).toLocaleString('vi-VN')}</time>.</> : 'Chưa đủ số liệu mới.'} Tự làm mới khi quay lại tab.</p>
    <LoadState state={state} />{data && <>
      {overview && <section className="workQueue" aria-label="Hội thoại cần xử lý"><h2>Cần xử lý hiện tại</h2><p>Hội thoại hiện tại, không giới hạn theo khoảng thống kê.</p><LoadState state={mine} /><LoadState state={overdue} /><div className="quickLinks">{[['Chờ tiếp nhận', data.conversation_statuses.handoff_requested || 0, { status: 'handoff_requested' }], ['Quá hạn phản hồi', overdue.data?.total, { sla: 'overdue' }], ['Bạn đang phụ trách', mine.data?.total, { assignment: 'mine', status: 'assigned' }]].map(([title, count, filters]) => <button key={title} onClick={() => navigate('inbox', filters)}><div><b>{title}</b><small>{count == null ? 'Chưa có số liệu' : `${number(count)} hội thoại`} · Mở danh sách</small></div><ArrowUpRight size={20} aria-hidden="true" /></button>)}</div></section>}
      <div className="stats workspaceStats">{(overview ? [['Hội thoại', data.totals.conversations], ['Khách hàng', data.totals.customers], ['Đơn hàng', data.totals.orders], ['Tài liệu', data.totals.documents]] : [['Hội thoại mới', period.conversations], ['Tin nhắn', period.messages], ['Ticket mới', period.tickets], ['Ticket đã phản hồi', period.responded_tickets]]).map(([label, value], index) => { const Icon = (overview ? [MessagesSquare, UsersRound, ShoppingBag, BookOpen] : [MessagesSquare, MessageCircle, TicketCheck, TicketCheck])[index]; return <div key={label}><span className="statIcon"><Icon size={20} aria-hidden="true" /></span><small>{label}</small><b>{number(value)}</b><span>{overview ? 'Toàn bộ dữ liệu' : `Trong ${days} ngày`}</span></div>; })}</div>
      <div className="reportGrid"><article className="workspaceCard"><h2>{overview ? 'Trạng thái hội thoại' : 'Hội thoại theo ngày'}</h2><p>{overview ? 'Trạng thái hiện tại của toàn bộ hội thoại.' : 'Ngày tạo hội thoại, tính theo UTC.'}</p><div className="metricRows">{(overview ? Object.entries(chatLabels).map(([key, label]) => ({ label, count: data.conversation_statuses[key] || 0 })) : period.daily.map(d => ({ label: d.date, count: d.count }))).map(row => <div className="metricRow" key={row.label}><span>{row.label}</span><meter min="0" max={Math.max(1, ...(overview ? [data.totals.conversations] : period.daily.map(d => d.count)))} value={row.count} aria-label={row.label} /><b>{number(row.count)}</b></div>)}</div></article>
        <article className="workspaceCard"><h2>SLA phản hồi đầu tiên</h2><p>Ticket tạo trong {days} ngày; tính 24/7.</p><div className="slaNumbers"><div><b>{period.sla_met_percent == null ? 'Chưa có' : `${period.sla_met_percent}%`}</b><small>Đúng hạn / ticket đã phản hồi</small></div><div><b>{period.mean_response_minutes == null ? 'Chưa có' : `${number(period.mean_response_minutes)} phút`}</b><small>Thời gian phản hồi trung bình</small></div></div>{Object.entries(slaLabels).map(([key, label]) => <div className="summaryLine" key={key}><span>{label}</span><strong>{period.sla[key]}</strong></div>)}</article>
        <article className="workspaceCard"><h2>Kênh tiếp nhận</h2><p>Hội thoại tạo trong khoảng thống kê.</p>{Object.entries(period.channels).length ? Object.entries(period.channels).map(([name, count]) => <div className="summaryLine" key={name}><span>{name}</span><strong>{count}</strong></div>) : <p>Chưa có hội thoại trong khoảng này.</p>}</article>
        <article className="workspaceCard"><h2>Đơn hàng hiện tại</h2>{Object.entries(data.order_statuses).length ? Object.entries(data.order_statuses).map(([status, count]) => <div className="summaryLine" key={status}><Badge value={status} /><strong>{count}</strong></div>) : <p>Chưa có đơn hàng.</p>}</article></div>
      <p className="syncNote">Khoảng thống kê: {data.start.slice(0, 10)} đến {data.end.slice(0, 10)} (UTC). SLA chưa phản hồi được tách riêng; số liệu này không đo độ chính xác RAG.</p>
    </>}
  </section>;
}

function RecordForm({ kind, record, request, onExpired, onSaved }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const customer = kind === 'customers';
  async function save(event) {
    event.preventDefault();
    const body = fieldsOf(event);
    if (customer) body.email = body.email.trim() || null;
    else { body.tracking_code = body.tracking_code.trim() || null; if (!record) body.id = body.id.trim().toUpperCase(); }
    if (record) body.expected = customer ? { display_name: record.display_name, email: record.email } : { status: record.status, tracking_code: record.tracking_code };
    setBusy(true); setError('');
    try { await request(`/workspace/${kind}${record ? `/${encodeURIComponent(record.id)}` : ''}`, { method: record ? 'PATCH' : 'POST', body: JSON.stringify(body) }); onSaved(); }
    catch (e) { setError(e.message); if (e.status === 401) onExpired(); }
    finally { setBusy(false); }
  }
  return <form className="recordForm" onSubmit={save}><fieldset disabled={busy}>
    {customer ? <><label>Tên khách hàng<input name="display_name" defaultValue={record?.display_name || ''} required maxLength={160} /></label><label>Email<input name="email" type="email" defaultValue={record?.email || ''} maxLength={255} /></label></> : <>
      {!record && <><label>Mã đơn<input name="id" required maxLength={64} pattern="(DH|ORD)[-_]?[A-Za-z0-9]{4,}" placeholder="ORD-DEMO03" /></label><CustomerPicker request={request} onExpired={onExpired} /></>}
      <label>Trạng thái<select name="status" defaultValue={record?.status || 'processing'}>{Object.entries(orderLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label><label>Mã vận đơn<input name="tracking_code" maxLength={100} defaultValue={record?.tracking_code || ''} /></label>
    </>}
    {error && <p role="alert" className="workspaceError">{error}</p>}<button className="primary" type="submit">{busy ? 'Đang lưu...' : record ? 'Lưu thay đổi' : customer ? 'Tạo khách hàng' : 'Tạo đơn hàng'}</button>
  </fieldset></form>;
}

function CustomerPicker({ request, onExpired }) {
  const [q, setQ] = useState(''), [selected, setSelected] = useState('');
  const state = useData(`/workspace/customers?${new URLSearchParams({ q, limit: 25 })}`, request, onExpired);
  return <div><label>Tìm khách để gắn đơn<input value={q} onChange={e => { setQ(e.target.value); setSelected(''); }} placeholder="Tên, email hoặc mã khách" /></label><LoadState state={state} /><label>Khách hàng<select name="customer_id" required value={selected} onChange={e => setSelected(e.target.value)}><option value="">Chọn khách hàng</option>{state.data?.items.map(c => <option value={c.id} key={c.id}>{c.display_name} · {c.email || c.id}</option>)}</select></label>{state.data && <small>{state.data.total} kết quả; hiển thị tối đa 25. Nhập thêm để thu hẹp tìm kiếm.</small>}</div>;
}

function CustomerDetail({ id, request, onExpired, user, onSaved, openInbox, openOrders }) {
  const state = useData(`/workspace/customers/${encodeURIComponent(id)}`, request, onExpired);
  const record = state.data;
  return <><LoadState state={state} />{record && <><p className="recordId">{record.id}</p>{user.role === 'admin' ? <RecordForm key={JSON.stringify(record)} kind="customers" record={record} request={request} onExpired={onExpired} onSaved={() => { state.reload(); onSaved(); }} /> : <><h3>{record.display_name}</h3><p>{record.email || 'Chưa có email'}</p></>}
    <h3>Lịch sử hỗ trợ ({record.conversation_count})</h3><p className="syncNote">Tối đa 20 hội thoại gần nhất.</p>{record.conversations.length ? record.conversations.map(c => <button className="relatedRecord" key={c.id} onClick={() => openInbox(c.id)}><span>{c.channel}<small>{c.id}</small></span><Badge value={c.status} labels={chatLabels} /></button>) : <p>Chưa có hội thoại.</p>}
    <h3>Đơn hàng ({record.order_count})</h3>{record.orders.slice(0, 5).map(o => <div className="summaryLine" key={o.id}><span>{o.id}</span><Badge value={o.status} /></div>)}<button onClick={() => openOrders(record.id)}>Xem đơn của khách <ArrowUpRight size={16} /></button>
  </>}</>;
}

function OrderAccessControls({ orderId, request, onExpired }) {
  const [access, setAccess] = useState(null), [busy, setBusy] = useState(false);
  const [error, setError] = useState(''), [notice, setNotice] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  async function change(revoke) {
    if (!revoke && !confirmed) return;
    setBusy(true); setError(''); setNotice(''); setAccess(null); setConfirmed(false);
    try {
      const result = await request(`/workspace/orders/${encodeURIComponent(orderId)}/access-code`, { method: revoke ? 'DELETE' : 'POST' });
      if (revoke) setNotice('Đã thu hồi mã và quyền tra cứu của đơn này.');
      else setAccess(result);
    } catch (e) { setError(e.message); if (e.status === 401) onExpired(); }
    finally { setBusy(false); }
  }
  return <section className="recordForm" aria-label="Quyền tra cứu đơn"><h3>Mã truy cập đơn hàng</h3>
    <p>Mã chỉ mở quyền xem đơn này trong một phiên chat, hết hạn sau 15 phút kể từ lúc cấp. Không xác minh toàn bộ tài khoản khách.</p>
    <p>Giao mã qua kênh liên hệ đã xác minh của chủ đơn. Không gửi mã vào hội thoại đang yêu cầu xác minh.</p>
    <label className="accessConfirmation"><input type="checkbox" checked={confirmed} disabled={busy} onChange={e => setConfirmed(e.target.checked)} />Đã xác minh người nhận qua kênh tin cậy. Cấp mã mới sẽ thu hồi mã và quyền cũ của đơn này.</label>
    <div className="toolbar"><button disabled={busy || !confirmed} onClick={() => change(false)}>Cấp mã mới</button><button disabled={busy} onClick={() => change(true)}>Thu hồi quyền</button></div>
    {access && <><label>Mã chỉ hiển thị lần này<input readOnly value={access.code} autoComplete="off" spellCheck={false} onFocus={e => e.target.select()} /></label><p role="status">Hết hạn: {new Date(access.expires_at * 1000).toLocaleString('vi-VN')}. Khách nhập mã tại mục Quyền tra cứu đơn trong widget.</p><button onClick={() => setAccess(null)}>Ẩn mã</button></>}
    {notice && <p role="status">{notice}</p>}{error && <p className="workspaceError" role="alert">{error}</p>}
  </section>;
}

function Records({ kind, request, onExpired, user, openInbox, openOrders, route, updateNavigation }) {
  const { recordSearch: q, recordStatus: status, recordOffset: offset, recordId: selected, customerFilter: customerId } = route;
  const setSelected = value => updateNavigation({ recordId: value }, false);
  const [adding, setAdding] = useState(false), [notice, setNotice] = useState('');
  const detailPanel = useRef(null);
  useEffect(() => { if (selected || adding) detailPanel.current?.focus(); }, [selected, adding]);
  const customer = kind === 'customers';
  const state = useData(`/workspace/${kind}?${new URLSearchParams({ q, offset, ...(status && { status }), ...(!customer && customerId && { customer_id: customerId }) })}`, request, onExpired);
  const record = state.data?.items.find(item => item.id === selected);
  const saved = () => { setNotice('Đã lưu dữ liệu.'); setAdding(false); state.reload(); };
  const filter = key => event => updateNavigation({ [key]: event.target.value, recordOffset: 0, recordId: null });
  return <section className="management"><header><div><p className="eyebrow">CUSTOMER OPERATIONS</p><h1>{customer ? 'Khách hàng' : 'Đơn hàng'}</h1><p>{customer ? 'Hồ sơ, lịch sử hội thoại và đơn hàng tại một nơi.' : 'Tra trạng thái đơn hàng và thông tin vận chuyển.'}</p></div><div className="toolbar"><button onClick={state.reload} disabled={state.loading}><RefreshCw size={16} />Làm mới</button>{user.role === 'admin' && <button className="primary" onClick={() => { setAdding(true); setSelected(null); setNotice(''); }}><Plus size={16} />{customer ? 'Thêm khách hàng' : 'Tạo đơn hàng'}</button>}</div></header>
    <div className="recordFilters"><label className="search"><Search size={16} /><input aria-label={customer ? 'Tìm khách hàng' : 'Tìm đơn hàng'} maxLength={160} value={q} onChange={filter('recordSearch')} placeholder={customer ? 'Tên, email, mã khách...' : 'Mã đơn, tên khách, vận đơn...'} /></label>{!customer && <label>Trạng thái<select value={status} onChange={filter('recordStatus')}><option value="">Tất cả</option>{Object.entries(orderLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>}{customerId && !customer && <button onClick={() => updateNavigation({ customerFilter: '', recordOffset: 0, recordId: null })}>Bỏ lọc khách hàng <X size={16} /></button>}</div>
    {notice && <p role="status" className="workspaceNotice">{notice}</p>}<LoadState state={state} />
    <div className={`recordsLayout ${adding || selected ? 'withDetail' : ''}`}><div className="workspaceCard tableCard">{state.data && <><div className="tableScroll"><table className="recordTable" role="table"><caption className="visuallyHidden">{customer ? 'Danh sách khách hàng' : 'Danh sách đơn hàng'}</caption><thead role="rowgroup"><tr role="row"><th role="columnheader" scope="col">{customer ? 'Khách hàng' : 'Mã đơn'}</th><th role="columnheader" scope="col">{customer ? 'Email' : 'Khách hàng'}</th><th role="columnheader" scope="col">{customer ? 'Hội thoại' : 'Trạng thái'}</th><th role="columnheader" scope="col">{customer ? 'Đơn hàng' : 'Mã vận đơn'}</th></tr></thead><tbody role="rowgroup">{state.data.items.map(item => <tr role="row" key={item.id} className={selected === item.id ? 'selectedRecord' : ''}><td role="cell" data-label={customer ? 'Khách hàng' : 'Mã đơn'}><button className="recordLink" onClick={() => { setSelected(item.id); setAdding(false); setNotice(''); }}>{customer ? item.display_name : item.id}</button>{customer && <small className="recordId">{item.id}</small>}</td><td role="cell" data-label={customer ? 'Email' : 'Khách hàng'}>{customer ? item.email || 'Chưa có' : item.customer_name}</td><td role="cell" data-label={customer ? 'Hội thoại' : 'Trạng thái'}>{customer ? item.conversation_count : <Badge value={item.status} />}</td><td role="cell" data-label={customer ? 'Đơn hàng' : 'Mã vận đơn'}>{customer ? item.order_count : item.tracking_code || 'Chưa có'}</td></tr>)}</tbody></table></div>{!state.data.items.length && <p className="state">Không có {customer ? 'khách hàng' : 'đơn hàng'} phù hợp.</p>}<Pager total={state.data.total} offset={offset} setOffset={value => updateNavigation({ recordOffset: value, recordId: null }, false)} /></>}</div>
      {(adding || selected) && <section ref={detailPanel} tabIndex={-1} className="workspaceCard detailCard" aria-label="Chi tiết bản ghi"><div className="panelTitle"><h2>{adding ? customer ? 'Thêm khách hàng' : 'Tạo đơn hàng' : customer ? 'Hồ sơ khách hàng' : 'Thông tin đơn hàng'}</h2><button aria-label="Đóng chi tiết" onClick={() => { setSelected(null); setAdding(false); }}><X size={18} /></button></div>
        {adding ? <RecordForm key={`new-${kind}`} kind={kind} request={request} onExpired={onExpired} onSaved={saved} /> : customer ? <CustomerDetail key={selected} id={selected} request={request} onExpired={onExpired} user={user} onSaved={saved} openInbox={openInbox} openOrders={openOrders} /> : record ? <><p className="recordId">{record.id}</p><h3>{record.customer_name}</h3><p className="recordId">Mã khách: {record.customer_id}</p>{user.role === 'admin' ? <RecordForm key={JSON.stringify(record)} kind={kind} record={record} request={request} onExpired={onExpired} onSaved={saved} /> : <><Badge value={record.status} /><p>Mã vận đơn: {record.tracking_code || 'Chưa có'}</p></>}</> : <p>Đang tải hoặc bản ghi không còn trong bộ lọc.</p>}
        {!customer && record && !adding && user.role === 'admin' && <OrderAccessControls key={record.id} orderId={record.id} request={request} onExpired={onExpired} />}
      </section>}
    </div><p className="syncNote">{customer ? 'Tên và email không xác minh quyền sở hữu đơn hàng của khách widget.' : 'Dữ liệu đơn hàng nội bộ phục vụ đồ án. Chỉ admin được tạo và cập nhật; chủ đơn không đổi qua màn hình này.'}</p>
  </section>;
}

function PasswordForm({ request, onExpired }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function submit(event) {
    event.preventDefault();
    const { current_password, new_password, confirm } = fieldsOf(event);
    if (new_password !== confirm) { setError('Mật khẩu xác nhận không khớp.'); return; }
    setBusy(true); setError('');
    try { const result = await request('/workspace/password', { method: 'POST', body: JSON.stringify({ current_password, new_password }) }); onExpired(result.message); }
    catch (e) { setError(e.message); if (e.status === 401) onExpired(); }
    finally { setBusy(false); }
  }
  return <form className="recordForm" onSubmit={submit}><fieldset disabled={busy}><label>Mật khẩu hiện tại<input type="password" name="current_password" autoComplete="current-password" required maxLength={128} /></label><label>Mật khẩu mới<input type="password" name="new_password" autoComplete="new-password" required minLength={12} maxLength={128} /></label><label>Nhập lại mật khẩu mới<input type="password" name="confirm" autoComplete="new-password" required minLength={12} maxLength={128} /></label><small>12–128 ký tự. Đổi thành công sẽ đăng xuất mọi phiên của tài khoản này.</small>{error && <p className="workspaceError" role="alert">{error}</p>}<button className="primary">{busy ? 'Đang đổi...' : 'Đổi mật khẩu'}</button></fieldset></form>;
}

function StaffAccounts({ request, onExpired }) {
  const [offset, setOffset] = useState(0), [busy, setBusy] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('');
  const state = useData(`/workspace/users?offset=${offset}`, request, onExpired);
  async function create(event) {
    event.preventDefault(); const form = event.currentTarget; const body = fieldsOf(event);
    setBusy(true); setError(''); setNotice('');
    try { const user = await request('/auth/users', { method: 'POST', body: JSON.stringify(body) }); form.reset(); setNotice(`Đã tạo tài khoản ${user.username}.`); state.reload(); }
    catch (e) { setError(e.message); if (e.status === 401) onExpired(); }
    finally { setBusy(false); }
  }
  return <article className="workspaceCard"><h2>Tài khoản nhân viên</h2><p>Admin cấp tài khoản riêng cho từng người.</p><form className="recordForm" onSubmit={create}><fieldset disabled={busy}><div className="formGrid"><label>Tên đăng nhập<input name="username" required maxLength={64} pattern="[a-zA-Z0-9_.-]+" autoComplete="off" /></label><label>Tên hiển thị<input name="display_name" required maxLength={160} /></label><label>Mật khẩu ban đầu<input name="password" type="password" required minLength={12} maxLength={128} autoComplete="new-password" /></label><label>Vai trò<select name="role" defaultValue="agent"><option value="agent">Nhân viên</option><option value="admin">Quản trị viên</option></select></label></div>{error && <p className="workspaceError" role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}<button className="primary">{busy ? 'Đang tạo...' : 'Tạo tài khoản'}</button></fieldset></form><LoadState state={state} />{state.data && <><div className="tableScroll"><table><caption className="visuallyHidden">Tài khoản nhân viên</caption><thead><tr><th>Tài khoản</th><th>Họ tên</th><th>Vai trò</th><th>Trạng thái</th></tr></thead><tbody>{state.data.items.map(u => <tr key={u.id}><td>{u.username}</td><td>{u.display_name}</td><td>{u.role === 'admin' ? 'Quản trị viên' : 'Nhân viên'}</td><td>{u.active ? 'Hoạt động' : 'Đã khóa'}</td></tr>)}</tbody></table></div><Pager total={state.data.total} offset={offset} setOffset={setOffset} /></>}</article>;
}

function SettingsPage({ user, request, onExpired }) {
  const state = useData('/workspace/settings', request, onExpired);
  return <section className="management"><header><div><p className="eyebrow">WORKSPACE SETTINGS</p><h1>Cài đặt</h1><p>Tài khoản, bảo mật và thông tin vận hành.</p></div></header><LoadState state={state} /><div className="reportGrid"><article className="workspaceCard"><h2>Tài khoản của bạn</h2><div className="summaryLine"><span>Tên hiển thị</span><strong>{user.display_name}</strong></div><div className="summaryLine"><span>Đăng nhập</span><strong>{user.username}</strong></div><div className="summaryLine"><span>Vai trò</span><strong>{user.role === 'admin' ? 'Quản trị viên' : 'Nhân viên'}</strong></div><h3>Đổi mật khẩu</h3><PasswordForm request={request} onExpired={onExpired} /></article><article className="workspaceCard"><h2>Kênh hỗ trợ</h2>{state.data?.channels.map(channel => <div className="summaryLine" key={channel.name}><span>{channel.name}<small className="syncNote">{channel.detail}</small></span><Badge value={channel.status} labels={{ available: 'Sẵn sàng', connected: 'Đã kết nối', connecting: 'Đang kết nối', error: 'Lỗi kết nối', not_connected: 'Chưa kết nối' }} /></div>)}<h3>Chính sách SLA hiện tại</h3><p>Phản hồi đầu tiên, tính 24/7.</p>{Object.entries(state.data?.sla_minutes || {}).map(([key, minutes]) => <div className="summaryLine" key={key}><span>{{ urgent: 'Khẩn cấp', high: 'Cao', normal: 'Bình thường', low: 'Thấp' }[key]}</span><strong>{minutes} phút</strong></div>)}<p className="syncNote">Chính sách cố định cho bản đồ án; chưa hỗ trợ chỉnh lịch làm việc và hạn SLA.</p></article></div>{user.role === 'admin' && <StaffAccounts request={request} onExpired={onExpired} />}</section>;
}

export default function Workspace({ page, ...props }) {
  if (page === 'overview' || page === 'analytics') return <Metrics page={page} {...props} />;
  if (page === 'settings') return <SettingsPage {...props} />;
  return <Records kind={page} {...props} />;
}
