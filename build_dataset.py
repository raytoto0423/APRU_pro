"""Build county-year training table.

Features: growth-stage weather anomalies for the current year AND the mean anomaly of the previous 5 years
(the baseline an insurer uses is a mean of those 5 yields, so shocks inside the baseline window matter).
Target: yield deviation (%) from the county's previous-5-year mean yield.
"""
import os
import numpy as np
import pandas as pd
from prep_yield import load_yield
from weather import load_asos, stage_features
from stations import build_map

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TRANSPLANT = (6, 1)   # used for training rows (team assumption: no per-county transplant dates in public data)
BASE_YEARS = 5


def station_year_table(asos, transplant_md=DEFAULT_TRANSPLANT):
    feats = {}
    for (sid, yr), g in asos.groupby(["stnId", asos["date"].dt.year]):
        feats[(sid, yr)] = stage_features(g, transplant_md)
    F = pd.DataFrame.from_dict(feats, orient="index")
    F.index = pd.MultiIndex.from_tuples(F.index, names=["stnId", "year"])
    return F.reset_index()


def base_feature_cols(F):
    return [c for c in F.columns if c not in ("stnId", "year") and not c.endswith("_n")]


def anomalies_and_lags(F, cols):
    F = F.sort_values(["stnId", "year"]).reset_index(drop=True)
    for c in cols:
        F[c] = F[c].astype(float)
        F[c] = F[c].fillna(F.groupby("stnId")[c].transform("mean")).fillna(F[c].mean())
    A = F[["stnId", "year"]].copy()
    for c in cols:
        A[c + "_anom"] = F[c] - F.groupby("stnId")[c].transform("mean")
    acols = [c + "_anom" for c in cols]
    # previous-5-year mean of anomalies (needs the 5 preceding calendar years to exist)
    L = A.groupby("stnId")[acols].transform(lambda s: s.shift(1).rolling(BASE_YEARS, min_periods=BASE_YEARS).mean())
    L.columns = [c.replace("_anom", "_lag5") for c in acols]
    A = pd.concat([A, L], axis=1)
    return A, acols, list(L.columns)


def build(transplant_md=DEFAULT_TRANSPLANT):
    y = load_yield()
    # drop counties with tiny paddy area (median < 500 ha): yields there are too noisy (e.g. 1000 or 215 kg/10a)
    y = y[y.groupby(["province", "county"])["area_ha"].transform("median") >= 500].copy()
    asos = load_asos()
    names = asos.groupby("stnId")["stnNm"].last().to_dict()
    mp = build_map(set(zip(y.province, y.county)), names)
    y = y[[(p, c) in mp for p, c in zip(y.province, y.county)]].copy()
    y["stnId"] = [mp[(p, c)] for p, c in zip(y.province, y.county)]

    F = station_year_table(asos, transplant_md)
    cols = base_feature_cols(F)
    A, acols, lcols = anomalies_and_lags(F, cols)
    # lag mean only valid when all 5 previous years exist for that station
    have = F.groupby("stnId")["year"].apply(set).to_dict()
    ok = [all((yr - k) in have[s] for k in range(1, BASE_YEARS + 1)) for s, yr in zip(A.stnId, A.year)]
    A.loc[~np.array(ok), lcols] = np.nan
    y = y.merge(A, on=["stnId", "year"], how="inner")
    y = y.merge(F[["stnId", "year"] + [c for c in F.columns if c.endswith("_n")]], on=["stnId", "year"], how="left")

    y = y.sort_values(["province", "county", "year"]).reset_index(drop=True)
    base = []
    for (_, _), g in y.groupby(["province", "county"]):
        s = g["yield_kg10a"]
        base.append(s.shift(1).rolling(BASE_YEARS, min_periods=BASE_YEARS).mean())
    y["baseline"] = pd.concat(base)
    y["dev_pct"] = (y["yield_kg10a"] / y["baseline"] - 1.0) * 100.0
    y = y.dropna(subset=["baseline", "dev_pct"])
    y = y.dropna(subset=lcols)
    return y, acols + lcols


if __name__ == "__main__":
    d, cols = build()
    d.to_csv(os.path.join(HERE, "data", "train_table.csv"), index=False, encoding="utf-8-sig")
    print(d.shape, "counties:", d.county.nunique(), "years:", d.year.min(), d.year.max())
    print("features:", len(cols))
    print(d[["yield_kg10a", "baseline", "dev_pct"]].describe().round(2))
