# src/models/tables.py
from sqlalchemy import Table, Column, ForeignKey, UUID
from src.core.db import Base

arbitrator_offer_networks = Table(
    'p2p_arbitrator_offer_networks',
    Base.metadata,
    Column('offer_id', UUID, ForeignKey('p2p_arbitrager_offers.id'), primary_key=True),
    Column('network_id', UUID, ForeignKey('p2p_networks.id'), primary_key=True)
)