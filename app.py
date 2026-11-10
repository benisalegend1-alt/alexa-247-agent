import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

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
        
        # Pull text from the slot safely
        user_query = None
        if "query" in slots and "value" in slots["query"]:
            user_query = slots["query"]["value"]
        
        if not user_query:
            speech = "Your agent is listening. Please ask me to or about something."
        else:
            try:
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "openrouter/free",
                    "messages": [{"role": "user", "content": user_query}]
                }

                cloud_response = requests.post(
                    "https://openrouter.ai",
                    headers=headers,
                    json=payload
                )

                response_json = cloud_response.json()
                
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    speech = response_json["choices"]["message"]["content"]
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
    app.run()
