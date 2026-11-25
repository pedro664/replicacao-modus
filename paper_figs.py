"""Figuras do artigo (paper/figs/*.pdf), a partir das rodadas salvas em results/.

  python paper_figs.py            # todas as figuras cujas rodadas existem
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

R = Path(__file__).parent / "results"
OUT = Path(__file__).parent / "paper" / "figs"
OUT.mkdir(parents=True, exist_ok=True)

# paleta categórica (ordem fixa) e tinta de texto
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e2dc"
plt.rcParams.update({
    "font.family": "serif", "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
    "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.2,
    "legend.frameon": False, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})
COL1 = 3.45  # largura de uma coluna IEEE (pol.)


def scores(ds, run, cols=None):
    f = R / ds / run / "scores.csv.gz"
    return pd.read_csv(f, usecols=cols) if f.exists() else None


def metrics(ds, run):
    f = R / ds / run / "metrics.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def fig_leak():
    """ASEADOS, config do artigo: score com e sem o rótulo no fluxo do HST do MOA."""
    a, b = scores("aseados", "paper"), scores("aseados", "nl_paper")
    if a is None or b is None:
        return
    fig, axes = plt.subplots(2, 1, figsize=(COL1, 2.7), sharex=True, gridspec_kw={"hspace": 0.45})
    rng = np.random.default_rng(0)
    for ax, d, title in [(axes[0], a, "MOA com rótulo no fluxo (Etapa 1): F1 99,73%"),
                         (axes[1], b, "MOA sem rótulo (corrigido): F1 0,00%")]:
        d = d[d.t >= 50_000]
        ben, att = d[d.label == 0], d[d.label == 1]
        ben = ben.iloc[rng.choice(len(ben), min(len(ben), 20_000), replace=False)]
        ax.scatter(ben.t / 1e3, ben.score, s=0.6, c=BLUE, alpha=0.35, lw=0, rasterized=True, label="benigno")
        ax.scatter(att.t / 1e3, att.score, s=1.2, c=ORANGE, alpha=0.8, lw=0, rasterized=True, label="DDoS")
        ax.plot(d.t / 1e3, d.tau, c=INK, lw=0.8, label=r"limiar $\tau$")
        ax.set_title(title, loc="left")
        ax.set_ylabel("score")
        ax.set_ylim(-0.04, 1.04)
    axes[1].set_xlabel("instância (mil)")
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=3, markerscale=8, handletextpad=0.3,
               bbox_to_anchor=(0.5, 1.06))
    fig.savefig(OUT / "leak_aseados.pdf", dpi=300)
    plt.close(fig)


def fig_frozen():
    """ASEADOS: distribuição dos scores do modelo congelado (benigno vs DDoS) e do adaptativo."""
    d = scores("aseados", "ppq_all", ["label", "score", "score_frozen", "t"])
    m = metrics("aseados", "ppq_all")
    if d is None:
        return
    d = d[d.score_frozen.notna()]
    fig, axes = plt.subplots(1, 2, figsize=(COL1, 1.55), sharey=True)
    bins = np.linspace(0, 1, 61)
    for ax, col, title in [(axes[0], "score", "HST adaptativo"), (axes[1], "score_frozen", "HST congelado")]:
        for lab, c, name in [(0, BLUE, "benigno"), (1, ORANGE, "DDoS")]:
            v = d.loc[d.label == lab, col]
            ax.hist(v, bins=bins, density=True, color=c, alpha=0.55, label=name)
        ax.set_title(title, loc="left")
        ax.set_xlabel("score")
    tau_f = None
    log = (R / "aseados" / "ppq_all" / "log.txt").read_text(encoding="utf-8")
    for line in log.splitlines():
        if line.startswith("modelo congelado"):
            tau_f = float(line.split("limiar ")[1].split()[0])
    if tau_f:
        axes[1].axvline(tau_f, c=INK, lw=0.8)
        axes[1].text(tau_f - 0.02, axes[1].get_ylim()[1] * 0.9, r"$\tau_f$", ha="right", color=INK)
    axes[0].set_ylabel("densidade")
    axes[0].legend(loc="upper left")
    fig.savefig(OUT / "frozen_aseados.pdf")
    plt.close(fig)


def _per_second(d, ts_col="ts"):
    sec = np.floor(d[ts_col]).astype(int)
    g = pd.DataFrame({"sec": sec, "y": d.label, "p": d.pred, "tr": d.get("trained", 0)})
    att = g[g.y == 1].groupby("sec").agg(n=("p", "size"), rec=("p", "mean"), tr=("tr", "mean"))
    ben = g[g.y == 0].groupby("sec").agg(fpr=("p", "mean"))
    return att, ben


def fig_ctu_timeline():
    """CTU-13: por segundo, fração do ataque detectada e usada no treino; base vs MODUS++."""
    runs = [("ppq_base", "MODUS+ fixed_q", BLUE), ("ppq_frozen", "+ congelado", AQUA),
            ("ppq_all", "MODUS++", ORANGE), ("ppq_all_cap01", "MODUS++ teto 0,1x (sens.)", YELLOW)]
    data = {}
    for run, _, _ in runs:
        d = scores("ctu13", run, ["timestamp", "label", "pred", "trained"])
        if d is None:
            return
        data[run] = d.rename(columns={"timestamp": "ts"})
    fig, axes = plt.subplots(3, 1, figsize=(COL1, 3.4), sharex=True,
                             gridspec_kw={"height_ratios": [0.6, 1, 1]})
    att0, _ = _per_second(data[runs[0][0]])
    axes[0].fill_between(att0.index, att0.n / 1e3, step="mid", color=MUTED, alpha=0.35, lw=0)
    axes[0].set_ylabel("ataque\n(mil pac./s)")
    full = np.arange(780, 976)
    for run, name, c in runs:
        att, ben = _per_second(data[run])
        att = att.reindex(full)  # NaN onde não há ataque: a linha quebra em vez de interpolar
        axes[1].plot(att.index, 100 * att.rec, c=c, lw=0.9, label=name)
        axes[2].plot(att.index, 100 * att.tr, c=c, lw=0.9, label=name)
    axes[1].set_ylabel("detectado (%)")
    axes[2].set_ylabel("treinado (%)")
    axes[2].set_xlabel("tempo (s)")
    h, lab = axes[1].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.07))
    for ax in axes[1:]:
        ax.set_ylim(-3, 103)
    axes[2].set_xlim(780, 975)
    fig.savefig(OUT / "ctu_timeline.pdf")
    plt.close(fig)


def fig_ablation():
    """F1 a priori e AUC do score, por variante, nas duas bases."""
    variants = [("ppq_base", "MODUS+\nfixed_q"), ("ppq_time10", "+janela\n10 s"), ("ppq_warmad", "+aquec.\nadapt."),
                ("ppq_cap", "+teto"), ("ppq_frozen", "+cong."), ("ppq_all", "MODUS++")]
    ctu = {"ppq_time10": "ppq_time10cap", "ppq_cap": "ppq_time10cap"}
    fig, axes = plt.subplots(1, 2, figsize=(COL1, 1.8), sharey=True)
    x = np.arange(len(variants))
    for ax, ds, title in [(axes[0], "aseados", "ASEADOS"), (axes[1], "ctu13", "CTU-13")]:
        f1 = []
        for run, _ in variants:
            r = ctu.get(run, run) if ds == "ctu13" else run
            if ds == "ctu13" and run == "ppq_warmad":
                f1.append(np.nan)
                continue
            m = metrics(ds, r)
            f1.append(np.nan if m is None else 100 * m["metrics_post_warmup"]["f1"])
        ax.bar(x, f1, width=0.7, color=[BLUE] * (len(variants) - 1) + [ORANGE], edgecolor="white", linewidth=1)
        for i, v in enumerate(f1):
            ax.text(i, (0 if np.isnan(v) else v) + 2, "n/r" if np.isnan(v) else f"{v:.0f}", ha="center",
                    va="bottom", fontsize=6, color=INK)
        ax.set_xticks(x, [v[1].replace("\n", " ") for v in variants], fontsize=6, rotation=40, ha="right",
                      rotation_mode="anchor")
        ax.set_title(title, loc="left")
        ax.set_ylim(0, 100)
    axes[0].set_ylabel("F1 a priori (%)")
    fig.savefig(OUT / "ablation.pdf")
    plt.close(fig)


if __name__ == "__main__":
    for f in [fig_leak, fig_frozen, fig_ctu_timeline, fig_ablation]:
        f()
        print("ok", f.__name__)
