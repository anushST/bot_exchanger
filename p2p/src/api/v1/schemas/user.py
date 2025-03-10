from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None


class UserResponse(UserBase):
    is_email_confirmed: bool
    is_active: bool
    tg_id: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True
    )
