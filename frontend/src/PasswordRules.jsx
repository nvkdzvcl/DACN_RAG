import React from 'react';

// Same rules as the backend (app/api/customer_auth.py new_password_text) and the form pattern.
export const CUSTOMER_RULES = [
  ['Từ 8 đến 128 ký tự', value => value.length >= 8 && value.length <= 128],
  ['Có chữ thường', value => /[a-z]/.test(value)],
  ['Có chữ hoa', value => /[A-Z]/.test(value)],
  ['Có chữ số', value => /[0-9]/.test(value)],
  ['Có ký tự đặc biệt', value => /[^A-Za-z0-9\s]/.test(value)],
];

export default function PasswordRules({ value = '', rules = CUSTOMER_RULES }) {
  return <ul className="passwordRules" aria-label="Điều kiện mật khẩu">{rules.map(([label, test]) => {
    const met = test(value);
    return <li key={label} className={met ? 'met' : ''}><span aria-hidden="true">{met ? '✓' : '○'}</span>{label}<span className="srOnly">{met ? ' – đã đạt' : ' – chưa đạt'}</span></li>;
  })}</ul>;
}
