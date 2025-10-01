from flask import Flask, request, Response
from flask_cors import CORS
import requests
import json
import os
from pathlib import Path

# LangChain FAISS for RAG
from langchain_community.vectorstores import FAISS
try:
    from langchain_ollama import OllamaEmbeddings
except ImportError:
    from langchain_community.embeddings import OllamaEmbeddings
try:
    from prompts.loader import load_system_prompt
except Exception:
    # Fallback: read prompt file directly without import/package
    def load_system_prompt(path: str = "prompts/system_prompt.txt") -> str:
        p = Path(path)
        if p.exists():
            try:
                return p.read_text(encoding="utf-8")
            except Exception:
                pass
        return (
            "You are **ChemTutor**, an AI assistant that helps students learn **Organic Chemistry**.\n"
            "Use only the provided CONTEXT; be concise; English first with very light Roman Nepali.\n"
            "If context is missing, state that briefly and ask one clarifying question."
        )

app = Flask(__name__)
CORS(app)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "mistral"
EMBED_MODEL = "nomic-embed-text"
INDEX_DIR = Path("local-pdf-rag/data/vector_index")

rag_store = None

def load_index_if_available():
    global rag_store
    if rag_store is not None:
        return rag_store
    if INDEX_DIR.exists():
        try:
            rag_store = FAISS.load_local(
                str(INDEX_DIR),
                OllamaEmbeddings(model=EMBED_MODEL),
                allow_dangerous_deserialization=True,
            )
            print(f"[RAG] Loaded FAISS index from {INDEX_DIR}")
        except Exception as e:
            print(f"[RAG] Failed to load index: {e}")
    return rag_store

# Attempt eager load at startup
load_index_if_available()


def stream_ollama(messages, model):
    payload = {
        "model": model or MODEL_NAME,
        "messages": messages,
        "stream": True,
    }
    with requests.post(OLLAMA_URL, json=payload, stream=True) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line.decode("utf-8"))
            except Exception:
                continue
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]
            if chunk.get("done"):
                break


@app.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    model = data.get("model", MODEL_NAME)

    def generate():
        try:
            for token in stream_ollama(messages, model):
                yield token
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    return Response(generate(), mimetype="text/plain")


@app.post("/api/rag-chat")
def api_rag_chat():
    store = load_index_if_available()
    if store is None:
        return Response("[RAG index not available]\n", mimetype="text/plain", status=200)

    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    model = data.get("model", MODEL_NAME)
    k = int(data.get("k", 4))

    # Extract latest user query
    user_messages = [m for m in messages if m.get("role") == "user"]
    query = user_messages[-1]["content"] if user_messages else ""

    # Retrieve relevant chunks
    try:
        docs = store.similarity_search(query, k=k)
    except Exception:
        docs = []
    context_blocks = []
    for idx, d in enumerate(docs):
        snippet = (d.page_content or "").strip().replace("\n", " ")
        snippet = snippet[:800]
        context_blocks.append(f"[{idx+1}] {snippet}")
    context_text = "\n\n".join(context_blocks) or "(no relevant context found)"

    # Load file-based system prompt and fill context + user query
    base_prompt = load_system_prompt()
    system_prompt = base_prompt.replace("{{context}}", context_text).replace("{{user_query}}", query)

    # Convert messages to Ollama format with a system message at the front
    chat_messages = [
        {"role": "system", "content": system_prompt},
    ]
    # Add a strict formatting controller to increase adherence
    formatting_rules = (
        "Output must be concise (<= 120 words) and use Markdown (a short heading or bullet list). "
        "Cite retrieved context inline like [1], [2] when relevant; if no context is relevant, state that briefly."
    )
    chat_messages.append({"role": "system", "content": formatting_rules})
    for m in messages:
        role = m.get("role")
        content = m.get("content")
        if role in ("user", "assistant"):
            chat_messages.append({"role": role, "content": content})

    def generate():
        try:
            for token in stream_ollama(chat_messages, model):
                # Pass-through token
                yield token
                # Detect fenced tool JSON and emit normalized event
                # Only process complete JSON objects, not partial tokens
                if token.strip().startswith("{") and token.strip().endswith("}") and '"tool"' in token and 'draw_molecule' in token:
                    # Wrap as event for frontend parser
                    try:
                        # ensure single-line json
                        compact = token.replace("\n", " ").strip()
                        evt_json = json.loads(compact)
                        # normalize to event shape
                        if 'items' in evt_json:
                            payload = {"type": "molecule", "items": evt_json.get('items', [])}
                        else:
                            payload = {"type": "molecule", "name": evt_json.get('name'), "smiles": evt_json.get('smiles')}
                        yield f"\n[EVENT]{json.dumps(payload)}\n"
                    except Exception as e:
                        # Log the error for debugging but don't break the stream
                        print(f"Error parsing tool JSON: {e}, token: {token}")
                        pass
            # Append Sources footer
            if context_blocks:
                yield "\n\nSources:\n" + "\n".join(context_blocks)
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    return Response(generate(), mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)


