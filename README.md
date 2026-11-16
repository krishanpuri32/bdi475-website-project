# College-town home price estimator

## What this site is for

What would a home sell for in one of 18 college towns, as of March 2026, and how far off could that guess be? Pick a city and enter the living area, bedrooms, bathrooms, year built and distance to campus. The page shows an estimated sale price, a likely range, and the six most similar homes that actually sold in that city.

## Live site

https://krishanpuri32.github.io/bdi475-website-project/

## Data notes

All figures come from `data/college_town_home_sales.csv` (35,442 sales, 2023-03-27 to 2026-03-25), processed by `scripts/build_model.py`. The page reads the script's output in `site_data/model.json` and `site_data/comps.json`.

### Rows left out

Rules applied in this order. Each count is the rows removed by that rule among rows that passed the earlier rules.

| Rule | Rows removed |
|---|---:|
| Sale date present | 6 |
| Year built present | 1 |
| Sale price $10,000 to $5,000,000 | 71 |
| Living area 300 to 8,000 sq ft | 562 |
| Bedrooms 1 to 7 | 35 |
| Bathrooms 1 to 7 | 55 |
| **Kept** | **34,712** |

The 562 removed by the living-area rule were 373 with no living area, 127 at 0 sq ft, 3 under 300 sq ft and 59 over 8,000 sq ft. Among the kept rows, 42 sold one or two years before their recorded year built (pre-construction sales). They are kept, with an age of −1 or −2 years.

### How each figure is defined

- **Estimate:** a least squares regression on the log of sale price. The inputs are the log of living area, bedrooms, bathrooms, age, age squared, miles to campus, years since the first sale, and one indicator per city. It was fitted on a random 80% of the kept rows (27,783 sales, fixed seed 475). The page evaluates it at the last sale date, 2026-03-25, with age = 2026 − year built. The estimate is exp of the predicted log price, so it is a typical (median-like) price, not an average.
- **"As of March 2026":** the last sale in the kept rows, 2026-03-25. The model has no data after that date.
- **Accuracy figures:** measured on the other 20% (6,929 sales the model never saw), with error = actual price ÷ estimate − 1. For half of them the actual price was within 14.9% of the estimate, and for 62.7% it was within 20%.
- **Likely range:** the 10th and 90th percentiles of that error, applied to the estimate. It uses the city's own held-out sales when the city has at least 100 of them. Otherwise it uses all 6,929 (74% to 136% of the estimate); that applies to Carrboro, Newberry, Pittsboro and Savoy. The page says which band it used.
- **Most similar homes:** the six kept sales in the chosen city with the lowest score `|ln(sqft ÷ your sqft)| ÷ 0.25 + 0.5 × |beds difference| + 0.5 × |baths difference| + |year built difference| ÷ 20`. Ties go to the more recent sale. Prices are as sold on their own dates, not adjusted to March 2026.

### The data sheet's five problems

1. **Days on market:** not used. The site uses no list or contract dates.
2. **Street address is not unique:** the address is not used and is not in the site's files. `listing_id` is used only to order the comparable sales and is not written either.
3. **Impossible prices:** only sales from $10,000 to $5,000,000 are kept (71 removed).
4. **`home_type` is unreliable:** not used.
5. **Impossible values:** the living-area rule removes the 0 sq ft rows and the other implausible areas (562 removed). The 60-bathroom home also lists 30 bedrooms, so the bedrooms rule removes it. The largest kept value is 7 for both. Lot size and tax are not used.

### Second-source check

`scripts/second_source_check.sql` recomputes three numbers from `data/college_town_home_sales.sqlite` with SQL only, independently of the Python script. Both give the same answers: 34,712 rows kept, 71 rows removed by the price rule at its position, and a median sale price of $240,000 for the 2,270 kept Champaign sales.

## How to rebuild the site data

From the repository root:

```
python scripts/build_model.py
```

It needs Python with pandas and numpy only. The committed files were made with Python 3.14.6, pandas 3.1.1 and numpy 2.5.5. `model.json` was also reproduced exactly under pandas 2.3.3. The script never writes to `data/`. Commit its output: GitHub Pages publishes the files as they are, with no build step.

## Files

| Path | What it is |
|---|---|
| `index.html` | The site: one page, with inline CSS and JavaScript |
| `site_data/model.json` | Model coefficients, city list, input limits, held-out accuracy and range bands, row counts |
| `site_data/comps.json` | The kept sales by city (date, price, size, beds, baths, year built, miles), for the similar-homes table |
| `scripts/build_model.py` | Makes both `site_data` files from the CSV |
| `scripts/data_checks.py` | Prints the extra checks behind figures in `DECISIONS.md` |
| `scripts/second_source_check.sql` | The SQLite cross-check above |
| `data/college_town_home_sales.*` | The dataset, version 1.0, in CSV, Excel, SQLite, DuckDB and Parquet. Never edited |
| `docs/data_description_sheet.md` | What every column means, and five problems in the data |
| `docs/build_plan.md` | The plan as written before the build |
| `DECISIONS.md` | What we decided, what we corrected and what we found |
| `CLAUDE.md` | Project instructions for the AI coding agent |
| `.github/workflows/pages.yml` | Publishes the repository to GitHub Pages on each push to main |

## Tools we used

Claude (Cowork) for planning and review, Claude Code for implementation, Python with pandas and numpy for the model, and GitHub Pages for hosting. The page uses no JavaScript libraries.

## Citation

College-town home sales dataset, version 1.0 (2026). University of Illinois-Deloitte Foundation Center for Business Emerging Technologies. Data collected March 2026.
