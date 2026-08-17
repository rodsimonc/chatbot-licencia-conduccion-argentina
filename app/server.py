"""API FastAPI del chatbot + entrega del widget embebible y una página demo."""
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
        return ChatOut(answer="Escribime una pregunta sobre el manual 🙂", sources=[])
    try:
        result = rag.answer(q)
        return ChatOut(answer=result["answer"], sources=result["sources"])
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        low = msg.lower()
        if "api" in low and "key" in low:
            return ChatOut(answer="Falta configurar la API key en el servidor (revisá el .env: OPENAI_API_KEY o GOOGLE_API_KEY según el proveedor).", sources=[])
        return ChatOut(answer=f"Ocurrió un error procesando la consulta: {msg}", sources=[])


# --- Widget embebible y demo ---
@app.get("/widget.js")
def widget():
    return FileResponse(config.WEB_DIR / "widget.js", media_type="application/javascript")


@app.get("/")
def demo():
    return FileResponse(config.WEB_DIR / "index.html")


@app.get("/embed", response_class=PlainTextResponse)
def embed_snippet():
    """Devuelve el snippet <script> listo para pegar en cualquier página."""
    return (
        '<script src="http://localhost:8000/widget.js" '
        'data-api="http://localhost:8000" defer></script>'
    )
