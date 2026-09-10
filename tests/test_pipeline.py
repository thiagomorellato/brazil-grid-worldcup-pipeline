"""Automated data quality and consistency tests for ONS World Cup Pipeline."""
import pytest
import pandas as pd
from src.config import SILVER_DIR, GOLD_DIR

def test_silver_file_exists():
    silver_file = SILVER_DIR / "grid_silver.parquet"
    assert silver_file.exists(), "Silver parquet file must exist"

def test_silver_columns_and_subsystems():
    silver_file = SILVER_DIR / "grid_silver.parquet"
    df = pd.read_parquet(silver_file)
    
    subsystems = df["id_subsistema"].unique()
    assert "SIN" in subsystems, "SIN must be present"
    assert "SE" in subsystems, "SE must be present"
    assert "S" in subsystems, "S must be present"
    
    assert "load_mw" in df.columns
    assert "hydro_gen_mw" in df.columns
    assert "thermal_gen_mw" in df.columns
    assert "is_match_day" in df.columns

def test_gold_match_impact_integrity():
    summary_file = GOLD_DIR / "gold_match_impact_summary.parquet"
    assert summary_file.exists(), "Gold summary file must exist"
    df = pd.read_parquet(summary_file)
    
    assert len(df) == 5, "Must contain all 5 Brazil 2022 World Cup matches"
    assert (df["max_load_drop_mw"] > 5000).all(), "All Brazil matches must show at least 5000 MW drop"
    assert (df["post_match_ramp_2h_mw"] > 0).all(), "Post-match ramp must be positive"

def test_gold_hourly_comparison_integrity():
    hourly_file = GOLD_DIR / "gold_match_hourly_comparison.parquet"
    assert hourly_file.exists(), "Gold hourly file must exist"
    df = pd.read_parquet(hourly_file)
    
    # Must have both baseline column variants for seamless compatibility
    assert "load_mw_baseline_2021" in df.columns or "load_mw_baseline" in df.columns
    assert "load_mw" in df.columns
    assert "id_subsistema" in df.columns
    assert "match_id" in df.columns
    assert len(df) == 600, "Must contain 5 matches * 5 subsystems * 24 hours = 600 rows"
