# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import shutil
from pathlib import Path

# Find Tesseract binary and data
tesseract_path = shutil.which('tesseract')
tesseract_binaries = []
tessdata_files = []

if tesseract_path:
    tesseract_binaries = [(tesseract_path, 'tesseract')]
    
    # Find tessdata directory
    possible_tessdata = [
        '/usr/share/tesseract-ocr/4.00/tessdata',
        '/usr/share/tesseract-ocr/5/tessdata',
        '/usr/share/tessdata',
    ]
    
    for tessdata_dir in possible_tessdata:
        if os.path.exists(tessdata_dir):
            # Include specific language files
            for lang_file in ['eng.traineddata', 'amh.traineddata', 'osd.traineddata']:
                lang_path = os.path.join(tessdata_dir, lang_file)
                if os.path.exists(lang_path):
                    tessdata_files.append((lang_path, 'tessdata'))
            break

a = Analysis(
    ['web_server.py', 'setup_runtime.py'],
    pathex=[],
    binaries=tesseract_binaries,
    datas=[
        ('data', 'data'),
        ('font', 'font'),
        ('setup_runtime.py', '.'),
    ] + tessdata_files,
    hiddenimports=[
        'PIL._tkinter_finder',
        'flask',
        'werkzeug',
        'jinja2',
        'click',
        'itsdangerous',
        'markupsafe',
        'qrcode',
        'barcode',
        'cv2',
        'numpy',
        'fitz',
        'pytesseract',
        'pyzbar',
        'convertdate',
        'pkg_resources.py2_warn',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['setup_runtime.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EthiopianIDGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if you have one
)
