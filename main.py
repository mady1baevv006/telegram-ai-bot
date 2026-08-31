import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT")

@app.route("/", methods=["GET"])
def home():
    return "AI Bot Server is Running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return jsonify({"status": "ok"}), 200

    # Проверяем обычное сообщение или бизнес-сообщение Telegram Business
    message = None
    business_connection_id = None

    if "business_message" in data:
        message = data["business_message"]
        business_connection_id = message.get("business_connection_id")
    elif "message" in data:
        message = data["message"]

    if not message:
        return jsonify({"status": "ok"}), 200

    chat_id = message["chat"]["id"]
    user_text = message.get("text", "")

    if not user_text:
        return jsonify({"status": "ok"}), 200

    # Запрос к OpenAI API
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        res_data = response.json()
        ai_reply = res_data["choices"][0]["message"]["content"]

        # Формируем ответ для Telegram
        reply_payload = {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": ai_reply
        }
        
        if business_connection_id:
            reply_payload["business_connection_id"] = business_connection_id

        return jsonify(reply_payload), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
