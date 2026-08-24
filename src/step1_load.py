from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/ "data"/ "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

matches = [
    p for p in RAW.glob("*.xlsx")
    if "closure" in p.name.lower()
    and "worksite" not in p.name.lower()
    and "appendix" not in p.name.lower()

]

if not matches:
    raise SystemExit(f"No disclosure file found in {RAW}")
if len(matches) > 1:
    raise SystemExit(f"Multiple candidates, expected one: {[p.name for p in matches]}")


source = matches[0]
print(f"Reading {source.name}")
print("This is a large Excel file. Expect several minutes and high memory use.\n")



df = pd.read_excel(source, dtype=str)


print(f"Rows:    {df.shape[0]:,}")
print(f"Columns:    {df.shape[1]}\n")
print("Column names:")
for i, col in enumerate(df.columns, 1):
    print(f"   {i:>3}. {col}")


cache = PROCESSED / "lca_raw.parquet"
df.to_parquet(cache, index=False)
print(f"\nCached to {cache.relative_to(ROOT)}")
print("Every later step loads from this in seconds.")