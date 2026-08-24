"""STEP 4: ANNUALIZE WAGES SO THEY CAN BE COMPARED TO EACH OTHER.
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
df = pd.read_parquet(PROCESSED / "nova_h1b.parquet")

print(f"Starting with {len(df):,} Northern Virgnia records\n")



MULTIPLIERS = {
    "YEAR": 1,
    "MONTH": 12,
    "BI_WEEKLY": 26,
    "WEEK": 52,
    "HOUR": 2080,
}

def annualize(amount, unit):
    """Convert a pay rate to an annual figure
    Amounts arrive as text with commas and stray symbols. Anything
    that will not parse becomes NaN rather than a silently wrong number, because wrong wage
    is worse than a missing one."""

    cleaned = (
        amount.astype(str)
        .str.replace(r"[^0-9.]", "", regex=True)
        .replace("", None)
    )
    numeric = pd.to_numeric(cleaned, errors="coerce")
    multiplier = unit.astype(str).str.strip().str.upper().map(MULTIPLIERS)
    return numeric * multiplier

raw = pd.to_numeric(
    df["WAGE_RATE_OF_PAY_FROM"].astype(str).str.replace(r"[^0-9.]", "", regex=True),
    errors="coerce",

)



df["ANNUAL_WAGE"] = annualize(df["WAGE_RATE_OF_PAY_FROM"], df["WAGE_UNIT_OF_PAY"])
df["ANNUAL_PREVAILING_WAGE"] = annualize(df["PREVAILING_WAGE"], df["PW_UNIT_OF_PAY"])

df["POSITIONS"] = (
    pd.to_numeric(df["TOTAL_WORKER_POSITIONS"], errors="coerce").fillna(1).clip(lower=1)

)

print("Pay units present in Northern Virginia:")
print(df["WAGE_UNIT_OF_PAY"].value_counts(), "\n")

non_annual = df["WAGE_UNIT_OF_PAY"].str.upper() != "YEAR"
print(f"Records needing conversion: {non_annual.sum():,} "
      f"({100 * non_annual.mean():.1f}%)")
print(f"  Median Value as stored:  ${raw[non_annual].median():>12,.0f}")
print(f"  Median once annualized:  ${df.loc[non_annual, 'ANNUAL_WAGE'].median():>12,.0f}\n")

#Validate. Below rougly the federal minimum wage or above $2M is a data entry error, not a real offer.


missing = df["ANNUAL_WAGE"].isna()
implausible = (df["ANNUAL_WAGE"]< 15_000) | (df["ANNUAL_WAGE"]> 2_000_000)

print(f"Failed to parse: {missing.sum():,}")
print(f"Implausible:   {implausible.sum():,}")
if implausible.sum():
    print("\nImplausible examples:")
    print(
        df.loc[implausible, ["EMPLOYER_NAME", "WAGE_RATE_OF_PAY_FROM",
                            "WAGE_UNIT_OF_PAY", "ANNUAL_WAGE"] ].head(10)
        .to_string(index=False)
    )

df.loc[implausible, "ANNUAL_WAGE"] =pd.NA
excluded = int(missing.sum() + implausible.sum())
print(f"\nExcluded from wage analysis: {excluded:,} "
      f"({100 * excluded / len (df):.2f}%)")


df["WAGE_PREMIUM_PCT"] = (
    100* (df["ANNUAL_WAGE"] - df["ANNUAL_PREVAILING_WAGE"])
    / df["ANNUAL_PREVAILING_WAGE"]
)

print("\n" + "=" * 55)
print(f"Usable wage records:       {df['ANNUAL_WAGE'].notna().sum():,}")
print(f"Median annual wage:        ${df['ANNUAL_WAGE'].median():,.0f}")
print(f"25th percentile:           ${df['ANNUAL_WAGE'].quantile(0.25):,.0f}")
print(f"75th percentile:           ${df['ANNUAL_WAGE'].quantile(0.75):,.0f}")
print(f"Median premium over prevailing wage: {df['WAGE_PREMIUM_PCT'].median():.1f}%")
print("=" * 55)


out = PROCESSED / "analysis_ready.parquet"
df.to_parquet(out, index=False)
print(f"\nSaved to {out.relative_to(ROOT)}")

