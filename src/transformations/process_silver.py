"""Process Bronze Parquet into cleaned, typed and World Cup-enriched Silver layer."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import shutil
import pandas as pd
from src.config import BRONZE_DIR, SILVER_DIR, BRAZIL_MATCHES, SUBSYSTEMS

def process_to_silver():
    print("[INFO] Reading Bronze layer partitions...")
    df = pd.read_parquet(BRONZE_DIR)
    
    # Standardize column naming
    rename_cols = {
        "val_carga": "load_mw",
        "val_gerhidraulica": "hydro_gen_mw",
        "val_gertermica": "thermal_gen_mw",
        "val_gereolica": "wind_gen_mw",
        "val_gersolar": "solar_gen_mw",
        "val_intercambio": "interchange_mw"
    }
    df = df.rename(columns=rename_cols)
    
    # Ensure numeric types
    metric_cols = ["load_mw", "hydro_gen_mw", "thermal_gen_mw", "wind_gen_mw", "solar_gen_mw", "interchange_mw"]
    for col in metric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
            
    df["total_generation_mw"] = (
        df["hydro_gen_mw"] + df["thermal_gen_mw"] + df["wind_gen_mw"] + df["solar_gen_mw"]
    )
    
    # Date & Hour helpers
    df["date"] = df["timestamp"].dt.strftime("%Y-%m-%d")
    df["hour"] = df["timestamp"].dt.hour
    
    # Enrich with Brazil World Cup Match schedule
    df["is_match_day"] = False
    df["is_match_hour"] = False
    df["match_id"] = None
    df["match_stage"] = None
    df["match_opponent"] = None
    
    for match in BRAZIL_MATCHES:
        m_date = match["date"]
        k_hour = match["kickoff_hour"]
        e_hour = match["end_hour"]
        
        mask_day = df["date"] == m_date
        df.loc[mask_day, "is_match_day"] = True
        df.loc[mask_day, "match_id"] = match["match_id"]
        df.loc[mask_day, "match_stage"] = match["stage"]
        df.loc[mask_day, "match_opponent"] = match["opponent"]
        
        mask_hour = mask_day & (df["hour"] >= k_hour) & (df["hour"] <= e_hour)
        df.loc[mask_hour, "is_match_hour"] = True

    if SILVER_DIR.exists():
        shutil.rmtree(SILVER_DIR)
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    
    out_file = SILVER_DIR / "grid_silver.parquet"
    df.to_parquet(out_file, index=False, compression="snappy")
    print(f"[SUCCESS] Silver layer written: {out_file} ({len(df):,} records)")
    return df

if __name__ == "__main__":
    process_to_silver()
