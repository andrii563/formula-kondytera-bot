import os
from flask import Flask, request
import telegram

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")  # Формат: -1002635000565

bot = telegram.Bot(token=BOT_TOKEN)

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("Received webhook:", data)

    try:
        # Перевірка статусу оплати
        if data.get("transactionStatus") == "Approved":
            order_ref = data.get("orderReference", "")
            if ":" in order_ref:
                user_id = int(order_ref.split(":")[1])
                bot.unban_chat_member(chat_id=CHAT_ID, user_id=user_id, only_if_banned=True)
                bot.send_message(chat_id=user_id, text="Оплату підтверджено! Ви додані до чату.")
                return "OK", 200
            else:
                return "Invalid orderReference format", 400

        elif data.get("transactionStatus") == "Expired":
            order_ref = data.get("orderReference", "")
            if ":" in order_ref:
                user_id = int(order_ref.split(":")[1])
                bot.kick_chat_member(chat_id=CHAT_ID, user_id=user_id)
                return "Subscription expired, user removed", 200
            else:
                return "Invalid orderReference format", 400

        else:
            return "Unhandled status", 200

    except Exception as e:
        print("Error:", e)
        return "Server error", 500

if __name__ == "__main__":
    app.run()
