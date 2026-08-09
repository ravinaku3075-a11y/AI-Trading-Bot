import os
import requests
import logging

logger = logging.getLogger(__name__)

class OllamaConnector:
    def __init__(self, host=None, model=None, timeout=5):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", timeout))

    def generate_response(self, prompt: str) -> dict:
        if not prompt or not prompt.strip():
            return {"success": False, "error": "Empty prompt provided", "response": ""}

        url = f"{self.host.rstrip('/')}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        try:
            res = requests.post(url, json=payload, timeout=self.timeout)
            if res.status_code == 200:
                data = res.json()
                response_text = data.get("response", "")
                if not response_text:
                    return {"success": False, "error": "Invalid/Empty response from Ollama", "response": ""}
                return {"success": True, "response": response_text, "error": None}
            else:
                return {"success": False, "error": f"HTTP Error {res.status_code}", "response": ""}
        except requests.exceptions.Timeout:
            logger.warning("Ollama connection timed out.")
            return {"success": False, "error": "Connection Timeout", "response": ""}
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ollama service unavailable: {e}")
            return {"success": False, "error": "Service Unavailable", "response": ""}
        except Exception as e:
            logger.error(f"Unexpected error in Ollama connector: {e}")
            return {"success": False, "error": str(e), "response": ""}