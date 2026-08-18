"""RAG chain: retrieves fragments from the manual and generates the answer with the LLM."""
from functools import lru_cache

from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from . import config
from .ingest import build_index, index_exists


SYSTEM_PROMPT = """You are «{bot_name}», an assistant that answers questions about the \
Driver's Manual of Argentina's National Road Safety Agency (ANSV).

The source document is written in Spanish, but you must always answer in English.

Rules:
- ALWAYS answer in English, clearly and concisely. You may translate the manual's content.
- Use ONLY the information in the CONTEXT extracted from the manual. Do not make things up.
- If the answer is not in the context, say that you cannot find it in the manual and \
suggest rephrasing the question. Do not use outside knowledge.
- When relevant, mention the manual page(s) the answer comes from.
- Do not give personalized legal advice; explain what the manual says.

CONTEXT:
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
    parts = []
    for d in docs:
        page = d.metadata.get("pagina", "?")
        parts.append(f"[Page {page}] {d.page_content}")
    return "\n\n".join(parts)


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
    """Return {answer, sources} for a question."""
    chain, retriever = _build_chain()
    docs = retriever.invoke(question)
    response = chain.invoke(question)
    pages = sorted({d.metadata.get("pagina") for d in docs if d.metadata.get("pagina")})
    return {"answer": response, "sources": pages}


def warmup() -> None:
    """Load the index and build the chain (to fail early if something is missing)."""
    _build_chain()
