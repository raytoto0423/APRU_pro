"""Leave-one-year-out comparison with sklearn models and a small PyTorch MLP (GPU).

Same target/features as train_eval.py: yield deviation (%) vs county 5-yr mean, 72 weather-anomaly features.
"""
import json, os, pickle, time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from build_dataset import build

HERE = os.path.dirname(os.path.abspath(__file__))
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class MLP:
    """Small MLP regressor (standardized inputs, weight decay, dropout, fixed epochs)."""

    def __init__(self, hidden=(32, 16), epochs=250, lr=3e-3, wd=1e-2, dropout=0.2, seed=0):
        self.hidden, self.epochs, self.lr, self.wd, self.dropout, self.seed = hidden, epochs, lr, wd, dropout, seed

    def fit(self, X, y):
        torch.manual_seed(self.seed)
        self.sc = StandardScaler().fit(X)
        self.ym, self.ys = float(np.mean(y)), float(np.std(y)) or 1.0
        Xt = torch.tensor(self.sc.transform(X), dtype=torch.float32, device=DEV)
        yt = torch.tensor((y - self.ym) / self.ys, dtype=torch.float32, device=DEV).unsqueeze(1)
        layers, d = [], X.shape[1]
        for h in self.hidden:
            layers += [nn.Linear(d, h), nn.ReLU(), nn.Dropout(self.dropout)]
            d = h
        layers.append(nn.Linear(d, 1))
        self.net = nn.Sequential(*layers).to(DEV)
        opt = torch.optim.AdamW(self.net.parameters(), lr=self.lr, weight_decay=self.wd)
        for _ in range(self.epochs):
            self.net.train()
            opt.zero_grad()
            loss = nn.functional.mse_loss(self.net(Xt), yt)
            loss.backward()
            opt.step()
        return self

    def predict(self, X):
        self.net.eval()
        with torch.no_grad():
            dev = next(self.net.parameters()).device
            Xt = torch.tensor(self.sc.transform(X), dtype=torch.float32, device=dev)
            return self.net(Xt).squeeze(1).cpu().numpy() * self.ys + self.ym


def loyo(d, cols, make):
    years = d["year"].values
    X = d[cols].values.astype(float)
    y = d["dev_pct"].values
    p = np.full(len(d), np.nan)
    for yr in np.unique(years):
        te = years == yr
        p[te] = make().fit(X[~te], y[~te]).predict(X[te])
    return p


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def mae(a, b):
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))


def run():
    d, cols = build()
    d = d.reset_index(drop=True)
    y = d["dev_pct"].values
    jn = (d["province"] == "전라남도").values
    cands = {
        "ridge_a100": lambda: make_pipeline(StandardScaler(), Ridge(100.0)),
        "ridge_a300": lambda: make_pipeline(StandardScaler(), Ridge(300.0)),
        "ridge_a1000": lambda: make_pipeline(StandardScaler(), Ridge(1000.0)),
        "lasso_a0.1": lambda: make_pipeline(StandardScaler(), Lasso(0.1, max_iter=5000)),
        "gbm_d2": lambda: GradientBoostingRegressor(n_estimators=150, max_depth=2, learning_rate=0.04, subsample=0.8, random_state=0),
        "mlp_32_16": lambda: MLP((32, 16), 250, 3e-3, 1e-2, 0.2),
        "mlp_16": lambda: MLP((16,), 200, 3e-3, 3e-2, 0.3),
    }
    scores = {"baseline_5yr_avg": dict(rmse=rmse(0 * y, y), mae=mae(0 * y, y), rmse_jeonnam=rmse(0 * y[jn], y[jn]))}
    preds = {}
    for name, f in cands.items():
        t = time.time()
        p = loyo(d, cols, f)
        preds[name] = p
        scores[name] = dict(rmse=rmse(p, y), mae=mae(p, y), rmse_jeonnam=rmse(p[jn], y[jn]), sec=round(time.time() - t, 1))
        print(name, scores[name], flush=True)
    best = min(preds, key=lambda k: scores[k]["rmse"])
    res = {"n_rows": int(len(d)), "n_counties": int(d.county.nunique()), "years": [int(d.year.min()), int(d.year.max())],
           "n_features": len(cols), "device": str(DEV), "scores": scores, "best_model": best,
           "improvement_pct_vs_baseline": 100 * (1 - scores[best]["rmse"] / scores["baseline_5yr_avg"]["rmse"])}
    d["pred_dev_cv"] = preds[best]
    d["pred_dev_cv_ridge"] = preds["ridge_a300"]
    d.to_csv(os.path.join(HERE, "data", "train_table_cv.csv"), index=False, encoding="utf-8-sig")
    # final models: ridge (interpretable, used by the app) + the best model if different
    X = d[cols].values.astype(float)
    ridge = cands["ridge_a300"]().fit(X, y)
    pack = {"ridge": ridge, "cols": cols, "best": best, "resid_std": float(np.std(y - preds["ridge_a300"]))}
    if best.startswith("mlp"):
        pack["best_model_obj"] = None  # MLP kept in memory only; app uses ridge for transparency
    with open(os.path.join(HERE, "data", "model.pkl"), "wb") as f:
        pickle.dump(pack, f)
    with open(os.path.join(HERE, "data", "results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    return res


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: v for k, v in r.items() if k != "scores"}, ensure_ascii=False, indent=2))
