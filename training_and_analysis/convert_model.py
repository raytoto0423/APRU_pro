"""Export the trained ridge + MLP-ensemble to plain numpy arrays (data/model_np.npz) so the deployed app needs no torch/sklearn."""
import os, pickle
import numpy as np
from product import Engine

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    e = Engine()                       # loads data/model.pkl (needs torch/sklearn on this PC only)
    pack = e.pack
    rp = pack["ridge"]
    sc, rg = rp.steps[0][1], rp.steps[1][1]
    arrs = {"cols": np.array(pack["cols"]), "resid_std": np.array(pack["resid_std"]),
            "r_mean": sc.mean_, "r_scale": sc.scale_, "r_coef": rg.coef_, "r_int": np.array(float(rg.intercept_)),
            "n_mlp": np.array(len(pack["mlp"].ms))}
    for i, m in enumerate(pack["mlp"].ms):
        lin = [l for l in m.net if l.__class__.__name__ == "Linear"]
        assert len(lin) == 2, "expected one hidden layer"
        arrs[f"m{i}_mean"] = m.sc.mean_
        arrs[f"m{i}_scale"] = m.sc.scale_
        arrs[f"m{i}_W1"] = lin[0].weight.detach().cpu().numpy()
        arrs[f"m{i}_b1"] = lin[0].bias.detach().cpu().numpy()
        arrs[f"m{i}_W2"] = lin[1].weight.detach().cpu().numpy()
        arrs[f"m{i}_b2"] = lin[1].bias.detach().cpu().numpy()
        arrs[f"m{i}_ym"] = np.array(m.ym)
        arrs[f"m{i}_ys"] = np.array(m.ys)
    np.savez(os.path.join(HERE, "data", "model_np.npz"), **arrs)

    # verify equality on real feature rows
    from npmodel import NumpyModel
    nm = NumpyModel(os.path.join(HERE, "data", "model_np.npz"))
    import pandas as pd
    d = pd.read_csv(os.path.join(HERE, "data", "train_table_cv.csv"), encoding="utf-8-sig")
    X = d[list(pack["cols"])].values.astype(float)[:300]
    ref = 0.5 * pack["ridge"].predict(X) + 0.5 * pack["mlp"].predict(X)
    got = nm.predict(X)
    print("max abs diff vs original:", float(np.max(np.abs(ref - got))))


if __name__ == "__main__":
    main()
