from flask import Flask, request, Response
from flask_cors import CORS
import requests
import json
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LangChain FAISS for RAG
from langchain_community.vectorstores import FAISS
try:
    from langchain_ollama import OllamaEmbeddings
except ImportError:
    from langchain_community.embeddings import OllamaEmbeddings
try:
    from prompts.loader import load_system_prompt
except Exception:
    # Fallback: read prompt file directly without import/package
    def load_system_prompt(path: str = "prompts/system_prompt.txt") -> str:
        p = Path(path)
        if p.exists():
            try:
                return p.read_text(encoding="utf-8")
            except Exception:
                pass
        return (
            "You are **ChemTutor**, an AI assistant that helps students learn **Organic Chemistry**.\n"
            "Use only the provided CONTEXT; be concise; English first with very light Roman Nepali.\n"
            "If context is missing, state that briefly and ask one clarifying question."
        )

# Import our new ChatMemory system
from chat_memory import get_or_create_chat_memory
# Import response processor for Nepali mixing
from response_processor import enhance_response
# Import molecule drawer for server-side molecule rendering
from molecule_drawer import draw_molecule_svg, draw_molecule_base64, get_molecule_info

# Get the absolute path to the chat-ui directory
import os
chat_ui_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chat-ui')
app = Flask(__name__, static_folder=chat_ui_path, static_url_path='')
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:14b"
EMBED_MODEL = "nomic-embed-text"
INDEX_DIR = Path("../local-pdf-rag/data/vector_index")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_DEFAULT_VOICE = os.getenv("OPENAI_DEFAULT_VOICE", "alloy")  # alloy, echo, fable, onyx, nova, shimmer
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "tts-1")

rag_store = None

def load_index_if_available():
    global rag_store
    if rag_store is not None:
        return rag_store
    if INDEX_DIR.exists():
        try:
            rag_store = FAISS.load_local(
                str(INDEX_DIR),
                OllamaEmbeddings(model=EMBED_MODEL),
                allow_dangerous_deserialization=True,
            )
            print(f"[RAG] Loaded FAISS index from {INDEX_DIR}")
        except Exception as e:
            print(f"[RAG] Failed to load index: {e}")
    return rag_store

# Attempt eager load at startup
load_index_if_available()

# ElevenLabs Helper Functions
def contains_nepali(text):
    """Detect if text contains Nepali characters"""
    nepali_chars = set('अआइईउऊएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहक्षत्रज्ञ')
    return any(char in nepali_chars for char in text)

def get_optimal_voice_for_text(text):
    """Choose the best voice based on text content"""
    if contains_nepali(text):
        # Use a voice that handles multilingual content well
        return "nova"  # Good for multilingual content
    else:
        # Use default voice for English
        return OPENAI_DEFAULT_VOICE

def synthesize_speech_openai(text, voice_id=None):
    """Generate speech using OpenAI TTS"""
    if not OPENAI_API_KEY:
        raise Exception("OpenAI API key not configured")
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        voice = voice_id or get_optimal_voice_for_text(text)
        
        # Clean text for better speech synthesis
        clean_text = text.replace('\n', ' ').replace('*', '').replace('#', '')
        
        # Generate audio using OpenAI TTS
        response = client.audio.speech.create(
            model=OPENAI_TTS_MODEL,
            voice=voice,
            input=clean_text,
            response_format="mp3"
        )
        
        return response.content
        
    except Exception as e:
        raise Exception(f"OpenAI TTS error: {str(e)}")

def transcribe_speech_openai(audio_data):
    """Transcribe audio using OpenAI Whisper API"""
    if not OPENAI_API_KEY:
        raise Exception("OpenAI API key not configured")
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Create a temporary file for the audio data
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe using OpenAI Whisper
            with open(temp_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"  # You can make this dynamic based on user preference
                )
            
            return transcript.text
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise Exception(f"OpenAI STT error: {str(e)}")


def stream_ollama(messages, model):
    payload = {
        "model": model or MODEL_NAME,
        "messages": messages,
        "stream": True,
        "temperature": 0.8,  # Even higher temperature for more creative responses
    }
    with requests.post(OLLAMA_URL, json=payload, stream=True) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line.decode("utf-8"))
            except Exception:
                continue
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]
            if chunk.get("done"):
                break


@app.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    model = data.get("model", MODEL_NAME)

    def generate():
        try:
            for token in stream_ollama(messages, model):
                yield token
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    return Response(generate(), mimetype="text/plain")


@app.post("/api/rag-chat")
def api_rag_chat():
    store = load_index_if_available()
    if store is None:
        return Response("[RAG index not available]\n", mimetype="text/plain", status=200)

    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    model = data.get("model", MODEL_NAME)
    k = int(data.get("k", 3))  # Reduced from 4 to 3 for more focused context
    chat_id = data.get("chat_id", "default")  # Use chat_id for memory management

    # Extract latest user query
    user_messages = [m for m in messages if m.get("role") == "user"]
    query = user_messages[-1]["content"] if user_messages else ""

    # Load system prompt
    base_prompt = load_system_prompt()
    
    # Get or create chat memory for this conversation
    chat_memory = get_or_create_chat_memory(chat_id, base_prompt)
    
    # Add the new user message to memory
    chat_memory.add_user(query)

    # Retrieve relevant chunks with optimized context
    try:
        docs = store.similarity_search(query, k=k)
    except Exception:
        docs = []
    
    # Build focused context with proper references
    context_blocks = []
    reference_list = []  # Store references separately for sources footer
    
    for idx, d in enumerate(docs):
        snippet = (d.page_content or "").strip().replace("\n", " ")
        # Keep snippets shorter for better focus (300 chars max)
        snippet = snippet[:300]
        
        # Extract proper reference information
        metadata = getattr(d, 'metadata', {})
        source = metadata.get('source', '')
        page = metadata.get('page', '')
        
        # Build proper reference format
        if source:
            # Extract filename and create proper reference
            filename = source.split('/')[-1] if '/' in source else source
            filename = filename.replace('.pdf', '').replace('_', ' ').title()
            
            if page:
                ref = f"[{idx+1}] {filename}, page {page}"
            else:
                ref = f"[{idx+1}] {filename}"
            
            context_blocks.append(snippet)  # Only include content, not reference
            reference_list.append(ref)
        else:
            # Try to extract reference from content if no metadata
            if "byjus.com" in snippet.lower():
                ref = f"[{idx+1}] Byju's Chemistry Reference"
            elif "formula" in snippet.lower() or "g/mol" in snippet:
                ref = f"[{idx+1}] Chemical Formula Reference"
            elif "organic" in snippet.lower() or "chemistry" in snippet.lower():
                ref = f"[{idx+1}] Organic Chemistry Reference"
            elif "molecule" in snippet.lower() or "structure" in snippet.lower():
                ref = f"[{idx+1}] Molecular Structure Reference"
            elif "reaction" in snippet.lower() or "bond" in snippet.lower():
                ref = f"[{idx+1}] Chemical Reaction Reference"
            else:
                ref = f"[{idx+1}] Chemistry Reference"
            
            context_blocks.append(snippet)
            reference_list.append(ref)
    
    context_text = "\n\n".join(context_blocks) if context_blocks else "(no relevant context found)"

    # Build messages with conversation history + RAG context
    chat_messages = chat_memory.build_messages_with_context(context_text)
    
    # Add final reminder for proper response style
    chat_messages.append({
        "role": "system",
        "content": "Remember: Mix English with Nepali words naturally (ठिक छ, राम्रो छ, धेरै important छ, हो, के, कसरी) and end with a mixed follow-up question. If user asks to draw something, add JSON tool call wrapped in code blocks: ```json\n{\"tool\":\"draw_molecule\",\"name\":\"water\",\"smiles\":\"O\"}\n```"
    })

    def generate():
        try:
            response_text = ""
            
            for token in stream_ollama(chat_messages, model):
                # Immediately forward tokens for true streaming UI
                if token:
                    yield token
                    response_text += token
                
                # Opportunistically detect tool JSON tokens and emit normalized event
                t = token.strip() if token else ""
                if t.startswith("{") and t.endswith("}") and '"tool"' in t and 'draw_molecule' in t:
                    try:
                        compact = t.replace("\n", " ").strip()
                        evt_json = json.loads(compact)
                        if 'items' in evt_json:
                            payload = {"type": "molecule", "items": evt_json.get('items', [])}
                        else:
                            payload = {"type": "molecule", "name": evt_json.get('name'), "smiles": evt_json.get('smiles')}
                        yield f"\n[EVENT]{json.dumps(payload)}\n"
                    except Exception as e:
                        print(f"Error parsing tool JSON: {e}, token: {token}")
                        pass
            
            # Append sources footer at the end of the stream
            if response_text.strip() and reference_list:
                sources_text = "\n\nSources:\n" + "\n".join(reference_list)
                yield sources_text
                response_text = response_text.strip() + sources_text
            else:
                response_text = response_text.strip()
            
            # Save final text to memory
            if response_text:
                chat_memory.add_assistant(response_text)
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    return Response(generate(), mimetype="text/plain")


@app.route("/api/draw-molecule", methods=['POST', 'OPTIONS'])
def api_draw_molecule():
    """API endpoint for drawing molecules using server-side RDKit."""
    if request.method == 'OPTIONS':
        return Response(status=200)
    
    try:
        data = request.get_json(silent=True) or {}
        smiles = data.get('smiles', '').strip()
        name = data.get('name', '').strip()
        format_type = data.get('format', 'svg')  # 'svg' or 'base64'
        width = int(data.get('width', 300))
        height = int(data.get('height', 300))
        
        if not smiles:
            return Response("Missing SMILES string", status=400)
        
        if format_type == 'svg':
            # Return SVG
            svg_content = draw_molecule_svg(smiles, name, width, height)
            if svg_content:
                return Response(svg_content, mimetype="image/svg+xml")
            else:
                return Response("Failed to generate molecule diagram", status=500)
        
        elif format_type == 'base64':
            # Return base64 PNG
            base64_content = draw_molecule_base64(smiles, name, width, height)
            if base64_content:
                return Response(base64_content, mimetype="text/plain")
            else:
                return Response("Failed to generate molecule diagram", status=500)
        
        else:
            return Response("Invalid format. Use 'svg' or 'base64'", status=400)
            
    except Exception as e:
        print(f"Error in draw-molecule API: {e}")
        return Response(f"Error: {str(e)}", status=500)


@app.route("/api/molecule-info", methods=['POST', 'OPTIONS'])
def api_molecule_info():
    """API endpoint for getting molecule information."""
    if request.method == 'OPTIONS':
        return Response(status=200)
    
    try:
        data = request.get_json(silent=True) or {}
        smiles = data.get('smiles', '').strip()
        
        if not smiles:
            return Response("Missing SMILES string", status=400)
        
        info = get_molecule_info(smiles)
        return Response(json.dumps(info), mimetype="application/json")
        
    except Exception as e:
        print(f"Error in molecule-info API: {e}")
        return Response(f"Error: {str(e)}", status=500)


@app.route("/api/tts", methods=['POST', 'OPTIONS'])
def api_tts():
    """Convert text to speech using OpenAI"""
    try:
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            response = Response()
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            return response
        
        data = request.get_json(silent=True) or {}
        text = data.get("text", "")
        voice_id = data.get("voice_id")
        
        if not text:
            return {"error": "No text provided"}, 400
        
        # Truncate text to fit OpenAI's 4096 character limit
        max_length = 4000  # Leave some buffer
        if len(text) > max_length:
            text = text[:max_length] + "..."
            print(f"[TTS] Text truncated from {len(data.get('text', ''))} to {len(text)} characters")
        
        # Generate speech
        audio_data = synthesize_speech_openai(text, voice_id)
        
        # Return audio as base64
        import base64
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        response_data = {
            "success": True,
            "audio_data": audio_b64,
            "voice_used": voice_id or get_optimal_voice_for_text(text)
        }
        
        # Add CORS headers
        response = Response(json.dumps(response_data), mimetype='application/json')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        
        return response
        
    except Exception as e:
        error_response = {"error": str(e), "success": False}
        response = Response(json.dumps(error_response), mimetype='application/json', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response


@app.post("/api/stt")
def api_stt():
    """Convert speech to text using OpenAI Whisper"""
    try:
        # Check if audio file is provided
        if 'audio' not in request.files:
            return {"error": "No audio file provided"}, 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return {"error": "No audio file selected"}, 400
        
        # Read audio data
        audio_data = audio_file.read()
        
        # Transcribe speech using OpenAI Whisper
        transcript = transcribe_speech_openai(audio_data)
        
        return {
            "success": True,
            "transcript": transcript
        }
        
    except Exception as e:
        return {"error": str(e), "success": False}, 500


@app.route("/")
def serve_index():
    """Serve the main chat interface"""
    from flask import send_from_directory
    return send_from_directory(chat_ui_path, 'index.html')

@app.get("/api/test")
def api_test():
    """Test endpoint to verify server is working"""
    return {"message": "Server is working!", "timestamp": "2025-01-01"}

@app.get("/api/voices")
def api_voices():
    """Get available OpenAI voices"""
    try:
        # OpenAI TTS voices are predefined
        voices = [
            {"voice_id": "alloy", "name": "Alloy", "category": "neural", "description": "Neutral, balanced voice"},
            {"voice_id": "echo", "name": "Echo", "category": "neural", "description": "Clear, confident voice"},
            {"voice_id": "fable", "name": "Fable", "category": "neural", "description": "Warm, engaging voice"},
            {"voice_id": "onyx", "name": "Onyx", "category": "neural", "description": "Deep, authoritative voice"},
            {"voice_id": "nova", "name": "Nova", "category": "neural", "description": "Friendly, expressive voice"},
            {"voice_id": "shimmer", "name": "Shimmer", "category": "neural", "description": "Soft, melodic voice"}
        ]
        
        return {
            "success": True,
            "voices": voices
        }
        
    except Exception as e:
        return {"error": str(e), "success": False}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)


