import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("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")

@app.route("/", methods=["POST"])
def alexa_endpoint():
    data = request.get_json()
    request_type = data.get("request", {}).get("type")

    # Fallback message
    speech = "I encountered an error processing your request."

    if request_type == "LaunchRequest":
        speech = "Your Groq powered AI agent is online and ready. What can I do for you?"
    
    elif request_type == "IntentRequest":
        slots = data["request"]["intent"].get("slots", {})
        
        user_query = None
        if "query" in slots and "value" in slots["query"]:
            user_query = slots["query"]["value"]
        
        if not user_query:
            speech = "Your agent is listening. Please ask me to or about something."
        else:
            try:
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.1-8b-instant", # Groq's lightning-fast, free Llama model
                    "messages": [{"role": "user", "content": user_query}]
                }

                # Direct call to Groq's official API endpoint
                cloud_response = requests.post(
                    "https://groq.com",
                    headers=headers,
                    json=payload
                )

                response_json = cloud_response.json()
                
                # Debug error handling
                if "error" in response_json:
                    error_msg = response_json["error"].get("message", "API Error")
                    speech = f"Groq cloud error: {error_msg}"
                elif "choices" in response_json and len(response_json["choices"]) > 0:
                    speech = response_json["choices"]["message"]["content"]
                else:
                    speech = "The Groq model returned an unexpected response structure."
            except Exception as e:
                speech = f"Internal server error occurred: {str(e)}"
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
