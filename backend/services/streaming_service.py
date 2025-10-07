"""
Streaming Service - Handles LLM streaming with integrated TTS
Buffers tokens into sentences and generates audio events
"""
import json
import re
import time
from typing import Generator, Optional, Dict, Any
from backend.services.llm_service import get_llm_service
from backend.services.voice_service import get_voice_service
from backend.config import OPENAI_API_KEY


class StreamingService:
    """
    Coordinates LLM streaming with real-time TTS generation
    Buffers tokens into sentences and emits SSE events
    """
    
    def __init__(self, enable_tts: bool = True):
        self.llm_service = get_llm_service()
        self.enable_tts = enable_tts and bool(OPENAI_API_KEY)
        
        if self.enable_tts:
            try:
                self.voice_service = get_voice_service()
                print("[Streaming] TTS enabled with OpenAI")
            except Exception as e:
                print(f"[Streaming] TTS disabled - {e}")
                self.enable_tts = False
        else:
            print("[Streaming] TTS disabled - no API key")
            self.voice_service = None
    
    def stream_with_tts(
        self,
        messages: list[dict],
        model: str = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Stream LLM response with integrated TTS
        
        Yields SSE events:
        - text: Display text chunks
        - audio: Audio for complete sentences
        - molecule: RDKit molecule drawing
        - complete: Stream finished
        """
        
        buffer = ""
        sentence_count = 0
        full_response = ""
        
        try:
            print(f"[Streaming] Starting LLM stream with {len(messages)} messages")
            print(f"[Streaming] Model: {model or 'default'}")
            
            token_count = 0
            
            # Stream tokens from LLM
            for token in self.llm_service.stream_chat(messages, model):
                if not token:
                    continue
                
                token_count += 1
                if token_count == 1:
                    print(f"[Streaming] First token received: '{token}'")
                
                buffer += token
                full_response += token
                
                # Send text event immediately for display
                yield {
                    "type": "text",
                    "content": token
                }
                
                # Log progress every 50 tokens
                if token_count % 50 == 0:
                    print(f"[Streaming] Progress: {token_count} tokens, {len(full_response)} chars")
                
                # Check for complete sentences
                sentences = self._extract_complete_sentences(buffer)
                
                for sentence in sentences:
                    sentence_count += 1
                    print(f"[Streaming] Sentence {sentence_count}: {sentence[:60]}...")
                    
                    # Remove sentence from buffer
                    buffer = buffer[len(sentence):].lstrip()
                    
                    # Generate TTS if enabled
                    if self.enable_tts and len(sentence.strip()) > 15:
                        try:
                            audio_data = self._generate_tts(sentence)
                            if audio_data:
                                yield {
                                    "type": "audio",
                                    "audio_base64": audio_data,
                                    "sentence_id": sentence_count,
                                    "text": sentence
                                }
                                print(f"[Streaming] Audio generated for sentence {sentence_count}")
                                
                                # No artificial delay - let frontend queue handle timing
                                # The frontend will play audio sequentially based on onended events
                                
                        except Exception as e:
                            print(f"[Streaming] TTS failed for sentence {sentence_count}: {e}")
                            # Continue without audio - non-blocking
                
                # Check for molecule tool usage
                tool_event = self.llm_service.detect_tool_usage(buffer)
                if tool_event:
                    yield {
                        "type": "molecule",
                        **tool_event
                    }
                    # Clear tool JSON from buffer to avoid re-detection
                    buffer = re.sub(r'\{[^}]*"tool"[^}]*\}', '', buffer)
            
            # Handle any remaining buffer (incomplete sentence)
            if buffer.strip():
                print(f"[Streaming] Remaining buffer: {buffer[:60]}...")
                # Don't generate TTS for incomplete sentences
                # They're usually partial or references section
            
            # Send completion event
            yield {
                "type": "complete",
                "full_text": full_response,
                "sentence_count": sentence_count
            }
            
            print(f"[Streaming] Stream complete - {sentence_count} sentences, {len(full_response)} chars")
            
        except Exception as e:
            print(f"[Streaming] Error: {e}")
            yield {
                "type": "error",
                "message": str(e)
            }
    
    def _extract_complete_sentences(self, text: str) -> list[str]:
        """
        Extract complete sentences from text buffer
        Returns sentences that end with . ! or ?
        Leaves incomplete sentences in buffer
        """
        sentences = []
        
        # Split on sentence-ending punctuation
        # Use a more robust pattern that captures the sentence with its punctuation
        parts = re.split(r'([.!?])', text)
        
        # Reconstruct sentences by pairing text with punctuation
        i = 0
        while i < len(parts) - 1:
            text_part = parts[i].strip()
            punct = parts[i + 1] if i + 1 < len(parts) else ""
            
            if punct in '.!?':
                sentence = (text_part + punct).strip()
                
                # Filter out:
                # - Very short fragments (< 15 chars)
                # - Citation-only like "[1]." or "[2]."
                # - Code blocks, events, etc.
                if (len(sentence) > 15 and 
                    not re.match(r'^\[\d+\]\.?$', sentence) and
                    not sentence.startswith('[EVENT]') and
                    not sentence.startswith('```')):
                    sentences.append(sentence)
                
                i += 2  # Skip both text and punctuation
            else:
                i += 1
        
        return sentences
    
    def _generate_tts(self, text: str) -> Optional[str]:
        """
        Generate TTS audio for text
        Returns base64-encoded audio or None
        """
        if not self.enable_tts or not self.voice_service:
            return None
        
        try:
            # Clean text for TTS
            clean_text = self._clean_text_for_tts(text)
            
            if len(clean_text) < 10:
                return None
            
            # Generate audio
            audio_bytes = self.voice_service.synthesize_speech(clean_text)
            
            # Convert to base64
            import base64
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            return audio_b64
            
        except Exception as e:
            print(f"[Streaming] TTS generation failed: {e}")
            return None
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for optimal TTS output"""
        clean = text
        
        # Remove code blocks first (before other processing)
        clean = re.sub(r'```[\s\S]*?```', '', clean)
        
        # Remove markdown and formatting
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', clean)  # Bold
        clean = re.sub(r'\*(.+?)\*', r'\1', clean)       # Italic
        clean = re.sub(r'`+', '', clean)                 # Backticks
        clean = re.sub(r'#{1,6}\s*', '', clean)          # Headers (with optional space)
        
        # Remove citations [1], [2], etc.
        clean = re.sub(r'\[\d+\]', '', clean)
        
        # Remove event markers
        clean = re.sub(r'\[EVENT\].*', '', clean)
        
        # Clean up whitespace and normalize punctuation
        clean = re.sub(r'\s*\.\s*', '. ', clean)         # Normalize periods
        clean = re.sub(r'\s*!\s*', '! ', clean)          # Normalize exclamations
        clean = re.sub(r'\s*\?\s*', '? ', clean)         # Normalize questions
        clean = re.sub(r'\s+', ' ', clean)               # Collapse spaces
        clean = clean.strip()
        
        return clean


# Global streaming service instance
_streaming_service: Optional[StreamingService] = None


def get_streaming_service(enable_tts: bool = True) -> StreamingService:
    """Get or create the global streaming service instance"""
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = StreamingService(enable_tts=enable_tts)
    return _streaming_service

