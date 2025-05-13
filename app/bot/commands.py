from aiogram.types import BotCommand

from app.core.logger import logger


async def setup_commands(bot):
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Help"),
        BotCommand(command="link", description="Get new invite link"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands set up")
