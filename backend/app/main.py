from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.models import models  # noqa: F401 — ensures models are registered on Base
from app.api import auth, projects, datasets, analyst, ml


@asynccontextmanager
async def lifespan(app: FastAPI):
    # For local dev only. In production, use Alembic migrations instead
    # of create_all so schema changes are tracked and reversible.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="DataPilot API",
    description="The AI Analyst for Every Business — backend API",
    version="0.1.0",
    lifespan=lifespan,
)

DEFAULT_LOCAL_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]
extra_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_LOCAL_ORIGINS + extra_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(datasets.router)
app.include_router(analyst.router)
app.include_router(ml.router)


@app.get("/health")
def health():
    return {"status": "ok"}
