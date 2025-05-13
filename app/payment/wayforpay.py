import hashlib
import hmac
import time
from dataclasses import dataclass

import aiohttp
from aiogram import types
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.config import settings


@dataclass
class PaymentConfig:
    merchant_account: str = "test_merch_n1"
    merchant_domain_name: str = settings.MERCHANT_DOMAIN_NAME
    currency: str = "UAH"
    product_name: str = "Subscription"


class WayForPayment:
    def __init__(self, merchant_secret_key: str):
        self.secret_key = merchant_secret_key
        self.config = PaymentConfig()

    def generate_signature(self, data: dict) -> str:
        sign_list = [
            data["merchantAccount"],
            data["merchantDomainName"],
            data["orderReference"],
            str(data["orderDate"]),
            str(data["amount"]),
            data["currency"],
            data["productName"][0],
            str(data["productCount"][0]),
            str(data["productPrice"][0]),
        ]
        sign_string = ";".join(sign_list)
        return hmac.new(
            self.secret_key.encode("utf-8"), sign_string.encode("utf-8"), hashlib.md5
        ).hexdigest()

    def generate_payment_url(self, user_id: int, amount: int, days: int) -> str:
        order_reference = f"order_{user_id}_{int(time.time())}_{days}"
        order_date = int(time.time())

        data = {
            "merchantAccount": self.config.merchant_account,
            "merchantDomainName": self.config.merchant_domain_name,
            "orderReference": order_reference,
            "orderDate": order_date,
            "amount": amount,
            "currency": self.config.currency,
            "productName": [self.config.product_name],
            "productCount": [1],
            "productPrice": [amount],
            "serviceUrl": settings.PAYMENT_CALLBACK_URL,
        }

        signature = self.generate_signature(data)
        data["merchantSignature"] = signature

        return "https://secure.wayforpay.com/pay", data


async def send_payment_link(query: types.CallbackQuery, user_id: int, amount: int, days: int):
    payment = WayForPayment(settings.MERCHANT_SECRET_KEY)
    form_url, data = payment.generate_payment_url(user_id, amount, days)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                form_url, data=data, allow_redirects=True
            ) as response:
                if response.status == 200:
                    payment_url = str(response.url)
                    await query.message.answer(
                        "🔐 Для оплати натисніть кнопку нижче\n"
                        "💳 Ви будете перенаправлені на безпечну сторінку оплати",
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text=f"💳 Оплатити підписку {amount} грн.", url=payment_url
                                    )
                                ]
                            ]
                        ),
                    )
                else:
                    await query.message.answer(f"❌ Помилка сервера: {response.status}")
    except aiohttp.ClientError as e:
        await query.message.answer(f"❌ Помилка при створенні платежу: {str(e)}")
    except TelegramAPIError as e:
        await query.message.answer(f"❌ Помилка Telegram API: {str(e)}")
