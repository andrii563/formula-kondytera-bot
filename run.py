import asyncio
from pathlib import Path

from hypercorn.asyncio import serve
from hypercorn.config import Config

from app.core.config import settings
from webhook import app

if __name__ == "__main__":
    config = Config()
    config.bind = [f"{settings.WEBAPP_HOST}:{settings.WEBAPP_PORT}"]
    config.use_reloader = True
    config.reload_dirs = [str(Path(__file__).parent)]
    config.worker_class = "asyncio"
    config.reload_delay = 0.25
    asyncio.run(serve(app, config))
