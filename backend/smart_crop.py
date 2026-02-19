import cv2
import numpy as np

try:
    import imutils
except ImportError:
    imutils = None

# --- FUNGSI MATEMATIKA UNTUK MELURUSKAN SUDUT ---
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)] # Kiri Atas
    rect[2] = pts[np.argmax(s)] # Kanan Bawah
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)] # Kanan Atas
    rect[3] = pts[np.argmax(diff)] # Kiri Bawah
    return rect

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Hitung lebar baru
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    # Hitung tinggi baru
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # Peta tujuan (rata)
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    # Lakukan transformasi perspektif
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

# --- LOGIKA UTAMA ---
def smart_doc_crop(image_bytes):
    """
    Menerima bytes gambar, mencoba crop dokumen (perspektif),
    mengembalikan bytes gambar hasil crop (atau asli jika gagal).
    """
    try:
        if imutils is None:
            print("INFO: imutils not installed, skipping smart crop")
            return image_bytes

        # Konversi bytes ke numpy array
        nparr = np.frombuffer(image_bytes.getvalue(), np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return image_bytes

        orig = image.copy()
        
        # 1. Resize agar deteksi lebih cepat & akurat (tinggi 500px)
        ratio = image.shape[0] / 500.0
        image = imutils.resize(image, height=500)

        # 2. Preprocessing (Grayscale -> Blur -> Edges)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(gray, 75, 200)

        # 3. Cari Kontur
        cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

        screenCnt = None
        
        # 4. Cari kontur segi empat (kertas)
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            
            # Jika punya 4 sudut, kemungkinan itu kertas
            if len(approx) == 4:
                screenCnt = approx
                break

        if screenCnt is None:
            # Gagal deteksi kertas, kembalikan asli
            print("INFO: Smart Crop - No document found found")
            return image_bytes
        
        # 5. Luruskan (Warp) - Gunakan koordinat asli (dikalikan rasio)
        warped = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)
        
        # 6. Encode kembali ke bytes
        success, encoded_img = cv2.imencode('.jpg', warped)
        if success:
            import io
            return io.BytesIO(encoded_img.tobytes())
        else:
            return image_bytes

    except Exception as e:
        print(f"Error Smart Crop: {e}")
        return image_bytes
