"""
Health Check API Routes
Simple endpoints for testing server connectivity
"""
import requests
from flask import Blueprint
from backend.services.rag_service import get_rag_service
from backend.config import OPENAI_API_KEY

health_bp = Blueprint('health', __name__)


@health_bp.route('/test', methods=['GET'])
def api_test():
    """Test endpoint to verify server is working"""
    return {
        "message": "ChemTutor server is working!",
        "status": "healthy",
        "version": "1.0.0"
    }


@health_bp.route('/health', methods=['GET'])
def api_health():
    """Comprehensive health check endpoint for monitoring"""
    health_status = {
        "status": "healthy",
        "service": "chemtutor-backend",
        "components": {}
    }
    
    # Check RAG service
    try:
        rag_service = get_rag_service()
        health_status["components"]["rag"] = {
            "status": "online" if rag_service.is_available() else "offline",
            "available": rag_service.is_available()
        }
    except Exception as e:
        health_status["components"]["rag"] = {
            "status": "offline",
            "available": False,
            "error": str(e)
        }
    
    # Check Ollama LLM
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        health_status["components"]["ollama"] = {
            "status": "online" if response.ok else "offline",
            "available": response.ok
        }
    except Exception as e:
        health_status["components"]["ollama"] = {
            "status": "offline",
            "available": False,
            "error": str(e)
        }
    
    # Check OpenAI API key
    health_status["components"]["openai_voice"] = {
        "status": "configured" if OPENAI_API_KEY else "not_configured",
        "available": bool(OPENAI_API_KEY)
    }
    
    # Overall status
    all_critical_online = (
        health_status["components"]["rag"]["available"] and
        health_status["components"]["ollama"]["available"]
    )
    
    health_status["status"] = "healthy" if all_critical_online else "degraded"
    
    return health_status, 200 if all_critical_online else 503

