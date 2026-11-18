import React, { useState } from 'react';
import useData from './useData';
import LoadState from './LoadState';
import { RefreshCw } from 'lucide-react';
import { channelNames, formatDate, formatDateTime, formatMinutes } from './shared';

// Figures the Overview does not show: totals for the period, the first-response SLA breakdown,
// channels and current orders. Built from the same components as the Overview (redesign-staff.css).
const slaRows = [['met', 'Phản hồi đúng hạn', ''], ['breached', 'Phản hồi trễ', 'bad'], ['on_track', 'Đang chờ, trong hạn', ''], ['overdue', 'Đang chờ, quá hạn', 'bad'], ['cancelled', 'Kết thúc trước phản hồi', '']];
const orderLabels = { processing: 'Đang xử lý', paid: 'Đã thanh toán', shipping: 'Đang giao', shipped: 'Đã gửi hàng', delivered: 'Đã giao', cancelled: 'Đã hủy' };
const number = value => new Intl.NumberFormat('vi-VN').format(value || 0);

export default function Analytics({ request, onExpired }) {
  const [days, setDays] = useState(7);
  const state = useData(`/workspace/summary?days=${days}`, request, onExpired, true);
  const data = state.data, period = data?.period;
  const channels = Object.entries(period?.channels || {});
  const maxChannel = Math.max(1, ...channels.map(([, count]) => count));
  return <section className="overview2 analytics2">
    <header className="ovTop">
      <div><p className="eyebrow">PHÂN TÍCH</p><h1>Phân tích hỗ trợ</h1>
        <p className="ovSub dashboardSync" role="status">{state.error ? 'Cập nhật thất bại · số liệu có thể đã cũ.' : state.loading ? 'Đang cập nhật...' : 'Đã cập nhật.'} {state.updatedAt ? <>Lần cuối: <time dateTime={state.updatedAt}>{formatDateTime(state.updatedAt)}</time> · tự làm mới khi quay lại tab.</> : null}</p></div>
      <div className="ovTools">
        <div className="ovSeg" role="group" aria-label="Khoảng thống kê">{[7, 30, 90].map(n => <button key={n} type="button" aria-pressed={days === n} onClick={() => setDays(n)}>{n} ngày</button>)}</div>
        <button type="button" className="ovRefresh" onClick={state.reload} disabled={state.loading} aria-label="Làm mới" title="Làm mới"><RefreshCw size={16} aria-hidden="true" /></button>
      </div>
    </header>
    <LoadState state={state} />
    {period && <>
      <dl className="ovStats">{[['Hội thoại mới', period.conversations], ['Tin nhắn', period.messages], ['Ticket chuyển nhân viên', period.tickets], ['Ticket đã phản hồi', period.responded_tickets]].map(([label, value]) =>
        <div key={label}><dt>{label}</dt><dd>{number(value)}</dd></div>)}</dl>
      <div className="ovGrid">
        <article className="ovPanel"><h2>Phản hồi đầu của nhân viên</h2><p>Ticket tạo trong {days} ngày · hạn SLA tính 24/7</p>
          <div className="ovKpis"><div><b>{period.sla_met_percent == null ? 'Chưa có' : `${period.sla_met_percent}%`}</b><span>Đúng hạn trên số ticket đã phản hồi</span></div><div><b>{period.mean_response_minutes == null ? 'Chưa có' : formatMinutes(period.mean_response_minutes)}</b><span>Thời gian phản hồi trung bình</span></div></div>
          {slaRows.map(([key, label, tone]) => <div className={`ovRow ovLine ${tone && period.sla[key] ? tone : ''}`} key={key}><span>{label}</span><b>{number(period.sla[key])}</b></div>)}
        </article>
        <div className="ovStack">
          <article className="ovPanel"><h2>Kênh tiếp nhận</h2><p>Hội thoại mới theo kênh · {days} ngày</p>
            {channels.length ? channels.map(([name, count]) => <div className="ovRow ovLine" key={name}><span>{channelNames[name] || name}</span><span className="ovMeter"><i style={{ width: `${(100 * count) / maxChannel}%` }} /></span><b>{number(count)}</b></div>) : <p className="ovEmpty">Chưa có hội thoại trong khoảng này.</p>}
          </article>
          <article className="ovPanel"><h2>Đơn hàng hiện tại</h2><p>Theo trạng thái, không phụ thuộc khoảng thống kê</p>
            {Object.keys(data.order_statuses).length ? <div className="ovPills">{Object.entries(data.order_statuses).map(([status, count]) => <span key={status}><span className={`statusPill order-${status}`}>{orderLabels[status] || status}</span><b>{number(count)}</b></span>)}</div> : <p className="ovEmpty">Chưa có đơn hàng.</p>}
          </article>
        </div>
      </div>
      <p className="ovFoot">Khoảng thống kê: {formatDate(data.start)} đến {formatDate(data.end)} (giờ Việt Nam). Biểu đồ hội thoại theo ngày và tỷ lệ trả lời của AI nằm ở trang Tổng quan.</p>
    </>}
  </section>;
}
