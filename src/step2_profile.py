""" STEP 2: PROFILE THE COLUMNS WE ARE ABOUT TO FILTER ON
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_parquet(ROOT / "data" / "processed" / "lca_raw.parquet")

print(f"Loaded {len(df):,} rows\n")


def show(title, series, n=None):
    print("="*60)
    print(title)
    print("=" * 60)
    counts = series.value_counts(dropna=False)
    print(counts.head(n)if n else counts)
    print()

    # 1. what outcomes exist? Determins which rows represent a real
    # wage committment versus an abandoned or rejected application.

show("CASE_STATUS", df["CASE_STATUS"])

# 2. this file covers H-1B, H-1B1 and E-3. We only want H-1B
show("VISA_CLASS", df["VISA_CLASS"])

# 3. confirm the actual time window rather than assuming Q3 means
# october through june. Every headline number is a count over
# this window, so it has to be stated correctly.

dates = pd.to_datetime(df["RECEIVED_DATE"], errors="coerce")
print("=" * 60)
print("RECEIVED_DATE range")
print("=" * 60)
print(f"Earliest: {dates.min()}")
print(f"Latest: {dates.max()}")
print(f"Unparseable dates: {dates.isna().sum():,}\n")

#4. wages are meaningless without knowing the pay period. 
# these are the exact strings we will have to convert to annual.
show("WAGE_UNIT_OF_PAY", df["WAGE_UNIT_OF_PAY"])

#5 where Virginia ranks, and how big the VA slice is.
show("Top 15 WORKSITE_STATE", df["WORKSITE_STATE"], n=15)

#6 the important one. County spelling in this field is inconsistent, so we need the real strings
# before we can match Northern Virginia

va = df[df["WORKSITE_STATE"].astype(str).str.strip().str.upper() == "VA"]
print(f"Virginia rows: {len(va):,}\n")
show("Top 25 Virginia WORKSITE_COUNTY", va["WORKSITE_COUNTY"], n =25)

                    