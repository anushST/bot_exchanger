from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class JsonRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str = Field(default_factory=lambda: str(uuid4()))
    method: str
    params: Any


class ErrorModel(BaseModel):
    jsonrpc: str = "2.0"
    id: str = Field(default_factory=lambda: str(uuid4()))
    error: Optional[Any] = None
    code: Optional[int] = None
    message: Optional[str] = None


class JsonRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str = Field(default_factory=lambda: str(uuid4()))
    result: Optional[Any] = None
    error: Optional[ErrorModel] = None
