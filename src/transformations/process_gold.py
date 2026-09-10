"""Build Gold analytical tables comparing Brazil match days (2022) against 2021 baselines."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import shutil
import pandas as pd
from src.config import SILVER_DIR, GOLD_DIR, BRAZIL_MATCHES

def process_to_gold():
    silver_file = SILVER_DIR / "grid_silver.parquet"
    print(f"[INFO] Reading Silver layer from: {silver_file}")
    df = pd.read_parquet(silver_file)
    
    if GOLD_DIR.exists():
        shutil.rmtree(GOLD_DIR)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    
    comparison_rows = []
    for match in BRAZIL_MATCHES:
        m_id = match["match_id"]
        m_date = match["date"]
        b_date = match["baseline_date"]  # 2021 same weekday
        opponent = match["opponent"]
        stage = match["stage"]
        kickoff = match["kickoff_hour"]
        
        for sub in df["id_subsistema"].unique():
            match_slice = df[(df["id_subsistema"] == sub) & (df["date"] == m_date)].sort_values("hour")
            base_slice = df[(df["id_subsistema"] == sub) & (df["date"] == b_date)].sort_values("hour")
            
            merged = pd.merge(
                match_slice[["hour", "load_mw", "hydro_gen_mw", "thermal_gen_mw", "wind_gen_mw", "solar_gen_mw"]],
                base_slice[["hour", "load_mw", "hydro_gen_mw", "thermal_gen_mw"]],
                on="hour",
                suffixes=("", "_baseline_2021")
            )
            
            merged["match_id"] = m_id
            merged["opponent"] = opponent
            merged["stage"] = stage
            merged["match_date"] = m_date
            merged["baseline_date"] = b_date
            merged["baseline_date_2021"] = b_date
            merged["kickoff_hour"] = kickoff
            merged["id_subsistema"] = sub
            merged["load_drop_mw"] = merged["load_mw_baseline_2021"] - merged["load_mw"]
            merged["load_drop_pct"] = (merged["load_drop_mw"] / merged["load_mw_baseline_2021"] * 100).round(2)
            
            # Backwards and forwards compatibility for baseline load column
            merged["load_mw_baseline"] = merged["load_mw_baseline_2021"]
            
            comparison_rows.append(merged)
            
    gold_hourly_comp = pd.concat(comparison_rows, ignore_index=True)
    comp_file = GOLD_DIR / "gold_match_hourly_comparison.parquet"
    gold_hourly_comp.to_parquet(comp_file, index=False, compression="snappy")
    print(f"[SUCCESS] Gold Hourly Comparison written: {comp_file} ({len(gold_hourly_comp):,} records)")
    
    # Match Summary Table
    sin_comp = gold_hourly_comp[gold_hourly_comp["id_subsistema"] == "SIN"]
    match_summaries = []
    for match in BRAZIL_MATCHES:
        m_id = match["match_id"]
        m_df = sin_comp[sin_comp["match_id"] == m_id]
        
        k_hour = match["kickoff_hour"]
        end_hour = match["end_hour"]
        during_match = m_df[(m_df["hour"] >= k_hour) & (m_df["hour"] <= end_hour)]
        
        max_drop_row = during_match.loc[during_match["load_drop_mw"].idxmax()]
        
        post_hour = min(23, end_hour + 2)
        load_end = m_df[m_df["hour"] == end_hour]["load_mw"].values[0] if len(m_df[m_df["hour"] == end_hour]) else 0
        load_post = m_df[m_df["hour"] == post_hour]["load_mw"].values[0] if len(m_df[m_df["hour"] == post_hour]) else 0
        ramp_up_mw = load_post - load_end
        
        match_summaries.append({
            "match_id": m_id,
            "stage": match["stage"],
            "opponent": match["opponent"],
            "match_date": match["date"],
            "kickoff_time": f"{match['kickoff_hour']}:00 BRT",
            "result": match["result"],
            "baseline_date_2021": match["baseline_date"],
            "baseline_date": match["baseline_date"],
            "baseline_load_mw": max_drop_row["load_mw_baseline_2021"],
            "match_load_mw": max_drop_row["load_mw"],
            "max_load_drop_mw": max_drop_row["load_drop_mw"],
            "max_load_drop_pct": max_drop_row["load_drop_pct"],
            "peak_drop_hour": f"{max_drop_row['hour']}:00 BRT",
            "post_match_ramp_2h_mw": ramp_up_mw
        })
        
    gold_summary = pd.DataFrame(match_summaries)
    summary_file = GOLD_DIR / "gold_match_impact_summary.parquet"
    gold_summary.to_parquet(summary_file, index=False, compression="snappy")
    print(f"[SUCCESS] Gold Match Impact Summary written: {summary_file} ({len(gold_summary)} matches)")
    
    return gold_hourly_comp, gold_summary

if __name__ == "__main__":
    process_to_gold()
