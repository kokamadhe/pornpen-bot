import os
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

app = Flask(__name__)

def send_message(chat_id, text):
    url = f"{BOT_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

def send_photo(chat_id, image_url):
    url = f"{BOT_URL}/sendPhoto"
    payload = {"chat_id": chat_id, "photo": image_url}
    requests.post(url, json=payload)

# Generate image with selected model
def generate_image(prompt, model):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/images/generate",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://yourdomain.com"
            },
            json={
                "prompt": prompt,
                "model": model,
                "n": 1,
                "size": "512x512"
            }
        )
        data = response.json()
        if "data" in data:
            return data["data"][0]["url"]
    except Exception as e:
        print("Error:", e)
    return None

@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()
    print("Incoming update:", update)

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if text.startswith("/image_"):
            parts = text.split(" ", 1)
            command = parts[0]
            prompt = parts[1] if len(parts) > 1 else ""

            model_map = {
                "/image_nsfw": "openai/o4-nsfw",       # NSFW photorealistic
                "/image_anime": "gruenberg-anime",     # NSFW anime-style
                "/image_real": "realvis",              # Realistic SFW
                "/image_safe": "stability/stable-diffusion-xl"  # Clean SFW
            }

            model = model_map.get(command)

            if not prompt:
                send_message(chat_id, f"⚠️ Please add a prompt after {command}.")
                return "ok"

            send_message(chat_id, f"🧠 Generating image with `{command[7:]}` model... Please wait.")
            image_url = generate_image(prompt, model)

            if image_url:
                send_photo(chat_id, image_url)
            else:
                send_message(chat_id, "❌ Failed to generate image. Try again later.")

        else:
            send_message(chat_id, f"💬 You said: {text}")

    return "ok"

if __name__ == "__main__":
    app.run()






