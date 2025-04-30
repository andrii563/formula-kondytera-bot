import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_handler(message: Message):
    await message.answer("Вітаю у Формулі Кондитера! Ваш бот працює.")

@dp.message_handler(commands=["pay"])
async def pay_handler(message: Message):
    link = generate_payment_link(
        order_reference=f"INV{message.from_user.id}{int(message.date.timestamp())}",
        amount=100,
        email="example@email.com"
    )
    await message.answer(f"Для оплати підписки натисни:\n{link}")

def generate_payment_link(order_reference, amount, email):
    base_url = "https://secure.wayforpay.com/pay"
    merchant = os.getenv("WAYFORPAY_MERCHANT_ACCOUNT")
    
    params = f"?merchantAccount={merchant}&orderReference={order_reference}&amount={amount}&currency=UAH&productName=Підписка&productCount=1&productPrice={amount}&clientEmail={email}"
    return base_url + params

if __name__ == "__main__":
    executor.start_polling(dp)
