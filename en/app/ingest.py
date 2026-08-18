"""Ingestion: loads the PDF, splits it into fragments, embeds them and saves the FAISS index.

Usage:  python -m app.ingest
Run once (or every time the PDF changes). The server also runs it
automatically if the index does not exist yet.

Indexing is done in BATCHES to respect the per-minute limits of the
free tier (for example, Gemini allows 100 embeddings per minute). If a rate
limit error (429) appears, it waits and retries. This only happens during indexing;
afterwards each question uses a single embedding.
"""
import os
import time

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from . import config


def _batch_params():
    """Batch size and pause between batches depending on the embeddings provider."""
    if config.EMBEDDINGS_PROVIDER == "google":
        # Gemini free tier: 100 embeddings/min. We use 90 per minute to stay safe.
        return int(os.getenv("INGEST_BATCH_SIZE", "90")), float(os.getenv("INGEST_BATCH_DELAY", "62"))
    if config.EMBEDDINGS_PROVIDER == "openai":
        return int(os.getenv("INGEST_BATCH_SIZE", "200")), float(os.getenv("INGEST_BATCH_DELAY", "0"))
    # huggingface (local): no limit
    return int(os.getenv("INGEST_BATCH_SIZE", "500")), float(os.getenv("INGEST_BATCH_DELAY", "0"))


def _add_with_retry(store, embeddings, batch, verbose):
    """Add a batch; on a 429 (per-minute limit), wait and retry."""
    for attempt in range(6):
        try:
            if store is None:
                return FAISS.from_documents(batch, embeddings)
            store.add_documents(batch)
            return store
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                wait = 62
                if verbose:
                    print(f"[ingest] Per-minute limit reached; waiting {wait}s and retrying…")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("Could not index due to quota limit after several retries.")


def build_index(verbose: bool = True) -> None:
    if not config.PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found at {config.PDF_PATH}")

    if verbose:
        print(f"[ingest] Loading PDF: {config.PDF_PATH}")
    pages = PyPDFLoader(str(config.PDF_PATH)).load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(pages)
    for c in chunks:
        c.metadata["pagina"] = int(c.metadata.get("page", 0)) + 1

    batch_size, delay = _batch_params()
    if verbose:
        print(f"[ingest] {len(pages)} pages -> {len(chunks)} fragments")
        print(f"[ingest] Embeddings: {config.EMBEDDINGS_PROVIDER} | batches of {batch_size}"
              + (f", {int(delay)}s pause between batches (free tier limit)" if delay else ""))

    embeddings = config.get_embeddings()
    store = None
    total = len(chunks)
    for i in range(0, total, batch_size):
        batch = chunks[i:i + batch_size]
        store = _add_with_retry(store, embeddings, batch, verbose)
        done = min(i + batch_size, total)
        if verbose:
            print(f"[ingest] {done}/{total} fragments indexed")
        if delay and done < total:
            if verbose:
                print(f"[ingest] Waiting {int(delay)}s for the free tier per-minute limit…")
            time.sleep(delay)

    config.INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)
    store.save_local(str(config.INDEX_DIR))
    if verbose:
        print(f"[ingest] Index saved at {config.INDEX_DIR}")


def index_exists() -> bool:
    return (config.INDEX_DIR / "index.faiss").exists()


if __name__ == "__main__":
    build_index(verbose=True)
    print("Ingestion completed.")
