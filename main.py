import os
from flask import Flask, request, jsonify
from google.cloud import storage
import datetime
import openai
from flask_cors import CORS  # ✅ Import CORS

app = Flask(__name__)

# ✅ Enable CORS for all domains (including Framer)
CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ Ensure Flask uses the correct Google Cloud service account key
SERVICE_ACCOUNT_KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not SERVICE_ACCOUNT_KEY_PATH:
    raise FileNotFoundError("Service account key file path not found!")

# ✅ Read OpenAI API Key from Environment Variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key is missing! Set OPENAI_API_KEY in environment variables.")

# ✅ Google Cloud Storage setup
BUCKET_NAME = "construction_ai"
storage_client = storage.Client()

@app.route("/", methods=["GET"])
def home():
    """Test route to verify Flask is running."""
    return jsonify({"message": "Flask is running on Cloud Run!"})

# ✅ 1️⃣ Generate a Signed URL for Image Upload Using V4 Signing
@app.route('/upload', methods=['POST'])
def generate_signed_url():
    """Generates a signed URL for image uploads using V4 signing."""
    data = request.get_json()
    file_name = data.get("file_name")

    if not file_name:
        return jsonify({"error": "Missing file_name"}), 400

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"uploads/{file_name}")

    expiration = datetime.timedelta(minutes=30)
    signed_url = blob.generate_signed_url(
        expiration=expiration,
        method="PUT",
        version="v4"
    )

    return jsonify({"signed_url": signed_url})

# ✅ 2️⃣ AI Home Inspector - Use GPT-4o Vision API for Image Analysis
@app.route('/chat', methods=['POST'])
def analyze_image():
    """Sends the uploaded image URL to GPT-4o for AI vision analysis."""
    data = request.get_json()
    image_url = data.get("image_url")

    if not image_url:
        return jsonify({"error": "Missing image_url"}), 400

    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a professional home inspector with expertise in damage assessment."},
            {"role": "user", "content": [
                {"type": "text", "text": "Analyze the damage in this image and provide the following:\n"
                    "- Description of the visible damage\n"
                    "- Possible causes of the issue\n"
                    "- Repair recommendations with cost estimates"},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]}
        ],
        max_tokens=500
    )

    return jsonify({"response": response.choices[0].message.content})

# ✅ Fix: Ensure Flask Listens on All Addresses
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
