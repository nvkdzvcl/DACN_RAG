import React, { useEffect, useState } from 'react';

const labels = { indexed: 'Đã lập chỉ mục', processing: 'Đang xử lý', failed: 'Xử lý lỗi', ready_for_embedding: 'Cần lập chỉ mục lại', deleting: 'Xóa chưa hoàn tất', uploaded: 'Đã tải lên' };

export function Citations({ citations, request }) {
  const [source, setSource] = useState(null);
  async function open(citation) {
    setSource({ id: citation.chunk_id, loading: true });
    try {
      const data = await request(`/documents/${encodeURIComponent(citation.document_id)}/chunks/${encodeURIComponent(citation.chunk_id)}?index_version=${encodeURIComponent(citation.index_version || '')}`);
      setSource(current => current?.id === citation.chunk_id ? { id: citation.chunk_id, ...data } : current);
    } catch (error) {
      setSource(current => current?.id === citation.chunk_id ? { id: citation.chunk_id, error: error.message } : current);
    }
  }
  return <div className="citations">{citations.map((citation, index) => <details key={`${citation.chunk_id}-${index}`}>
    <summary>{citation.source}{citation.location ? ` · ${citation.location}` : ''}</summary>
    {citation.quote && <blockquote>{citation.quote}</blockquote>}
    {citation.document_id && <button type="button" onClick={() => open(citation)}>Xem đoạn nguồn</button>}
    {source?.id === citation.chunk_id && <p role={source.error ? 'alert' : 'status'}>{source.loading ? 'Đang tải nguồn...' : source.error || source.content}</p>}
  </details>)}</div>;
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
  async function load(signal) {
    try {
      const [data, status] = await Promise.all([request('/documents', { signal }), request('/documents/runtime', { signal })]);
      if (signal?.aborted) return;
      setDocuments(data.documents); setRuntime(status); setError('');
    } catch (error) {
      if (signal?.aborted) return;
      if (error.status === 401) onExpired();
      setError(error.message);
    } finally { if (!signal?.aborted) setLoading(false); }
  }
  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    const timer = setInterval(() => load(controller.signal), 10000);
    return () => { controller.abort(); clearInterval(timer); };
  }, []);
  async function mutate(path, options, id) {
    setBusy(id); setError(''); setAnswer(null); setPreview(null);
    try {
      const result = await request(path, options);
      if (result.status === 'failed') setError(result.error_message);
      const data = await request('/documents'); setDocuments(data.documents);
    } catch (error) { if (error.status === 401) onExpired(); setError(error.message); }
    finally { setBusy(''); setRemoveId(null); }
  }
  async function upload(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const body = new FormData(form);
    const file = body.get('file');
    if (!file?.size || file.size > 10 * 1024 * 1024) { setError('Chọn file có nội dung, tối đa 10 MB.'); return; }
    await mutate('/documents/upload', { method: 'POST', body }, 'upload'); form.reset();
  }
  async function show(document) {
    setPreview({ id: document.document_id, name: document.filename, loading: true });
    try {
      const data = await request(`/documents/${encodeURIComponent(document.document_id)}/chunks`);
      setPreview(current => current?.id === document.document_id ? { ...current, chunks: data.chunks, loading: false } : current);
    } catch (error) { setPreview(current => current?.id === document.document_id ? { ...current, error: error.message, loading: false } : current); }
  }
  async function ask(event) {
    event.preventDefault(); setAsking(true); setAnswer(null); setAnswerError('');
    try { setAnswer(await request('/rag/answer', { method: 'POST', body: JSON.stringify({ query: question.trim() }) })); }
    catch (error) { if (error.status === 401) onExpired(); setAnswerError(error.message); }
    finally { setAsking(false); }
  }
  return <section className="knowledge">
    <header><div><h1>Kho tri thức</h1><p>Tài liệu nội bộ và câu trả lời có trích nguồn</p></div><button onClick={() => load()} disabled={loading}>Làm mới</button></header>
    <p className={`runtime ${runtime?.ready ? 'ready' : ''}`} role="status">{!runtime ? 'Đang kiểm tra Ollama...' : runtime.ready ? `Ollama kết nối được, đã tải đủ model · ${runtime.chat_model} · ${runtime.embedding_model}` : runtime.error || `Cần tải đủ model ${runtime.chat_model} và ${runtime.embedding_model}.`}</p>
    {user.role === 'admin' && <form className="uploadCard" onSubmit={upload} aria-busy={Boolean(busy)}>
      <label>Tải tài liệu<input name="file" type="file" accept=".pdf,.docx,.txt,.md,.markdown" required disabled={Boolean(busy)} /></label>
      <p>PDF, DOCX, TXT, Markdown · tối đa 10 MB. PDF scan cần OCR trước.</p>
      <button disabled={Boolean(busy)}>{busy === 'upload' ? 'Đang trích xuất và lập chỉ mục...' : 'Tải lên và lập chỉ mục'}</button>
    </form>}
    {error && <p role="alert" className="kbError">{error}</p>}
    {loading ? <p role="status">Đang tải tài liệu...</p> : !documents.length ? <p>Chưa có tài liệu. Quản trị viên tải tài liệu để bắt đầu hỏi đáp.</p> : <div className="documentList">{documents.map(document => <article className="documentCard" key={document.document_id}>
      <div><h2>{document.filename}</h2><p>{labels[document.status] || document.status} · {document.chunks} đoạn</p>{document.error_message && <p className="kbError">{document.error_message}</p>}</div>
      <div className="documentActions"><button onClick={() => show(document)} disabled={Boolean(busy)}>Xem nội dung</button>
      {user.role === 'admin' && <><button disabled={Boolean(busy) || document.status === 'deleting'} onClick={() => mutate(`/documents/${document.document_id}/reindex`, { method: 'POST' }, document.document_id)}>{busy === document.document_id ? 'Đang xử lý...' : 'Lập chỉ mục lại'}</button><button disabled={Boolean(busy)} onClick={() => setRemoveId(document.document_id)}>Xóa</button></>}</div>
      {removeId === document.document_id && <div className="deleteConfirm" role="alert"><p>Xóa tài liệu, các đoạn và vector? Lịch sử hội thoại vẫn giữ trích dẫn cũ.</p><button disabled={Boolean(busy)} onClick={() => mutate(`/documents/${document.document_id}`, { method: 'DELETE' }, document.document_id)}>Xác nhận xóa</button><button disabled={Boolean(busy)} onClick={() => setRemoveId(null)}>Hủy</button></div>}
    </article>)}</div>}
    {preview && <section className="sourcePreview" aria-label="Nội dung tài liệu"><button onClick={() => setPreview(null)}>Đóng nội dung</button><h2>{preview.name}</h2>{preview.loading ? <p role="status">Đang tải...</p> : preview.error ? <p role="alert">{preview.error}</p> : preview.chunks.map(chunk => <article key={chunk.chunk_id}><h3>{chunk.location || `Đoạn ${chunk.index + 1}`}</h3><p>{chunk.content}</p></article>)}</section>}
    <section className="askCard"><h2>Thử hỏi từ tài liệu</h2><form onSubmit={ask}><label>Câu hỏi<textarea value={question} onChange={event => setQuestion(event.target.value)} maxLength={2000} required rows={3} /></label><button disabled={asking || Boolean(busy) || !question.trim()}>{asking ? 'Đang tìm nguồn và tạo câu trả lời...' : 'Hỏi AI'}</button></form>
      {answerError && <p role="alert" className="kbError">{answerError}</p>}
      {answer && <div className="ragAnswer" role="status"><b>{answer.grounded ? 'Có trích nguồn' : 'Chưa đủ bằng chứng'}</b><p>{answer.answer}</p><Citations citations={answer.citations} request={request} /></div>}
    </section>
  </section>;
}
