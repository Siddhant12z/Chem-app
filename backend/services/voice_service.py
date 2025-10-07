"""
Voice Service
Handles Text-to-Speech (TTS) and Speech-to-Text (STT) operations using OpenAI
"""
import base64
import tempfile
import os
from typing import Optional
from openai import OpenAI

from backend.config import OPENAI_API_KEY, OPENAI_DEFAULT_VOICE, OPENAI_TTS_MODEL


class VoiceService:
    """Service for voice operations (TTS and STT)"""
    
    def __init__(self, api_key: str = OPENAI_API_KEY):
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = OpenAI(api_key=api_key)
        self.default_voice = OPENAI_DEFAULT_VOICE
        self.tts_model = OPENAI_TTS_MODEL
    
    @staticmethod
    def contains_nepali(text: str) -> bool:
        """Detect if text contains Nepali characters"""
        nepali_chars = set('अआइईउऊएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहक्षत्रज्ञ')
        return any(char in nepali_chars for char in text)
    
    def get_optimal_voice(self, text: str) -> str:
        """Choose the best voice based on text content"""
        if self.contains_nepali(text):
            # Fable voice works best with Nepali text (tested and confirmed)
            return "fable"  # Fable has the best Nepali pronunciation
        return self.default_voice
    
    def synthesize_speech(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """
        Generate speech using OpenAI TTS
        
        Args:
            text: Text to convert to speech
            voice_id: Optional specific voice to use
            
        Returns:
            Audio data as bytes (MP3 format)
        """
        voice = voice_id or self.get_optimal_voice(text)
        
        # Clean text for better speech synthesis with optimized punctuation
        import re
        clean_text = (text
            .replace('\n', ' ')                    # Replace newlines with spaces
            .replace('*', '')                      # Remove markdown bold/italic
            .replace('#', '')                      # Remove markdown headers
            .replace('```', '')                    # Remove code block markers
            .replace('`', '')                      # Remove inline code markers
        )
        
        # Special handling for Nepali text to improve TTS
        if self.contains_nepali(clean_text):
            print(f"[TTS] Processing text with Nepali characters: {clean_text[:100]}...")
            # Add spaces around Nepali words for better pronunciation
            # This helps TTS engines recognize word boundaries
            clean_text = re.sub(r'([a-zA-Z])([अ-ह])', r'\1 \2', clean_text)  # Space between English and Nepali
            clean_text = re.sub(r'([अ-ह])([a-zA-Z])', r'\1 \2', clean_text)  # Space between Nepali and English
        
        # Apply regex replacements for punctuation normalization
        clean_text = re.sub(r'\s*\.\s*', '. ', clean_text)      # Normalize period spacing
        clean_text = re.sub(r'\s*!\s*', '! ', clean_text)       # Normalize exclamation spacing  
        clean_text = re.sub(r'\s*\?\s*', '? ', clean_text)      # Normalize question spacing
        clean_text = re.sub(r'\s*;\s*', '; ', clean_text)       # Normalize semicolon spacing
        clean_text = re.sub(r'\s*:\s*', ': ', clean_text)       # Normalize colon spacing
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()    # Collapse multiple spaces
        
        # Truncate text to fit OpenAI's 4096 character limit
        max_length = 4000
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length] + "..."
            print(f"[TTS] Text truncated from {len(text)} to {len(clean_text)} characters")
        
        # Debug: Log voice selection and text for Nepali
        if self.contains_nepali(text):
            print(f"[TTS] Using voice '{voice}' for text: '{clean_text[:100]}...'")
        
        # Generate audio using OpenAI TTS
        response = self.client.audio.speech.create(
            model=self.tts_model,
            voice=voice,
            input=clean_text,
            response_format="mp3"
        )
        
        return response.content
    
    def synthesize_speech_base64(self, text: str, voice_id: Optional[str] = None) -> dict:
        """
        Generate speech and return as base64-encoded string
        
        Args:
            text: Text to convert to speech
            voice_id: Optional specific voice to use
            
        Returns:
            Dictionary with audio data and metadata
        """
        audio_data = self.synthesize_speech(text, voice_id)
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {
            "success": True,
            "audio_data": audio_b64,
            "voice_used": voice_id or self.get_optimal_voice(text)
        }
    
    def transcribe_speech(self, audio_data: bytes, language: str = "en") -> str:
        """
        Transcribe audio using OpenAI Whisper API
        
        Args:
            audio_data: Audio file data
            language: Language code for transcription
            
        Returns:
            Transcribed text
        """
        # Create a temporary file for the audio data
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe using OpenAI Whisper
            with open(temp_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language
                )
            
            return transcript.text
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
    
    @staticmethod
    def get_available_voices() -> list[dict]:
        """Get list of available OpenAI TTS voices"""
        return [
            {
                "voice_id": "alloy",
                "name": "Alloy",
                "category": "neural",
                "description": "Neutral, balanced voice"
            },
            {
                "voice_id": "echo",
                "name": "Echo",
                "category": "neural",
                "description": "Clear, confident voice"
            },
            {
                "voice_id": "fable",
                "name": "Fable",
                "category": "neural",
                "description": "Warm, engaging voice"
            },
            {
                "voice_id": "onyx",
                "name": "Onyx",
                "category": "neural",
                "description": "Deep, authoritative voice"
            },
            {
                "voice_id": "nova",
                "name": "Nova",
                "category": "neural",
                "description": "Friendly, expressive voice"
            },
            {
                "voice_id": "shimmer",
                "name": "Shimmer",
                "category": "neural",
                "description": "Soft, melodic voice"
            }
        ]


# Global voice service instance
_voice_service: Optional[VoiceService] = None


def get_voice_service() -> VoiceService:
    """Get or create the global voice service instance"""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service

