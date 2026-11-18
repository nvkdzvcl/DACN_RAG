import React, { useState } from 'react';
import useData from './useData';
import LoadState from './LoadState';
import { ArrowRight, FileText, RefreshCw } from 'lucide-react';
import { formatDateTime, formatDay, formatMinutes } from './shared';

function greeting(name) {
  const hour = Number(new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Ho_Chi_Minh', hour: '2-digit', hourCycle: 'h23' }).format(new Date()));
  const part = hour < 5 || hour >= 18 ? 'buổi tối' : hour < 11 ? 'buổi sáng' : hour < 14 ? 'buổi trưa' : 'buổi chiều';
  // The full display name: staff accounts are not always "family name ... given name".
  const shown = (name || '').trim();
  return `Chào ${part}${shown ? `, ${shown}` : ''}`;
}

const percent = (part, total) => total ? Math.round((100 * part) / total) : 0;

export default function Overview({ user, request, onExpired, navigate }) {
  const [days, setDays] = useState(7);
  const summary = useData(`/workspace/summary?days=${days}`, request, onExpired, true);
  const mine = useData('/inbox/conversations?assignment=mine&status=assigned&limit=1', request, onExpired, true);
  const overdue = useData('/inbox/conversations?sla=overdue&limit=1', request, onExpired, true);
  const data = summary.data, period = data?.period;
  const outcomes = period?.ai_outcomes || { answered: 0, not_answered: 0, handoffs: 0 };
  const handled = outcomes.answered + outcomes.not_answered + outcomes.handoffs;
  const maxDaily = Math.max(1, ...(period?.daily || []).map(d => d.count));
  const queue = [
    ['Chờ nhân viên', data?.conversation_statuses?.handoff_requested ?? null, 'Cần tiếp nhận', { status: 'handoff_requested' }, 'warn'],
    ['Quá hạn phản hồi', overdue.data?.total ?? null, 'Đã quá hạn SLA phản hồi đầu', { sla: 'overdue' }, 'bad'],
    ['Bạn đang phụ trách', mine.data?.total ?? null, 'Hội thoại bạn đã tiếp nhận', { assignment: 'mine', status: 'assigned' }, ''],
  ];
  const reloadAll = () => { summary.reload(); mine.reload(); overdue.reload(); };
  const sources = [summary, mine, overdue];
  const updatedAt = sources.every(source => source.updatedAt) ? sources.map(source => source.updatedAt).sort()[0] : null;
  return <section className="overview2">
    <header className="ovTop">
      <div><p className="eyebrow">VẬN HÀNH · TỔNG QUAN</p><h1>{greeting(user?.display_name)}</h1>
        <p className="ovSub dashboardSync" role="status">{sources.some(source => source.error) ? 'Cập nhật thất bại · số liệu có thể đã cũ.' : sources.some(source => source.loading) ? 'Đang cập nhật...' : 'Đã cập nhật.'} {updatedAt ? <>Lần cuối: <time dateTime={updatedAt}>{formatDateTime(updatedAt)}</time> · tự làm mới khi quay lại tab.</> : null}</p></div>
      <div className="ovTools">
        <div className="ovSeg" role="group" aria-label="Khoảng thống kê">{[7, 30, 90].map(n => <button key={n} type="button" aria-pressed={days === n} onClick={() => setDays(n)}>{n} ngày</button>)}</div>
        <button type="button" className="ovRefresh" onClick={reloadAll} disabled={summary.loading} aria-label="Làm mới" title="Làm mới"><RefreshCw size={16} aria-hidden="true" /></button>
      </div>
    </header>

    <LoadState state={summary} /><LoadState state={mine} /><LoadState state={overdue} />
    <div className="ovQueue">{queue.map(([title, count, hint, filters, tone]) =>
      <button key={title} type="button" className={`ovQ ${tone && count ? tone : ''}`} onClick={() => navigate('inbox', filters)}>
        <span className="ovN">{count ?? '–'}</span><span className="ovQText"><b>{title}</b><small>{hint}</small></span><ArrowRight size={18} aria-hidden="true" />
      </button>)}</div>

    {period && <>
      <div className="ovGrid">
        <article className="ovPanel"><h2>Hội thoại mới mỗi ngày</h2><p>Tính theo giờ Việt Nam · {days} ngày</p>
          <div className={`ovBars ${period.daily.length > 14 ? 'dense' : ''}`} role="img" aria-label={`Số hội thoại mới mỗi ngày trong ${days} ngày`}>
            {period.daily.map((d, i) => <div key={d.date} className={`ovBar ${i === period.daily.length - 1 ? 'today' : ''}`} style={{ height: `${Math.max(3, (100 * d.count) / maxDaily)}%` }} title={`${formatDay(d.date)}: ${d.count}`}>{period.daily.length <= 14 && <i>{d.count}</i>}</div>)}
          </div>
          <div className={`ovDays ${period.daily.length > 14 ? 'dense' : ''}`}>{period.daily.map((d, i) => <span key={d.date}>{period.daily.length > 14 && i % 7 ? '' : i === period.daily.length - 1 ? 'Hôm nay' : formatDay(d.date)}</span>)}</div>
        </article>
        <article className="ovPanel"><h2>Chất lượng phục vụ</h2><p>Trong {days} ngày</p>
          <div className="ovKpis"><div><b>{period.sla_met_percent == null ? 'Chưa có' : `${period.sla_met_percent}%`}</b><span>Phản hồi đầu đúng hạn</span></div><div><b>{period.mean_response_minutes == null ? 'Chưa có' : formatMinutes(period.mean_response_minutes)}</b><span>Thời gian phản hồi trung bình</span></div></div>
          {[['AI trả lời có nguồn', outcomes.answered, 'ai'], ['Chuyển nhân viên', outcomes.handoffs, 'assigned'], ['AI chưa trả lời được', outcomes.not_answered, 'closed']].map(([label, value, tone]) =>
            <div className="ovRow" key={label}><span className={`ovTag tone-${tone}`}>{label}</span><span className="ovMeter"><i className={`tone-${tone}`} style={{ width: `${percent(value, handled)}%` }} /></span><b>{handled ? `${percent(value, handled)}%` : '–'}</b></div>)}
          <p className="ovFoot">{handled ? `Trên ${handled} lượt: câu trả lời của AI và hội thoại chuyển nhân viên.` : 'Chưa có lượt nào trong khoảng này.'}</p>
        </article>
      </div>
      <div className="ovGrid">
        <article className="ovPanel"><h2>Câu hỏi AI chưa trả lời được</h2><p>Gợi ý bổ sung Kho tri thức · {days} ngày</p>
          {(period.unanswered_questions || []).length ? <ul className="ovList">{period.unanswered_questions.map(q =>
            <li key={q.question}><span>{q.question}</span><small>{q.count} lần · {formatDateTime(q.last_at)}</small></li>)}</ul> : <p className="ovEmpty">Không có câu hỏi nào bị từ chối trong khoảng này.</p>}
        </article>
        <article className="ovPanel"><h2>Tài liệu được trích nhiều nhất</h2><p>Số câu trả lời có trích tài liệu · {days} ngày</p>
          {(period.top_documents || []).length ? <ul className="ovList docs">{period.top_documents.map(d =>
            <li key={d.document_id}><FileText size={16} aria-hidden="true" /><span title={d.filename}>{d.title || d.filename}</span><b>{d.count}</b></li>)}</ul> : <p className="ovEmpty">Chưa có câu trả lời nào trích tài liệu.</p>}
          <button type="button" className="ovLink" onClick={() => navigate('knowledge')}>Mở Kho tri thức <ArrowRight size={15} aria-hidden="true" /></button>
        </article>
      </div>
    </>}
  </section>;
}
