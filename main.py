import os
import requests
import logging
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

def send_message(chat_id, text):
    logging.info(f"Sending message to {chat_id}: {text}")
    requests.post(f"{BOT_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

def send_photo(chat_id, image_url):
    logging.info(f"Sending photo to {chat_id}: {image_url}")
    requests.post(f"{BOT_URL}/sendPhoto", json={
        "chat_id": chat_id,
        "photo": image_url
    })

@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        logging.info(f"Received POST data: {data}")

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            logging.info(f"Chat ID: {chat_id}, Text: {text}")

            if text.startswith("/image"):
                prompt = text.replace("/image", "").strip()
                if not prompt:
                    send_message(chat_id, "Please provide a prompt. Example:\n/image a naked elf warrior with red hair")
                    return "ok"

                send_message(chat_id, "🎨 Generating your NSFW image... please wait 20–40 seconds.")

                try:
                    # Hugging Face NSFW SD 1.5 endpoint (no auth needed)
                    hf_url = "https://stablediffusionapi.com/api/v3/text2img"

                    payload = {
                        "prompt": prompt,
                        "negative_prompt": "blurry, low quality, watermark, text, cropped",
                        "width": "512",
                        "height": "768",
                        "samples": "1",
                        "num_inference_steps": "30",
                        "guidance_scale": 7.5,
                        "safety_checker": "no",
                        "enhance_prompt": "yes",
                        "seed": None,
                        "webhook": None,
                        "track_id": None
                    }

                    response = requests.post(hf_url, json=payload)
                    result = response.json()
                    logging.info(f"Image generation API response: {result}")

                    if "output" in result and len(result["output"]) > 0:
                        image_url = result["output"][0]
                        send_photo(chat_id, image_url)
                    else:
                        send_message(chat_id, "❌ Failed to generate image. Try again later.")

                except Exception as e:
                    logging.error(f"Error generating image: {e}", exc_info=True)
                    send_message(chat_id, f"⚠️ Error generating image: {str(e)}")

            else:
                # Echo back the received text for testing
                send_message(chat_id, f"Got your message: {text}")

        else:
            logging.info("No message found in update.")

    except Exception as e:
        logging.error(f"Exception in webhook: {e}", exc_info=True)

    return "ok"



