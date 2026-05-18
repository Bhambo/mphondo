from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.database import engine
from app.core.logging import configure_logging
from app.modules.ledger.router import router as ledger_router
from app.modules.mpesa.router import router as mpesa_router
from app.modules.banking_es.router import router as banking_es_router
from app.modules.xitiqui.router import router as xitiqui_router
from app.modules.analytics.router import router as analytics_router
from app.modules.accounts.router import router as accounts_router
from app.modules.budgets.router import router as budgets_router

configure_logging()
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", environment=settings.ENVIRONMENT)
    yield
    await engine.dispose()
    log.info("shutdown")


app = FastAPI(
    title="Mphondo API",
    version="0.1.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)

# CORS — Tailscale-only: allow the Expo dev client and the self-hosted frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics at /api/metrics (scraped by Prometheus container)
Instrumentator(excluded_handlers=["/api/health"]).instrument(app).expose(
    app, endpoint="/api/metrics", include_in_schema=False
)

# ── Routers ────────────────────────────────────────────────────────────────
API = "/api/v1"

app.include_router(accounts_router,   prefix=f"{API}/accounts",   tags=["accounts"])
app.include_router(ledger_router,     prefix=f"{API}/ledger",     tags=["ledger"])
app.include_router(mpesa_router,      prefix=f"{API}/mpesa",      tags=["mpesa"])
app.include_router(banking_es_router, prefix=f"{API}/banking-es", tags=["banking-es"])
app.include_router(xitiqui_router,    prefix=f"{API}/xitiqui",    tags=["xitiqui"])
app.include_router(analytics_router,  prefix=f"{API}/analytics",  tags=["analytics"])
app.include_router(budgets_router,    prefix=f"{API}/budgets",    tags=["budgets"])


@app.get("/api/health", include_in_schema=False)
async def health() -> dict:
    return {"status": "ok", "version": app.version}
