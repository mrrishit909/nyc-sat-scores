"""Step 1: the 2012 SAT results by school and the 2011-12 school demographics, from NYC Open Data (Socrata API).

    ./venv/bin/python download.py   -> data/sat.csv, data/demographics.csv, results/pull.json

SAT: dataset f9bf-2cp4, "2012 SAT Results" (NYC Department of Education), 478 schools.
Demographics: dataset ihfw-zy9j, "2006 - 2012 School Demographics and Accountability Snapshot", the 2011-12 school year (poverty = free or
reduced-price lunch eligibility, frl_percent).
"""
import csv
import json
import ssl
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import certifi

HERE = Path(__file__).parent
CTX = ssl.create_default_context(cafile=certifi.where())
BASE = "https://data.cityofnewyork.us/resource"


def fetch(dataset, **params):
    url = f"{BASE}/{dataset}.json?" + urllib.parse.urlencode({"$limit": 50000, **params})
    req = urllib.request.Request(url, headers={"User-Agent": "research-portfolio (Rishit Raj Mathur)"})
    return json.loads(urllib.request.urlopen(req, context=CTX, timeout=120).read())


def write(rows, name, keep):
    with open(HERE / "data" / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(keep)
        w.writerows([[str(r.get(k, "")).strip() for k in keep] for r in rows])


def main():
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "results").mkdir(exist_ok=True)
    sat = fetch("f9bf-2cp4")
    demo = fetch("ihfw-zy9j", **{"$where": "schoolyear='20112012'"})
    write(sat, "sat.csv", ["dbn", "school_name", "num_of_sat_test_takers", "sat_critical_reading_avg_score", "sat_math_avg_score", "sat_writing_avg_score"])
    write(demo, "demographics.csv", ["dbn", "name", "total_enrollment", "frl_percent", "ell_percent", "sped_percent"])
    info = {"pulled": date.today().isoformat(), "sat_rows": len(sat), "demographics_rows": len(demo), "demographics_year": "2011-12"}
    (HERE / "results" / "pull.json").write_text(json.dumps(info, indent=2) + "\n")
    print(info)


if __name__ == "__main__":
    main()
