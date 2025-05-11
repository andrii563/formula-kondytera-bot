import time
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from fastapi import FastAPI, Request, Depends
from contextlib import asynccontextmanager
from pydantic import BaseModel

from app.bot import handlers
from app.bot.commands import setup_commands
from app.core.config import settings
from app.core.logger import logger
from app.database.models import SubscriptionStatus
from app.database.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.crud import (
    update_subscriber_payment,
    update_subscriber_declined,
    get_subscriber,
)

# Error code explanations for declined payments
DECLINE_REASONS = {
    1101: "Declined by card issuer",
    1102: "Invalid CVV2 code",
    1103: "Card expired",
    1104: "Insufficient funds",
    1105: "Invalid card number",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting bot setup...")
    await setup_commands(bot)
    await bot.set_webhook(url=settings.WEBHOOK_URL)
    logger.info(f"Webhook set to {settings.WEBHOOK_URL}")
    yield
    # Shutdown logic
    logger.info("Shutting down...")
    await bot.delete_webhook()
    await bot.session.close()


app = FastAPI(lifespan=lifespan)

bot = Bot(token=settings.API_TOKEN)
dp = Dispatcher()

dp.include_router(handlers.router)


@app.post("/webhook")
async def webhook(request: Request):
    """Handle Telegram webhook updates"""
    update_data = await request.json()
    update = types.Update(**update_data)
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}


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
    user_id = int(order_reference.split("_")[1])
    order_timestamp = int(order_reference.split("_")[2])
    status = data.get("transactionStatus")
    reason_code = data.get("reasonCode")
    payment_id = order_reference
    now = datetime.fromtimestamp(order_timestamp)

    # Prepare response for WayForPay
    response_status = "accept"
    response_time = int(time.time())
    signature = generate_wfp_signature(
        order_reference, response_status, response_time, settings.MERCHANT_SECRET_KEY
    )

    subscriber = await get_subscriber(session, user_id)
    username = subscriber.username if subscriber else ""

    if status == "Approved":
        subscription_end = now + timedelta(days=30)
        await update_subscriber_payment(
            session=session,
            telegram_id=user_id,
            username=username,
            subscription_type=30,
            payment_date=now,
            subscription_end=subscription_end,
            status=SubscriptionStatus.ACTIVE.value,
            payment_id=payment_id,
        )
        try:
            await bot.send_message(
                user_id,
                "✅ Payment successful! Access to the channel is granted for 30 days.",
            )
        except Exception as e:
            logger.warning(f"Failed to send message to user {user_id}: {e}")

    elif status == "Declined" and reason_code == 1122:
        # Test payment
        subscription_end = now + timedelta(minutes=5)
        await update_subscriber_payment(
            session=session,
            telegram_id=user_id,
            username=username,
            subscription_type=0,
            payment_date=now,
            subscription_end=subscription_end,
            status=SubscriptionStatus.ACTIVE.value,
            payment_id=payment_id,
        )
        try:
            await bot.send_message(
                user_id,
                "🧪 Test Pay Successfully! Access granted for 5 minutes.",
            )
        except Exception as e:
            logger.warning(f"Failed to send message to user {user_id}: {e}")

    else:
        # Any other declined payment
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

    # Always return confirmation to WayForPay
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
