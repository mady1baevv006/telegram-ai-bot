import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama-3.3-70b-versatile")

# Запоминаем, кому уже отправляли предупреждение "я ИИ-ассистент".
# Хранится только в памяти сервера, поэтому после перезапуска сервиса
# на Render (например, после обновления кода) список обнулится и
# предупреждение придёт заново одному и тому же человеку один раз.
greeted_chats = set()
AI_DISCLAIMER = "Здравствуйте! Я ИИ-ассистент, помогаю отвечать на вопросы по курсам. 🙂\n\n"


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

    # Запрос к Groq (OpenAI-совместимый формат)
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res_data = response.json()

        if "error" in res_data:
            print("Groq Error Details:", res_data["error"])
            return jsonify({"status": "error"}), 200

        ai_reply = res_data["choices"][0]["message"]["content"]

        if chat_id not in greeted_chats:
            ai_reply = AI_DISCLAIMER + ai_reply
            greeted_chats.add(chat_id)

        # Отправка ответа в Telegram
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        tg_payload = {
            "chat_id": chat_id,
            "text": ai_reply,
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
