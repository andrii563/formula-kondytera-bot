import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "webhook:app", host=settings.WEBAPP_HOST, port=settings.WEBAPP_PORT, reload=True
    )
