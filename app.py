import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get("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")

@app.route("/", methods=["POST"])
def alexa_endpoint():
    data = request.get_json()
    request_type = data.get("request", {}).get("type")

    # Default fallback message
    speech = "I received your request but encountered an error processing it."

    if request_type == "LaunchRequest":
        speech = "Your cloud-powered AI agent is online and ready. What can I do for you?"
    
    elif request_type == "IntentRequest":
        intent_name = data["request"]["intent"].get("name")
        slots = data["request"]["intent"].get("slots", {})
        
        # Pull text from the slot, handling missing or empty values safely
        user_query = None
        if "query" in slots and "value" in slots["query"]:
            user_query = slots["query"]["value"]
        
        # If the slot is empty, check if you just said the invocation phrase alone
        if not user_query:
            speech = "Your agent is listening. Please ask me to or about something."
        else:
            try:
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                  "model": "meta-llama/llama-3.2-3b-instruct:free",
                    "messages": [{"role": "user", "content": user_query}]
                }

                cloud_response = requests.post(
                    "https://openrouter.ai",
                    headers=headers,
                    json=payload
                )

                response_json = cloud_response.json()
                
                # Check for explicit OpenRouter choices response structure
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    speech = response_json["choices"][0]["message"]["content"]
                else:
                    speech = "The cloud AI model returned an empty response."
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
