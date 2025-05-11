from sqlalchemy import select
from app.database.models import Subscriber
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime


async def get_subscriber(session: AsyncSession, telegram_id: int) -> Subscriber | None:
    result = await session.execute(
        select(Subscriber).where(Subscriber.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def update_subscriber_payment(
    session: AsyncSession,
    telegram_id: int,
    username: str,
    subscription_type: int,
    payment_date: datetime,
    subscription_end: datetime,
    status: str,
    payment_id: str,
):
    subscriber = await get_subscriber(session, telegram_id)
    if subscriber:
        subscriber.username = username
        subscriber.subscription_type = subscription_type
        subscriber.payment_date = payment_date
        subscriber.subscription_end = subscription_end
        subscriber.status = status
        subscriber.payment_id = payment_id
    else:
        subscriber = Subscriber(
            telegram_id=telegram_id,
            username=username,
            subscription_type=subscription_type,
            payment_date=payment_date,
            subscription_end=subscription_end,
            status=status,
            payment_id=payment_id,
        )
        session.add(subscriber)
    await session.commit()


async def update_subscriber_declined(
    session: AsyncSession,
    telegram_id: int,
    username: str,
    status: str,
    payment_id: str,
):
    subscriber = await get_subscriber(session, telegram_id)
    if subscriber:
        subscriber.username = username
        subscriber.status = status
        subscriber.payment_id = payment_id
        subscriber.payment_date = None
        subscriber.subscription_end = None
    else:
        subscriber = Subscriber(
            telegram_id=telegram_id,
            username=username,
            subscription_type=0,
            payment_date=None,
            subscription_end=None,
            status=status,
            payment_id=payment_id,
        )
        session.add(subscriber)
    await session.commit()
