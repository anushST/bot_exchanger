from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.db import Base


class MarketingLinkUser(Base):
    __tablename__ = 'marketing_link_user'
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'),
                     nullable=False)
    marketing_link_id = Column(UUID(as_uuid=True),
                               ForeignKey('marketing_links.id'),
                               nullable=False)

    user = relationship('User', lazy='joined')
