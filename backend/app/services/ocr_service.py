import os
import sys
import io
import cv2
import numpy as np
from PIL import Image
from typing import Optional

# Fix Windows console encoding for EasyOCR progress bars (uses █ chars)
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass


def preprocess_image(image_path: str) -> np.ndarray:
    """Preprocess image for better OCR results."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return thresh


# Module-level cache for EasyOCR reader (heavy to initialize)
_easyocr_reader = None


def _get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        _easyocr_reader = easyocr.Reader(["en"], gpu=False)
    return _easyocr_reader


def run_ocr_easyocr(image_path: str) -> dict:
    """Use EasyOCR for text extraction — no system install needed, works offline."""
    reader = _get_easyocr_reader()
    img = cv2.imread(image_path)
    if img is None:
        return {
            "text": "",
            "boxes": [],
            "confidences": [],
            "lines": [],
            "engine": "easyocr",
            "error": "Could not read image",
        }

    h, w = img.shape[:2]
    max_dim = max(h, w)
    scale = 1.0
    if max_dim > 1600:
        scale = 1600.0 / max_dim
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    results = reader.readtext(img, detail=1, paragraph=False)

    if not results:
        return {
            "text": "",
            "boxes": [],
            "confidences": [],
            "lines": [],
            "engine": "easyocr",
            "error": "No text detected in image",
        }

    boxes = []
    confidences = []
    words = []
    inv_scale = 1.0 / scale

    for (bbox, text, conf) in results:
        # Scale bounding box back to original image dimensions
        boxes.append([[int(p[0] * inv_scale), int(p[1] * inv_scale)] for p in bbox])
        confidences.append(float(conf))
        words.append(text)

    # Build full text by grouping words into lines based on Y-coordinate proximity
    if results:
        sorted_results = sorted(results, key=lambda r: (r[0][0][1], r[0][0][0]))  # Sort by Y then X
        lines = []
        current_line = []
        current_y = None
        y_threshold = 15  # pixels

        for (bbox, text, conf) in sorted_results:
            top_y = bbox[0][1]
            if current_y is None or abs(top_y - current_y) < y_threshold:
                current_line.append(text)
                current_y = top_y if current_y is None else (current_y + top_y) / 2
            else:
                lines.append(" ".join(current_line))
                current_line = [text]
                current_y = top_y

        if current_line:
            lines.append(" ".join(current_line))

        full_text = "\n".join(lines)
    else:
        full_text = ""
        lines = []

    return {
        "text": full_text,
        "boxes": boxes,
        "confidences": confidences,
        "lines": lines,
        "engine": "easyocr",
    }


def run_ocr_google_vision(image_path: str, api_key: str) -> dict:
    """Use Google Cloud Vision API for OCR (requires billing enabled)."""
    import base64
    import httpx

    with open(image_path, "rb") as f:
        image_content = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "requests": [
            {
                "image": {"content": image_content},
                "features": [
                    {"type": "TEXT_DETECTION", "maxResults": 1},
                    {"type": "DOCUMENT_TEXT_DETECTION", "maxResults": 1},
                ],
            }
        ]
    }

    response = httpx.post(
        f"https://vision.googleapis.com/v1/images:annotate?key={api_key}",
        json=payload,
        timeout=30.0,
    )
    response.raise_for_status()
    result = response.json()

    responses = result.get("responses", [])
    if not responses:
        return {"text": "", "boxes": [], "confidences": [], "lines": [], "engine": "google_vision", "error": "No response"}

    annotations = responses[0]
    full_text_annotation = annotations.get("fullTextAnnotation")
    text_annotations = annotations.get("textAnnotations", [])

    if full_text_annotation:
        full_text = full_text_annotation.get("text", "")
    elif text_annotations:
        full_text = text_annotations[0].get("description", "")
    else:
        return {"text": "", "boxes": [], "confidences": [], "lines": [], "engine": "google_vision", "error": "No text detected"}

    boxes = []
    confidences = []
    for annotation in text_annotations[1:]:
        desc = annotation.get("description", "")
        vertices = annotation.get("boundingPoly", {}).get("vertices", [])
        if vertices and desc.strip():
            box = [[v.get("x", 0), v.get("y", 0)] for v in vertices]
            boxes.append(box)
            confidences.append(annotation.get("score", 0.95))

    return {
        "text": full_text,
        "boxes": boxes,
        "confidences": confidences,
        "lines": full_text.split("\n"),
        "engine": "google_vision",
    }


def run_ocr_tesseract(image_path: str) -> dict:
    """Fallback: Use Tesseract for OCR (requires system install)."""
    import pytesseract

    preprocessed = preprocess_image(image_path)
    pil_img = Image.fromarray(preprocessed)
    config = "--oem 3 --psm 6"
    text = pytesseract.image_to_string(pil_img, lang="eng", config=config)
    data = pytesseract.image_to_data(
        pil_img, lang="eng", config=config, output_type=pytesseract.Output.DICT
    )

    boxes = []
    confidences = []
    n = len(data["level"])
    for i in range(n):
        if int(data["conf"][i]) > 30 and data["text"][i].strip():
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            boxes.append([[x, y], [x + w, y], [x + w, y + h], [x, y + h]])
            confidences.append(int(data["conf"][i]) / 100.0)

    return {
        "text": text,
        "boxes": boxes,
        "confidences": confidences,
        "lines": text.split("\n"),
        "engine": "tesseract",
    }


_google_vision_disabled = False

def run_ocr(image_path: str) -> dict:
    """
    Run OCR with fallback chain:
      1. Google Cloud Vision (if API key is set and billing enabled)
      2. EasyOCR (Python-only, no system install needed)
      3. Tesseract (requires system install)
    """
    global _google_vision_disabled
    api_key = os.environ.get("GOOGLE_VISION_API_KEY", "")

    # 1) Try Google Cloud Vision first (most accurate)
    if api_key and not _google_vision_disabled:
        try:
            result = run_ocr_google_vision(image_path, api_key)
            if result.get("text"):
                print(f"[OCR] Google Vision succeeded ({len(result['text'])} chars)")
                return result
            print(f"[OCR] Google Vision returned no text: {result.get('error', 'unknown')}")
        except Exception as e:
            print(f"[OCR] Google Vision failed: {e}")
            # If billing is disabled or authentication fails, disable for future calls
            err_str = str(e).lower()
            if "403" in err_str or "billing" in err_str or "permission" in err_str or "401" in err_str:
                print("[OCR] Disabling Google Vision for future calls (billing/permission error)")
                _google_vision_disabled = True

    # 2) Try EasyOCR (works offline, no system install)
    try:
        result = run_ocr_easyocr(image_path)
        if result.get("text"):
            print(f"[OCR] EasyOCR succeeded ({len(result['text'])} chars)")
            return result
        print(f"[OCR] EasyOCR returned no text")
    except Exception as e:
        print(f"[OCR] EasyOCR failed: {e}")

    # 3) Try Tesseract (requires system install)
    try:
        result = run_ocr_tesseract(image_path)
        if result.get("text"):
            print(f"[OCR] Tesseract succeeded ({len(result['text'])} chars)")
            return result
    except Exception as e:
        print(f"[OCR] Tesseract failed: {e}")

    return {
        "text": "",
        "boxes": [],
        "confidences": [],
        "lines": [],
        "engine": "none",
        "error": "All OCR engines failed. Install EasyOCR (pip install easyocr) or Tesseract.",
    }


def estimate_font_sizes(image_path: str, boxes: list) -> list:
    """Estimate font sizes from bounding boxes."""
    img = cv2.imread(image_path)
    if img is None or not boxes:
        return []

    estimated_dpi = 300
    sizes = []

    for box in boxes:
        if len(box) >= 4:
            y_coords = [pt[1] for pt in box]
            box_height_px = max(y_coords) - min(y_coords)
            height_mm = (box_height_px / estimated_dpi) * 25.4
            sizes.append(round(height_mm, 2))

    return sizes


def detect_barcode(image_path: str) -> Optional[str]:
    """Detect and decode barcodes in the image using multiple engines (OpenCV + pyzbar fallback)."""
    # 1. OpenCV BarcodeDetector (EAN-13, UPC, Code 128, etc. - works natively on Windows/Linux)
    try:
        detector = cv2.barcode.BarcodeDetector()
        img = cv2.imread(image_path)
        if img is not None:
            res = detector.detectAndDecode(img)
            if res and isinstance(res, (tuple, list)) and len(res) > 0 and res[0]:
                code = str(res[0]).strip()
                if code and len(code) >= 6:
                    return code
    except Exception:
        pass

    # 2. OpenCV QRCodeDetector (for QR codes)
    try:
        qr_detector = cv2.QRCodeDetector()
        img = cv2.imread(image_path)
        if img is not None:
            data, _, _ = qr_detector.detectAndDecode(img)
            if data and data.strip():
                return data.strip()
    except Exception:
        pass

    # 3. pyzbar fallback (if C++ runtime DLLs are available)
    try:
        from pyzbar.pyzbar import decode

        with Image.open(image_path) as pimg:
            barcodes = decode(pimg)
            if barcodes:
                return barcodes[0].data.decode("utf-8")
    except Exception:
        pass

    return None

