from datetime import datetime
from src.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Table, Index, String, Integer, Boolean, Column, MetaData, ForeignKey, DateTime, Float

from src.lang import Language


class ExchangerCurrency(Base):
    __tablename__ = 'currency'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    currency_id = Column(Integer, ForeignKey('currency.id'), nullable=False)
    value = Column(String, nullable=False)
    exchanger_id = Column(Integer, ForeignKey("exchanger.id"), nullable=True)
