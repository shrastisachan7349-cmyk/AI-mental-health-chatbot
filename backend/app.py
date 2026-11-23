from flask import Flask, jsonify, render_template, request
import hashlib
import re

app = Flask(
    __name__,
    template_folder="../",
    static_folder="../",
    static_url_path="/static",
)

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

    def mentions(*terms):
        return any(
            re.search(r"\b" + re.escape(term) + r"\b", text)
            for term in terms
        )

    replies = []
    if mentions("anxious", "anxiety", "panic", "stress", "stressed", "overwhelmed", "nervous"):
        replies = [
            "It sounds like a lot is weighing on you. Try naming one thing you can set aside for a moment. What feels most urgent right now?",
            "When everything feels urgent, a slow breath can help create a little space. What is one small part of this that you can handle first?",
            "That sounds exhausting. You don’t have to solve it all at once. Would it help to talk through what’s been causing the most pressure?",
        ]
    elif mentions("sad", "lonely", "down", "unhappy", "depressed", "heartbroken"):
        replies = [
            "I’m sorry things feel heavy right now. You deserve care and support. Would you like to tell me what has been hardest today?",
            "Feeling low can make even small things feel difficult. Is there someone you trust you could check in with today?",
            "Thank you for telling me. You don’t have to put a positive spin on it—what do you wish someone understood about how you feel?",
        ]
    elif mentions("sleep", "insomnia", "tired", "exhausted", "awake"):
        replies = [
            "Not getting enough rest can make everything harder. Has something been on your mind when you try to sleep?",
            "That sounds draining. If you can, give yourself a quiet wind-down moment without pressure to fall asleep immediately. What has your sleep been like lately?",
            "It’s difficult to feel rested when sleep is a struggle. Have you noticed anything that helps you feel a little calmer at night?",
        ]
    elif mentions("angry", "anger", "frustrated", "annoyed", "irritated"):
        replies = [
            "It sounds like something really crossed a line for you. What happened just before you started feeling this way?",
            "That frustration makes sense as a signal that something matters to you. What do you need most in this moment: space, to be heard, or help deciding what to do?",
            "Before reacting, it may help to pause and give yourself a little distance. What would you want the other person to understand?",
        ]
    elif mentions("friend", "partner", "relationship", "family", "boyfriend", "girlfriend", "argument", "breakup"):
        replies = [
            "Relationships can bring up a lot of feelings. What part of this situation has been on your mind the most?",
            "It sounds like this connection matters to you. What would a helpful outcome look like from your point of view?",
            "That can be hard to navigate. Would you like to talk about what happened or think through what you might say next?",
        ]
    elif mentions("school", "study", "exam", "college", "homework", "work", "job", "deadline", "boss"):
        replies = [
            "School or work pressure can pile up quickly. What is the next small task you could make more manageable?",
            "That sounds like a lot to juggle. Which part feels most difficult: getting started, the workload, or uncertainty about the outcome?",
            "Let’s make it smaller: what is one thing you can do in the next ten minutes, even if it isn’t the whole solution?",
        ]
    elif mentions("thank", "thanks", "grateful"):
        replies = [
            "You’re welcome. I’m glad you shared that with me. Is there anything else you’d like to explore?",
            "I’m glad this conversation feels helpful. What would you like to focus on next?",
        ]
    elif mentions("hello", "hi", "hey"):
        replies = [
            "Hi, I’m glad you stopped by. What’s been on your mind today?",
            "Hello! We can take this one step at a time. How are you feeling right now?",
        ]
    elif mood == "Happy" or mentions("happy", "excited", "great", "good", "proud"):
        replies = [
            "I’m glad there’s something good in your day. What would you like to remember about this moment?",
            "That’s lovely to hear. What do you think helped you feel this way?",
            "It sounds like a positive moment. Is there someone you’d like to share it with?",
        ]
    elif mood == "Calm" or mentions("calm", "peaceful", "relaxed"):
        replies = [
            "It’s good to have a calm moment. What do you notice about how you’re feeling right now?",
            "That sounds grounding. Is there anything you’d like to make space for while you feel this way?",
        ]
    else:
        replies = [
            "I hear you. What feels most important about this for you?",
            "Thanks for sharing that. What part would you like to work through first?",
            "We can take it one step at a time. What would feel helpful from me right now?",
        ]

    # Keep replies stable for the same message while varying them across messages.
    choice = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % len(replies)
    return replies[choice]


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
    app.run(debug=True, port=8080)