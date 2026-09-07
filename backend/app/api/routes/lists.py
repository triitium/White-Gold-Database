from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import (
    AdminUser,
    CsrfProtected,
    CurrentUser,
    SessionDep,
)
from app.mappers.movie_list import (
    movie_list_to_read,
    movie_list_to_summary,
)
from app.schemas.common import Page
from app.schemas.movie_list import (
    MovieListCreate,
    MovieListItemCreate,
    MovieListItemUpdate,
    MovieListRead,
    MovieListReorder,
    MovieListSummaryRead,
    MovieListUpdate,
)
from app.services import movie_list as movie_list_service


router = APIRouter(
    prefix="/lists",
    tags=["lists"],
)


async def _active_list_or_404(
    session: SessionDep,
    list_id: UUID,
):
    movie_list = await movie_list_service.get_movie_list(
        session,
        list_id,
    )

    if movie_list is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "List not found",
        )

    return movie_list


def _require_owner(movie_list, user_id: UUID) -> None:
    try:
        movie_list_service.require_owner(
            movie_list,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            str(exc),
        ) from exc


@router.get(
    "",
    response_model=Page[MovieListSummaryRead],
)
async def list_public_movie_lists(
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 25,
):
    rows, total = await movie_list_service.list_movie_lists(
        session,
        page=page,
        page_size=page_size,
    )

    return Page[MovieListSummaryRead].create(
        items=[
            movie_list_to_summary(row)
            for row in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/mine",
    response_model=list[MovieListSummaryRead],
)
async def list_my_movie_lists(
    session: SessionDep,
    current_user: CurrentUser,
):
    rows = await movie_list_service.list_my_movie_lists(
        session,
        user_id=current_user.id,
    )

    return [
        movie_list_to_summary(row)
        for row in rows
    ]


@router.post(
    "",
    response_model=MovieListRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie_list(
    data: MovieListCreate,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
):
    try:
        movie_list = await movie_list_service.create_movie_list(
            session,
            data=data,
            user_id=current_user.id,
        )
        await session.commit()

        movie_list = await movie_list_service.get_movie_list(
            session,
            movie_list.id,
        )
        return movie_list_to_read(movie_list)
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            str(exc),
        ) from exc


@router.get(
    "/{list_id}",
    response_model=MovieListRead,
)
async def get_public_movie_list(
    list_id: UUID,
    session: SessionDep,
):
    movie_list = await _active_list_or_404(
        session,
        list_id,
    )
    return movie_list_to_read(movie_list)


@router.patch(
    "/{list_id}",
    response_model=MovieListRead,
)
async def update_movie_list(
    list_id: UUID,
    data: MovieListUpdate,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
):
    movie_list = await _active_list_or_404(
        session,
        list_id,
    )
    _require_owner(movie_list, current_user.id)

    try:
        await movie_list_service.update_movie_list(
            session,
            movie_list=movie_list,
            data=data,
            user_id=current_user.id,
        )
        await session.commit()

        movie_list = await movie_list_service.get_movie_list(
            session,
            list_id,
        )
        return movie_list_to_read(movie_list)
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            str(exc),
        ) from exc


@router.delete(
    "/{list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie_list(
    list_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
) -> None:
    movie_list = await _active_list_or_404(
        session,
        list_id,
    )
    _require_owner(movie_list, current_user.id)

    await movie_list_service.soft_delete_movie_list(
        session,
        movie_list=movie_list,
        actor_user_id=current_user.id,
    )
    await session.commit()


@router.post(
    "/{list_id}/items",
    response_model=MovieListRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_movie_list_item(
    list_id: UUID,
    data: MovieListItemCreate,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
):
    movie_list = await _active_list_or_404(
        session,
        list_id,
    )
    _require_owner(movie_list, current_user.id)

    try:
        await movie_list_service.add_movie_list_item(
            session,
            movie_list=movie_list,
            data=data,
            user_id=current_user.id,
        )
        await session.commit()

        movie_list = await movie_list_service.get_movie_list(
            session,
            list_id,
        )
        return movie_list_to_read(movie_list)
    except LookupError as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            str(exc),
        ) from exc
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            str(exc),
        ) from exc


@router.patch(
    "/{list_id}/items/{movie_id}",
    response_model=MovieListRead,
)
async def update_movie_list_item(
    list_id: UUID,
    movie_id: UUID,
    data: MovieListItemUpdate,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
):
    movie_list = await _active_list_or_404(
        session,
        list_id,
    )
    _require_owner(movie_list, current_user.id)

    try:
        await movie_list_service.update_movie_list_item(
            session,
            movie_list=movie_list,
            movie_id=movie_id,
            data=data,
            user_id=current_user.id,
        )
        await session.commit()

        movie_list = await movie_list_service.get_movie_list(
            session,
            list_id,
        )
        return movie_list_to_read(movie_list)
    except LookupError as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            str(exc),
        ) from exc


@router.delete(
    "/{list_id}/items/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_movie_list_item(
    list_id: UUID,
    movie_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
) -> None:
    movie_list = await _active_list_or_404(
        session,
        list_id,
    )
    _require_owner(movie_list, current_user.id)

    try:
        await movie_list_service.remove_movie_list_item(
            session,
            movie_list=movie_list,
            movie_id=movie_id,
            user_id=current_user.id,
        )
        await session.commit()
    except LookupError as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            str(exc),
        ) from exc


@router.put(
    "/{list_id}/items/order",
    response_model=MovieListRead,
)
async def reorder_movie_list(
    list_id: UUID,
    data: MovieListReorder,
    session: SessionDep,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
):
    movie_list = await _active_list_or_404(
        session,
        list_id,
    )
    _require_owner(movie_list, current_user.id)

    try:
        await movie_list_service.reorder_movie_list(
            session,
            movie_list=movie_list,
            movie_ids=data.movie_ids,
            user_id=current_user.id,
        )
        await session.commit()

        movie_list = await movie_list_service.get_movie_list(
            session,
            list_id,
        )
        return movie_list_to_read(movie_list)
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            str(exc),
        ) from exc


admin_router = APIRouter(
    prefix="/admin/lists",
    tags=["admin", "lists"],
)


@admin_router.delete(
    "/{list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def admin_delete_movie_list(
    list_id: UUID,
    session: SessionDep,
    admin: AdminUser,
    _csrf: CsrfProtected,
) -> None:
    movie_list = await movie_list_service.get_movie_list(
        session,
        list_id,
    )

    if movie_list is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "List not found",
        )

    await movie_list_service.soft_delete_movie_list(
        session,
        movie_list=movie_list,
        actor_user_id=admin.id,
        require_actor_owner=False,
        action="MODERATION_DELETE",
    )

    await session.commit()
