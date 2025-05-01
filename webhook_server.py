import os
import json
from flask import Flask, request
import telegram

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID"))

bot = telegram.Bot(token=BOT_TOKEN)

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("Отримано webhook:", data)

    try:
        if data.get("transactionStatus") == "Approved":
            order_ref = data.get("orderReference", "")
            if ":" not in order_ref:
                return "Невірний формат orderReference", 400

            user_id = int(order_ref.split(":")[1])
            bot.unban_chat_member(chat_id=CHAT_ID, user_id=user_id, only_if_banned=True)
            return "OK", 200
        else:
            return "Оплата не підтверджена", 400
    except Exception as e:
        print("Помилка:", e)
        return "Помилка сервера", 500

if __name__ == "__main__":
    app.run()
