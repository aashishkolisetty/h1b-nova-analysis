

from pathlib import Path
import re
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

df = pd.read_parquet(ROOT / "data" / "processed" / "analysis_ready.parquet")
print(f"Loaded {len(df):,}, records\n")

BAR, INK, MUTED, GRID = "#1F5FBF", "#1a1a1a", "#6b6b6b", "#dcdcdc"
plt.rcParams.update({"font.size": 10, "figure.facecolor": "white", "axes.facecolor": "white" })


SUFFIXES = r"\b(INC|INCORPORATED|LLC|LLP|LP|LTD|LIMITED|CORP|CORPORATION|CO|COMPANY|PLC|PC|PA|GROUP|HOLDINGS|USA|US|NA|NATIONAL ASSOCIATION)\b"


PARENT_RULES = [
    (r"\bAMAZON\b",                              "Amazon"),
    (r"\bAWS\b",                                 "Amazon"),
    (r"\bCAPITAL ONE\b",                         "Capital One"),
    (r"\bFEDERAL HOME LOAN MORTGAGE\b",          "Freddie Mac"),
    (r"\bFREDDIE MAC\b",                         "Freddie Mac"),
    (r"\bFEDERAL NATIONAL MORTGAGE\b",           "Fannie Mae"),
    (r"\bFANNIE MAE\b",                          "Fannie Mae"),
    (r"\bDELOITTE\b",                            "Deloitte"),
    (r"\bACCENTURE\b",                           "Accenture"),
    (r"\bBOOZ ALLEN\b",                          "Booz Allen Hamilton"),
    (r"\bMICROSOFT\b",                           "Microsoft"),
    (r"\bGOOGLE\b",                              "Google"),
    (r"\bMETA PLATFORMS\b",                      "Meta"),
    (r"\bCOGNIZANT\b",                           "Cognizant"),
    (r"\bINFOSYS\b",                             "Infosys"),
    (r"\bTATA CONSULTANCY\b",                    "Tata Consultancy Services"),
    (r"\bWIPRO\b",                               "Wipro"),
    (r"\bHCL\b",                                 "HCL"),
    (r"\bLEIDOS\b",                              "Leidos"),
    (r"\bCGI\b",                                 "CGI"),
    (r"\bERNST\b",                               "Ernst & Young"),
    (r"\bKPMG\b",                                "KPMG"),
    (r"\bPRICEWATERHOUSE\b",                     "PwC"),
    (r"\bGENERAL DYNAMICS\b",                    "General Dynamics"),
    (r"\bNORTHROP GRUMMAN\b",                    "Northrop Grumman"),
]

def normalize(name: str) -> str:
    """Strip punctuation and legal suffixes down to a comparable core."""
    s = str(name).upper()
    s = re.sub(r"[^A-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(SUFFIXES, " ", s)
    return re.sub(r"\s+", " ", s).strip()



def to_parent(name: str) -> str:
    """Map an entity to its parent, or return a cleaned version of itself."""
    core = normalize(name)
    for pattern, parent in PARENT_RULES:
        if re.search(pattern, core):
            return parent
        return str(name).title()


df["PARENT_EMPLOYER"] = df["EMPLOYER_NAME"].map(to_parent)




merges = (
    df.groupby("PARENT_EMPLOYER")
    .agg(entities=("EMPLOYER_NAME", "nunique"),
         positions=("POSITIONS", "sum"))
    .query("entities > 1")
    .sort_values("positions", ascending=False)
    .reset_index()
)

print("Parents assembled from multiple filing entities:")
print(merges.to_string(index=False), "\n")

detail = (
    df[df["PARENT_EMPLOYER"].isin(merges["PARENT_EMPLOYER"])]
    .groupby(["PARENT_EMPLOYER", "EMPLOYER_NAME"])
    .agg(positions=("POSITIONS","sum"))
    .sort_values(["PARENT_EMPLOYER", "positions"], ascending=[True, False])
    .reset_index()
)

detail.to_csv(OUT / "entity_merge_report.csv", index=False)
print(f" wrote entity_merge_report.csv ({len(detail)} entities)\n")


total = df["POSITIONS"].sum()

parents = (
    df.groupby("PARENT_EMPLOYER")
    .agg(certified_positions=("POSITIONS", "sum"),
         filing_entities=("EMPLOYER_NAME", "nunique"),
         applications=("CASE_NUMBER", "count"),
         median_annual_wage=("ANNUAL_WAGE", "median"))
        .sort_values("certified_positions", ascending=False)
        .round(0)
        .reset_index()
        )
parents.to_csv(OUT / "top_parent_employers.csv", index=False)
print("  wrote top_parent_employers.csv")

top = parents.head(12).iloc[::-1]
lab = top["PARENT_EMPLOYER"].str.slice(0, 42)
val = top["certified_positions"]

fig, ax =  plt.subplots(figsize=(9.5, 0.42 * len(top) + 1.9))
bars = ax.barh(lab, val, color=BAR, height=0.62)
for bar, v in zip(bars, val):
    ax.text(bar.get_width() + val.max() * 0.012, 
            bar.get_y() + bar.get_height() / 2,
            f"{v:,.0f}", va="center", ha="left", color=MUTED, fontsize=9)



ax.set_xlim(0, val.max()*1.16)
ax.set_xticks([])
ax.tick_params(axis="y", length=0, colors=INK)
ax.spines[["top", "right", "bottom"]].set_visible(False)
ax.spines["left"].set_color(GRID)
ax.set_title("Amazon drives around 39%  of Northern Virginia's H-1B demand",
             loc="left", fontsize=13, color=INK, pad=30, weight="bold")
ax.text(0, 1.02,
        "Certified positions by parent company, after consolidating filing entities. "
        "Decided Oct 2025 to Jun 2026.",
        transform=ax.transAxes, fontsize=9.5, color=MUTED, va="bottom")
fig.tight_layout()
fig.savefig(OUT / "top_parent_employers.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("  wrote top_parent_employers.png\n")

entity_top10 = (
    df.groupby("EMPLOYER_NAME")["POSITIONS"].sum()
    .sort_values(ascending=False).head(10).sum()
)
parent_top10 = parents.head(10)["certified_positions"].sum()
lead = parents.iloc[0]
 
lines = [
    "# Findings after entity resolution",
    "",
    f"- Filing entities: {df['EMPLOYER_NAME'].nunique():,}",
    f"- Parent companies after consolidation: {df['PARENT_EMPLOYER'].nunique():,}",
    f"- Parents assembled from more than one entity: {len(merges)}",
    "",
    f"- Top 10 concentration, by filing entity:   "
    f"{100 * entity_top10 / total:.1f}%",
    f"- Top 10 concentration, by parent company:  "
    f"{100 * parent_top10 / total:.1f}%",
    "",
    f"- Largest parent: {lead['PARENT_EMPLOYER']} at "
    f"{int(lead['certified_positions']):,} positions, "
    f"{100 * lead['certified_positions'] / total:.1f}% of all certified "
    f"positions in the region, filed across "
    f"{int(lead['filing_entities'])} legal entities.",
]
text = "\n".join(lines)
(OUT / "summary_entities.md").write_text(text + "\n")
print(text)
 
df.to_parquet(ROOT / "data" / "processed" / "analysis_ready.parquet", index=False)
print("\nAdded PARENT_EMPLOYER to analysis_ready.parquet")