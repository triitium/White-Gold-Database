from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


AUDIT_CREATE = "CREATE"
AUDIT_UPDATE = "UPDATE"
AUDIT_SOFT_DELETE = "SOFT_DELETE"
AUDIT_RESTORE = "RESTORE"
AUDIT_HARD_DELETE = "HARD_DELETE"


def diff_snapshots(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """
    Reduce two snapshots to changed top-level fields only.

    CREATE:
        before=None, after=full snapshot
    HARD_DELETE:
        before=full snapshot, after=None
    UPDATE/DELETE/RESTORE:
        only changed fields are retained.
    """
    if before is None or after is None:
        return (
            deepcopy(before) if before is not None else None,
            deepcopy(after) if after is not None else None,
        )

    changed_before: dict[str, Any] = {}
    changed_after: dict[str, Any] = {}

    keys = set(before) | set(after)

    for key in keys:
        old = before.get(key)
        new = after.get(key)

        if old != new:
            changed_before[key] = deepcopy(old)
            changed_after[key] = deepcopy(new)

    return (
        changed_before or None,
        changed_after or None,
    )


async def log_audit(
    session: AsyncSession,
    *,
    actor_user_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID,
    before_data: dict[str, Any] | None,
    after_data: dict[str, Any] | None,
    reduce_to_diff: bool = True,
) -> AuditLog:
    if reduce_to_diff:
        before_data, after_data = diff_snapshots(
            before_data,
            after_data,
        )

    log = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_data=before_data,
        after_data=after_data,
    )

    session.add(log)
    await session.flush()

    return log
