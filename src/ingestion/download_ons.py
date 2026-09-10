"""Download ONS 2022 Energy Balance dataset from AWS Open Data."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import urllib.request
from src.config import ONS_BALANCE_2022_URL, RAW_ONS_FILE, RAW_DIR

def download_ons_dataset():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if RAW_ONS_FILE.exists():
        size_mb = RAW_ONS_FILE.stat().st_size / (1024 * 1024)
        print(f"[INFO] ONS dataset already present at: {RAW_ONS_FILE} ({size_mb:.2f} MB)")
        return RAW_ONS_FILE
    
    print(f"[INFO] Downloading ONS 2022 energy balance from: {ONS_BALANCE_2022_URL}")
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(ONS_BALANCE_2022_URL, headers=headers)
    with urllib.request.urlopen(req) as resp, open(RAW_ONS_FILE, "wb") as f:
        f.write(resp.read())
    
    size_mb = RAW_ONS_FILE.stat().st_size / (1024 * 1024)
    print(f"[SUCCESS] Download completed: {RAW_ONS_FILE} ({size_mb:.2f} MB)")
    return RAW_ONS_FILE

if __name__ == "__main__":
    download_ons_dataset()
