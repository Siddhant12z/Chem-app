"""
Chat API Routes
Handles chat endpoints with RAG support
"""
import json
from flask import Blueprint, request, Response
from pathlib import Path

from backend.services.rag_service import get_rag_service
from backend.services.llm_service import get_llm_service
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
            "Use only the provided CONTEXT; be concise; English first with very light Roman Nepali.\n"
            "If context is missing, state that briefly and ask one clarifying question."
        )

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat', methods=['POST'])
def api_chat():
    """Basic chat endpoint without RAG"""
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    model = data.get("model", MODEL_NAME)
    
    llm_service = get_llm_service()
    
    def generate():
        try:
            for token in llm_service.stream_chat(messages, model):
                yield token
        except Exception as e:
            yield f"\n[Error: {str(e)}]"
    
    return Response(generate(), mimetype="text/plain")


@chat_bp.route('/rag-chat', methods=['POST'])
def api_rag_chat():
    """Chat endpoint with RAG (Retrieval Augmented Generation)"""
    rag_service = get_rag_service()
    
    if not rag_service.is_available():
        return Response("[RAG index not available]\n", mimetype="text/plain", status=200)
    
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    model = data.get("model", MODEL_NAME)
    k = int(data.get("k", RAG_TOP_K))
    chat_id = data.get("chat_id", "default")
    
    # Extract latest user query
    user_messages = [m for m in messages if m.get("role") == "user"]
    query = user_messages[-1]["content"] if user_messages else ""
    
    # Load system prompt
    base_prompt = load_system_prompt()
    
    # Get or create chat memory for this conversation
    chat_memory = get_or_create_chat_memory(chat_id, base_prompt)
    
    # Add the new user message to memory
    chat_memory.add_user(query)
    
    # Retrieve relevant chunks
    context_blocks, reference_list = rag_service.retrieve_context(query, k)
    context_text = "\n\n".join(context_blocks) if context_blocks else "(no relevant context found)"
    
    # Build messages with conversation history + RAG context
    chat_messages = chat_memory.build_messages_with_context(context_text)
    
    # Add final reminder for proper response style
    chat_messages.append({
        "role": "system",
        "content": (
            "Remember: Use minimal Nepali in Devanagari (ठिक छ, राम्रो छ, बुझ्नुभयो?) - only 1-2 words. "
            "Keep responses clear and concise in English. "
            "If user asks to draw something, add JSON tool call wrapped in code blocks: "
            "```json\n{\"tool\":\"draw_molecule\",\"name\":\"water\",\"smiles\":\"O\"}\n```"
        )
    })
    
    llm_service = get_llm_service()
    
    def generate():
        try:
            response_text = ""
            
            for token in llm_service.stream_chat(chat_messages, model):
                # Immediately forward tokens for true streaming UI
                if token:
                    yield token
                    response_text += token
                
                # Detect tool JSON tokens and emit normalized event
                tool_event = llm_service.detect_tool_usage(token)
                if tool_event:
                    yield f"\n[EVENT]{json.dumps(tool_event)}\n"
            
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

