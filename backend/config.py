"""Configuration file for API keys and environment variables"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base project directory (two levels up from this file: backend/ -> project root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Gemini API Configuration - expect user to set this in environment
# e.g. export GEMINI_API_KEY="<your-key>"
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

# Flask Configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
PORT = int(os.getenv('PORT', 5000))
DEBUG = FLASK_ENV == 'development'

# File Paths (project-relative defaults)
RESUME_FILE = os.getenv('RESUME_FILE', str(BASE_DIR / 'resume.txt'))
AVATAR_MODEL_PATH = os.getenv('AVATAR_MODEL_PATH', str(BASE_DIR / 'frontend' / 'assets' / 'avatar.glb'))

# Conversation Settings
MAX_HISTORY_LENGTH = int(os.getenv('MAX_HISTORY_LENGTH', 10))
