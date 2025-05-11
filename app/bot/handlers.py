from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.core.logger import logger
from app.payment.wayforpay import send_payment_link
from app.database.session import get_session
from app.database.crud import update_subscriber_payment

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


@router.message(Command("help"))
async def handle_help(message: Message):
    await message.answer(
        "Якщо у вас виникли питання, будь ласка, зверніться до адміністратора каналу...\n"
        "Скоро ми додамо функцію зворотного зв'язку, щоб ви могли отримати допомогу прямо тут. "
    )
    logger.info(f"User {message.from_user.full_name} requested help")


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
    username = query.from_user.username or ""
    async for session in get_session():
        await update_subscriber_payment(
            session=session,
            telegram_id=user_id,
            username=username,
            subscription_type=0,
            payment_date=None,
            subscription_end=None,
            status="expired",
            payment_id=None,
        )
        amount = 600
        await send_payment_link(query, user_id, amount)
