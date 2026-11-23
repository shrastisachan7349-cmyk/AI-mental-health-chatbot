from flask import Flask, jsonify, render_template, request
import re

app = Flask(__name__)

CRISIS_PATTERNS = [
    r"\bsuicid(?:e|al)\b",
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bwant to die\b",
    r"\bhurt myself\b",
    r"\bself[- ]harm\b",
]


def is_crisis_message(message):
    return any(
        re.search(pattern, message.lower())
        for pattern in CRISIS_PATTERNS
    )


def get_reply(message, mood):
    text = message.lower()

    if any(word in text for word in ("anxious", "anxiety", "panic", "stress", "stressed")):
        return (
            "That sounds difficult. Try taking a slow breath in, then breathe out "
            "a little longer. What feels most important to talk about right now?"
        )

    if any(word in text for word in ("sad", "lonely", "down", "unhappy")):
        return (
            "I’m sorry you’re feeling this way. You deserve support. "
            "Would you like to share what has been making today difficult?"
        )

    if mood == "Happy":
        return "I’m glad to hear that. What has been going well today?"

    if mood == "Calm":
        return "It’s good to have a calm moment. What would you like to talk about?"

    return (
        "Thanks for sharing that with me. I’m here to help you reflect. "
        "What would feel like a useful next step?"
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    mood = str(data.get("mood", "")).strip()

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    if len(message) > 2000:
        return jsonify({"error": "Keep your message under 2,000 characters."}), 413

    if is_crisis_message(message):
        return jsonify({
            "reply": (
                "I’m sorry you’re going through this. I can’t provide emergency care. "
                "If you may be in immediate danger, call your local emergency number "
                "or go to the nearest emergency department. If possible, tell someone "
                "you trust and stay with them. In India, you can call Tele-MANAS at "
                "14416. This chatbot is not monitored by a person."
            ),
            "crisis": True,
        })

    return jsonify({
        "reply": get_reply(message, mood),
        "crisis": False,
    })


if __name__ == "__main__":
    app.run(debug=True)