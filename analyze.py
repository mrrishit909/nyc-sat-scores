"""Steps 3-4: who scores highest, how boroughs compare, and how much school poverty explains.

    ./venv/bin/python analyze.py
        -> results/top10.csv  math_640.csv  borough.csv  poverty.json  poverty_quartiles.csv
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

HERE = Path(__file__).parent
R = HERE / "results"


def ols(d, with_borough):
    """Total SAT on school poverty (per 10 points of free-or-reduced-price lunch), optionally with borough dummies; robust (HC3) intervals."""
    X = pd.DataFrame({"poverty_per10": d["poverty_pct"] / 10})
    if with_borough:
        X = X.join(pd.get_dummies(d["borough"], drop_first=True, dtype=float))
    r = sm.OLS(d["total"], sm.add_constant(X)).fit(cov_type="HC3")
    lo, hi = r.conf_int().loc["poverty_per10"]
    return {"n": int(r.nobs), "slope_per10": float(r.params["poverty_per10"]), "slope_lo": float(lo), "slope_hi": float(hi), "r2": float(r.rsquared)}


def main():
    m = pd.read_csv(R / "schools.csv")
    s = m[m["total"].notna()].copy()

    # Step 3: the best schools, and the strict "80% of the maximum math score" bar
    top = s.nlargest(10, "total")[["school", "borough", "takers", "math", "total", "poverty_pct"]]
    top.to_csv(R / "top10.csv", index=False)
    s[s["math"] >= 0.8 * 800].sort_values("math", ascending=False)[["school", "borough", "takers", "math", "total"]].to_csv(R / "math_640.csv", index=False)

    # by borough: the plain average of school averages, the student-weighted average, and the spread
    g = s.groupby("borough")
    b = pd.DataFrame({"schools": g.size(), "takers": g["takers"].sum(), "mean_total": g["total"].mean(), "median_total": g["total"].median(),
                      "std_total": g["total"].std(), "min_total": g["total"].min(), "max_total": g["total"].max(),
                      "weighted_mean_total": g.apply(lambda d: np.average(d["total"], weights=d["takers"]), include_groups=False)}).round(1)
    b.loc["All"] = [len(s), s["takers"].sum(), s["total"].mean(), s["total"].median(), s["total"].std(), s["total"].min(), s["total"].max(), np.average(s["total"], weights=s["takers"])]
    b.round(1).reset_index().to_csv(R / "borough.csv", index=False)

    # Step 4: school poverty against the score (scored schools that have a demographics row)
    p = s[s["poverty_pct"].notna()].copy()
    out = {"schools": len(p), "pearson_r": float(stats.pearsonr(p["poverty_pct"], p["total"])[0]), "spearman_rho": float(stats.spearmanr(p["poverty_pct"], p["total"])[0]),
           "simple": ols(p, False), "with_borough": ols(p, True), "without_top10": ols(p[~p["dbn"].isin(s.nlargest(10, "total")["dbn"])], False)}
    json.dump(out, open(R / "poverty.json", "w"), indent=2)
    p["quartile"] = pd.qcut(p["poverty_pct"], 4, labels=["lowest poverty", "second", "third", "highest poverty"])
    q = p.groupby("quartile", observed=True).apply(lambda d: pd.Series({"schools": len(d), "takers": d["takers"].sum(), "poverty_from": d["poverty_pct"].min(), "poverty_to": d["poverty_pct"].max(),
                                                                       "mean_total": d["total"].mean(), "weighted_mean_total": np.average(d["total"], weights=d["takers"])}), include_groups=False).round(1)
    q.reset_index().to_csv(R / "poverty_quartiles.csv", index=False)

    print(top.to_string(index=False)); print(pd.read_csv(R / "math_640.csv").to_string(index=False)); print(b.to_string()); print(json.dumps(out, indent=1)); print(q.to_string())


if __name__ == "__main__":
    main()
