"""ASOS daily growing-season data -> growth-stage weather features keyed by transplant date."""
import glob, os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
NUM = ["avgTa", "minTa", "maxTa", "sumRn", "hr1MaxRn", "avgWs", "maxWs", "maxInsWs", "sumSsHr", "avgRhm", "sumGsr"]

# growth stages as days-after-transplant windows (team assumption, typical Korean normal-season rice)
STAGES = {"S1_tiller": (0, 30), "S2_panicle": (30, 65), "S3_heading": (65, 95), "S4_ripen": (95, 135)}


def load_asos():
    files = glob.glob(os.path.join(HERE, "data", "asos_daily", "*_*.csv"))
    parts = []
    for f in files:
        try:
            d = pd.read_csv(f, encoding="utf-8-sig")
        except Exception:
            continue
        if len(d):
            parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    df["date"] = pd.to_datetime(df["tm"])
    for c in NUM:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["stnId"] = df["stnId"].astype(int)
    df["sumRn"] = df["sumRn"].fillna(0.0)  # blank daily rain = no rain recorded
    return df.sort_values(["stnId", "date"]).reset_index(drop=True)


def stage_features(daily, transplant_md=(6, 1)):
    """daily: one station-year DataFrame. Returns dict of stage features for the given transplant month/day."""
    year = daily["date"].dt.year.iloc[0]
    t0 = pd.Timestamp(year=year, month=transplant_md[0], day=transplant_md[1])
    out = {}
    for name, (a, b) in STAGES.items():
        w = daily[(daily["date"] >= t0 + pd.Timedelta(days=a)) & (daily["date"] < t0 + pd.Timedelta(days=b))]
        n = len(w)
        out[f"{name}_n"] = n
        out[f"{name}_tmean"] = w["avgTa"].mean() if n else np.nan
        out[f"{name}_tmax"] = w["maxTa"].mean() if n else np.nan
        out[f"{name}_tmin"] = w["minTa"].mean() if n else np.nan
        out[f"{name}_rain"] = w["sumRn"].sum() if n else np.nan
        out[f"{name}_sun"] = w["sumSsHr"].mean() if n else np.nan
        out[f"{name}_hot"] = int((w["maxTa"] >= 33).sum()) if n else np.nan
        out[f"{name}_heavy"] = int((w["sumRn"] >= 80).sum()) if n else np.nan
        out[f"{name}_wind"] = w["maxInsWs"].max() if n else np.nan
        out[f"{name}_coldnight"] = int((w["minTa"] < 17).sum()) if n else np.nan
    return out
