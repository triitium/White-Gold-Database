from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=200)


class LoginResponse(BaseModel):
    authenticated: bool = True


class LogoutResponse(BaseModel):
    authenticated: bool = False
