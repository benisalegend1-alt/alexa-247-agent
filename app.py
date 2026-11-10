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
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://render.com",
                    "X-Title": "Alexa Agent"
                }
                payload = {
                    "model": "openrouter/free",
                    "messages": [{"role": "user", "content": user_query}]
                }

                cloud_response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                )

                response_json = cloud_response.json()
                
                # Dynamic Error Debugger: If OpenRouter returns an error, Alexa will read it!
                if "error" in response_json:
                    error_msg = response_json["error"].get("message", "Unknown API error")
                    print(f"OpenRouter API Error: {error_msg}")
                    speech = f"OpenRouter cloud error: {error_msg}"
                elif "choices" in response_json and len(response_json["choices"]) > 0:
                    speech = response_json["choices"][0]["message"]["content"]
                else:
                    print(f"Unexpected raw response structure: {response_json}")
                    speech = "The cloud model returned an unexpected payload structure."
            except Exception as e:
                print(f"Server Script Crash Error: {e}")
                speech = f"Internal server script error occurred: {str(e)}"
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
