import os
import io
import re
import requests
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from smart_crop import smart_doc_crop

class MultiSetPDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Halaman {self.page_no()}', 0, 0, 'C')

def fetch_drive_image(url):
    """
    Downloads image from Google Drive URL to BytesIO object.
    Supports formats: /file/d/ID/view and open?id=ID
    """
    if not url: 
        return None

    try:
        # Regex to extract File ID
        match_id = re.search(r'id=([a-zA-Z0-9_-]+)', url)
        match_d = re.search(r'/d/([a-zA-Z0-9_-]+)', url)

        file_id = None
        if match_id:
            file_id = match_id.group(1)
        elif match_d:
            file_id = match_d.group(1)

        if not file_id:
            return None 

        if not file_id:
            return None 

        session = requests.Session()

        # --- OPTIMIZATION: Try Thumbnail API First (sz=s1000) ---
        thumbnail_url = f'https://drive.google.com/thumbnail?id={file_id}&sz=s1000'
        # console.log equivalent for python backend
        print(f"INFO: Trying thumbnail for {file_id}")
        
        try:
            # Short timeout for thumbnail
            # Note: We now catch ALL exceptions to ensure fallback runs
            thumb_resp = session.get(thumbnail_url, timeout=5, verify=False)
            
            # Google sometimes returns 200 OK but with an HTML error page or empty body
            # We strictly check Content-Type
            ct = thumb_resp.headers.get('Content-Type', '')
            if thumb_resp.status_code == 200 and ct.startswith('image/'):
                 return io.BytesIO(thumb_resp.content)
            else:
                 print(f"WARN: Thumbnail fetch failed (Status: {thumb_resp.status_code}, Type: {ct}). Falling back to original.")
        except Exception as e:
            # This catch block ensures we proceed to fallback even if thumbnail request explodes
            print(f"WARN: Thumbnail API error ({e}). Falling back to original.")

        # --- FALLBACK: Use Original Download URL ---
        download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = session.get(download_url, stream=True, timeout=15, verify=False)
        
        # Helper to check for confirmation token
        def get_confirm_token(response):
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    return value
            return None

        token = get_confirm_token(response)

        if token:
            params = {'id': file_id, 'confirm': token}
            response = session.get(download_url, params=params, stream=True, timeout=15, verify=False)
            
        # Check Content-Type
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
             # Case: Virus scan warning might be in the HTML body (not cookies)
             # Or it's a login page
             content_preview = response.content[:200].decode('utf-8', errors='ignore')
             print(f"DEBUG: HTML response for {url}: {content_preview}")
             
             # Fallback: Try to find 'confirm=XXXX' in the HTML link
             # Google sometimes puts a link like <a href="/uc?export=download&amp;id=XXX&amp;confirm=Op9R">
             match_confirm = re.search(r'confirm=([a-zA-Z0-9_-]+)', response.text)
             if match_confirm:
                 confirm_code = match_confirm.group(1)
                 params = {'id': file_id, 'confirm': confirm_code}
                 response = session.get(download_url, params=params, stream=True, timeout=15, verify=False)
                 content_type = response.headers.get('Content-Type', '')

        if 'image' not in content_type and 'application/octet-stream' not in content_type:
            print(f"Warning: URL {url} returned Content-Type: {content_type}")
            # We continue anyway, as sometimes headers are wrong, but PIL will fail if it's not bytes.
            
        response.raise_for_status()
        return io.BytesIO(response.content)

    except Exception as e:
        print(f"Failed to download drive image {url}: {e}")
        return None

def fit_and_center_image(pdf, img_path, x, y, w, h, auto_crop=False):
    """
    Fits an image into a box defined by x, y, w, h while maintaining aspect ratio
    and centering it. Handles local paths and Google Drive URLs.
    """
    if not img_path:
        # Draw placeholder
        pdf.set_xy(x, y + h/2 - 5)
        # Using Helvetica for error text to be safe.
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(w, 10, "[No Image]", align='C')
        return

    try:
        image_source = img_path
        
        # Check if it is a Google Drive URL
        if isinstance(img_path, str) and ('drive.google.com' in img_path):
            drive_img_data = fetch_drive_image(img_path)
            if drive_img_data:
                image_source = drive_img_data
            else:
                 raise Exception("Failed to download or invalid Drive link")

        # --- SMART CROP LOGIC ---
        if auto_crop:
            # If it's a file path, read bytes first
            if isinstance(image_source, str):
                with open(image_source, 'rb') as f:
                    import io
                    image_source = io.BytesIO(f.read())
            
            # Apply Smart Crop
            image_source = smart_doc_crop(image_source)

        # Get image dimensions using Pillow
        # Image.open handles both file paths and file-like objects (BytesIO)
        with Image.open(image_source) as img:
            img_w, img_h = img.size
        
        # Calculate aspect ratios
        ratio_w = w / img_w
        ratio_h = h / img_h
        scale = min(ratio_w, ratio_h)
        
        new_w = img_w * scale
        new_h = img_h * scale
        
        # Center offset
        offset_x = (w - new_w) / 2
        offset_y = (h - new_h) / 2
        
        # Draw image
        # fpdf.image() also accepts BytesIO objects for 'name' argument if type is specified 
        # or it can infer from BytesIO content if we are lucky, but safest to pass the stream or path.
        # For BytesIO, FPDF2 recommends specifying a name or format.
        # However, passing the PIL image object directly is often supported or we pass the stream.
        # Let's try passing the stream/path directly as we did for local files.
        # Note: formatting might be tricky for FPDF with BytesIO without a name.
        # Let's use the image_source directly.
        pdf.image(image_source, x=x + offset_x, y=y + offset_y, w=new_w, h=new_h)
        
    except Exception as e:
        print(f"Error scaling image {str(img_path)[:50]}...: {e}")
        pdf.set_xy(x, y + h/2 - 5)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(w, 10, "[Error/Link]", align='C')

def create_multiset_pdf(units, output_path, layout_config=None):
    pdf = MultiSetPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Add Calibri Font (Try Windows path first, else fallback)
    main_font = "Helvetica"
    try:
        font_paths = {
            "": ["calibri.ttf", r"C:\Windows\Fonts\calibri.ttf"],
            "B": ["calibrib.ttf", r"C:\Windows\Fonts\calibrib.ttf"],
            "I": ["calibrii.ttf", r"C:\Windows\Fonts\calibrii.ttf"]
        }
        
        success_count = 0
        for style, paths in font_paths.items():
            found = False
            for path in paths:
                if os.path.exists(path):
                    pdf.add_font("Calibri", style, path, uni=True)
                    found = True
                    break
            if found:
                success_count += 1
                
        if success_count == 3:
            main_font = "Calibri"
        else:
             print("Warning: Calibri font not fully found. Falling back to Helvetica.")
             
    except Exception as e:
        print(f"Warning: Could not load Calibri font, falling back to Helvetica. Error: {e}")
        main_font = "Helvetica"

    # Default Layout Configuration
    default_layout = {
        'front': {'x': 10, 'y': 50, 'w': 90, 'h': 80},
        'back': {'x': 110, 'y': 50, 'w': 90, 'h': 80},
        'right': {'x': 10, 'y': 140, 'w': 90, 'h': 80},
        'left': {'x': 110, 'y': 140, 'w': 90, 'h': 80}
    }

    # Merge provided layout with defaults
    layout = default_layout.copy()
    if layout_config:
        for key, conf in layout_config.items():
            if key in layout and isinstance(conf, dict):
                layout[key].update(conf)

    processed_summary = []

    for unit in units:
        nopol = unit.get('nopol', 'UNKNOWN')
        bu = unit.get('bu', '')
        location = unit.get('lokasi', '')
        
        # Additional fields
        merk = unit.get('merk', '-')
        tipe = unit.get('tipe', '-')
        no_rangka = unit.get('no_rangka', '-')
        no_mesin = unit.get('no_mesin', '-')
        tahun = unit.get('tahun', '-')
        user_name = unit.get('user', '-')
        
        # Header Title Format
        header_title = f"BU : {bu} - {location} - {nopol}".upper()

        # ==========================================
        # HALAMAN 1: DOKUMEN (Moved from Page 3)
        # ==========================================
        pdf.add_page()
        pdf.set_font(main_font, "B", 11)
        pdf.cell(0, 10, header_title, ln=True, align='L')
        pdf.ln(2)
        
        # 1. STNK (Full Width)
        stnk_y = 35
        full_w = 170
        full_h = 70
        center_x = (210 - full_w) / 2
        
        # Draw STNK
        pdf.set_xy(center_x, stnk_y - 8)
        pdf.set_font(main_font, "B", 10)
        pdf.cell(full_w, 8, "FOTO STNK (SURAT TANDA NOMOR KENDARAAN) :", ln=False, align='L')
        pdf.rect(center_x, stnk_y, full_w, full_h)
        fit_and_center_image(pdf, unit.get('images', {}).get('stnk'), center_x, stnk_y, full_w, full_h, auto_crop=True)
        
        # 2. PAJAK (Full Width)
        pajak_y = stnk_y + full_h + 15
        pdf.set_xy(center_x, pajak_y - 8)
        pdf.set_font(main_font, "B", 10)
        pdf.cell(full_w, 8, "FOTO LEMBAR PAJAK :", ln=False, align='L')
        pdf.rect(center_x, pajak_y, full_w, full_h)
        fit_and_center_image(pdf, unit.get('images', {}).get('tax'), center_x, pajak_y, full_w, full_h, auto_crop=True)
        
        # 3. KIR (Split: Left = Paper, Right = Card)
        kir_y = pajak_y + full_h + 15
        half_w = (full_w - 10) / 2 # 10mm gap
        kir_h = 60 # Slightly smaller to fit page
        
        # Left: Paper KIR
        left_x = center_x
        pdf.set_xy(left_x, kir_y - 8)
        pdf.set_font(main_font, "B", 10)
        pdf.cell(half_w, 8, "FOTO LEMBAR KIR :", ln=False, align='L')
        pdf.rect(left_x, kir_y, half_w, kir_h)
        fit_and_center_image(pdf, unit.get('images', {}).get('kir'), left_x, kir_y, half_w, kir_h, auto_crop=True)
        
        # Right: Card KIR
        right_x = left_x + half_w + 10
        pdf.set_xy(right_x, kir_y - 8)
        pdf.set_font(main_font, "B", 10)
        pdf.cell(half_w, 8, "FOTO KARTU KIR :", ln=False, align='L')
        pdf.rect(right_x, kir_y, half_w, kir_h)
        fit_and_center_image(pdf, unit.get('images', {}).get('kir_card'), right_x, kir_y, half_w, kir_h, auto_crop=True)


        # ==========================================
        # HALAMAN 2: LAMPIRAN FOTO FISIK (Moved from Page 2)
        # ==========================================
        pdf.add_page()
        pdf.set_font(main_font, "B", 11)
        pdf.cell(0, 10, header_title, ln=True, align='L')
        pdf.ln(5)
        
        photo_items = [
            ('TAMPAK DEPAN', 'front'),
            ('TAMPAK BELAKANG', 'back'),
            ('TAMPAK SAMPING KANAN', 'right'),
            ('TAMPAK SAMPING KIRI', 'left')
        ]
        
        for label, key in photo_items:
            conf = layout.get(key, {})
            x, y, w, h = conf.get('x', 0), conf.get('y', 0), conf.get('w', 90), conf.get('h', 80)
            
            # Label
            pdf.set_xy(x, y - 8)
            pdf.set_font(main_font, "B", 9)
            pdf.cell(w, 8, label, ln=False, align='L')
            
            # Box
            pdf.set_draw_color(0, 0, 0)
            pdf.rect(x, y, w, h)
            
            # Image
            img_path = unit.get('images', {}).get(key)
            fit_and_center_image(pdf, img_path, x, y, w, h)
            

        # Check completeness for summary
        doc_keys = ['stnk', 'tax', 'kir', 'kir_card']
        photo_keys = ['front', 'back', 'right', 'left']
        missing = []
        for k in doc_keys + photo_keys:
             path = unit.get('images', {}).get(k)
             if not (path and os.path.exists(path)):
                 missing.append(k.upper())

        status = "LENGKAP" if not missing else f"KURANG ({len(missing)})"
        
        processed_summary.append({
            "nopol": nopol,
            "bu": bu,
            "status": status,
            "missing": ", ".join(missing) if missing else "-"
        })

    # --- FINAL PAGE: SUMMARY ---
    pdf.add_page()
    pdf.set_font(main_font, "B", 14)
    pdf.cell(0, 10, "RINGKASAN STATUS ASET", ln=True, align='C')
    pdf.ln(5)

    # Table Header
    pdf.set_font(main_font, "B", 10)
    pdf.set_fill_color(220, 220, 220)
    
    col_w = [10, 30, 30, 40, 80] # No, Nopol, BU, Status, Ket
    headers = ["No", "Nopol", "BU", "Status", "Keterangan"]
    
    table_w = sum(col_w)
    start_x = (pdf.w - table_w) / 2
    pdf.set_x(start_x)
    
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 10, h, 1, 0, 'C', True)
    pdf.ln()
    
    # Table Rows
    pdf.set_font(main_font, "", 10)
    for i, item in enumerate(processed_summary):
        pdf.set_x(start_x)
        
        # Status Color
        if "LENGKAP" in item['status']:
            pdf.set_text_color(0, 100, 0)
        else:
            pdf.set_text_color(200, 0, 0)
            
        pdf.cell(col_w[0], 10, str(i+1), 1, 0, 'C')
        pdf.cell(col_w[1], 10, item['nopol'], 1, 0, 'C')
        pdf.cell(col_w[2], 10, item['bu'], 1, 0, 'C')
        pdf.cell(col_w[3], 10, item['status'], 1, 0, 'C')
        
        pdf.set_text_color(0, 0, 0) # Reset color
        pdf.cell(col_w[4], 10, item['missing'], 1, 0, 'L')
        pdf.ln()

    pdf.output(output_path)
    return output_path
