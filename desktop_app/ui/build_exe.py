import os
import sys
import shutil
import subprocess

def build_executable():
    print("=================================================================")
    print("   AI Trading Terminal v2.2 - Production Build Script")
    print("=================================================================\n")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) == "ui":
        project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    elif os.path.basename(current_dir) == "desktop_app":
        project_root = os.path.abspath(os.path.join(current_dir, ".."))
    else:
        project_root = current_dir

    os.chdir(project_root)
    print(f"[INFO] Project Root Directory: {project_root}")

    # 1. Clean previous builds
    print("[INFO] Cleaning old build and dist directories...")
    for folder in ['build', 'dist']:
        folder_path = os.path.join(project_root, folder)
        if os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path, ignore_errors=True)
            except Exception:
                pass

    for file in os.listdir(project_root):
        if file.endswith('.spec'):
            try:
                os.remove(os.path.join(project_root, file))
            except Exception:
                pass

    # 2. PyInstaller Build Command
    main_script = os.path.join("desktop_app", "main.py")
    
    build_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=AI_Trading_Terminal",
        "--paths=.",
        "--paths=desktop_app",
        "--hidden-import=psutil",
        "--collect-all=streamlit",
        "--collect-all=altair",
        "--collect-all=pydeck",
        "--collect-all=psutil",
        "--copy-metadata=streamlit",
        "--add-data=app.py;.",
        "--add-data=reasoning_engine.py;.",
        "--add-data=voice_assistant.py;.",
        "--add-data=chart_vision.py;.",
        "--add-data=paper_trading.py;.",
        "--add-data=portfolio_viewer.py;.",
        "--add-data=backtesting_engine.py;.",
        "--add-data=telegram_notifier.py;.",
        "--add-data=risk_engine.py;.",
        "--add-data=sqlite_logger.py;.",
        "--add-data=desktop_app;desktop_app",
        main_script
    ]

    print("\n[INFO] Executing PyInstaller build command...")
    print("-----------------------------------------------------------------")
    
    try:
        result = subprocess.run(build_cmd, check=True)
        if result.returncode == 0:
            output_path = os.path.join(project_root, "dist", "AI_Trading_Terminal")
            
            # 3. DIRECT HARD COPY OF PSUTIL INTO DIST FOLDER
            print("\n[INFO] Force-copying psutil directly into dist folder...")
            import psutil
            psutil_src_dir = os.path.dirname(psutil.__file__)
            psutil_dest_dir = os.path.join(output_path, "psutil")
            
            if os.path.exists(psutil_dest_dir):
                shutil.rmtree(psutil_dest_dir, ignore_errors=True)
            
            shutil.copytree(psutil_src_dir, psutil_dest_dir)
            print(f"       [SUCCESS] Copied psutil from '{psutil_src_dir}' -> '{psutil_dest_dir}'")

            print("-----------------------------------------------------------------")
            print("\n[SUCCESS] BUILD COMPLETED SUCCESSFULLY!")
            print(f"[EXECUTABLE] {os.path.join(output_path, 'AI_Trading_Terminal.exe')}\n")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] BUILD FAILED with exit code: {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during build: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()