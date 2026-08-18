# «Argentina Driving License» Chatbot

A question-and-answer chatbot about the **Driver's Manual** of Argentina's National Road Safety Agency (ANSV). It uses **RAG with LangChain**: it indexes the PDF into a vector store (FAISS) and answers citing the manual's pages. It includes an **embeddable widget** to insert into any web page.

## Stack

- **LangChain** (RAG) + **FAISS** (vector store)
- Configurable model: **Google Gemini** (free tier) or **OpenAI**
- **FastAPI** (backend) + embeddable JS widget

## Free option (Google Gemini)

Gemini has a **free tier with no credit card**, usable for both answers and embeddings.

1. Get your free API key at **https://aistudio.google.com/app/apikey**.
2. In `.env` keep `LLM_PROVIDER=google` and `EMBEDDINGS_PROVIDER=google`, and paste your key into `GOOGLE_API_KEY` (the `.env.example` already comes set up this way by default).
3. Follow the "Getting started" steps. No heavy installs required.

To use OpenAI instead, set `LLM_PROVIDER=openai` and `EMBEDDINGS_PROVIDER=openai` and fill in `OPENAI_API_KEY`.

## Getting started

Requires Python 3.10+.

```bash
# 1. Install dependencies (recommended in a virtual environment)
python -m venv .venv && source .venv/bin/activate      # on Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure the API key
cp .env.example .env        # on Windows: copy .env.example .env
#   edit .env and set your OPENAI_API_KEY

# 3. Index the PDF (creates storage/faiss_index)
python -m app.ingest

# 4. Start the server
uvicorn app.server:app --reload
```

Open **http://localhost:8000/** to see the demo with the chatbot working (💬 button in the bottom right corner).

> If you don't want to pay for embeddings, set `EMBEDDINGS_PROVIDER=huggingface` in `.env`: it uses a free local model (multilingual). The answer LLM still uses OpenAI.

## Local embeddings (no quota or limits)

Ideal if you want to reindex frequently without waiting for the free tier's per-minute limits. The embeddings run on your machine and the answers still use Gemini (or OpenAI).

1. Install the local packages (once): `pip install langchain-huggingface sentence-transformers` (downloads ~500 MB).
2. In `.env` set `EMBEDDINGS_PROVIDER=huggingface` (keep `LLM_PROVIDER=google` for the answers).
3. `python -m app.ingest` (now it indexes instantly, no quota).

The first time, a model (~470 MB) is downloaded to the HuggingFace cache. To choose where it is stored (for example another disk), set the `HF_HOME` environment variable to the folder you want before running it.

## Add the chatbot to your page

Paste this line before `</body>` on any site:

```html
<script src="http://localhost:8000/widget.js" data-api="http://localhost:8000" defer></script>
```

When you publish it, replace `http://localhost:8000` with your server's URL. Optional: `data-title="..."` changes the chat title.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | `{ "question": "..." }` → `{ answer, sources }` |
| GET | `/widget.js` | The embeddable widget |
| GET | `/` | Demo page |
| GET | `/health` | Status |

## How it works (RAG)

1. **Ingestion:** the PDF is split into fragments, converted into vectors (embeddings) and stored in FAISS.
2. **Query:** given a question, the most similar fragments are retrieved and passed to the model as context.
3. **Answer:** the model responds **only** with that context and cites the pages. If something is not in the manual, it says so instead of making things up.

## Deployment

Includes `render.yaml` (Render Blueprint). See the deployment section: connect the repo to Render, set `OPENAI_API_KEY` as a secret environment variable, and you're done. The index is built automatically on the first startup if it doesn't exist.
