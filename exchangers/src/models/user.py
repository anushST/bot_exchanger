from sqlalchemy import Column, Integer, String

from src.database import BaseModel
from src.lang import Language


class User(BaseModel):
    __tablename__ = 'user'
    tg_id = Column(Integer, unique=True, nullable=False)
    tg_name = Column(String(255), nullable=False)
    tg_username = Column(String(255), nullable=True)
    language = Column(String(2), nullable=False, default="ru")

    def get_lang(self):
        return Language(self.language)
