# Portfolio AI - 3D Avatar Q&A System

An interactive 3D avatar portfolio website that uses AI to answer questions about your resume with real-time lip synchronization.

## 🎯 Features

- **3D Avatar**: Interactive 3D face model with Oculus Visemes support
- **Voice Input**: Real-time speech recognition using Web Speech API
- **AI Responses**: Gemini-powered responses based on your resume
- **Lip Sync**: Real-time lip synchronization with audio responses
- **Natural Animations**: Idle animations, eye blinking, and body movements

# Portfolio AI — 3D Avatar Q&A

An interactive 3D avatar portfolio application that answers questions about a resume using a generative AI model and provides real-time lip-synced audio.

Features
- 3D avatar with Oculus Viseme support
- Voice input and real-time text-to-speech responses
- RAG (Retriever-Augmented Generation) using your resume as context
- Project-friendly, environment-driven configuration

Quick start (Windows PowerShell)

1. Clone the repo and enter the folder:

```powershell
git clone <repo-url>
cd portfolio-ai
```

2. Create and activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
cd backend
pip install -r requirements.txt
```

4. Add your Gemini API key (recommended: use a `.env` file in project root):

```powershell
copy .env.example .env
# then edit .env and set GEMINI_API_KEY=your_key_here
```

Alternatively set it for the current PowerShell session:

```powershell
$env:GEMINI_API_KEY = 'your_gemini_key_here'
```

5. Run the server:

```powershell
python app.py
```

Open http://localhost:5000 in your browser.

Environment variables (example `.env`)

GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.0-flash
PORT=5000
RESUME_FILE=resume.txt
AVATAR_MODEL_PATH=frontend/assets/avatar.glb

Notes about recent changes
- Hard-coded API keys and absolute system paths were removed; `backend/config.py` now reads `GEMINI_API_KEY` and path defaults from environment and resolves project-relative paths via `BASE_DIR`.

Common Git commands to commit these changes

```bash
git status
git add -A
git commit -m "chore: normalize paths, remove hard-coded API key, update README"
git push origin main
```

If you prefer to create a branch first:

```bash
git checkout -b fix/config-paths
git add -A
git commit -m "fix: use project-relative paths and env vars for config"
git push -u origin fix/config-paths
```

Where to look in the codebase
- `backend/config.py` — project `BASE_DIR`, env-driven config
- `backend/app.py` — serves `frontend/index.html` using project paths
- `backend/routes.py` — serves frontend assets via `BASE_DIR`

If you want, I can also:
- update `.env.example` to remove example API keys
- add a startup check that fails fast if `GEMINI_API_KEY` is missing

---
Updated README to be GitHub-friendly and include run/commit commands.
