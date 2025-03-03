from pydantic import BaseModel, EmailStr


class RefreshRequest(BaseModel):
    refresh_token: str


class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str


class CreateLogin(BaseModel):
    username: EmailStr
    password: str
