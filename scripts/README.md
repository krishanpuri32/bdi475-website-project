# Scripts

Run each from the repository root with the Python in `.venv`.

| Script | What it does |
|---|---|
| `build_model.py` | Filters the CSV, fits the price model and writes `site_data/model.json` and `site_data/comps.json`. Prints a report. |
| `data_checks.py` | Prints the extra checks behind figures in `DECISIONS.md`. Writes nothing new. |
| `second_source_check.sql` | Recomputes three headline numbers from the SQLite file with SQL only: `sqlite3 "file:data/college_town_home_sales.sqlite?mode=ro" < scripts/second_source_check.sql` |

The site reads only the files in `site_data/`. GitHub Pages publishes them as committed, so rerun `build_model.py` and commit its output after any change to it.
