from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Boolean, CheckConstraint, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.USER.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'admin')",
            name="role_valid",
        ),
        Index("uq_users_username_lower", func.lower(username), unique=True),
        Index("uq_users_email_lower", func.lower(email), unique=True),
    )

    user_movies = relationship(
        "UserMovie",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    reviews = relationship(
        "UserReview",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    movie_lists = relationship(
        "MovieList",
        back_populates="created_by",
        passive_deletes=True,
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="actor",
        foreign_keys="AuditLog.actor_user_id",
    )
