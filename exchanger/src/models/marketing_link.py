from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.db import Base


class MarketingLink(Base):
    __tablename__ = "marketing_links"

    name = Column(String, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"),
                     nullable=False)

    new_users = Column(Integer, default=0, nullable=False)
    total_clicks = Column(Integer, default=0, nullable=False)

    user = relationship("User", lazy="joined")
