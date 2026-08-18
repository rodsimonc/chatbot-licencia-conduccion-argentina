"""FastAPI API for the chatbot + serving the embeddable widget and a demo page."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

from . import config

app = FastAPI(title=f"Chatbot · {config.BOT_NAME}")

origins = ["*"] if config.ALLOWED_ORIGINS.strip() == "*" else [o.strip() for o in config.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatIn(BaseModel):
    question: str


class ChatOut(BaseModel):
    answer: str
    sources: list[int]


@app.get("/health")
def health():
    return {"status": "ok", "bot": config.BOT_NAME}


@app.get("/api/info")
def info():
    return {"botName": config.BOT_NAME}


@app.post("/api/chat", response_model=ChatOut)
def chat(body: ChatIn):
    from . import rag
    q = (body.question or "").strip()
    if not q:
        return ChatOut(answer="Type a question about the manual 🙂", sources=[])
    try:
        result = rag.answer(q)
        return ChatOut(answer=result["answer"], sources=result["sources"])
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        low = msg.lower()
        if "api" in low and "key" in low:
            return ChatOut(answer="The API key is not configured on the server (check the .env: OPENAI_API_KEY or GOOGLE_API_KEY depending on the provider).", sources=[])
        return ChatOut(answer=f"An error occurred while processing the query: {msg}", sources=[])


# --- Embeddable widget and demo ---
@app.get("/widget.js")
def widget():
    return FileResponse(config.WEB_DIR / "widget.js", media_type="application/javascript")


@app.get("/")
def demo():
    return FileResponse(config.WEB_DIR / "index.html")


@app.get("/embed", response_class=PlainTextResponse)
def embed_snippet():
    """Return the <script> snippet ready to paste into any page."""
    return (
        '<script src="http://localhost:8000/widget.js" '
        'data-api="http://localhost:8000" defer></script>'
    )
