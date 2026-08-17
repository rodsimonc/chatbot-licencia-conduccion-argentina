"""Ingesta: carga el PDF, lo parte en fragmentos, los embebe y guarda el índice FAISS.

Uso:  python -m app.ingest
Se ejecuta una vez (o cada vez que cambie el PDF). El servidor también lo corre
automáticamente si el índice no existe todavía.

La indexación se hace por TANDAS para respetar los límites por minuto del plan
gratuito (por ejemplo, Gemini permite 100 embeddings por minuto). Si aparece un
error de límite (429), espera y reintenta. Esto solo pasa al indexar; después
cada pregunta usa un único embedding.
"""
import os
import time

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from . import config


def _batch_params():
    """Tamaño de tanda y pausa entre tandas según el proveedor de embeddings."""
    if config.EMBEDDINGS_PROVIDER == "google":
        # Gemini free tier: 100 embeddings/min. Usamos 90 por minuto para ir holgados.
        return int(os.getenv("INGEST_BATCH_SIZE", "90")), float(os.getenv("INGEST_BATCH_DELAY", "62"))
    if config.EMBEDDINGS_PROVIDER == "openai":
        return int(os.getenv("INGEST_BATCH_SIZE", "200")), float(os.getenv("INGEST_BATCH_DELAY", "0"))
    # huggingface (local): sin límite
    return int(os.getenv("INGEST_BATCH_SIZE", "500")), float(os.getenv("INGEST_BATCH_DELAY", "0"))


def _add_with_retry(store, embeddings, batch, verbose):
    """Agrega una tanda; si hay 429 (límite por minuto), espera y reintenta."""
    for intento in range(6):
        try:
            if store is None:
                return FAISS.from_documents(batch, embeddings)
            store.add_documents(batch)
            return store
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                espera = 62
                if verbose:
                    print(f"[ingest] Límite por minuto alcanzado; espero {espera}s y reintento…")
                time.sleep(espera)
                continue
            raise
    raise RuntimeError("No se pudo indexar por límite de cuota tras varios reintentos.")


def build_index(verbose: bool = True) -> None:
    if not config.PDF_PATH.exists():
        raise FileNotFoundError(f"No se encontró el PDF en {config.PDF_PATH}")

    if verbose:
        print(f"[ingest] Cargando PDF: {config.PDF_PATH}")
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
        print(f"[ingest] {len(pages)} páginas -> {len(chunks)} fragmentos")
        print(f"[ingest] Embeddings: {config.EMBEDDINGS_PROVIDER} | tandas de {batch_size}"
              + (f", pausa {int(delay)}s entre tandas (límite del plan gratis)" if delay else ""))

    embeddings = config.get_embeddings()
    store = None
    total = len(chunks)
    for i in range(0, total, batch_size):
        batch = chunks[i:i + batch_size]
        store = _add_with_retry(store, embeddings, batch, verbose)
        hechos = min(i + batch_size, total)
        if verbose:
            print(f"[ingest] {hechos}/{total} fragmentos indexados")
        if delay and hechos < total:
            if verbose:
                print(f"[ingest] Espero {int(delay)}s por el límite por minuto del plan gratuito…")
            time.sleep(delay)

    config.INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)
    store.save_local(str(config.INDEX_DIR))
    if verbose:
        print(f"[ingest] Índice guardado en {config.INDEX_DIR}")


def index_exists() -> bool:
    return (config.INDEX_DIR / "index.faiss").exists()


if __name__ == "__main__":
    build_index(verbose=True)
    print("Ingesta completada.")
