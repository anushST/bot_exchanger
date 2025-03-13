from pydantic import BaseModel, UUID4, ConfigDict

from .user import UserResponse


class ModeratorResponse(BaseModel):
    id: UUID4
    user: UserResponse

    model_config = ConfigDict(
        from_attributes=True
    )
