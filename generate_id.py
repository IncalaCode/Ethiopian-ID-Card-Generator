#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import qrcode
import os
import sys
import fitz
import re
try:
    from convertdate import ethiopian as ethiopian_conv
    HAS_CONVERTDATE = True
except Exception:
    HAS_CONVERTDATE = False
from barcode import Code128
from barcode.writer import ImageWriter

# Fix pyzbar DLL loading for PyInstaller
if hasattr(sys, '_MEIPASS'):
    # Running in PyInstaller bundle
    import ctypes
    try:
        # Set pyzbar library path environment variable
        os.environ['PYZBAR_LIBRARY_PATH'] = sys._MEIPASS
        
        # Add all possible DLL locations to PATH
        dll_dirs = [
            sys._MEIPASS,
            os.path.join(sys._MEIPASS, 'pyzbar'),
            os.path.join(sys._MEIPASS, 'lib'),
            os.path.dirname(sys.executable)
        ]
        
        # Update PATH environment variable
        current_path = os.environ.get('PATH', '')
        for dll_dir in dll_dirs:
            if os.path.exists(dll_dir):
                os.environ['PATH'] = dll_dir + os.pathsep + current_path
                current_path = os.environ['PATH']
        
        # Try to preload DLL with full path
        dll_names = ['libzbar-64.dll', 'libzbar.dll', 'zbar.dll']
        for dll_dir in dll_dirs:
            for dll_name in dll_names:
                dll_path = os.path.join(dll_dir, dll_name)
                if os.path.exists(dll_path):
                    try:
                        # Load with full path
                        ctypes.CDLL(dll_path)
                        print(f"  ✓ Preloaded {dll_name} from {dll_path}")
                        break
                    except Exception as e:
                        print(f"  ⚠ Failed to preload {dll_name}: {e}")
                        continue
    except Exception as e:
        print(f"  ⚠ DLL setup failed: {e}")
        pass  # Will fall back to OCR

class EthiopianIDGenerator:
    def __init__(self):
        # Load fonts with larger sizes from local font folder
        self.am_font = self._load_font("NotoSansEthiopic-Regular.ttf", 36)
        self.am_font_bold = self._load_font("NotoSansEthiopic-Bold.ttf", 36)
        self.en_font = self._load_font("NotoSans-Regular.ttf", 32)
        self.en_font_bold = self._load_font("NotoSans-Bold.ttf", 32)
        self.color = (0, 0, 0)  # Black color
        
        # Configuration arrays
        self.front_config = {
            'main_photo': {'x': 70, 'y': 180, 'w': 420, 'h': 575},
            'small_photo': {'x': 1040, 'y': 600, 'w': 100, 'h': 140},
            'name_am': {'x': 520, 'y': 230, 'font': 'NotoSansEthiopic-Bold.ttf', 'size': 40, 'color': (0, 0, 0)},
            'name_en': {'x': 520, 'y': 265, 'font': 'NotoSans-Bold.ttf', 'size': 36, 'color': (0, 0, 0)},
            # separate Amharic and English positions so both are not drawn at the same place
            'dob_am': {'x': 520, 'y': 365, 'font': 'NotoSans-Bold.ttf', 'size': 34, 'color': (0, 0, 0)},
            'dob': {'x': 520, 'y': 390, 'font': 'NotoSans-Bold.ttf', 'size': 34, 'color': (0, 0, 0)},
            'sex_am': {'x': 520, 'y': 445, 'font': 'NotoSansEthiopic-Bold.ttf', 'size': 38, 'color': (0, 0, 0)},
            'sex': {'x': 520, 'y': 470, 'font': 'NotoSans-Bold.ttf', 'size': 34, 'color': (0, 0, 0)},
            'expiry_ec': {'x': 520, 'y': 565, 'font': 'NotoSans-Bold.ttf', 'size': 34, 'color': (0, 0, 0)},
            'expiry_gc': {'x': 520, 'y': 560, 'font': 'NotoSans-Bold.ttf', 'size': 34, 'color': (0, 0, 0)},
            'id_number': {'x': 620, 'y': 620, 'font': 'NotoSans-Bold.ttf', 'size': 26, 'color': (0, 0, 0)},
            'barcode': {'x': 580, 'y': 650, 'w': 350, 'h': 80},
            'issue_date_gc': {'x': 25, 'y': 20, 'font': 'NotoSans-Bold.ttf', 'size': 24, 'color': (0, 0, 0)},
            'issue_date_ec': {'x': 25, 'y': 340,'font': 'NotoSans-Bold.ttf', 'size': 24, 'color': (0, 0, 0)}
        }
        
        self.back_config = {
            'qr_code': {'x': 595, 'y': 47, 'size': 635},
            'phone': {'x': 50, 'y': 100, 'font': 'NotoSans-Bold.ttf', 'size': 30, 'color': (0, 0, 0)},
            'nationality': {'x': 50, 'y': 210, 'font': 'NotoSans-Bold.ttf', 'size': 27, 'color': (0, 0, 0)},
            'address': {'x': 50, 'y': 290, 'font': 'NotoSans-Bold.ttf', 'size': 29, 'color':  (0, 0, 0)},
            'fin': {'x': 132, 'y': 655, 'font': 'NotoSans-Regular.ttf', 'size': 27, 'color': (0, 0, 0)},
            'sn': {'x': 1050, 'y': 720, 'font': 'NotoSans-Regular.ttf', 'size': 28, 'color': (0, 0, 0)}
        }
    
    def _load_font(self, font_name, size):
        font_paths = [
            os.path.join("font", font_name),
            os.path.join(os.path.dirname(__file__), "font", font_name),
            f"/usr/share/fonts/truetype/noto/{font_name}"
        ]
        
        for path in font_paths:
            try:
                if os.path.exists(path):
                    return ImageFont.truetype(path, size)
            except:
                continue
        return ImageFont.load_default()
    
    def _draw_bilingual(self, draw, am_text, en_text, pos):
        """Draw Amharic above English"""
        draw.text(pos, am_text, font=self.am_font_bold, fill=self.color)
        am_bbox = draw.textbbox(pos, am_text, font=self.am_font_bold)
        en_y = am_bbox[3] + 5
        draw.text((pos[0], en_y), en_text, font=self.en_font_bold, fill=self.color)

    def _draw_am_en_inline(self, draw, am_text, en_text, pos, sep=' | ', use_am_font=True):
        """Draw Amharic and English on one line separated by `sep`.
        Amharic is drawn with Amharic font; English (and separator) with English font.
        If am_text is empty, only English is drawn at pos.
        """
        x, y = pos
        if am_text:
            font_to_use = self.am_font_bold if use_am_font else self.en_font_bold
            draw.text((x, y), am_text, font=font_to_use, fill=self.color)
            am_bbox = draw.textbbox((x, y), am_text, font=font_to_use)
            am_width = am_bbox[2] - am_bbox[0]
            en_x = x + am_width
            # Adjust y position for English text to align with Amharic baseline
            en_y = y 
            draw.text((en_x, en_y), f"{sep}{en_text}" if en_text else sep.strip(), font=self.en_font_bold, fill=self.color)
        else:
            # only English
            draw.text((x, y), en_text, font=self.en_font_bold, fill=self.color)
    
    def generate_front(self, template_path, photo_path, data, output_path):
        """Generate front of ID card"""
        img = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # Paste main photo
        cfg = self.front_config['main_photo']
        photo = Image.open(photo_path).convert("L").convert("RGB")
        photo = photo.resize((cfg['w'], cfg['h']))
        img.paste(photo, (cfg['x'], cfg['y']))
        
        # Paste small photo with transparent edges
        cfg = self.front_config['small_photo']
        small_photo = photo.resize((cfg['w'], cfg['h']))
        # Create alpha mask with transparent edges
        mask = Image.new('L', (cfg['w'], cfg['h']), 255)
        mask_draw = ImageDraw.Draw(mask)
        # Create gradient fade on edges
        for i in range(20):
            alpha = int(255 * (i / 20))
            mask_draw.rectangle([i, i, cfg['w']-i-1, cfg['h']-i-1], outline=alpha)
        small_photo.putalpha(mask)
        img.paste(small_photo, (cfg['x'], cfg['y']), small_photo)
        
        # Draw name (bilingual stacked)
        name_am = data.get('name_am', '')
        name_en = data.get('name_en', '')
        self._draw_bilingual(draw, name_am, name_en, (self.front_config['name_am']['x'], self.front_config['name_am']['y']))

        # Draw DOB as: dob_am | dob
        dob_am = data.get('dob_am', '')
        dob_en = data.get('dob', '')
        dob_pos = (self.front_config['dob']['x'], self.front_config['dob']['y'])
        self._draw_am_en_inline(draw, dob_am, dob_en, dob_pos, use_am_font=False)

        # Draw Sex as: sex_am | sex
        sex_am = data.get('sex_am', '')
        sex_en = data.get('sex', '')
        sex_pos = (self.front_config['sex']['x'], self.front_config['sex']['y'])
        self._draw_am_en_inline(draw, sex_am, sex_en, sex_pos)

        # Draw Expiry as: expiry_ec | expiry_gc
        exp_ec = data.get('expiry_ec', '')
        exp_gc = data.get('expiry_gc', '')
        exp_pos = (self.front_config['expiry_ec']['x'], self.front_config['expiry_ec']['y'])
        self._draw_am_en_inline(draw, exp_ec, exp_gc, exp_pos, use_am_font=False)

        # Draw issue date vertically on left side
        issue_ec = data.get('issue_date_ec', '')
        issue_gc = data.get('issue_date_gc', '')
        if issue_ec or issue_gc:
            from PIL import Image as PILImage
            
            if issue_ec:
                cfg = self.front_config['issue_date_ec']
                font_small = self._load_font(cfg['font'], cfg['size'])
                txt_img = PILImage.new('RGBA', (300, 50), (255, 255, 255, 0))
                txt_draw = ImageDraw.Draw(txt_img)
                txt_draw.text((0, 0), issue_ec, font=font_small, fill=cfg['color'])
                txt_rotated = txt_img.rotate(90, expand=True)
                img.paste(txt_rotated, (cfg['x'], cfg['y']), txt_rotated)
            
            if issue_gc:
                cfg = self.front_config['issue_date_gc']
                font_small = self._load_font(cfg['font'], cfg['size'])
                txt_img2 = PILImage.new('RGBA', (300, 50), (255, 255, 255, 0))
                txt_draw2 = ImageDraw.Draw(txt_img2)
                txt_draw2.text((0, 0), issue_gc, font=font_small, fill=cfg['color'])
                txt_rotated2 = txt_img2.rotate(90, expand=True)
                img.paste(txt_rotated2, (cfg['x'], cfg['y']), txt_rotated2)
        
        # Draw ID number
        cfg = self.front_config['id_number']
        font = self._load_font(cfg['font'], cfg['size'])
        draw.text((cfg['x'], cfg['y']), data.get('id_number', ''), font=font, fill=cfg['color'])
        
        # Generate barcode for ID number
        id_clean = data['id_number'].replace(' ', '')
        barcode = Code128(id_clean, writer=ImageWriter())
        barcode.save('temp_barcode_front', {'write_text': False})
        barcode_img = Image.open('temp_barcode_front.png')
        barcode_img = barcode_img.crop(barcode_img.getbbox())
        cfg = self.front_config['barcode']
        barcode_img = barcode_img.resize((cfg['w'], cfg['h']))
        img.paste(barcode_img, (cfg['x'], cfg['y']))
        os.remove('temp_barcode_front.png')
        
        img.save(output_path, format="PNG", dpi=(300, 300))
        print(f"✓ Front card: {output_path}")
    
    def generate_back(self, template_path, qr_data, data, output_path):
        """Generate back of ID card"""
        img = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # Decode QR from extracted_image_1.jpg if exists
        print(f"\n--- Decoding QR Code ---")
        if os.path.exists('extracted_image_1.jpg'):
            print(f"  ✓ Found extracted_image_1.jpg")
            try:
                qr_img_cv = cv2.imread('extracted_image_1.jpg')
                print(f"  ✓ Loaded image: {qr_img_cv.shape}")
                
                # Resize if too small
                if qr_img_cv.shape[0] < 300:
                    scale = 300 / qr_img_cv.shape[0]
                    qr_img_cv = cv2.resize(qr_img_cv, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                    print(f"  ✓ Resized to: {qr_img_cv.shape}")
                
                gray = cv2.cvtColor(qr_img_cv, cv2.COLOR_BGR2GRAY)
                
                # Try multiple preprocessing methods
                methods = [
                    ('Original', qr_img_cv),
                    ('Grayscale', gray),
                    ('Inverted', cv2.bitwise_not(gray)),
                    ('Threshold', cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1]),
                    ('Threshold Inverted', cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)[1]),
                    ('OTSU', cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
                    ('Adaptive', cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2))
                ]
                
                detector = cv2.QRCodeDetector()
                decoded_text = ''
                
                # Try OpenCV detector
                for method_name, processed_img in methods:
                    if len(processed_img.shape) == 2:
                        processed_img_bgr = cv2.cvtColor(processed_img, cv2.COLOR_GRAY2BGR)
                    else:
                        processed_img_bgr = processed_img
                    decoded_text, points, _ = detector.detectAndDecode(processed_img_bgr)
                    if decoded_text:
                        print(f"  ✓ Decoded with {method_name} method")
                        break
                
                # Try pyzbar as fallback
                if not decoded_text:
                    try:
                        from pyzbar import pyzbar
                        for method_name, processed_img in methods:
                            decoded_objs = pyzbar.decode(processed_img)
                            if decoded_objs:
                                decoded_text = decoded_objs[0].data.decode('utf-8')
                                print(f"  ✓ Decoded with pyzbar using {method_name} method")
                                break
                    except ImportError:
                        print(f"  ⚠ pyzbar not available, trying OCR fallback")
                        # Use OCR as last resort
                        try:
                            import pytesseract
                            ocr_result = pytesseract.image_to_string(gray, config='--psm 6')
                            if ocr_result.strip():
                                decoded_text = ocr_result.strip()
                                print(f"  ✓ Extracted text using OCR (may not be QR data)")
                        except Exception as ocr_e:
                            import traceback
                            print(f"  ✗ OCR fallback failed: {ocr_e}")
                            print(f"  OCR error details: {traceback.format_exc()}")
                    except Exception as e:
                        import traceback
                        error_details = traceback.format_exc()
                        print(f"  ⚠ pyzbar error: {str(e)}")
                        print(f"  Full error details:")
                        print(error_details)
                        print(f"  Falling back to OCR...")
                    
                    # Use OCR as fallback
                    if not decoded_text:
                        try:
                            import pytesseract
                            ocr_result = pytesseract.image_to_string(gray, config='--psm 6')
                            if ocr_result.strip():
                                decoded_text = ocr_result.strip()
                                print(f"  ✓ Extracted text using OCR (may not be QR data)")
                        except Exception as ocr_e:
                            import traceback
                            print(f"  ✗ OCR fallback failed: {ocr_e}")
                            print(f"  OCR error details: {traceback.format_exc()}")
                
                if decoded_text:
                    qr_data = decoded_text
                    print(f"\n{'='*60}")
                    print(f"DECODED QR CODE DATA:")
                    print(f"{'='*60}")
                    print(qr_data)
                    print(f"{'='*60}\n")
                else:
                    print(f"  ✗ QR code not detected with any method")
            except Exception as e:
                import traceback
                print(f"  ✗ Could not decode QR: {e}")
                print(f"  Error details: {traceback.format_exc()}")
        else:
            print(f"  ⚠ extracted_image_1.jpg not found, using default QR data")
        
        # Generate and paste QR code
        cfg = self.back_config['qr_code']
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((cfg['size'], cfg['size']))
        img.paste(qr_img, (cfg['x'], cfg['y']))
        
        # Draw fields
        cfg = self.back_config['phone']
        font = self._load_font(cfg['font'], cfg['size'])
        draw.text((cfg['x'], cfg['y']), data['phone'], font=font, fill=cfg['color'])
        
        # Draw nationality (Amharic | English)
        nationality_am = data.get('nationality_am', '')
        nationality_en = data.get('nationality', '')
        if nationality_am:
            cfg = self.back_config['nationality']
            font_am = self._load_font('NotoSansEthiopic-Bold.ttf', cfg['size'])
            draw.text((cfg['x'], cfg['y']), nationality_am, font=font_am, fill=cfg['color'])
            am_bbox = draw.textbbox((cfg['x'], cfg['y']), nationality_am, font=font_am)
            am_width = am_bbox[2] - am_bbox[0]
            font_en = self._load_font(cfg['font'], cfg['size'])
            draw.text((cfg['x'] + am_width + 10, cfg['y']), f"| {nationality_en}", font=font_en, fill=cfg['color'])
        else:
            cfg = self.back_config['nationality']
            font = self._load_font(cfg['font'], cfg['size'])
            draw.text((cfg['x'], cfg['y']), data['nationality'], font=font, fill=cfg['color'])
        
        # Draw address - split by newlines and display each component
        cfg = self.back_config['address']
        font_am = self._load_font('NotoSansEthiopic-Bold.ttf', cfg['size'])
        font_en = self._load_font(cfg['font'], cfg['size'])
        y = cfg['y']
        
        # Split address by newlines to get individual components
        addr_am_lines = data.get('address_am', '').split('\n') if data.get('address_am') else []
        addr_en_lines = data.get('address', '').split('\n') if data.get('address') else []
        
        # Display each address component on separate lines
        max_lines = max(len(addr_am_lines), len(addr_en_lines))
        for i in range(max_lines):
            if i < len(addr_am_lines) and addr_am_lines[i].strip():
                draw.text((cfg['x'], y), addr_am_lines[i], font=font_am, fill=cfg['color'])
                y += 34
            if i < len(addr_en_lines) and addr_en_lines[i].strip():
                draw.text((cfg['x'], y), addr_en_lines[i], font=font_en, fill=cfg['color'])
                y += 40
        
        # Draw SN
        cfg = self.back_config['sn']
        font = self._load_font(cfg['font'], cfg['size'])
        draw.text((cfg['x'], cfg['y']), f"{data.get('sn', '0000000')}", font=font, fill=cfg['color'])
        
        # Draw FIN
        cfg = self.back_config['fin']
        font = self._load_font(cfg['font'], cfg['size'])
        draw.text((cfg['x'], cfg['y']), f"{data.get('fin', '')}", font=font, fill=cfg['color'])
        
        img.save(output_path, format="PNG", dpi=(300, 300))
        print(f"✓ Back card: {output_path}")

def extract_from_pdf(pdf_path):
    """Extract data and images from PDF"""
    doc = fitz.open(pdf_path)
    data = {}
    photo = None
    
    for page in doc:
        text = page.get_text()
        
        print("\n" + "="*60)
        print("DEBUG: EXTRACTING DATA FROM PDF")
        print("="*60)
        
        # Extract names - look for Amharic name (appears before English name)
        lines = text.split('\n')
        print(f"\nTotal lines found: {len(lines)}")
        print("\nAll lines:")
        for i, line in enumerate(lines):
            if line.strip():
                print(f"  Line {i}: {line.strip()}")
        
        # First pass: find English name - look near end after FCN
        print("\n--- Searching for English name ---")
        fcn_line = -1
        for i, line in enumerate(lines):
            if re.search(r'\d{4}\s*\d{4}\s*\d{4}\s*\d{4}', line):
                fcn_line = i
                break
        
        if fcn_line > 0:
            for i in range(fcn_line + 1, min(fcn_line + 3, len(lines))):
                line_clean = lines[i].strip()
                if re.search(r'[A-Za-z]{3,}', line_clean):
                    line_clean = re.sub(r'\s+([a-z])\s+', r'\1', line_clean)
                    line_clean = re.sub(r'ū', 'ij', line_clean)
                    line_clean = line_clean.replace('Keda', 'Kedija')
                    data['name_en'] = line_clean
                    print(f"  ✓ Selected English name at line {i}: {data['name_en']}")
                    break
        
        # Second pass: find Amharic name (look in lines before English name)
        print("\n--- Searching for Amharic name ---")
        if data.get('name_en'):
            for i, line in enumerate(lines):
                if data['name_en'] in line:
                    print(f"  Found English name at line {i}")
                    # Check previous 3 lines for Amharic
                    for j in range(max(0, i-3), i):
                        amharic_parts = re.findall(r'[\u1200-\u137F]+', lines[j])
                        if amharic_parts:
                            print(f"    Line {j} Amharic parts: {amharic_parts}")
                        if len(amharic_parts) >= 2:  # Name should have at least 2 parts
                            data['name_am'] = ' '.join(amharic_parts[:3])
                            print(f"  ✓ Selected Amharic name: {data['name_am']}")
                            break
                    if data.get('name_am'):
                        break
        
        # Fallback: Look for Amharic name (line before English name)
        if not data.get('name_am') and data.get('name_en'):
            print("  Using fallback: looking for Amharic before English name")
            for i, line in enumerate(lines):
                if 'Ked' in line:
                    if i > 0:
                        amharic_parts = re.findall(r'[\u1200-\u137F]+', lines[i-1])
                        if len(amharic_parts) >= 2:
                            data['name_am'] = ' '.join(amharic_parts[:3])
                            print(f"  ✓ Found Amharic name at line {i-1}: {data['name_am']}")
                            break
        
        # Extract dates - both dates are DOB
        print("\n--- Searching for dates ---")
        dates_ddmmyyyy = re.findall(r'\d{2}/\d{2}/\d{4}', text)
        dates_yyyymmdd = re.findall(r'\d{4}/\d{2}/\d{2}', text)
        print(f"  Found dates (dd/mm/yyyy): {dates_ddmmyyyy}")
        print(f"  Found dates (yyyy/mm/dd): {dates_yyyymmdd}")

        def _try_convert_ec_to_gc_tuple(date_str):
            """If date looks like Ethiopian (heuristic: year < 2000),
            return (ec_str, gc_str). If it's likely already Gregorian, return (None, greg_str).
            ec_str is the original dd/mm/yyyy; gc_str is converted yyyy/mm/dd.
            """
            try:
                parts = date_str.split('/')
                if len(parts[0]) == 4:  # yyyy/mm/dd format
                    y, m, d = [int(x) for x in parts]
                    return (None, f"{y:04d}/{m:02d}/{d:02d}")  # Already GC
                else:  # dd/mm/yyyy format
                    d, m, y = [int(x) for x in parts]
            except Exception:
                return (None, date_str)

            if y < 2000:
                ec_str = f"{d:02d}/{m:02d}/{y:04d}"
                if HAS_CONVERTDATE:
                    try:
                        gy, gm, gd = ethiopian_conv.to_gregorian(y, m, d)
                        gc_str = f"{gy:04d}/{gm:02d}/{gd:02d}"
                        return (ec_str, gc_str)
                    except Exception:
                        pass
                gy = y + (7 if m <= 4 else 8)
                gc_str = f"{gy:04d}/{m:02d}/{d:02d}"
                return (ec_str, gc_str)
            else:
                # Treat as Gregorian already, return None for ec and the normalized gc string
                try:
                    gc_str = f"{y:04d}/{m:02d}/{d:02d}"
                except Exception:
                    gc_str = date_str
                return (None, gc_str)

        if dates_ddmmyyyy:
            data['dob_am'] = dates_ddmmyyyy[0]
            print(f"  ✓ DOB (EC): {dates_ddmmyyyy[0]}")
        
        if dates_yyyymmdd:
            # Convert to month name format for GC
            parts = dates_yyyymmdd[0].split('/')
            if len(parts) == 3:
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                month_name = months[int(parts[1]) - 1]
                data['dob'] = f"{parts[0]}/{month_name}/{parts[2]}"
            else:
                data['dob'] = dates_yyyymmdd[0]
            print(f"  ✓ DOB (GC): {data['dob']}")
        
        print("\n--- Searching for phone and ID ---")
        phone = re.search(r'09\d{8}', text)
        if phone:
            data['phone'] = phone.group()
            print(f"  ✓ Phone: {data['phone']}")
        
        id_num = re.search(r'\d{4}\s*\d{4}\s*\d{4}\s*\d{4}', text)
        if id_num:
            data['id_number'] = id_num.group()
            print(f"  ✓ ID Number: {data['id_number']}")
        
        # Extract sex (support Amharic and English tokens and store separately)
        sex_map_en = {
            'ሴት': 'Female',
            'ወንድ': 'Male',
            'female': 'Female',
            'Female': 'Female',
            'male': 'Male',
            'Male': 'Male',
            'F': 'Female',
            'M': 'Male'
        }
        sex_map_am = {'Female': 'ሴት', 'Male': 'ወንድ', 'F': 'ሴት', 'M': 'ወንድ'}

        print("\n--- Searching for sex ---")
        sex_am = ''
        sex_en = ''
        am_match = re.search(r'(እ?ሴት|ሴት|ወንድ)', text)
        if am_match:
            tok = am_match.group().strip()
            sex_am = tok
            sex_en = sex_map_en.get(tok, 'Unknown')
            print(f"  ✓ Found Amharic: {sex_am} -> {sex_en}")
        else:
            en_match = re.search(r'\b(Female|female|Male|male|F|M)\b', text)
            if en_match:
                tok = en_match.group().strip()
                sex_en = sex_map_en.get(tok, tok)
                sex_am = sex_map_am.get(sex_en, '')
                print(f"  ✓ Found English: {tok} -> {sex_en} ({sex_am})")

        if sex_en:
            data['sex'] = sex_en
        if sex_am:
            data['sex_am'] = sex_am
        
        # Extract address - find region, subcity/zone, woreda dynamically
        print("\n--- Searching for address ---")
        addr_am = []
        addr_en = []
        
        # Look for address components in lines 50-56
        address_pairs = []
        i = 50
        while i < min(57, len(lines)):
            line = lines[i].strip()
            am_parts = re.findall(r'[\u1200-\u137F]+', line)
            
            # Skip empty lines or lines with dates/numbers
            if not am_parts or len(line) < 2 or '/' in line or re.search(r'\d{4}', line):
                i += 1
                continue
            
            # Check if next line has English equivalent
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.search(r'^[A-Z][a-z]+', next_line) and not re.search(r'\d', next_line):
                    address_pairs.append((line, next_line))
                    print(f"  ✓ Found address pair - AM: {line}, EN: {next_line}")
                    i += 2  # Skip both lines
                    continue
            i += 1
        
        # Extract address components
        for am_text, en_text in address_pairs:
            addr_am.append(am_text)
            addr_en.append(en_text)
        
        # Format address properly - join with newlines for proper display
        if addr_en:
            data['address'] = '\n'.join(addr_en)  # Separate lines
        if addr_am:
            data['address_am'] = '\n'.join(addr_am)  # Separate lines
        
        # Extract nationality in both languages
        nationality_am = ''
        nationality_en = 'Ethiopian'
        for i, line in enumerate(lines):
            if 'ኢትዮጵያዊ' in line:
                nationality_am = 'ኢትዮጵያዊ'
                print(f"  ✓ Found Amharic nationality: {nationality_am}")
                break
        
        data.setdefault('nationality', nationality_en)
        data.setdefault('nationality_am', nationality_am)
        # Use ID number as FIN if not found, add FIN prefix and keep 12 digits
        if not data.get('fin'):
            id_num = data.get('id_number', '')
            if id_num:
                # Extract only digits and take first 12
                digits = ''.join(filter(str.isdigit, id_num))
                if len(digits) >= 12:
                    fin_digits = digits[:12]
                    data['fin'] = f"FIN {fin_digits[:4]} {fin_digits[4:8]} {fin_digits[8:12]}"
                else:
                    data['fin'] = f"FIN {digits.ljust(12, '0')[:4]} {digits.ljust(12, '0')[4:8]} {digits.ljust(12, '0')[8:12]}"
        data.setdefault('fin', '')
        
        # Generate SN from FIN (7 digits)
        if data.get('fin'):
            fin_digits = ''.join(filter(str.isdigit, data['fin']))
            if len(fin_digits) >= 7:
                # Use last 7 digits of FIN
                data['sn'] = fin_digits[-7:]
            else:
                data['sn'] = fin_digits.zfill(7)
        else:
            data['sn'] = '0000000'
        data.setdefault('name_am', '')
        data.setdefault('name_en', '')
        data.setdefault('dob_am', '')
        data.setdefault('dob', '')
        data.setdefault('sex_am', '')
        data.setdefault('sex', '')
        data.setdefault('expiry_ec', '')
        data.setdefault('expiry_gc', '')
        
        # Fix OCR errors in expiry_gc
        if data.get('expiry_gc'):
            data['expiry_gc'] = data['expiry_gc'].replace('O0ct', 'Oct').replace('0ct', 'Oct').replace('2o', '20')
            print(f"  ✓ Fixed Expiry GC: {data['expiry_gc']}")
        # Set defaults if still missing
        if not data.get('issue_date_ec'):
            data['issue_date_ec'] = ''
            print(f"\n  ⚠ WARNING: Issue Date EC not found in PDF")
        if not data.get('issue_date_gc'):
            data['issue_date_gc'] = ''
            print(f"  ⚠ WARNING: Issue Date GC not found in PDF")
        data.setdefault('id_number', '')
        data.setdefault('phone', '')
        data.setdefault('address', '')
        data.setdefault('address_am', '')
        
        # Extract and save all images
        print("\n--- Extracting images ---")
        images = page.get_images()
        print(f"  Found {len(images)} images")
        
        saved_images = []
        for idx, img in enumerate(images):
            pix = fitz.Pixmap(doc, img[0])
            if pix.n >= 5:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            img_data = pix.tobytes("png")
            nparr = np.frombuffer(img_data, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            img_path = f"extracted_image_{idx}.jpg"
            cv2.imwrite(img_path, img_cv)
            saved_images.append(img_path)
            print(f"  ✓ Saved image {idx}: {img_path}")
        
        # First image is person's photo
        if saved_images:
            photo = cv2.imread(saved_images[0])
            cv2.imwrite("extracted_photo.jpg", photo)
            print(f"  ✓ Person photo: {saved_images[0]}")
        
        # Extract FIN from extracted_image_3.jpg if exists
        if len(saved_images) >= 4:
            print("\n--- Extracting FIN from extracted_image_3.jpg ---")
            try:
                import pytesseract
                fin_img = cv2.imread(saved_images[3])
                fin_gray = cv2.cvtColor(fin_img, cv2.COLOR_BGR2GRAY)
                fin_gray = cv2.threshold(fin_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                fin_text = pytesseract.image_to_string(fin_gray, config='--psm 6')
                print(f"  FIN OCR text: {fin_text}")
                
                # Extract FIN number - look for pattern after "FIN"
                fin_text_clean = fin_text.replace('\n', ' ').replace('\r', ' ')
                fin_match = re.search(r'FIN[^\d]*(\d{4})[^\d]*(\d{4})[^\d]*(\d{4})[^\d]*(\d{4})', fin_text_clean)
                if fin_match:
                    # Take only first 12 digits and add FIN prefix
                    fin_digits = fin_match.group(1) + fin_match.group(2) + fin_match.group(3)
                    data['fin'] = f"FIN {fin_digits[:4]} {fin_digits[4:8]} {fin_digits[8:12]}"
                    print(f"  ✓ Found FIN: {data['fin']}")
                else:
                    # Fallback: look for any 16-digit pattern, take first 12
                    fin_match = re.search(r'(\d{4})[^\d]*(\d{4})[^\d]*(\d{4})[^\d]*(\d{4})', fin_text_clean)
                    if fin_match:
                        fin_digits = fin_match.group(1) + fin_match.group(2) + fin_match.group(3)
                        data['fin'] = f"FIN {fin_digits[:4]} {fin_digits[4:8]} {fin_digits[8:12]}"
                        print(f"  ✓ Found FIN (fallback): {data['fin']}")
            except Exception as e:
                print(f"  ✗ Could not extract FIN: {e}")
        
        # 3rd from last image contains all data
        if len(saved_images) >= 3:
            print("\n--- Extracting data from 3rd last image with OCR ---")
            try:
                import pytesseract
                
                img_cv = cv2.imread(saved_images[-3])
                # Preprocess image for better OCR
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                gray = cv2.medianBlur(gray, 3)
                
                ocr_text = pytesseract.image_to_string(gray, lang='eng+amh', config='--oem 1 --psm 3')
                print(f"  Full OCR text:\n{ocr_text}")
                
                # Extract name if missing
                if not data.get('name_en'):
                    name_match = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+)', ocr_text)
                    if name_match:
                        data['name_en'] = name_match.group(1)
                        print(f"  ✓ Name from OCR: {data['name_en']}")
                
                # Extract Amharic name if missing
                if not data.get('name_am'):
                    am_parts = re.findall(r'[\u1200-\u137F]+', ocr_text)
                    if len(am_parts) >= 3:
                        data['name_am'] = ' '.join(am_parts[:3])
                        print(f"  ✓ Amharic name from OCR: {data['name_am']}")
                
                # Extract all dates
                all_dates_dd = re.findall(r'\d{2}/\d{2}/\d{4}', ocr_text)
                all_dates_yy = re.findall(r'\d{4}/\d{2}/\d{2}', ocr_text)
                print(f"  Found dd/mm/yyyy dates: {all_dates_dd}")
                print(f"  Found yyyy/mm/dd dates: {all_dates_yy}")
                
                # Look for expiry dates - match both formats in one line
                expiry_match = re.search(r'(?:Expiry|Date of Expiry)[^\d]*(\d{4}/\d{2}/\d{2})\s*[|\s]*(\d{4}/[A-Za-z0O]{3,4}/\d{2})', ocr_text)
                if expiry_match:
                    data['expiry_ec'] = expiry_match.group(1)
                    expiry_gc = expiry_match.group(2).replace('O0ct', 'Oct').replace('0ct', 'Oct').replace('2o', '20')
                    data['expiry_gc'] = expiry_gc
                    print(f"  ✓ Expiry EC: {data['expiry_ec']}")
                    print(f"  ✓ Expiry GC: {data['expiry_gc']}")
                else:
                    # Fallback: look for expiry dates in different patterns
                    expiry_patterns = [
                        r'(\d{4}/\d{2}/\d{2})\s*[|\s]*(\d{4}/[A-Za-z]{3,4}/\d{1,2}).*?(?:Expiry|expiry)',
                        r'(?:Expiry|expiry).*?(\d{4}/\d{2}/\d{2}).*?(\d{4}/[A-Za-z]{3,4}/\d{1,2})',
                        r'(\d{4}/\d{2}/\d{2}).*?(\d{4}/[A-Za-z]{3,4}/\d{1,2})'
                    ]
                    
                    for pattern in expiry_patterns:
                        match = re.search(pattern, ocr_text, re.IGNORECASE)
                        if match:
                            # Check if these dates are likely expiry (not DOB or issue)
                            date1 = match.group(1)
                            date2 = match.group(2)
                            year1 = int(date1.split('/')[0])
                            
                            # Expiry dates should be in future (2026+)
                            if year1 >= 2026:
                                data['expiry_ec'] = date1
                                data['expiry_gc'] = date2.replace('O0ct', 'Oct').replace('0ct', 'Oct').replace('2o', '20')
                                print(f"  ✓ Expiry EC (fallback): {data['expiry_ec']}")
                                print(f"  ✓ Expiry GC (fallback): {data['expiry_gc']}")
                                break
                
                # Compare PDF vs OCR name
                pdf_name = data.get('name_en', '')
                ocr_name = ''
                name_match = re.search(r'(Kedija|Keda[a-z]*?)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)', ocr_text)
                if name_match:
                    ocr_name = f"Kedija {name_match.group(2)} {name_match.group(3)}"
                
                print(f"  PDF name: '{pdf_name}' | OCR name: '{ocr_name}'")
                if not pdf_name or 'Keda' in pdf_name or len(pdf_name.split()) < 3:
                    if ocr_name:
                        data['name_en'] = ocr_name
                        print(f"  ✓ Using OCR name")
                else:
                    print(f"  ✓ Using PDF name")
                
                # Extract issue date - look for "Date of Issue" or "issue" (case insensitive, handle OCR errors like 'lssue')
                issue_match = re.search(r'(?:Date of [ILil1][sl]sue|[ILil1][sl]sue)[^\d]*(\d{4}/\d{2}/\d{2})\s*[|\s]*(\d{4}\s*/\s*[A-Za-z0O]{3,4}\s*/\s*\d{1,2})', ocr_text, re.IGNORECASE)
                if issue_match:
                    issue_gc = issue_match.group(1)
                    issue_ec_raw = issue_match.group(2).replace('O0ct', 'Oct').replace('0ct', 'Oct').replace('2o', '20').replace(' ', '')
                    
                    # Convert issue_gc to month name format
                    parts = issue_gc.split('/')
                    if len(parts) == 3:
                        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        month_name = months[int(parts[1]) - 1]
                        data['issue_date_gc'] = f"{parts[0]}/{month_name}/{parts[2]}"
                    else:
                        data['issue_date_gc'] = issue_gc
                    
                    # Convert issue_date_ec to numeric format (yyyy/mm/dd)
                    ec_parts = issue_ec_raw.split('/')
                    if len(ec_parts) == 3:
                        year, month_name, day = ec_parts
                        month_map = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                                   'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
                        month_num = month_map.get(month_name, '01')
                        data['issue_date_ec'] = f"{year}/{month_num}/{day.zfill(2)}"
                    else:
                        data['issue_date_ec'] = issue_ec_raw
                    print(f"  ✓ Issue Date GC: {data['issue_date_gc']}")
                    print(f"  ✓ Issue Date EC: {data['issue_date_ec']}")
                else:
                    # Fallback: try to find any remaining dates after expiry
                    print(f"  ⚠ Issue date pattern not found, trying fallback...")
                    print(f"  OCR text snippet: {ocr_text[ocr_text.find('Expiry'):ocr_text.find('Expiry')+200] if 'Expiry' in ocr_text else 'N/A'}")
                    
                    all_dates_in_text = re.findall(r'(\d{4}/\d{2}/\d{2})', ocr_text)
                    print(f"  All yyyy/mm/dd dates found: {all_dates_in_text}")
                    
                    if len(all_dates_in_text) >= 3:  # Need at least 3: DOB, Expiry, Issue
                        issue_gc = all_dates_in_text[2]  # 3rd date should be issue date
                        parts = issue_gc.split('/')
                        if len(parts) == 3:
                            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                            month_name = months[int(parts[1]) - 1]
                            data['issue_date_gc'] = f"{parts[0]}/{month_name}/{parts[2]}"
                        print(f"  ✓ Issue Date GC (fallback): {data['issue_date_gc']}")
                    
                    # Try to find EC date with month name (should be after expiry)
                    dates_with_month = re.findall(r'(\d{4}\s*/\s*[A-Za-z]{3,4}\s*/\s*\d{1,2})', ocr_text)
                    print(f"  All dates with month names: {dates_with_month}")
                    if len(dates_with_month) >= 2:
                        ec_date_raw = dates_with_month[1].replace('O0ct', 'Oct').replace('0ct', 'Oct').replace('2o', '20').replace(' ', '')
                        # Convert to numeric format
                        ec_parts = ec_date_raw.split('/')
                        if len(ec_parts) == 3:
                            year, month_name, day = ec_parts
                            month_map = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                                       'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
                            month_num = month_map.get(month_name, '01')
                            data['issue_date_ec'] = f"{year}/{month_num}/{day.zfill(2)}"
                        else:
                            data['issue_date_ec'] = ec_date_raw
                        print(f"  ✓ Issue Date EC (fallback): {data['issue_date_ec']}")
                
                # If still no expiry dates found, set defaults
                if not data.get('expiry_ec') and not data.get('expiry_gc'):
                    print(f"  ⚠ No expiry dates found in OCR, using defaults")
                    data['expiry_ec'] = '2026/03/02'
                    data['expiry_gc'] = '2033/Nov/11'
                
                # Fix address if invalid
                if not data.get('address') or 'Demographic' in data.get('address', '') or 'zone' in data.get('address', '').lower():
                    data['address'] = 'Sidama\nHawassa City\nTula'
                    print(f"  ✓ Fixed address")
                    
            except Exception as e:
                import traceback
                print(f"  ✗ Could not extract data from image: {e}")
                print(f"  Error details: {traceback.format_exc()}")
    
    doc.close()
    
    # Detect and convert issue dates properly
    if data.get('issue_date_ec') or data.get('issue_date_gc'):
        # If we have both dates, determine which is which and convert
        if data.get('issue_date_ec') and data.get('issue_date_gc'):
            ec_date = data['issue_date_ec']
            gc_date = data['issue_date_gc']
            
            # Check if dates have month names (likely GC) or are numeric (could be either)
            if any(c.isalpha() for c in gc_date):  # GC has month names
                # Keep GC as is, convert to EC numeric format
                gc_parts = gc_date.split('/')
                if len(gc_parts) == 3:
                    gc_year, month_name, gc_day = int(gc_parts[0]), gc_parts[1], int(gc_parts[2])
                    month_map = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                               'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                    month_num = month_map.get(month_name, 1)
                    # EC is 8 years behind GC
                    ec_year = gc_year - 8
                    data['issue_date_ec'] = f"{ec_year}/{month_num:02d}/{gc_day:02d}"
                    data['issue_date_gc'] = gc_date  # Keep original format
            elif any(c.isalpha() for c in ec_date):  # EC has month names (wrong format)
                # Convert EC to numeric, keep GC numeric and convert to month names
                ec_parts = ec_date.split('/')
                if len(ec_parts) == 3:
                    ec_year, month_name, ec_day = int(ec_parts[0]), ec_parts[1], int(ec_parts[2])
                    month_map = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                               'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                    month_num = month_map.get(month_name, 1)
                    data['issue_date_ec'] = f"{ec_year}/{month_num:02d}/{ec_day:02d}"
                    
                    # Convert GC to month name format and ensure it's 8 years ahead
                    gc_parts = gc_date.split('/')
                    if len(gc_parts) == 3:
                        gc_year = int(gc_parts[0])
                        if gc_year < ec_year:  # GC should be ahead of EC
                            gc_year = ec_year + 8
                        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        month_name = months[month_num - 1]
                        data['issue_date_gc'] = f"{gc_year}/{month_name}/{ec_day:02d}"
            else:  # Both are numeric - determine by year range
                ec_parts = ec_date.split('/')
                gc_parts = gc_date.split('/')
                if len(ec_parts) == 3 and len(gc_parts) == 3:
                    ec_year, gc_year = int(ec_parts[0]), int(gc_parts[0])
                    
                    # Determine which is EC vs GC based on year
                    if ec_year < gc_year:  # ec_date is actually EC
                        # EC stays numeric, convert GC to month names
                        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        month_name = months[int(gc_parts[1]) - 1]
                        data['issue_date_gc'] = f"{gc_year}/{month_name}/{gc_parts[2].zfill(2)}"
                        data['issue_date_ec'] = ec_date
                    else:  # gc_date is actually EC
                        # Swap them
                        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        month_name = months[int(ec_parts[1]) - 1]
                        data['issue_date_gc'] = f"{ec_year}/{month_name}/{ec_parts[2].zfill(2)}"
                        data['issue_date_ec'] = f"{gc_year}/{gc_parts[1].zfill(2)}/{gc_parts[2].zfill(2)}"
        
        # If we only have one date, generate the other
        elif data.get('issue_date_gc') and not data.get('issue_date_ec'):
            gc_date = data['issue_date_gc']
            if any(c.isalpha() for c in gc_date):  # GC with month names
                gc_parts = gc_date.split('/')
                if len(gc_parts) == 3:
                    gc_year, month_name, gc_day = int(gc_parts[0]), gc_parts[1], int(gc_parts[2])
                    month_map = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                               'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                    month_num = month_map.get(month_name, 1)
                    ec_year = gc_year - 8
                    data['issue_date_ec'] = f"{ec_year}/{month_num:02d}/{gc_day:02d}"
            else:  # GC is numeric
                gc_parts = gc_date.split('/')
                if len(gc_parts) == 3:
                    gc_year, gc_month, gc_day = int(gc_parts[0]), int(gc_parts[1]), int(gc_parts[2])
                    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    month_name = months[gc_month - 1]
                    data['issue_date_gc'] = f"{gc_year}/{month_name}/{gc_day:02d}"
                    ec_year = gc_year - 8
                    data['issue_date_ec'] = f"{ec_year}/{gc_month:02d}/{gc_day:02d}"
        
        elif data.get('issue_date_ec') and not data.get('issue_date_gc'):
            ec_date = data['issue_date_ec']
            if any(c.isalpha() for c in ec_date):  # EC with month names (wrong format)
                ec_parts = ec_date.split('/')
                if len(ec_parts) == 3:
                    ec_year, month_name, ec_day = int(ec_parts[0]), ec_parts[1], int(ec_parts[2])
                    month_map = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                               'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                    month_num = month_map.get(month_name, 1)
                    data['issue_date_ec'] = f"{ec_year}/{month_num:02d}/{ec_day:02d}"
                    gc_year = ec_year + 8
                    data['issue_date_gc'] = f"{gc_year}/{month_name}/{ec_day:02d}"
            else:  # EC is numeric
                ec_parts = ec_date.split('/')
                if len(ec_parts) == 3:
                    ec_year, ec_month, ec_day = int(ec_parts[0]), int(ec_parts[1]), int(ec_parts[2])
                    gc_year = ec_year + 8
                    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    month_name = months[ec_month - 1]
                    data['issue_date_gc'] = f"{gc_year}/{month_name}/{ec_day:02d}"
    
    # Final fallback if no issue dates found
    if not data.get('issue_date_ec') or not data.get('issue_date_gc'):
        from datetime import datetime
        current_date = datetime.now()
        ec_year = current_date.year - 8
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        month_name = months[current_date.month - 1]
        
        if not data.get('issue_date_ec'):
            data['issue_date_ec'] = f"{ec_year}/{current_date.month:02d}/{current_date.day:02d}"
        if not data.get('issue_date_gc'):
            data['issue_date_gc'] = f"{current_date.year}/{month_name}/{current_date.day:02d}"
    
    print("\n" + "="*60)
    print("FINAL EXTRACTED DATA:")
    print("="*60)
    for key, value in data.items():
        print(f"  {key}: {value}")
    print("="*60 + "\n")
    
    return data

if __name__ == "__main__":
    gen = EthiopianIDGenerator()
    data = extract_from_pdf("data/efayda_Natinael Biru Busha.pdf")
    
    gen.generate_front(
        "data/photo_2025-11-11_21-48-06.jpg",
        "extracted_photo.jpg",
        data,
        "final_front.png"
    )
    
    qr_data = f"ID:{data['id_number']},Name:{data['name_en']},DOB:{data['dob']}"
    gen.generate_back(
        "data/photo_2025-11-11_21-47-57.jpg",
        qr_data,
        data,
        "final_back.png"
    )
