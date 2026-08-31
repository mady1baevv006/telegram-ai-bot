import os
import requests
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Инициализируем клиент Google Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

@app.route("/", methods=["GET"])
def home():
    return "AI Bot Server with Gemini is Running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return jsonify({"status": "ok"}), 200

    message = None
    business_connection_id = None

    if "business_message" in data:
        message = data["business_message"]
        business_connection_id = message.get("business_connection_id")
    elif "message" in data:
        message = data["message"]

    if not message:
        return jsonify({"status": "ok"}), 200

    if message.get("from", {}).get("is_bot", False):
        return jsonify({"status": "ok"}), 200

    chat_id = message["chat"]["id"]
    user_text = message.get("text", "")

    if not user_text:
        return jsonify({"status": "ok"}), 200

    try:
        # Запрос к Google Gemini 2.5 Flash с системным промптом
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.7
            }
        )

        ai_reply = response.text

        # Отправка ответа в Telegram
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        tg_payload = {
            "chat_id": chat_id,
            "text": ai_reply
        }
        
        if business_connection_id:
            tg_payload["business_connection_id"] = business_connection_id

        requests.post(tg_url, json=tg_payload)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("Gemini Error:", e)
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
