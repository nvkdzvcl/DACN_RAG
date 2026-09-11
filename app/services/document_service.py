from pathlib import Path
from uuid import uuid4

from docx import Document
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models.support import KnowledgeDocument
from app.models.support import DocumentChunk

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown"}
MAX_FILE_SIZE = 10 * 1024 * 1024
CHUNK_SIZE = 900
CHUNK_OVERLAP = 120

def chunk_text(text: str) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - CHUNK_OVERLAP
    return chunks


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages).strip()
    if path.suffix.lower() == ".docx":
        return "\n".join(p.text for p in Document(str(path)).paragraphs).strip()
    return path.read_text(encoding="utf-8", errors="replace").strip()


def save_document(db: Session, filename: str, content: bytes, root: Path) -> dict:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported document type")
    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File exceeds 10 MB limit")
    document_id = str(uuid4())
    target_dir = root / document_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / Path(filename).name
    target.write_bytes(content)
    record = KnowledgeDocument(id=document_id, filename=Path(filename).name, status="processing")
    db.add(record)
    try:
        text = extract_text(target)
        if not text:
            raise ValueError("No text could be extracted")
        chunks = chunk_text(text)
        for index, chunk in enumerate(chunks):
            db.add(DocumentChunk(id=f"{document_id}_{index:04d}", document_id=document_id, chunk_index=index, content=chunk, source=record.filename))
        record.status = "ready_for_embedding"
        db.commit()
        return {"document_id": document_id, "filename": record.filename, "status": record.status, "characters": len(text), "chunks": len(chunks), "text": text}
    except Exception as exc:
        record.status = "failed"
        record.error_message = str(exc)
        db.commit()
        raise
