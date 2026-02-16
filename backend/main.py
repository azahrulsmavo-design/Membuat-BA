import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import cv2

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model (lazy loading or at start)
# Using yolov8n.pt as requested. It will download automatically on first use if not present.
model = YOLO('yolov8n.pt') 

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def ai_smart_crop(image_path, output_path):
    """
    Detects the first object using YOLOv8 and crops the image with a margin.
    """
    results = model(image_path)
    img = cv2.imread(image_path)
    
    # Check if image loaded correctly
    if img is None:
        return False

    for result in results:
        # Check if boxes are detected
        if result.boxes and len(result.boxes) > 0:
            # Get box with highest confidence (first one usually)
            box = result.boxes[0].xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, box)
            
            # Add margin (padding)
            h, w, _ = img.shape
            pad = int(min(h, w) * 0.05) # 5% padding
            x1 = max(0, x1 - pad)
            y1 = max(0, y1 - pad)
            x2 = min(w, x2 + pad)
            y2 = min(h, y2 + pad)
            
            # Crop
            cropped_img = img[y1:y2, x1:x2]
            
            # Save
            cv2.imwrite(output_path, cropped_img)
            return True
            
    # Fallback: copy original if no detection
    # shutil.copy(image_path, output_path) 
    return False

@app.post("/crop")
async def crop_image(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    cropped_filename = f"cropped_{filename}"
    cropped_path = os.path.join(UPLOAD_DIR, cropped_filename)

    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process
        success = ai_smart_crop(file_path, cropped_path)
        
        if success:
            return FileResponse(cropped_path, media_type="image/jpeg")
        else:
            # If AI fails, return original or error? 
            # User requirement: "Proceed". So maybe return original?
            # User code said "False # Jika gagal deteksi". 
            # I will return the original image if crop fails, but maybe with a header/flag?
            # For now, let's just return the original if it fails to crop, 
            # or maybe a 204 to let frontend handle it? 
            # Let's return the original for simplicity so the flow continues.
            return FileResponse(file_path, media_type="image/jpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up files? 
        # In a real app we'd want to clean up. 
        # For now, we can leave them or use a background task to delete after response.
        # Since we return FileResponse, we can't delete immediately.
        pass

import base64
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pdf_generator import create_multiset_pdf, fetch_drive_image

# ... existing imports ...

# Pydantic Models for JSON Payload
class UnitImages(BaseModel):
    front: Optional[str] = None
    back: Optional[str] = None
    right: Optional[str] = None
    left: Optional[str] = None
    stnk: Optional[str] = None
    tax: Optional[str] = None
    kir: Optional[str] = None
    kir_card: Optional[str] = None

class UnitData(BaseModel):
    nopol: str
    bu: str
    lokasi: str
    images: UnitImages

class ReportRequest(BaseModel):
    units: List[UnitData]
    layout: Optional[Dict[str, Dict[str, float]]] = None # Nested dict for x,y,w,h

def save_base64_image(data_url):
    """Decodes base64 data_url and saves to a temp file. Returns the path."""
    if not data_url or "," not in data_url:
        return None
    
    try:
        header, encoded = data_url.split(",", 1)
        data = base64.b64decode(encoded)
        extension = header.split(";")[0].split("/")[1]
        
        filename = f"{uuid.uuid4()}.{extension}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(data)
        return filepath
    except Exception as e:
        print(f"Error saving base64 image: {e}")
        return None

from fastapi.responses import FileResponse, StreamingResponse
# ... (existing imports)
from pdf_generator import create_multiset_pdf, fetch_drive_image

# ... (existing code)

@app.get("/proxy-image")
async def proxy_image(url: str):
    """
    Proxies a Google Drive image to the frontend to bypass CORS for cropping.
    """
    try:
        image_io = fetch_drive_image(url)
        if not image_io:
            raise HTTPException(status_code=404, detail="Failed to fetch image from Drive")
        
        # Reset pointer
        image_io.seek(0)
        
        return StreamingResponse(image_io, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-multiset")
async def generate_multiset_report(request: ReportRequest):
    try:
        # 1. Process Data & Save Images
        processed_units = []
        
        for unit in request.units:
            unit_dict = {
                "nopol": unit.nopol,
                "bu": unit.bu,
                "lokasi": unit.lokasi,
                "images": {}
            }
            
            # Map images
            img_map = {
                "front": unit.images.front,
                "back": unit.images.back,
                "right": unit.images.right,
                "left": unit.images.left,
                "stnk": unit.images.stnk,
                "tax": unit.images.tax,
                "kir": unit.images.kir,
                "kir_card": unit.images.kir_card,
            }
            
            for key, data_val in img_map.items():
                if data_val:
                    # Try to save as base64
                    saved_path = save_base64_image(data_val)
                    if saved_path:
                        unit_dict["images"][key] = saved_path
                    else:
                        # If not base64 (e.g. URL), keep original value
                        unit_dict["images"][key] = data_val
            
            processed_units.append(unit_dict)
            
        # 2. Generate PDF
        pdf_filename = f"Report_Assets_{uuid.uuid4()}.pdf"
        output_path = os.path.join(UPLOAD_DIR, pdf_filename)
        
        # Pass layout config
        create_multiset_pdf(processed_units, output_path, request.layout)
        
        return FileResponse(output_path, media_type="application/pdf", filename="Asset_Report.pdf")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from docx_generator import create_multiset_docx
import time

@app.post("/generate-multiset-docx")
async def generate_multiset_docx(request: ReportRequest):
    try:
        PROCESSED_DATA = {"units": [], "layout": request.layout}
        
        for unit in request.units:
            unit_dict = {
                "nopol": unit.nopol,
                "bu": unit.bu,
                "lokasi": unit.lokasi,
                "images": {}
            }
            
            img_map = {
                "front": unit.images.front,
                "back": unit.images.back,
                "right": unit.images.right,
                "left": unit.images.left,
                "stnk": unit.images.stnk,
                "tax": unit.images.tax,
                "kir": unit.images.kir,
                "kir_card": unit.images.kir_card,
            }
            
            for key, data_val in img_map.items():
                if data_val:
                    unit_dict["images"][key] = data_val
            
            PROCESSED_DATA["units"].append(unit_dict)
            
        timestamp = int(time.time())
        filename = f"ba_asset_multiset_{timestamp}.docx"
        output_path = os.path.join(UPLOAD_DIR, filename)
        
        create_multiset_docx(PROCESSED_DATA, output_path)
        
        return FileResponse(output_path, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', filename=filename)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "running", "model": "YOLOv8n"}
