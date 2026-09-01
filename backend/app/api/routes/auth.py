from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CsrfProtected, CurrentUser, SessionDep
from app.core.config import settings
from app.core.security import (
    ACCESS_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    generate_csrf_token,
)
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse
from app.schemas.user import UserRead
from app.services import auth as auth_service


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


def _set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    csrf_token: str,
) -> None:
    max_age = settings.access_token_expire_minutes * 60

    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )

    # Deliberately NOT HttpOnly: React must echo this value in X-CSRF-Token.
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


def _delete_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        ACCESS_COOKIE_NAME,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )
    response.delete_cookie(
        CSRF_COOKIE_NAME,
        path="/",
        secure=settings.cookie_secure,
        httponly=False,
        samesite=settings.cookie_samesite,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(
    data: LoginRequest,
    response: Response,
    session: SessionDep,
) -> LoginResponse:
    user = await auth_service.authenticate_user(
        session,
        data.login,
        data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
        )

    access_token = auth_service.issue_access_token(user)
    csrf_token = generate_csrf_token()

    _set_auth_cookies(
        response,
        access_token=access_token,
        csrf_token=csrf_token,
    )

    return LoginResponse()


@router.post(
    "/logout",
    response_model=LogoutResponse,
)
async def logout(
    response: Response,
    current_user: CurrentUser,
    _csrf: CsrfProtected,
) -> LogoutResponse:
    _delete_auth_cookies(response)
    return LogoutResponse()


@router.get(
    "/me",
    response_model=UserRead,
)
async def me(
    current_user: CurrentUser,
) -> UserRead:
    return UserRead.model_validate(current_user)
