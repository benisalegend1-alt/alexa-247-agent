import os
import urllib.request
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

# Keeping your API key directly as requested
client = Groq(
    api_key="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".strip()
)

# Replace this with your secret topic name from the ntfy app on your phone
NTFY_TOPIC = "my_secret_alexa_groq_98234"

@app.route("/ping", methods=["GET"])
def ping():
    """Lightweight health check endpoint to keep Render awake."""
    return "OK", 200

def send_to_phone(text, title="Alexa AI Agent"):
    """Sends a push notification to your phone via ntfy.sh using built-in urllib."""
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh{NTFY_TOPIC}",
            data=text.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": "high"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            return 200 <= response.status < 300
    except Exception:
        return False

def is_send_command(query):
    """Checks if the user wants to send something to their phone."""
    q = query.lower().strip()
    triggers = [
        "to my phone",
        "to phone",
        "text me",
        "text that",
        "push that",
        "push this",
        "send that",
        "send this"
    ]
    return any(t in q for t in triggers)

def is_referring_to_previous(query):
    """Checks if the user is referring to the last answer (e.g., 'send that to my phone')."""
    q = query.lower().strip()
    exact_phrases = [
        "send that to my phone",
        "send this to my phone",
        "send to my phone",
        "send it to my phone",
        "text that to me",
        "text me that",
        "push that to my phone"
    ]
    return q in exact_phrases or (len(q.split()) <= 5 and ("that" in q or "it" in q or "this" in q))

@app.route("/", methods=["POST"])
def alexa_endpoint():
    data = request.get_json(silent=True) or {}
    request_type = data.get("request", {}).get("type", "")
    
    # Retrieve conversation memory from Alexa's sessionAttributes
    session_attributes = data.get("session", {}).get("attributes", {})
    history = session_attributes.get("history", [])
    last_response = session_attributes.get("last_response", "")
    should_end = False

    if request_type == "LaunchRequest":
        speech = "Your Groq AI agent is online and ready. Ask me anything."

    elif request_type == "IntentRequest":
        intent = data.get("request", {}).get("intent", {})
        intent_name = intent.get("name", "")

        if intent_name in ["AMAZON.StopIntent", "AMAZON.CancelIntent"]:
            speech = "Goodbye."
            should_end = True
        else:
            slots = intent.get("slots", {})
            user_query = slots.get("query", {}).get("value", "")

            # Handle SendToPhoneIntent directly when no {query} slot is spoken
            if not user_query and intent_name == "SendToPhoneIntent":
                user_query = "send that to my phone"

            if not user_query:
                speech = "I am listening. Try saying, ask my agent about, followed by your question."

            # CASE 1: User wants to send something to their phone
            elif intent_name == "SendToPhoneIntent" or is_send_command(user_query):
                # Subcase 1A: Sending the previous spoken answer ("Send that to my phone")
                if intent_name == "SendToPhoneIntent" or is_referring_to_previous(user_query):
                    if not last_response:
                        speech = "I haven't answered a question yet, so there is nothing to send."
                    elif send_to_phone(last_response):
                        speech = "Sent to your phone."
                    else:
                        speech = "Sorry, I couldn't reach your phone right now."
                
                # Subcase 1B: Generating new specific content for the phone ("Send a taco shopping list to my phone")
                else:
                    try:
                        chat_completion = client.chat.completions.create(
                            model="openai/gpt-oss-20b",
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "You are generating text to be sent directly to a user's smartphone screen. "
                                        "Fulfill their request clearly and concisely using clean plain-text formatting "
                                        "(like short dashes for lists). Do not add conversational filler like 'Here is your list'."
                                    )
                                }
                            ] + history[-2:] + [{"role": "user", "content": user_query}],
                            max_tokens=300,
                            temperature=0.4,
                            timeout=6.5
                        )

                        phone_text = (chat_completion.choices[0].message.content or "").replace("*", "").replace("#", "").strip()
                        
                        if send_to_phone(phone_text, title="Alexa Note"):
                            speech = "I've sent that to your phone."
                            session_attributes["last_response"] = phone_text
                        else:
                            speech = "I generated the response, but couldn't reach your phone."

                    except Exception as e:
                        speech = f"An API processing error occurred: {str(e)}"

            # CASE 2: Normal voice Q&A
            else:
                try:
                    messages = [
                        {
                            "role": "system",
                            "content": (
                                "You are a sharp, intelligent voice assistant on an Amazon Echo Dot. "
                                "Give direct, insightful, conversational answers in 2 to 3 short sentences. "
                                "Never use markdown, bullet points, or special symbols."
                            )
                        }
                    ] + history[-4:] + [{"role": "user", "content": user_query}]

                    chat_completion = client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=messages,
                        max_tokens=180,
                        temperature=0.5,
                        timeout=6.5
                    )

                    raw_text = chat_completion.choices[0].message.content or ""
                    speech = raw_text.replace("*", "").replace("#", "").strip()

                    # Save turn into Alexa's session memory
                    history.append({"role": "user", "content": user_query})
                    history.append({"role": "assistant", "content": speech})
                    session_attributes["history"] = history[-6:]
                    session_attributes["last_response"] = speech

                except Exception as e:
                    speech = f"An API processing error occurred: {str(e)}"
    else:
        speech = "Goodbye."
        should_end = True

    return jsonify({
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": speech
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Anything else?"
                }
            },
            "shouldEndSession": should_end
        }
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
