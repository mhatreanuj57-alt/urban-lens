"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1 import analytics, auth, complaints, incidents, reports, risk, uploads

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(complaints.router, prefix="/reports", tags=["complaints"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
