from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.services.audit import log_audit


def user_snapshot(user: User) -> dict:
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }


async def list_users(
    session: AsyncSession,
    *,
    q: str | None = None,
) -> list[User]:
    stmt = select(User)

    if q:
        needle = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            func.lower(User.username).like(needle)
            | func.lower(User.email).like(needle)
        )

    return (
        await session.scalars(
            stmt.order_by(func.lower(User.username))
        )
    ).all()


async def change_role(
    session: AsyncSession,
    *,
    target: User,
    new_role: str,
    actor_user_id: UUID,
) -> User:
    if new_role not in {
        UserRole.USER.value,
        UserRole.ADMIN.value,
    }:
        raise ValueError("Invalid role")

    before = user_snapshot(target)
    target.role = new_role
    await session.flush()
    after = user_snapshot(target)

    await log_audit(
        session,
        actor_user_id=actor_user_id,
        action="ROLE_CHANGE",
        entity_type="user",
        entity_id=target.id,
        before_data=before,
        after_data=after,
        reduce_to_diff=True,
    )

    return target


async def change_active(
    session: AsyncSession,
    *,
    target: User,
    is_active: bool,
    actor_user_id: UUID,
) -> User:
    before = user_snapshot(target)
    target.is_active = is_active
    await session.flush()
    after = user_snapshot(target)

    await log_audit(
        session,
        actor_user_id=actor_user_id,
        action="ACTIVATE" if is_active else "DEACTIVATE",
        entity_type="user",
        entity_id=target.id,
        before_data=before,
        after_data=after,
        reduce_to_diff=True,
    )

    return target
