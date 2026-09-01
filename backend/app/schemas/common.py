from __future__ import annotations

import math
from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    pages: int
    has_previous: bool
    has_next: bool

    @classmethod
    def create(cls, *, items: list[T], page: int, page_size: int, total: int):
        pages = math.ceil(total / page_size) if total else 0
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            pages=pages,
            has_previous=page > 1,
            has_next=page < pages,
        )
