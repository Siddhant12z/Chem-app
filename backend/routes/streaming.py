"""
Streaming API Routes
Server-Sent Events (SSE) endpoint for real-time chat with TTS
"""
import json
from flask import Blueprint, request, Response, stream_with_context
from pathlib import Path

from backend.services.streaming_service import get_streaming_service
from backend.services.rag_service import get_rag_service
from backend.services.chat_memory import get_or_create_chat_memory
from backend.config import MODEL_NAME, RAG_TOP_K

# Load system prompt
try:
    from prompts.loader import load_system_prompt
except Exception:
    def load_system_prompt(path: str = "prompts/system_prompt.txt") -> str:
        p = Path(path)
        if p.exists():
            try:
                return p.read_text(encoding="utf-8")
            except Exception:
                pass
        return (
            "You are **ChemTutor**, an AI assistant that helps students learn **Organic Chemistry**.\n"
            "Use only the provided CONTEXT; be concise; English first with minimal Devanagari Nepali.\n"
            "If context is missing, state that briefly."
        )

streaming_bp = Blueprint('streaming', __name__)


@streaming_bp.route('/stream-chat', methods=['POST', 'OPTIONS'])
def api_stream_chat():
    """
    Server-Sent Events endpoint for chat with integrated TTS
    Returns SSE stream with text and audio events
    """
    if request.method == 'OPTIONS':
        return Response(status=200)
    
    # Get RAG service
    rag_service = get_rag_service()
    
    if not rag_service.is_available():
        # Return error event
        def error_stream():
            yield format_sse_event("error", {"message": "RAG index not available"})
            yield format_sse_event("complete", {})
        return Response(stream_with_context(error_stream()), mimetype='text/event-stream')
    
    # Parse request
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    model = data.get("model", MODEL_NAME)
    k = int(data.get("k", RAG_TOP_K))
    chat_id = data.get("chat_id", "default")
    enable_tts = data.get("enable_tts", True)
    tts_mode = data.get("tts_mode", "openai")  # "openai" or "browser"
    
    # Disable backend TTS if using browser mode
    backend_tts_enabled = enable_tts and tts_mode == "openai"
    
    # Extract latest user query
    user_messages = [m for m in messages if m.get("role") == "user"]
    query = user_messages[-1]["content"] if user_messages else ""
    
    print(f"\n[SSE Stream] New request - chat_id: {chat_id}, query: {query[:50]}...")
    
    # Load system prompt
    base_prompt = load_system_prompt()
    
    # Get chat memory
    chat_memory = get_or_create_chat_memory(chat_id, base_prompt)
    chat_memory.add_user(query)
    
    # Retrieve context from RAG
    context_blocks, reference_list = rag_service.retrieve_context(query, k)
    context_text = "\n\n".join(context_blocks) if context_blocks else "(no relevant context found)"
    
    print(f"[SSE Stream] Retrieved {len(context_blocks)} context blocks")
    
    # Build messages with context
    chat_messages = chat_memory.build_messages_with_context(context_text)
    
    # Add style reminder
    chat_messages.append({
        "role": "system",
        "content": (
            "Use minimal Devanagari Nepali (ठिक छ, राम्रो छ, बुझ्नुभयो?) - only 1-2 words. "
            "Keep responses clear in English. "
            "For molecule drawing: ```json\n{\"tool\":\"draw_molecule\",\"name\":\"benzene\",\"smiles\":\"c1ccccc1\"}\n```"
        )
    })
    
    # Get streaming service with TTS mode
    streaming_service = get_streaming_service(enable_tts=backend_tts_enabled)
    
    @stream_with_context
    def generate():
        """Generate SSE events"""
        try:
            full_text = ""
            
            # Stream events from service
            for event in streaming_service.stream_with_tts(chat_messages, model):
                event_type = event.get("type")
                
                # Format and yield SSE event
                sse_data = format_sse_event(event_type, event)
                yield sse_data
                
                # Collect full text for memory
                if event_type == "text":
                    full_text += event.get("content", "")
                elif event_type == "complete":
                    full_text = event.get("full_text", full_text)
            
            # Add sources to final text
            if full_text.strip() and reference_list:
                sources_text = "\n\nSources:\n" + "\n".join(reference_list)
                
                # Send sources as text event
                yield format_sse_event("text", {"content": sources_text})
                
                full_text += sources_text
            
            # Save to memory
            if full_text.strip():
                chat_memory.add_assistant(full_text)
                print(f"[SSE Stream] Saved response to memory ({len(full_text)} chars)")
            
            # Send final complete event
            yield format_sse_event("done", {"message": "Stream complete"})
            
        except Exception as e:
            print(f"[SSE Stream] Error: {e}")
            import traceback
            traceback.print_exc()
            yield format_sse_event("error", {"message": str(e)})
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    
    return response


def format_sse_event(event_type: str, data: dict) -> str:
    """
    Format data as Server-Sent Event
    
    Args:
        event_type: Event name (text, audio, molecule, complete, error)
        data: Event data dictionary
        
    Returns:
        Formatted SSE string
    """
    # Remove type from data if present (it's in event name)
    data_copy = {k: v for k, v in data.items() if k != 'type'}
    
    # Format as SSE
    sse = f"event: {event_type}\n"
    sse += f"data: {json.dumps(data_copy)}\n\n"
    
    return sse

