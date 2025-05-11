from aiogram import Bot, Dispatcher, types
from fastapi import FastAPI, Request
from aiogram.exceptions import TelegramBadRequest
from pydantic import BaseModel

from app.bot import handlers
from app.bot.commands import setup_commands
from app.core.config import settings
from app.core.logger import logger

app = FastAPI()

bot = Bot(token=settings.API_TOKEN)
dp = Dispatcher()

dp.include_router(handlers.router)


@app.on_event("startup")
async def on_startup():
    logger.info("Starting bot setup...")
    await setup_commands(bot)
    await bot.set_webhook(url=settings.WEBHOOK_URL)
    logger.info(f"Webhook set to {settings.WEBHOOK_URL}")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down...")
    await bot.delete_webhook()
    await bot.session.close()


@app.post("/webhook")
async def webhook(request: Request):
    """Обработка webhook от Telegram"""
    update_data = await request.json()
    update = types.Update(**update_data)
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}


# Модель для данных от WayForPay
class WayForPayCallback(BaseModel):
    merchantAccount: str
    orderReference: str
    amount: float
    currency: str
    authCode: str | None = None
    cardPan: str | None = None
    transactionStatus: str
    reasonCode: int | None = None

@app.post("/payment/callback")
async def payment_callback(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = await request.body()  # если ни JSON, ни form — просто сырой байтовый дамп
        logger.warning(f"Raw body received: {data}")
        return {"status": "error"}

    logger.info(f"Received payment callback: {data}")
    
    order_reference = data["orderReference"]  # например, "order_585406658_1746735052"
    user_id = int(order_reference.split("_")[1])
    status = data.get("transactionStatus")

    if status == "Approved":
        # Здесь логика: отметить в БД, что платеж прошёл
        logger.info(f"Payment approved for user {user_id}")
        # ...обновить подписку...
        return {"status": "accept"}
    else:
        logger.info(f"Payment not approved (status: {status}) for user {user_id}")
        # Можно вернуть error или accept, но повторные уведомления будут до успешной обработки
        return {"status": "accept"}
