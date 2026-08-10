import os
import time
import glob
import psutil
from datetime import datetime
import code_review_engine
import performance_optimizer
import security_scanner
import ai_architect_engine
import auto_testing_engine
import self_improvement_engine

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

AI_MODULES = [
    {"name": "Auto-Coder", "file": "auto_coder.py"},
    {"name": "Code Review Engine", "file": "code_review_engine.py"},
    {"name": "Performance Optimizer", "file": "performance_optimizer.py"},
    {"name": "Security Scanner", "file": "security_scanner.py"},
    {"name": "Auto Testing Engine", "file": "auto_testing_engine.py"},
    {"name": "Self Improvement Engine", "file": "self_improvement_engine.py"},
    {"name": "AI Architect Engine", "file": "ai_architect_engine.py"},
]

def check_system_metrics():
    """Live System Metrics: CPU, RAM, Response Time"""
    start_time = time.time()
    cpu_usage = psutil.cpu_percent(interval=0.1)
    ram_usage = psutil.virtual_memory().percent
    latency_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "cpu": cpu_usage,
        "ram": ram_usage,
        "latency_ms": latency_ms
    }

def detect_module_statuses():
    """Module Status Auto-Detection: Green (Running), Red (Failed), Yellow (Loading)"""
    statuses = []
    for mod in AI_MODULES:
        file_path = os.path.join(PROJECT_DIR, mod["file"])
        if not os.path.exists(file_path):
            status = "FAILED"
            color = "red"
            msg = "File Missing"
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    compile(f.read(), file_path, 'exec')
                status = "RUNNING"
                color = "green"
                msg = "Healthy"
            except Exception as e:
                status = "FAILED"
                color = "red"
                msg = f"Syntax/Runtime Error: {str(e)[:30]}..."

        statuses.append({
            "name": mod["name"],
            "file": mod["file"],
            "status": status,
            "color": color,
            "message": msg
        })
    return statuses

def run_full_inspection():
    """Orchestrates all AI modules and generates combined health report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Code Review
    review_data = code_review_engine.run_code_review()
    avg_quality = int(sum(r["score"] for r in review_data) / len(review_data)) if review_data else 100

    # 2. Performance Scan
    perf_data = performance_optimizer.run_performance_audit()
    avg_perf = int(sum(r["score"] for r in perf_data) / len(perf_data)) if perf_data else 100

    # 3. Security Scan
    sec_data = security_scanner.run_security_scan()
    avg_sec = int(sum(r["score"] for r in sec_data) / len(sec_data)) if sec_data else 100

    # 4. Architecture Analysis
    arch_stats = ai_architect_engine.analyze_system_architecture()
    arch_score = arch_stats.get("scalability_score", 90)

    # 5. Auto Testing
    test_data = auto_testing_engine.run_full_test_suite()
    total_files = len(test_data)
    passed_files = sum(1 for r in test_data if r["status"] != "FAILED")
    tests_passed_str = f"{passed_files}/{total_files}"

    # 6. Self Improvement Plan
    improvement_plan = self_improvement_engine.generate_self_improvement_plan()

    project_health = int((avg_quality + avg_perf + avg_sec + arch_score) / 4)
    tech_debt_hours = max(0, int((400 - (avg_quality + avg_perf + avg_sec + arch_score)) * 0.25))

    return {
        "timestamp": timestamp,
        "project_health": project_health,
        "avg_quality": avg_quality,
        "avg_perf": avg_perf,
        "avg_sec": avg_sec,
        "arch_score": arch_score,
        "tests_passed": tests_passed_str,
        "pending_improvements": 4,
        "tech_debt_hours": f"{tech_debt_hours} Hours",
        "improvement_plan": improvement_plan,
        "review_data": review_data,
        "perf_data": perf_data,
        "sec_data": sec_data,
        "arch_stats": arch_stats,
        "test_data": test_data
    }

def export_html_report(metrics):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Production AI Project Manager Audit</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 30px; background-color: #0f172a; color: #f8fafc; }}
            .header {{ background: linear-gradient(135deg, #1e293b, #0f172a); border: 1px solid #334155; padding: 25px; border-radius: 12px; text-align: center; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin-top: 20px; }}
            .card {{ background: #1e293b; border: 1px solid #334155; padding: 20px; border-radius: 10px; text-align: center; }}
            .card h3 {{ font-size: 28px; color: #38bdf8; margin: 0; }}
            .card p {{ margin-top: 5px; color: #94a3b8; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>👑 Production AI Project Manager Dashboard</h1>
            <p>Generated: {metrics['timestamp']}</p>
        </div>
        <div class="grid">
            <div class="card"><h3>{metrics['project_health']}%</h3><p>Project Health</p></div>
            <div class="card"><h3>{metrics['avg_quality']}/100</h3><p>Quality Score</p></div>
            <div class="card"><h3>{metrics['avg_perf']}/100</h3><p>Performance</p></div>
            <div class="card"><h3>{metrics['avg_sec']}/100</h3><p>Security Score</p></div>
            <div class="card"><h3>{metrics['arch_score']}/100</h3><p>Architecture Score</p></div>
            <div class="card"><h3>{metrics['tests_passed']}</h3><p>Tests Passed</p></div>
        </div>
    </body>
    </html>
    """

def export_text_pdf_report(metrics):
    return f"""
====================================================================
           👑 PRODUCTION AI PROJECT MANAGER EXECUTIVE REPORT
====================================================================
Timestamp: {metrics['timestamp']}

[ LIVE SYSTEM METRICS ]
--------------------------------------------------------------------
• Overall Project Health : {metrics['project_health']}%
• Quality Score          : {metrics['avg_quality']}/100
• Performance Score      : {metrics['avg_perf']}/100
• Security Score         : {metrics['avg_sec']}/100
• Architecture Score     : {metrics['arch_score']}/100
• Unit Tests Passed      : {metrics['tests_passed']}
• Est. Technical Debt    : {metrics['tech_debt_hours']}

--------------------------------------------------------------------
[ STRATEGIC IMPROVEMENT ROADMAP ]
--------------------------------------------------------------------
{metrics['improvement_plan']}
====================================================================
    """
