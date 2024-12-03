from datetime import datetime
from src.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import String, Integer, Boolean, Column, ForeignKey, DateTime, Float


class Exchange(Base):
    __tablename__ = 'exchange'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))

    is_fixed_rate = Column(Boolean, nullable=True)
    currency_from_id = Column(Integer, ForeignKey("currency.id"), nullable=True)
    currency_to_id = Column(Integer, ForeignKey("currency.id"), nullable=True)
    origin_amount = Column(Float, nullable=True)
    final_amount = Column(Float, nullable=True)
    rate = Column(Float, nullable=True)
    commission  = Column(Float, nullable=True)
    wallet = Column(String, nullable=True)

    exchanger_id = Column(Integer, ForeignKey("exchanger.id"), nullable=True)
    exchanger_operation_id = Column(Integer, nullable=True)
    status = Column(Integer, default=0)

    created_on = Column(DateTime(), default=datetime.now)
    updated_on = Column(DateTime(), default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="exchanges")
