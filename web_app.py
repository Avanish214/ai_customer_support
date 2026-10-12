import os
import secrets
from functools import lru_cache
from threading import Lock

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from langchain_core.messages import AIMessage, HumanMessage

import app as assistant


load_dotenv()

web_app = Flask(__name__)
web_app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

conversations = {}
conversations_lock = Lock()


@lru_cache(maxsize=1)
def get_chain():
    return assistant.PROMPT | assistant.create_model()


def get_conversation_id():
    if "conversation_id" not in session:
        session["conversation_id"] = secrets.token_urlsafe(24)
    return session["conversation_id"]


@web_app.get("/")
def home():
    return render_template("index.html")


@web_app.get("/api/config")
def get_config():
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    model = os.getenv(
        "OLLAMA_MODEL" if provider == "ollama" else "OPENROUTER_MODEL",
        "llama3.2" if provider == "ollama" else "openai/gpt-4o-mini",
    )
    return jsonify(provider=provider, model=model)


@web_app.get("/api/history")
def get_history():
    conversation_id = get_conversation_id()
    with conversations_lock:
        history = list(conversations.get(conversation_id, []))
    messages = [
        {
            "role": "user" if isinstance(message, HumanMessage) else "assistant",
            "content": str(message.content),
        }
        for message in history
    ]
    return jsonify(messages=messages)


@web_app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True)
    question = payload.get("question") if isinstance(payload, dict) else None
    if not isinstance(question, str) or not question.strip():
        return jsonify(error="Enter a message to continue."), 400
    question = question.strip()
    if len(question) > 4000:
        return jsonify(error="Messages must be 4,000 characters or fewer."), 400

    conversation_id = get_conversation_id()
    with conversations_lock:
        history = list(conversations.get(conversation_id, []))

    try:
        answer = assistant.invoke_assistant(get_chain(), history, question)
    except assistant.AssistantError as error:
        return jsonify(error=str(error)), 502
    except (ValueError, ImportError) as error:
        return jsonify(error=f"Configuration error: {error}"), 503

    with conversations_lock:
        conversation = conversations.setdefault(conversation_id, [])
        conversation.extend(
            [HumanMessage(content=question), AIMessage(content=answer)]
        )
        del conversation[:-32]

    return jsonify(answer=answer)


@web_app.post("/api/clear")
def clear_history():
    conversation_id = get_conversation_id()
    with conversations_lock:
        conversations.pop(conversation_id, None)
    return jsonify(ok=True)


if __name__ == "__main__":
    web_app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False,
    )