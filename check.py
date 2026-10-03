"""Step 5: the project's check. Rebuild every result from the two raw downloads with plain Python (csv, statistics, math, numpy for the
matrix algebra; no pandas, no statsmodels, nothing from clean.py or analyze.py) and require it to equal what results/ holds.

    ./venv/bin/python check.py
"""
import csv
import json
import math
import statistics
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
R = HERE / "results"
BOROUGH = {"M": "Manhattan", "K": "Brooklyn", "X": "Bronx", "Q": "Queens", "R": "Staten Island"}
Z = 1.959963984540054
n_ok = 0


def close(label, got, want, tol=1e-6):
    global n_ok
    n_ok += 1
    assert abs(float(got) - float(want)) <= tol * max(1.0, abs(float(want))), f"{label}: recount {got} != results {want}"


def table(name):
    return list(csv.DictReader(open(R / name)))


def percentile(xs, q):
    """linear interpolation between order statistics, as numpy and pandas do by default"""
    xs = sorted(xs)
    pos = (len(xs) - 1) * q / 100
    lo = math.floor(pos)
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (pos - lo)


def ranks(xs):
    """average ranks for ties"""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out, i = [0.0] * len(xs), 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return out


def pearson(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))


def ols_hc3(X, y):
    """slope CI with HC3 robust errors; X includes the constant in column 0, the slope of interest in column 1"""
    X, y = np.array(X, float), np.array(y, float)
    inv = np.linalg.inv(X.T @ X)
    beta = inv @ X.T @ y
    e = y - X @ beta
    h = np.einsum("ij,jk,ik->i", X, inv, X)
    cov = inv @ (X.T * (e / (1 - h)) ** 2) @ X @ inv
    se = math.sqrt(cov[1, 1])
    r2 = 1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return beta[1], beta[1] - Z * se, beta[1] + Z * se, r2


def main():
    sat = list(csv.DictReader(open(HERE / "data" / "sat.csv")))
    demo = {r["dbn"]: r for r in csv.DictReader(open(HERE / "data" / "demographics.csv"))}
    rows = []                                                      # scored schools
    for r in sat:
        if r["sat_math_avg_score"] == "s":
            continue
        t = int(r["sat_critical_reading_avg_score"]) + int(r["sat_math_avg_score"]) + int(r["sat_writing_avg_score"])
        d = demo.get(r["dbn"])
        rows.append({"dbn": r["dbn"], "school": r["school_name"], "borough": BOROUGH[r["dbn"][2]], "takers": int(r["num_of_sat_test_takers"]), "math": int(r["sat_math_avg_score"]),
                     "total": t, "poverty": float(d["frl_percent"]) if d and d["frl_percent"] != "" else None})
    log = {r["step"]: int(r["count"]) for r in table("cleaning.csv")}
    close("rows read", len(sat), log["SAT rows read"], 0)
    close("suppressed rows", sum(r["sat_math_avg_score"] == "s" for r in sat), log["rows with an 's' (suppressed: fewer than 5 test takers) instead of numbers"], 0)
    close("scored rows", len(rows), log["rows with scores after cleaning"], 0)
    close("test takers", sum(r["takers"] for r in rows), log["SAT test takers in scored schools"], 0)
    close("scored and matched", sum(r["poverty"] is not None for r in rows), log["scored schools matched (used in the poverty analysis)"], 0)

    top = sorted(rows, key=lambda r: -r["total"])[:10]
    for i, r in enumerate(table("top10.csv")):
        assert top[i]["school"] == r["school"], f"top 10 order {i}"
        close(f"top {i} total", top[i]["total"], r["total"], 0); close(f"top {i} takers", top[i]["takers"], r["takers"], 0)
        close(f"top {i} poverty", top[i]["poverty"], r["poverty_pct"], 0)
    strict = sorted((r for r in rows if r["math"] >= 640), key=lambda r: -r["math"])
    close("schools with math >= 640", len(strict), len(table("math_640.csv")), 0)
    assert [r["school"] for r in strict] == [r["school"] for r in table("math_640.csv")], "math 640 list"

    for r in table("borough.csv"):
        xs = rows if r["borough"] == "All" else [x for x in rows if x["borough"] == r["borough"]]
        t = [x["total"] for x in xs]
        close(r["borough"] + " schools", len(xs), r["schools"], 0); close(r["borough"] + " takers", sum(x["takers"] for x in xs), r["takers"], 0)
        close(r["borough"] + " mean", statistics.mean(t), r["mean_total"], 0.0051); close(r["borough"] + " median", statistics.median(t), r["median_total"], 0.0051)
        close(r["borough"] + " std", statistics.stdev(t), r["std_total"], 0.0051); close(r["borough"] + " min", min(t), r["min_total"], 0); close(r["borough"] + " max", max(t), r["max_total"], 0)
        close(r["borough"] + " weighted mean", sum(x["total"] * x["takers"] for x in xs) / sum(x["takers"] for x in xs), r["weighted_mean_total"], 0.0051)

    p = [x for x in rows if x["poverty"] is not None]
    out = json.load(open(R / "poverty.json"))
    close("schools in poverty analysis", len(p), out["schools"], 0)
    pv, tt = [x["poverty"] for x in p], [x["total"] for x in p]
    close("Pearson", pearson(pv, tt), out["pearson_r"]); close("Spearman", pearson(ranks(pv), ranks(tt)), out["spearman_rho"])

    def fit(sub, borough):
        cats = sorted({x["borough"] for x in sub})[1:]                  # drop the first borough (alphabetically), as the dummy coding does
        X = [[1.0, x["poverty"] / 10] + ([1.0 * (x["borough"] == c) for c in cats] if borough else []) for x in sub]
        return ols_hc3(X, [x["total"] for x in sub])
    top_ids = {x["dbn"] for x in sorted(rows, key=lambda r: -r["total"])[:10]}
    for key, sub, borough in [("simple", p, False), ("with_borough", p, True), ("without_top10", [x for x in p if x["dbn"] not in top_ids], False)]:
        s, lo, hi, r2 = fit(sub, borough)
        close(key + " n", len(sub), out[key]["n"], 0); close(key + " slope", s, out[key]["slope_per10"], 1e-7)
        close(key + " lo", lo, out[key]["slope_lo"], 1e-7); close(key + " hi", hi, out[key]["slope_hi"], 1e-7); close(key + " R2", r2, out[key]["r2"], 1e-7)

    edges = [percentile(pv, q) for q in (0, 25, 50, 75, 100)]          # pandas qcut: quartile edges, each bin closed on the right
    for k, r in enumerate(table("poverty_quartiles.csv")):
        members = [x for x in p if (x["poverty"] > edges[k] or k == 0) and x["poverty"] <= edges[k + 1]]
        close(f"quartile {k} schools", len(members), r["schools"], 0); close(f"quartile {k} takers", sum(x["takers"] for x in members), r["takers"], 0)
        close(f"quartile {k} from", min(x["poverty"] for x in members), r["poverty_from"], 0.0051); close(f"quartile {k} to", max(x["poverty"] for x in members), r["poverty_to"], 0.0051)
        close(f"quartile {k} mean", statistics.mean(x["total"] for x in members), r["mean_total"], 0.0051)
        close(f"quartile {k} weighted", sum(x["total"] * x["takers"] for x in members) / sum(x["takers"] for x in members), r["weighted_mean_total"], 0.0051)
    print(f"check.py: {n_ok} recomputed numbers agree with results/")


if __name__ == "__main__":
    main()
