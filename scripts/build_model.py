"""Fit the home price model and write site_data/model.json.

Run from the repository root:
    python scripts/build_model.py

Reads data/college_town_home_sales.csv (never writes to data/). Uses pandas and numpy only.
Model: ordinary least squares on log(sale_price) with log living area, beds, baths, age at sale,
age squared, miles to campus, years since the first sale in the data, and one dummy per city.
Fitted on a random 80% of the kept rows (fixed seed) and scored on the other 20%. The shipped
coefficients are the 80% fit, so the held-out errors describe exactly the model the page uses.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "college_town_home_sales.csv"
OUT = ROOT / "site_data" / "model.json"
SEED = 475
TEST_SHARE = 0.20

# Data sheet: read these as text so leading zeros survive.
df = pd.read_csv(CSV, dtype={"zipcode": str, "county_fips": str, "parcel_number": str})
df["sale_date"] = pd.to_datetime(df["sale_date"])
rows_total = len(df)

# Filter rules, applied in this order. Each count is rows removed by that rule
# among rows that survived the earlier rules.
rules = [
    ("sale_date present", df["sale_date"].notna()),
    ("year_built present", df["year_built"].notna()),
    ("sale_price 10,000 to 5,000,000", df["sale_price"].between(10_000, 5_000_000)),
    ("living_area_sqft 300 to 8,000", df["living_area_sqft"].between(300, 8_000)),
    ("beds 1 to 7", df["beds"].between(1, 7)),
    ("baths 1 to 7", df["baths"].between(1, 7)),
]
keep = pd.Series(True, index=df.index)
dropped = []
for name, ok in rules:
    removed = int((keep & ~ok).sum())
    dropped.append({"rule": name, "rows_removed": removed})
    keep &= ok
d = df[keep].copy()
rows_kept = len(d)

# Detail for the data notes: what the living-area rule removed, counted at the rule
# (rows that passed the earlier rules) and in the whole file.
before_sqft = rules[0][1] & rules[1][1] & rules[2][1]
sqft = df["living_area_sqft"]
sqft_parts = {"missing": sqft.isna(), "zero": sqft == 0,
              "1_to_299": (sqft > 0) & (sqft < 300), "over_8000": sqft > 8000}
sqft_detail = {
    "at_rule": {k: int((before_sqft & v).sum()) for k, v in sqft_parts.items()},
    "whole_file": {k: int(v.sum()) for k, v in sqft_parts.items()},
}
neg_age = {
    "kept_rows": int(((d["sale_date"].dt.year - d["year_built"]) < 0).sum()),
    "whole_file": int(((df["sale_date"].dt.year - df["year_built"]) < 0).sum()),
}

first_sale = d["sale_date"].min()
last_sale = d["sale_date"].max()
cities = sorted(d["city"].unique())
base_city = cities[0]  # absorbed into the intercept


def design(frame):
    """Build the feature matrix. Column order must match FEATURES."""
    age = frame["sale_date"].dt.year - frame["year_built"]
    cols = {
        "intercept": np.ones(len(frame)),
        "log_sqft": np.log(frame["living_area_sqft"]),
        "beds": frame["beds"],
        "baths": frame["baths"],
        "age": age,
        "age_sq": age**2,
        "miles_to_campus": frame["miles_to_campus"],
        "years_since_first_sale": (frame["sale_date"] - first_sale).dt.days / 365.25,
    }
    for c in cities[1:]:
        cols["city=" + c] = (frame["city"] == c).astype(float)
    return pd.DataFrame(cols, index=frame.index)


X = design(d)
FEATURES = list(X.columns)
y = np.log(d["sale_price"].to_numpy())

rng = np.random.default_rng(SEED)
is_test = rng.random(rows_kept) < TEST_SHARE
Xtr, Xte = X.to_numpy()[~is_test], X.to_numpy()[is_test]
ytr, yte = y[~is_test], y[is_test]

beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
pred = Xte @ beta
resid = yte - pred
r2 = 1 - np.sum(resid**2) / np.sum((yte - yte.mean()) ** 2)
# Error as a share of the estimate: actual / estimate - 1
ratio_err = np.exp(resid) - 1
abs_pct = np.abs(ratio_err)

# Comparison only, not shipped: same model plus log assessed value (planning check).
has_av = d["tax_assessed_value"].fillna(0).to_numpy() > 0
Xav = np.column_stack([X.to_numpy(), np.log(np.where(has_av, d["tax_assessed_value"], 1))])
m_tr, m_te = ~is_test & has_av, is_test & has_av
b_av, *_ = np.linalg.lstsq(Xav[m_tr], y[m_tr], rcond=None)
av_med = float(np.median(np.abs(np.exp(y[m_te] - Xav[m_te] @ b_av) - 1)))

coef = dict(zip(FEATURES, (float(b) for b in beta)))

city_info = []
for c in cities:
    g = d[d["city"] == c]
    city_info.append({
        "city": c,
        "state": g["state"].iloc[0],
        "rows": int(len(g)),
        "median_miles_to_campus": round(float(g["miles_to_campus"].median()), 1),
    })


def rng_of(col):
    s = d[col]
    return {"min": float(s.min()), "max": float(s.max()),
            "p01": float(s.quantile(0.01)), "p99": float(s.quantile(0.99)),
            "median": float(s.median())}


model = {
    "description": "OLS on log(sale_price). estimate = exp(sum of coefficient * feature).",
    "source": "data/college_town_home_sales.csv, fitted by scripts/build_model.py",
    "features": {
        "log_sqft": "natural log of living_area_sqft",
        "age": "sale year minus year_built (the page uses the reference date's year)",
        "age_sq": "age squared",
        "years_since_first_sale": "(sale_date - first_sale_date) in days / 365.25",
        "city=<name>": f"1 if that city, else 0; {base_city} is the base city",
    },
    "coefficients": coef,
    "base_city": base_city,
    "first_sale_date": first_sale.strftime("%Y-%m-%d"),
    "reference_date": last_sale.strftime("%Y-%m-%d"),
    "reference_years_since_first_sale": (last_sale - first_sale).days / 365.25,
    "cities": city_info,
    "input_ranges": {c: rng_of(c) for c in
                     ["living_area_sqft", "beds", "baths", "year_built", "miles_to_campus"]},
    "rows": {"total": rows_total, "kept": rows_kept, "dropped_by_rule": dropped,
             "train": int((~is_test).sum()), "test": int(is_test.sum()),
             "seed": SEED,
             "living_area_rule_detail": sqft_detail,
             "negative_age": neg_age},
    "holdout": {
        "r_squared_log": float(r2),
        "median_abs_pct_error": float(np.median(abs_pct)),
        "share_within_10pct": float(np.mean(abs_pct <= 0.10)),
        "share_within_20pct": float(np.mean(abs_pct <= 0.20)),
        # actual / estimate - 1, for the range in session 2
        "error_quantiles": {f"p{q}": float(np.quantile(ratio_err, q / 100))
                            for q in (5, 10, 25, 50, 75, 90, 95)},
    },
}

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(model, indent=2) + "\n")

# Comparable sales: the same kept rows, as parallel arrays per city. No addresses or ids.
# Prices are as sold, on their own dates.
comps = {"columns": ["sale_date", "sale_price", "living_area_sqft", "beds", "baths",
                     "year_built", "miles_to_campus"],
         "source": "kept rows of data/college_town_home_sales.csv, by scripts/build_model.py",
         "cities": {}}
for c in cities:
    g = d[d["city"] == c].sort_values(["sale_date", "listing_id"], ascending=[False, True])
    comps["cities"][c] = [
        g["sale_date"].dt.strftime("%Y-%m-%d").tolist(),
        g["sale_price"].astype(int).tolist(),
        g["living_area_sqft"].astype(int).tolist(),
        g["beds"].astype(int).tolist(),
        [float(b) if b % 1 else int(b) for b in g["baths"]],
        g["year_built"].astype(int).tolist(),
        [float(m) for m in g["miles_to_campus"]],
    ]
COMPS = ROOT / "site_data" / "comps.json"
COMPS.write_text(json.dumps(comps, separators=(",", ":")) + "\n")

# Printed report
print(f"Rows in file: {rows_total:,}")
for r in dropped:
    print(f"  dropped by '{r['rule']}': {r['rows_removed']:,}")
print(f"Rows kept: {rows_kept:,}  (train {model['rows']['train']:,}, test {model['rows']['test']:,})")
print(f"Sales {model['first_sale_date']} to {model['reference_date']}")
print(f"Held-out R^2 (log): {r2:.3f}")
print(f"Held-out median abs error: {np.median(abs_pct):.1%}")
print(f"Held-out within 20%: {np.mean(abs_pct <= 0.20):.1%}")
print(f"With log assessed value (comparison only): median abs error {av_med:.1%}")
print(f"Elasticity on living area: {coef['log_sqft']:.3f}")
print(f"Time trend per year: {np.exp(coef['years_since_first_sale']) - 1:+.2%}")
print(f"Beds coefficient: {coef['beds']:+.4f}   baths: {coef['baths']:+.4f}")
print(f"Miles to campus coefficient: {coef['miles_to_campus']:+.4f}")
print(f"Living-area rule detail: {sqft_detail}")
print(f"Negative age (sale year before year built): {neg_age}")
print(f"Wrote {OUT.relative_to(ROOT)}")
print(f"Wrote {COMPS.relative_to(ROOT)} ({COMPS.stat().st_size:,} bytes, "
      f"{sum(len(v[0]) for v in comps['cities'].values()):,} sales)")
