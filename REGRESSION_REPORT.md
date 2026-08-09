# REGRESSION_REPORT.md

**Timestamp:** 2026-08-08 06:47:18
**Release Gate:** FAIL

## Summary Metrics
- **Total Tests:** 12
- **Passed:** 11
- **Failed:** 1
- **Skipped:** 0
- **Critical Failures:** 1

## Detailed Test Results

| Category | Test Name | Status | Timestamp |
|---|---|---|---|
| Import Validation | Import ai_engine | **PASS** | 2026-08-08 06:47:10 |
| Import Validation | Import ai_reasoning | **PASS** | 2026-08-08 06:47:10 |
| Import Validation | Import ai_supervisor | **PASS** | 2026-08-08 06:47:10 |
| Import Validation | Import agent_developer | **PASS** | 2026-08-08 06:47:10 |
| Import Validation | Import ai_architect_engine | **PASS** | 2026-08-08 06:47:10 |
| Import Validation | Import auto_coder | **PASS** | 2026-08-08 06:47:10 |
| Import Validation | Import auto_testing_engine | **PASS** | 2026-08-08 06:47:10 |
| Import Validation | Import alerts_engine | **PASS** | 2026-08-08 06:47:10 |
| Import Validation | Import backtesting_engine | **PASS** | 2026-08-08 06:47:12 |
| Import Validation | Import broker_api | **PASS** | 2026-08-08 06:47:12 |
| AI Assistant | Groq Engine Call | **FAIL** | 2026-08-08 06:47:18 |
| Discovered Tests | Run 1 unit tests | **PASS** | 2026-08-08 06:47:18 |

## Failure Analysis & Tracebacks

### Groq Engine Call (ai_engine)
- **Error:** Error code: 401 - {'error': {'message': 'Invalid API Key', 'type': 'invalid_request_error', 'code': 'invalid_api_key'}}
`python
Traceback (most recent call last):
  File "C:\Users\ravi\Desktop\AI-Trading-Bot\release_test_runner.py", line 50, in run_all_tests
    client.models.list()
  File "C:\Users\ravi\Desktop\AI-Trading-Bot\venv\Lib\site-packages\groq\resources\models.py", line 89, in list
    return self._get(
           ^^^^^^^^^^
  File "C:\Users\ravi\Desktop\AI-Trading-Bot\venv\Lib\site-packages\groq\_base_client.py", line 1215, in get
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\ravi\Desktop\AI-Trading-Bot\venv\Lib\site-packages\groq\_base_client.py", line 1071, in request
    raise self._make_status_error_from_response(err.response) from None
groq.AuthenticationError: Error code: 401 - {'error': {'message': 'Invalid API Key', 'type': 'invalid_request_error', 'code': 'invalid_api_key'}}

`
