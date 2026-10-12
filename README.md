# AI Customer Support Assistant

A browser-based e-commerce support assistant powered by LangChain, with a
command-line mode also available. Choose a local Ollama model or a model
available through OpenRouter. Browser conversation history is kept in memory
for each browser session while the server is running.

## Set up

Create and activate a virtual environment, then install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

Copy `.env.example` to `.env` and edit the settings for your provider.

### Ollama

Install Ollama from [ollama.com](https://ollama.com/), then download a model:

```bash
ollama pull llama3.2
```

Keep `LLM_PROVIDER=ollama` in `.env`. Ollama must be running and reachable at
`OLLAMA_BASE_URL` (default `http://localhost:11434`). Set `OLLAMA_MODEL` to a
model you have downloaded.

### OpenRouter

Create an OpenRouter API key, set `LLM_PROVIDER=openrouter`, and add the key to
`OPENROUTER_API_KEY` in `.env`. Set `OPENROUTER_MODEL` to a model enabled for
your account. Keep `.env` private; it is excluded from git.

## Run in a browser

```bash
python web_app.py
```

Open <http://localhost:5000>. Use **New conversation** to clear the current
thread. Conversation history is cleared when the server stops.

## Run in the terminal

```bash
python app.py
```

Enter a question at the `You:` prompt. Use `/clear` to start a fresh
conversation or `/quit` to exit. The assistant cannot access order systems, so
it will ask for details or recommend a human agent rather than claim an order
or refund has been checked.

## Evaluate

Try questions about a delayed order, a damaged product, a return, and a refund.
Then ask a follow-up (for example, clarify the order issue) to check that the
assistant uses conversation history. Check that replies address the question,
do not invent policy or order details, and remain consistent across follow-ups.