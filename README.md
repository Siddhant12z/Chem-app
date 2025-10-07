# ChemTutor: Voice-First Bilingual Organic Chemistry Tutor

A comprehensive bilingual (English-Nepali) organic chemistry tutoring system with voice capabilities, powered by local LLMs and RAG.

## Features

- 🧪 **Organic Chemistry Focus**: Specialized knowledge base with PDF documents and textbooks
- 🗣️ **Voice Interface**: Speech-to-text input and text-to-speech output with OpenAI integration
- 🌐 **Bilingual Support**: English-Nepali mixed responses with natural language switching
- 📚 **RAG Integration**: Retrieval Augmented Generation with FAISS vector search
- 🎨 **Modern UI**: Clean React-based chat interface with real-time streaming
- 🔊 **Streaming TTS**: Real-time text-to-speech as responses are generated
- 🧬 **Molecule Visualization**: Interactive chemical structure diagrams using RDKit
- 💾 **Chat Memory**: Persistent conversation history and context management

## Project Structure

```
chemtutor/
├── frontend/               # React frontend application
│   ├── public/
│   │   └── index.html     # Main HTML file
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── contexts/      # React contexts
│   │   ├── services/      # API services
│   │   ├── styles/        # CSS styling
│   │   └── utils/         # Utility functions
│   └── package.json       # Frontend dependencies
├── backend/               # Python Flask backend
│   ├── __init__.py
│   ├── app.py            # Main Flask application
│   ├── config.py         # Configuration settings
│   ├── models/           # Data models
│   ├── routes/           # API endpoints
│   ├── services/         # Business logic services
│   └── utils/            # Utility functions
├── rag-system/           # RAG implementation
│   ├── __init__.py
│   ├── indexer.py        # Document indexing
│   ├── retriever.py      # Document retrieval
│   ├── data/             # Knowledge base data
│   └── vectorstore/      # FAISS vector store
├── prompts/              # AI system prompts
│   └── system_prompt.txt # Main system prompt
├── docs/                 # Documentation
│   ├── API.md           # API documentation
│   └── DEPLOYMENT.md    # Deployment guide
├── scripts/              # Utility scripts
│   ├── setup.py         # Setup script
│   └── migrate.py       # Database migration
├── requirements.txt     # Python dependencies
├── pyproject.toml      # Python project configuration
├── .env.template       # Environment variables template
└── README.md           # This file
```

## Prerequisites

- **Python 3.10+**
- **OpenAI API key** (for voice services)
- **Ollama** running locally with models:
  - `qwen2.5:14b` or `mistral` (LLM)
  - `nomic-embed-text` (embeddings)

## Quick Start

### Automated Setup (Recommended)
```bash
python scripts/setup.py
```

This will:
- Check system requirements
- Create virtual environment
- Install dependencies
- Set up configuration files
- Pull Ollama models
- Create necessary directories

### Manual Setup

1. **Install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.template .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Pull Ollama models:**
   ```bash
   ollama pull qwen2.5:14b
   ollama pull nomic-embed-text
   ```

4. **Build knowledge base:**
   ```bash
   # Place PDF textbooks in rag-system/data/
   cd rag-system
   python indexer.py data/ --directory
   ```

5. **Start the server:**
   ```bash
   python backend/app.py
   ```

6. **Open the application:**
   Navigate to `http://localhost:8000` in your browser

## Usage

### Chat Interface
- **Text Input**: Type chemistry questions in the input field
- **Voice Input**: Click the microphone button to speak your question
- **Voice Output**: Responses are automatically spoken (toggle with speaker button)
- **Quick Questions**: Use the suggested question chips to get started

### Molecule Visualization
- Ask to "draw" or "show" a molecule structure
- Example: "Show me the structure of benzene"
- The system will generate 2D diagrams using RDKit

### Bilingual Features
- Responses include natural Nepali phrases mixed with English
- Example: "ठिक छ?" (Is that okay?), "राम्रो छ" (That's good)
- Helps make the learning experience more engaging for Nepali students

## Key Features

- 🧪 **Chemistry-Focused**: Grounded in organic chemistry textbooks
- 🗣️ **Voice Interface**: Full speech-to-text and text-to-speech support
- 🌐 **Bilingual**: Natural English-Nepali language mixing
- 📚 **RAG System**: Retrieves relevant context from knowledge base
- 🧬 **Molecule Drawing**: Generates chemical structure diagrams on demand
- 💾 **Chat Memory**: Maintains conversation context and history
- 🎨 **Modern UI**: Clean, responsive React interface

## Technical Stack

- **Backend**: Flask + Python 3.10+
- **Frontend**: React 18 with runtime JSX transpilation
- **LLM**: Ollama (Mistral 7B / Qwen 2.5 14B)
- **RAG**: FAISS vector search with LangChain
- **Embeddings**: Nomic Embed Text (local)
- **Voice**: OpenAI Whisper (STT) + OpenAI TTS
- **Chemistry**: RDKit for molecule visualization
- **Language**: Bilingual English-Nepali support

## Documentation

- [API Documentation](docs/API.md) - Complete API reference
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment instructions
- [Project Report](report.md) - Full technical dissertation

## Common Issues

### Backend Issues
- **RAG index not available**: Run `python rag-system/indexer.py rag-system/data/ --directory`
- **Ollama connection failed**: Ensure Ollama is running with `ollama serve`
- **Import errors**: Make sure virtual environment is activated

### Frontend Issues  
- **Blank screen**: Check browser console for errors, refresh page
- **RDKit load errors**: Non-blocking, will use fallback SVG rendering
- **Voice not working**: Verify `OPENAI_API_KEY` is set in `.env`

### Performance
- For faster inference, use a GPU-enabled setup
- For lower memory usage, use `mistral:7b` instead of `qwen2.5:14b`
- Adjust `RAG_TOP_K` in `.env` to control context size

## Development

### Project Structure
```
├── backend/          # Flask API server
│   ├── routes/      # API endpoints
│   ├── services/    # Business logic
│   └── utils/       # Helper functions
├── frontend/        # React frontend
│   └── src/        # Components, hooks, styles
├── rag-system/      # Document indexing & retrieval
├── prompts/         # LLM system prompts
├── docs/           # Documentation
└── scripts/        # Utility scripts
```

### Running Tests
```bash
# Coming soon
pytest tests/
```

### Contributing
Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with Ollama for local LLM inference
- Uses OpenAI APIs for voice services
- Powered by RDKit for chemistry visualization
- FAISS for efficient vector search


