import React, { useEffect, useId, useRef, useState } from 'react';
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

const RESEND_SECONDS = 60;

function CodeInput({ disabled }) {
  const [digits, setDigits] = useState(Array(6).fill(''));
  const boxes = useRef([]);
  const labelId = useId();
  function put(index, text, previous) {
    let clean = text.replace(/\D/g, '');
    // Typing over a filled box replaces its digit; a longer value is a paste or one-time-code autofill.
    if (previous && clean.length === 2) clean = clean.replace(previous, '') || clean.slice(-1);
    if (!clean) { setDigits(current => current.map((digit, i) => i === index ? '' : digit)); return; }
    setDigits(current => { const next = [...current]; [...clean.slice(0, 6 - index)].forEach((digit, k) => { next[index + k] = digit; }); return next; });
    boxes.current[Math.min(index + clean.length, 5)]?.focus();
  }
  return <div className="authField"><label id={labelId}>Mã xác minh 6 số</label>
    <div className="codeBoxes" role="group" aria-labelledby={labelId}>{digits.map((digit, index) => <input key={index} ref={element => { boxes.current[index] = element; }}
      value={digit} inputMode="numeric" autoComplete={index ? 'off' : 'one-time-code'} maxLength={6} aria-label={`Chữ số thứ ${index + 1}`} disabled={disabled}
      onChange={event => put(index, event.target.value, digit)} onFocus={event => event.target.select()}
      onKeyDown={event => { if (event.key === 'Backspace' && !digit && index) boxes.current[index - 1]?.focus(); }}
      onPaste={event => { event.preventDefault(); put(index, event.clipboardData.getData('text')); }} />)}</div>
    <input type="hidden" name="code" value={digits.join('')} /></div>;
}

export default function CustomerEmail({ action, request, onBack, onComplete, onLogout }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('');
  // A code was just sent when the screen opens after register/login; resending waits out the countdown.
  const [cooldown, setCooldown] = useState(action.sent ? RESEND_SECONDS : 0);
  useEffect(() => { if (cooldown <= 0) return; const timer = setTimeout(() => setCooldown(n => n - 1), 1000); return () => clearTimeout(timer); }, [cooldown]);
  const [resendBusy, setResendBusy] = useState(false);
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
    if (mode === 'register-code' && !/^[0-9]{6}$/.test(fields.get('code'))) { setError('Vui lòng nhập đủ 6 chữ số của mã xác minh.'); return; }
    setBusy(true);
    const endpoint = mode === 'forgot' ? 'forgot-password' : mode === 'verify' ? 'verify-email' : mode === 'register-code' ? 'verify-registration' : 'reset-password';
    const payload = mode === 'forgot' ? { email: fields.get('email').trim() } : mode === 'verify' ? { token: action.token, password: fields.get('password') } : mode === 'register-code' ? { code: fields.get('code') } : { token: action.token, new_password: fields.get('new_password') };
    try {
      const data = await request('/account/' + endpoint, { method: 'POST', body: JSON.stringify(payload) });
      if (mode === 'forgot') setNotice(data.message); else onComplete(mode, data.message);
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  async function resendRegistrationCode() {
    setResendBusy(true); setError(''); setNotice('');
    try { const data = await request('/account/registration-verification-request', { method: 'POST' }); setNotice(data.message); setCooldown(RESEND_SECONDS); }
    catch (e) { setError(e.message); }
    finally { setResendBusy(false); }
  }
  return <AuthLayout><h1>{mode === 'forgot' ? 'Quên mật khẩu?' : mode === 'verify' ? 'Xác minh email của bạn' : mode === 'register-code' ? 'Xác minh email đăng ký' : 'Đặt lại mật khẩu'}</h1><p className="authLead">{mode === 'forgot' ? 'Nhập email đã xác minh để nhận liên kết đặt lại mật khẩu.' : mode === 'verify' ? 'Nhập mật khẩu của tài khoản đã yêu cầu xác minh để xác nhận quyền sở hữu email.' : mode === 'register-code' ? 'Nhập mã 6 số đã gửi tới email đăng ký. Bạn chỉ trò chuyện được sau khi xác minh.' : 'Chọn mật khẩu mới. Mọi phiên đăng nhập cũ sẽ hết hiệu lực sau khi đổi.'}</p>
    <form onSubmit={submit} aria-busy={busy}><fieldset disabled={busy}>
      {mode === 'register-code' ? <CodeInput disabled={busy} /> : mode === 'forgot' ? <AuthInput label="Email" name="email" type="email" required maxLength={254} autoComplete="email" placeholder="Email đã xác minh của bạn" /> : mode === 'verify' ? <AuthInput label="Mật khẩu hiện tại" name="password" type="password" required maxLength={128} autoComplete="current-password" /> : <><AuthInput label="Mật khẩu mới" name="new_password" type="password" required minLength={8} maxLength={128} pattern="(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9\s]).{8,128}" autoComplete="new-password" placeholder="Tối thiểu 8 ký tự, gồm chữ hoa, chữ thường, số và ký tự đặc biệt" /><AuthInput label="Nhập lại mật khẩu mới" name="confirm" type="password" required minLength={8} maxLength={128} pattern="(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9\s]).{8,128}" autoComplete="new-password" /></>}
      <button className="authSubmit" disabled={busy || mode === 'forgot' && !configured}><ArrowRight size={18} />{busy ? 'Đang xử lý...' : mode === 'forgot' ? 'Gửi liên kết khôi phục' : mode === 'verify' ? 'Xác minh email' : mode === 'register-code' ? 'Xác minh email' : 'Lưu mật khẩu mới'}</button>
    </fieldset></form>
    {mode === 'register-code' && <><p className="authFeedback" role="status">Mã xác minh có hạn 15 phút và chỉ dùng một lần.</p><button className="authBack" type="button" onClick={resendRegistrationCode} disabled={busy || resendBusy || cooldown > 0}>{resendBusy ? 'Đang gửi lại...' : cooldown > 0 ? `Gửi lại mã sau ${cooldown} giây` : 'Gửi lại mã xác minh'}</button></>}
    {mode === 'forgot' && configured === false && <p className="authFeedback" role="status">Chức năng gửi email chưa sẵn sàng. Vui lòng liên hệ cửa hàng hoặc thử lại sau.</p>}
    {error && <p className="authFeedback" role="alert">{error}</p>}{notice && <p className="authFeedback" role="status">{notice}</p>}
    {mode !== 'register-code' ? <button className="authBack" type="button" onClick={onBack} disabled={busy}><ArrowLeft size={15} />Quay lại</button> : <><p className="authFeedback" role="status">Bạn cần nhập đúng mã xác minh để hoàn tất đăng ký tài khoản.</p>{onLogout && <button className="authBack" type="button" onClick={onLogout} disabled={busy}><ArrowLeft size={15} />Dùng tài khoản khác</button>}</>}
    <div className="authNote"><Mail size={22} /><div>{mode === 'forgot' ? 'Kiểm tra cả thư rác' : 'Liên kết chỉ dùng một lần'}<small>{mode === 'forgot' ? 'Email chưa xác minh không nhận được thư khôi phục. Nếu còn nhớ mật khẩu, đăng nhập và xác minh trong mục Tài khoản.' : mode === 'verify' ? 'Liên kết có hạn 60 phút. Không yêu cầu xác minh hoặc không biết mật khẩu? Hãy đóng trang này.' : 'Liên kết có hạn 15 phút. Nếu hết hạn, quay lại Đăng nhập và chọn Quên mật khẩu để yêu cầu thư mới.'}</small></div></div>
  </AuthLayout>;
}
