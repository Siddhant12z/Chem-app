# ChemTutor Architecture & Technologies

## High-Level Architecture

```
User ─▶ Frontend (React via CDN)
        ├─ useSSEChat (SSE client)
        ├─ useStreamingVoice (audio queue)
        └─ useBrowserTTS (fallback)
            │
            ▼
Backend (Flask)
├─ routes/streaming.py  (SSE endpoint)
├─ services/streaming_service.py
│  ├─ LLMService.stream_chat (Ollama)
│  ├─ Sentence buffering → text events
│  ├─ Per‑sentence TTS → audio events
│  └─ Tool detection → molecule events
├─ services/rag_service.py (FAISS retrieval)
├─ routes/molecule.py (RDKit SVG)
└─ routes/voice.py (OpenAI TTS/STT)
```

Data/Control Flow:
1. Frontend posts messages to `/api/stream-chat`.
2. Backend builds messages with RAG context + memory.
3. LLM streams tokens (Ollama). Backend buffers into sentences.
4. For each sentence: emit `text` (UI), synthesize `audio` (if OpenAI TTS mode), detect tools.
5. Frontend appends text, plays audio queue sequentially, renders molecules.

## Key Components

### 1) Streaming Service (Backend)
- In `services/streaming_service.py`.
- Responsibilities:
  - Glue for LLM → events → frontend.
  - Robust sentence extraction; text cleaning for TTS.
  - Detect JSON tool blocks anywhere in stream (supports ```json fences).

### 2) SSE Endpoint (Backend)
- In `routes/streaming.py`.
- Streams `text`, `audio`, `molecule`, `done` events with `text/event-stream`.
- Disables backend TTS when `tts_mode: "browser"` to avoid duplicate speech.

### 3) Frontend Hooks
- `useSSEChat.js`: Manages POST streaming; parses SSE; dispatches to handlers.
- `useStreamingVoice.js`: Plays base64 MP3 chunks sequentially with a processing lock (no overlap).
- `useBrowserTTS.js`: SpeechSynthesis fallback with queue and voice selection.

### 4) RAG
- PDFs → chunks → embeddings (nomic‑embed‑text) → FAISS.
- Retrieval joins system prompt + context + rolling history.

### 5) RDKit
- `routes/molecule.py`: SMILES → SVG via RDKit.
- Frontend `MoleculeCard` requests SVG; auto‑fallback to simple SVG if backend fails.

## Technologies & Rationale

- **Flask**: Lightweight Python web framework; easy blueprints and streaming.
- **Server-Sent Events (SSE)**: Simple, robust unidirectional streaming; ideal for token/line streams.
- **Ollama**: Local LLM runtime; private, configurable models; HTTP streaming API.
- **Qwen 2.5 7B**: Balanced performance vs memory usage; good general chemistry knowledge.
- **FAISS**: Fast, local vector search; file‑based persistence; trivial deployment.
- **RDKit**: Industry-standard cheminformatics toolkit; SVG output for web.
- **OpenAI TTS + Whisper**: High‑quality TTS/STT; replaced or bypassed by Browser TTS as needed.
- **Browser SpeechSynthesis**: Free/offline fallback; ensures demo resilience.
- **React (CDN + Babel)**: Zero-build dev loop; components defined as inline scripts for simplicity.
- **DOMPurify + Marked**: Safe markdown rendering; prevents XSS.

## Configuration
- `backend/config.py`:
  - `MODEL_NAME`, `OLLAMA_URL`, `LLM_TEMPERATURE`
  - `RAG_INDEX_DIR`, `RAG_TOP_K`
  - `OPENAI_TTS_MODEL`, `OPENAI_DEFAULT_VOICE`
  - `PORT`, `DEBUG`

## Health & Observability
- `routes/health.py` exposes health endpoints: RAG available, Ollama reachable, OpenAI key present.
- Extensive logging in LLM service and streaming service (first chunk, token counts, errors).

## Failure Modes & Mitigations
- Ollama OOM → switch to 7B model; timeouts; retry guidance in logs.
- OpenAI TTS outage → Browser TTS mode.
- Missing RAG index → `scripts/manage_rag.py rebuild`.
- RDKit route failure → client simple SVG fallback.

## Extensibility
- Add tools: parse new JSON blocks and emit events.
- Swap LLM: change `MODEL_NAME`, adjust prompt.
- Swap embeddings: update indexer; rebuild FAISS.
- UI build system: migrate to a bundler if needed; CDN approach keeps setup minimal.

## Security & Privacy
- Local LLM + local FAISS by default (no data leaves machine).
- Sanitized HTML rendering; CORS limited to expected origins (configurable).
- API keys loaded from environment via `dotenv`.

## Deployment Notes
- Start order: FAISS index present → Ollama running → `python run.py`.
- Windows console may require avoiding emojis (fixed already in code).
- For production: run via WSGI server (gunicorn/uvicorn + ASGI wrapper) and reverse proxy; keep SSE buffering disabled at proxy.
