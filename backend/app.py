"""FastAPI/Flask entry point"""
from flask import Flask, render_template_string
from config import PORT, DEBUG, BASE_DIR
from routes import api_bp
from pathlib import Path

app = Flask(__name__)

# Register API blueprint
app.register_blueprint(api_bp, url_prefix='')

# Load HTML template
def load_html_template():
    """Load HTML template from frontend"""
    # Try project-relative frontend paths
    possible_paths = [
        BASE_DIR / 'frontend' / 'index.html',
        Path('frontend') / 'index.html',
        Path(__file__).resolve().parent.parent / 'frontend' / 'index.html'
    ]

    for template_path in possible_paths:
        try:
            if template_path.exists():
                return template_path.read_text(encoding='utf-8')
        except Exception:
            continue

    return "<h1>Frontend not found. Please ensure index.html exists in frontend folder.</h1>"


@app.route('/')
def home():
    """Serve main page"""
    html_template = load_html_template()
    return render_template_string(html_template)


if __name__ == '__main__':
    print("=" * 70)
    print("🎤 3D Avatar Q&A with Real-Time Lip Sync")
    print("=" * 70)
    print(f"Server starting on http://localhost:{PORT}")
    print()
    print("📁 Files needed:")
    print("   - avatar.glb (your 3D model) - optional")
    print("   - resume.txt (your resume content)")
    print()
    print("✨ Features:")
    print("   - Real-time lip syncing with wawa-lipsync")
    print("   - Voice input and output")
    print("   - 3D avatar animations")
    print()
    print("🎮 Controls:")
    print("   - Drag to rotate • Scroll to zoom • Click mic to speak")
    print()
    print("=" * 70)
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)
