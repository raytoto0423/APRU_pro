"""Pure-numpy inference for the ridge + 5-net MLP blend (no torch / sklearn needed)."""
import numpy as np


class NumpyModel:
    def __init__(self, path):
        z = np.load(path, allow_pickle=False)
        self.z = {k: z[k] for k in z.files}
        self.cols = [str(c) for c in self.z["cols"]]
        self.resid_std = float(self.z["resid_std"])
        self.n_mlp = int(self.z["n_mlp"])

    def _ridge(self, X):
        z = self.z
        return ((X - z["r_mean"]) / z["r_scale"]) @ z["r_coef"] + float(z["r_int"])

    def _mlp(self, X):
        z, outs = self.z, []
        for i in range(self.n_mlp):
            Xs = (X - z[f"m{i}_mean"]) / z[f"m{i}_scale"]
            h = np.maximum(Xs @ z[f"m{i}_W1"].T + z[f"m{i}_b1"], 0.0)
            o = (h @ z[f"m{i}_W2"].T + z[f"m{i}_b2"]).ravel()
            outs.append(o * float(z[f"m{i}_ys"]) + float(z[f"m{i}_ym"]))
        return np.mean(outs, axis=0)

    def predict(self, X):
        X = np.atleast_2d(np.asarray(X, dtype=float))
        return 0.5 * self._ridge(X) + 0.5 * self._mlp(X)
