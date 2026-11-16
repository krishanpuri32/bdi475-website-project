"""Print the checks behind figures in DECISIONS.md that build_model.py does not print.

Run from the repository root:
    python scripts/data_checks.py

Reads the CSV and reuses build_model.py's kept rows and features (by running it, which
rewrites site_data/*.json with identical content). Writes nothing else.
"""

import contextlib
import io
import runpy
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(ROOT / "scripts" / "build_model.py"))
df, d, X, y, is_test = g["df"], g["d"], g["X"], g["y"], g["is_test"]

print("Fill rate of the model inputs, whole file:")
for c in ["city", "living_area_sqft", "beds", "baths", "year_built", "miles_to_campus"]:
    print(f"  {c}: {df[c].notna().mean():.2%}")

# ZIP dummies in place of city dummies, same rows, same split
vc = d["zipcode"].value_counts()
print(f"ZIP codes among kept rows: {len(vc)}; with under 30 kept rows: {int((vc < 30).sum())}")
base = X[[c for c in X.columns if not c.startswith("city=")]]
zips = sorted(vc.index)
Z = pd.concat([base, pd.DataFrame({"zip=" + z: (d["zipcode"] == z).astype(float)
                                   for z in zips[1:]}, index=d.index)], axis=1).to_numpy()
b, *_ = np.linalg.lstsq(Z[~is_test], y[~is_test], rcond=None)
e = np.abs(np.exp(y[is_test] - Z[is_test] @ b) - 1)
print(f"ZIP model held-out median abs error: {np.median(e):.1%}; within 20%: {np.mean(e <= 0.2):.1%}")

# Repeated parcel numbers
pn = df["parcel_number"]
placeholder = pn.isin(["0", "0.0"])
print(f"Parcel number is a placeholder ('0' or '0.0'): {int(placeholder.sum())} rows")
real = df[pn.notna() & ~placeholder].copy()
real["sale_date"] = pd.to_datetime(real["sale_date"])
grp = real.groupby(["parcel_number", "address_street"])
pairs = grp.filter(lambda x: len(x) > 1)
s = pairs.groupby(["parcel_number", "address_street"]).agg(
    n=("listing_id", "size"), zips=("zipcode", "nunique"), prices=("sale_price", "nunique"),
    days=("sale_date", lambda v: (v.max() - v.min()).days))
likely_dup = s[(s["prices"] == 1) & (s["days"] <= 30)]
print(f"Same parcel number and street on more than one row: {len(s)} groups, {len(pairs)} rows; "
      f"groups whose rows differ in ZIP: {int((s['zips'] > 1).sum())}")
print(f"  of those, same price and sale dates within 30 days: {len(likely_dup)} groups")
dup_ids = pairs.set_index(["parcel_number", "address_street"]).loc[likely_dup.index, "listing_id"]
print(f"  rows in those groups that are in the model's kept rows: "
      f"{int(d['listing_id'].isin(dup_ids).sum())}")
print(f"Largest baths value: whole file {df['baths'].max():g}, kept rows {d['baths'].max():g}")
