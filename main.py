from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODELLABS_API_KEY = os.getenv("MODELLABS_API_KEY")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Send text message
def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

# Send image/photo
def send_photo(chat_id, image_url):
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    payload = {"chat_id": chat_id, "photo": image_url}
    requests.post(url, json=payload)

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    logging.info("Received update: %s", data)

    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        if text.startswith("/start"):
            send_message(chat_id, "👋 Welcome to Aria Blaze Bot! Type anything to chat.\nUse /image to generate NSFW pics.")

        elif text.startswith("/help"):
            send_message(chat_id, "🤖 Commands:\n- Type anything for chat\n- `/image your prompt` to get NSFW images")

        elif text.startswith("/image"):
            prompt = text.replace("/image", "").strip()
            if not prompt:
                send_message(chat_id, "❗ Please provide a prompt. Example: `/image a fantasy elf girl`")
                return jsonify(success=True)

            send_message(chat_id, "🎨 Generating your NSFW image... please wait 20–40 seconds.")

            try:
                headers = {
                    "Authorization": f"Bearer {MODELLABS_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "prompt": prompt,
                    "model": "realistic-vision",  # you can change to other ModelLabs models
                    "negative_prompt": "bad anatomy, disfigured",
                    "width": 512,
                    "height": 768,
                    "steps": 30
                }

                response = requests.post("https://api.modellabs.ai/v1/generate", json=payload, headers=headers)
                result = response.json()
                logging.info("ModelLabs response: %s", result)

                image_url = result.get("data", {}).get("image_url") or result.get("image_url")
                if image_url:
                    send_photo(chat_id, image_url)
                else:
                    send_message(chat_id, "❌ Failed to generate image. Try again later.")
            except Exception as e:
                logging.error("ModelLabs error: %s", e)
                send_message(chat_id, "⚠️ Something went wrong while generating the image.")

        else:
            # Default AI Chat
            try:
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "openrouter/llama3-8b-instruct",
                    "messages": [{"role": "user", "content": text}],
                    "temperature": 0.7
                }
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
                result = response.json()
                reply = result["choices"][0]["message"]["content"]
                send_message(chat_id, reply)

            except Exception as e:
                logging.error("OpenRouter error: %s", e)
                send_message(chat_id, "⚠️ Failed to generate reply.")

    return jsonify(success=True)

@app.route("/", methods=["GET"])
def index():
    return "🤖 Aria Blaze Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)




