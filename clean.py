"""Step 2: clean the SAT table and join it to the demographics. Every change is counted in results/cleaning.csv.

    ./venv/bin/python clean.py   -> results/schools.csv, results/cleaning.csv
"""
import pandas as pd
from pathlib import Path

HERE = Path(__file__).parent
BOROUGH = {"M": "Manhattan", "K": "Brooklyn", "X": "Bronx", "Q": "Queens", "R": "Staten Island"}
SCORES = ["num_of_sat_test_takers", "sat_critical_reading_avg_score", "sat_math_avg_score", "sat_writing_avg_score"]


def main():
    sat = pd.read_csv(HERE / "data" / "sat.csv", dtype=str, keep_default_na=False)
    demo = pd.read_csv(HERE / "data" / "demographics.csv", dtype=str, keep_default_na=False)
    log = [("SAT rows read", len(sat))]
    log.append(("duplicate school codes (DBN)", int(sat["dbn"].duplicated().sum())))
    log.append(("rows with an 's' (suppressed: fewer than 5 test takers) instead of numbers", int((sat["sat_math_avg_score"] == "s").sum())))
    for c in SCORES:
        sat[c] = pd.to_numeric(sat[c], errors="coerce")                               # 's' becomes missing, not zero
    log.append(("rows with scores after cleaning", int(sat["sat_math_avg_score"].notna().sum())))
    bad = ~sat["dbn"].str.fullmatch(r"\d{2}[MKXQR]\d{3}")
    log.append(("school codes that don't look like district + borough letter + number", int(bad.sum())))
    sat["borough"] = sat["dbn"].str[2].map(BOROUGH)                                  # the letter after the district number
    sat["total"] = sat["sat_critical_reading_avg_score"] + sat["sat_math_avg_score"] + sat["sat_writing_avg_score"]   # the 2012 SAT had three sections, 2400 in all
    for c in ["total_enrollment", "frl_percent", "ell_percent", "sped_percent"]:
        demo[c] = pd.to_numeric(demo[c], errors="coerce")
    log.append(("demographics rows (2011-12)", len(demo)))
    m = sat.merge(demo[["dbn", "total_enrollment", "frl_percent", "ell_percent", "sped_percent"]], on="dbn", how="left")
    log.append(("SAT schools matched to a demographics row", int(m["frl_percent"].notna().sum())))
    log.append(("scored schools matched (used in the poverty analysis)", int((m["frl_percent"].notna() & m["total"].notna()).sum())))
    log.append(("SAT test takers in scored schools", int(m["num_of_sat_test_takers"].sum())))
    m["takers_share_pct"] = (100 * m["num_of_sat_test_takers"] / m["total_enrollment"]).round(1)
    m = m.rename(columns={"school_name": "school", "num_of_sat_test_takers": "takers", "sat_critical_reading_avg_score": "reading",
                          "sat_math_avg_score": "math", "sat_writing_avg_score": "writing", "frl_percent": "poverty_pct", "ell_percent": "ell_pct", "sped_percent": "sped_pct"})
    m.to_csv(HERE / "results" / "schools.csv", index=False)
    pd.DataFrame(log, columns=["step", "count"]).to_csv(HERE / "results" / "cleaning.csv", index=False)
    print(pd.DataFrame(log, columns=["step", "count"]).to_string(index=False))


if __name__ == "__main__":
    main()
