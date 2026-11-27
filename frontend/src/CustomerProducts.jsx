import React, { useEffect, useState } from 'react';
import { ExternalLink, MessageSquare } from 'lucide-react';

const vnd = price => price == null ? 'Liên hệ' : `${price.toLocaleString('vi-VN')}₫`;

// Same catalogue as the Telegram /products command; staff manage it on the Sản phẩm page.
export default function CustomerProducts({ request, onAsk }) {
  const [data, setData] = useState(null), [error, setError] = useState(''), [category, setCategory] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    request('/products', { signal: controller.signal })
      .then(result => { if (!controller.signal.aborted) setData(result); })
      .catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, []);
  const items = data ? data.products.filter(product => !category || product.category === category) : [];
  return <section className="portalPage productsPage" aria-label="Sản phẩm">
    <div className="portalPageHead"><div><h1>Sản phẩm</h1><p>Giá tham khảo, có thể thay đổi. Hỏi trợ lý về bảo hành, trả góp hoặc gặp nhân viên để được tư vấn.</p></div></div>
    {error && <p className="widgetError" role="alert">{error}</p>}
    {!data && !error && <p className="historyState" role="status">Đang tải sản phẩm...</p>}
    {data && !data.products.length && <div className="portalEmpty"><p>Cửa hàng chưa đăng sản phẩm nào.</p></div>}
    {data && data.products.length > 0 && <>
      <div className="historyChips productChips" role="group" aria-label="Nhóm sản phẩm">
        {[{ id: '', label: 'Tất cả', count: data.products.length }, ...data.categories].map(group =>
          <button type="button" key={group.id} aria-pressed={category === group.id} onClick={() => setCategory(group.id)}>{group.label} ({group.count})</button>)}
      </div>
      <div className="productGrid">{items.map(product => <article key={product.id} className="productCard">
        <h2>{product.name}</h2>
        <p className="productPrice">{vnd(product.price)}</p>
        <span className={`statusPill ${product.stock > 0 ? 'order-delivered' : 'order-cancelled'}`}>{product.stock > 0 ? `Còn ${product.stock}` : 'Hết hàng'}</span>
        {product.description && <p className="productDescription">{product.description}</p>}
        <div className="productActions">
          <button type="button" onClick={() => onAsk(`Mua ${product.name} thì được bảo hành và trả góp thế nào?`)}><MessageSquare size={15} aria-hidden="true" />Hỏi trợ lý</button>
          {product.url && <a href={product.url} target="_blank" rel="noopener noreferrer"><ExternalLink size={15} aria-hidden="true" />Xem trên website</a>}
        </div>
      </article>)}</div>
    </>}
  </section>;
}
