import sys
import os
from unittest.mock import patch, MagicMock
from ai_provider import AIProvider, ask_ai
import security_scanner
import self_improvement_engine

def run_ai_provider_tests():
    print("--- RUNNING AI PROVIDER FALLBACK TESTS ---")
    provider = AIProvider()
    provider.groq_api_key = "mock_groq_key"

    # 1. Groq Primary Success
    with patch("requests.post") as mock_post:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {"choices": [{"message": {"content": "Groq Output"}}]}
        mock_post.return_value = mock_res

        res = provider.generate_chat_completion("Test Prompt")
        assert res["success"] is True
        assert res["provider"] == "Groq"
        assert res["response"] == "Groq Output"
        print("1. Groq Primary Success: PASSED")

    # 2. Groq Timeout -> Ollama Fallback
    import requests
    with patch("requests.post", side_effect=requests.exceptions.Timeout):
        with patch.object(provider.ollama, "generate_response", return_value={"success": True, "response": "Ollama Fallback Output"}):
            res = provider.generate_chat_completion("Test Prompt")
            assert res["success"] is True
            assert res["provider"] == "Ollama"
            assert res["response"] == "Ollama Fallback Output"
            print("2. Groq Timeout Fallback: PASSED")

    # 3. Groq HTTP 429 -> Ollama Fallback
    with patch("requests.post") as mock_post:
        mock_res = MagicMock()
        mock_res.status_code = 429
        mock_post.return_value = mock_res
        with patch.object(provider.ollama, "generate_response", return_value={"success": True, "response": "Ollama Rate Limit Fallback"}):
            res = provider.generate_chat_completion("Test Prompt")
            assert res["success"] is True
            assert res["provider"] == "Ollama"
            print("3. Groq HTTP 429 Fallback: PASSED")

    # 4. Groq HTTP 500/503 -> Ollama Fallback
    with patch("requests.post") as mock_post:
        mock_res = MagicMock()
        mock_res.status_code = 500
        mock_post.return_value = mock_res
        with patch.object(provider.ollama, "generate_response", return_value={"success": True, "response": "Ollama Server Error Fallback"}):
            res = provider.generate_chat_completion("Test Prompt")
            assert res["success"] is True
            assert res["provider"] == "Ollama"
            print("4. Groq HTTP 500 Fallback: PASSED")

    # 5. Invalid Response -> Ollama Fallback
    with patch("requests.post") as mock_post:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {"choices": []}
        mock_post.return_value = mock_res
        with patch.object(provider.ollama, "generate_response", return_value={"success": True, "response": "Ollama Empty Choice Fallback"}):
            res = provider.generate_chat_completion("Test Prompt")
            assert res["success"] is True
            assert res["provider"] == "Ollama"
            print("5. Invalid Groq Response Fallback: PASSED")

    # 6. Both Providers Down
    with patch("requests.post", side_effect=Exception("Groq Down")):
        with patch.object(provider.ollama, "generate_response", return_value={"success": False, "error": "Ollama Down", "response": ""}):
            res = provider.generate_chat_completion("Test Prompt")
            assert res["success"] is False
            assert "failed or were unavailable" in res["error"]
            print("6. Both Providers Down Handling: PASSED")

    # 7. Security Scanner Call Integration Test
    with patch("security_scanner.ask_ai", return_value={"success": True, "provider": "Groq", "response": "No vulnerabilities"}):
        out = security_scanner.get_groq_security_advice("main.py", "print('hello')")
        assert "Groq" in out
        print("7. Security Scanner Integration: PASSED")

    # 8. Self Improvement Engine Call Integration Test
    with patch("self_improvement_engine.ask_ai", return_value={"success": True, "provider": "Groq", "response": "Refactor code"}):
        out = self_improvement_engine.analyze_and_improve_code("Fix bug")
        assert out["success"] is True
        assert out["provider"] == "Groq"
        print("8. Self Improvement Engine Integration: PASSED")

    print("ALL AI PROVIDER FALLBACK TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_ai_provider_tests()