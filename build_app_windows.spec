# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import sys

# ============================================================
# EASYOCR MODELS BUNDLING
# ============================================================
easyocr_models = []

# Find EasyOCR model directory
try:
    import easyocr
    # EasyOCR stores models in ~/.EasyOCR/model/
    user_home = os.path.expanduser('~')
    easyocr_model_dir = os.path.join(user_home, '.EasyOCR', 'model')
    
    if os.path.exists(easyocr_model_dir):
        print(f"Found EasyOCR models at: {easyocr_model_dir}")
        # Bundle all model files
        for file in os.listdir(easyocr_model_dir):
            model_path = os.path.join(easyocr_model_dir, file)
            if os.path.isfile(model_path):
                easyocr_models.append((model_path, '.EasyOCR/model'))
                print(f"  → Bundling model: {file}")
    else:
        print("WARNING: EasyOCR models not found!")
        print("  → Run the app once to download models before building")
except ImportError:
    print("WARNING: EasyOCR not installed!")
    print("  → Install with: pip install easyocr")

# ============================================================
# PYZBAR DLL BUNDLING
# ============================================================
pyzbar_binaries = []
try:
    import pyzbar
    pyzbar_path = os.path.dirname(pyzbar.__file__)
    
    # Find the main DLL
    dll_names = ['libzbar-64.dll', 'libzbar.dll', 'zbar.dll']
    main_dll = None
    
    for dll_name in dll_names:
        dll_path = os.path.join(pyzbar_path, dll_name)
        if os.path.exists(dll_path):
            main_dll = dll_path
            break
    
    if main_dll:
        # Add main DLL to root and pyzbar folder
        pyzbar_binaries.extend([
            (main_dll, '.'),
            (main_dll, 'pyzbar'),
        ])
        
        # Also look for any other DLLs in pyzbar directory
        for file in os.listdir(pyzbar_path):
            if file.endswith('.dll'):
                dll_full_path = os.path.join(pyzbar_path, file)
                pyzbar_binaries.extend([
                    (dll_full_path, '.'),
                    (dll_full_path, 'pyzbar'),
                ])
                
except ImportError:
    pass

# ============================================================
# FONT FILES BUNDLING
# ============================================================
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

# ============================================================
# PYINSTALLER ANALYSIS
# ============================================================
a = Analysis(
    ['web_server.py', 'setup_runtime.py'],
    pathex=[],
    binaries=pyzbar_binaries,
    datas=[
        ('data', 'data'),
        ('font', 'font'),
        ('setup_runtime.py', '.'),
    ] + easyocr_models + font_files,
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
        'easyocr',
        'easyocr.recognition',
        'easyocr.detection',
        'easyocr.utils',
        'pyzbar',
        'pyzbar.pyzbar',
        'pyzbar.wrapper',
        'pyzbar.zbar_library',
        'convertdate',
        'pkg_resources.py2_warn',
        'torch',
        'torchvision',
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
