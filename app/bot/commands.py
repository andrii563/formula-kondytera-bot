from aiogram import types

from app.core.logger import logger


async def setup_commands(bot):
    commands = [
        types.BotCommand(command="start", description="Start the bot"),
        types.BotCommand(command="help", description="Help"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands set up")
