from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import connect_db, disconnect_db
from app.api.v1.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    yield
    # Shutdown
    await disconnect_db()

app = FastAPI(
    title="StockFlow Pro API",
    description="API de gestion de stock intelligente pour PME tunisiennes",
    version="1.0.0 (MVP Phase 1)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes API v1
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "StockFlow Pro API",
        "version": "1.0.0",
        "phase": "MVP Phase 1",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
