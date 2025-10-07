"""
Voice API Routes
Handles Text-to-Speech (TTS) and Speech-to-Text (STT) endpoints
"""
import json
from flask import Blueprint, request, Response

from backend.services.voice_service import get_voice_service

voice_bp = Blueprint('voice', __name__)


@voice_bp.route('/tts', methods=['POST', 'OPTIONS'])
def api_tts():
    """Convert text to speech using OpenAI TTS"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = Response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        data = request.get_json(silent=True) or {}
        text = data.get("text", "")
        voice_id = data.get("voice_id")
        
        if not text:
            return {"error": "No text provided"}, 400
        
        voice_service = get_voice_service()
        response_data = voice_service.synthesize_speech_base64(text, voice_id)
        
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


@voice_bp.route('/stt', methods=['POST'])
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
        
        voice_service = get_voice_service()
        transcript = voice_service.transcribe_speech(audio_data)
        
        return {
            "success": True,
            "transcript": transcript
        }
        
    except Exception as e:
        return {"error": str(e), "success": False}, 500


@voice_bp.route('/voices', methods=['GET'])
def api_voices():
    """Get available OpenAI TTS voices"""
    try:
        from backend.services.voice_service import VoiceService
        voices = VoiceService.get_available_voices()
        
        return {
            "success": True,
            "voices": voices
        }
        
    except Exception as e:
        return {"error": str(e), "success": False}, 500

