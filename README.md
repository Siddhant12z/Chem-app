Chem Tutor (Ollama + RAG)
=========================

A lightweight organic chemistry tutor UI backed by a local Ollama model (Mistral) with FAISS-based RAG over your PDFs.

Project layout
--------------
- `chat-ui/` Static React UI (CDN) — open `index.html` in a browser.
- `server/ollama_proxy.py` Flask proxy that streams responses from Ollama.
- `local-pdf-rag/data/` FAISS index and PDF docs.

Prerequisites
-------------
- Python 3.10+
- Ollama running locally with models:
  - `mistral`
  - `nomic-embed-text`

Setup
-----
```bash
pip install -r requirements.txt  # or install inline deps below
# or: pip install flask flask-cors requests langchain-community
python server/ollama_proxy.py
```
Open `chat-ui/index.html` in your browser and chat.

Notes
-----
- RAG loads FAISS from `local-pdf-rag/data/vector_index`.
- Responses are streamed as Markdown and rendered in the UI.
- PDFs and indexes are gitignored by default.


