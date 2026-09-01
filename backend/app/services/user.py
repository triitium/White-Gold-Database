from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.scalar(select(User).where(User.id == user_id))


async def get_user_by_login(session: AsyncSession, login: str) -> User | None:
    normalized = login.strip().lower()
    return await session.scalar(
        select(User).where(
            or_(
                func.lower(User.username) == normalized,
                func.lower(User.email) == normalized,
            )
        )
    )


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    user = User(
        username=data.username.strip(),
        email=str(data.email).strip().lower(),
        password_hash=hash_password(data.password),
        role=data.role,
    )
    session.add(user)
    await session.flush()
    return user
