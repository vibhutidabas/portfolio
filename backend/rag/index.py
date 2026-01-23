"""Vector store setup for RAG"""
# This module can be extended for vector store setup if needed
# Currently using direct text context from resume file

def setup_vector_store():
    """Setup vector store for embeddings (future implementation)"""
    pass

def get_context():
    """Get context from resume (currently direct file read)"""
    from models.resume_loader import read_resume
    return read_resume()
