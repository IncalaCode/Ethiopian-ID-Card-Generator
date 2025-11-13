#!/bin/bash
# Build script for Ethiopian ID Generator

echo "=================================="
echo "Ethiopian ID Generator - Build"
echo "=================================="

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null
then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build the application
echo "Building application..."
pyinstaller build_app.spec

# Check if build was successful
if [ -f "dist/EthiopianIDGenerator" ]; then
    echo ""
    echo "=================================="
    echo "Build successful!"
    echo "=================================="
    echo "Single executable created: dist/EthiopianIDGenerator"
    echo "File size: $(du -h dist/EthiopianIDGenerator | cut -f1)"
    echo ""
    echo "To run the app:"
    echo "  ./dist/EthiopianIDGenerator"
    echo ""
    echo "To distribute:"
    echo "  Just copy the single file: dist/EthiopianIDGenerator"
else
    echo ""
    echo "Build failed! Check errors above."
    exit 1
fi
