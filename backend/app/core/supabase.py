"""Supabase helpers — validate access tokens issued by Supabase Auth.

We keep FastAPI as the app backend (it runs the ML/geo/business logic) but let
Supabase own credentials and JWT issuance. The frontend signs in with supabase-js
and sends the resulting access token as a Bearer token; here we confirm it with
Supabase's /auth/v1/user endpoint and read back the verified user identity.
"""

import logging
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def verify_supabase_token(token: str) -> Optional[dict[str, Any]]:
    """Return the Supabase user ({id, email, ...}) for a valid access token, else None."""
    if not (settings.SUPABASE_URL and settings.SUPABASE_PUBLISHABLE_KEY):
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/user",
                headers={
                    "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
                    "Authorization": f"Bearer {token}",
                },
            )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("id"):
            return data
        return None
    except Exception as exc:  # pragma: no cover - network/parse safety
        logger.info("Supabase token verification failed: %s", exc)
        return None
