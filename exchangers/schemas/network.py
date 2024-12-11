from pydantic import BaseModel


class NetworkSchema(BaseModel):
    network_name: str
