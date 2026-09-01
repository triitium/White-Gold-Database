from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.services.user import get_user_by_login


async def authenticate_user(
    session: AsyncSession,
    login: str,
    password: str,
) -> User | None:
    user = await get_user_by_login(session, login)

    if user is None or not user.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def issue_access_token(user: User) -> str:
    return create_access_token(user.id)
