import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    API_TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    WEBAPP_HOST = os.getenv("HOST", "localhost")
    WEBAPP_PORT = int(os.getenv("PORT", 8000))
    MERCHANT_SECRET_KEY = os.getenv("MERCHANT_SECRET_KEY")
    MERCHANT_DOMAIN_NAME = os.getenv("MERCHANT_DOMAIN_NAME")
    PAYMENT_CALLBACK_URL = f"{WEBHOOK_URL.replace('/webhook', '/payment/callback')}"
    GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))
    DATABASE_URL = os.getenv("DATABASE_URL")


settings = Settings()
