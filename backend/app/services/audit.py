"""Audit event helper — append-only history."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_event import AuditEvent


async def record_audit(
    db: AsyncSession,
    *,
    actor_id: UUID | None,
    entity_type: str,
    entity_id: UUID,
    action: str,
    previous_value: dict | None = None,
    new_value: dict | None = None,
) -> None:
    db.add(AuditEvent(
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        previous_value=previous_value,
        new_value=new_value,
    ))
    await db.flush()
