from fastapi import FastAPI, HTTPException, Request
import requests
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import hmac

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
GHOST_HOOK_SECRET = os.getenv("GHOST_HOOK_SECRET")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        # Print all headers
        headers = request.headers
        req_payload = await request.body()
        sha256 = hmac.new(
            GHOST_HOOK_SECRET.encode("utf-8"), req_payload, hashlib.sha256
        ).hexdigest()
        # Check authorization 
        if headers.get("x-ghost-signature").split(", ")[0] != f"sha256={sha256}":
            raise HTTPException(status_code=403, detail="Forbidden")

        data = await request.json()
        # Don't alert when partner page is published.
        if any(
            tag["name"] in ["#partnerpage", "#mainpartnerpage"]
            for tag in data["post"]["current"]["tags"]
        ):
            return {"message": "Partner pages do not alert TG Bot"}
        url_to_post = data["post"]["current"]["url"]

        if not url_to_post:
            return {"error": "No URL provided"}

        # Prepare payload for sending a message to the Telegram channel
        payload = {
            "chat_id": CHANNEL_ID,
            "text": url_to_post,
        }

        # Send message to Telegram
        response = requests.post(TELEGRAM_API_URL, json=payload)

        if response.status_code != 200:
            return {"error": "Failed to send message to Telegram"}

        return {"message": "URL posted successfully"}
    except Exception as e:
        print(e)
        return {"error": str(e)}
