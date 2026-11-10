from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Your valid Groq API Key
GROQ_API_KEY = "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".strip()

@app.route("/", methods=["POST"])
def alexa_endpoint():
    data = request.get_json(silent=True) or {}
    request_type = data.get("request", {}).get("type", "")

    if request_type == "LaunchRequest":
        speech = "Your Groq AI agent is online and ready. Ask me anything."
    
    elif request_type == "IntentRequest":
        slots = data.get("request", {}).get("intent", {}).get("slots", {})
        user_query = slots.get("query", {}).get("value", "")
        
        if not user_query:
            speech = "I am listening. Try saying, ask my agent about, followed by your question."
        else:
            try:
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are a helpful voice assistant on an Amazon Echo Dot. Keep your answers clear, conversational, and under 3 sentences."
                        },
                        {
                            "role": "user", 
                            "content": user_query
                        }
                    ]
                }

                # CHANGED TO NATIVE CORE DIRECT ENDPOINT URL
                cloud_response = requests.post(
                    "https://groq.com",
                    headers=headers,
                    json=payload,
                    timeout=10
                )

                if cloud_response.status_code != 200:
                    speech = f"Groq response error, status code: {cloud_response.status_code}."
                else:
                    response_json = cloud_response.json()
                    choices = response_json.get("choices", [])
                    
                    if len(choices) > 0:
                        raw_text = choices[0].get("message", {}).get("content", "")
                        speech = raw_text.replace("*", "").replace("#", "")
                    else:
                        speech = "The AI model returned an empty response."
                        
            except requests.exceptions.Timeout:
                speech = "The cloud server took too long to think. Please ask me again."
            except Exception as e:
                speech = f"A local server error occurred: {str(e)}"
    else:
        speech = "Goodbye."

    return jsonify({
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText", 
                "text": speech
            },
            "shouldEndSession": False if request_type == "LaunchRequest" else True
        }
    })

if __name__ == "__main__":
    app.run()

