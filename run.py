#!/usr/bin/env python3
"""
Simple startup script for ChemTutor
Adds project root to Python path and starts the backend
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import and run the app
from backend.app import create_app

if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print(" ChemTutor Backend Starting...")
    print("=" * 60)
    print(f" Server: http://localhost:8000")
    print(f" RAG System: Checking...")
    print(f" Voice Services: OpenAI TTS/STT")
    print(f" LLM: Local Ollama")
    print("=" * 60)
    print("\n Server is ready! Open http://localhost:8000 in your browser\n")
    
    app.run(host="0.0.0.0", port=8000, debug=True)

