from langchain.text_splitter import CharacterTextSplitter

def chunk_text(text: str, size: int = 1000, overlap: int = 200):
    splitter = CharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        separator="\n"
    )
    return splitter.split_text(text)
