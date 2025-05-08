import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config
from app.core.config import settings
from webhook import app

if __name__ == "__main__":
    config = Config()
    config.bind = [f"{settings.WEBAPP_HOST}:{settings.WEBAPP_PORT}"]
    asyncio.run(serve(app, config))