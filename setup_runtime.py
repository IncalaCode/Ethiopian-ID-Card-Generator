#!/usr/bin/env python3
"""
Runtime setup script to configure Tesseract and fonts paths
This runs when the bundled app starts
"""
import os
import sys

def setup_tesseract():
    """Configure Tesseract path for bundled executable"""
    if getattr(sys, 'frozen', False):
        # Running as bundled executable
        bundle_dir = sys._MEIPASS
        
        # Windows uses .exe extension
        if sys.platform == 'win32':
            tesseract_path = os.path.join(bundle_dir, 'tesseract', 'tesseract.exe')
        else:
            tesseract_path = os.path.join(bundle_dir, 'tesseract', 'tesseract')
        
        tessdata_path = os.path.join(bundle_dir, 'tessdata')
        
        # Set Tesseract paths
        if os.path.exists(tesseract_path):
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            print(f"✓ Tesseract configured: {tesseract_path}")
        
        # Set tessdata path
        if os.path.exists(tessdata_path):
            if sys.platform == 'win32':
                os.environ['TESSDATA_PREFIX'] = tessdata_path + '\\'
            else:
                os.environ['TESSDATA_PREFIX'] = tessdata_path + '/'
            print(f"✓ Tessdata configured: {tessdata_path}")
            # List available language files
            if os.path.isdir(tessdata_path):
                lang_files = [f for f in os.listdir(tessdata_path) if f.endswith('.traineddata')]
                print(f"  Available languages: {', '.join([f.replace('.traineddata', '') for f in lang_files])}")
        else:
            print("⚠ Tessdata not found in bundle, using system installation")

def setup_fonts():
    """Configure font paths for bundled executable"""
    if getattr(sys, 'frozen', False):
        # Running as bundled executable
        bundle_dir = sys._MEIPASS
        
        # Check font directory
        font_dirs = [
            os.path.join(bundle_dir, 'font')
        ]
        
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                os.environ['FONTCONFIG_PATH'] = font_dir
                print(f"✓ Fonts configured: {font_dir}")
                return
        
        print("⚠ Fonts not found in bundle, using system fonts")

def setup_pyzbar():
    """Configure pyzbar DLL path for Windows"""
    if getattr(sys, 'frozen', False) and sys.platform == 'win32':
        bundle_dir = sys._MEIPASS
        pyzbar_dir = os.path.join(bundle_dir, 'pyzbar')
        
        if os.path.exists(pyzbar_dir):
            # Add pyzbar directory to DLL search path
            os.add_dll_directory(pyzbar_dir)
            print(f"✓ Pyzbar DLL configured: {pyzbar_dir}")

# Run setup when imported
if __name__ != '__main__':
    setup_tesseract()
    setup_fonts()
    setup_pyzbar()
