"""API endpoints"""
from flask import Blueprint, request, jsonify, send_from_directory
from pathlib import Path

# Try different import paths for flexibility
from rag.retriever import retrieve_context
from rag.generator import generate_response
from audio.text_to_speech import text_to_speech
from config import BASE_DIR


api_bp = Blueprint('api', __name__)

# Store conversation history per session
conversation_history = {}


@api_bp.route('/ask', methods=['POST'])
def ask():
    """Handle question and return answer with audio"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        session_id = data.get('session_id', 'default')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        print(f"Question received: {question}")
        
        # Get or create conversation history for session
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        # Retrieve context
        context = retrieve_context(question)
        
        # Generate response
        answer_text = generate_response(
            question=question,
            context=context,
            conversation_history=conversation_history[session_id]
        )
        
        # Save to history
        conversation_history[session_id].append((question, answer_text))
        
        # Limit history length
        if len(conversation_history[session_id]) > 10:
            conversation_history[session_id] = conversation_history[session_id][-10:]
        
        print(f"Answer generated: {answer_text[:100]}...")
        
        # Convert to speech
        audio_base64 = text_to_speech(answer_text)
        
        return jsonify({
            'answer': answer_text,
            'audio': audio_base64
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/intro', methods=['GET'])
def get_intro():
    """Get intro speech audio"""
    try:
        intro_text = "Hello, I am Vibhuti! What would you like to know about me?"
        audio_base64 = text_to_speech(intro_text)
        
        return jsonify({
            'text': intro_text,
            'audio': audio_base64
        })
    except Exception as e:
        print(f"Error generating intro: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/styles.css')
def serve_css():
    """Serve CSS file"""
    return _serve_frontend_file('styles.css', 'text/css')


@api_bp.route('/script.js')
def serve_js():
    """Serve JavaScript file"""
    return _serve_frontend_file('script.js', 'application/javascript')


def _serve_frontend_file(filename, mimetype):
    """Helper function to serve frontend files"""
    # Try project-relative frontend paths
    possible_paths = [
        BASE_DIR / 'frontend' / filename,
        Path('frontend') / filename,
        Path(__file__).resolve().parent.parent / 'frontend' / filename
    ]

    for file_path in possible_paths:
        try:
            if file_path.exists():
                directory = str(file_path.parent)
                file_name = file_path.name
                return send_from_directory(directory, file_name, mimetype=mimetype)
        except Exception:
            continue

    return jsonify({'error': f'{filename} not found'}), 404


@api_bp.route('/frontend/assets/<path:filename>')
def serve_model(filename):
    """Serve 3D model files from frontend/assets directory"""
    return _serve_frontend_asset(filename)


@api_bp.route('/model/<path:filename>')
def serve_model_legacy(filename):
    """Legacy route for model files - redirects to frontend/assets"""
    return _serve_frontend_asset(filename)


def _serve_frontend_asset(filename):
    """Helper function to serve files from frontend/assets"""
    # Try project-relative frontend assets paths
    possible_paths = [
        BASE_DIR / 'frontend' / 'assets' / filename,
        Path('frontend') / 'assets' / filename,
        Path(__file__).resolve().parent.parent / 'frontend' / 'assets' / filename
    ]

    for file_path in possible_paths:
        try:
            if file_path.exists():
                directory = str(file_path.parent)
                file_name = file_path.name
                return send_from_directory(directory, file_name)
        except Exception:
            continue

    return jsonify({'error': f'Model file {filename} not found'}), 404
