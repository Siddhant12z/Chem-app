# ChemTutor Codebase Tour

This document walks through the repository structure, describing what each folder and important file contains, and why it exists.

```
final-chem/
├─ backend/
│  ├─ app.py
│  ├─ config.py
│  ├─ __init__.py
│  ├─ routes/
│  │  ├─ __init__.py
│  │  ├─ chat.py
│  │  ├─ health.py
│  │  ├─ molecule.py
│  │  ├─ streaming.py
│  │  └─ voice.py
│  └─ services/
│     ├─ chat_memory.py
│     ├─ llm_service.py
│     ├─ molecule_drawer.py
│     ├─ rag_service.py
│     ├─ streaming_service.py
│     └─ voice_service.py
│
├─ frontend/
│  ├─ package.json
│  ├─ public/
│  │  └─ index.html
│  └─ src/
│     ├─ components/
│     │  ├─ AppShell.js
│     │  ├─ ComposerArea.js
│     │  ├─ ConfirmModal.js
│     │  ├─ MainPane.js
│     │  ├─ MessageList.js
│     │  ├─ Sidebar.js
│     │  ├─ StatusBar.js
│     │  └─ TTSModeSelector.js
│     ├─ contexts/ChatContext.js
│     ├─ hooks/
│     │  ├─ useBrowserTTS.js
│     │  ├─ useSSEChat.js
│     │  └─ useStreamingVoice.js
│     ├─ services/apiService.js
│     ├─ styles/{globals.css,tokens.css}
│     └─ utils/{nepaliHelpers.js,toast.js}
│
├─ rag-system/
│  ├─ __init__.py
│  ├─ data/                # PDFs
│  ├─ indexer.py           # Build FAISS vector index
│  └─ vectorstore/{index.faiss,index.pkl}
│
├─ prompts/
│  ├─ loader.py
│  └─ system_prompt.txt
│
├─ scripts/
│  └─ manage_rag.py        # CLI for RAG (add/list/rebuild/extract/clean)
│
├─ README.md
├─ requirements.txt
├─ run.py
└─ VIVA_QA.md, CODEBASE_TOUR.md, ARCHITECTURE_TECH.md
```

## Top Level
- **run.py**: Entrypoint to start Flask app with proper `PYTHONPATH`. Use this on Windows to avoid import issues.
- **requirements.txt**: Python dependencies (Flask, RDKit, FAISS, OpenAI, etc.).
- **README.md**: Setup, usage, troubleshooting.

## Backend
- **backend/app.py**: Creates Flask app, applies config, registers blueprints via `backend.routes.register_routes(app)`.
- **backend/config.py**: Central configuration (paths, models, ports, RAG params, OpenAI keys, etc.). Change `MODEL_NAME`, `RAG_INDEX_DIR`, TTS model/voice here.

### Routes
- **routes/__init__.py**: Registers all routes: chat, voice (TTS/STT), molecule (RDKit), health, streaming.
- **routes/chat.py**: Basic chat / RAG chat endpoints (non‑SSE), useful for debugging or simple calls.
- **routes/streaming.py**: SSE endpoint `/api/stream-chat`. Reads request, builds context, streams events from `StreamingService` (text, audio, molecule, complete).
- **routes/molecule.py**: `/api/draw-molecule` SVG rendering using RDKit. Used by the frontend `MoleculeCard`.
- **routes/voice.py**: `/api/tts` (OpenAI TTS) and `/api/stt` (Whisper) helpers.
- **routes/health.py**: `/api/health` and `/api/test` for liveness and dependency health (RAG, Ollama, OpenAI).

### Services
- **services/streaming_service.py**: Core streaming pipeline:
  - Consumes tokens from `LLMService.stream_chat`
  - Buffers into sentences; emits SSE `text`
  - Per‑sentence TTS (if enabled) → emits `audio`
  - Scans buffer for JSON tool calls → emits `molecule`
  - Sends `complete` with full text at end
- **services/llm_service.py**: Talks to Ollama `/api/chat` with `stream: true`; robust parsing & logging; `detect_tool_usage` finds draw_molecule JSON (supports ```json fences).
- **services/rag_service.py**: Loads FAISS index; `retrieve_context(query, k)` returns top‑K chunks + references.
- **services/voice_service.py**: OpenAI TTS/STT wrappers; Nepali detection and voice selection (`fable`); text cleaning for prosody.
- **services/molecule_drawer.py**: RDKit core (SMILES → SVG) used by `routes/molecule.py`.
- **services/chat_memory.py**: Rolling conversation memory, builds system+context+history messages.

## Frontend
- **public/index.html**: Entry HTML using CDN React + Babel; loads hooks/components via `<script type="text/babel">`.

### Hooks
- **hooks/useSSEChat.js**: Manages POST + streamed response; parses SSE blocks; dispatches to handlers for `text`, `audio`, `molecule`, `done`.
- **hooks/useStreamingVoice.js**: Audio queue with processing lock; plays base64 MP3 sequentially (no overlap).
- **hooks/useBrowserTTS.js**: Free/offline TTS using SpeechSynthesis; sequential queue; mode used when toggled.

### Components
- **AppShell.js**: Top‑level shell; wires chat state + SSE + audio (passes `ttsMode`, routes text events to browser TTS when enabled).
- **MainPane.js**: Chat UI; composer + message list; sends messages; switches TTS modes.
- **ComposerArea.js**: Input row + quick chips; `TTSModeSelector` toggle.
- **MessageList.js**: Renders messages with markdown, references, and molecule attachments (`MoleculeCard`).
- **TTSModeSelector.js**: Dropdown to choose OpenAI vs Browser TTS.

### Utilities
- **services/apiService.js**: Fetch wrappers for backend API.
- **styles/**: Global and tokens CSS.
- **utils/**: Helpers (Nepali text, toasts).

## RAG System
- **rag-system/indexer.py**: PDF → text chunks → embeddings → FAISS. Prints progress; saves `index.faiss` and `index.pkl`.
- **scripts/manage_rag.py**: CLI to manage the index (list/add/rebuild/extract/clean). Use this for maintenance.

## Prompts
- **prompts/system_prompt.txt**: Tutor persona, bilingual constraints (English first, minimal Devanagari), and tool use format.
- **prompts/loader.py**: Convenience loader with fallback if file is missing.

## Why This Structure?
- Clear separation: backend (SSE/TTS/RAG) vs frontend (render/audio).
- Testability: services are small, focused units.
- Reliability: backend centralizes timing and tools; frontend is a thin event consumer.
- Flexibility: swap LLM, embeddings, TTS voices, or add tools with minimal coupling.
