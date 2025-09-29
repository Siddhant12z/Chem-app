from flask import Flask, request, Response
from flask_cors import CORS
import requests
import json
import os
from pathlib import Path

# LangChain FAISS for RAG
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings

app = Flask(__name__)
CORS(app)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "mistral"
EMBED_MODEL = "nomic-embed-text"
INDEX_DIR = Path("local-pdf-rag/data/vector_index")

# Load FAISS index on startup if available
rag_store = None
if INDEX_DIR.exists():
    try:
        rag_store = FAISS.load_local(str(INDEX_DIR), OllamaEmbeddings(model=EMBED_MODEL),
                                     allow_dangerous_deserialization=True)
        print(f"[RAG] Loaded FAISS index from {INDEX_DIR}")
    except Exception as e:
        print(f"[RAG] Failed to load index: {e}")


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
    if rag_store is None:
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
        docs = rag_store.similarity_search(query, k=k)
    except Exception:
        docs = []
    context_blocks = []
    for idx, d in enumerate(docs):
        snippet = (d.page_content or "").strip().replace("\n", " ")
        snippet = snippet[:800]
        context_blocks.append(f"[{idx+1}] {snippet}")
    context_text = "\n\n".join(context_blocks) or "(no relevant context found)"

    system_prompt = (
        "You are Chem Tutor, an organic chemistry assistant. Use the provided context to answer the user's question. "
        "If the context is insufficient, say so and provide your best general explanation. Cite sources inline like [1], [2]. "
        "Format your response in GitHub-flavored Markdown with clear headings, subheadings, bullet lists, bold/italics, and code blocks when appropriate.\n\n"
        f"Context:\n{context_text}\n\n"
    )

    # Convert messages to Ollama format with a system message at the front
    chat_messages = [
        {"role": "system", "content": system_prompt},
    ]
    for m in messages:
        role = m.get("role")
        content = m.get("content")
        if role in ("user", "assistant"):
            chat_messages.append({"role": role, "content": content})

    def generate():
        try:
            for token in stream_ollama(chat_messages, model):
                yield token
            # Append Sources footer
            if context_blocks:
                yield "\n\nSources:\n" + "\n".join(context_blocks)
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    return Response(generate(), mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)


