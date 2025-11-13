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
        tesseract_path = os.path.join(bundle_dir, 'tesseract', 'tesseract')
        tessdata_path = os.path.join(bundle_dir, 'tessdata')
        
        # Set Tesseract paths
        if os.path.exists(tesseract_path):
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            print(f"✓ Tesseract configured: {tesseract_path}")
        
        # Set tessdata path (must end with /)
        if os.path.exists(tessdata_path):
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
        font_dir = os.path.join(bundle_dir, 'fonts', 'noto')
        
        if os.path.exists(font_dir):
            # Add font directory to system path
            os.environ['FONTCONFIG_PATH'] = font_dir
            print(f"✓ Fonts configured: {font_dir}")
        else:
            print("⚠ Fonts not found in bundle, using system fonts")

# Run setup when imported
if __name__ != '__main__':
    setup_tesseract()
    setup_fonts()
