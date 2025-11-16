# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import sys

# Paths for Windows Tesseract (adjust if needed)
tesseract_binaries = []
tessdata_files = []

# Common Tesseract installation paths on Windows
tesseract_paths = [
    r'C:\Program Files\Tesseract-OCR',
    r'C:\Program Files (x86)\Tesseract-OCR',
]

for tess_path in tesseract_paths:
    if os.path.exists(tess_path):
        # Add tesseract.exe
        tess_exe = os.path.join(tess_path, 'tesseract.exe')
        if os.path.exists(tess_exe):
            tesseract_binaries.append((tess_exe, 'tesseract'))
        
        # Add tessdata files
        tessdata_dir = os.path.join(tess_path, 'tessdata')
        if os.path.exists(tessdata_dir):
            for lang_file in ['eng.traineddata', 'amh.traineddata', 'osd.traineddata']:
                lang_path = os.path.join(tessdata_dir, lang_file)
                if os.path.exists(lang_path):
                    tessdata_files.append((lang_path, 'tessdata'))
        break

# Find pyzbar DLL with comprehensive search
pyzbar_binaries = []
try:
    import pyzbar
    import site
    
    # Search in multiple locations
    search_paths = [
        os.path.dirname(pyzbar.__file__),
        os.path.join(os.path.dirname(pyzbar.__file__), 'pyzbar'),
    ] + site.getsitepackages()
    
    dll_names = ['libzbar-64.dll', 'libzbar.dll', 'zbar.dll']
    
    for search_path in search_paths:
        for dll_name in dll_names:
            dll_path = os.path.join(search_path, dll_name)
            if os.path.exists(dll_path):
                # Add to multiple locations to ensure it's found
                pyzbar_binaries.extend([
                    (dll_path, '.'),
                    (dll_path, 'pyzbar'),
                    (dll_path, 'lib'),
                ])
                break
        if pyzbar_binaries:
            break
except ImportError:
    pass

# Find Noto fonts - use local font folder
font_files = []
local_font_dir = 'font'
if os.path.exists(local_font_dir):
    for font_name in ['NotoSans-Regular.ttf', 'NotoSans-Bold.ttf', 'NotoSansEthiopic-Regular.ttf', 'NotoSansEthiopic-Bold.ttf']:
        font_path = os.path.join(local_font_dir, font_name)
        if os.path.exists(font_path):
            font_files.append((font_path, 'font'))

# Fallback to Windows system fonts
if not font_files:
    windows_fonts = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
    for font_name in ['NotoSans-Regular.ttf', 'NotoSans-Bold.ttf', 'NotoSansEthiopic-Regular.ttf', 'NotoSansEthiopic-Bold.ttf']:
        font_path = os.path.join(windows_fonts, font_name)
        if os.path.exists(font_path):
            font_files.append((font_path, 'font'))

a = Analysis(
    ['web_server.py', 'setup_runtime.py'],
    pathex=[],
    binaries=tesseract_binaries + pyzbar_binaries,
    datas=[
        ('data', 'data'),
        ('font', 'font'),
        ('setup_runtime.py', '.'),
    ] + tessdata_files + font_files,
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
        'pyzbar.pyzbar',
        'convertdate',
        'pkg_resources.py2_warn',
    ],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=['setup_runtime.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create single file executable
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
    console=True,  # Show console for testing
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
