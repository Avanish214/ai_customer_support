import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from openai import APIConnectionError, APIStatusError, AuthenticationError


SYSTEM_PROMPT = """You are a helpful e-commerce customer support assistant.
Be clear, courteous, concise, and practical. Use the conversation history when
answering follow-up questions. Never claim to have accessed an order, account,
or company policy unless the user supplied that information. Do not invent
delivery dates, refund decisions, or return-policy details. Ask for the minimum
non-sensitive information needed to help, and never request passwords or full
payment-card details. When a case requires account access or a policy decision,
explain that a human support agent may need to verify it."""

PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)


def create_model():
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

    if provider == "ollama":
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.2,
        )

    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is missing. Add it to your .env file."
            )
        return ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.2,
        )

    raise ValueError("LLM_PROVIDER must be either 'ollama' or 'openrouter'.")


class AssistantError(Exception):
    pass


def invoke_assistant(chain, history, question):
    try:
        response = chain.invoke({"history": history, "question": question})
    except AuthenticationError as error:
        raise AssistantError(
            "Authentication failed. Check your OpenRouter API key."
        ) from error
    except APIConnectionError as error:
        raise AssistantError(
            "Could not connect to the LLM provider. Check your network, "
            "provider URL, and that Ollama is running if selected."
        ) from error
    except APIStatusError as error:
        raise AssistantError(
            f"The provider returned HTTP {error.status_code}. Check the "
            "model name, account limits, and provider status."
        ) from error
    except Exception as error:
        raise AssistantError(
            f"Could not get a response ({error}). Check that the selected "
            "model is available and its provider is running."
        ) from error

    return str(response.content)


def main():
    load_dotenv()

    try:
        chain = PROMPT | create_model()
    except (ValueError, ImportError) as error:
        print(f"Configuration error: {error}")
        return

    history = []
    print("E-commerce support assistant. Enter /clear to reset or /quit to exit.")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return

        if not question:
            continue
        if question.lower() in {"/quit", "/exit"}:
            print("Goodbye.")
            return
        if question.lower() == "/clear":
            history.clear()
            print("Conversation history cleared.")
            continue

        try:
            answer = invoke_assistant(chain, history, question)
        except AssistantError as error:
            print(error)
            continue

        history.append(HumanMessage(content=question))
        history.append(AIMessage(content=answer))
        print(f"Assistant: {answer}")


if __name__ == "__main__":
    main()