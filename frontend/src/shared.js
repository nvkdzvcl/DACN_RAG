// One glossary and one date/time format for the customer portal and the staff workspace.

export const conversationStatuses = {
  open: 'AI đang hỗ trợ',
  handoff_requested: 'Chờ nhân viên',
  assigned: 'Nhân viên đang hỗ trợ',
  resolved: 'Đã giải quyết',
  closed: 'Đã đóng',
};

// A ticket is the staff's work item, so its states are named from the staff's side.
export const ticketStatuses = { open: 'Chờ tiếp nhận', assigned: 'Đang xử lý', resolved: 'Đã giải quyết', closed: 'Đã đóng' };

export const channelNames = { website: 'Website', telegram: 'Telegram' };

// The shop runs on Vietnam time; reports from the API use the same zone.
const TIME_ZONE = 'Asia/Ho_Chi_Minh';
const partsFormat = new Intl.DateTimeFormat('en-GB', { timeZone: TIME_ZONE, day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });

function parse(value) {
  if (!value) return null;
  // API timestamps without an offset are UTC.
  const date = value instanceof Date ? value : new Date(typeof value === 'string' && !/[zZ]$|[+-]\d{2}:\d{2}$/.test(value) ? `${value}Z` : value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function parts(value) {
  const date = parse(value);
  return date && Object.fromEntries(partsFormat.formatToParts(date).map(part => [part.type, part.value]));
}

/** dd/mm/yyyy HH:mm */
export function formatDateTime(value) {
  const p = parts(value);
  return p ? `${p.day}/${p.month}/${p.year} ${p.hour}:${p.minute}` : '';
}

/** dd/mm/yyyy */
export function formatDate(value) {
  const p = parts(value);
  return p ? `${p.day}/${p.month}/${p.year}` : '';
}

/** HH:mm for today, dd/mm for earlier days (compact lists). */
export function formatShort(value) {
  const p = parts(value), today = parts(new Date());
  if (!p) return '';
  return p.day === today.day && p.month === today.month && p.year === today.year ? `${p.hour}:${p.minute}` : `${p.day}/${p.month}`;
}

/** 'YYYY-MM-DD' (a calendar day from the API) as dd/mm. */
export function formatDay(isoDay) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDay || '');
  return match ? `${match[3]}/${match[2]}` : isoDay;
}

/** A duration given in minutes, in the largest sensible unit. */
export function formatMinutes(minutes) {
  if (minutes == null) return '';
  if (minutes < 1) return `${Math.round(minutes * 60)} giây`;
  if (minutes < 60) return `${minutes.toLocaleString('vi-VN', { maximumFractionDigits: 1 })} phút`;
  const hours = Math.floor(minutes / 60), rest = Math.round(minutes % 60);
  return rest ? `${hours} giờ ${rest} phút` : `${hours} giờ`;
}

/** Generated IDs are long UUIDs; lists show the first 8 characters and keep the full value in a tooltip. */
export function shortId(id) {
  return typeof id === 'string' && id.length > 16 ? id.slice(0, 8) : id;
}

/** Ticket summaries written before the labels were localized start lines with sender_type. */
export function localizeSummary(text) {
  return String(text ?? '').replace(/^(customer|ai|agent|system): /gm, (_, sender) => ({ customer: 'Khách: ', ai: 'AI: ', agent: 'Nhân viên: ', system: 'Hệ thống: ' })[sender]);
}

// One citation label everywhere (customer chat, history, staff inbox, knowledge base): "thanh-toan · dòng 13".
export function citationLabel(citation) {
  const where = citation.location ? citation.location.toLowerCase() : citation.page ? `trang ${citation.page}` : '';
  return [(citation.source || '').replace(/\.(md|txt|markdown|pdf|docx)$/i, ''), where].filter(Boolean).join(' · ');
}
