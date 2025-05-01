import os
from flask import Flask, request
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # приклад: -1002635000565

def add_user(user_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/inviteChatMember"
    data = {
        "chat_id": CHAT_ID,
        "user_id": user_id
    }
    response = requests.post(url, json=data)
    return response.ok

def remove_user(user_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/banChatMember"
    data = {
        "chat_id": CHAT_ID,
        "user_id": user_id
    }
    requests.post(url, json=data)

    # одразу розбанити — просто для видалення
    url_unban = f"https://api.telegram.org/bot{BOT_TOKEN}/unbanChatMember"
    requests.post(url_unban, json=data)

@app.route("/", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    print("Отримано webhook:", data)

    if data and data.get("reasonCode") == "1100":
        # оплата успішна
        user_id = int(data["orderReference"].split("_")[1])
        add_user(user_id)
        return "User added", 200

    if data and data.get("event") == "expire":
        user_id = int(data["orderReference"].split("_")[1])
        remove_user(user_id)
        return "User removed", 200

    return "Ignored", 200

@app.route("/", methods=["GET"])
def health_check():
    return "OK", 200
