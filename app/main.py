from fastapi import FastAPI
from app.api.routes import router
from app.db.session import Base, engine
from app.models import support  # noqa: F401
from app.api.documents import router as document_router
from app.api.chunks import router as chunks_router
from app.api.search import router as search_router
from app.api.answer import router as answer_router
from app.api.orders import router as orders_router
from app.api.seed import router as seed_router
from app.api.process import router as process_router
from app.api.inbox import router as inbox_router

app = FastAPI(title="AI Customer Support Platform", version="0.1.0")
Base.metadata.create_all(bind=engine)
app.include_router(router)
app.include_router(document_router)
app.include_router(chunks_router)
app.include_router(search_router)
app.include_router(answer_router)
app.include_router(orders_router)
app.include_router(seed_router)
app.include_router(process_router)
app.include_router(inbox_router)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "customer-support-api"}
