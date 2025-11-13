# Ethiopian ID Card Generator

Generate Ethiopian ID cards from PDF documents with automatic data extraction and QR code generation.

## Features

- 📄 Extract data from Ethiopian ID PDFs
- 🖼️ Generate front and back ID cards
- 🔍 QR code generation and decoding
- 📊 Tkinter GUI with table view
- 🌐 Web interface for file upload
- 📥 Batch PDF download
- ✅ Real-time toast notifications

## Requirements

- Python 3.8+
- Tkinter (for GUI)
- Required fonts: Noto Sans, Noto Sans Ethiopic

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd fyida_id
```

2. **Install system dependencies**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-tk tesseract-ocr

# macOS
brew install python-tk tesseract
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Install fonts** (if not already installed)
```bash
# Ubuntu/Debian
sudo apt-get install fonts-noto fonts-noto-extra

# macOS
brew tap homebrew/cask-fonts
brew install font-noto-sans font-noto-sans-ethiopic
```

## Usage

### Start the Application

```bash
python web_server.py
```

This will:
- Start Flask web server on `http://localhost:5000`
- Open Tkinter GUI window

### Upload PDFs

1. Open browser: `http://localhost:5000`
2. Click "Choose Files" and select PDF(s)
3. Click "Upload & Process All"

### View Generated IDs

- Generated IDs appear in the Tkinter GUI table
- Check boxes to select IDs for download
- Click "Download Selected (PDF)" to save

### Preview

- Select items in the table to preview
- Preview shows back and front side by side
- Scrollable for multiple selections

## Project Structure

```
fyida_id/
├── web_server.py          # Flask server + Tkinter GUI
├── generate_id.py         # ID generation logic
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── data/                 # Template images
├── uploads/              # Uploaded PDFs (auto-created)
└── output/               # Generated IDs (auto-created)
```

## Configuration

### Save Path
- Default: `output/`
- Change in GUI: Enter path and click "Create Folder"

### Templates
- Front template: `data/photo_2025-11-11_21-48-06.jpg`
- Back template: `data/photo_2025-11-11_21-47-57.jpg`

## Features in Detail

### Toast Notifications
- 📤 Upload confirmation
- ⏳ Generation in progress (persistent)
- ✅ Completion notification
- ❌ Error alerts

### Table View
- ☑ Checkbox selection
- Name, Time, Status columns
- Select All / Deselect All buttons
- Scrollable list

### Preview
- Auto-scales to window size
- Shows selected items stacked
- Back card first, then front
- Responsive to window resize

## Building Standalone Executable

You can create a standalone executable that doesn't require Python installation.

### For Ubuntu/Linux

1. **Install PyInstaller**
```bash
pip install pyinstaller
```

2. **Build the app**
```bash
chmod +x build.sh
./build.sh
```

3. **Run the executable**
```bash
cd dist/EthiopianIDGenerator
./EthiopianIDGenerator
```

4. **Create distributable package**
```bash
tar -czf EthiopianIDGenerator-linux.tar.gz -C dist EthiopianIDGenerator
```

### For Windows

1. **Install PyInstaller**
```cmd
pip install pyinstaller
```

2. **Build the app**
```cmd
build.bat
```

3. **Run the executable**
```cmd
cd dist\EthiopianIDGenerator
EthiopianIDGenerator.exe
```

4. **Create installer (optional)**
- Use Inno Setup or NSIS to create an installer
- Or zip the `dist/EthiopianIDGenerator` folder

### Notes
- First build may take 5-10 minutes
- Executable size: ~300-400 MB (includes Python, dependencies, Tesseract, and fonts)
- ✅ Tesseract OCR is bundled - no separate installation needed
- ✅ Noto fonts are bundled - no separate installation needed
- Fully portable - just copy the folder and run!

## Troubleshooting

### Tkinter not found
```bash
sudo apt-get install python3-tk
```

### Font errors
```bash
sudo apt-get install fonts-noto fonts-noto-extra
```

### Permission errors
```bash
chmod +x web_server.py
```

### PyInstaller build errors
```bash
# If missing modules
pip install --upgrade pyinstaller
pip install -r requirements.txt

# If Tesseract not found during build
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-amh

# If font errors during build
sudo apt-get install fonts-noto fonts-noto-extra
```

## License

MIT License

## Author

Ethiopian ID Card Generator Team
