from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    full_name: Optional[str] = None


class UserCreate(UserBase):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None


class UserResponse(UserBase):
    email: Optional[EmailStr]
    is_email_confirmed: bool
    is_active: bool
    tg_id: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True
    )
