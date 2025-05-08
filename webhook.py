from aiogram import Bot, Dispatcher, types
from fastapi import FastAPI, Request

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
    update_data = await request.json()
    update = types.Update(**update_data)
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}
