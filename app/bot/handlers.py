from aiogram import F, Router, Bot
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    ChatJoinRequest,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.core.logger import logger
from app.core.config import settings
from app.payment.wayforpay import send_payment_link
from app.database.session import get_session
from app.database.crud import update_subscriber_payment, get_subscriber
from app.database.models import SubscriptionStatus

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message):
    if message.chat.type != "private":
        await reply_private_only(message)
        return
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
                        text="Підписка на місяць", callback_data="payment_30"
                    ),
                ]
            ]
        ),
    )
    logger.info(f"User {message.from_user.full_name} started the bot")


@router.message(Command("help"))
async def handle_help(message: Message):
    if message.chat.type != "private":
        await reply_private_only(message)
        return
    await message.answer(
        "Якщо у вас виникли питання, будь ласка, зверніться до адміністратора каналу...\n"
        "Скоро ми додамо функцію зворотного зв'язку, щоб ви могли отримати допомогу прямо тут. "
    )
    logger.info(f"User {message.from_user.full_name} requested help")


@router.message(Command("link"))
async def handle_link_command(message: Message, bot: Bot):
    if message.chat.type != "private":
        await message.reply(
            "Ця команда доступна лише в особистих повідомленнях з ботом."
        )
        return

    async for session in get_session():
        subscriber = await get_subscriber(session, message.from_user.id)
        if not subscriber or subscriber.status != SubscriptionStatus.ACTIVE.value:
            await message.answer("У вас немає активної підписки.")
            logger.info(
                f"User {message.from_user.id} try get link without subscription"
            )
            return

        try:
            invite = await bot.create_chat_invite_link(
                settings.GROUP_CHAT_ID,
                creates_join_request=True,
                expire_date=None,
            )
            await message.answer(
                "Ось ваш персональний інвайт до групи 👇",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Приєднатися до групи", url=invite.invite_link
                            )
                        ]
                    ]
                ),
            )
            logger.info(f"User {message.from_user.id} get invite link")
        except Exception as e:
            await message.answer("Не вдалося створити інвайт. Спробуйте пізніше.")
            logger.error(f"Error in creation invite link {message.from_user.id}: {e}")


@router.chat_join_request()
async def handle_join_request(event: ChatJoinRequest):
    user_id = event.from_user.id
    chat_id = event.chat.id

    async for session in get_session():
        subscriber = await get_subscriber(session, user_id)
        if subscriber and subscriber.status == "active":
            await event.bot.approve_chat_join_request(chat_id, user_id)
        else:
            await event.bot.decline_chat_join_request(chat_id, user_id)


@router.callback_query(F.data.startswith("payment_"))
async def handle_payment(query: CallbackQuery):
    if query.message.chat.type != "private":
        return
    user_id = query.from_user.id
    username = query.from_user.username or ""

    try:
        subscription_days = int(query.data.split("_")[1])
    except (IndexError, ValueError):
        await query.message.answer("Невірний формат підписки.")
        return

    prices = {7: 200, 14: 350, 30: 600}
    amount = prices.get(subscription_days)
    if not amount:
        await query.message.answer("Невідомий термін підписки.")
        return

    async for session in get_session():
        subscriber = await get_subscriber(session, user_id)
        if not subscriber:
            await update_subscriber_payment(
                session=session,
                telegram_id=user_id,
                username=username,
                subscription_type=subscription_days,
                payment_date=None,
                subscription_end=None,
                status="expired",
                payment_id=None,
            )
        else:
            if subscriber.username != username:
                subscriber.username = username
                await session.commit()
        await send_payment_link(query, user_id, amount, subscription_days)


async def reply_private_only(message: Message):
    await message.reply(
        "Краще викликати цю команду в особистому чаті з ботом -> @Formula_Kondytora_Bot"
    )


@router.message()
async def handle_message(message: Message):
    if message.chat.type != "private":
        return
    logger.info(f"Received message: {message.text}")
    await message.answer(
        "Скористуйтеся вбудованим меня,\nАбо використайте команду /start",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Почати", callback_data="start")]
            ]
        ),
    )
