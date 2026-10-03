"""Step 6: charts.   ./venv/bin/python charts.py -> charts/00_cover.png, 01_top10.png, 02_poverty.png, 03_borough.png, 04_quartiles.png"""
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
R = HERE / "results"
INK, DIM, GRID, BG, BLUE, ORANGE, GRAY, GREEN = "#f2f2f0", "#8a8a87", "#1d1d1d", "#0b0b0b", "#3987e5", "#d95926", "#9a9a96", "#3aa876"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "text.color": INK,
                     "axes.edgecolor": "#3a3a3a", "axes.labelcolor": DIM, "xtick.color": DIM, "ytick.color": DIM,
                     "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 1,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 11, "axes.titlesize": 13,
                     "axes.titlelocation": "left", "axes.titlepad": 12})


def save(fig, name):
    fig.tight_layout(); fig.savefig(HERE / "charts" / name, dpi=150); plt.close(fig)


def short(name):
    return textwrap.fill(name.title().replace("High School", "HS").replace("Technical", "Tech").replace(" And ", " and ").replace(" For ", " for ").replace(" At ", " at ").replace(" The ", " the ").replace(" Of ", " of "), 34)


def poverty(ax):
    s = pd.read_csv(R / "schools.csv"); s = s[s["total"].notna() & s["poverty_pct"].notna()]; out = json.load(open(R / "poverty.json"))
    top = set(pd.read_csv(R / "top10.csv")["school"])
    is_top = s["school"].isin(top)
    ax.scatter(s.loc[~is_top, "poverty_pct"], s.loc[~is_top, "total"], s=s.loc[~is_top, "takers"] / 5 + 8, color=BLUE, alpha=0.65, linewidths=0)
    ax.scatter(s.loc[is_top, "poverty_pct"], s.loc[is_top, "total"], s=s.loc[is_top, "takers"] / 5 + 8, color=ORANGE, alpha=0.9, linewidths=0)
    b, a = np.polyfit(s["poverty_pct"], s["total"], 1); xs = np.array([10, 100]); ax.plot(xs, a + b * xs, color=INK, linestyle="--", linewidth=1.2)
    for _, r in s.nlargest(3, "total").iterrows():
        ax.annotate(short(r["school"]).replace("\n", " ").replace("Hs", "HS"), (r["poverty_pct"], r["total"]), (r["poverty_pct"] + 5, r["total"] + 25), color=INK, fontsize=8, arrowprops={"arrowstyle": "-", "color": DIM, "linewidth": 0.6})
    ax.text(99, 2030, f"{out['simple']['slope_per10']:.0f} points per +10 points of poverty\nr = {out['pearson_r']:.2f}; poverty alone explains {100 * out['simple']['r2']:.0f}%", ha="right", va="top", color=INK, fontsize=10)
    ax.set_xlim(10, 102); ax.set_ylim(850, 2150); ax.set_xlabel("% of the school's students eligible for free or reduced-price lunch (2011-12)"); ax.set_ylabel("average SAT total (of 2400)")
    ax.set_title("Poorer schools score lower; the ten top scorers (orange) sit far above the trend")


def quartiles(ax):
    q = pd.read_csv(R / "poverty_quartiles.csv"); x = np.arange(4)
    ax.bar(x, q["mean_total"], color=[GREEN, BLUE, BLUE, ORANGE], width=0.6)
    ax.scatter(x, q["weighted_mean_total"], color=INK, marker="D", s=40, zorder=3, label="weighted by test takers")
    for xi, (_, r) in zip(x, q.iterrows()):
        ax.text(xi, r["mean_total"] - 150, f"{r['mean_total']:,.0f}", ha="center", color=BG, fontsize=11)
    ax.set_xticks(x); ax.set_xticklabels([f"{n}\n{r['poverty_from']:.0f}-{r['poverty_to']:.0f}%\n{int(r['schools'])} schools" for n, (_, r) in zip(["lowest poverty", "second", "third", "highest poverty"], q.iterrows())])
    ax.set_ylim(0, 1600); ax.set_ylabel("average SAT total"); ax.grid(axis="x", visible=False); ax.legend(frameon=False, labelcolor=INK, fontsize=9, loc="upper right")
    ax.set_title("Average SAT by school-poverty quartile")


def main():
    (HERE / "charts").mkdir(exist_ok=True)
    fig, (a, b) = plt.subplots(1, 2, figsize=(14, 8), gridspec_kw={"width_ratios": [1.35, 1]})
    poverty(a); quartiles(b)
    a.set_title("School poverty against SAT score", fontsize=15); b.set_title("Average SAT by school-poverty quartile", fontsize=15)
    fig.suptitle("Which NYC schools post the top SAT scores? 421 schools, 2012", x=0.01, ha="left", fontsize=20, color=INK, y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(HERE / "charts" / "00_cover.png", dpi=100); plt.close(fig)

    t = pd.read_csv(R / "top10.csv"); fig, ax = plt.subplots(figsize=(10, 5.4)); y = np.arange(10)[::-1]
    ax.barh(y, t["total"], color=BLUE, height=0.7)
    for yi, (_, r) in zip(y, t.iterrows()):
        ax.text(r["total"] + 12, yi, f"{r['total']:,.0f}   {int(r['takers']):,} test takers   {r['poverty_pct']:.0f}% free/reduced lunch", va="center", color=INK, fontsize=9)
    ax.set_yticks(y); ax.set_yticklabels([short(n) for n in t["school"]], fontsize=8); ax.set_xlim(0, 3300); ax.set_xlabel("average SAT total (of 2400)"); ax.grid(axis="y", visible=False)
    ax.set_title(f"The ten highest-scoring schools: {int(t['takers'].min())} to {int(t['takers'].max()):,} test takers each, {t['poverty_pct'].min():.0f}% to {t['poverty_pct'].max():.0f}% on free or reduced-price lunch")
    save(fig, "01_top10.png")

    fig, ax = plt.subplots(figsize=(10, 4.4)); poverty(ax); save(fig, "02_poverty.png")

    s = pd.read_csv(R / "schools.csv"); s = s[s["total"].notna()]; b = pd.read_csv(R / "borough.csv").set_index("borough")
    order = list(b.drop("All").sort_values("mean_total").index); rng = np.random.default_rng(0); fig, ax = plt.subplots(figsize=(10, 3.8))
    for i, bo in enumerate(order):
        d = s[s["borough"] == bo]; ax.scatter(i + rng.uniform(-0.28, 0.28, len(d)), d["total"], s=d["takers"] / 12 + 6, color=BLUE, alpha=0.55, linewidths=0)
    ax.scatter(range(5), [b.loc[o, "mean_total"] for o in order], marker="D", color=INK, s=60, zorder=3, label="average of school averages")
    ax.scatter(range(5), [b.loc[o, "weighted_mean_total"] for o in order], marker="D", color=ORANGE, s=60, zorder=3, label="weighted by test takers")
    ax.set_xticks(range(5)); ax.set_xticklabels([f"{o}\n{int(b.loc[o, 'schools'])} schools" for o in order]); ax.set_ylabel("average SAT total"); ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, labelcolor=INK, fontsize=9, loc="upper left"); ax.set_title("By borough: the plain average and the student-weighted average tell different stories")
    save(fig, "03_borough.png")

    fig, ax = plt.subplots(figsize=(10, 3.6)); quartiles(ax); save(fig, "04_quartiles.png")


if __name__ == "__main__":
    main()
