from __future__ import annotations

import asyncio
from getpass import getpass

from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models.user import User, UserRole
from app.services.audit import log_audit


async def main() -> None:
    username = input("Username: ").strip()
    email = input("Email: ").strip().lower()
    password = getpass("Password (min 12 chars): ")

    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters")

    async with async_session_factory() as session:
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        session.add(user)
        try:
            await session.flush()
            await log_audit(
                session,
                actor_user_id=None,
                action="CREATE",
                entity_type="user",
                entity_id=user.id,
                before_data=None,
                after_data={
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active,
                },
                reduce_to_diff=False,
            )
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise SystemExit("Username or email already exists") from exc

    print(f"Created admin: {username}")


if __name__ == "__main__":
    asyncio.run(main())
