"""Debug the Vision API 403 error."""
import httpx, base64, json, os
from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get("GOOGLE_VISION_API_KEY", "")
print(f"API Key: {api_key[:15]}...")

# Send a minimal test request
url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"

# Use a tiny 1x1 pixel PNG
import struct, zlib
def make_tiny_png():
    raw = b'\x00\xff\xff\xff'
    compressed = zlib.compress(raw)
    ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', compressed) + chunk(b'IEND', b'')

img_bytes = make_tiny_png()
content = base64.b64encode(img_bytes).decode()

payload = {
    "requests": [{
        "image": {"content": content},
        "features": [{"type": "TEXT_DETECTION"}]
    }]
}

resp = httpx.post(url, json=payload, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)[:2000]}")
