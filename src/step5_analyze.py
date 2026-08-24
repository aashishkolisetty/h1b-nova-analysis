"""STEP 5: AGGREGATE THE CLEANED DATA AND RENDER THE CHARTS."""

from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

df = pd.read_parquet(ROOT / "data" / "processed" / "analysis_ready.parquet")


BAR, INK, MUTED, GRID = "#1F5FBF", "#1A1A1A", "#6B6B6B", "#DCDCDC"
plt.rcParams.update({"font.size": 10, "figure.facecolor": "white", "axes.facecolor": "white"})


def barh(frame, labels, values, title, subtitle, fname, fmt="{:,.0f}"):
    """Horizontal bars, largest at top, every bar labeled directly."""

    frame = frame.iloc[::-1]
    lab, val = frame[labels].str.title().str.slice(0, 42), frame[values]

    fig, ax = plt.subplots(figsize=(9.5, 0.42 * len(frame) + 1.9))
    bars = ax.barh(lab, val, color=BAR, height=0.62)

    for bar, v in zip(bars, val):
        ax.text(bar.get_width() + val.max()*0.012, bar.get_y() + bar.get_height()/2, fmt.format(v), va="center", ha="left", color=MUTED, fontsize = 9)

    ax.set_xlim(0, val.max()*1.16)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0, colors=INK)
    ax.spines[["top","right", "bottom"]].set_visible(False)
    ax.spines["left"].set_color(GRID)

    ax.set_title(title, loc="left", fontsize=13, color=INK, pad=18, weight="bold")
    ax.text(0, 1.02, subtitle, transform=ax.transAxes,
            fontsize = 9.5, color=MUTED, va="bottom")

    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f" wrote {fname}")

def hist(series, title, subtitle, xlabel, fname, marker=None, marker_label=""):
    fig, ax = plt.subplots(figsize=(9.5, 5))
    ax.hist(series.dropna(), bins=45, color=BAR, edgecolor="white", linewidth=0.6)

    if marker is not None:
        ax.axvline(marker, color=INK, linewidth=1.4, linestyle="--")
        ax.text(marker, ax.get_ylim()[1]*0.95, f" {marker_label}", 
                color=INK, fontsize=9.5, va="top", ha="left")


    ax.set_xlabel(xlabel, color=MUTED, fontsize=9.5)
    ax.set_ylabel("Applications", color=MUTED, fontsize=9.5)
    ax.tick_params(colors=MUTED, length=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color(GRID)
    ax.grid(axis="y", color=GRID, alpha=0.5, linewidth=0.7)
    ax.set_axisbelow(True)

    ax.set_title(title, loc="left", fontsize=13, color=INK, pad=18, weight="bold")
    ax.text(0, 1.02, subtitle, transform=ax.transAxes,
            fontsize=9.5, color=MUTED, va="bottom")

    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f" wrote {fname}")

employers = (
     df.groupby("EMPLOYER_NAME")
    .agg(certified_positions=("POSITIONS", "sum"),
        applications=("CASE_NUMBER","count"),
        median_annual_wage=("ANNUAL_WAGE","median"))
    .sort_values("certified_positions", ascending=False)
     .round(0)
     .reset_index())

occupations = (
    df.groupby("SOC_TITLE")
    .agg(certified_positions=("POSITIONS","sum"),
        median_annual_wage=("ANNUAL_WAGE","median"),
        median_premium_pct=("WAGE_PREMIUM_PCT", "median"))
        .sort_values("certified_positions", ascending=False)
        .round(1)
        .reset_index()

)

jurisdictions = (
    df.groupby("COUNTY_CLEAN")
    .agg(certified_positions=("POSITIONS", "sum"),
         median_annual_wage=("ANNUAL_WAGE", "median"))
    .sort_values("certified_positions", ascending=False)
    .round(0)
    .reset_index()
)

for name, frame in[("top_employers", employers),
                    ("top_occupations", occupations),
                    ("by_jurisdiction", jurisdictions)]:
    frame.to_csv(OUT / f"{name}.csv", index=False)
    print(f" wrote {name}.csv")



window = "certified applications decided Oct 2025 to Jun 2026"

barh(employers.head(12), "EMPLOYER_NAME", "certified_positions",
         "Northern Virginia H-1B demand concentrates in a handful of employers",
         f"Certified positions by employer, {window}", "top_employers.png")

barh(occupations.head(12), "SOC_TITLE", "certified_positions",
         "Software and systems roles dominate the occupation mix",
         f"Certified positions by occupation, {window}", "top_occupations.png")


hist(df["ANNUAL_WAGE"].clip(upper=300_000),
         "Offered salaries cluster in a narrow band",
         f"Annualized offered wage, {window}. Values above $300k truncated.",
         "Annual wage(USD)", "wage_distribution.png",
        marker=df["ANNUAL_WAGE"].median(),
        marker_label=f"Median ${df['ANNUAL_WAGE'].median():,.0f}")

hist(df["WAGE_PREMIUM_PCT"].clip(lower=-10, upper=60),
         "Employers anchor tightly to the government wage floor",
         f"Offered wage above prevailing wage, {window}. Clipped to -10% and 60%.",
         "Premium over prevailing wage (%)", "wage_premium.png",
        marker=df["WAGE_PREMIUM_PCT"].median(),
        marker_label=f"Median {df['WAGE_PREMIUM_PCT'].median():.1f}%")



top_occ = occupations.iloc[0]
total_positions = df["POSITIONS"].sum()

lines = [
     "# Findings",
     "",
    f"Scope: certified H-1B applications with Northern Virginia worksites,",
    f"decided between 2025-10-01 and 2026-06-30.",
    "",
    f"- Applications analyzed: {len(df):,}",
    f"- Certified positions requested: {int(df['POSITIONS'].sum()):,}",
    f"- Distinct employers: {df['EMPLOYER_NAME'].nunique():,}",
    f"- Distinct occupations: {df['SOC_TITLE'].nunique():,}",
    "",
    f"- Median annual wage: ${df['ANNUAL_WAGE'].median():,.0f}",
    f"- Median premium over prevailing wage: {df['WAGE_PREMIUM_PCT'].median():.1f}%",
    "",
    f"- Top employer: {employers.iloc[0]['EMPLOYER_NAME'].title()} "
    f"({int(employers.iloc[0]['certified_positions']):,} positions)",
    f"- Top 10 employers account for "
    f"{100 * employers.head(10)['certified_positions'].sum() / df['POSITIONS'].sum():.1f}% "
    "of all certified positions",
    f"- Top occupation: {top_occ['SOC_TITLE'].title()} "
    f"({100 * top_occ['certified_positions'] / df['POSITIONS'].sum():.1f}% of positions)",
    f"- Fairfax share of applications: "
    f"{100 * (df['COUNTY_CLEAN'] == 'FAIRFAX').mean():.1f}%",
    ]

text = "\n".join(lines)
(OUT / "summary.md").write_text(text + "\n")
print("\n" + text)


    
    
