# Decisions

How the site was built, what we corrected along the way, and what the data showed. Built in three sessions on 2026-11-15: Claude (Cowork) planned and reviewed each one, and Claude Code implemented it. Every number here comes from `site_data/model.json`, the report printed by `scripts/build_model.py`, `scripts/data_checks.py` or `scripts/second_source_check.sql`.

## Main build directives

- **An estimator, not a dashboard.** A few inputs give one sale-price estimate. It is quick to build and plainly based on the data.
- **Least squares on log price, fitted offline, shipped as a JSON file of coefficients.** The page is plain HTML and JavaScript and only does arithmetic, so there is no server and no build step.
- **Inputs: city, living area, bedrooms, bathrooms, year built, miles to campus.** Each is at least 98.9% filled (living area is the lowest; the rest are 99.96% or 100%).
- **City indicators, not ZIP.** On the same rows and split, ZIP indicators cut the held-out median error only from 14.9% to 13.7%. That gain wasn't worth a 64-item dropdown with 7 ZIPs of under 30 sales.
- **Keep sales priced $10,000 to $5,000,000, with 300 to 8,000 sq ft and 1 to 7 bedrooms and bathrooms.** This handles the data sheet's problems 3 (impossible prices) and 5 (impossible values).
- **`home_type` and lot size are not used.** Data sheet problems 4 and 5.
- **No agent log, two or three sessions, no cosmetic work.** The log is not in the rubric, and time was short. This file replaces it.
- **Session 2: show a range, six comparable sold homes and a plain "how wrong can this be" section.** One number on its own overstates what a model with a 14.9% median error knows.
- **Comparable sales come from the same kept rows as the model, with no addresses, at prices as sold.** The same filters apply everywhere, and the address is not unique (data sheet problem 2).
- **Session 3: the range is city-specific.** Among cities with at least 100 held-out sales, the median error runs from 10.3% (West Lafayette) and 10.6% (Davis) to 18.1% (Champaign), 18.4% (Ann Arbor) and 18.5% (Urbana). One band would misstate most of them. Carrboro, Newberry, Pittsboro and Savoy have fewer than 100 held-out sales and use the pooled band.
- **No assessed-value input.** It improves the held-out median error only from 14.9% to 13.6%, which doesn't justify a second set of coefficients and another field.

## Corrections and changes

| What changed | How it was caught |
|---|---|
| The planned "purchase price" input was dropped | Planning data check: the data has one row per completed sale and no earlier purchase price |
| "Current market" became "as of March 2026" | Planning data check: the sales stop on 2026-03-25 |
| The local folder was a clone of the course template with nowhere to push; recreated with "Use this template" | Planning: `git remote` pointed at the course organisation |
| The shipped coefficients are the 80% fit, not a refit on all rows | Code's call in session 1, kept: the held-out errors then describe exactly the model on the page |
| The time trend came out at +3.20% a year against about +2.8% in planning | Code checked 20 different random splits in session 1: they range from +2.87% to +3.23%, so this is split noise |
| The accuracy sentence stated the error the wrong way round ("estimates within X of the actual price") | Session 1 review of `index.html` against the script; fixed in session 2 to "the actual price was within X of the estimate" |
| The living-area breakdown given to the agent (376 / 127 / 3 / 70) was counted on the whole file and summed to 576, not the 562 the rule removes. At the rule it is 373 / 127 / 3 / 59 | Code checked the sum against the rule's count in session 2 and recorded both |
| "46 homes sold before they were built" is a whole-file count; 42 of them are in the kept rows | Code recounted on the kept rows in session 2; both counts are in `model.json` |
| The range wording changed from "8 in 10 similar sales closed between X and Y" to "8 in 10 held-back sales sold for between 74% and 136% of their estimate" | Code pointed out that the held-out errors measure all test sales, not "similar" sales |
| The input-limit line read "year built 1,900 to 2,026" | Code's own mistake (a shared number formatter), caught reading the browser test output before commit |
| A draft said "roughly 1 in 3 homes" sell for more than 20% off | Code replaced the rounded figure with the computed 37.3% |
| `AGENTS.md` and `AGENT_LOG.md` were deleted; `CLAUDE.md` is the one instruction file, without its plan-approval rule | The two instruction files were identical, and the rule conflicted with how the sessions were actually run |
| A README draft said the bathrooms rule removes the 60-bathroom home | Code checked the row in session 3: it also lists 30 bedrooms, so the bedrooms rule, which runs first, removes it |
| A DECISIONS.md draft called Champaign's band (66% to 142%) the widest | Code checked the band widths: Athens (73% to 153%) is wider |
| Session 2's notes gave the pooled 90th-percentile error as +0.3619 | Session 3 printed it in full: 0.36196, which rounds to +0.3620. The page shows 136% either way |

## Interesting findings

- **The bedrooms coefficient is slightly negative (−0.013).** Holding living area fixed, another bedroom means smaller rooms.
- **Price rises 0.72% for each 1% more living area, and falls about 2.3% for each mile from campus** (coefficient −0.0231).
- **Assessed value would add little.** It improves the held-out median error only from 14.9% to 13.6%, so leaving it out costs little.
- **Most rows removed for living area had none recorded.** Of the 562 the rule removes, 373 have no living area at all.
- **Some homes sold before they were built.** 46 sold in a year before their recorded year built (pre-construction sales), and 42 of them are in the fit.
- **No kept home is between 300 and 335 sq ft,** so the page's lower limit for living area is 336.
- **Accuracy differs a lot by city.** The middle-80% band is narrowest in Davis (79% to 121% of the estimate) and widest in Athens (73% to 153%). The pooled band is 74% to 136%.
- **The comparable sales show the spread better than the percentage does.** For a 1,800 sq ft, 3-bed, 2-bath home built in 1990 in Ann Arbor, the estimate is $491,989 but the six most similar sales went for $387,500 to $725,000.
- **The same home costs very different amounts in different towns.** That 1,800 sq ft, 3-bed, 2-bath home built in 1990, at the city's median distance from campus, is about $251k in Champaign, $492k in Ann Arbor and $906k in Davis.
- **Some sales appear to be recorded twice under two ZIP codes.** 19 pairs of rows share a parcel number and street but differ only in ZIP. In 17 of them the price is the same and the sale dates are within 30 days, so they are likely one sale entered twice. The data sheet's duplicate-address query groups by ZIP, so it misses them. 33 of those rows are in the kept rows, under 0.1% of 34,712, so the model was left as it is.
- **Some parcel numbers are placeholders.** 69 rows have a parcel number of "0" or "0.0", so the parcel number is not always the field that tells homes apart.
- **The SQLite file agrees with the CSV.** Plain SQL on it gives the same 34,712 kept rows, the same 71 removed by the price rule, and the same $240,000 median for the 2,270 kept Champaign sales.
