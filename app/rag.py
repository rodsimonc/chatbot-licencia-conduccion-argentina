"""Cadena RAG: recupera fragmentos del manual y genera la respuesta con el LLM."""
from functools import lru_cache

from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from . import config
from .ingest import build_index, index_exists


SYSTEM_PROMPT = """Sos «{bot_name}», un asistente que responde preguntas sobre el \
Manual del Conductor de la Agencia Nacional de Seguridad Vial (ANSV) de Argentina.

Reglas:
- Respondé SIEMPRE en español rioplatense, de forma clara y breve.
- Usá ÚNICAMENTE la información del CONTEXTO extraído del manual. No inventes.
- Si la respuesta no está en el contexto, decí que no lo encontrás en el manual y \
sugerí reformular la pregunta. No uses conocimiento externo.
- Cuando corresponda, mencioná la/las páginas del manual de donde surge la respuesta.
- No des asesoramiento legal personalizado; explicá lo que dice el manual.

CONTEXTO:
{context}
"""


def _get_llm():
    if config.LLM_PROVIDER == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=config.GEMINI_CHAT_MODEL, temperature=config.TEMPERATURE,
            google_api_key=config.GOOGLE_API_KEY,
        )
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=config.CHAT_MODEL, temperature=config.TEMPERATURE, api_key=config.OPENAI_API_KEY)


def _format_docs(docs) -> str:
    partes = []
    for d in docs:
        pag = d.metadata.get("pagina", "?")
        partes.append(f"[Página {pag}] {d.page_content}")
    return "\n\n".join(partes)


@lru_cache(maxsize=1)
def _load_store():
    if not index_exists():
        build_index(verbose=True)
    embeddings = config.get_embeddings()
    return FAISS.load_local(str(config.INDEX_DIR), embeddings, allow_dangerous_deserialization=True)


@lru_cache(maxsize=1)
def _build_chain():
    retriever = _load_store().as_retriever(search_kwargs={"k": config.RETRIEVER_K})
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ]).partial(bot_name=config.BOT_NAME)
    llm = _get_llm()
    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever


def answer(question: str) -> dict:
    """Devuelve {answer, sources} para una pregunta."""
    chain, retriever = _build_chain()
    docs = retriever.invoke(question)
    respuesta = chain.invoke(question)
    paginas = sorted({d.metadata.get("pagina") for d in docs if d.metadata.get("pagina")})
    return {"answer": respuesta, "sources": paginas}


def warmup() -> None:
    """Carga el índice y arma la cadena (para fallar temprano si falta algo)."""
    _build_chain()
