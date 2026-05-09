import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx

from app.config import settings
from app.database.mongodb import connect_db, close_db
from app.handlers.webhook_handler import handle_update

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting up...")
    await connect_db()
    await setup_webhook()
    yield
    logger.info("🛑 Shutting down...")
    await close_db()


app = FastAPI(title="Telegram AI Bot", version="1.0.0", lifespan=lifespan)


async def setup_webhook():
    webhook_url = f"{settings.BASE_URL}/webhook/{settings.WEBHOOK_SECRET}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook",
                json={"url": webhook_url, "drop_pending_updates": True}
            )
            data = r.json()
            if data.get("ok"):
                logger.info(f"✅ Webhook registered: {webhook_url}")
            else:
                logger.error(f"❌ Webhook failed: {data}")
    except Exception as e:
        logger.error(f"❌ Webhook setup error: {e}")


@app.get("/health")
async def health():
    return {"status": "ok", "bot": settings.BOT_NAME}


@app.post("/webhook/{secret}")
async def webhook(secret: str, request: Request):
    if secret != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    update = await request.json()
    await handle_update(update)
    return JSONResponse({"ok": True})
