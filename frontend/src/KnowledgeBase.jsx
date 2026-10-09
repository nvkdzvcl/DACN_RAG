import React, { useEffect, useRef, useState } from 'react';

const labels = { indexed: 'Đã lập chỉ mục', processing: 'Đang xử lý', failed: 'Xử lý lỗi', ready_for_embedding: 'Cần lập chỉ mục lại', deleting: 'Xóa chưa hoàn tất', uploaded: 'Đã tải lên' };

export function Citations({ citations, request }) {
  const [source, setSource] = useState(null);
  async function open(citation) {
    const id = `${citation.document_id}:${citation.chunk_id}:${citation.index_version || ''}`;
    setSource({ id, loading: true });
    try {
      const data = await request(`/documents/${encodeURIComponent(citation.document_id)}/chunks/${encodeURIComponent(citation.chunk_id)}?index_version=${encodeURIComponent(citation.index_version || '')}`);
      setSource(current => current?.id === id ? { ...data, id } : current);
    } catch (error) {
      setSource(current => current?.id === id ? { id, error: error.message } : current);
    }
  }
  return <div className="citations">{citations.map((citation, index) => {
    const id = `${citation.document_id}:${citation.chunk_id}:${citation.index_version || ''}`;
    const current = source?.id === id ? source : null;
    const content = current?.content?.replace(/\s+/g, ' ').trim() || '';
    const quote = citation.quote?.replace(/\s+/g, ' ').trim();
    const start = quote ? content.indexOf(quote) : -1;
    return <details key={`${id}-${index}`}>
      <summary>Nguồn {index + 1} · {citation.source}{citation.location ? ` · ${citation.location}` : citation.page ? ` · Trang ${citation.page}` : ''}</summary>
      {citation.quote && <><p className="sourceLabel">Trích dẫn trong câu trả lời</p><blockquote>{citation.quote}</blockquote></>}
      {citation.document_id && <button type="button" disabled={current?.loading} onClick={() => open(citation)}>{current?.loading ? 'Đang tải nguồn...' : current?.error ? 'Thử tải lại nguồn' : 'Xem đoạn nguồn'}</button>}
      {current?.error && <p role="alert">{current.error}</p>}
      {content && <div className="sourceContext"><p className="sourceLabel">Toàn đoạn nguồn · phần khớp trích dẫn được đánh dấu</p><p>{start < 0 ? content : <>{content.slice(0, start)}<mark>{content.slice(start, start + quote.length)}</mark>{content.slice(start + quote.length)}</>}</p></div>}
    </details>;
  })}</div>;
}

export default function KnowledgeBase({ user, request, onExpired }) {
  const [documents, setDocuments] = useState([]);
  const [runtime, setRuntime] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [loading, setLoading] = useState(true);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [asking, setAsking] = useState(false);
  const [answerError, setAnswerError] = useState('');
  const [preview, setPreview] = useState(null);
  const [removeId, setRemoveId] = useState(null);
  const [section, setSection] = useState('documents');
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [loadError, setLoadError] = useState('');
  const [slow, setSlow] = useState(false);
  const answerRequest = useRef(null);
  const tabs = [['documents', 'Tài liệu'], ...(user.role === 'admin' ? [['upload', 'Tải tài liệu']] : []), ['ask', 'Thử hỏi AI']];
  const visibleDocuments = documents.filter(document => document.filename.toLocaleLowerCase('vi').includes(search.trim().toLocaleLowerCase('vi')) && (!status || document.status === status));
  useEffect(() => () => answerRequest.current?.abort(), []);
  useEffect(() => {
    setSlow(false);
    if (!asking) return;
    const timer = setTimeout(() => setSlow(true), 15000);
    return () => clearTimeout(timer);
  }, [asking]);
  async function load(signal) {
    try {
      const [data, status] = await Promise.all([request('/documents', { signal }), request('/documents/runtime', { signal })]);
      if (signal?.aborted) return;
      setDocuments(data.documents); setRuntime(status); setLoadError('');
    } catch (error) {
      if (signal?.aborted) return;
      if (error.status === 401) onExpired();
      setLoadError(error.message);
    } finally { if (!signal?.aborted) setLoading(false); }
  }
  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    const timer = setInterval(() => load(controller.signal), 10000);
    return () => { controller.abort(); clearInterval(timer); };
  }, []);
  async function mutate(path, options, id) {
    answerRequest.current?.abort(); setAsking(false);
    setBusy(id); setError(''); setAnswer(null); setPreview(null);
    try {
      const result = await request(path, options);
      if (result.status === 'failed') setError(result.error_message || 'Xử lý tài liệu thất bại.');
      const data = await request('/documents'); setDocuments(data.documents);
      return result.status !== 'failed';
    } catch (error) { if (error.status === 401) onExpired(); setError(error.message); }
    finally { setBusy(''); setRemoveId(null); }
  }
  async function upload(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const body = new FormData(form);
    const file = body.get('file');
    if (!file?.size || file.size > 10 * 1024 * 1024) { setError('Chọn file có nội dung, tối đa 10 MB.'); return; }
    if (await mutate('/documents/upload', { method: 'POST', body }, 'upload')) { form.reset(); setSection('documents'); }
  }
  async function show(document) {
    setPreview({ id: document.document_id, name: document.filename, loading: true });
    try {
      const data = await request(`/documents/${encodeURIComponent(document.document_id)}/chunks`);
      setPreview(current => current?.id === document.document_id ? { ...current, chunks: data.chunks, loading: false } : current);
    } catch (error) { setPreview(current => current?.id === document.document_id ? { ...current, error: error.message, loading: false } : current); }
  }
  async function ask(event) {
    event.preventDefault();
    if (asking || busy || !question.trim()) return;
    answerRequest.current?.abort();
    const controller = new AbortController(); answerRequest.current = controller;
    setAsking(true); setAnswer(null); setAnswerError('');
    try {
      const result = await request('/rag/answer', { method: 'POST', body: JSON.stringify({ query: question.trim() }), signal: controller.signal });
      if (!controller.signal.aborted) setAnswer(result);
    } catch (error) {
      if (!controller.signal.aborted) { if (error.status === 401) onExpired(); setAnswerError(error.message); }
    } finally { if (!controller.signal.aborted) setAsking(false); }
  }
  return <section className="knowledge">
    <header><div><h1>Kho tri thức</h1><p>Tài liệu nội bộ và câu trả lời có trích nguồn</p></div><button onClick={() => { setLoading(true); load(); }} disabled={loading}>Làm mới</button></header>
    <div className="kbTabs" role="tablist" aria-label="Các phần kho tri thức" onKeyDown={event => {
      const index = tabs.findIndex(([id]) => id === section);
      const next = event.key === 'ArrowRight' ? (index + 1) % tabs.length : event.key === 'ArrowLeft' ? (index + tabs.length - 1) % tabs.length : event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : null;
      if (next !== null) { event.preventDefault(); setSection(tabs[next][0]); event.currentTarget.querySelectorAll('[role=tab]')[next].focus(); }
    }}>{tabs.map(([id, label]) => <button key={id} id={`kb-tab-${id}`} role="tab" aria-selected={section === id} aria-controls={`kb-panel-${id}`} tabIndex={section === id ? 0 : -1} onClick={() => setSection(id)}>{label}</button>)}</div>
    <p className={`runtime ${runtime?.ready ? 'ready' : ''}`} role="status">{!runtime ? 'Đang kiểm tra Ollama...' : runtime.ready ? `Ollama kết nối được, đã tải đủ model · ${runtime.chat_model} · ${runtime.embedding_model}` : runtime.error || `Cần tải đủ model ${runtime.chat_model} và ${runtime.embedding_model}.`}</p>
    {loadError && <div role="alert" className="kbError">{loadError} <button onClick={() => load()}>Thử tải lại</button></div>}
    {user.role === 'admin' && <section id="kb-panel-upload" role="tabpanel" aria-labelledby="kb-tab-upload" hidden={section !== 'upload'}><form id="tai-tai-lieu" className="uploadCard" onSubmit={upload} aria-busy={Boolean(busy)}>
      <label>Tải tài liệu<input name="file" type="file" accept=".pdf,.docx,.txt,.md,.markdown" required disabled={Boolean(busy)} /></label>
      <p>PDF, DOCX, TXT, Markdown · tối đa 10 MB. PDF scan cần OCR trước.</p>
      <button disabled={Boolean(busy)}>{busy === 'upload' ? 'Đang trích xuất và lập chỉ mục...' : 'Tải lên và lập chỉ mục'}</button>
    </form></section>}
    {error && <p role="alert" className="kbError">{error}</p>}
    <section id="kb-panel-documents" role="tabpanel" aria-labelledby="kb-tab-documents" hidden={section !== 'documents'}>
    <h2 className="documentHeading" id="tai-lieu">Tài liệu <span>{visibleDocuments.length} / {documents.length} tài liệu</span></h2>
    <div className="documentFilters"><label>Tìm tài liệu<input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Tên tài liệu..." /></label><label>Trạng thái<select value={status} onChange={event => setStatus(event.target.value)}><option value="">Tất cả trạng thái</option>{Object.entries(labels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>{(search || status) && <button onClick={() => { setSearch(''); setStatus(''); }}>Xóa bộ lọc</button>}</div>
    {loading ? <p role="status">Đang tải tài liệu...</p> : !documents.length ? <p>Chưa có tài liệu. {user.role === 'admin' ? <button onClick={() => setSection('upload')}>Tải tài liệu đầu tiên</button> : 'Quản trị viên tải tài liệu để bắt đầu hỏi đáp.'}</p> : !visibleDocuments.length ? <p role="status">Không có tài liệu phù hợp. Thử đổi tên hoặc bỏ bộ lọc trạng thái.</p> : <div className="documentList">{visibleDocuments.map(document => <article className="documentCard" key={document.document_id}>
      <div><h2>{document.filename}</h2><p>{labels[document.status] || document.status} · {document.chunks} đoạn</p>{document.error_message && <p className="kbError">{document.error_message}</p>}</div>
      <div className="documentActions"><button onClick={() => show(document)} disabled={Boolean(busy)}>Xem nội dung</button>
      {user.role === 'admin' && <><button disabled={Boolean(busy) || document.status === 'deleting'} onClick={() => mutate(`/documents/${document.document_id}/reindex`, { method: 'POST' }, document.document_id)}>{busy === document.document_id ? 'Đang xử lý...' : 'Lập chỉ mục lại'}</button><button disabled={Boolean(busy)} onClick={() => setRemoveId(document.document_id)}>Xóa</button></>}</div>
      {removeId === document.document_id && <div className="deleteConfirm" role="alert"><p>Xóa tài liệu, các đoạn và vector? Lịch sử hội thoại vẫn giữ trích dẫn cũ.</p><button disabled={Boolean(busy)} onClick={() => mutate(`/documents/${document.document_id}`, { method: 'DELETE' }, document.document_id)}>Xác nhận xóa</button><button disabled={Boolean(busy)} onClick={() => setRemoveId(null)}>Hủy</button></div>}
    </article>)}</div>}
    {preview && <section className="sourcePreview" aria-label="Nội dung tài liệu"><button onClick={() => setPreview(null)}>Đóng nội dung</button><h2>{preview.name}</h2>{preview.loading ? <p role="status">Đang tải...</p> : preview.error ? <p role="alert">{preview.error}</p> : preview.chunks.map(chunk => <article key={chunk.chunk_id}><h3>{chunk.location || `Đoạn ${chunk.index + 1}`}</h3><p>{chunk.content}</p></article>)}</section>}
    </section>
    <section id="kb-panel-ask" role="tabpanel" aria-labelledby="kb-tab-ask" hidden={section !== 'ask'}><div className="askCard"><h2>Thử hỏi từ tài liệu</h2><p>Trích nguồn giúp đối chiếu, không bảo đảm mọi câu trả lời đều đúng.</p><form onSubmit={ask} aria-busy={asking}><label>Câu hỏi<textarea value={question} onChange={event => setQuestion(event.target.value)} disabled={asking} maxLength={2000} required rows={3} /></label><button disabled={asking || Boolean(busy) || !question.trim()}>{asking ? 'Đang xử lý...' : answerError ? 'Thử lại câu hỏi' : 'Hỏi AI'}</button></form>
      {asking && <p role="status">{slow ? 'Yêu cầu vẫn đang chờ phản hồi. Model có thể cần tải; không cần gửi lại câu hỏi.' : 'Đang tìm nguồn và kiểm định câu trả lời...'}</p>}
      {answerError && <div role="alert" className="kbError"><b>Không xử lý được yêu cầu</b><p>{answerError}</p><p>Câu hỏi được giữ lại. Kiểm tra kết nối rồi thử lại.</p></div>}
      {answer && <div className={`ragAnswer ${answer.needs_clarification ? 'clarification' : answer.grounded ? 'grounded' : 'abstention'}`} role="status"><b>{answer.needs_clarification ? 'Cần làm rõ câu hỏi' : answer.grounded ? 'Có trích nguồn — cần đối chiếu' : 'Chưa đủ bằng chứng'}</b><p>{answer.answer}</p><Citations citations={answer.citations} request={request} /></div>}
      </div>
    </section>
  </section>;
}
