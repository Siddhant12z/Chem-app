# ChemTutor Viva Questions and Answers (Expanded)

This document anticipates basic → advanced viva questions and provides concise, technically accurate answers with implementation detail where useful.

---

## A. Project Overview (Basics)

- **What is ChemTutor?**
  - A voice‑first, bilingual (English + Nepali) organic chemistry tutor. It uses RAG for grounded answers, renders molecular structures via RDKit, and streams responses with synchronized text‑to‑speech. It runs locally using Ollama for privacy and offline capability.

- **Key features and differentiators?**
  - Backend‑driven streaming (SSE) with sentence‑level TTS
  - RAG over curated PDFs using FAISS for reproducible, citeable answers
  - RDKit server‑side rendering (SVG/PNG) + curated/OPSIN name→SMILES resolution
  - Bilingual UX with minimal Devanagari inline phrases
  - OpenAI TTS and Browser TTS fallback (offline mode)

- **High‑level data flow?**
  1) User asks question → POST `/api/stream-chat`
  2) Backend collects memory + RAG context → streams LLM tokens
  3) Tokens buffered → complete sentences → emit `text` and per‑sentence `audio`
  4) Tool JSON detected (e.g., draw_molecule) → emit `molecule` events
  5) Frontend appends text, enqueues audio, renders molecules

---

## B. Retrieval Augmented Generation (RAG)

- **How is the knowledge base built? Why FAISS?**
  - PDFs → text extraction → chunking → embeddings (nomic‑embed‑text) → FAISS index (`rag-system/vectorstore/`).
  - FAISS is fast, local, file‑based, and simple to deploy for single‑node demos.

- **Chunking strategy and rationale?**
  - Overlapping fixed‑size chunks balance recall and latency. Overlap maintains continuity across sentences; chunk size tuned to LLM context window and domain language density.

- **Runtime retrieval pipeline?**
  - Query → embedding → FAISS top‑K → build a CONTEXT block with sources → prepend to conversation as system/context messages. The LLM is instructed to cite sources.

- **How to add or rebuild knowledge?**
  - Add: `python scripts/manage_rag.py add path/to.pdf`
  - Rebuild: `python scripts/manage_rag.py rebuild`
  - List/extract/clean are also supported for maintenance.

---

## C. LLM, Streaming, and Prompting

- **Which LLM and why local? Model selection?**
  - Default: Qwen 2.5 7B via Ollama. 7B provides good chemistry competence at lower memory than 14B. Switch in `backend/config.py` (`MODEL_NAME`).

- **Why Server‑Sent Events (SSE)?**
  - Unidirectional token streaming maps perfectly to LLM output. SSE is simpler than WebSockets, works through proxies, and needs less infra.

- **Sentence assembly and TTS timing?**
  - The backend buffers tokens and splits on `. ! ?`. On each completed sentence, it emits a `text` event and, if enabled, an `audio` event after synthesizing per‑sentence TTS. This achieves sub‑second time‑to‑first‑audio and keeps playback sequential.

- **Tool invocation detection?**
  - We scan the buffer for JSON blocks, including ```json‑fenced code. Valid draw_molecule JSON triggers a `molecule` SSE event. The detector tolerates partial and noisy streams.

- **Prompting style?**
  - System prompt fixes persona, bilingual rules (English primary; minimal Devanagari), citation format, and tool JSON schema. We keep prompts concise to reduce drift.

---

## D. TTS (Text‑to‑Speech) and Voice UX

- **Why backend TTS instead of frontend?**
  - Centralized sentence detection, consistent timing, and no duplicated logic. The frontend only plays audio chunks, avoiding reentrancy/race conditions.

- **Preventing overlap/echo?**
  - The frontend `useStreamingVoice` maintains a queue and a processing lock; it starts the next clip only on `onended` of the current one, with a small gap. This guarantees one‑at‑a‑time playback.

- **Nepali speech reliability?**
  - Voice selection prefers an OpenAI voice that pronounces Devanagari well (e.g., `fable`). Text preprocessing inserts boundaries between Latin and Devanagari to improve prosody.

- **Fallback when OpenAI TTS is unavailable or offline?**
  - Browser SpeechSynthesis (`useBrowserTTS`) provides free, offline TTS. A UI toggle switches modes. The backend disables TTS emission when browser mode is active.

---

## E. Molecule Rendering (RDKit) and Name→SMILES Resolution

- **Rendering path?**
  - Frontend requests `/api/draw-molecule` with `name` and/or `smiles`. Backend resolves a canonical SMILES (see below), then RDKit renders SVG/PNG and returns it.

- **Why were wrong diagrams observed before?**
  - LLM occasionally paired the right name with a wrong SMILES (e.g., ethanol with acetic acid). We used to draw whatever SMILES arrived. Now we resolve and validate.

- **Robust resolution strategy (implemented):**
  1) Curated dictionary (from PR + parsed Formulas.pdf) → SMILES
  2) OPSIN resolver (name → SMILES), cached
  3) Validate candidate SMILES from LLM via RDKit canonicalization
  - The SVG is annotated with a comment indicating the source: `curated | opsin | llm` for audits.

- **Client‑side safety net?**
  - If a known name is present, the frontend prefers curated SMILES over an LLM‑provided one when requesting a draw.

---

## F. Memory, Context, and Safety

- **How is chat memory managed?**
  - Rolling window: system + context (RAG) + trimmed history to fit token budgets. This avoids context overflow and retains recent turns.

- **Hallucination controls?**
  - RAG citations, instructing the model to use only provided context, and short, directive prompts. We display sources alongside answers.

---

## G. Deployment, Ops, and Health

- **How do I run locally?**
  - `python run.py` for the Flask backend; open `frontend/public/index.html`. Ensure Ollama is running and the FAISS index exists.

- **Health checks?**
  - `/api/health` returns status of RAG index, Ollama availability, and OpenAI key presence.

- **Common operational issues and fixes?**
  - OOM with 14B → switch to 7B in `config.py`
  - No tokens from LLM → check Ollama logs, model pull, and timeouts
  - RDKit not drawing → confirm `/api/draw-molecule` reachable; check SMILES validity
  - SSE stalls → ensure `text/event-stream` and no proxy buffering

---

## H. Security, Privacy, and Compliance

- **Privacy posture?**
  - LLM runs locally; embeddings and vector store are on disk. Optionally disable OpenAI calls (use browser TTS). Sanitization (DOMPurify) for rendered markdown.

- **Secrets and config?**
  - `.env` via `dotenv`; `backend/config.py` centralizes tunables. Keys never committed.

---

## I. Performance and Observability

- **Latency optimizations?**
  - Streaming + sentence‑level TTS for fast first audio; minimal prompt; top‑K tuned for recall vs context size.

- **Logging/metrics?**
  - LLMService logs first chunk keys, first token, token counts; StreamingService logs sentence extraction and event emission; molecule route logs failures.

---

## J. Detailed Q&A (Advanced)

- **Explain chunking parameters and why they matter.**
  - Size controls recall vs noise; overlap prevents semantic breaks across chunks; both tuned to the LLM’s effective context window. Too large reduces precision; too small increases fragmentation.

- **How do you canonicalize SMILES and why?**
  - RDKit `MolFromSmiles` → `MolToSmiles`. Canonical forms allow equality checks, caching, and stable rendering independent of input order/stereochemistry text.

- **How do you ensure the molecule matches the name?**
  - Lookup curated map; else OPSIN name→SMILES; else accept LLM SMILES if RDKit validates. SVG is annotated with `source:` for traceability.

- **What happens if the LLM emits partial or malformed tool JSON?**
  - The detector searches the entire buffer for complete `{...}` or ```json fenced blocks. Only complete, parseable JSON triggers events; partials are ignored until completed.

- **Why sentence‑by‑sentence TTS vs single long TTS?**
  - Much lower latency and better UX (conversational feel, interruptible). A single long TTS forces waiting for the entire response and is difficult to synchronize.

- **How do you avoid audio overlap precisely?**
  - A queue plus a processing lock: if `currentAudio` exists, we only enqueue; `onended` advances the queue with a small gap (100–200 ms) for natural flow.

- **How is bilingual output controlled?**
  - Prompt constrains Nepali to “minimal Devanagari” (1–2 words like “ठिक छ”, “बुझ्नुभयो?”) and keeps the main explanation in English.

- **Compare SSE and WebSockets here.**
  - SSE: HTTP/1, server→client only, easy, auto‑reconnect, good with proxies. WebSockets: full‑duplex, more boilerplate. For LLM token streaming (one‑way), SSE is simpler and sufficient.

- **Why Ollama over an API‑hosted LLM?**
  - Privacy, cost control, offline support. For demos and classrooms, local inference avoids data egress and unpredictable latency.

- **How would you scale this for many users?**
  - Move embeddings to a service (Chroma/pgvector), add a task queue for TTS, run multiple LLM workers, sticky sessions for SSE behind a proxy, and cache per‑query RAG results.

- **What tests would you write?**
  - Unit: sentence extractor, tool detector, curated/OPSIN resolver, SMILES validator.
  - Integration: `/api/stream-chat` happy path, molecule SVG route.
  - E2E: scripted conversations validating no audio overlap and correct molecule rendering for a set of names.

---

## K. Quick Commands (Memory Aids)

- Run backend: `python run.py`
- Build RAG: `python scripts/manage_rag.py rebuild`
- Add PDFs: `python scripts/manage_rag.py add file1.pdf file2.pdf`
- Curate name→SMILES from Formulas.pdf: `python scripts/manage_rag.py curate-smiles`
- Health: `GET /api/health`

---

## L. Possible Oral/Board Questions

- How would you handle ambiguous names (e.g., “butyl alcohol”)?
  - Resolve via OPSIN, prefer IUPAC names, prompt the user for disambiguation, and keep a synonym table mapping common names to unique SMILES.

- How do you prevent citation spam or irrelevant sources?
  - Limit to top‑K; filter low‑similarity hits; instruct model to cite only sources used; optionally verify by checking quoted spans.

- If OPSIN is offline, what happens?
  - We fall back to curated or validated SMILES. The source tag shows `llm` so we can spot potential mismatches.

- What are the security pitfalls of rendering markdown and SVG?
  - Use DOMPurify for markdown; for SVG, we control generation (RDKit) server‑side and never inject untrusted SVG directly from users.

- How would you internationalize beyond Nepali?
  - Abstract locale phrases and add language‑specific voice selection; keep minimal code in frontend, push rules to the system prompt.

---

## M. One‑slide Summary (if asked)

- Local LLM + FAISS RAG + RDKit + SSE + per‑sentence TTS
- Curated/OPSIN name→SMILES = correct diagrams
- Minimal Devanagari inline phrases for bilingual UX
- Offline/online TTS modes; no audio overlap
- Clean, modular backend; thin frontend

