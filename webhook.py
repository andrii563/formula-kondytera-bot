import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import handlers
from app.bot.commands import setup_commands
from app.core.config import settings
from app.core.logger import logger
from app.database.crud import (
    get_subscriber,
    update_subscriber_declined,
    update_subscriber_payment,
)
from app.database.models import Subscriber, SubscriptionStatus
from app.database.session import get_session

DECLINE_REASONS = {
    1101: "Declined by card issuer",
    1102: "Invalid CVV2 code",
    1103: "Card expired",
    1104: "Insufficient funds",
    1105: "Invalid card number",
}


bot = Bot(token=settings.API_TOKEN)
dp = Dispatcher()
dp.include_router(handlers.router)

async def safe_polling():
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"Polling crashed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting bot setup...")
    await setup_commands(bot)
    # await bot.set_webhook(url=settings.WEBHOOK_URL)
    # logger.info(f"Webhook set to {settings.WEBHOOK_URL}")
    asyncio.create_task(periodic_subscription_check())
    asyncio.create_task(periodic_expiry_notify())
    asyncio.create_task(safe_polling())
    yield
    logger.info("Shutting down...")
    # await bot.delete_webhook()
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


# @app.post("/webhook")
# async def webhook(request: Request):
#     update_data = await request.json()
#     update = types.Update(**update_data)
#     await dp.feed_update(bot=bot, update=update)
#     return {"ok": True}


class WayForPayCallback(BaseModel):
    merchantAccount: str
    orderReference: str
    amount: float
    currency: str
    authCode: str | None = None
    cardPan: str | None = None
    transactionStatus: str
    reason: str | None = None
    reasonCode: int | None = None


async def add_user_to_group_and_send_invite(bot: Bot, user_id: int):
    try:
        await bot.unban_chat_member(settings.GROUP_CHAT_ID, user_id)
        logger.info(f"User {user_id} unbanned in group {settings.GROUP_CHAT_ID}")
    except Exception as e:
        logger.warning(f"Failed to unban user {user_id} in group: {e}")

    try:
        invite = await bot.create_chat_invite_link(
            settings.GROUP_CHAT_ID,
            member_limit=1,
            creates_join_request=False,
            expire_date=None,
        )
        await bot.send_message(
            user_id,
            "Ось ваша персональний інвайт до групи 👇",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="Приєднатися до групи", url=invite.invite_link
                        )
                    ]
                ]
            ),
        )
        logger.info(f"Invite link sent to user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to create/send invite link to user {user_id}: {e}")


@app.post("/payment/callback")
async def payment_callback(
    request: Request, session: AsyncSession = Depends(get_session)
):
    try:
        data = await request.json()
    except Exception:
        data = await request.body()
        logger.warning(f"Raw body received: {data}")
        return {"status": "error"}

    logger.info(f"Received payment callback: {data}")

    order_reference = data["orderReference"]
    parts = order_reference.split("_")
    user_id = int(parts[1])
    order_timestamp = int(parts[2])
    if len(parts) > 3:
        subscription_days = int(parts[3])
    else:
        subscription_days = 30

    now = datetime.utcfromtimestamp(order_timestamp)
    status = data.get("transactionStatus")
    reason_code = data.get("reasonCode")
    payment_id = order_reference

    response_status = "accept"
    response_time = int(time.time())
    signature = generate_wfp_signature(
        order_reference, response_status, response_time, settings.MERCHANT_SECRET_KEY
    )

    subscriber = await get_subscriber(session, user_id)
    username = subscriber.username if subscriber else ""

    if status == "Approved":
        if (
            subscriber
            and subscriber.subscription_end
            and subscriber.subscription_end > now
        ):
            new_subscription_end = subscriber.subscription_end + timedelta(
                days=subscription_days
            )
        else:
            new_subscription_end = now + timedelta(days=subscription_days)
        await update_subscriber_payment(
            session=session,
            telegram_id=user_id,
            username=username,
            subscription_type=subscription_days,
            payment_date=now,
            subscription_end=new_subscription_end,
            status=SubscriptionStatus.ACTIVE.value,
            payment_id=payment_id,
        )
        try:
            await bot.send_message(
                user_id,
                f"✅ Payment successful! Access to the channel is granted until {new_subscription_end.strftime('%d.%m.%Y %H:%M')}.",
            )
            await add_user_to_group_and_send_invite(bot, user_id)
        except Exception as e:
            logger.warning(f"Failed to send message to user {user_id}: {e}")

    else:
        await update_subscriber_declined(
            session=session,
            telegram_id=user_id,
            username=username,
            status=SubscriptionStatus.EXPIRED.value,
            payment_id=payment_id,
        )
        error_explanation = DECLINE_REASONS.get(reason_code, "Unknown error")
        try:
            await bot.send_message(
                user_id,
                f"❌ Payment failed: {error_explanation}",
            )
        except Exception as e:
            logger.warning(f"Failed to send message to user {user_id}: {e}")

    return {
        "orderReference": order_reference,
        "status": response_status,
        "time": response_time,
        "signature": signature,
    }


def generate_wfp_signature(
    order_reference: str, status: str, time_: int, secret_key: str
) -> str:
    import hashlib
    import hmac

    sign_string = f"{order_reference};{status};{time_}"
    return hmac.new(secret_key.encode(), sign_string.encode(), hashlib.md5).hexdigest()


async def notify_users_about_expiry(bot: Bot):
    """Notify users whose subscription expires in 24 hours."""
    async with get_session() as session:
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        result = await session.execute(
            select(Subscriber).where(
                Subscriber.subscription_end != None,  # noqa
                Subscriber.status == SubscriptionStatus.ACTIVE.value,
                Subscriber.subscription_end > now,
                Subscriber.subscription_end <= tomorrow,
            )
        )
        expiring_soon = result.scalars().all()
        for sub in expiring_soon:
            time_left = sub.subscription_end - now
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes = remainder // 60
            try:
                await bot.send_message(
                    sub.telegram_id,
                    f"⚠️ Ваша підписка закінчиться через {hours} год {minutes} хвилин.\n"
                    "Щоб не втратити доступ, продовжіть підписку!",
                )
                logger.info(f"Sent expiry notification to {sub.telegram_id}")
            except Exception as e:
                logger.warning(f"Failed to notify {sub.telegram_id}: {e}")


async def ban_expired_users(bot: Bot):
    """Ban users with expired subscriptions and notify them."""
    async with get_session() as session:
        now = datetime.utcnow()
        result = await session.execute(
            select(Subscriber).where(
                Subscriber.subscription_end != None,  # noqa
                Subscriber.subscription_end < now,
                Subscriber.status == SubscriptionStatus.ACTIVE.value,
            )
        )
        expired_subs = result.scalars().all()
        for sub in expired_subs:
            try:
                await bot.send_message(
                    sub.telegram_id,
                    "❌ Ваша підписка закінчилась. Доступ до групи закрито.",
                )
            except Exception as e:
                logger.warning(f"Failed to notify expired {sub.telegram_id}: {e}")
            try:
                await bot.ban_chat_member(settings.GROUP_CHAT_ID, sub.telegram_id)
                logger.info(f"Banned user {sub.telegram_id} from group")
            except Exception as e:
                logger.warning(f"Failed to ban user {sub.telegram_id}: {e}")
            sub.status = SubscriptionStatus.EXPIRED.value
        if expired_subs:
            await session.commit()


async def periodic_subscription_check():
    while True:
        try:
            logger.info("🔁 Checking for expired subscriptions...")
            await ban_expired_users(bot)
        except Exception as e:
            logger.exception(f"❌ Error in periodic_subscription_check: {e}")
        await asyncio.sleep(300)


async def periodic_expiry_notify():
    while True:
        try:
            logger.info("🔁 Checking for subscriptions expiring in 24h...")
            await notify_users_about_expiry(bot)
        except Exception as e:
            logger.exception(f"❌ Error in periodic_expiry_notify: {e}")
        await asyncio.sleep(86400)
