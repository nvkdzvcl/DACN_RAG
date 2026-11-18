import React, { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, Search, Plus, RefreshCw, X } from 'lucide-react';
import './workspace.css';
import useData from './useData';
import LoadState from './LoadState';
import Overview from './Overview';
import Analytics from './Analytics';
import PasswordRules from './PasswordRules';
import { conversationStatuses, formatDateTime, shortId } from './shared';

const orderLabels = { processing: 'Đang xử lý', paid: 'Đã thanh toán', shipping: 'Đang giao', shipped: 'Đã gửi hàng', delivered: 'Đã giao', cancelled: 'Đã hủy' };
const chatLabels = conversationStatuses;
const fieldsOf = (event) => Object.fromEntries(new FormData(event.currentTarget));
const labelOf = (labels, value) => labels[value] || value;



function Pager({ total, offset, setOffset }) {
  return <div className="pager"><span>{total ? `${offset + 1}–${Math.min(offset + 25, total)} / ${total}` : 'Không có kết quả'}</span><div><button disabled={!offset} onClick={() => setOffset(Math.max(0, offset - 25))}>Trước</button><button disabled={offset + 25 >= total} onClick={() => setOffset(offset + 25)}>Sau</button></div></div>;
}

function Badge({ value, labels = orderLabels }) {
  // One color per status everywhere: the same pills as the customer pages and the inbox.
  return <span className={`statusPill ${labels === orderLabels ? 'order' : 'status'}-${value}`}>{labelOf(labels, value)}</span>;
}

const SHIPPED = ['shipping', 'shipped', 'delivered'];
// Same rule as the API: upper case, no spaces, letters, digits and inner dashes, 8-30 characters.
const normalizeTracking = value => value.replace(/\s+/g, '').toUpperCase();
const TRACKING_PATTERN = '[A-Z0-9][A-Z0-9\\-]{6,28}[A-Z0-9]';

function RecordForm({ kind, record, request, onExpired, onSaved }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [status, setStatus] = useState(record?.status || 'processing'), [tracking, setTracking] = useState(record?.tracking_code || '');
  const customer = kind === 'customers';
  async function save(event) {
    event.preventDefault();
    const body = fieldsOf(event);
    if (customer) body.email = body.email.trim() || null;
    else {
      body.tracking_code = tracking || null;
      // The server generates the order ID (DH + date + 4 characters).
      if (!record && !body.customer_id) { setError('Chọn khách hàng cho đơn.'); return; }
    }
    if (record) body.expected = customer ? { display_name: record.display_name, email: record.email } : { status: record.status, tracking_code: record.tracking_code };
    setBusy(true); setError('');
    try { onSaved(await request(`/workspace/${kind}${record ? `/${encodeURIComponent(record.id)}` : ''}`, { method: record ? 'PATCH' : 'POST', body: JSON.stringify(body) })); }
    catch (e) { setError(e.message); if (e.status === 401) onExpired(); }
    finally { setBusy(false); }
  }
  return <form className="recordForm" onSubmit={save}><fieldset disabled={busy}>
    {customer ? <><label>Tên khách hàng<input name="display_name" defaultValue={record?.display_name || ''} required maxLength={160} /></label><label>Email<input name="email" type="email" defaultValue={record?.email || ''} maxLength={255} placeholder="Không bắt buộc" /></label></> : <>
      {!record && <CustomerPicker request={request} onExpired={onExpired} />}
      <label>Trạng thái<select name="status" value={status} onChange={e => setStatus(e.target.value)}>{Object.entries(orderLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
      <label>Mã vận đơn<input name="tracking_code" value={tracking} onChange={e => setTracking(normalizeTracking(e.target.value))} maxLength={30} pattern={TRACKING_PATTERN} title="8–30 ký tự: chữ in hoa, số và dấu gạch ngang ở giữa." placeholder="VD: VN123456789" autoComplete="off" spellCheck={false} />
        <small className={SHIPPED.includes(status) && !tracking ? 'fieldWarn' : undefined}>{SHIPPED.includes(status) && !tracking ? 'Đơn đã gửi đi thường cần mã vận đơn để khách tra cứu.' : 'Tự viết hoa và bỏ khoảng trắng. Để trống nếu chưa gửi hàng.'}</small></label>
    </>}
    {error && <p role="alert" className="workspaceError">{error}</p>}<button className="primary wide" type="submit">{busy ? 'Đang lưu...' : record ? 'Lưu thay đổi' : customer ? 'Lưu khách hàng mới' : 'Lưu đơn mới'}</button>
  </fieldset></form>;
}

function CustomerPicker({ request, onExpired }) {
  const [q, setQ] = useState(''), [query, setQuery] = useState(''), [chosen, setChosen] = useState(null);
  useEffect(() => { const timer = setTimeout(() => setQuery(q.trim()), 250); return () => clearTimeout(timer); }, [q]);
  const state = useData(chosen ? null : `/workspace/customers?${new URLSearchParams({ q: query, limit: 6 })}`, request, onExpired);
  const items = state.data?.items || [];
  const input = useRef(null);
  return <div className="customerPicker"><input type="hidden" name="customer_id" value={chosen?.id || ''} />
    {chosen ? <><span className="pickerLabel">Khách hàng</span><div className="pickedCustomer"><span><b>{chosen.display_name}</b><small>{chosen.email || shortId(chosen.id)}</small></span><button type="button" onClick={() => { setChosen(null); setTimeout(() => input.current?.focus()); }}>Đổi khách</button></div></>
      : <><label>Khách hàng<span className="pickerSearch"><Search size={15} aria-hidden="true" /><input ref={input} value={q} onChange={e => setQ(e.target.value)} placeholder="Gõ tên, email hoặc mã khách" autoComplete="off" /></span></label>
        <div className="pickerResults" role="group" aria-label="Khách hàng phù hợp" aria-busy={state.loading}>
          {items.map(c => <button type="button" key={c.id} onClick={() => setChosen(c)}><b>{c.display_name}</b><small>{c.email || shortId(c.id)}</small></button>)}
          {state.data && !items.length && <p>Không có khách phù hợp. Thêm khách ở trang Khách hàng trước.</p>}
          {state.data && state.data.total > items.length && <p>Còn {state.data.total - items.length} khách khác · gõ thêm để thu hẹp.</p>}
        </div></>}
  </div>;
}

function CreateDialog({ title, onClose, children }) {
  const dialog = useRef(null);
  useEffect(() => { dialog.current?.showModal(); }, []);
  return <dialog ref={dialog} className="createDialog" aria-labelledby="createDialogTitle" onCancel={event => { event.preventDefault(); onClose(); }} onClick={event => { if (event.target === dialog.current) onClose(); }}>
    <div className="panelTitle"><h2 id="createDialogTitle">{title}</h2><button type="button" aria-label="Đóng" onClick={onClose}><X size={18} /></button></div>{children}</dialog>;
}

function CustomerDetail({ id, request, onExpired, user, onSaved, openInbox, openOrders }) {
  const state = useData(`/workspace/customers/${encodeURIComponent(id)}`, request, onExpired);
  const record = state.data;
  return <><LoadState state={state} />{record && <><p className="recordId" title={record.id}>Mã khách {shortId(record.id)}</p>{user.role === 'admin' ? <RecordForm key={JSON.stringify(record)} kind="customers" record={record} request={request} onExpired={onExpired} onSaved={() => { state.reload(); onSaved(); }} /> : <><h3>{record.display_name}</h3><p>{record.email || 'Chưa có email'}</p></>}
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
    <p>Mở quyền xem đơn này trong một phiên chat, hết hạn sau 15 phút. Chỉ gửi mã qua kênh đã xác minh của chủ đơn, không gửi vào hội thoại đang hỏi.</p>
    <label className="accessConfirmation"><input type="checkbox" checked={confirmed} disabled={busy} onChange={e => setConfirmed(e.target.checked)} />Tôi đã xác minh người nhận. Mã mới thay thế mã cũ.</label>
    <div className="toolbar"><button disabled={busy || !confirmed} onClick={() => change(false)}>Cấp mã mới</button><button disabled={busy} onClick={() => change(true)}>Thu hồi quyền</button></div>
    {access && <><label>Mã chỉ hiển thị lần này<input readOnly value={access.code} autoComplete="off" spellCheck={false} onFocus={e => e.target.select()} /></label><p role="status">Hết hạn: {formatDateTime(new Date(access.expires_at * 1000))}. Khách nhập mã tại mục Quyền tra cứu đơn trong widget.</p><button onClick={() => setAccess(null)}>Ẩn mã</button></>}
    {notice && <p role="status">{notice}</p>}{error && <p className="workspaceError" role="alert">{error}</p>}
  </section>;
}

function Records({ kind, request, onExpired, user, openInbox, openOrders, openCustomer, route, updateNavigation }) {
  const { recordSearch: q, recordStatus: status, recordOffset: offset, recordId: selected, customerFilter: customerId } = route;
  const setSelected = value => updateNavigation({ recordId: value }, false);
  const [adding, setAdding] = useState(false), [notice, setNotice] = useState('');
  const detailPanel = useRef(null);
  useEffect(() => { if (selected) detailPanel.current?.focus(); }, [selected]);
  const customer = kind === 'customers';
  const state = useData(`/workspace/${kind}?${new URLSearchParams({ q, offset, ...(status && { status }), ...(!customer && customerId && { customer_id: customerId }) })}`, request, onExpired);
  const record = state.data?.items.find(item => item.id === selected);
  const saved = () => { setNotice('Đã lưu thay đổi.'); state.reload(); };
  // After creating, clear the filters and open the new record so it is visible straight away.
  const created = result => { setAdding(false); setNotice(customer ? `Đã thêm khách hàng ${result.display_name}.` : `Đã tạo đơn ${result.id}.`); updateNavigation({ recordSearch: '', recordStatus: '', recordOffset: 0, recordId: result.id }, false); state.reload(); };
  const filter = key => event => updateNavigation({ [key]: event.target.value, recordOffset: 0, recordId: null });
  return <section className="management"><header><div><p className="eyebrow">DỮ LIỆU · {customer ? 'KHÁCH HÀNG' : 'ĐƠN HÀNG'}</p><h1>{customer ? 'Khách hàng' : 'Đơn hàng'}</h1><p>{customer ? 'Hồ sơ, lịch sử hội thoại và đơn hàng tại một nơi.' : 'Tra trạng thái đơn hàng và thông tin vận chuyển.'}</p></div><div className="toolbar"><button onClick={state.reload} disabled={state.loading}><RefreshCw size={16} />Làm mới</button>{user.role === 'admin' && <button className="primary" onClick={() => { setAdding(true); setNotice(''); }}><Plus size={16} />{customer ? 'Thêm khách hàng' : 'Tạo đơn hàng'}</button>}</div></header>
    <div className="recordFilters"><label className="search"><Search size={16} /><input aria-label={customer ? 'Tìm khách hàng' : 'Tìm đơn hàng'} maxLength={160} value={q} onChange={filter('recordSearch')} placeholder={customer ? 'Tên, email, mã khách...' : 'Mã đơn, tên khách, vận đơn...'} /></label>{!customer && <div className="recordChips" role="group" aria-label="Trạng thái">{[['', 'Tất cả'], ...Object.entries(orderLabels)].map(([value, label]) => <button type="button" key={value} aria-pressed={(status || '') === value} onClick={() => updateNavigation({ recordStatus: value, recordOffset: 0, recordId: null })}>{label}</button>)}</div>}{customerId && !customer && <button onClick={() => updateNavigation({ customerFilter: '', recordOffset: 0, recordId: null })}>Bỏ lọc khách hàng <X size={16} /></button>}</div>
    {notice && <p role="status" className="workspaceNotice">{notice}</p>}<LoadState state={state} />
    <div className={`recordsLayout ${selected ? 'withDetail' : ''}`}><div className="workspaceCard tableCard">{state.data && <><div className="tableScroll"><table className={`recordTable ${customer ? 'customersTable' : 'ordersTable'}`} role="table"><caption className="visuallyHidden">{customer ? 'Danh sách khách hàng' : 'Danh sách đơn hàng'}</caption><thead role="rowgroup"><tr role="row"><th role="columnheader" scope="col">{customer ? 'Khách hàng' : 'Mã đơn'}</th><th role="columnheader" scope="col">{customer ? 'Email' : 'Khách hàng'}</th><th role="columnheader" scope="col">{customer ? 'Hội thoại' : 'Trạng thái'}</th><th role="columnheader" scope="col">{customer ? 'Đơn hàng' : 'Mã vận đơn'}</th></tr></thead><tbody role="rowgroup">{state.data.items.map(item => <tr role="row" key={item.id} className={selected === item.id ? 'selectedRecord' : ''}><td role="cell" data-label={customer ? 'Khách hàng' : 'Mã đơn'}><button className="recordLink" onClick={() => { setSelected(item.id); setNotice(''); }}>{customer ? item.display_name : item.id}</button>{customer && <small className="recordId" title={item.id}>{shortId(item.id)}</small>}</td><td role="cell" data-label={customer ? 'Email' : 'Khách hàng'}>{customer ? item.email || <span className="recordEmpty"><span aria-hidden="true">–</span><span className="srOnly">Chưa có email</span></span> : item.customer_name}</td><td role="cell" data-label={customer ? 'Hội thoại' : 'Trạng thái'}>{customer ? item.conversation_count : <Badge value={item.status} />}</td><td role="cell" data-label={customer ? 'Đơn hàng' : 'Mã vận đơn'}>{customer ? item.order_count : item.tracking_code || 'Chưa có'}</td></tr>)}</tbody></table></div>{!state.data.items.length && <p className="state">Không có {customer ? 'khách hàng' : 'đơn hàng'} phù hợp.</p>}<Pager total={state.data.total} offset={offset} setOffset={value => updateNavigation({ recordOffset: value, recordId: null }, false)} /></>}</div>
      {selected && <section ref={detailPanel} tabIndex={-1} className="workspaceCard detailCard" aria-label={customer ? 'Hồ sơ khách hàng' : 'Thông tin đơn hàng'}>
        {customer ? <><div className="panelTitle"><h2>Hồ sơ khách hàng</h2><button aria-label="Đóng chi tiết" onClick={() => setSelected(null)}><X size={18} /></button></div><CustomerDetail key={selected} id={selected} request={request} onExpired={onExpired} user={user} onSaved={saved} openInbox={openInbox} openOrders={openOrders} /></>
          : record ? <><div className="panelTitle"><div><p className="panelEyebrow">Đơn hàng</p><h2>{record.id}</h2></div><button aria-label="Đóng chi tiết" onClick={() => setSelected(null)}><X size={18} /></button></div>
            <div className="orderHead"><Badge value={record.status} /><span>{record.tracking_code ? <>Vận đơn <b>{record.tracking_code}</b></> : 'Chưa có mã vận đơn'}</span></div>
            <button type="button" className="orderCustomer" onClick={() => openCustomer?.(record.customer_id)} title={record.customer_id}><span><b>{record.customer_name}</b><small>Mã khách {shortId(record.customer_id)} · mở hồ sơ</small></span><ArrowUpRight size={16} aria-hidden="true" /></button>
            {user.role === 'admin' && <><h3 className="panelSection">Cập nhật đơn</h3><RecordForm key={JSON.stringify(record)} kind={kind} record={record} request={request} onExpired={onExpired} onSaved={saved} /><OrderAccessControls key={record.id} orderId={record.id} request={request} onExpired={onExpired} /></>}</>
          : <><div className="panelTitle"><h2>Thông tin đơn hàng</h2><button aria-label="Đóng chi tiết" onClick={() => setSelected(null)}><X size={18} /></button></div><p>Đang tải hoặc đơn không còn trong bộ lọc.</p></>}
      </section>}
    </div>{adding && <CreateDialog title={customer ? 'Thêm khách hàng' : 'Tạo đơn hàng'} onClose={() => setAdding(false)}>{!customer && <p className="dialogNote">Mã đơn được tạo tự động khi lưu (DH + ngày + 4 ký tự).</p>}<RecordForm key={`new-${kind}`} kind={kind} request={request} onExpired={onExpired} onSaved={created} /></CreateDialog>}<p className="syncNote">{customer ? 'Tên và email không xác minh quyền sở hữu đơn hàng của khách widget.' : 'Dữ liệu đơn hàng nội bộ phục vụ đồ án. Chỉ admin được tạo và cập nhật; chủ đơn không đổi qua màn hình này.'}</p>
  </section>;
}

function PasswordForm({ request, onExpired }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [current, setCurrent] = useState(''), [next, setNext] = useState('');
  // Same checks as POST /workspace/password.
  const rules = [['Từ 12 đến 128 ký tự', value => value.length >= 12 && value.length <= 128], ['Khác mật khẩu hiện tại', value => value.length > 0 && value !== current]];
  async function submit(event) {
    event.preventDefault();
    const { current_password, new_password, confirm } = fieldsOf(event);
    if (new_password !== confirm) { setError('Mật khẩu xác nhận không khớp.'); return; }
    setBusy(true); setError('');
    try { const result = await request('/workspace/password', { method: 'POST', body: JSON.stringify({ current_password, new_password }) }); onExpired(result.message); }
    catch (e) { setError(e.message); if (e.status === 401) onExpired(); }
    finally { setBusy(false); }
  }
  return <form className="recordForm" onSubmit={submit}><fieldset disabled={busy}><label>Mật khẩu hiện tại<input type="password" name="current_password" autoComplete="current-password" required maxLength={128} onChange={event => setCurrent(event.target.value)} /></label><label>Mật khẩu mới<input type="password" name="new_password" autoComplete="new-password" required minLength={12} maxLength={128} onChange={event => setNext(event.target.value)} /></label><PasswordRules value={next} rules={rules} /><label>Nhập lại mật khẩu mới<input type="password" name="confirm" autoComplete="new-password" required minLength={12} maxLength={128} /></label><small>Đổi thành công sẽ đăng xuất mọi phiên của tài khoản này.</small>{error && <p className="workspaceError" role="alert">{error}</p>}<button className="primary">{busy ? 'Đang đổi...' : 'Đổi mật khẩu'}</button></fieldset></form>;
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
  return <article className="workspaceCard"><h2>Tài khoản nhân viên</h2><p>Admin cấp tài khoản riêng cho từng người.</p><form className="recordForm" onSubmit={create}><fieldset disabled={busy}><div className="formGrid"><label>Tên đăng nhập<input name="username" required maxLength={64} pattern="[a-zA-Z0-9_.\-]+" autoComplete="off" /></label><label>Tên hiển thị<input name="display_name" required maxLength={160} /></label><label>Mật khẩu ban đầu<input name="password" type="password" required minLength={12} maxLength={128} autoComplete="new-password" /></label><label>Vai trò<select name="role" defaultValue="agent"><option value="agent">Nhân viên</option><option value="admin">Quản trị viên</option></select></label></div>{error && <p className="workspaceError" role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}<button className="primary">{busy ? 'Đang tạo...' : 'Tạo tài khoản'}</button></fieldset></form><LoadState state={state} />{state.data && <><div className="tableScroll"><table><caption className="visuallyHidden">Tài khoản nhân viên</caption><thead><tr><th>Tài khoản</th><th>Họ tên</th><th>Vai trò</th><th>Trạng thái</th></tr></thead><tbody>{state.data.items.map(u => <tr key={u.id}><td>{u.username}</td><td>{u.display_name}</td><td>{u.role === 'admin' ? 'Quản trị viên' : 'Nhân viên'}</td><td>{u.active ? 'Hoạt động' : 'Đã khóa'}</td></tr>)}</tbody></table></div><Pager total={state.data.total} offset={offset} setOffset={setOffset} /></>}</article>;
}

function SettingsPage({ user, request, onExpired }) {
  const state = useData('/workspace/settings', request, onExpired);
  return <section className="management"><header><div><p className="eyebrow">HỆ THỐNG · CÀI ĐẶT</p><h1>Cài đặt</h1><p>Tài khoản, bảo mật và thông tin vận hành.</p></div></header><LoadState state={state} /><div className="reportGrid"><article className="workspaceCard"><h2>Tài khoản của bạn</h2><div className="summaryLine"><span>Tên hiển thị</span><strong>{user.display_name}</strong></div><div className="summaryLine"><span>Đăng nhập</span><strong>{user.username}</strong></div><div className="summaryLine"><span>Vai trò</span><strong>{user.role === 'admin' ? 'Quản trị viên' : 'Nhân viên'}</strong></div><h3>Đổi mật khẩu</h3><PasswordForm request={request} onExpired={onExpired} /></article><article className="workspaceCard"><h2>Kênh hỗ trợ</h2>{state.data?.channels.map(channel => <div className="summaryLine" key={channel.name}><span>{channel.name}<small className="syncNote">{channel.detail}</small></span><Badge value={channel.status} labels={{ available: 'Sẵn sàng', connected: 'Đã kết nối', connecting: 'Đang kết nối', error: 'Lỗi kết nối', not_connected: 'Chưa kết nối' }} /></div>)}<h3>Chính sách SLA hiện tại</h3><p>Phản hồi đầu tiên, tính 24/7.</p>{Object.entries(state.data?.sla_minutes || {}).map(([key, minutes]) => <div className="summaryLine" key={key}><span>{{ urgent: 'Khẩn cấp', high: 'Cao', normal: 'Bình thường', low: 'Thấp' }[key]}</span><strong>{minutes} phút</strong></div>)}<p className="syncNote">Chính sách cố định cho bản đồ án; chưa hỗ trợ chỉnh lịch làm việc và hạn SLA.</p></article></div>{user.role === 'admin' && <StaffAccounts request={request} onExpired={onExpired} />}</section>;
}

export default function Workspace({ page, ...props }) {
  if (page === 'overview') return <Overview {...props} />;
  if (page === 'analytics') return <Analytics {...props} />;
  if (page === 'settings') return <SettingsPage {...props} />;
  return <Records kind={page} {...props} />;
}
