from sqlalchemy.orm import relationship

from src.database import Base
from datetime import datetime
from sqlalchemy import Table, Index, String, Integer, Boolean, Column, MetaData, ForeignKey, DateTime

from src.lang import Language


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    tg_name = Column(String, nullable=False)
    tg_username = Column(String, nullable=True)
    language = Column(String, nullable=False, default="ru")
    created_on = Column(DateTime(), default=datetime.now)
    updated_on = Column(DateTime(), default=datetime.now, onupdate=datetime.now)

    exchanges = relationship("Exchange", back_populates="user")

    def get_lang(self):
        return Language(self.language)
