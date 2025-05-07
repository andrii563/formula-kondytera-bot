from aiogram import Router, types
from aiogram.filters import CommandStart

from app.core.logger import logger

router = Router()


@router.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer("Hello! I'm your bot. How can I assist you today?")
    logger.info(f"User {message.from_user.id} started the bot")


@router.message()
async def handle_message(message: types.Message):
    logger.info(f"Received message: {message.text}")
    await message.answer("Message received")
