import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

@app.route("/", methods=["GET"])
def home():
    return "AI Bot Server is Running!", 200

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

    # Прямой запрос к Google Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": [
            {
                "parts": [{"text": user_text}]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload)
        res_data = response.json()

        if "error" in res_data:
            print("Gemini Error Details:", res_data["error"])
            return jsonify({"status": "error"}), 200

        ai_reply = res_data["candidates"][0]["content"]["parts"][0]["text"]

        # Отправка в Telegram
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
        print("General Error:", e)
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
