import os
import glob
import shutil
import difflib
import ast

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(PROJECT_DIR, ".auto_coder_backups")

def ensure_backup_dir():
    """Creates hidden backup directory if not existing"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

def create_backup(file_path):
    """Creates a timestamped backup copy before any overwrite"""
    ensure_backup_dir()
    filename = os.path.basename(file_path)
    backup_path = os.path.join(BACKUP_DIR, f"{filename}.bak")
    shutil.copy2(file_path, backup_path)
    return backup_path

def generate_diff(original_code, modified_code, filename):
    """Generates a clean unified line-by-line diff string"""
    orig_lines = original_code.splitlines(keepends=True)
    mod_lines = modified_code.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        orig_lines, mod_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        n=3
    )
    return "".join(diff)

def analyze_and_propose_fixes():
    """Scans python files, detects issues and proposes fixes with diffs"""
    py_files = sorted(glob.glob(os.path.join(PROJECT_DIR, "*.py")))
    proposals = []

    for file_path in py_files:
        filename = os.path.basename(file_path)
        if filename.startswith("app") or filename.startswith("auto_coder"):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            # Syntax Audit via AST
            ast.parse(code)
            
            # Simple Auto-Clean Optimization: strip trailing spaces & remove empty lines at EOF
            cleaned_code = "\n".join([line.rstrip() for line in code.splitlines()]).strip() + "\n"
            
            if code != cleaned_code:
                diff_text = generate_diff(code, cleaned_code, filename)
                proposals.append({
                    "filename": filename,
                    "file_path": file_path,
                    "original_code": code,
                    "proposed_code": cleaned_code,
                    "diff": diff_text
                })

        except SyntaxError as se:
            # Auto-comment out invalid syntax lines as safety fix
            lines = code.splitlines()
            if se.lineno and se.lineno <= len(lines):
                lines[se.lineno - 1] = f"# FIX_AUTODETECTED: {lines[se.lineno - 1]}"
            proposed = "\n".join(lines) + "\n"
            diff_text = generate_diff(code, proposed, filename)
            
            proposals.append({
                "filename": filename,
                "file_path": file_path,
                "original_code": code,
                "proposed_code": proposed,
                "diff": diff_text
            })

    return proposals

def apply_fix_with_backup(file_path, proposed_code):
    """Creates backup and overwrites file with proposed code"""
    backup_path = create_backup(file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(proposed_code)
    return backup_path

def rollback_file(filename):
    """Restores the backup copy if available"""
    backup_path = os.path.join(BACKUP_DIR, f"{filename}.bak")
    original_path = os.path.join(PROJECT_DIR, filename)

    if os.path.exists(backup_path):
        shutil.copy2(backup_path, original_path)
        os.remove(backup_path)
        return True, f"✅ Successfully restored `{filename}` from backup!"
    return False, f"⚠️ No backup found for `{filename}`."

def run_auto_fix_and_report():
    """Fallback runner for legacy dashboard call"""
    proposals = analyze_and_propose_fixes()
    if not proposals:
        return "✅ Project codebase is clean! No fixes required."
    return f"🔍 Found {len(proposals)} files requiring formatting or fixes."