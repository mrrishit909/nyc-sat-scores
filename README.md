# Which NYC schools post the top SAT scores?

The 2012 SAT results for New York City's public high schools, cleaned and joined to school demographics:
- which schools score highest, and what a strict "80% of the maximum math score" bar leaves;
- how the five boroughs compare, with the plain average of school averages and the student-weighted average side by side;
- how much of the spread in school scores a school's poverty rate explains.

The questions follow DataCamp's "Exploring NYC Public School Test Result Scores" project (data cleaning and group statistics). The data is
the city's open data, with a demographics table joined on.

Build log: https://mrrishit909.github.io/projects/nyc-sat-scores/

## Data

NYC Open Data, both tables from the NYC Department of Education, pulled 2026-10-03 (the city lists no licence; they are public records
published as open data):
- **2012 SAT Results** (`f9bf-2cp4`): 478 schools, with test takers and average critical reading, math and writing scores.
- **2006 - 2012 School Demographics and Accountability Snapshot** (`ihfw-zy9j`), the 2011-12 school year: enrolment, poverty (the
  share of students eligible for free or reduced-price lunch), English-language learners, special education.

Both are small, so the downloads are committed in `data/`; `download.py` refreshes them.

```
./venv/bin/pip install pandas numpy scipy statsmodels matplotlib certifi      # in a venv
./venv/bin/python download.py    # data/*.csv
./venv/bin/python clean.py       # results/schools.csv, cleaning.csv
./venv/bin/python analyze.py
./venv/bin/python check.py
./venv/bin/python charts.py
```

## Steps

1. **Download** both tables.
2. **Clean and join** (`clean.py`, every change counted in `results/cleaning.csv`): 57 of 478 schools have an "s" instead of numbers (fewer
   than 5 test takers), which becomes missing rather than zero; the borough comes from the letter in the school code; the total is
   reading + math + writing (2,400 at most in 2012); 450 schools match a demographics row (412 of the 421 scored ones; the nine
   that don't are alternative programs, such as Young Adult Borough Centers and GED programs, and a special-education site, with 109 of the 46,445 test takers).
3. **Rankings and boroughs:** the top 10 by total, the schools with math average at least 640, and each borough's number of schools, average,
   median, spread and student-weighted average.
4. **Poverty:** correlation (Pearson and Spearman) between school poverty and the total, a regression with robust (HC3) intervals, with and
   without borough effects and without the ten top scorers, and the average score by poverty quartile.
5. **Check.** `check.py` rebuilds everything from the two raw downloads with plain Python (no pandas or statsmodels): 126 numbers agree.
6. **Charts.**

## Results

- **The best schools:** Stuyvesant 2,096, Bronx Science 1,969, Staten Island Technical 1,953, American Studies at Lehman 1,920, Townsend Harris
  1,910. Eight schools clear 640 in math (Stuyvesant 735 is highest). The ten best have 92 to 1,277 test takers and 16% to 51% of students on
  free or reduced-price lunch.
- **Boroughs:** the plain average of school averages runs from the Bronx 1,145 and Brooklyn 1,167 through Manhattan 1,260 and Queens 1,275 to
  Staten Island 1,359 (12 schools). Weighted by test takers it is Bronx 1,240, Brooklyn 1,305, Queens 1,332, Manhattan 1,392 and Staten Island 1,394:
  Manhattan passes Queens (Stuyvesant alone has 832 test takers). The spread is widest in Staten Island (205) and Manhattan (202).
- **Poverty:** across 412 schools the correlation with school poverty is -0.72 (Spearman -0.57). Each 10 points more of poverty goes with 79 fewer
  SAT points (95% interval 68 to 90), and poverty alone explains 52% of the variation (55% with borough effects). Without the ten top scorers the
  slope is -63 (R squared 0.45). By quartile: 1,390 in the lowest-poverty fifth to 1,112 in the highest.

## Not done, and caveats

- Poverty is the school's rate, not the test takers' rate, and the 421 scored schools are those with at least five test takers; who takes the SAT
  differs by school (the lowest-poverty quartile has 22,352 of the 46,336 test takers in matched schools), so scores are not a measure of how
  well a school teaches.
- Many top schools admit by entrance exam, audition or screening (the data does not record admissions), so their scores reflect who is admitted.
- This is one year (2012), with the three-section SAT. It is a correlation across schools; nothing here says poverty causes lower scores.
