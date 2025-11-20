#!/usr/bin/env python3
"""
Runtime setup script to configure EasyOCR models and fonts paths
This runs when the bundled app starts
"""
import os
import sys

def setup_easyocr():
    """Configure EasyOCR model path for bundled executable"""
    if getattr(sys, 'frozen', False):
        # Running as bundled executable
        bundle_dir = sys._MEIPASS
        
        # EasyOCR models bundled in .EasyOCR/model/
        easyocr_model_dir = os.path.join(bundle_dir, '.EasyOCR', 'model')
        
        if os.path.exists(easyocr_model_dir):
            # Set environment variable for EasyOCR to find models
            os.environ['EASYOCR_MODULE_PATH'] = bundle_dir
            print(f"✓ EasyOCR models configured: {easyocr_model_dir}")
            
            # List bundled models
            if os.path.isdir(easyocr_model_dir):
                model_files = [f for f in os.listdir(easyocr_model_dir)]
                print(f"  Bundled models: {len(model_files)} files")
        else:
            print("⚠ EasyOCR models not found in bundle")
            print("  Models will be downloaded on first run")

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
    setup_easyocr()
    setup_fonts()
    setup_pyzbar()
