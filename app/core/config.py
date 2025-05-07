import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    API_TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    WEBAPP_HOST = os.getenv("HOST", "localhost")
    WEBAPP_PORT = int(os.getenv("PORT", 8000))


settings = Settings()
