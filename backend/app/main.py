"""UrbanLens AI — FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.database import engine, Base

# Create tables (dev only — use Alembic in production)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="UrbanLens AI",
    description="Civic intelligence platform for Navi Mumbai",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
