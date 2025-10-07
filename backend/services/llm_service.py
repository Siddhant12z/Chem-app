"""
LLM Service
Handles interactions with the local LLM via Ollama
"""
import json
import requests
from typing import List, Dict, Generator

from backend.config import OLLAMA_URL, MODEL_NAME, LLM_TEMPERATURE


class LLMService:
    """Service for LLM operations"""
    
    def __init__(self, ollama_url: str = OLLAMA_URL, model_name: str = MODEL_NAME):
        self.ollama_url = ollama_url
        self.model_name = model_name
    
    def stream_chat(
        self, 
        messages: List[Dict[str, str]], 
        model: str = None,
        temperature: float = LLM_TEMPERATURE
    ) -> Generator[str, None, None]:
        """
        Stream chat responses from Ollama
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use (defaults to configured model)
            temperature: Temperature for generation
            
        Yields:
            Text tokens from the LLM
        """
        model_to_use = model or self.model_name
        
        payload = {
            "model": model_to_use,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
        }
        
        print(f"[LLM Service] Streaming from Ollama, model: {model_to_use}")
        print(f"[LLM Service] URL: {self.ollama_url}")
        print(f"[LLM Service] Messages count: {len(messages)}")
        
        # Debug: Print first and last message
        if messages:
            print(f"[LLM Service] First message role: {messages[0].get('role')}, content length: {len(messages[0].get('content', ''))}")
            print(f"[LLM Service] Last message role: {messages[-1].get('role')}, content length: {len(messages[-1].get('content', ''))}")
        
        try:
            with requests.post(self.ollama_url, json=payload, stream=True, timeout=60) as r:
                print(f"[LLM Service] Response status: {r.status_code}")
                r.raise_for_status()
                
                line_count = 0
                token_count = 0
                
                for line in r.iter_lines():
                    if not line:
                        continue
                    
                    line_count += 1
                    
                    try:
                        chunk = json.loads(line.decode("utf-8"))
                    except Exception as e:
                        print(f"[LLM Service] JSON parse error on line {line_count}: {e}")
                        print(f"[LLM Service] Raw line: {line[:200]}")
                        continue
                    
                    # Debug: Print first chunk
                    if line_count == 1:
                        print(f"[LLM Service] First chunk keys: {list(chunk.keys())}")
                        if 'error' in chunk:
                            print(f"[LLM Service] ERROR FROM OLLAMA: {chunk['error']}")
                        if 'message' in chunk:
                            print(f"[LLM Service] Message keys: {list(chunk['message'].keys())}")
                            print(f"[LLM Service] Content: '{chunk['message'].get('content', 'NONE')}'")
                    
                    # Check for error in response
                    if 'error' in chunk:
                        error_msg = chunk['error']
                        print(f"[LLM Service] Ollama error: {error_msg}")
                        yield f"\n[Ollama Error: {error_msg}]"
                        break
                    
                    if "message" in chunk and "content" in chunk["message"]:
                        content = chunk["message"]["content"]
                        if content:
                            token_count += 1
                            if token_count == 1:
                                print(f"[LLM Service] First token: '{content}'")
                            yield content
                    
                    if chunk.get("done"):
                        print(f"[LLM Service] Stream complete - {token_count} tokens from {line_count} lines")
                        break
                
                if token_count == 0:
                    print(f"[LLM Service] WARNING: No tokens generated! Lines received: {line_count}")
                    print(f"[LLM Service] This usually means the model returned empty content or an error")
                    
        except requests.exceptions.Timeout:
            error_msg = f"Ollama timeout - model might be loading"
            print(f"[LLM Service] {error_msg}")
            yield f"\n[Error: {error_msg}. Please wait a moment and try again.]"
        except Exception as e:
            error_msg = f"LLM error: {str(e)}"
            print(f"[LLM Service] {error_msg}")
            import traceback
            traceback.print_exc()
            yield f"\n[Error: {error_msg}]"
    
    def detect_tool_usage(self, text: str) -> Dict | None:
        """
        Detect a draw_molecule tool invocation embedded anywhere in the streamed text.
        Supports plain JSON or fenced ```json code blocks.

        Expected shapes:
        {"tool":"draw_molecule","name":"benzene","smiles":"c1ccccc1"}
        or
        ```json\n{"tool":"draw_molecule","items":[{"name":"water","smiles":"O"}]}\n```
        """
        if not text:
            return None

        t = text.strip()

        # First, try to find a fenced code block
        import re
        code_block_match = re.search(r"```(?:json)?\s*\{[\s\S]*?\}\s*```", t, re.IGNORECASE)
        candidate = None
        if code_block_match:
            candidate = code_block_match.group(0)
        else:
            # Fallback: find a single JSON object containing the tool field
            json_match = re.search(r"\{[^}]*\"tool\"\s*:\s*\"draw_molecule\"[^}]*\}", t, re.IGNORECASE)
            if json_match:
                candidate = json_match.group(0)

        if not candidate:
            return None

        # Strip code fences if present
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate).strip()

        # Compact and parse
        try:
            compact = candidate.replace("\n", " ").strip()
            evt_json = json.loads(compact)

            # Support list of items or single name/smiles
            if isinstance(evt_json, dict) and evt_json.get("tool") == "draw_molecule":
                if 'items' in evt_json and isinstance(evt_json['items'], list):
                    return {"type": "molecule", "items": evt_json.get('items', [])}
                else:
                    return {
                        "type": "molecule",
                        "name": evt_json.get('name'),
                        "smiles": evt_json.get('smiles')
                    }
        except Exception as e:
            print(f"Error parsing tool JSON: {e}, candidate: {candidate}")
            return None

        return None


# Global LLM service instance
_llm_service = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

