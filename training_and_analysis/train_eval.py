"""Leave-one-year-out comparison: 5-year-average baseline vs ridge / lasso / shallow gradient boosting.

Target = yield deviation (%) from the county's previous-5-year average (insurer-style normal yield).
Prediction of the deviation from stage weather anomalies lets us adjust that baseline.
"""
import json, os, pickle
import numpy as np
import pandas as pd
from models import Ridge, Lasso, GradientBoosting, leave_one_year_out, rmse, mae
from build_dataset import build

HERE = os.path.dirname(os.path.abspath(__file__))


def run():
    d, cols = build()
    d = d.reset_index(drop=True)
    y = d["dev_pct"].values
    res = {"n_rows": int(len(d)), "n_counties": int(d.county.nunique()),
           "years": [int(d.year.min()), int(d.year.max())], "n_features": len(cols)}
    cands = {
        "ridge_a30": lambda: Ridge(30.0), "ridge_a100": lambda: Ridge(100.0), "ridge_a300": lambda: Ridge(300.0),
        "lasso_a0.1": lambda: Lasso(0.1, 200), "lasso_a0.2": lambda: Lasso(0.2, 200),
        "gbm_d2": lambda: GradientBoosting(60, 0.06, 2, 12),
    }
    preds, scores = {}, {}
    base_pred = np.zeros(len(d))   # insurer-style: 5-year average => deviation 0
    jn = (d["province"] == "전라남도").values
    scores["baseline_5yr_avg"] = dict(rmse=rmse(base_pred, y), mae=mae(base_pred, y),
                                      rmse_jeonnam=rmse(base_pred[jn], y[jn]) if jn.any() else None)
    for name, f in cands.items():
        p = leave_one_year_out(d, cols, "dev_pct", "year", f)
        preds[name] = p
        scores[name] = dict(rmse=rmse(p, y), mae=mae(p, y),
                            rmse_jeonnam=rmse(p[jn], y[jn]) if jn.any() else None)
    best = min((k for k in scores if k != "baseline_5yr_avg"), key=lambda k: scores[k]["rmse"])
    res["scores"] = scores
    res["best_model"] = best
    res["improvement_pct_vs_baseline"] = 100 * (1 - scores[best]["rmse"] / scores["baseline_5yr_avg"]["rmse"])
    d["pred_dev_cv"] = preds[best]
    d.to_csv(os.path.join(HERE, "data", "train_table_cv.csv"), index=False, encoding="utf-8-sig")
    # final model on all data
    final = cands[best]().fit(d[cols].values.astype(float), y)
    with open(os.path.join(HERE, "data", "model.pkl"), "wb") as f:
        pickle.dump({"model": final, "cols": cols, "best": best, "resid_std": float(np.std(y - preds[best]))}, f)
    with open(os.path.join(HERE, "data", "results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    return res


if __name__ == "__main__":
    r = run()
    print(json.dumps(r, ensure_ascii=False, indent=2))
