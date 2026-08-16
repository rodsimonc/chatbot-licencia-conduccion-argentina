"""Ingesta: carga el PDF, lo parte en fragmentos, los embebe y guarda el índice FAISS.

Uso:  python -m app.ingest
Se ejecuta una vez (o cada vez que cambie el PDF). El servidor también lo corre
automáticamente si el índice no existe todavía.
"""
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from . import config


def build_index(verbose: bool = True) -> None:
    if not config.PDF_PATH.exists():
        raise FileNotFoundError(f"No se encontró el PDF en {config.PDF_PATH}")

    if verbose:
        print(f"[ingest] Cargando PDF: {config.PDF_PATH}")
    loader = PyPDFLoader(str(config.PDF_PATH))
    pages = loader.load()  # una entrada por página, con metadata['page']

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(pages)
    # Numeramos la página de forma legible (1-based) para poder citarla.
    for c in chunks:
        c.metadata["pagina"] = int(c.metadata.get("page", 0)) + 1
    if verbose:
        print(f"[ingest] {len(pages)} páginas -> {len(chunks)} fragmentos")
        print(f"[ingest] Embeddings: {config.EMBEDDINGS_PROVIDER}")

    embeddings = config.get_embeddings()
    store = FAISS.from_documents(chunks, embeddings)
    config.INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)
    store.save_local(str(config.INDEX_DIR))
    if verbose:
        print(f"[ingest] Índice guardado en {config.INDEX_DIR}")


def index_exists() -> bool:
    return (config.INDEX_DIR / "index.faiss").exists()


if __name__ == "__main__":
    build_index(verbose=True)
    print("Ingesta completada.")
