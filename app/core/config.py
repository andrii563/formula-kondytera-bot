import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    API_TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = "https://8c98-91-203-143-82.ngrok-free.app/webhook"
    WEBAPP_HOST = "localhost"
    WEBAPP_PORT = 8000


settings = Settings()
