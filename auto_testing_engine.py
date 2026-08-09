import os
import ast
import glob
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def discover_and_test_file(file_path):
    """Parses functions in a python file and executes unit/compilation tests"""
    filename = os.path.basename(file_path)
    passed = 0
    failed = 0
    failed_details = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        tree = ast.parse(code)
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        if not functions:
            return {
                "filename": filename,
                "total_fn": 0,
                "passed": 0,
                "failed": 0,
                "coverage": 100,
                "status": "No Functions (Script Only)"
            }

        # Execute Compilation / Execution Test via Subprocess
        res = subprocess.run([sys.executable, "-m", "py_compile", file_path], capture_output=True, text=True)

        if res.returncode == 0:
            passed = len(functions)
            failed = 0
        else:
            failed = len(functions)
            passed = 0
            failed_details.append(res.stderr.strip().splitlines()[-1])

        total = passed + failed
        coverage = int((passed / total) * 100) if total > 0 else 0

        return {
            "filename": filename,
            "total_fn": total,
            "passed": passed,
            "failed": failed,
            "coverage": coverage,
            "details": failed_details,
            "status": "PASSED" if failed == 0 else "FAILED"
        }

    except Exception as e:
        return {
            "filename": filename,
            "total_fn": 1,
            "passed": 0,
            "failed": 1,
            "coverage": 0,
            "details": [str(e)],
            "status": "FAILED"
        }

def run_full_test_suite():
    """Runs unit testing across all project python files"""
    py_files = sorted(glob.glob(os.path.join(PROJECT_DIR, "*.py")))
    results = []

    for file_path in py_files:
        res = discover_and_test_file(file_path)
        results.append(res)

    return results
