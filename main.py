import os
import logging
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_IMAGE_MODEL = "stabilityai/sdxl"  # or pick another below

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_telegram_message(chat_id, text):
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

def send_telegram_photo(chat_id, image_url, caption=None):
    requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json={
        "chat_id": chat_id,
        "photo": image_url,
        "caption": caption or ""
    })

def generate_image(prompt):
    url = "https://openrouter.ai/api/v1/images/generate"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": OPENROUTER_IMAGE_MODEL,
        "prompt": prompt,
        "nsfw": True
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        logging.info(f"Image generation API response: {response.json()}")
        image_url = response.json().get("image_url")
        return image_url
    except Exception as e:
        logging.error(f"Image generation failed: {e}")
        return None

@app.route("/", methods=["POST"])
def handle_webhook():
    data = request.json
    logging.info(f"Received POST data: {data}")

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        logging.info(f"Chat ID: {chat_id}, Text: {text}")

        if text.startswith("/image"):
            prompt = text.replace("/image", "").strip()
            if not prompt:
                send_telegram_message(chat_id, "Please provide a prompt, e.g. /image cyberpunk girl")
                return "ok"

            send_telegram_message(chat_id, "🎨 Generating your image... please wait 20–40 seconds.")
            image_url = generate_image(prompt)

            if image_url:
                send_telegram_photo(chat_id, image_url, caption=f"🖼️ Prompt: {prompt}")
            else:
                send_telegram_message(chat_id, "❌ Failed to generate image. Try again later.")

        else:
            send_telegram_message(chat_id, f"Got your message: {text}")

    return "ok"





