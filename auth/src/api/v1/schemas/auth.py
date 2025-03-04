from pydantic import BaseModel, EmailStr


class RefreshRequest(BaseModel):
    refresh_token: str


class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str


class CreateLogin(BaseModel):
    username: EmailStr
    password: str


class TelegramAuthRequest(BaseModel):
    id: int
    first_name: str
    username: str
    photo_url: str
    auth_date: int
    hash: str
