from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message,
)

from app.core.logger import logger
from app.payment.wayforpay import send_payment_link

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message):
    await message.answer(
        "Привіт! Я — бот клубу Формула Кондитера. 🎂🍰\n\n"
        "Тут ти знайдеш:\n"
        "- Ексклюзивні майстер-класи 🎨🍫\n"
        "- Поради від шефів 👩‍🍳👨‍🍳\n"
        "- Підтримку та спілкування з іншими кондитерами 💬🍪\n\n"
        "Ти можеш отримати доступ до нашого каналу натиснувши на кнопку нижче. 👇\n\n"
        "Ціна: 600 / 1 місяць 💵",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Перейти до сплати", callback_data="payment"
                    )
                ]
            ]
        ),
    )
    logger.info(f"User {message.from_user.full_name} started the bot")


@router.callback_query(F.data == "join_channel")
async def join_channel(query: CallbackQuery):
    logger.info(f"Callback from {query.from_user.full_name}: {query.data}")
    await query.answer("Дякуємо за реєстрацію!", show_alert=True)


@router.message()
async def handle_message(message: Message):
    logger.info(f"Received message: {message.text}")
    await message.answer(
        "Скористуйтеся вбудованим меня,\nАбо використайте команду /start",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Почати", callback_data="start")]
            ]
        ),
    )


@router.callback_query(F.data == "payment")
async def handle_payment(query: CallbackQuery):
    user_id = query.from_user.id
    amount = 600
    await send_payment_link(query, user_id, amount)
