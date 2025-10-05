"""
ChatMemory class for managing conversation history with rolling window.
Adapted from the TypeScript pattern for Python/Flask backend.
"""

import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class Message:
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None


class ChatMemory:
    """
    Manages conversation history with a rolling window that fits within token budget.
    Uses pragmatic token estimation (≈4 chars/token) to avoid extra dependencies.
    """
    
    AVG_CHARS_PER_TOKEN = 4  # rough estimate, good enough for rolling window
    
    def __init__(self, system_content: str, max_tokens: int = 6000):
        self.system = Message(role="system", content=system_content)
        self.turns: List[Message] = []
        self.max_tokens = max_tokens
    
    def add_user(self, text: str) -> None:
        """Add a user message to the conversation."""
        self.turns.append(Message(role="user", content=text))
    
    def add_assistant(self, text: str) -> None:
        """Add an assistant message to the conversation."""
        self.turns.append(Message(role="assistant", content=text))
    
    def _approx_tokens(self, text: str) -> int:
        """Estimate token count from character count."""
        return max(1, len(text) // self.AVG_CHARS_PER_TOKEN)
    
    def build_messages_with_context(self, rag_context: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Build messages array with rolling history + current RAG context.
        
        Args:
            rag_context: Optional RAG context to include as system message
            
        Returns:
            List of message dictionaries in the format expected by Ollama
        """
        # Create context block if RAG context provided
        context_messages = []
        if rag_context:
            context_messages.append(Message(
                role="system", 
                content=f"Knowledgebase context:\n{rag_context}"
            ))
        
        # Start with system + context + all turns, then trim from oldest turns
        full_messages = [self.system] + context_messages + self.turns
        total_tokens = sum(self._approx_tokens(msg.content) for msg in full_messages)
        
        # Keep system + context fixed; trim within conversational turns only
        head = [self.system] + context_messages
        body = self.turns.copy()  # oldest → newest
        
        # Trim from the beginning (oldest messages) to fit token budget
        while total_tokens > self.max_tokens and len(body) > 2:
            # Drop the oldest message
            first = body.pop(0)
            total_tokens -= self._approx_tokens(first.content)
            
            # If still over budget and next message is not a user message, drop it too
            if (total_tokens > self.max_tokens and 
                len(body) > 0 and 
                body[0].role != "user"):
                second = body.pop(0)
                total_tokens -= self._approx_tokens(second.content)
        
        # Convert to Ollama format
        final_messages = head + body
        return [
            {"role": msg.role, "content": msg.content} 
            for msg in final_messages
        ]
    
    def get_conversation_summary(self) -> str:
        """Get a brief summary of the conversation for debugging."""
        return f"Conversation with {len(self.turns)} turns, estimated {sum(self._approx_tokens(msg.content) for msg in [self.system] + self.turns)} tokens"
    
    def clear_history(self) -> None:
        """Clear conversation history while keeping system prompt."""
        self.turns.clear()


# Global chat memory instances - one per chat session
# In a production system, you'd want to use a proper session store
_chat_memories: Dict[str, ChatMemory] = {}


def get_or_create_chat_memory(chat_id: str, system_content: str) -> ChatMemory:
    """Get existing chat memory or create new one for the given chat ID."""
    if chat_id not in _chat_memories:
        _chat_memories[chat_id] = ChatMemory(system_content)
    return _chat_memories[chat_id]


def clear_chat_memory(chat_id: str) -> None:
    """Clear chat memory for a specific chat."""
    if chat_id in _chat_memories:
        del _chat_memories[chat_id]
