import os
from flask import Flask, request, jsonify
from google.cloud import storage
import datetime
import openai

app = Flask(__name__)

# ✅ Ensure Flask uses the correct Google Cloud service account key
SERVICE_ACCOUNT_KEY_PATH = "C:/pythonscriptsgpt/gcp-key.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_KEY_PATH

# ✅ Check if the service account key file exists
if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
    raise FileNotFoundError(f"Service account key not found: {SERVICE_ACCOUNT_KEY_PATH}")

# ✅ Read OpenAI API Key from File
OPENAI_KEY_PATH = "C:/pythonscriptsgpt/chatgptapikey.txt"
if not os.path.exists(OPENAI_KEY_PATH):
    raise FileNotFoundError(f"OpenAI API key file not found: {OPENAI_KEY_PATH}")

with open(OPENAI_KEY_PATH, "r") as file:
    OPENAI_API_KEY = file.read().strip()

# ✅ Enable CORS (allows frontend apps like Framer to access this API)
from flask_cors import CORS
CORS(app)

# ✅ Google Cloud Storage setup
BUCKET_NAME = "construction_ai"  # 🔹 Your actual bucket name
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
        version="v4"  # 🔥 Ensuring V4 signing is used
    )

    print(f"Generated Signed URL for Upload: {signed_url}")  # Debugging output

    return jsonify({"signed_url": signed_url})

# ✅ 2️⃣ Generate a Signed URL for Reading (GET) the Uploaded Image
@app.route('/signed_url', methods=['POST'])
def generate_read_signed_url():
    """Generates a signed URL for reading (GET) an uploaded image."""
    data = request.get_json()
    file_name = data.get("file_name")

    if not file_name:
        return jsonify({"error": "Missing file_name"}), 400

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"uploads/{file_name}")

    expiration = datetime.timedelta(minutes=30)  # URL expires in 30 minutes
    signed_url = blob.generate_signed_url(
        expiration=expiration,
        method="GET",  # 🔥 Allowing READ access
        version="v4"
    )

    print(f"Generated Signed URL for Reading: {signed_url}")  # Debugging output

    return jsonify({"signed_url": signed_url})

# ✅ 3️⃣ AI Home Inspector - Use GPT-4o Vision API for Image Analysis
@app.route('/chat', methods=['POST'])
def analyze_image():
    """Sends the uploaded image URL to GPT-4o for AI vision analysis."""
    data = request.get_json()
    image_url = data.get("image_url")

    if not image_url:
        return jsonify({"error": "Missing image_url"}), 400

    # ✅ Use OpenAI API Key securely
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # ✅ Send Image URL to GPT-4o Vision API
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
    app.run(host="0.0.0.0", port=5000, debug=True)
