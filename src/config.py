"""Configuration, paths, and FIFA World Cup 2022 match metadata."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

BASE_DIR = _ROOT
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"

# ONS AWS Open Data URLs (Hourly Generation & Load Balance for 2021 and 2022)
ONS_BALANCE_2021_URL = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/balanco_energia_subsistema_ho/BALANCO_ENERGIA_SUBSISTEMA_2021.csv"
ONS_BALANCE_2022_URL = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/balanco_energia_subsistema_ho/BALANCO_ENERGIA_SUBSISTEMA_2022.csv"

RAW_ONS_2021_FILE = RAW_DIR / "ons_balanco_energia_2021.csv"
RAW_ONS_2022_FILE = RAW_DIR / "ons_balanco_energia_2022.csv"

# FIFA World Cup 2022 Qatar - Brazil Matches vs. Previous Year (2021) Baseline Weekdays
# Comparing with the identical weekday of the previous non-World Cup year
BRAZIL_MATCHES = [
    {
        "match_id": "WC2022_G1",
        "opponent": "Serbia",
        "stage": "Group Stage (Match 1)",
        "date": "2022-11-24",  # Thursday
        "kickoff_hour": 16,
        "end_hour": 18,
        "result": "Brazil 2 x 0 Serbia",
        "baseline_date": "2021-11-25"  # Same Thursday in 2021
    },
    {
        "match_id": "WC2022_G2",
        "opponent": "Switzerland",
        "stage": "Group Stage (Match 2)",
        "date": "2022-11-28",  # Monday
        "kickoff_hour": 13,
        "end_hour": 15,
        "result": "Brazil 1 x 0 Switzerland",
        "baseline_date": "2021-11-29"  # Same Monday in 2021
    },
    {
        "match_id": "WC2022_G3",
        "opponent": "Cameroon",
        "stage": "Group Stage (Match 3)",
        "date": "2022-12-02",  # Friday
        "kickoff_hour": 16,
        "end_hour": 18,
        "result": "Cameroon 1 x 0 Brazil",
        "baseline_date": "2021-12-03"  # Same Friday in 2021
    },
    {
        "match_id": "WC2022_R16",
        "opponent": "South Korea",
        "stage": "Round of 16",
        "date": "2022-12-05",  # Monday
        "kickoff_hour": 16,
        "end_hour": 18,
        "result": "Brazil 4 x 1 South Korea",
        "baseline_date": "2021-12-06"  # Same Monday in 2021
    },
    {
        "match_id": "WC2022_QF",
        "opponent": "Croatia",
        "stage": "Quarter-finals",
        "date": "2022-12-09",  # Friday
        "kickoff_hour": 12,
        "end_hour": 15,
        "result": "Croatia 1 (4) x (2) 1 Brazil",
        "baseline_date": "2021-12-10"  # Same Friday in 2021
    }
]

SUBSYSTEMS = {
    "SIN": "National Interconnected Power System (Brazil total)",
    "SE": "Southeast / Central-West (Industrial heartland)",
    "S": "South (Hydropower & Industrial)",
    "NE": "Northeast (Wind & Solar hub)",
    "N": "North (Amazon Hydropower)"
}
