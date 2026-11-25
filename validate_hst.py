"""Valida src/hst.py contra o HSTrees do MOA (CapyMOA): mesmas árvores e mesmos scores.

Fluxo de teste: score e depois treino em cada instância, com a janela por contagem do MOA.
O MOA inclui o atributo de classe entre as dimensões; aqui ele vai como uma coluna constante 0.

  python validate_hst.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "src"))
from hst import HST  # noqa: E402


def moa_scores(X, W, T, D, seed):
    from capymoa.anomaly import HalfSpaceTrees
    from capymoa.stream import NumpyStream

    st = NumpyStream(X, np.zeros(len(X), dtype=int), feature_names=[f"f{i}" for i in range(X.shape[1])])
    h = HalfSpaceTrees(st.get_schema(), random_seed=seed, window_size=W, number_of_trees=T, max_depth=D)
    out = []
    while st.has_more_instances():
        inst = st.next_instance()
        out.append(h.score_instance(inst))
        h.train(inst)
    return np.array(out)


def numpy_scores(X, W, T, D, seed):
    Xp = np.column_stack([X, np.zeros(len(X))])  # atributo de classe do MOA
    h = HST(Xp.shape[1], T, D, seed=seed)
    out, k, ref = [], 0, True
    for x in Xp:
        out.append(0.5 if ref else h.score(x[None, :], W)[0])
        h.add(x[None, :], to_reference=ref)
        if k > 50:
            ref = False
        if k % W == 0:
            h.swap()
        k += 1
    return np.array(out)


def main():
    rng = np.random.default_rng(0)
    # mistura de regimes, valores em [0,1] e fora dele, empates (protocolo discreto)
    X = np.column_stack([rng.random(4000), rng.integers(0, 3, 4000) / 2, rng.normal(0.5, 0.3, 4000),
                         np.r_[np.zeros(2000), rng.random(2000)]])
    ok = True
    for W, T, D, seed in [(250, 25, 15, 1), (500, 10, 8, 7), (100, 30, 12, 3)]:
        a, b = moa_scores(X, W, T, D, seed), numpy_scores(X, W, T, D, seed)
        diff = np.abs(a - b).max()
        print(f"W={W} T={T} D={D} seed={seed}: max |MOA - numpy| = {diff:.2e}")
        ok &= diff < 1e-9
    print("OK" if ok else "DIVERGE")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
