"""Gera figura score x limiar ao longo do fluxo para uma ou mais rodadas.

  python plot_run.py results/aseados/paper results/aseados/chronological
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

for run in map(Path, sys.argv[1:]):
    s = pd.read_csv(run / "scores.csv.gz")
    step = max(1, len(s) // 20000)  # subamostra só para desenhar
    d = s.iloc[::step]
    fig, ax = plt.subplots(figsize=(11, 3.6))
    att = s["label"].to_numpy() == 1
    edges = np.flatnonzero(np.diff(np.r_[0, att.astype(int), 0]))
    for a, b in zip(edges[::2], edges[1::2]):
        ax.axvspan(a, b, color="tab:red", alpha=0.12, lw=0)
    ax.scatter(d["t"], d["score"], s=1, c=np.where(d["label"] == 1, "tab:red", "tab:blue"), alpha=0.4)
    ax.plot(d["t"], d["tau"], color="black", lw=1, label="limiar τ")
    ax.axvline(50_000, color="gray", ls="--", lw=1, label="fim do aquecimento")
    for t in s["t"][s["flag"] == 1]:
        ax.axvline(t, color="tab:green", lw=0.6, alpha=0.6)
    ax.set(xlabel="instância (ordem do fluxo)", ylabel="score HST", ylim=(-0.02, 1.02),
           title=f"{run.name}: score (azul = benigno, vermelho = DDoS); verde = mudança ADWIN")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(run / "scores.png", dpi=150)
    print("salvo", run / "scores.png")
