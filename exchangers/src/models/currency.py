from sqlalchemy import Column, String

from src.database import BaseModel


class Currency(BaseModel):
    __tablename__ = 'currency'
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(32), nullable=False, index=True, unique=True)
    network = Column(String(255), nullable=False)
    network_code = Column(String(32), nullable=False, index=True)
    image_url = Column(String(2083), nullable=True)
