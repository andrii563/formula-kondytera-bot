from flask import Flask, request, jsonify
import os
import hmac
import hashlib
import base64
app = Flask(__name__)
@app.route("/wayforpay", methods=["POST"])
def wayforpay_webhook():
    data = request.json
  signature_base = ";".join([
        data["merchantAccount"],
        data["orderReference"],
        str(data["amount"]),
        data["currency"],
        data["authCode"],
        str(data["cardPan"]),
       str(data["transactionStatus"]),
        str(data["reason"]),
        str(data["reasonCode"])
    ])
secret = os.getenv("WAYFORPAY_SECRET_KEY")
    generated_signature = base64.b64encode(
        hmac.new(secret.encode(), signature_base.encode(), hashlib.md5).digest()
    ).decode()
if data.get("merchantSignature") != generated_signature:
        return jsonify({"reason": "Invalid signature"}), 403
      if data.get("transactionStatus") == "Approved":
        print("Оплата успішна для:", data.get("orderReference"))
        # Тут можна вставити логіку додавання користувача в чат
            return jsonify({"orderReference": data["orderReference"], "status": "accept"})
