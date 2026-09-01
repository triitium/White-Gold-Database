from __future__ import annotations

from datetime import date

from sqlalchemy import BigInteger, Date, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Person(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "people"
    __table_args__ = (Index("ix_people_name", "name"),)

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date)
    death_date: Mapped[date | None] = mapped_column(Date)
    biography: Mapped[str | None] = mapped_column(Text)
    profile_url: Mapped[str | None] = mapped_column(Text)
    profile_path: Mapped[str | None] = mapped_column(Text)
    tmdb_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    imdb_id: Mapped[str | None] = mapped_column(String(20), unique=True)

    movie_credits = relationship(
        "MoviePerson",
        back_populates="person",
        passive_deletes=True,
    )
