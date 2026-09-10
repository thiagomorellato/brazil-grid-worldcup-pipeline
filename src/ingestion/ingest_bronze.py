"""Ingest ONS Energy Balance into partitioned Bronze Parquet layer."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import uuid
from datetime import datetime, timezone
import shutil
import pandas as pd
from src.config import RAW_ONS_FILE, BRONZE_DIR
from src.ingestion.download_ons import download_ons_dataset

def ingest_to_bronze():
    raw_file = download_ons_dataset()
    print("[INFO] Loading ONS 2022 CSV into memory...")
    df = pd.read_csv(raw_file, sep=";")
    total_records = len(df)
    
    # Parse timestamp
    df["timestamp"] = pd.to_datetime(df["din_instante"])
    
    # Filter for World Cup observation window: Nov 1 to Dec 31, 2022
    # This covers all baselines, pre-tournament, and the entire tournament
    df = df[(df["timestamp"] >= "2022-11-01") & (df["timestamp"] <= "2022-12-31 23:00:00")].copy()
    
    # Metadata
    ingested_at = datetime.now(timezone.utc)
    batch_id = str(uuid.uuid4())
    df["meta_ingested_at"] = ingested_at
    df["meta_batch_id"] = batch_id
    df["meta_source_system"] = "ONS_DADOS_ABERTOS_AWS"
    
    # Clean partition directory before write to prevent duplicate files
    if BRONZE_DIR.exists():
        shutil.rmtree(BRONZE_DIR)
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"[INFO] Writing {len(df):,} records partitioned by id_subsistema into Bronze...")
    df.to_parquet(
        BRONZE_DIR,
        partition_cols=["id_subsistema"],
        index=False,
        compression="snappy"
    )
    print(f"[SUCCESS] Bronze layer successfully written to: {BRONZE_DIR}")
    return len(df)

if __name__ == "__main__":
    ingest_to_bronze()
