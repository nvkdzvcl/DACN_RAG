import React, { useEffect, useState } from 'react';
import { ArrowLeft, ArrowRight, Mail, ShieldCheck } from 'lucide-react';
import AuthLayout, { AuthInput } from './AuthLayout';

export function takeEmailLink() {
  const match = /^#(verify|reset)=(.*)$/.exec(window.location.hash);
  if (!match) return null;
  // Keep the secret in memory only; fragments never reach the HTTP server or referrer.
  window.history.replaceState(null, '', window.location.pathname + window.location.search);
  return { mode: match[1], token: match[2] };
}

export function EmailVerification({ account, request, onExpired }) {
  const [configured, setConfigured] = useState(null), [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(''), [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    request('/account/email-status', { signal: controller.signal }).then(data => { if (!controller.signal.aborted) setConfigured(data.configured); })
      .catch(() => { if (!controller.signal.aborted) setConfigured(false); });
    return () => controller.abort();
  }, []);
  async function send() {
    setBusy(true); setError(''); setNotice('');
    try { const data = await request('/account/verification-request', { method: 'POST' }); setNotice(data.message); }
    catch (e) { if (e.status === 401) onExpired(); else setError(e.message); }
    finally { setBusy(false); }
  }
  return <div className="portalEmailCard"><ShieldCheck size={23} aria-hidden="true" /><div><h2>{account.email_verified ? 'Email đã xác minh' : 'Xác minh email để bảo vệ tài khoản'}</h2><p>{account.email_verified ? 'Bạn có thể dùng email này để khôi phục mật khẩu. Quyền tra đơn vẫn cần mã truy cập riêng.' : 'Mở liên kết trong thư và nhập mật khẩu hiện tại. Sau khi xác minh, bạn mới có thể khôi phục mật khẩu qua email.'}</p>
    {!account.email_verified && <><button disabled={busy || !configured} onClick={send}>{busy ? 'Đang gửi yêu cầu...' : 'Gửi email xác minh'}</button>{configured === false && <p>Chức năng gửi email chưa sẵn sàng. Vui lòng liên hệ cửa hàng.</p>}{configured === null && <p role="status">Đang kiểm tra dịch vụ email...</p>}</>}
    {notice && <p role="status">{notice}</p>}{error && <p role="alert" className="widgetError">{error}</p>}</div></div>;
}

export default function CustomerEmail({ action, request, onBack, onComplete }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('');
  const [configured, setConfigured] = useState(null);
  const mode = action.mode;
  useEffect(() => {
    if (mode !== 'forgot') return;
    const controller = new AbortController();
    request('/account/email-status', { signal: controller.signal }).then(data => { if (!controller.signal.aborted) setConfigured(data.configured); })
      .catch(() => { if (!controller.signal.aborted) setConfigured(false); });
    return () => controller.abort();
  }, [mode]);
  async function submit(event) {
    event.preventDefault(); const fields = new FormData(event.currentTarget); setError(''); setNotice('');
    if (mode === 'reset' && fields.get('new_password') !== fields.get('confirm')) { setError('Mật khẩu nhập lại chưa khớp.'); return; }
    setBusy(true);
    const endpoint = mode === 'forgot' ? 'forgot-password' : mode === 'verify' ? 'verify-email' : 'reset-password';
    const payload = mode === 'forgot' ? { email: fields.get('email').trim() } : mode === 'verify' ? { token: action.token, password: fields.get('password') } : { token: action.token, new_password: fields.get('new_password') };
    try {
      const data = await request('/account/' + endpoint, { method: 'POST', body: JSON.stringify(payload) });
      if (mode === 'forgot') setNotice(data.message); else onComplete(mode, data.message);
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  return <AuthLayout><h1>{mode === 'forgot' ? 'Quên mật khẩu?' : mode === 'verify' ? 'Xác minh email của bạn' : 'Đặt lại mật khẩu'}</h1><p className="authLead">{mode === 'forgot' ? 'Nhập email đã xác minh để nhận liên kết đặt lại mật khẩu.' : mode === 'verify' ? 'Nhập mật khẩu của tài khoản đã yêu cầu xác minh để xác nhận quyền sở hữu email.' : 'Chọn mật khẩu mới. Mọi phiên đăng nhập cũ sẽ hết hiệu lực sau khi đổi.'}</p>
    <form onSubmit={submit} aria-busy={busy}><fieldset disabled={busy}>
      {mode === 'forgot' ? <AuthInput label="Email" name="email" type="email" required maxLength={254} autoComplete="email" placeholder="Email đã xác minh của bạn" /> : mode === 'verify' ? <AuthInput label="Mật khẩu hiện tại" name="password" type="password" required maxLength={128} autoComplete="current-password" /> : <><AuthInput label="Mật khẩu mới" name="new_password" type="password" required minLength={15} maxLength={128} autoComplete="new-password" placeholder="Từ 15 đến 128 ký tự" /><AuthInput label="Nhập lại mật khẩu mới" name="confirm" type="password" required minLength={15} maxLength={128} autoComplete="new-password" /></>}
      <button className="authSubmit" disabled={busy || mode === 'forgot' && !configured}><ArrowRight size={18} />{busy ? 'Đang xử lý...' : mode === 'forgot' ? 'Gửi liên kết khôi phục' : mode === 'verify' ? 'Xác minh email' : 'Lưu mật khẩu mới'}</button>
    </fieldset></form>
    {mode === 'forgot' && configured === false && <p className="authFeedback" role="status">Chức năng gửi email chưa sẵn sàng. Vui lòng liên hệ cửa hàng hoặc thử lại sau.</p>}
    {error && <p className="authFeedback" role="alert">{error}</p>}{notice && <p className="authFeedback" role="status">{notice}</p>}
    <button className="authBack" type="button" onClick={onBack} disabled={busy}><ArrowLeft size={15} />Quay lại</button>
    <div className="authNote"><Mail size={22} /><div>{mode === 'forgot' ? 'Kiểm tra cả thư rác' : 'Liên kết chỉ dùng một lần'}<small>{mode === 'forgot' ? 'Email chưa xác minh không nhận được thư khôi phục. Nếu còn nhớ mật khẩu, đăng nhập và xác minh trong mục Tài khoản.' : mode === 'verify' ? 'Liên kết có hạn 60 phút. Không yêu cầu xác minh hoặc không biết mật khẩu? Hãy đóng trang này.' : 'Liên kết có hạn 15 phút. Nếu hết hạn, quay lại Đăng nhập và chọn Quên mật khẩu để yêu cầu thư mới.'}</small></div></div>
  </AuthLayout>;
}
