# Chatbot «Licencia conducción Argentina»

Chatbot de preguntas y respuestas sobre el **Manual del Conductor** de la Agencia Nacional de Seguridad Vial (ANSV). Usa **RAG con LangChain**: indexa el PDF en un vector store (FAISS) y responde citando las páginas del manual. Incluye un **widget embebible** para insertar en cualquier página web.

## Stack

- **LangChain** (RAG) + **FAISS** (vector store)
- **OpenAI** (`gpt-4o-mini` + embeddings) — configurable
- **FastAPI** (backend) + widget JS embebible

## Puesta en marcha

Requiere Python 3.10+.

```bash
# 1. Instalar dependencias (recomendado en un entorno virtual)
python -m venv .venv && source .venv/bin/activate      # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configurar la API key
cp .env.example .env        # en Windows: copy .env.example .env
#   editá .env y poné tu OPENAI_API_KEY

# 3. Indexar el PDF (crea storage/faiss_index)
python -m app.ingest

# 4. Levantar el servidor
uvicorn app.server:app --reload
```

Abrí **http://localhost:8000/** para ver la demo con el chatbot funcionando (botón 💬 abajo a la derecha).

> Si no querés pagar embeddings, poné `EMBEDDINGS_PROVIDER=huggingface` en `.env`: usa un modelo local gratuito (multilingüe). El LLM de las respuestas sí usa OpenAI.

## Insertar el chatbot en tu página

Pegá esta línea antes de `</body>` en cualquier sitio:

```html
<script src="http://localhost:8000/widget.js" data-api="http://localhost:8000" defer></script>
```

Cuando lo publiques, reemplazá `http://localhost:8000` por la URL de tu servidor. Opcional: `data-title="..."` cambia el título del chat.

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/chat` | `{ "question": "..." }` → `{ answer, sources }` |
| GET | `/widget.js` | El widget embebible |
| GET | `/` | Página demo |
| GET | `/health` | Estado |

## Cómo funciona (RAG)

1. **Ingesta:** el PDF se parte en fragmentos, se convierten en vectores (embeddings) y se guardan en FAISS.
2. **Consulta:** ante una pregunta, se buscan los fragmentos más parecidos y se le pasan al modelo como contexto.
3. **Respuesta:** el modelo responde **solo** con ese contexto y cita las páginas. Si algo no está en el manual, lo aclara en vez de inventar.

## Despliegue

Incluye `render.yaml` (Blueprint de Render). Ver la sección de despliegue: conectás el repo a Render, cargás `OPENAI_API_KEY` como variable de entorno secreta y listo. El índice se construye solo en el primer arranque si no existe.
