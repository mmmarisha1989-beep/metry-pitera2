from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import base64
import json

app = Flask(__name__)
CORS(app)

CHAT_ID = -74435268265279
API_BASE = "https://platform-api.max.ru"

@app.route("/publish", methods=["POST"])
def publish():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "invalid json"}), 400

    token = data.get("token", "").strip()
    text = data.get("text", "").strip()
    btn_text = data.get("btn_text", "Написать нам")
    image_b64 = data.get("image")
    image_type = data.get("image_type", "image/jpeg")

    if not token or not text:
        return jsonify({"error": "missing token or text"}), 400

    auth_headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }

    attachments = []

    if image_b64:
        try:
            image_bytes = base64.b64decode(image_b64)
            upload_res = requests.post(
                f"{API_BASE}/uploads?type=photo",
                headers={
                    "Authorization": token,
                    "Content-Type": image_type
                },
                data=image_bytes,
                timeout=15
            )
            print(f"Upload status: {upload_res.status_code}, body: {upload_res.text}")
            if upload_res.status_code == 200:
                photos = upload_res.json().get("photos", {})
                for key, val in photos.items():
                    photo_token = val.get("token")
                    if photo_token:
                        attachments.append({
                            "type": "image",
                            "payload": {"token": photo_token}
                        })
                    break
        except Exception as e:
            print(f"Image upload error: {e}")

    attachments.append({
        "type": "inline_keyboard",
        "payload": {
            "buttons": [[{
                "text": "👉 " + btn_text,
                "url": "https://t.me/MetryPiteraBot"
            }]]
        }
    })

    payload = {"text": text, "attachments": attachments}
    body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    send_headers = {
        "Authorization": token,
        "Content-Type": "application/json; charset=utf-8"
    }

    res = requests.post(
        f"{API_BASE}/messages?chat_id={CHAT_ID}",
        data=body_bytes,
        headers=send_headers,
        timeout=15
    )

    print(f"MAX API status: {res.status_code}, response: {res.text}")

    try:
        return jsonify(res.json()), res.status_code
    except Exception:
        return jsonify({"raw": res.text}), res.status_code


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "2.0"}), 200


@app.route("/")
def index():
    return "MAX Proxy Server v2.0 — OK", 200


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
