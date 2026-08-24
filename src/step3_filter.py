"""STEP 3: FILTER TO CERTIFIED H-1B RECORDS WITH NORTHERN VIRGINIA WORKSITES"""

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
df = pd.read_parquet(PROCESSED / "lca_raw.parquet")

audit = {"rows_in_file": len(df)}



# 0. resolve which date actually defines this file's coverage

received = pd.to_datetime(df["RECEIVED_DATE"], errors="coerce")
decided = pd.to_datetime(df["DECISION_DATE"], errors="coerce")

print("DECISION_DATE range:", decided.min().date(), "to", decided.max().date())
print("RECEIVED_DATE range:", received.min().date(), "to", received.max().date())
print("\nApplications by year received:")
print(received.dt.year.value_counts().sort_index())
print()

#1. visa class. the file bundles h-1b with e-3 and h-1b1, which
# are separate treaty programs with different rules and purposes.

df = df[df["VISA_CLASS"] == "H-1B"]
audit["h1b"] = len(df)






audit["certified_withdrawn_excluded"] = int(
    (df["CASE_STATUS"] == "Certified - Withdrawn").sum()

)

df = df[df["CASE_STATUS"] == "Certified"]
audit["certified"] = len(df)


#3. Geography. NOVA as defined by the Northern Virginia Regional Commission" Arlington, Fairfax, Loudoun, and Prince William counties
# Plus the independent cities of Alexandria, Fairfax, Falls Church, Manassas and Manassas Park.


NOVA = {
    "ARLINGTON", "FAIRFAX", "LOUDOUN", "PRINCE WILLIAM",
    "ALEXANDRIA", "FALLS CHURCH", "MANASSAS", "MANASSAS PARK",
}
df = df[df["WORKSITE_STATE"].astype(str).str.strip().str.upper() == "VA"]
audit["virginia"] = len(df)

county = (
    df["WORKSITE_COUNTY"].astype(str).str.strip().str.upper()
    .str.replace(r"\s+(COUNTY|CITY)$", "", regex=True)

)
df = df.assign(COUNTY_CLEAN=county)

unmatched = df[~df["COUNTY_CLEAN"].isin(NOVA)]
print("Virginia counties excluded as non-NoVA, top 10: ")
print(unmatched["COUNTY_CLEAN"].value_counts().head(10))
print()

df = df[df["COUNTY_CLEAN"].isin(NOVA)]
audit["northern_virginia"] = len(df)

#Audit Trail

print("=" * 55)
for key, value in audit.items():
    print(f"{key:<32} {value:>10,}")
print("=" * 55)
print("\nRecords by jurisdiction:")
print(df["COUNTY_CLEAN"].value_counts())

out = PROCESSED / "nova_h1b.parquet"
df.to_parquet(out, index=False)
print(f"\nSaved {len(df):,} rows to {out.relative_to(ROOT)}")
