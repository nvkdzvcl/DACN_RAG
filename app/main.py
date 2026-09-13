from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
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

@asynccontextmanager
async def lifespan(app):
    migrate(engine)
    yield

app = FastAPI(title="AI Customer Support Platform", version="0.1.0", lifespan=lifespan)
app.include_router(auth_router)
for staff_router in (router, chunks_router, search_router, answer_router, orders_router, process_router, inbox_router):
    app.include_router(staff_router, dependencies=[Depends(require_staff)])
for admin_router in (document_router, seed_router):
    app.include_router(admin_router, dependencies=[Depends(require_admin)])


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "customer-support-api"}
