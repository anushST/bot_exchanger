from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams:
    def __init__(self, limit: int = Query(10, ge=1, le=100),
                 offset: int = Query(0, ge=0)):
        self.limit = limit
        self.offset = offset


class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    items: list[T]
