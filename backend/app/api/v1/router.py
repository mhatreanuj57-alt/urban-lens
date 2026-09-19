"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1 import reports, incidents, uploads, auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
