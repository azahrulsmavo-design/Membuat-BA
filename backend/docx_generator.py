from docx import Document
from docx.shared import Mm, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import requests
from io import BytesIO
import os

def fetch_image(path_or_url):
    """
    Fetches an image from a local path or URL and returns a BytesIO object.
    Returns None if the image cannot be loaded.
    """
    if not path_or_url:
        return None

    try:
        # Check if it's a URL
        if path_or_url.startswith('http'):
            # Specific handling for Google Drive is done in the frontend/proxy, 
            # but if a direct URL (e.g., from proxy) is passed, we handle it here.
            # Ideally, the frontend sends base64 or a local path if it was already downloaded.
            # But if we get a raw URL, try to fetch it.
            
            # Disable SSL verify for internal consistency with pdf_generator
            response = requests.get(path_or_url, verify=False, timeout=10)
            if response.status_code == 200:
                return BytesIO(response.content)
            else:
                return None
        
        # Check if it's a base64 string (data URI)
        elif path_or_url.startswith('data:image'):
            # Base64 handling
            from base64 import b64decode
            header, encoded = path_or_url.split(",", 1)
            data = b64decode(encoded)
            return BytesIO(data)

        # Local file path
        elif os.path.exists(path_or_url):
             with open(path_or_url, 'rb') as f:
                return BytesIO(f.read())
        
        return None

    except Exception as e:
        print(f"Error fetching image {path_or_url}: {e}")
        return None

def set_cell_margins(cell, top=0, start=0, bottom=0, end=0):
    """
    Sets cell margins for a specific table cell.
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    
    for name, value in [('top', top), ('left', start), ('bottom', bottom), ('right', end)]:
        node = OxmlElement(f'w:{name}')
        node.set(qn('w:w'), str(int(value * 20))) # value in points * 20 = twips? No, input is roughly pixels or small units? 
        # Actually docx uses distinct units. Let's rely on standard paragraph spacing inside calls instead if this is complex.
        # But this function is useful for strict layout. 
        # width in w:w is in twentieths of a point (dxa).
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    
    tcPr.append(tcMar)

def create_multiset_docx(data, output_path):
    doc = Document()
    
    # Set Narrow Margins (1.27 cm)
    section = doc.sections[0]
    section.page_height = Mm(297)
    section.page_width = Mm(210)
    section.left_margin = Mm(12.7)
    section.right_margin = Mm(12.7)
    section.top_margin = Mm(12.7)
    section.bottom_margin = Mm(12.7)

    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    units = data.get('units', [])
    layout_config = data.get('layout', {}) 

    for i, unit in enumerate(units):
        nopol = unit.get('nopol', 'UNKNOWN')
        bu = unit.get('bu', 'UNKNOWN')
        lokasi = unit.get('lokasi', 'UNKNOWN')
        images = unit.get('images', {})

        # --- PAGE 1: Check Fisik Dokumen ---
        
        # Header
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"BERITA ACARA CEK FISIK KENDARAAN\nUNIT BISNIS: {bu}\nLOKASI: {lokasi}")
        run.bold = True
        run.font.size = Pt(14)
        
        p = doc.add_paragraph(f"Nomor Polisi: {nopol}")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].bold = True
        
        doc.add_paragraph("-" * 80).alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_heading('1. DOKUMEN KENDARAAN', level=2)

        # Table for Documents (STNK, Pajak, KIR)
        # Layout: 
        # Row 1: STNK (Left), Pajak (Right)
        # Row 2: KIR Kertas (Left), KIR Kartu (Right)
        
        table = doc.add_table(rows=2, cols=2)
        table.style = 'Table Grid'
        table.autofit = False
        # Set column widths roughly half page each (minus margins)
        # Page width 210mm - 25.4mm margin = 184.6mm. Col width ~92mm
        
        for row in table.rows:
            for cell in row.cells:
                cell.width = Mm(92)

        # Helper to fill cell
        def fill_cell(cell, title, img_key):
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(title + "\n")
            run.bold = True
            
            img_data = images.get(img_key)
            if img_data:
                # Handle both dict with dataUrl or direct string
                path = img_data.get('dataUrl') if isinstance(img_data, dict) else img_data
                
                img_stream = fetch_image(path)
                if img_stream:
                    try:
                        # Add image, constraining width to cell width minus padding
                        run.add_picture(img_stream, width=Mm(85))
                    except Exception as e:
                        run.add_text(f"[Error loading image: {e}]")
                else:
                    run.add_text("[Gambar Tidak Ditemukan]")
            else:
                run.add_text("[Tidak Ada Gambar]")

        fill_cell(table.cell(0, 0), "FOTO STNK", 'stnk')
        fill_cell(table.cell(0, 1), "FOTO PAJAK", 'tax')
        fill_cell(table.cell(1, 0), "FOTO KIR (Kertas)", 'kir')
        fill_cell(table.cell(1, 1), "FOTO KIR (Kartu)", 'kir_card')

        doc.add_page_break()

        # --- PAGE 2: Foto Fisik Kendaraan ---
        
        # Header (Repeated for context)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"FOTO FISIK KENDARAAN - {nopol}")
        run.bold = True
        run.font.size = Pt(14)
        
        doc.add_heading('2. KONDISI FISIK', level=2)

        # Table for Physical Photos
        # Row 1: Depan, Belakang
        # Row 2: Kanan, Kiri
        
        table_phys = doc.add_table(rows=2, cols=2)
        table_phys.style = 'Table Grid'
        
        fill_cell(table_phys.cell(0, 0), "TAMPAK DEPAN", 'front')
        fill_cell(table_phys.cell(0, 1), "TAMPAK BELAKANG", 'back')
        fill_cell(table_phys.cell(1, 0), "TAMPAK KANAN", 'right')
        fill_cell(table_phys.cell(1, 1), "TAMPAK KIRI", 'left')

        doc.add_page_break()

    # --- PAGE 3: Summary (Rekapitulasi) ---
    doc.add_heading('REKAPITULASI ASET KENDARAAN', level=1)
    
    summary_table = doc.add_table(rows=1, cols=4)
    summary_table.style = 'Table Grid'
    
    # Header Row
    hdr_cells = summary_table.rows[0].cells
    hdr_cells[0].text = 'No'
    hdr_cells[1].text = 'Nomor Polisi'
    hdr_cells[2].text = 'Status Dokumen'
    hdr_cells[3].text = 'Kekurangan'
    
    for i, unit in enumerate(units):
        row_cells = summary_table.add_row().cells
        row_cells[0].text = str(i + 1)
        row_cells[1].text = unit.get('nopol', 'UNKNOWN')
        
        # Logic to check completeness
        unit_images = unit.get('images', {})
        required_keys = ['stnk', 'tax', 'front', 'back', 'right', 'left'] # Basic Requirement
        missing = []
        
        for key in required_keys:
            val = unit_images.get(key)
            # Check for null, empty string, or empty dict
            if not val or (isinstance(val, dict) and not val.get('dataUrl')):
                missing.append(key.upper())
        
        if not missing:
            row_cells[2].text = "LENGKAP"
            row_cells[3].text = "-"
        else:
            row_cells[2].text = "TIDAK LENGKAP"
            row_cells[3].text = ", ".join(missing)

    doc.save(output_path)
    return output_path
