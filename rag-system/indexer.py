"""
Document Indexer
Builds FAISS vector index from PDF documents
"""
import sys
from pathlib import Path
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import PyPDF2


class DocumentIndexer:
    """Handles document indexing for RAG"""
    
    def __init__(
        self,
        embed_model: str = "nomic-embed-text",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        self.embed_model = embed_model
        self.embeddings = OllamaEmbeddings(model=embed_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    def load_pdf(self, pdf_path: str) -> str:
        """
        Load text from a PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        text = []
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                print(f"Loading PDF: {pdf_path} ({len(pdf_reader.pages)} pages)")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text.append(page_text)
                
                print(f"Extracted {len(text)} pages of text")
        except Exception as e:
            print(f"Error loading PDF {pdf_path}: {e}")
            return ""
        
        return "\n\n".join(text)
    
    def load_pdf_directory(self, directory: str) -> List[tuple[str, str]]:
        """
        Load all PDFs from a directory
        
        Args:
            directory: Path to directory containing PDFs
            
        Returns:
            List of (filename, text) tuples
        """
        pdf_dir = Path(directory)
        if not pdf_dir.exists():
            print(f"Directory not found: {directory}")
            return []
        
        documents = []
        for pdf_file in pdf_dir.glob("*.pdf"):
            print(f"\nProcessing: {pdf_file.name}")
            text = self.load_pdf(str(pdf_file))
            if text:
                documents.append((pdf_file.name, text))
        
        return documents
    
    def chunk_documents(self, documents: List[tuple[str, str]]) -> List[str]:
        """
        Split documents into chunks
        
        Args:
            documents: List of (filename, text) tuples
            
        Returns:
            List of text chunks
        """
        all_chunks = []
        for filename, text in documents:
            chunks = self.text_splitter.split_text(text)
            print(f"  -> {len(chunks)} chunks from {filename}")
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def build_index(
        self,
        chunks: List[str],
        output_dir: str,
        metadatas: Optional[List[dict]] = None
    ) -> FAISS:
        """
        Build and save FAISS index from text chunks
        
        Args:
            chunks: List of text chunks
            output_dir: Directory to save the index
            metadatas: Optional metadata for each chunk
            
        Returns:
            FAISS vector store
        """
        print(f"\nBuilding FAISS index from {len(chunks)} chunks...")
        
        if metadatas:
            store = FAISS.from_texts(chunks, embedding=self.embeddings, metadatas=metadatas)
        else:
            store = FAISS.from_texts(chunks, embedding=self.embeddings)
        
        # Save index
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        store.save_local(str(output_path))
        
        print(f"✓ Saved FAISS index to: {output_path}")
        return store
    
    def index_pdf(self, pdf_path: str, output_dir: str) -> None:
        """
        Index a single PDF file
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save the index
        """
        text = self.load_pdf(pdf_path)
        if not text:
            print("No text extracted from PDF")
            return
        
        chunks = self.text_splitter.split_text(text)
        print(f"Created {len(chunks)} chunks")
        
        self.build_index(chunks, output_dir)
    
    def index_directory(self, pdf_dir: str, output_dir: str) -> None:
        """
        Index all PDFs in a directory
        
        Args:
            pdf_dir: Directory containing PDF files
            output_dir: Directory to save the index
        """
        documents = self.load_pdf_directory(pdf_dir)
        if not documents:
            print("No documents found to index")
            return
        
        print(f"\n📚 Found {len(documents)} PDF documents")
        chunks = self.chunk_documents(documents)
        print(f"\n📝 Total chunks: {len(chunks)}")
        
        # Create metadata for each chunk
        metadatas = []
        for filename, text in documents:
            doc_chunks = self.text_splitter.split_text(text)
            for i in range(len(doc_chunks)):
                metadatas.append({
                    "source": filename,
                    "chunk_index": i
                })
        
        self.build_index(chunks, output_dir, metadatas)


def main():
    """CLI entry point for indexing"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python indexer.py <pdf-file>")
        print("  python indexer.py <pdf-directory> --directory")
        sys.exit(1)
    
    indexer = DocumentIndexer()
    path = sys.argv[1]
    output_dir = "vectorstore"
    
    if "--directory" in sys.argv or Path(path).is_dir():
        print("📂 Indexing directory...")
        indexer.index_directory(path, output_dir)
    else:
        print("📄 Indexing single file...")
        indexer.index_pdf(path, output_dir)


if __name__ == "__main__":
    main()

