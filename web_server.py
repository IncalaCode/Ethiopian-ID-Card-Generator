#!/usr/bin/env python3
# Setup runtime paths for bundled executable
try:
    import setup_runtime
except ImportError:
    pass  # Not running as bundled app

from flask import Flask, request, jsonify
import os
import sys
import threading
import queue
import time
try:
    import tkinter as tk
    from tkinter import ttk
    from PIL import Image, ImageTk
    HAS_TK = True
except ImportError:
    HAS_TK = False
    print("Warning: tkinter not available. Install with: sudo apt-get install python3-tk")

from generate_id import extract_from_pdf, EthiopianIDGenerator

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global data storage
extracted_data = {}
ui_window = None
processing_queue = queue.Queue()
processing_lock = threading.Lock()
is_processing = False

def update_ui(data, front_path, back_path):
    """Update Tkinter UI with extracted data"""
    if ui_window:
        ui_window.update_data(data, front_path, back_path)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ethiopian ID Upload</title>
        <style>
            body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .upload-area { border: 2px dashed #4CAF50; padding: 40px; text-align: center; border-radius: 5px; margin: 20px 0; }
            input[type="file"] { display: none; }
            .upload-btn { background: #4CAF50; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            .upload-btn:hover { background: #45a049; }
            .upload-btn:disabled { background: #ccc; cursor: not-allowed; }
            #result { margin-top: 20px; padding: 15px; border-radius: 5px; display: none; }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .file-list { margin-top: 10px; text-align: left; }
            .file-item { padding: 5px; margin: 5px 0; background: #f0f0f0; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🇪🇹 Ethiopian ID Card Generator</h1>
            <div class="upload-area">
                <p>📄 Select PDF files (multiple allowed)</p>
                <input type="file" id="fileInput" accept=".pdf" multiple>
                <button class="upload-btn" onclick="document.getElementById('fileInput').click()">Choose Files</button>
                <div id="fileList" class="file-list"></div>
            </div>
            <button class="upload-btn" id="uploadBtn" onclick="uploadFiles()" style="width: 100%;">Upload & Process All</button>
            <div id="result"></div>
        </div>
        <script>
            let selectedFiles = [];
            document.getElementById('fileInput').addEventListener('change', function(e) {
                selectedFiles = Array.from(e.target.files);
                const fileList = document.getElementById('fileList');
                fileList.innerHTML = selectedFiles.map(f => `<div class="file-item">📄 ${f.name}</div>`).join('');
            });
            async function uploadFiles() {
                const result = document.getElementById('result');
                const uploadBtn = document.getElementById('uploadBtn');
                if (selectedFiles.length === 0) {
                    result.className = 'error';
                    result.textContent = 'Please select at least one file';
                    result.style.display = 'block';
                    return;
                }
                uploadBtn.disabled = true;
                result.style.display = 'block';
                result.className = '';
                result.textContent = `⏳ Uploading ${selectedFiles.length} file(s)...`;
                let success = 0, failed = 0;
                for (let i = 0; i < selectedFiles.length; i++) {
                    const formData = new FormData();
                    formData.append('file', selectedFiles[i]);
                    try {
                        result.textContent = `⏳ Uploading ${i+1}/${selectedFiles.length}: ${selectedFiles[i].name}`;
                        const response = await fetch('/upload', { method: 'POST', body: formData });
                        const data = await response.json();
                        if (data.success) success++;
                        else failed++;
                    } catch (error) {
                        failed++;
                    }
                }
                uploadBtn.disabled = false;
                result.className = failed === 0 ? 'success' : 'error';
                result.textContent = `✅ ${success} uploaded, ❌ ${failed} failed. Queue size: ${success}`;
            }
        </script>
    </body>
    </html>
    '''

def process_queue():
    global is_processing
    while True:
        try:
            filepath = processing_queue.get(timeout=1)
            with processing_lock:
                is_processing = True
            try:
                data = extract_from_pdf(filepath)
                name = data.get('name_en', 'Unknown')
                
                # Notify UI of generation start - persistent toast
                if ui_window:
                    ui_window.show_toast(f"⏳ Generating: {name}...", "info", persistent=True)
                
                gen = EthiopianIDGenerator()
                
                # Create unique filenames
                name_clean = name.replace(' ', '_')
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                front_path = f"front_{name_clean}_{timestamp}.png"
                back_path = f"back_{name_clean}_{timestamp}.png"
                
                gen.generate_front("data/photo_2025-11-11_21-48-06.jpg", "extracted_photo.jpg", data, front_path)
                qr_data = f"ID:{data['id_number']},Name:{data['name_en']},DOB:{data['dob']}"
                gen.generate_back("data/photo_2025-11-11_21-47-57.jpg", qr_data, data, back_path)
                update_ui(data, front_path, back_path)
            except Exception as e:
                import traceback
                print(f"Error processing {filepath}: {e}")
                traceback.print_exc()
                # Only show error toast for critical failures, not for normal processing issues
                if ui_window and "extract_from_pdf" in str(e):
                    ui_window.show_toast(f"❌ Failed to process PDF", "error", persistent=False)
            finally:
                with processing_lock:
                    is_processing = False
                processing_queue.task_done()
        except queue.Empty:
            continue

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    filepath = os.path.join(UPLOAD_FOLDER, f"{int(time.time())}_{file.filename}")
    file.save(filepath)
    processing_queue.put(filepath)
    
    # Notify UI of upload - brief notification
    if ui_window:
        ui_window.show_toast(f"📤 Uploaded: {file.filename}", "info", persistent=False)
    
    return jsonify({'success': True, 'message': 'File queued for processing', 'queue_size': processing_queue.qsize()})

class DataViewerUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Ethiopian ID Data Viewer")
        self.root.geometry("1400x900")
        self.history = {}
        self.checkboxes = {}
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for responsive layout
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Top: Save path
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(path_frame, text="Save Path:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.save_path = tk.StringVar(value="output")
        ttk.Entry(path_frame, textvariable=self.save_path, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(path_frame, text="Create Folder", command=self.create_folder).pack(side=tk.LEFT, padx=5)
        
        # Left: Table
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        ttk.Label(left_frame, text="Generated IDs", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Table with scrollbar
        table_container = ttk.Frame(left_frame)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(table_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.table = ttk.Treeview(table_container, columns=('Name', 'Time', 'Status'), show='tree headings', yscrollcommand=scrollbar.set, height=20)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.table.yview)
        
        self.table.heading('#0', text='☑')
        self.table.heading('Name', text='Name')
        self.table.heading('Time', text='Time')
        self.table.heading('Status', text='Status')
        
        self.table.column('#0', width=40, stretch=False)
        self.table.column('Name', width=250)
        self.table.column('Time', width=150)
        self.table.column('Status', width=80)
        
        self.table.bind('<ButtonRelease-1>', self.on_table_click)
        self.table.bind('<<TreeviewSelect>>', self.on_table_select)
        
        # Buttons below table
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Download Selected (PDF)", command=self.download_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Deselect All", command=self.deselect_all).pack(side=tk.LEFT, padx=5)
        
        # Right: Preview with scrollbar
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right_frame, text="Preview (Selected Items)", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Scrollable canvas for preview
        canvas = tk.Canvas(right_frame, bg='#f5f5f5', highlightthickness=0, bd=0)
        scrollbar_y = ttk.Scrollbar(right_frame, orient='vertical', command=canvas.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.configure(yscrollcommand=scrollbar_y.set)
        
        preview_container = tk.Frame(canvas, bg='#f5f5f5', bd=0, highlightthickness=0)
        canvas_window = canvas.create_window((0, 0), window=preview_container, anchor='nw')
        
        # Update scroll region and refresh preview on resize
        preview_container.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda e: self.on_canvas_resize())
        
        self.canvas = canvas
        self.preview_container = preview_container
        self.current_front = None
        self.current_back = None
        self.current_item = None
        self.toast_label = None
        self.last_canvas_width = 0
    
    def create_folder(self):
        path = self.save_path.get()
        os.makedirs(path, exist_ok=True)
        self.show_toast(f"✓ Folder created: {path}", "success")
    
    def show_toast(self, message, type="info", persistent=False):
        if self.toast_label:
            try:
                self.toast_label.destroy()
            except:
                pass
        
        bg_color = "#4CAF50" if type == "success" else "#2196F3" if type == "info" else "#f44336"
        self.toast_label = tk.Label(self.root, text=message, bg=bg_color, fg="white", 
                                     font=('Arial', 11, 'bold'), padx=20, pady=10)
        self.toast_label.place(relx=0.98, rely=0.02, anchor='ne')
        
        # Only auto-dismiss if not persistent
        if not persistent:
            self.root.after(3000, lambda: self.toast_label.destroy() if self.toast_label else None)
    
    def update_data(self, data, front_path, back_path):
        name = data.get('name_en', 'Unknown')
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        key = f"{name}_{int(time.time())}"
        
        # Move files to save path
        save_dir = self.save_path.get()
        os.makedirs(save_dir, exist_ok=True)
        
        new_front = os.path.join(save_dir, os.path.basename(front_path))
        new_back = os.path.join(save_dir, os.path.basename(back_path))
        
        if os.path.exists(front_path):
            os.rename(front_path, new_front)
        if os.path.exists(back_path):
            os.rename(back_path, new_back)
        
        self.history[key] = {
            'data': data.copy(),
            'front': new_front,
            'back': new_back,
            'name': name,
            'time': timestamp
        }
        
        # Add to table
        item_id = self.table.insert('', 'end', text='☐', values=(name, timestamp, '✓ Done'))
        self.checkboxes[item_id] = {'checked': False, 'key': key}
        
        self.table.selection_set(item_id)
        self.table.see(item_id)
        
        # Show success toast - replaces loading toast
        self.show_toast(f"✅ Completed: {name}", "success", persistent=False)
    
    def on_table_click(self, event):
        region = self.table.identify_region(event.x, event.y)
        if region == 'tree':
            item = self.table.identify_row(event.y)
            if item and item in self.checkboxes:
                self.checkboxes[item]['checked'] = not self.checkboxes[item]['checked']
                self.table.item(item, text='☑' if self.checkboxes[item]['checked'] else '☐')
                self.update_preview()
    
    def on_table_select(self, event):
        selection = self.table.selection()
        if selection:
            item = selection[0]
            if item in self.checkboxes:
                key = self.checkboxes[item]['key']
                self.current_item = item
                self.display_preview(key)
    
    def select_all(self):
        for item in self.checkboxes:
            self.checkboxes[item]['checked'] = True
            self.table.item(item, text='☑')
        self.update_preview()
    
    def deselect_all(self):
        for item in self.checkboxes:
            self.checkboxes[item]['checked'] = False
            self.table.item(item, text='☐')
        self.update_preview()
    
    def on_canvas_resize(self):
        # Only update if width actually changed
        current_width = self.canvas.winfo_width()
        if abs(current_width - self.last_canvas_width) > 10:
            self.last_canvas_width = current_width
            self.update_preview()
    
    def display_preview(self, key):
        self.update_preview()
    
    def update_preview(self):
        # Clear preview container
        for widget in self.preview_container.winfo_children():
            widget.destroy()
        
        # Get all selected items
        selected_keys = [self.checkboxes[item]['key'] for item in self.checkboxes if self.checkboxes[item]['checked']]
        
        if not selected_keys:
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
            return
        
        # Get canvas width for scaling - force update
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width() - 40
        if canvas_width < 100:
            canvas_width = 600
        
        row = 0
        for key in selected_keys:
            if key not in self.history:
                continue
            
            entry = self.history[key]
            self.current_front = entry['front']
            self.current_back = entry['back']
            
            # Load and combine images side by side (BACK FIRST, then FRONT)
            try:
                if os.path.exists(entry['front']) and os.path.exists(entry['back']):
                    front_img = Image.open(entry['front']).transpose(Image.FLIP_LEFT_RIGHT)
                    back_img = Image.open(entry['back']).transpose(Image.FLIP_LEFT_RIGHT)
                    
                    # Combine side by side - BACK first, then FRONT
                    combined_width = back_img.width + front_img.width + 20
                    combined = Image.new('RGB', (combined_width, back_img.height), 'white')
                    combined.paste(back_img, (0, 0))
                    combined.paste(front_img, (back_img.width + 20, 0))
                    
                    # Scale to fit canvas width
                    scale = canvas_width / combined_width
                    new_width = int(combined_width * scale)
                    new_height = int(combined.height * scale)
                    combined = combined.resize((new_width, new_height), Image.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(combined)
                    label = tk.Label(self.preview_container, image=photo, bg='#f5f5f5', bd=0, highlightthickness=0)
                    label.image = photo
                    label.grid(row=row, column=0, pady=10, padx=10)
                    row += 1
            except Exception as e:
                print(f"Error loading images: {e}")
        
        # Update scroll region
        self.preview_container.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def download_selected(self):
        selected_keys = [self.checkboxes[item]['key'] for item in self.checkboxes if self.checkboxes[item]['checked']]
        
        if not selected_keys:
            self.show_toast("No items selected", "error")
            return
        
        try:
            all_images = []
            for key in selected_keys:
                entry = self.history[key]
                front_img = Image.open(entry['front']).transpose(Image.FLIP_LEFT_RIGHT)
                back_img = Image.open(entry['back']).transpose(Image.FLIP_LEFT_RIGHT)
                
                # Combine BACK first, then FRONT
                combined_width = back_img.width + front_img.width + 20
                combined = Image.new('RGB', (combined_width, back_img.height), 'white')
                combined.paste(back_img, (0, 0))
                combined.paste(front_img, (back_img.width + 20, 0))
                all_images.append(combined)
            
            save_dir = self.save_path.get()
            output_path = os.path.join(save_dir, f"ID_Selected_{len(selected_keys)}_{time.strftime('%Y%m%d_%H%M%S')}.pdf")
            
            # Save as PDF
            all_images[0].save(output_path, save_all=True, append_images=all_images[1:], resolution=100.0)
            
            self.show_toast(f"✓ Downloaded {len(selected_keys)} IDs as PDF", "success")
        except Exception as e:
            self.show_toast(f"Error: {str(e)}", "error")
    
    def on_closing(self):
        for f in os.listdir('.'):
            if f.startswith('extracted_image_') or f == 'extracted_photo.jpg' or f.startswith('temp_'):
                try:
                    os.remove(f)
                except:
                    pass
        self.root.destroy()
    
    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    if not HAS_TK:
        print("\n" + "="*60)
        print("ERROR: tkinter not installed!")
        print("Please run: sudo apt-get install python3-tk")
        print("Then restart this script.")
        print("="*60)
        sys.exit(1)
    
    # Start processing queue thread
    queue_thread = threading.Thread(target=process_queue, daemon=True)
    queue_thread.start()
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("="*60)
    print("Server started on http://0.0.0.0:5000")
    print("Upload files to: http://0.0.0.0:5000/upload")
    print("="*60)
    
    # Start Tkinter UI
    ui_window = DataViewerUI()
    ui_window.run()
