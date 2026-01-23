"""Resume ingestion and parsing"""
from pathlib import Path
from typing import Optional


def read_resume(filepath: Optional[str] = None) -> str:
    """
    Read resume text from file
    
    Args:
        filepath: Path to resume file. If None, uses default from config
        
    Returns:
        Resume content as string
    """
    if filepath is None:
        from config import RESUME_FILE, BASE_DIR
        filepath = RESUME_FILE

    try:
        path = Path(filepath)

        # If not absolute and doesn't exist, try project base directory
        if not path.exists():
            candidate = Path(BASE_DIR) / path
            if candidate.exists():
                path = candidate

        if not path.exists():
            return "Resume file not found. Please ensure resume.txt exists."

        return path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return "Resume file not found. Please ensure resume.txt exists."
    except Exception as e:
        return f"Error reading resume: {str(e)}"
