"""Quick diagnostic to test OCR and field extraction on an uploaded image."""
import sys, os, glob

# Load .env
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ocr_service import run_ocr
from app.services.field_extractor import extract_all_fields

# Check if API key is set
api_key = os.environ.get("GOOGLE_VISION_API_KEY", "")
print(f"Google Vision API Key: {'SET (' + api_key[:10] + '...)' if api_key else 'NOT SET'}")
print()

# Find the most recently uploaded image
upload_dir = "uploads"
if os.path.exists(upload_dir):
    images = glob.glob(os.path.join(upload_dir, "*.*"))
    if images:
        latest = max(images, key=os.path.getmtime)
        print(f"Testing with: {latest}")
        print("=" * 60)
        
        # Run OCR
        result = run_ocr(latest)
        print(f"OCR Engine: {result.get('engine', 'unknown')}")
        if result.get("error"):
            print(f"OCR ERROR: {result['error']}")
        
        raw_text = result.get("text", "")
        print(f"\nRaw OCR Text ({len(raw_text)} chars):")
        print("-" * 40)
        print(raw_text[:3000] if raw_text else "(EMPTY - NO TEXT EXTRACTED)")
        print("-" * 40)
        
        # Run field extraction
        fields = extract_all_fields(raw_text)
        print(f"\nExtracted Fields ({len(fields)} found):")
        for key, val in fields.items():
            print(f"  {key}: {val}")
        
        if not fields:
            print("  (NO FIELDS EXTRACTED)")
    else:
        print("No images found in uploads/")
else:
    print("uploads/ directory doesn't exist")
