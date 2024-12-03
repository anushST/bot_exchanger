from datetime import datetime
from src.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Table, Index, String, Integer, Boolean, Column, MetaData, ForeignKey, DateTime, Float

from src.lang import Language


class Currency(Base):
    __tablename__ = 'currency'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, index=True)
    network = Column(String, nullable=True)
    network_code = Column(String, nullable=True, index=True)
