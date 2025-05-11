from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"


class SubscriptionType(int, Enum):
    WEEK = 7
    TWO_WEEKS = 14
    MONTH = 30


class Subscriber(Base):
    __tablename__ = "subscribers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str] = mapped_column(String)
    subscription_type: Mapped[int] = mapped_column(Integer)
    payment_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    subscription_end: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default=SubscriptionStatus.ACTIVE.value)
    payment_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)