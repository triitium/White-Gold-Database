from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.audit import log_audit


def snapshot(obj, fields: tuple[str, ...]) -> dict[str, Any]:
    data = {"id": str(obj.id)}
    for field in fields:
        value = getattr(obj, field)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        data[field] = value
    return data


async def create_reference(
    session: AsyncSession,
    *,
    model,
    values: dict[str, Any],
    fields: tuple[str, ...],
    entity_type: str,
    actor_user_id: UUID,
):
    obj = model(**values)
    session.add(obj)
    await session.flush()

    await log_audit(
        session,
        actor_user_id=actor_user_id,
        action="CREATE",
        entity_type=entity_type,
        entity_id=obj.id,
        before_data=None,
        after_data=snapshot(obj, fields),
        reduce_to_diff=False,
    )
    return obj


async def update_reference(
    session: AsyncSession,
    *,
    obj,
    changes: dict[str, Any],
    fields: tuple[str, ...],
    entity_type: str,
    actor_user_id: UUID,
):
    before = snapshot(obj, fields)
    for field, value in changes.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(obj, field, value)
    await session.flush()
    after = snapshot(obj, fields)

    await log_audit(
        session,
        actor_user_id=actor_user_id,
        action="UPDATE",
        entity_type=entity_type,
        entity_id=obj.id,
        before_data=before,
        after_data=after,
        reduce_to_diff=True,
    )
    return obj
