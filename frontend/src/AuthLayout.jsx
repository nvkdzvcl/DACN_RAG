import React, { useId, useState } from 'react';
import { Headphones, Eye, EyeOff, LockKeyhole, Mail, UserRound } from 'lucide-react';
import './auth.css';
import { ThemeToggle } from './Theme';

// Redesign step 5: one message and a real sourced answer instead of the robot illustration.
const story = {
  customer: { title: 'Hỏi về chính sách, nhận câu trả lời có nguồn.', lead: 'Trợ lý AI trích nguyên văn chính sách của cửa hàng. Khi cần, nhân viên sẽ tiếp nhận ngay trong cuộc trò chuyện.',
    facts: [['Có nguồn', 'Mỗi câu trả lời dẫn về chính sách'], ['Website và Telegram', 'Một nơi hỗ trợ, hai kênh'], ['Nhân viên thật', 'Chuyển khi bạn cần']] },
  staff: { title: 'Trả lời khách nhanh, đúng chính sách.', lead: 'AI trả lời các câu hỏi có trong Kho tri thức; hội thoại cần người xử lý được chuyển vào hộp thư của bạn kèm tóm tắt.',
    facts: [['Hộp thư chung', 'Website và Telegram'], ['Hạn phản hồi', 'Cảnh báo khi sắp quá hạn'], ['Kho tri thức', 'Biết tài liệu nào được trích']] },
};

export function AuthInput({ label, type = 'text', ...props }) {
  const id = useId(); const [visible, setVisible] = useState(false);
  const Icon = type === 'password' ? LockKeyhole : type === 'email' ? Mail : UserRound;
  return <div className="authField"><label htmlFor={id}>{label}</label><div className="authInput"><Icon size={18} aria-hidden="true" /><input {...props} id={id} type={type === 'password' && visible ? 'text' : type} />{type === 'password' && <button className="authReveal" type="button" aria-label={(visible ? 'Ẩn ' : 'Hiện ') + label.toLowerCase()} aria-pressed={visible} onClick={() => setVisible(v => !v)}>{visible ? <Eye size={18} /> : <EyeOff size={18} />}</button>}</div></div>;
}

export default function AuthLayout({ children, staff = false }) {
  const text = story[staff ? 'staff' : 'customer'];
  return <main className="authPage">
    <section className="authStory" aria-label="Giới thiệu RAG Support">
      <a className="authBrand" href={staff ? '/' : '/chat'}><span><Headphones size={20} /></span><div><b>RAG Support</b><small>{staff ? 'Không gian làm việc của nhân viên' : 'Hỗ trợ khách hàng'}</small></div></a>
      <div className="authStoryBody">
        <h2>{text.title}</h2><p>{text.lead}</p>
        <figure className="authSample" aria-label="Ví dụ câu trả lời có nguồn">
          <p className="authSampleQ">Hoàn tiền về thẻ mất mấy ngày?</p>
          <blockquote><b>Hoàn tiền – về nguồn thanh toán ban đầu:</b> tiền được hoàn trong 5 đến 7 ngày, không tính thứ Bảy, Chủ nhật và ngày lễ, Tết.</blockquote>
          <figcaption>Nguồn · Thanh toán, dòng 13</figcaption>
        </figure>
        <dl className="authFacts">{text.facts.map(([title, detail]) => <div key={title}><dt>{title}</dt><dd>{detail}</dd></div>)}</dl>
      </div>
    </section>
    <section className="authPanel" aria-label={staff ? 'Đăng nhập nhân viên' : 'Tài khoản khách hàng'}><div className="authTop"><span>{staff ? 'Không gian nhân viên' : 'Không gian khách hàng'}</span><ThemeToggle /></div><div className="authContent"><div className="authBrand authFormBrand"><span><Headphones size={22} /></span><div><b>RAG Support</b><small>{staff ? 'Nền tảng chăm sóc khách hàng' : 'Hỗ trợ khách hàng'}</small></div></div>{children}</div><footer className="authFooter"><span>© {new Date().getFullYear()} RAG Support</span><a href={staff ? '/chat' : '/'}>{staff ? 'Dành cho khách hàng' : 'Bạn là nhân viên? Vào không gian làm việc'} <span aria-hidden="true">↗</span></a></footer></section>
  </main>;
}
