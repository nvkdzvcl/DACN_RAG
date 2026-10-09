import React, { useId, useState } from 'react';
import { Bot, Headphones, Sparkles, MessagesSquare, HeartHandshake, ChartNoAxesCombined, Globe, Send, BookOpen, Check, ShieldCheck, Eye, EyeOff, LockKeyhole, Mail, UserRound } from 'lucide-react';
import './auth.css';
import { ThemeToggle } from './Theme';

const features = [[Sparkles, 'Trả lời thông minh với RAG', 'Đọc hiểu tài liệu, trả lời kèm trích dẫn nguồn.'], [MessagesSquare, 'Kết nối nhiều kênh', 'Website và Telegram, cùng một nơi hỗ trợ.'], [HeartHandshake, 'AI đồng hành cùng nhân viên', 'Chuyển tiếp cho người hỗ trợ khi bạn cần.'], [ChartNoAxesCombined, 'Chăm sóc khách hàng hiệu quả', 'Theo dõi hội thoại, tra cứu đơn và phản hồi kịp thời.']];

export function AuthInput({ label, type = 'text', ...props }) {
  const id = useId(); const [visible, setVisible] = useState(false);
  const Icon = type === 'password' ? LockKeyhole : type === 'email' ? Mail : UserRound;
  return <div className="authField"><label htmlFor={id}>{label}</label><div className="authInput"><Icon size={18} aria-hidden="true" /><input {...props} id={id} type={type === 'password' && visible ? 'text' : type} />{type === 'password' && <button className="authReveal" type="button" aria-label={(visible ? 'Ẩn ' : 'Hiện ') + label.toLowerCase()} aria-pressed={visible} onClick={() => setVisible(v => !v)}>{visible ? <Eye size={18} /> : <EyeOff size={18} />}</button>}</div></div>;
}

export default function AuthLayout({ children, staff = false }) {
  return <main className="authPage">
    <section className="authStory" aria-label="Giới thiệu RAG Support">
      <a className="authBrand" href="/chat"><span><Headphones size={30} /></span><div><b>RAG Support</b><small>Hỗ trợ thông minh. Kết nối tận tâm.</small></div></a>
      <div className="authStoryBody"><div className="authPitch"><span className="authEyebrow">Nền tảng trợ lý AI hỗ trợ khách hàng</span><h2>Ứng dụng AI & RAG<br />để mang đến trải nghiệm<br /><em>chăm sóc khách hàng vượt trội</em></h2><p>Tìm câu trả lời, tra cứu thông tin và kết nối với nhân viên khi cần. Tất cả trong một trải nghiệm hỗ trợ liền mạch.</p></div>
        <div className="authFeatures">{features.map(([Icon, title, detail], i) => <div key={title}><span className={'authFeatureIcon tone' + i}><Icon size={22} /></span><div><h3>{title}</h3><p>{detail}</p></div></div>)}</div>
        <div className="authScene" aria-hidden="true"><div className="authOrbit" /><span className="authChannel web"><Globe size={22} />Website Chat</span><span className="authChannel telegram"><Send size={20} />Telegram</span><div className="authBubble question">Mình cần hỗ trợ về chính sách đổi trả.</div><div className="authBubble answer">Mình sẽ tìm thông tin trong tài liệu của cửa hàng nhé!</div><div className="authRobot"><div className="robotAntenna" /><div className="robotHead"><i className="robotEar left" /><i className="robotEar right" /><div className="robotFace"><i /><i /><span /></div><div className="robotMic" /></div><div className="robotBody" /><div className="robotLaptop"><Bot size={34} /></div><div className="robotBase" /></div><div className="authSource"><span><Check size={15} /></span><div>Thông tin có nguồn<small>Từ kho tri thức của cửa hàng</small></div><BookOpen size={23} /></div><div className="authChecklist">{['Tra cứu tài liệu', 'Trích dẫn nguồn', 'Kết nối nhân viên'].map(text => <span key={text}><Check size={13} />{text}</span>)}</div></div>
      </div>
      <div className="authHighlights"><div><Sparkles size={19} /><b>RAG</b><span>Trả lời từ tài liệu</span></div><div><MessagesSquare size={19} /><b>Đa kênh</b><span>Kết nối hội thoại</span></div><div><BookOpen size={19} /><b>Lịch sử</b><span>Lưu theo tài khoản</span></div><div><HeartHandshake size={19} /><b>AI + Người</b><span>Phối hợp hỗ trợ</span></div></div>
    </section>
    <section className="authPanel" aria-label={staff ? 'Đăng nhập nhân viên' : 'Tài khoản khách hàng'}><div className="authTop"><span><ShieldCheck size={15} />{staff ? 'Không gian nhân viên' : 'Không gian khách hàng'}</span><ThemeToggle /></div><div className="authContent"><div className="authBrand authFormBrand"><span><Headphones size={37} /></span><div><b>RAG Support</b><small>{staff ? 'Nền tảng chăm sóc khách hàng' : 'Luôn sẵn sàng lắng nghe bạn'}</small></div></div>{children}</div><footer className="authFooter"><span>© {new Date().getFullYear()} RAG Support</span><a href={staff ? '/chat' : '/'}>{staff ? 'Dành cho khách hàng' : 'Dành cho nhân viên'} <span aria-hidden="true">↗</span></a></footer></section>
  </main>;
}
