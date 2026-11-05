"""ClimateCredit engine: farm checklist -> weather-normal substitution -> personalised base yield & insured amount.

All thresholds below are team assumptions (prototype), labelled as such in the UI.
"""
import os, pickle, json
import numpy as np
import pandas as pd
from prep_yield import load_yield
from weather import load_asos, stage_features
from stations import build_map, JEONNAM
from build_dataset import base_feature_cols

HERE = os.path.dirname(os.path.abspath(__file__))
COVERAGE = [60, 70, 80, 85, 90]            # 2026 rice coverage levels (MAFRA guideline)
SUBSIDY = {60: 65, 70: 60, 80: 50, 85: 38, 90: 33}  # national premium subsidy %, by coverage level [MAFRA 2026]
SHOCK_EFFECT_PCT = -7.0                    # team assumption (picked by Jeonnam back-test): weather effect <= -7% => shock year
MAX_REPLACED = 2                           # at most 2 of the last 5 years replaced
UPLIFT_CAP_PCT = 7.0                       # team assumption: cap on base-yield uplift
DEFAULT_PRICE = 2500                       # KRW per kg (milled rice basis) - team assumption


class Engine:
    def __init__(self):
        npz = os.path.join(HERE, "data", "model_np.npz")
        if os.path.exists(npz):               # deployed / light path: pure numpy, no torch or sklearn
            from npmodel import NumpyModel
            self.nm = NumpyModel(npz)
            self.pack = None
            self.cols = self.nm.cols
            self.resid_std = self.nm.resid_std
        else:                                 # training PC path
            class _U(pickle.Unpickler):          # model.pkl was written while train_final.py ran as __main__
                def find_class(self, module, name):
                    if module == "__main__" and name == "Ensemble":
                        from train_final import Ensemble
                        return Ensemble
                    return super().find_class(module, name)
            with open(os.path.join(HERE, "data", "model.pkl"), "rb") as f:
                self.pack = _U(f).load()
            self.nm = None
            self.cols = self.pack["cols"]
            self.resid_std = self.pack["resid_std"]
        self.yield_df = load_yield()
        cache = os.path.join(HERE, "data", "asos_all.pkl")
        slim = os.path.join(HERE, "data", "asos_slim.csv.gz")
        if os.path.exists(slim):
            self.asos = pd.read_csv(slim, parse_dates=["date"], encoding="utf-8")
            self.asos["stnId"] = self.asos["stnId"].astype(int)
        elif os.path.exists(cache):
            self.asos = pd.read_pickle(cache)
        else:
            self.asos = load_asos()
            self.asos.to_pickle(cache)
        names = self.asos.groupby("stnId")["stnNm"].last().to_dict()
        self.stn_names = names
        self.cmap = build_map(set(zip(self.yield_df.province, self.yield_df.county)), names)
        self._clim = {}

    # ---------- helpers ----------
    def counties(self, province="전라남도"):
        return sorted(c for (p, c) in self.cmap if p == province)

    def station_of(self, province, county):
        sid = self.cmap.get((province, county))
        own = bool(sid) and (self.stn_names.get(sid, "").rstrip("시군구") == county.rstrip("시군구"))
        return sid, own

    def _station_years(self, sid, md):
        key = (sid, md)
        if key in self._clim:
            return self._clim[key]
        g = self.asos[self.asos.stnId == sid]
        rows = {}
        for yr, gg in g.groupby(g["date"].dt.year):
            rows[yr] = stage_features(gg, md)
        F = pd.DataFrame.from_dict(rows, orient="index")
        bcols = base_feature_cols(F.reset_index().rename(columns={"index": "year"}))
        bcols = [c for c in F.columns if not c.endswith("_n")]
        F = F[bcols].astype(float)
        F = F.fillna(F.mean())
        A = F - F.mean()
        A.columns = [c + "_anom" for c in A.columns]
        self._clim[key] = (A, F)
        return self._clim[key]

    def feature_row(self, sid, year, md, cur_only=False):
        A, _ = self._station_years(sid, md)
        acols = [c for c in self.cols if c.endswith("_anom")]
        lcols = [c for c in self.cols if c.endswith("_lag5")]
        if year not in A.index:
            return None
        cur = A.loc[year, acols].values.astype(float)
        if cur_only:
            lag = np.zeros(len(lcols))
        else:
            prev = [y for y in range(year - 5, year) if y in A.index]
            lag = A.loc[prev, acols].mean().values.astype(float) if len(prev) == 5 else np.full(len(lcols), np.nan)
        return np.concatenate([cur, lag])

    def predict(self, X):
        X = np.atleast_2d(X)
        if self.nm is not None:
            return self.nm.predict(X)
        pr = self.pack["ridge"].predict(X)
        pm = self.pack["mlp"].predict(X)
        return 0.5 * pr + 0.5 * pm

    def weather_effect(self, sid, year, md):
        """Weather-driven yield deviation (%) of `year` vs an average-weather year (lag features zeroed)."""
        x = self.feature_row(sid, year, md, cur_only=True)
        if x is None:
            return None
        zero = np.zeros_like(x)
        return float(self.predict(x)[0] - self.predict(zero)[0])

    def explain(self, sid, year, md, topk=6):
        """Break the weather effect of `year` into additive parts.

        effect = 0.5 * ridge(current anomalies) + 0.5 * mlp(...)  (lag features cancel out).
        The ridge half is linear, so it is split per feature; the neural-net half is shown as one block.
        Returns {"total", "rows": [...], "other", "nn", "ridge_sum"} (all in % points of yield).
        """
        A, F = self._station_years(sid, md)
        x = self.feature_row(sid, year, md, cur_only=True)
        if x is None:
            return None
        acols = [c for c in self.cols if c.endswith("_anom")]
        n = len(acols)
        if self.nm is not None:
            coef, scale = self.nm.z["r_coef"], self.nm.z["r_scale"]
        else:
            sc, rg = self.pack["ridge"].steps[0][1], self.pack["ridge"].steps[1][1]
            coef, scale = rg.coef_, sc.scale_
        contrib = 0.5 * coef[:n] * x[:n] / scale[:n]
        total = self.weather_effect(sid, year, md)
        rows = []
        for j in np.argsort(-np.abs(contrib))[:topk]:
            base = acols[j][:-5]
            rows.append({"key": base, "value": float(F.loc[year, base]), "normal": float(F[base].mean()),
                         "anom": float(A.loc[year, acols[j]]), "effect": float(contrib[j])})
        top_sum = sum(r["effect"] for r in rows)
        ridge_sum = float(contrib.sum())
        return {"total": float(total), "rows": rows, "other": ridge_sum - top_sum,
                "nn": float(total - ridge_sum), "ridge_sum": ridge_sum}

    # ---------- main product calculation ----------
    def quote(self, province, county, target_year, transplant_md, n_verified, n_items=6,
              area_ha=1.0, price=DEFAULT_PRICE):
        sid, own = self.station_of(province, county)
        hist = self.yield_df[(self.yield_df.province == province) & (self.yield_df.county == county)]
        hist = hist.set_index("year")["yield_kg10a"]
        yrs = list(range(target_year - 5, target_year))
        out = {"station": sid, "station_name": self.stn_names.get(sid), "own_station": own, "years": yrs}
        if sid is None or any(y not in hist.index for y in yrs):
            out["fallback"] = "history_missing"
            return out
        actual = np.array([hist[y] for y in yrs], dtype=float)
        eff = np.array([self.weather_effect(sid, y, transplant_md) for y in yrs], dtype=float)
        regional = float(actual.mean())
        normal = actual / (1 + eff / 100.0)          # yield that year would have had under average weather
        shock_idx = [i for i in np.argsort(eff) if eff[i] <= SHOCK_EFFECT_PCT][:MAX_REPLACED]
        sub = actual.copy()
        for i in shock_idx:
            sub[i] = max(actual[i], normal[i])
        adjusted_raw = float(sub.mean())
        cap_hit = adjusted_raw > regional * (1 + UPLIFT_CAP_PCT / 100)
        adjusted = min(adjusted_raw, regional * (1 + UPLIFT_CAP_PCT / 100))
        completeness = n_verified / n_items
        if completeness >= 5 / 6 and own:
            conf = "High"
        elif completeness >= 4 / 6:
            conf = "Medium"
        else:
            conf = "Low"
        fallback = "low_confidence" if conf == "Low" else None
        base_used = regional if fallback else adjusted
        units = area_ha * 10.0                         # 10a units
        table = []
        for c in COVERAGE:
            reg_amt = regional * units * price * c / 100
            per_amt = base_used * units * price * c / 100
            table.append({"coverage": c, "regional_amt": reg_amt, "personal_amt": per_amt,
                          "diff": per_amt - reg_amt, "subsidy_pct": SUBSIDY[c]})
        out.update({"actual": actual.tolist(), "effect_pct": eff.tolist(), "normal": normal.tolist(),
                    "replaced_years": [yrs[i] for i in shock_idx], "regional_base": regional,
                    "adjusted_base_raw": adjusted_raw, "adjusted_base": adjusted, "cap_hit": cap_hit,
                    "uplift_pct": 100 * (base_used / regional - 1), "confidence": conf, "fallback": fallback,
                    "completeness": completeness, "table": table})
        return out

    # ---------- backtest on Jeonnam ----------
    def backtest(self, province="전라남도", md=(6, 1), years=range(2006, 2026)):
        rows = []
        for county in self.counties(province):
            sid, _ = self.station_of(province, county)
            hist = self.yield_df[(self.yield_df.province == province) & (self.yield_df.county == county)].set_index("year")["yield_kg10a"]
            for t in years:
                yrs = list(range(t - 5, t))
                if t not in hist.index or any(y not in hist.index for y in yrs):
                    continue
                actual = np.array([hist[y] for y in yrs], dtype=float)
                eff = [self.weather_effect(sid, y, md) for y in yrs]
                if any(e is None for e in eff):
                    continue
                eff = np.array(eff)
                reg = actual.mean()
                normal = actual / (1 + eff / 100)
                idx = [i for i in np.argsort(eff) if eff[i] <= SHOCK_EFFECT_PCT][:MAX_REPLACED]
                sub = actual.copy()
                for i in idx:
                    sub[i] = max(actual[i], normal[i])
                adj = min(sub.mean(), reg * (1 + UPLIFT_CAP_PCT / 100))
                rows.append(dict(county=county, year=t, y=float(hist[t]), regional=float(reg), adjusted=float(adj),
                                 replaced=len(idx)))
        return pd.DataFrame(rows)


if __name__ == "__main__":
    e = Engine()
    q = e.quote("전라남도", "해남군", 2025, (6, 1), 6)
    print({k: v for k, v in q.items() if k not in ("table",)})
    for r in q["table"]:
        print(r)
