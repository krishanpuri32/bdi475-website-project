> Note: this is the plan as written before the build. `DECISIONS.md` records what changed.

# Build plan: college-town home price estimator

Written in the planning session on 2026-11-15. This is the handoff for Claude Code. Read it with
`AGENTS.md` and `docs/data_description_sheet.md` before writing code.

## What we are building

One static page. The visitor picks a city and enters a few facts about a home; the page shows an
estimated sale price as of the end of the data (March 2026), a likely range, and the most similar
homes that actually sold. No server, no build step, no framework.

Graded on three things only (20 points each): a public repo with at least one commit of our own,
the site loading at a public URL that is listed in the repo's About section, and a page built from
the dataset. Session 1 must end with all three met. Everything after that is improvement.

## Step 0, before any code

Done 2026-11-15: the public repo `krishanpuri32/bdi475-website-project` was created from the
template and cloned here; this folder's only commit is the template's "Initial commit".

Still to confirm at the start of session 1 (Krishan, on GitHub):

1. Settings, Pages, Source = GitHub Actions. Then Actions, "Publish site to GitHub Pages", Run
   workflow, and wait for the green check.
2. The Pages URL (expected `https://krishanpuri32.github.io/bdi475-website-project/`) is in the
   repo's About section (gear icon, Website field).

## Decisions already made

| Decision | Choice | Why |
|---|---|---|
| Model | Ordinary least squares on log(sale_price), fitted offline in Python | Small enough to ship as one JSON of coefficients; the page does the arithmetic in plain JavaScript |
| Inputs | City (18), living area, beds, baths, year built, miles to campus | All 98%+ filled. Miles to campus defaults to the city median so it can be left alone |
| "Purchase price" input | Left out | The data has one sale per home and no prior purchase price. `tax_assessed_value` is the nearest thing and is a possible session 3 add-on |
| "Current market" | A linear time trend in the model, evaluated at the last sale date | Sales run 2023-03-27 to 2026-03-25. The page must say "as of March 2026", not "today" |
| Location detail | City fixed effects, not ZIP | ZIP gained about 1 point of accuracy for a 64-item dropdown with 7 thin ZIPs |
| Rows used | sale_price 10,000 to 5,000,000; living area 300 to 8,000 sq ft; beds 1 to 7; baths 1 to 7; year built and sale date present | Covers data sheet problems 3 and 5. Leaves about 34,700 of 35,442 rows. Report the exact count dropped by each rule |
| `home_type`, lot size | Not used | Data sheet problems 4 and 5 |
| Agent log | Skipped (not in the rubric). `DECISIONS.md` replaces it | Written after the build: main directives, then corrections, changes and findings |

## Expected numbers (from a quick check in planning, to be recomputed by the script)

Model: log price on log sqft, beds, baths, age, age squared, years since first sale, city dummies.
Fitted on a random 80%, scored on the other 20%:

- R squared about 0.73; median absolute error about 15%; 63% of homes within 20% of the estimate.
- Adding log assessed value: median error about 13%.
- Price rises about 0.72% for each 1% more living area; the time trend is about +2.8% a year.
- The beds coefficient comes out slightly negative. That is not a bug: holding square footage
  fixed, an extra bedroom means smaller rooms. Worth a line in DECISIONS.md.

If the script's numbers land far from these, stop and find out why before building the page.

## Files

| Path | Made by | Purpose |
|---|---|---|
| `CLAUDE.md` | copy of `AGENTS.md` | Claude Code reads this name |
| `scripts/build_model.py` | session 1 | Reads the CSV (zipcode, county_fips, parcel_number as text), filters, fits, writes the two JSON files. pandas and numpy only. Fixed random seed |
| `site_data/model.json` | script | Coefficients, city list with median miles to campus, input ranges, reference date, held-out error quantiles, row counts kept and dropped |
| `site_data/comps.json` | script, session 2 | Slim sales table for the comparable-homes list: city, sale date, price, sqft, beds, baths, year built. Target under 2 MB |
| `index.html` | session 1 | Replaces the placeholder. Inline CSS and JS, relative paths |
| `README.md` | session 3 | Fill the template sections; delete "Start here" |
| `DECISIONS.md` | session 3 | Post hoc write-up |

Never write into `data/`.

## Sessions

**Session 1: get all 60 points.** Step 0 confirmed, `CLAUDE.md`, `scripts/build_model.py`,
`site_data/model.json`, and an `index.html` with the form and a single estimate. Check three
hand-computed estimates against the page. Debrief, then push and confirm the live URL loads in a
private window.

**Session 2: make the estimate honest and visibly data-driven.** A range around the estimate from
the held-out error quantiles (middle 80%), the five to eight most similar sold homes in the same
city from `comps.json`, a short "how this works and how wrong it can be" section, and input limits
so the page refuses values outside the fitted range instead of extrapolating.

**Session 3: paperwork and one optional feature.** README sections including the data notes,
`DECISIONS.md`, a second-source check of two or three headline numbers against the SQLite file.
Optional if time allows: an assessed-value field with its own coefficient set.

Out of scope: styling beyond readable defaults, charts, maps, mobile polish.

## Debrief checklist (before each push)

1. Does the page load from a fresh browser with no console errors?
2. Do the numbers on the page match what the script printed?
3. Is every number on the page computed from the data, with its filter rule stated?
4. Did anything in `data/` change? (`git status` must show nothing there.)
5. What went wrong or surprised us? One line each, for DECISIONS.md.
