"""UrbanLens AI — FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.APP_ENV != "test":
        try:
            from app.services.storage import storage_service

            storage_service.ensure_buckets()
        except Exception as exc:
            logging.getLogger(__name__).warning(
                "Object storage unavailable at startup: %s", exc
            )
    try:
        yield
    finally:
        from app.database import engine

        await engine.dispose()


app = FastAPI(
    title="UrbanLens AI",
    description="Civic intelligence platform for Navi Mumbai",
    version="0.1.0",
    lifespan=lifespan,
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
