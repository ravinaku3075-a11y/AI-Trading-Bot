import os
import requests
import logging
from local_ai_connector import OllamaConnector

logger = logging.getLogger(__name__)

class AIProvider:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        self.ollama = OllamaConnector()

    def generate_chat_completion(self, prompt: str, system_prompt: str = "You are a helpful assistant.", model: str = "llama-3.1-70b-versatile", timeout: int = 5) -> dict:
        if not prompt or not prompt.strip():
            return {"success": False, "provider": None, "response": "", "error": "Empty prompt provided"}

        # 1. Try Primary Provider: Groq
        if self.groq_api_key:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            }
            try:
                res = requests.post(self.groq_url, json=payload, headers=headers, timeout=timeout)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices and len(choices) > 0:
                        content = choices[0].get("message", {}).get("content", "")
                        if content:
                            return {"success": True, "provider": "Groq", "response": content, "error": None}
                else:
                    logger.warning(f"Groq primary call failed with status code {res.status_code}. Initiating fallback...")
            except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
                logger.warning(f"Groq primary call failed due to network error: {e}. Initiating fallback...")
            except Exception as e:
                logger.error(f"Unexpected error in Groq provider call: {e}")
        else:
            logger.warning("Groq API key not configured or missing. Initiating fallback...")

        # 2. Fallback Provider: Ollama Local AI
        logger.info("Attempting fallback to Local Ollama AI...")
        ollama_res = self.ollama.generate_response(prompt)
        if ollama_res["success"]:
            return {"success": True, "provider": "Ollama", "response": ollama_res["response"], "error": None}

        # 3. Both Providers Failed
        return {
            "success": False,
            "provider": None,
            "response": "",
            "error": "Both primary (Groq) and fallback (Ollama) providers failed or were unavailable."
        }

def ask_ai(prompt: str, system_prompt: str = "You are a helpful assistant.") -> dict:
    provider = AIProvider()
    return provider.generate_chat_completion(prompt=prompt, system_prompt=system_prompt)