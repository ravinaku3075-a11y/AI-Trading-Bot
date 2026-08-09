import sys
from unittest.mock import patch, MagicMock
from local_ai_connector import OllamaConnector

def run_ollama_connector_tests():
    print("--- RUNNING OLLAMA CONNECTOR TESTS ---")
    
    # 1. Import and Configuration Test
    connector = OllamaConnector(host="http://localhost:11434", model="llama3", timeout=2)
    assert connector.host == "http://localhost:11434"
    assert connector.model == "llama3"
    print("1. Config & Import Test: PASSED")

    # 2. Mock Successful Response Test
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Local AI Hello World"}
        mock_post.return_value = mock_response

        res = connector.generate_response("Hello")
        assert res["success"] is True
        assert res["response"] == "Local AI Hello World"
        print("2. Mock Success Response Test: PASSED")

    # 3. Unavailable / Connection Error Test
    with patch("requests.post", side_effect=Exception("Service Down")):
        res = connector.generate_response("Hello")
        assert res["success"] is False
        assert "error" in res
        print("3. Unavailable Service Handling Test: PASSED")

    # 4. Timeout Handling Test
    import requests
    with patch("requests.post", side_effect=requests.exceptions.Timeout):
        res = connector.generate_response("Hello")
        assert res["success"] is False
        assert res["error"] == "Connection Timeout"
        print("4. Timeout Handling Test: PASSED")

    # 5. Invalid / Empty Response Test
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": ""}
        mock_post.return_value = mock_response

        res = connector.generate_response("Hello")
        assert res["success"] is False
        assert "Invalid/Empty response" in res["error"]
        print("5. Invalid/Empty Response Handling Test: PASSED")

    print("ALL OLLAMA CONNECTOR TESTS PASSED!")

if __name__ == "__main__":
    run_ollama_connector_tests()