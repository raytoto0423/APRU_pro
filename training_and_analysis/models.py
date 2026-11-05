"""Pure-numpy models (scikit-learn/scipy are blocked on this PC by the app-control policy).

Ridge, Lasso (coordinate descent) and a shallow gradient-boosting regressor,
plus leave-one-year-out cross-validation.
"""
import numpy as np


def standardize_fit(X):
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd == 0] = 1.0
    return mu, sd


class Ridge:
    def __init__(self, alpha=1.0):
        self.alpha = alpha

    def fit(self, X, y):
        self.mu, self.sd = standardize_fit(X)
        Z = (X - self.mu) / self.sd
        self.y_mean = y.mean()
        n_features = Z.shape[1]
        A = Z.T @ Z + self.alpha * np.eye(n_features)
        self.coef_ = np.linalg.solve(A, Z.T @ (y - self.y_mean))
        return self

    def predict(self, X):
        Z = (X - self.mu) / self.sd
        return Z @ self.coef_ + self.y_mean


class Lasso:
    def __init__(self, alpha=0.05, n_iter=500):
        self.alpha = alpha
        self.n_iter = n_iter

    def fit(self, X, y):
        self.mu, self.sd = standardize_fit(X)
        Z = (X - self.mu) / self.sd
        self.y_mean = y.mean()
        yc = y - self.y_mean
        n, p = Z.shape
        w = np.zeros(p)
        col_sq = (Z ** 2).sum(axis=0) / n
        for _ in range(self.n_iter):
            for j in range(p):
                r = yc - Z @ w + Z[:, j] * w[j]
                rho = Z[:, j] @ r / n
                w[j] = np.sign(rho) * max(abs(rho) - self.alpha, 0) / col_sq[j]
        self.coef_ = w
        return self

    def predict(self, X):
        Z = (X - self.mu) / self.sd
        return Z @ self.coef_ + self.y_mean


class _Stump:
    """Depth-limited regression tree (depth 1-2) on numpy arrays."""

    def __init__(self, max_depth=2, min_leaf=5):
        self.max_depth = max_depth
        self.min_leaf = min_leaf

    def _best_split(self, X, r):
        best = (None, None, np.inf)
        n, p = X.shape
        for j in range(p):
            xs = X[:, j]
            order = np.argsort(xs)
            xs_s, r_s = xs[order], r[order]
            cs = np.cumsum(r_s)
            cs2 = np.cumsum(r_s ** 2)
            tot, tot2 = cs[-1], cs2[-1]
            for i in range(self.min_leaf - 1, n - self.min_leaf):
                if xs_s[i] == xs_s[i + 1]:
                    continue
                nl, nr = i + 1, n - i - 1
                sse_l = cs2[i] - cs[i] ** 2 / nl
                sse_r = (tot2 - cs2[i]) - (tot - cs[i]) ** 2 / nr
                sse = sse_l + sse_r
                if sse < best[2]:
                    best = (j, (xs_s[i] + xs_s[i + 1]) / 2.0, sse)
        return best

    def _build(self, X, r, depth):
        if depth >= self.max_depth or len(r) < 2 * self.min_leaf:
            return ("leaf", r.mean())
        j, thr, _ = self._best_split(X, r)
        if j is None:
            return ("leaf", r.mean())
        mask = X[:, j] <= thr
        return ("node", j, thr,
                self._build(X[mask], r[mask], depth + 1),
                self._build(X[~mask], r[~mask], depth + 1))

    def fit(self, X, r):
        self.tree = self._build(X, r, 0)
        return self

    def _pred_one(self, node, x):
        while node[0] == "node":
            node = node[3] if x[node[1]] <= node[2] else node[4]
        return node[1]

    def predict(self, X):
        return np.array([self._pred_one(self.tree, x) for x in X])


class GradientBoosting:
    def __init__(self, n_estimators=60, lr=0.08, max_depth=2, min_leaf=8):
        self.n_estimators = n_estimators
        self.lr = lr
        self.max_depth = max_depth
        self.min_leaf = min_leaf

    def fit(self, X, y):
        self.base = y.mean()
        pred = np.full(len(y), self.base)
        self.trees = []
        for _ in range(self.n_estimators):
            resid = y - pred
            t = _Stump(self.max_depth, self.min_leaf).fit(X, resid)
            pred = pred + self.lr * t.predict(X)
            self.trees.append(t)
        return self

    def predict(self, X):
        out = np.full(len(X), self.base)
        for t in self.trees:
            out = out + self.lr * t.predict(X)
        return out


def leave_one_year_out(df, feature_cols, target_col, year_col, model_factory):
    """Predict each year with a model trained on all other years."""
    preds = np.full(len(df), np.nan)
    years = df[year_col].values
    X = df[feature_cols].values.astype(float)
    y = df[target_col].values.astype(float)
    for yr in np.unique(years):
        te = years == yr
        tr = ~te
        m = model_factory().fit(X[tr], y[tr])
        preds[te] = m.predict(X[te])
    return preds


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def mae(a, b):
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))
