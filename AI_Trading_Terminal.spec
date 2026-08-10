# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 1. Collect all static assets and hidden modules for Streamlit & dependencies
datas = collect_data_files('streamlit')
datas += [('run_streamlit.py', '.')]

hiddenimports = collect_submodules('streamlit') + [
    'streamlit.web.cli',
    'streamlit.web.bootstrap',
    'streamlit.runtime.scriptrunner.magic_funcs',
    'streamlit.runtime.v2.state',
    'altair',
    'pandas',
    'numpy'
]

block_cipher = None

a = Analysis(
    ['run_desktop.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI_Trading_Terminal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to True so you can see any residual runtime logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI_Trading_Terminal',
)