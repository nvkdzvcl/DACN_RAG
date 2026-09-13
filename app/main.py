from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.api.routes import router
from app.db.session import engine
from app.api.documents import router as document_router
from app.api.chunks import router as chunks_router
from app.api.search import router as search_router
from app.api.answer import router as answer_router
from app.api.orders import router as orders_router
from app.api.seed import router as seed_router
from app.api.process import router as process_router
from app.api.inbox import router as inbox_router
from app.api.auth import router as auth_router
from app.core.auth import require_admin, require_staff
from app.db.migrations import migrate
from app.rag.ollama import ProviderError
from app.rag.vector_store import vector_store

@asynccontextmanager
async def lifespan(app):
    migrate(engine)
    with engine.begin() as connection:
        connection.execute(text("UPDATE knowledge_documents SET status = 'failed', index_version = NULL, error_message = 'Xử lý bị gián đoạn. Hãy lập chỉ mục lại.' WHERE status = 'processing'"))
    try:
        yield
    finally:
        vector_store.close()

app = FastAPI(title="AI Customer Support Platform", version="0.1.0", lifespan=lifespan)
app.include_router(auth_router)
for staff_router in (router, document_router, chunks_router, search_router, answer_router, orders_router, process_router, inbox_router):
    app.include_router(staff_router, dependencies=[Depends(require_staff)])
for admin_router in (seed_router,):
    app.include_router(admin_router, dependencies=[Depends(require_admin)])


@app.exception_handler(ProviderError)
def provider_error(request: Request, exc: ProviderError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "customer-support-api"}
