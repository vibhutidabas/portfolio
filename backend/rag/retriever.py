"""Resume embeddings & search"""
# This module can be extended for vector search if needed
# Currently using direct context retrieval

def retrieve_context(query: str) -> str:
    """
    Retrieve relevant context from resume
    
    Args:
        query: User query
        
    Returns:
        Relevant context string
    """
    from rag.index import get_context
    # For now, return full context
    # Can be enhanced with semantic search later
    return get_context()
