from sqlalchemy import Column, String

from src.database import BaseModel


class Currency(BaseModel):
    __tablename__ = 'currency'
    name = Column(String(255), nullable=False)
    code = Column(String(32), nullable=False, index=True)
    network = Column(String(255), nullable=True)
    network_code = Column(String(32), nullable=True, index=True)
