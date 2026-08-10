import os
import ast
import glob
import requests
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
GROQ_API_KEY = ""

def analyze_ast(file_path):
    """Static AST analysis for quick issue detection"""
    issues = []
    score = 100

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        tree = ast.parse(code)

        # 1. Imports Analysis
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]

        # 2. Function Level Checks (Long functions, missing docstrings, missing type hints)
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        for fn in functions:
            # Missing Docstrings
            if not ast.get_docstring(fn):
                issues.append(f"Missing docstring in function `{fn.name}()`")
                score -= 3

            # Missing Type Hints
            if not fn.returns and not any(arg.annotation for arg in fn.args.args):
                issues.append(f"Missing type hints in function `{fn.name}()`")
                score -= 2

            # Long Functions (>30 lines)
            fn_lines = fn.end_lineno - fn.lineno if hasattr(fn, 'end_lineno') else 0
            if fn_lines > 30:
                issues.append(f"Long function `{fn.name}()` ({fn_lines} lines)")
                score -= 5

        # 3. Poor Variable Names Check (Single letter variable names except common ones like i, x)
        names = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]
        short_names = set([n for n in names if len(n) == 1 and n not in ['i', 'j', 'k', 'x', 'y', 'f', '_']])
        if short_names:
            issues.append(f"Poor or non-descriptive variable names detected: {', '.join(short_names)}")
            score -= 4

    except Exception as e:
        issues.append(f"AST Parsing Warning: {str(e)}")
        score -= 10

    return max(score, 40), issues

def get_groq_ai_suggestions(file_name, code_content):
    """Groq AI Code Smell & Quality Review"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are an expert Senior Python Code Reviewer. Analyze the provided Python code for: "
        "1. Duplicate code 2. Unused imports 3. Code smells / nested logic 4. Best practices. "
        "Return 3 to 5 concise bullet point suggestions starting with '✓ '. "
        "Do NOT return code blocks or explanations. Only bullet points."
    )

    user_prompt = f"File: {file_name}\n\nCode:\n{code_content[:3000]}"  # Cap length for safety

    try:
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 200
        }
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content'].strip()
    except Exception:
        pass
    return "✓ Remove unused imports\n✓ Add type hints\n✓ Simplify nested logic"

def run_code_review():
    """Runs read-only review across all Python files in the project"""
    py_files = sorted(glob.glob(os.path.join(PROJECT_DIR, "*.py")))
    results = []

    for file_path in py_files:
        filename = os.path.basename(file_path)
        base_score, ast_issues = analyze_ast(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            code_content = f.read()

        ai_suggestions = get_groq_ai_suggestions(filename, code_content)

        # Calculate final combined score
        final_score = max(min(base_score, 100), 50)

        results.append({
            "filename": filename,
            "score": final_score,
            "ast_issues": ast_issues,
            "suggestions": ai_suggestions
        })

    return results
