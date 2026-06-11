from __future__ import annotations

import numpy as np
from scipy.optimize import minimize


def _utilities(w: np.ndarray, bias: np.ndarray, X: np.ndarray) -> np.ndarray:
    return bias + X @ w


def predict_proba(w: np.ndarray, bias: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Softmax over dialects for one (K, F) score matrix."""
    u = _utilities(np.asarray(w), np.asarray(bias), np.asarray(X, dtype=float))
    u = u - u.max()
    e = np.exp(u)
    return e / e.sum()


def _unpack(theta: np.ndarray, n_features: int, n_dialects: int):
    w = theta[:n_features]
    free_bias = theta[n_features:]
    bias = np.concatenate([[0.0], free_bias])  # bias[0] fixed at 0
    return w, bias


def fit_combiner(
    Xs: list[np.ndarray], ys: list[int], n_dialects: int, l2: float = 1.0
) -> tuple[np.ndarray, np.ndarray]:
    """Fit shared weights w (F,) and per-dialect bias (K,) by minimizing
    L2-regularized softmax NLL. bias[0] is pinned to 0 for identifiability."""
    Xs = [np.asarray(X, dtype=float) for X in Xs]
    n_features = Xs[0].shape[1]
    theta0 = np.zeros(n_features + (n_dialects - 1))

    def nll(theta: np.ndarray) -> float:
        w, bias = _unpack(theta, n_features, n_dialects)
        total = 0.0
        for X, y in zip(Xs, ys):
            u = _utilities(w, bias, X)
            u = u - u.max()
            logZ = np.log(np.exp(u).sum())
            total += logZ - u[y]
        total += l2 * float(w @ w)  # regularize weights, not biases
        return total

    res = minimize(nll, theta0, method="L-BFGS-B")
    w, bias = _unpack(res.x, n_features, n_dialects)
    return w, bias
