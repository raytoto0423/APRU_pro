"""Choose the final model: ridge vs MLP-ensemble vs blend (leave-one-year-out), then fit on all data and save."""
import json, os, pickle
import numpy as np
import torch
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from build_dataset import build
from train_eval2 import MLP, rmse, mae

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = [0, 1, 2, 3, 4]


def ridge_f():
    return make_pipeline(StandardScaler(), Ridge(300.0))


def mlp_f(seed):
    return MLP((16,), 200, 3e-3, 3e-2, 0.3, seed=seed)


class Ensemble:
    def __init__(self):
        self.ms = [mlp_f(s) for s in SEEDS]

    def fit(self, X, y):
        for m in self.ms:
            m.fit(X, y)
        return self

    def predict(self, X):
        return np.mean([m.predict(X) for m in self.ms], axis=0)


def main():
    d, cols = build()
    d = d.reset_index(drop=True)
    X = d[cols].values.astype(float)
    y = d["dev_pct"].values
    years = d["year"].values
    jn = (d["province"] == "전라남도").values
    p_r, p_m = np.zeros(len(d)), np.zeros(len(d))
    for yr in np.unique(years):
        te = years == yr
        p_r[te] = ridge_f().fit(X[~te], y[~te]).predict(X[te])
        p_m[te] = Ensemble().fit(X[~te], y[~te]).predict(X[te])
    p_b = 0.5 * p_r + 0.5 * p_m
    out = {}
    for name, p in [("baseline_5yr_avg", 0 * y), ("ridge", p_r), ("mlp_ensemble5", p_m), ("blend_ridge_mlp", p_b)]:
        out[name] = dict(rmse=rmse(p, y), mae=mae(p, y), rmse_jeonnam=rmse(p[jn], y[jn]), mae_jeonnam=mae(p[jn], y[jn]))
        print(name, {k: round(v, 3) for k, v in out[name].items()}, flush=True)
    best = min(["ridge", "mlp_ensemble5", "blend_ridge_mlp"], key=lambda k: out[k]["rmse"])
    preds = {"ridge": p_r, "mlp_ensemble5": p_m, "blend_ridge_mlp": p_b}[best]
    d["pred_dev_cv"] = preds
    d["pred_dev_cv_ridge"] = p_r
    d.to_csv(os.path.join(HERE, "data", "train_table_cv.csv"), index=False, encoding="utf-8-sig")

    ridge = ridge_f().fit(X, y)
    ens = Ensemble().fit(X, y)
    for m in ens.ms:   # move to CPU for the app
        m.net.to("cpu")
    pack = {"ridge": ridge, "mlp": ens, "best": best, "cols": cols, "resid_std": float(np.std(y - preds)),
            "blend_w": 0.5}
    with open(os.path.join(HERE, "data", "model.pkl"), "wb") as f:
        pickle.dump(pack, f)
    res = {"n_rows": int(len(d)), "n_counties": int(d.county.nunique()), "years": [int(d.year.min()), int(d.year.max())],
           "n_features": len(cols), "scores": out, "best_model": best,
           "improvement_pct_vs_baseline": 100 * (1 - out[best]["rmse"] / out["baseline_5yr_avg"]["rmse"]),
           "improvement_pct_vs_baseline_jeonnam": 100 * (1 - out[best]["rmse_jeonnam"] / out["baseline_5yr_avg"]["rmse_jeonnam"])}
    with open(os.path.join(HERE, "data", "results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("BEST:", best, round(res["improvement_pct_vs_baseline"], 1), "% overall,",
          round(res["improvement_pct_vs_baseline_jeonnam"], 1), "% Jeonnam")


if __name__ == "__main__":
    main()
