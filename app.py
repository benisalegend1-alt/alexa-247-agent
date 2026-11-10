import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Read the secure API key from Render's hidden environment variables
OPENROUTER_API_KEY = os.environ.get("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")

@app.route("/", methods=["POST"])
def alexa_endpoint():
    data = request.get_json()
    request_type = data.get("request", {}).get("type")

    if request_type == "LaunchRequest":
        speech = "Your cloud-powered AI agent is online and ready. What can I do for you?"
    elif request_type == "IntentRequest":
        slots = data["request"]["intent"].get("slots", {})
        user_query = slots.get("query", {}).get("value", "I didn't quite catch that.")

        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": [{"role": "user", "content": user_query}]
            }

            cloud_response = requests.post(
                "https://openrouter.ai",
                headers=headers,
                json=payload
            )

            response_json = cloud_response.json()
            speech = response_json["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error occurred: {e}")
            speech = "I could not communicate with the cloud AI engine."
    else:
        speech = "Goodbye."

    return jsonify({
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": speech},
            "shouldEndSession": False if request_type == "LaunchRequest" else True
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

