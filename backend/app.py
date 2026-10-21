import os
import re
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError

app = Flask(__name__)

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://mongo:27017/cloudshield"
)

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = client["cloudshield"]

@app.get("/health")
def health():
    return jsonify({"status": "healthy", "service": "CloudShield API"}), 200

@app.post("/api/messages")
def create_message():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    message = data.get("message")

    if not isinstance(message, str):
        return jsonify({"error": "Message must be text"}), 400

    message = message.strip()

    if not message or len(message) > 200:
        return jsonify({"error": "Message must contain 1–200 characters"}), 400

    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", message):
        return jsonify({"error": "Message contains invalid characters"}), 400

    try:
        result = db.messages.insert_one({"message": message})
        return jsonify({
            "status": "saved",
            "id": str(result.inserted_id)
        }), 201
    except PyMongoError:
        app.logger.exception("Database operation failed")
        return jsonify({"error": "Database temporarily unavailable"}), 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
