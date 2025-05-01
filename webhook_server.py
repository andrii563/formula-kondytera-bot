import os
import json
from flask import Flask, request
import telegram

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")  # наприклад: -1002635000565

bot = telegram.Bot(token=BOT_TOKEN)

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("Отримано webhook:", data)

    try:
        # Перевірка статусу оплати
        if data.get("transactionStatus") == "Approved":
            user_id = int(data["orderReference"].split(":")[1])  # orderReference = "subscription:USER_ID"
            bot.unban_chat_member(chat_id=CHAT_ID, user_id=user_id, only_if_banned=True)
            bot.invite_link_create(chat_id=CHAT_ID)  # для публічних чатів можна генерувати інвайт
            return "OK", 200
        else:
            return "Оплата не підтверджена", 400
    except Exception as e:
        print("Помилка:", e)
        return "Помилка сервера", 500

if __name__ == "__main__":
    app.run()
