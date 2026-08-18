"""Chatbot configuration, read from environment variables (.env)."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = BASE_DIR / "storage"
WEB_DIR = BASE_DIR / "web"

# Source document
PDF_PATH = Path(os.getenv("PDF_PATH", DATA_DIR / "manual.pdf"))
INDEX_DIR = STORAGE_DIR / "faiss_index"

# Bot identity
BOT_NAME = os.getenv("BOT_NAME", "Argentina Driving License")

# Language model provider (answers): openai | google
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

# Google Gemini (free tier in Google AI Studio)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-001")

# HuggingFace (free local embeddings)
HF_EMBED_MODEL = os.getenv("HF_EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Embeddings provider (for indexing and searching): openai | google | huggingface
EMBEDDINGS_PROVIDER = os.getenv("EMBEDDINGS_PROVIDER", "openai")

# RAG parameters
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
RETRIEVER_K = int(os.getenv("RETRIEVER_K", "4"))

# CORS (for embedding the widget in another page). "*" = any origin.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")


def get_embeddings():
    """Return the embeddings model according to the configured provider."""
    if EMBEDDINGS_PROVIDER == "google":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model=GEMINI_EMBED_MODEL, google_api_key=GOOGLE_API_KEY)
    if EMBEDDINGS_PROVIDER == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=HF_EMBED_MODEL)
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(model=OPENAI_EMBED_MODEL, api_key=OPENAI_API_KEY)
