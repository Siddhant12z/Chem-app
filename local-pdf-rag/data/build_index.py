import sys
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings

from pdf_loader import load_pdf_text
from text_chunking import chunk_text

EMBED_MODEL = "nomic-embed-text"
INDEX_DIR = "vector_index"

def build_index(pdf_path: str, index_dir: str = INDEX_DIR):
    text = load_pdf_text(pdf_path)
    chunks = chunk_text(text)
    

    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    store = FAISS.from_texts(chunks, embedding=embeddings)
    Path(index_dir).mkdir(parents=True, exist_ok=True)
    store.save_local(index_dir)
    print(f"Saved FAISS index to: {index_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python build_index.py <path-to-pdf>")
        sys.exit(1)
    build_index(sys.argv[1])
