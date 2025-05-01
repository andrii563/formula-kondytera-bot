import os
from flask import Flask, request
from telegram import Bot

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("Webhook data:", data)

    try:
        if data.get("transactionStatus") == "Approved":
            user_id = int(data["orderReference"].split(":")[1])
            bot.unban_chat_member(chat_id=CHAT_ID, user_id=user_id, only_if_banned=True)
            bot.send_message(chat_id=user_id, text="Оплату підтверджено. Вас додано до чату.")
            bot.invite_link_create(chat_id=CHAT_ID)
            return "OK", 200
        else:
            return "Оплата не підтверджена", 400
    except Exception as e:
        print("Error:", e)
        return "Server error", 500

if __name__ == "__main__":
    app.run(debug=True)
