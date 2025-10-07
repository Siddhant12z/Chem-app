#!/usr/bin/env python3
"""
RAG Knowledge Base Management Tool
Manage PDFs and vector index for ChemTutor
"""
import sys
import argparse
import json
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path is set
def _load_indexer_class():
    """Lazy-load DocumentIndexer to avoid requiring PyPDF2 when not needed."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("indexer", project_root / "rag-system" / "indexer.py")
    indexer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(indexer_module)
    return indexer_module.DocumentIndexer


def add_documents(pdf_paths, output_dir="rag-system/vectorstore"):
    """Add new PDFs to the knowledge base"""
    print("\n" + "=" * 60)
    print("  Adding Documents to Knowledge Base")
    print("=" * 60)
    
    DocumentIndexer = _load_indexer_class()
    indexer = DocumentIndexer()
    
    # Process each PDF
    documents = []
    for pdf_path in pdf_paths:
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            print(f"[ERROR] File not found: {pdf_path}")
            continue
        
        print(f"\n[PROCESSING] {pdf_file.name}")
        text = indexer.load_pdf(str(pdf_file))
        if text:
            documents.append((pdf_file.name, text))
    
    if not documents:
        print("\n[ERROR] No valid documents to add!")
        return
    
    # Chunk and index
    chunks = indexer.chunk_documents(documents)
    print(f"\n[TOTAL] {len(chunks)} chunks to add")
    
    # Create metadata
    metadatas = []
    for filename, text in documents:
        doc_chunks = indexer.text_splitter.split_text(text)
        for i in range(len(doc_chunks)):
            metadatas.append({
                "source": filename,
                "chunk_index": i
            })
    
    # Build index
    indexer.build_index(chunks, output_dir, metadatas)
    
    print("\n[SUCCESS] Documents added to knowledge base!")
    print(f"[LOCATION] {output_dir}")


def rebuild_index(pdf_dir="rag-system/data", output_dir="rag-system/vectorstore"):
    """Rebuild the entire index from scratch"""
    print("\n" + "=" * 60)
    print("  Rebuilding Knowledge Base from Scratch")
    print("=" * 60)
    
    DocumentIndexer = _load_indexer_class()
    indexer = DocumentIndexer()
    
    # Load all PDFs
    documents = indexer.load_pdf_directory(pdf_dir)
    
    if not documents:
        print(f"\n[ERROR] No PDFs found in {pdf_dir}")
        return
    
    print(f"\n[FOUND] {len(documents)} PDF documents")
    
    # Chunk documents
    chunks = indexer.chunk_documents(documents)
    print(f"\n[TOTAL] {len(chunks)} chunks")
    
    # Create metadata
    metadatas = []
    for filename, text in documents:
        doc_chunks = indexer.text_splitter.split_text(text)
        for i in range(len(doc_chunks)):
            metadatas.append({
                "source": filename,
                "chunk_index": i
            })
    
    # Build index
    indexer.build_index(chunks, output_dir, metadatas)
    
    print("\n[SUCCESS] Knowledge base rebuilt!")
    print(f"[LOCATION] {output_dir}")


def list_documents(data_dir="rag-system/data"):
    """List all PDFs in the knowledge base"""
    print("\n" + "=" * 60)
    print("  Documents in Knowledge Base")
    print("=" * 60)
    
    pdf_dir = Path(data_dir)
    if not pdf_dir.exists():
        print(f"\n[ERROR] Directory not found: {data_dir}")
        return
    
    pdfs = list(pdf_dir.glob("*.pdf"))
    
    if not pdfs:
        print(f"\n[INFO] No PDF documents found in {data_dir}")
        return
    
    print(f"\nFound {len(pdfs)} PDF documents:\n")
    
    total_size = 0
    for pdf in sorted(pdfs):
        size = pdf.stat().st_size / 1024  # KB
        total_size += size
        print(f"  - {pdf.name:<30} ({size:,.1f} KB)")
    
    print(f"\n[TOTAL SIZE] {total_size / 1024:.2f} MB")


def clean_all(data_dir="rag-system/data", index_dir="rag-system/vectorstore"):
    """Remove all documents and index (WARNING: Destructive!)"""
    print("\n" + "=" * 60)
    print("  WARNING: Clean All Knowledge Base")
    print("=" * 60)
    
    print("\nThis will DELETE:")
    print(f"  1. All PDFs in {data_dir}")
    print(f"  2. All index files in {index_dir}")
    
    confirm = input("\nType 'DELETE' to confirm: ")
    
    if confirm != "DELETE":
        print("\n[CANCELLED] Operation cancelled")
        return
    
    import shutil
    
    # Remove PDFs
    pdf_dir = Path(data_dir)
    if pdf_dir.exists():
        for pdf in pdf_dir.glob("*.pdf"):
            pdf.unlink()
            print(f"[DELETED] {pdf.name}")
    
    # Remove index
    index_path = Path(index_dir)
    if index_path.exists():
        shutil.rmtree(index_path)
        index_path.mkdir(parents=True)
        print(f"[DELETED] Index directory")
    
    print("\n[SUCCESS] Knowledge base cleaned!")


def extract_by_source(source_name, data_dir="rag-system/data", output_file="extracted.txt"):
    """Extract all text from a specific source document"""
    print("\n" + "=" * 60)
    print(f"  Extracting Text from: {source_name}")
    print("=" * 60)
    
    DocumentIndexer = _load_indexer_class()
    indexer = DocumentIndexer()
    
    # Find the PDF
    pdf_dir = Path(data_dir)
    pdf_files = list(pdf_dir.glob(f"*{source_name}*"))
    
    if not pdf_files:
        print(f"\n[ERROR] No PDF found matching: {source_name}")
        print(f"[HINT] Available files:")
        for pdf in pdf_dir.glob("*.pdf"):
            print(f"  - {pdf.name}")
        return
    
    pdf_file = pdf_files[0]
    print(f"\n[FOUND] {pdf_file.name}")
    
    # Extract text
    text = indexer.load_pdf(str(pdf_file))
    
    if not text:
        print("\n[ERROR] Failed to extract text")
        return
    
    # Save to file
    output_path = Path(output_file)
    output_path.write_text(text, encoding='utf-8')
    
    print(f"\n[SUCCESS] Text extracted!")
    print(f"[OUTPUT] {output_file}")
    print(f"[SIZE] {len(text):,} characters")
    print(f"[LINES] {text.count(chr(10)):,} lines")


def main():
    parser = argparse.ArgumentParser(
        description="Manage ChemTutor RAG Knowledge Base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all documents
  python scripts/manage_rag.py list

  # Add new PDF to knowledge base
  python scripts/manage_rag.py add path/to/new-book.pdf

  # Add multiple PDFs
  python scripts/manage_rag.py add book1.pdf book2.pdf book3.pdf

  # Rebuild entire index (after adding/removing PDFs)
  python scripts/manage_rag.py rebuild

  # Extract text from a specific book
  python scripts/manage_rag.py extract org-chem --output extracted.txt

  # Clean everything (WARNING: Deletes all data!)
  python scripts/manage_rag.py clean
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all PDFs in knowledge base')
    list_parser.add_argument('--data-dir', default='rag-system/data', help='PDF data directory')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add new PDFs to knowledge base')
    add_parser.add_argument('pdf_files', nargs='+', help='PDF files to add')
    add_parser.add_argument('--output', default='rag-system/vectorstore', help='Output directory for index')
    
    # Rebuild command
    rebuild_parser = subparsers.add_parser('rebuild', help='Rebuild entire index from scratch')
    rebuild_parser.add_argument('--data-dir', default='rag-system/data', help='PDF data directory')
    rebuild_parser.add_argument('--output', default='rag-system/vectorstore', help='Output directory for index')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract text from a specific document')
    extract_parser.add_argument('source', help='Source document name (partial match)')
    extract_parser.add_argument('--data-dir', default='rag-system/data', help='PDF data directory')
    extract_parser.add_argument('--output', default='extracted.txt', help='Output text file')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Remove all documents and index')
    clean_parser.add_argument('--data-dir', default='rag-system/data', help='PDF data directory')
    clean_parser.add_argument('--index-dir', default='rag-system/vectorstore', help='Index directory')
    
    # Curate SMILES command
    curate_parser = subparsers.add_parser('curate-smiles', help='Parse Formulas.pdf and create curated_smiles_extra.json')
    curate_parser.add_argument('--pdf', default=str(project_root / 'rag-system' / 'data' / 'Formulas.pdf'), help='Formulas PDF path')
    curate_parser.add_argument('--out', default=str(project_root / 'backend' / 'services' / 'curated_smiles_extra.json'), help='Output JSON path')

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'list':
            list_documents(args.data_dir)
        
        elif args.command == 'add':
            add_documents(args.pdf_files, args.output)
        
        elif args.command == 'rebuild':
            rebuild_index(args.data_dir, args.output)
        
        elif args.command == 'extract':
            extract_by_source(args.source, args.data_dir, args.output)
        
        elif args.command == 'clean':
            clean_all(args.data_dir, args.index_dir)
        
        elif args.command == 'curate-smiles':
            parse_formulas_to_curated(args.pdf, args.out)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def parse_formulas_to_curated(pdf_path: str, out_path: str):
    """
    Parse a formulas PDF for lines like "Name (SMILES)" or "Name — SMILES" and write a curated JSON.
    Requires PyMuPDF for best results; falls back to reading raw text if possible.
    """
    pdf = Path(pdf_path)
    if not pdf.exists():
        print(f"[ERROR] PDF not found: {pdf}")
        return

    text = None
    try:
        import fitz  # PyMuPDF
        with fitz.open(pdf) as doc:
            pages = [p.get_text("text") for p in doc]
        text = "\n".join(pages)
        print(f"[OK] Extracted text from {pdf.name} using PyMuPDF")
    except Exception:
        try:
            text = pdf.read_text(encoding="utf-8", errors="ignore")
            print(f"[WARN] PyMuPDF not available; using raw text read (may be incomplete)")
        except Exception:
            print("[ERROR] Unable to extract text. Install PyMuPDF: pip install pymupdf")
            return

    if not text or len(text) < 100:
        print("[ERROR] No text extracted from PDF")
        return

    patterns = [
        re.compile(r"(^|\n)\s*([A-Za-z][A-Za-z0-9\-\s]+?)\s*[\(\[\{]\s*([A-Za-z0-9@+\-=#\[\]\/\\]+)\s*[\)\]\}]", re.M),
        re.compile(r"(^|\n)\s*([A-Za-z][A-Za-z0-9\-\s]+?)\s*[—\-:]\s*([A-Za-z0-9@+\-=#\[\]\/\\]+)", re.M),
    ]

    pairs: dict[str, str] = {}

    for pat in patterns:
        for m in pat.finditer(text):
            name = m.group(2).strip().lower()
            smiles = m.group(3).strip()
            # Basic sanity: SMILES-like tokens often contain bracket/bond symbols; also trim overly long weird tokens
            if re.search(r"[=#\[\]\\/]", smiles) or len(smiles) <= 25:
                pairs[name] = smiles

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(pairs, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] Curated SMILES file written: {out_file} ({len(pairs)} entries)")


if __name__ == "__main__":
    main()

