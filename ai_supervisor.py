import time
import json
import os
import gc
import threading
from queue import Queue
from datetime import datetime

import code_review_engine
import performance_optimizer
import security_scanner
import auto_testing_engine
import self_improvement_engine
import project_manager

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(PROJECT_DIR, ".ai_supervisor_logs.json")

task_queue = Queue()
supervisor_thread = None
is_running = False

def append_log_entry(entry):
    """Saves structured log entry to JSON file"""
    logs = get_supervisor_logs()
    logs.insert(0, entry)
    logs = logs[:50]  # Keep last 50 execution logs
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
    except Exception:
        pass

def get_supervisor_logs():
    """Reads logs from storage"""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def execute_task_with_retry(task_name, func, max_retries=3):
    """Executes supervisor task with automated retry mechanism & memory cleanup"""
    attempts = 0
    while attempts < max_retries:
        try:
            attempts += 1
            result = func()
            log_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "task": task_name,
                "status": "SUCCESS",
                "attempt": attempts,
                "details": f"Task '{task_name}' executed successfully on attempt {attempts}."
            }
            append_log_entry(log_entry)
            gc.collect()  # Clean memory right after execution
            return True, result
        except Exception as e:
            if attempts >= max_retries:
                log_entry = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "task": task_name,
                    "status": "FAILED",
                    "attempt": attempts,
                    "details": f"Failed after {max_retries} retries. Error: {str(e)}"
                }
                append_log_entry(log_entry)
                gc.collect()
                return False, str(e)
            time.sleep(1)

def background_supervisor_worker():
    """Background Daemon Thread Loop with Memory Safety"""
    global is_running
    while is_running:
        if not task_queue.empty():
            task_name, func = task_queue.get()
            execute_task_with_retry(task_name, func)
            task_queue.task_done()
            gc.collect()  # Clear unreferenced objects in worker thread
        else:
            time.sleep(2)

def start_supervisor():
    """Starts background supervisor service"""
    global supervisor_thread, is_running
    if not is_running:
        is_running = True
        supervisor_thread = threading.Thread(target=background_supervisor_worker, daemon=True)
        supervisor_thread.start()

def stop_supervisor():
    """Stops background supervisor service"""
    global is_running
    is_running = False

def trigger_full_autonomous_cycle():
    """Queues all primary supervisor monitoring tasks"""
    tasks = [
        ("Auto Code Review", code_review_engine.run_code_review),
        ("Auto Performance Scan", performance_optimizer.run_performance_audit),
        ("Auto Security Scan", security_scanner.run_security_scan),
        ("Auto Testing Suite", auto_testing_engine.run_full_test_suite),
        ("Auto Self Improvement", self_improvement_engine.run_daily_project_scan),
        ("Auto Project Audit", project_manager.run_full_inspection)
    ]
    
    for name, fn in tasks:
        task_queue.put((name, fn))
        
    return len(tasks)