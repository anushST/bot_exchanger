from sqlalchemy import Column, Integer, String

from src.core.db import Base


class MarketingLink(Base):
    __tablename__ = "marketing_links"

    name = Column(String, unique=True, nullable=False)

    new_users = Column(Integer, default=0, nullable=True)
    total_clicks = Column(Integer, default=0, nullable=True)
