"""Ingest ONS 2021 and 2022 Energy Balance datasets into Bronze Parquet."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import uuid
from datetime import datetime, timezone
import shutil
import pandas as pd
from src.config import RAW_ONS_2021_FILE, RAW_ONS_2022_FILE, BRONZE_DIR
from src.ingestion.download_ons import download_all_ons

def ingest_to_bronze():
    download_all_ons()
    print("[INFO] Ingesting 2021 (baseline year) and 2022 (World Cup year) datasets...")
    
    df21 = pd.read_csv(RAW_ONS_2021_FILE, sep=";")
    df22 = pd.read_csv(RAW_ONS_2022_FILE, sep=";")
    
    df21["timestamp"] = pd.to_datetime(df21["din_instante"])
    df22["timestamp"] = pd.to_datetime(df22["din_instante"])
    
    # Filter observation windows: Nov 1 to Dec 31 for both years
    df21 = df21[(df21["timestamp"] >= "2021-11-01") & (df21["timestamp"] <= "2021-12-31 23:00:00")].copy()
    df22 = df22[(df22["timestamp"] >= "2022-11-01") & (df22["timestamp"] <= "2022-12-31 23:00:00")].copy()
    
    combined = pd.concat([df21, df22], ignore_index=True)
    
    combined["meta_ingested_at"] = datetime.now(timezone.utc)
    combined["meta_batch_id"] = str(uuid.uuid4())
    combined["meta_source_system"] = "ONS_DADOS_ABERTOS_AWS"
    
    if BRONZE_DIR.exists():
        shutil.rmtree(BRONZE_DIR)
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"[INFO] Writing {len(combined):,} combined records partitioned by id_subsistema to Bronze...")
    combined.to_parquet(
        BRONZE_DIR,
        partition_cols=["id_subsistema"],
        index=False,
        compression="snappy"
    )
    print(f"[SUCCESS] Bronze layer written: {BRONZE_DIR}")
    return len(combined)

if __name__ == "__main__":
    ingest_to_bronze()
