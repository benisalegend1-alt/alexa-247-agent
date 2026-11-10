import os
from flask import Flask, request, jsonify
from groq import Groq  # Import the official SDK

app = Flask(__name__)

# Initialize the official Groq client with your key directly
client = Groq(
    api_key="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".strip()
)

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
                # Use the official client.chat.completions.create method to completely avoid 405 errors
                chat_completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant", #  PASTE THIS INSTEAD
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a helpful voice assistant on an Amazon Echo Dot. Keep answers clear, conversational, and under 3 sentences."
                        },
                        {
                            "role": "user", 
                            "content": user_query
                        }
                    ],
                    timeout=10
                )

                # Extract the message using the SDK attributes cleanly
                raw_text = chat_completion.choices[0].message.content
                speech = raw_text.replace("*", "").replace("#", "")
                        
            except Exception as e:
                speech = f"An API processing error occurred: {str(e)}"
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


if __name__ == "__main__":
    app.run()

