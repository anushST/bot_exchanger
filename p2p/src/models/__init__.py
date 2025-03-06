# flake8: noqa: F401
from sqlalchemy.ext.asyncio import AsyncEngine

from .appeal import ModerationRequest, ModerationStatus
from .bank import Bank
from .currency import Currency, CurrencyType, Network
from .deal import Deal, DealStatus
from .messages import ChatMessage, MessageType
from .offer import Offer, OfferType
from .tables import arbitrator_offer_networks
from .user import Moderator, Arbitrager, User, UserRole
from src.core.db import Base


async def init_models(db: AsyncEngine):
    async with db.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
