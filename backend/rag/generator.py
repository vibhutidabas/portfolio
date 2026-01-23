"""Gemini response generation logic"""
import google.genai as genai
from typing import List, Tuple
from config import GEMINI_API_KEY, GEMINI_MODEL


def generate_response(
    question: str,
    context: str,
    conversation_history: List[Tuple[str, str]] = None
) -> str:
    """
    Generate response using Gemini AI
    
    Args:
        question: User's question
        context: Resume context
        conversation_history: List of (question, answer) tuples
        
    Returns:
        Generated answer text
    """
    if conversation_history is None:
        conversation_history = []
    
    # Format history as text
    history_text = ""
    for q, a in conversation_history:
        history_text += f"Previous question: {q}\nPrevious answer: {a}\n\n"
    
    # Build prompt
    prompt = f"""
    Only start with a salutation if the user does so.
You are assisting the user by answering questions using the provided resume documents only where you will try to answer in a summary manner and only going in detail when asked.
Respond in first person ("I", "my experience", "my background") as if you are the owner of the resume.
In case asked about 'tell me about this portfolio.', refer to 'PROJECT: QandA System by Text Extraction from PDF' in projects and phrase it accordingly.

Do NOT invent personal information that is not in the retrieved documents.
If the answer is not found or looks closer to an information you have, first ask a follow up question to clarify, otherwise choose between with:
"That information isn't in my resume. Would you like to know anything else?" OR add a funny answer.

Tone: concise, professional, confident, clear.

Conversation history:
{history_text}

RAG Context:
{context}

User question: {question}

Answer:"""
    
    # Configure API key from environment-configured value
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    
    return response.text

