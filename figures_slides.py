"""Figuras limpas para os slides (results/figs/*.png), a partir das rodadas salvas."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

R = Path(__file__).parent / "results"
OUT = R / "figs"
OUT.mkdir(exist_ok=True)

INK, MUTED, BG = "#14213D", "#5B6475", "#F7F6F2"
BLUE, ORANGE, GRID = "#2F6FB0", "#D9691E", "#DEDBD2"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 20, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG})


def per_type(run):
    j = json.loads((R / "edgeiiot" / run / "metrics.json").read_text(encoding="utf-8"))
    return {k: 100 * v["alarm_rate"] for k, v in j["per_type_post_warmup"].items()}


# 1) Edge-IIoT, 14 ataques: alarmes por tipo, MODUS original vs MODUS+ (config fixa)
orig, plus = per_type("all_orig"), per_type("all_fixed_plus")
nomes = {"DDoS_HTTP": "DDoS HTTP", "DDoS_ICMP": "DDoS ICMP", "DDoS_TCP": "DDoS TCP SYN", "DDoS_UDP": "DDoS UDP",
         "SQL_injection": "SQL injection", "Port_Scanning": "Port scanning",
         "Vulnerability_scanner": "Vuln. scanner", "Normal": "Normal (falso positivo)"}
tipos = sorted([t for t in orig if t != "Normal"], key=lambda t: (plus[t], orig[t]))
tipos = ["Normal"] + tipos
y = np.arange(len(tipos))
fig, ax = plt.subplots(figsize=(16, 9.2), dpi=100)
h = 0.38
ax.barh(y + h / 2, [orig[t] for t in tipos], h, color=BLUE, label="MODUS original")
ax.barh(y - h / 2, [plus[t] for t in tipos], h, color=ORANGE, label="MODUS+ (taxa + normalização online)")
ax.set_yticks(y, [nomes.get(t, t) for t in tipos])
ax.set_xlim(0, 100)
ax.set_xlabel("pacotes que geraram alarme (%)")
ax.xaxis.grid(True, color=GRID)
ax.set_axisbelow(True)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.legend(loc="lower right", frameon=False, fontsize=20)
fig.tight_layout()
fig.savefig(OUT / "edge_por_tipo.png")
plt.close(fig)

# 2) ASEADOS: o score do DDoS é constante e o limiar fica no piso
s = pd.read_csv(R / "aseados" / "paper" / "scores.csv.gz", usecols=["t", "label", "score", "tau"])
b = s[(s.label == 0) & (s.t >= 50_000)].iloc[::8]
a = s[s.label == 1]
fig, ax = plt.subplots(figsize=(16, 7.2), dpi=100)
ax.axvspan(a.t.min(), a.t.max(), color="#F3D9C6", lw=0)
ax.scatter(b.t, b.score, s=3, color=BLUE, alpha=0.35, label="tráfego benigno")
ax.plot(a.t, a.score, color=ORANGE, lw=5, label="DDoS: todas as 51.465 instâncias = 0,806")
ax.plot(s.t[s.t >= 50_000], s.tau[s.t >= 50_000], color=INK, lw=2, label="limiar dinâmico")
ax.axhline(0.75, color=INK, ls="--", lw=1.5)
ax.text(5_000, 0.715, "piso ajustado à mão: 0,75", color=INK, fontsize=20, va="top")
ax.set_ylim(0, 1.02)
ax.set_xlim(0, len(s))
ax.set_xlabel("instância (ordem do fluxo)")
ax.set_ylabel("score de anomalia (HST)")
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v / 1000)} mil"))
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)
ax.legend(loc="lower left", frameon=False, fontsize=19, markerscale=6)
fig.tight_layout()
fig.savefig(OUT / "aseados_score.png")
plt.close(fig)
print("salvo em", OUT)
