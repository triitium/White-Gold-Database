from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MovieList(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "movie_lists"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_by = relationship(
        "User",
        back_populates="movie_lists",
    )

    items = relationship(
        "MovieListItem",
        back_populates="movie_list",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MovieListItem.position",
    )


class MovieListItem(Base):
    __tablename__ = "movie_list_items"
    __table_args__ = (
        CheckConstraint(
            "position >= 0",
            name="position_nonnegative",
        ),
    )

    list_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("movie_lists.id", ondelete="CASCADE"),
        primary_key=True,
    )

    movie_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    note: Mapped[str | None] = mapped_column(Text)

    movie_list = relationship(
        "MovieList",
        back_populates="items",
    )

    movie = relationship(
        "Movie",
        back_populates="list_items",
    )
