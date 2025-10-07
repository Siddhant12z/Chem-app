"""
API Routes for ChemTutor backend
"""
from flask import Blueprint

def register_routes(app):
    """Register all routes with the Flask app"""
    from backend.routes.chat import chat_bp
    from backend.routes.voice import voice_bp
    from backend.routes.molecule import molecule_bp
    from backend.routes.health import health_bp
    from backend.routes.streaming import streaming_bp

    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(voice_bp, url_prefix='/api')
    app.register_blueprint(molecule_bp, url_prefix='/api')
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(streaming_bp, url_prefix='/api')

