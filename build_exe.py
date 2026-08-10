import os, sys, subprocess

print('--- CLEANING & REBUILDING STANDALONE EXE ---')

cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--noconfirm',
    '--onedir',
    '--windowed',
    '--name=AI_Trading_Assistant',
    '--clean',
    '--hidden-import=streamlit',
    '--hidden-import=PyQt6',
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=PyQt6.QtWidgets',
    '--hidden-import=PyQt6.QtWebEngineWidgets',
    '--hidden-import=groq',
    '--hidden-import=pkgutil',
    '--exclude-module=dotenv.env',
    'run_desktop.py'
]

print('Running PyInstaller Build...')
res = subprocess.run(cmd)
if res.returncode == 0:
    print('SUCCESS: Build completed without memory error!')
else:
    print('FAILED: Build exited with error.')
