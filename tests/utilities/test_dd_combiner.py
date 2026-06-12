import numpy as np
from QC.utilities.dialect_detector.combiner import predict_proba, fit_combiner

def test_predict_proba_is_softmax_of_utilities():
    w = np.array([1.0, 0.0])
    bias = np.array([0.0, 0.0])
    X = np.array([[2.0, 9.0], [0.0, 9.0]])  # dialect0 has higher first feature
    p = predict_proba(w, bias, X)
    assert p.shape == (2,)
    assert abs(p.sum() - 1.0) < 1e-9
    assert p[0] > p[1]

def test_fit_recovers_separating_weight():
    # Feature 0 is perfectly diagnostic: correct dialect always has the larger value.
    rng = np.random.default_rng(0)
    Xs, ys = [], []
    for _ in range(50):
        true = int(rng.integers(0, 2))
        X = np.zeros((2, 2))
        X[true, 0] = 1.0          # diagnostic feature
        X[:, 1] = rng.normal(size=2)  # noise feature
        Xs.append(X); ys.append(true)
    w, bias = fit_combiner(Xs, ys, n_dialects=2, l2=0.1)
    # weight on the diagnostic feature should dominate the noise feature
    assert w[0] > abs(w[1])
    # and the fitted model classifies the training set well
    correct = sum(int(np.argmax(predict_proba(w, bias, X)) == y) for X, y in zip(Xs, ys))
    assert correct >= 45
