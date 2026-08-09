import os
import ast
import glob
import requests
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
GROQ_API_KEY = ""

def analyze_performance_ast(file_path):
    """Static AST Scan for Performance Bottlenecks"""
    issues = []
    score = 100

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        tree = ast.parse(code)

        # 1. Check for loops containing nested loops or heavy calls
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Check nested loops
                nested_loops = [n for n in ast.walk(node) if isinstance(n, (ast.For, ast.While)) and n != node]
                if nested_loops:
                    issues.append("Nested loop detected (O(n²) complexity risk)")
                    score -= 10

                # Check for network/API/file I/O calls inside loops
                for sub_node in ast.walk(node):
                    if isinstance(sub_node, ast.Call):
                        func_name = ""
                        if isinstance(sub_node.func, ast.Name):
                            func_name = sub_node.func.id
                        elif isinstance(sub_node.func, ast.Attribute):
                            func_name = sub_node.func.attr

                        if func_name in ['get', 'post', 'request', 'download', 'read', 'write', 'sleep']:
                            issues.append(f"Potential blocking I/O call `{func_name}()` inside loop")
                            score -= 12

        # 2. Check for broad global variables or un-cached repeat operations
        global_vars = [node for node in ast.walk(tree) if isinstance(node, ast.Global)]
        if len(global_vars) > 3:
            issues.append(f"Multiple global variables ({len(global_vars)}) may impact execution performance")
            score -= 5

    except Exception as e:
        issues.append(f"AST Analysis Warning: {str(e)}")
        score -= 5

    return max(score, 30), issues

def get_groq_performance_advice(file_name, code_content):
    """Groq AI Performance Analysis"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are an expert Python Performance Optimization Engineer. Analyze the provided code for: "
        "1. Memory bottlenecks 2. Speed optimizations (vectorization, caching, async) "
        "3. Redundant operations. "
        "Return 3 to 4 actionable, concise bullet points starting with '⚡ '. "
        "Do NOT return code blocks or prose text. Only bullet points."
    )

    user_prompt = f"File: {file_name}\n\nCode:\n{code_content[:3000]}"

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
    return "⚡ Use @st.cache_data for heavy API operations\n⚡ Vectorize DataFrame iterations with pandas\n⚡ Avoid blocking network calls in main thread"

def run_performance_audit():
    """Runs read-only performance scan across all Python files"""
    py_files = sorted(glob.glob(os.path.join(PROJECT_DIR, "*.py")))
    results = []

    for file_path in py_files:
        filename = os.path.basename(file_path)
        base_score, ast_issues = analyze_performance_ast(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            code_content = f.read()

        ai_advice = get_groq_performance_advice(filename, code_content)
        final_score = max(min(base_score, 100), 40)

        results.append({
            "filename": filename,
            "score": final_score,
            "ast_issues": ast_issues,
            "advice": ai_advice
        })

    return results
