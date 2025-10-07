# RAG Knowledge Base Management Guide

Complete guide for managing your ChemTutor knowledge base using command line.

---

## 🎯 Quick Start

### View Current Documents
```bash
python scripts/manage_rag.py list
```

### Add New Documents
```bash
python scripts/manage_rag.py add path/to/new-book.pdf
```

### Rebuild Index (After Changes)
```bash
python scripts/manage_rag.py rebuild
```

---

## 📚 Common Tasks

### 1. **Add New Knowledge (Single PDF)**

**Step 1:** Copy your PDF to the data directory
```bash
# Windows
copy "C:\path\to\new-chemistry-book.pdf" rag-system\data\

# Or just drag and drop the file into rag-system/data/ folder
```

**Step 2:** Rebuild the index
```bash
python scripts/manage_rag.py rebuild
```

**Step 3:** Restart the server
```bash
# Stop the current server (Ctrl+C)
# Start again
python run.py
```

✅ **Done!** Your new knowledge is now available.

---

### 2. **Add Multiple PDFs at Once**

```bash
# Add all PDFs from a folder
python scripts/manage_rag.py add book1.pdf book2.pdf book3.pdf

# Then rebuild
python scripts/manage_rag.py rebuild
```

---

### 3. **View All Documents in Knowledge Base**

```bash
python scripts/manage_rag.py list
```

**Example Output:**
```
============================================================
  Documents in Knowledge Base
============================================================

Found 3 PDF documents:

  - Formulas.pdf                 (113.1 KB)
  - org-chem.pdf                 (10,705.6 KB)
  - test.pdf                     (75.1 KB)

[TOTAL SIZE] 10.57 MB
```

---

### 4. **Extract Text from Specific Book**

```bash
# Extract text from a specific PDF
python scripts/manage_rag.py extract org-chem --output extracted.txt
```

This creates a text file with all the content from that book.

**Use Cases:**
- Review what's indexed
- Search for specific content
- Debug retrieval issues
- Create summaries

---

### 5. **Remove Specific Document**

**Step 1:** List documents to see filename
```bash
python scripts/manage_rag.py list
```

**Step 2:** Delete the PDF manually
```bash
# Windows
del rag-system\data\unwanted-book.pdf

# Or delete via File Explorer
```

**Step 3:** Rebuild index
```bash
python scripts/manage_rag.py rebuild
```

---

### 6. **Clean Everything (Start Fresh)**

⚠️ **WARNING: This deletes ALL PDFs and index!**

```bash
python scripts/manage_rag.py clean
```

You'll be asked to type `DELETE` to confirm.

**When to use:**
- Starting over with new curriculum
- Removing outdated content
- Debugging index issues

---

## 🔧 Advanced Usage

### Custom Chunk Size

Edit `rag-system/indexer.py` to change chunking:

```python
indexer = DocumentIndexer(
    chunk_size=1000,      # Larger chunks (more context)
    chunk_overlap=100     # More overlap (better continuity)
)
```

**Recommendations:**
- **Small chunks (300-500)**: Better for specific facts
- **Large chunks (800-1200)**: Better for explanations
- **More overlap (100-200)**: Better continuity, but slower

---

### Check Index Health

```bash
# After rebuilding, check the logs
python scripts/manage_rag.py rebuild
```

Look for:
```
[FOUND] X PDF documents
[TOTAL] Y chunks
✓ Saved FAISS index to: rag-system/vectorstore
```

---

### Update Configuration Path

If you moved files, update `backend/config.py`:

```python
RAG_INDEX_DIR = BASE_DIR / "rag-system" / "vectorstore"
```

---

## 📋 Step-by-Step Workflows

### Workflow 1: Adding New Textbook

```bash
# 1. Copy PDF
copy "Advanced-Organic-Chemistry.pdf" rag-system\data\

# 2. Check it's there
python scripts/manage_rag.py list

# 3. Rebuild index
python scripts/manage_rag.py rebuild

# 4. Verify success (should see "Successfully loaded FAISS index")
python run.py

# 5. Test in browser
# Ask: "What is in Advanced Organic Chemistry?"
```

---

### Workflow 2: Replacing Old Content

```bash
# 1. Remove old PDF
del rag-system\data\old-textbook.pdf

# 2. Add new PDF
copy "new-textbook.pdf" rag-system\data\

# 3. Rebuild
python scripts/manage_rag.py rebuild

# 4. Restart server
python run.py
```

---

### Workflow 3: Quality Check

```bash
# 1. List all documents
python scripts/manage_rag.py list

# 2. Extract text from each
python scripts/manage_rag.py extract org-chem --output check1.txt
python scripts/manage_rag.py extract formulas --output check2.txt

# 3. Review extracted files to ensure quality
notepad check1.txt

# 4. If text extraction is poor, try different PDF
```

---

## 🐛 Troubleshooting

### Issue: "RAG index not available"

**Solution:**
```bash
# Rebuild the index
python scripts/manage_rag.py rebuild

# Restart server
python run.py
```

---

### Issue: "No relevant context found"

**Possible causes:**
1. PDF text extraction failed (scanned images)
2. Query doesn't match indexed content
3. Embedding model not working

**Solution:**
```bash
# 1. Check PDFs are readable
python scripts/manage_rag.py extract your-pdf --output test.txt
notepad test.txt  # Should see actual text, not garbage

# 2. Verify Ollama embedding model
ollama list  # Should see "nomic-embed-text"

# 3. Rebuild index
python scripts/manage_rag.py rebuild
```

---

### Issue: Poor quality text extraction

**Symptoms:**
- Gibberish in extracted text
- Missing content
- Garbled characters

**Solution:**
1. **Use text-based PDFs** (not scanned images)
2. **OCR scanned PDFs** first using:
   - Adobe Acrobat Pro (OCR feature)
   - Online tools like smallpdf.com
3. **Use higher quality source files**

---

### Issue: Index is too large / slow

**Solution:**
```bash
# Reduce to essential documents only
python scripts/manage_rag.py list

# Remove unnecessary PDFs
del rag-system\data\extra-reference.pdf

# Rebuild with fewer docs
python scripts/manage_rag.py rebuild
```

---

## 💡 Best Practices

### 1. **Organize PDFs**
```
rag-system/data/
├── core-textbook.pdf       # Main reference (always keep)
├── formulas.pdf            # Quick reference
├── advanced-topics.pdf     # Supplementary
└── examples.pdf            # Practice problems
```

### 2. **Use Descriptive Filenames**
```
✅ Good: organic-chemistry-2024-morrison-boyd.pdf
❌ Bad: book1.pdf, download.pdf, untitled.pdf
```

### 3. **Verify Before Adding**
- ✅ Text-based PDF (not scanned image)
- ✅ Related to organic chemistry
- ✅ High quality content
- ✅ Reasonable size (< 50MB per file)

### 4. **Regular Maintenance**
```bash
# Monthly: Review and clean
python scripts/manage_rag.py list
# Remove outdated content
# Add new curriculum materials
python scripts/manage_rag.py rebuild
```

---

## 📊 Performance Tips

### Faster Indexing
```bash
# Use fewer chunks (larger chunk size)
# Edit rag-system/indexer.py:
chunk_size=800  # Instead of 500
```

### Better Retrieval
```bash
# In backend/config.py, adjust:
RAG_TOP_K = 5  # Retrieve more context (default: 3)
RAG_MAX_CONTEXT_LENGTH = 500  # Longer snippets (default: 300)
```

### Smaller Index
```bash
# Keep only essential books
python scripts/manage_rag.py list
# Remove extras, rebuild
```

---

## 🎓 For Your Demo

### Pre-Demo Checklist:

```bash
# 1. List current knowledge base
python scripts/manage_rag.py list

# 2. Verify index exists
dir rag-system\vectorstore\
# Should see: index.faiss, index.pkl

# 3. Test extraction
python scripts/manage_rag.py extract org-chem --output demo-check.txt

# 4. Verify all working
python run.py
# Open browser, ask test question
```

---

## 📝 Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `list` | Show all PDFs | `python scripts/manage_rag.py list` |
| `add` | Add new PDF(s) | `python scripts/manage_rag.py add book.pdf` |
| `rebuild` | Rebuild index | `python scripts/manage_rag.py rebuild` |
| `extract` | Get text from PDF | `python scripts/manage_rag.py extract org-chem` |
| `clean` | Delete everything | `python scripts/manage_rag.py clean` |

---

## 🚀 Quick Commands for Demo Day

```bash
# Show what's in the knowledge base
python scripts/manage_rag.py list

# Verify specific content
python scripts/manage_rag.py extract formulas --output formulas.txt

# If something's wrong, quick fix:
python scripts/manage_rag.py rebuild
python run.py
```

---

## 🆘 Emergency Recovery

If everything breaks:

```bash
# 1. Backup current PDFs (if any good ones)
copy rag-system\data\*.pdf backup\

# 2. Clean everything
python scripts/manage_rag.py clean
# Type: DELETE

# 3. Re-add PDFs
copy backup\*.pdf rag-system\data\

# 4. Rebuild from scratch
python scripts/manage_rag.py rebuild

# 5. Test
python run.py
```

---

## 📞 Getting Help

Run any command with `--help`:
```bash
python scripts/manage_rag.py --help
python scripts/manage_rag.py add --help
python scripts/manage_rag.py extract --help
```

---

**Your RAG system is now fully manageable from the command line!** 🎉

