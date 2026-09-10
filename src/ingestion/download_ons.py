"""Download ONS 2021 and 2022 Energy Balance datasets from AWS Open Data."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import urllib.request
from src.config import ONS_BALANCE_2021_URL, ONS_BALANCE_2022_URL, RAW_ONS_2021_FILE, RAW_ONS_2022_FILE, RAW_DIR

def download_file(url, target_file):
    if target_file.exists():
        size_mb = target_file.stat().st_size / (1024 * 1024)
        print(f"[INFO] File already exists: {target_file.name} ({size_mb:.2f} MB)")
        return target_file
        
    print(f"[INFO] Downloading: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp, open(target_file, "wb") as f:
        f.write(resp.read())
        
    size_mb = target_file.stat().st_size / (1024 * 1024)
    print(f"[SUCCESS] Downloaded: {target_file.name} ({size_mb:.2f} MB)")
    return target_file

def download_all_ons():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    download_file(ONS_BALANCE_2021_URL, RAW_ONS_2021_FILE)
    download_file(ONS_BALANCE_2022_URL, RAW_ONS_2022_FILE)
    return RAW_ONS_2021_FILE, RAW_ONS_2022_FILE

if __name__ == "__main__":
    download_all_ons()
