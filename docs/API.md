# ChemTutor API Documentation

## Base URL
```
http://localhost:8000/api
```

## Endpoints

### Health Check

#### GET `/api/health`
Check if the server is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "chemtutor-backend"
}
```

#### GET `/api/test`
Test endpoint with version information.

**Response:**
```json
{
  "message": "ChemTutor server is working!",
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### Chat Endpoints

#### POST `/api/chat`
Basic chat without RAG (Retrieval Augmented Generation).

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "What is organic chemistry?"}
  ],
  "model": "qwen2.5:14b"
}
```

**Response:**
Streaming plain text response from the LLM.

---

#### POST `/api/rag-chat`
Chat with RAG - retrieves relevant context from the knowledge base.

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "What is an electrophile?"}
  ],
  "model": "qwen2.5:14b",
  "k": 3,
  "chat_id": "session-123"
}
```

**Parameters:**
- `messages` (required): Array of message objects
- `model` (optional): LLM model name (default: "qwen2.5:14b")
- `k` (optional): Number of context chunks to retrieve (default: 3)
- `chat_id` (optional): Session ID for conversation memory (default: "default")

**Response:**
Streaming plain text with:
- Answer from LLM based on retrieved context
- `[EVENT]{...}` markers for tool invocations (e.g., molecule drawings)
- Sources section at the end with references

**Example Response:**
```
An electrophile is a reagent that is attracted to electrons...

[EVENT]{"type":"molecule","name":"water","smiles":"O"}

Sources:
[1] Organic Chemistry Textbook, page 45
[2] Chemical Reactions Reference
```

---

### Voice Endpoints

#### POST `/api/tts`
Convert text to speech using OpenAI TTS.

**Request Body:**
```json
{
  "text": "Hello, this is ChemTutor!",
  "voice_id": "nova"
}
```

**Parameters:**
- `text` (required): Text to convert to speech
- `voice_id` (optional): Voice ID (alloy, echo, fable, onyx, nova, shimmer)

**Response:**
```json
{
  "success": true,
  "audio_data": "base64_encoded_mp3_data...",
  "voice_used": "nova"
}
```

---

#### POST `/api/stt`
Convert speech to text using OpenAI Whisper.

**Request:**
- Multipart form data with `audio` file field
- Supported formats: webm, mp3, wav, etc.

**Response:**
```json
{
  "success": true,
  "transcript": "What is organic chemistry?"
}
```

---

#### GET `/api/voices`
Get list of available TTS voices.

**Response:**
```json
{
  "success": true,
  "voices": [
    {
      "voice_id": "alloy",
      "name": "Alloy",
      "category": "neural",
      "description": "Neutral, balanced voice"
    },
    ...
  ]
}
```

---

### Molecule Endpoints

#### POST `/api/draw-molecule`
Generate molecule diagram from SMILES string.

**Request Body:**
```json
{
  "smiles": "c1ccccc1",
  "name": "benzene",
  "format": "svg",
  "width": 300,
  "height": 300
}
```

**Parameters:**
- `smiles` (required): SMILES notation of the molecule
- `name` (optional): Name of the molecule
- `format` (optional): Output format ("svg" or "base64", default: "svg")
- `width` (optional): Image width in pixels (default: 300)
- `height` (optional): Image height in pixels (default: 300)

**Response:**
- If `format=svg`: SVG image (Content-Type: image/svg+xml)
- If `format=base64`: Base64-encoded PNG image (Content-Type: text/plain)

---

#### POST `/api/molecule-info`
Get information about a molecule from SMILES.

**Request Body:**
```json
{
  "smiles": "CCO"
}
```

**Response:**
```json
{
  "success": true,
  "smiles": "CCO",
  "formula": "C2H6O",
  "molecular_weight": 46.07,
  "num_atoms": 9,
  "num_bonds": 8
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message description",
  "success": false
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (missing required parameters)
- `500` - Internal Server Error

---

## CORS

All API endpoints support CORS with the following configuration:
- **Allowed Origins:** `*` (configurable via environment)
- **Allowed Methods:** GET, POST, OPTIONS
- **Allowed Headers:** Content-Type, Authorization

---

## Rate Limiting

Currently, no rate limiting is implemented. For production deployment, consider adding rate limiting middleware.

---

## Authentication

Currently, no authentication is required. For production deployment with external APIs (OpenAI), ensure proper API key management and consider adding user authentication.

