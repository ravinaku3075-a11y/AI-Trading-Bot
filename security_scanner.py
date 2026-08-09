import os
import re
from ai_provider import ask_ai

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def get_groq_security_advice(file_name: str, code_content: str) -> str:
    """
    Analyzes code content for security vulnerabilities using the centralized AI provider.
    Automatically falls back from Groq to Ollama if primary provider is unavailable.
    """
    prompt = f"Analyze code in file '{file_name}' for security vulnerabilities:\n\n{code_content}"
    system_prompt = "You are a cybersecurity expert analyzing code for vulnerabilities."
    
    res = ask_ai(prompt, system_prompt=system_prompt)
    if res["success"]:
        return f"[{res['provider']}] {res['response']}"
        
    return f"Security Analysis Unavailable: {res['error']}"

def scan_file_for_hardcoded_secrets(file_path: str) -> list:
    """
    Scans a python file for potential hardcoded secrets/API keys using regex patterns.
    """
    findings = []
    if not os.path.exists(file_path):
        return findings

    patterns = {
        "Hardcoded Groq API Key": r'gsk_[a-zA-Z0-9]{32,}',
        "Hardcoded Telegram Token": r'\d{8,10}:[a-zA-Z0-9_-]{35}',
        "Generic Secret Key": r'(?i)(api_key|secret|password|token)\s*=\s*["\'][a-zA-Z0-9_\-]{8,}["\']'
    }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line_idx, line in enumerate(lines, 1):
                # Skip comments or env variable reads
                if line.strip().startswith("#") or "os.getenv" in line or "os.environ" in line:
                    continue
                for label, pattern in patterns.items():
                    if re.search(pattern, line):
                        findings.append(f"Line {line_idx}: {label} pattern detected")
    except Exception as e:
        findings.append(f"Scan Error: {str(e)}")

    return findings