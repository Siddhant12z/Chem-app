"""
ChemTutor Backend Application
Main Flask application with all routes and services configured
"""
from flask import Flask, send_from_directory
from flask_cors import CORS

from backend.config import HOST, PORT, DEBUG, CORS_ORIGINS, FRONTEND_PATH
from backend.routes import register_routes


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, static_folder=str(FRONTEND_PATH), static_url_path='')
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": CORS_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register all API routes
    register_routes(app)
    
    # Serve frontend
    @app.route("/")
    def serve_index():
        """Serve the main chat interface"""
        return send_from_directory(str(FRONTEND_PATH), 'index.html')
    
    @app.route("/<path:path>")
    def serve_static(path):
        """Serve static frontend files"""
        return send_from_directory(str(FRONTEND_PATH), path)
    
    return app


def main():
    """Run the Flask development server"""
    app = create_app()
    print(f"🧪 ChemTutor Backend starting on http://{HOST}:{PORT}")
    print(f"📚 RAG System: Initializing...")
    print(f"🎤 Voice Services: OpenAI TTS/STT")
    print(f"💬 LLM: Local Ollama")
    app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()

