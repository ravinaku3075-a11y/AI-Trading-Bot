import os
import logging
from ai_provider import ask_ai

logger = logging.getLogger(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def analyze_and_improve_code(prompt: str) -> dict:
    """
    Analyzes code or user prompts for self-improvement suggestions using centralized AI Provider.
    Falls back gracefully to Ollama if Groq is unavailable.
    """
    system_prompt = "You are an autonomous AI software developer focused on self-improvement and refactoring."
    res = ask_ai(prompt, system_prompt=system_prompt)
    
    if res["success"]:
        return {
            "success": True, 
            "provider": res["provider"], 
            "advice": res["response"]
        }
    return {
        "success": False, 
        "error": res["error"]
    }