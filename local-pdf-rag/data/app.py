import sys
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings


INDEX_DIR = "vector_index"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "mistral"


def load_index(index_dir: str = INDEX_DIR) -> FAISS:
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    return FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)


def answer(query: str, k: int = 4) -> str:
    index = load_index()
    retriever = index.as_retriever(search_kwargs={"k": k})
    docs = retriever.get_relevant_documents(query)
    context = "\n\n".join(d.page_content for d in docs)
    prompt = f"""
You are a helpful assistant. Use the provided context to answer the question.

Context:
{context}

Question: {query}
Answer concisely.
""".strip()

    llm = Ollama(model=LLM_MODEL)
    return llm.invoke(prompt)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app.py \"<question>\"")
        sys.exit(1)
    print(answer(sys.argv[1]))


