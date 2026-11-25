"""Tabela das rodadas da Etapa 2 (MODUS++ e reavaliação sem vazamento): results/modus_pp.md.

Para cada rodada: métricas a priori (pós-aquecimento), AUC-ROC/PR-AUC do HST adaptativo e do
congelado, fração do ataque usada no treino (envenenamento) e o F1 com o melhor limiar fixo sobre
o score adaptativo (ORÁCULO: usa rótulos, serve só como teto do que o score permite).

  python summarize_pp.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))
from modus import score_metrics  # noqa: E402

R = Path(__file__).parent / "results"

# (dataset, rodada, descrição) na ordem das tabelas do artigo
RUNS = [
    ("aseados", "paper", "MODUS, config do artigo, MOA com rótulo (Etapa 1)"),
    ("aseados", "nl_paper", "MODUS, config do artigo, sem rótulo"),
    ("aseados", "nl_no_flag", "MODUS sem flag ADWIN, sem rótulo"),
    ("aseados", "nl_fixedq_paper", "MODUS fixed_q, sem rótulo"),
    ("aseados", "nl_fixedq_plus", "MODUS+ fixed_q (MOA), sem rótulo"),
    ("aseados", "ppq_base", "MODUS+ fixed_q (numpy)"),
    ("aseados", "ppq_time10", "+ janela 10 s"),
    ("aseados", "ppq_warmad", "+ aquecimento adaptativo"),
    ("aseados", "ppq_cap", "+ teto de treino"),
    ("aseados", "ppq_normfreeze", "+ normalização congelada"),
    ("aseados", "ppq_frozen", "+ modelo congelado (c/ norm. congelada)"),
    ("aseados", "ppq_all", "MODUS++ (todas)"),
    ("aseados", "ppq_all_notime", "MODUS++ sem janela em tempo"),
    ("aseados", "ppq_all_nowarm", "MODUS++ sem aquecimento adaptativo"),
    ("aseados", "ppq_all_nocap", "MODUS++ sem teto"),
    ("aseados", "ppq_all_nofrozen", "MODUS++ sem modelo congelado"),
    ("aseados", "ppq_all_seed2", "MODUS++ semente 2"),
    ("aseados", "ppq_all_seed3", "MODUS++ semente 3"),
    ("aseados", "ppq_base_seed2", "MODUS+ fixed_q semente 2"),
    ("aseados", "ppq_base_seed3", "MODUS+ fixed_q semente 3"),
    ("aseados", "ppq_all_w1", "sens.: MODUS++ janela 1 s"),
    ("aseados", "ppq_all_w60", "sens.: MODUS++ janela 60 s"),
    ("aseados", "ppq_all_q99", "sens.: MODUS++ quantil congelado 0,99"),
    ("aseados", "nl_all_orig", "5 classes: MODUS artigo, sem rótulo"),
    ("aseados", "ppq_base_allcls", "5 classes: MODUS+ fixed_q"),
    ("aseados", "ppq_all_allcls", "5 classes: MODUS++"),
    ("ctu13", "paper", "MODUS, config do artigo, MOA com rótulo (Etapa 1)"),
    ("ctu13", "nl_paper", "MODUS, config do artigo, sem rótulo"),
    ("ctu13", "nl_cfg_aseados", "MODUS, config do ASEADOS, sem rótulo"),
    ("ctu13", "nl_fixedq_plus", "MODUS+ fixed_q (MOA), sem rótulo"),
    ("ctu13", "nl_fixed_plus", "MODUS+ fixed (MOA), sem rótulo"),
    ("ctu13", "ppq_base", "MODUS+ fixed_q (numpy)"),
    ("ctu13", "ppq_frozen", "+ modelo congelado (c/ norm. congelada)"),
    ("ctu13", "ppq_time10cap", "+ janela 10 s + teto"),
    ("ctu13", "ppq_all", "MODUS++ (todas)"),
    ("ctu13", "ppq_all_cap01", "sens.: MODUS++ teto 0,1x"),
    ("ctu13", "ppq_all_q99", "sens.: MODUS++ quantil congelado 0,99"),
]


def best_f1(y, s):
    """F1 máximo sobre todos os limiares fixos do score (oráculo)."""
    o = np.argsort(-s, kind="mergesort")
    ys, ss = y[o], s[o]
    grp = np.r_[np.flatnonzero(np.diff(ss)), len(ss) - 1]
    tp = np.cumsum(ys)[grp]
    fp = grp + 1 - tp
    f1 = 2 * tp / (tp + fp + y.sum())
    return float(f1.max()) if len(f1) else 0.0


def row(ds, run, desc):
    d = R / ds / run
    if not (d / "metrics.json").exists():
        return None
    m = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
    mp = m["metrics_post_warmup"]
    w = m.get("warmup_end", m["config"].get("warmup", 50_000))
    out = {"base": ds, "rodada": run, "descrição": desc, "aquec.": w,
           "Prec %": 100 * mp["precision"], "Rec %": 100 * mp["recall"], "F1 %": 100 * mp["f1"],
           "FPR %": 100 * mp["FP"] / max(1, mp["FP"] + mp["VN"]),
           "envenen. %": None if m.get("attacks_trained") is None else 100 * m["attacks_trained"],
           "AUC adapt. %": None, "AUC cong. %": None, "F1 oráculo %": None}
    sc = d / "scores.csv.gz"
    try:
        _scores_metrics(sc, w, out)
    except (EOFError, OSError, ValueError) as e:  # rodada em andamento ou arquivo truncado
        print(f"aviso: {sc}: {e}", file=sys.stderr)
    return out


def _scores_metrics(sc, w, out):
    if sc.exists():
        cols = pd.read_csv(sc, nrows=0).columns
        use = ["t", "label", "score"] + (["score_frozen"] if "score_frozen" in cols else [])
        s = pd.read_csv(sc, usecols=use)
        s = s[s.t >= w]
        y = s.label.to_numpy()
        out["AUC adapt. %"] = 100 * score_metrics(y, s.score.to_numpy())["roc_auc"]
        out["F1 oráculo %"] = 100 * best_f1(y, s.score.to_numpy())
        if "score_frozen" in s and s.score_frozen.notna().any():
            out["AUC cong. %"] = 100 * score_metrics(y, s.score_frozen.to_numpy())["roc_auc"]


def main():
    rows = [r for r in (row(*x) for x in RUNS) if r]
    df = pd.DataFrame(rows)
    fmt = lambda v: "–" if v is None or (isinstance(v, float) and np.isnan(v)) else (  # noqa: E731
        f"{v:.2f}" if isinstance(v, float) else f"{v:,}" if isinstance(v, (int, np.integer)) else str(v))
    lines = ["# Etapa 2 — MODUS++ e reavaliação sem vazamento de rótulo", "",
             "Fase operacional (após o aquecimento de cada rodada). `F1 oráculo` usa rótulos para escolher o "
             "melhor limiar fixo do score adaptativo: é um teto, não um resultado do método.", "",
             "| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(fmt(v) for v in r.values) + " |")
    (R / "modus_pp.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
