import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import storage

app = Flask(__name__)
CORS(app)  # ✅ Enable CORS for external access (Framer, browsers, etc.)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.route("/")
def home():
    return jsonify({"message": "Flask is running on Cloud Run!"})

# ✅ Generate a Signed URL for Uploading Files
@app.route("/upload", methods=["OPTIONS", "POST"])
def upload():
    """Handles file uploads and generates a signed URL."""
    if request.method == "OPTIONS":
        return '', 204  # ✅ Handle preflight requests

    try:
        data = request.get_json()
        if not data or "file_name" not in data:
            return jsonify({"error": "Missing 'file_name' in request"}), 400

        bucket_name = "construction_ai"  # 🔹 Your Cloud Storage bucket name
        file_name = data["file_name"]

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)

        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=3600,  # URL expires in 1 hour
            method="PUT",
        )

        return jsonify({"signed_url": signed_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Generate a Signed URL for Downloading Files
@app.route("/download", methods=["OPTIONS", "POST"])
def download():
    """Generates a signed URL to access a file."""
    if request.method == "OPTIONS":
        return '', 204  # ✅ Handle preflight requests

    try:
        data = request.get_json()
        if not data or "file_name" not in data:
            return jsonify({"error": "Missing 'file_name' in request"}), 400

        bucket_name = "construction_ai"  # 🔹 Your Cloud Storage bucket name
        file_name = data["file_name"]

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)

        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=3600,  # URL expires in 1 hour
            method="GET",  # ✅ This is for downloading
        )

        return jsonify({"signed_url": signed_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  
    app.run(host="0.0.0.0", port=port)