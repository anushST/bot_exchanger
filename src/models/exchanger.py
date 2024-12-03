from src.database import Base
from sqlalchemy import String, Integer, Column


class Exchanger(Base):
    __tablename__ = 'exchanger'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    token = Column(String, nullable=False)
    additional_token = Column(String, nullable=True)
