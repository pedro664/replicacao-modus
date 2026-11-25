"""Roda o MODUS (ou o MODUS+) num dataset e salva insumos em results/<dataset>/<nome>/.

Exemplos:
  python run.py aseados --name paper
  python run.py aseados --name chronological --order chronological
  python run.py ctu13 --name paper
  python run.py edgeiiot --name clean --variant clean
  python run.py ctu13 --name cfg_aseados --preset aseados          # config fixa de outra base
  python run.py edgeiiot --name plus_all --variant all --features plus --preset fixed
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))
from datasets import load_aseados, load_ctu13, load_edgeiiot  # noqa: E402
from features import modus_plus_features  # noqa: E402
from modus import ModusConfig, metrics, run_modus, score_metrics  # noqa: E402
from modus_plus import ModusPPConfig, run_modus_pp  # noqa: E402

# Seção 4.1 e Tabelas 2/3 do artigo
PRESETS = {
    "aseados": dict(hst_window=2500, hst_trees=150, hst_depth=12, alpha=8.0, tau_min=0.75, tau_max=0.95),
    "ctu13": dict(hst_window=100_000, hst_trees=80, hst_depth=15, alpha=6.0, tau_min=0.40, tau_max=None),
    "edgeiiot": dict(hst_window=100_000, hst_trees=80, hst_depth=15, alpha=6.0, tau_min=0.40, tau_max=None),
    # Configuração única, escolhida a priori e sem olhar resultados: padrões do HS-Trees
    # (Tan et al.: janela 250, 25 árvores, profundidade 15) e a regra do z-score modificado de
    # Iglewicz & Hoaglin (referência do próprio artigo): 0,6745·(s − med)/MAD > 3,5
    # ⇔ s > med + 5,19·MAD; piso 0,5 = limiar padrão de anomalia do HST.
    "fixed": dict(hst_window=250, hst_trees=25, hst_depth=15, alpha=3.5 / 0.6745, tau_min=0.5, tau_max=None),
    # Variante definida DEPOIS de ver o "fixed" no ASEADOS (piso preso em 0,5 com ~24% de FP):
    # mesmo "fixed", mas piso = quantil 99,9% dos scores ao fim do aquecimento.
    "fixed_q": dict(hst_window=250, hst_trees=25, hst_depth=15, alpha=3.5 / 0.6745, tau_min=0.5, tau_max=None,
                    tau_min_quantile=0.999),
    # Variante definida DEPOIS de ver o fixed_q falhar no flood do CTU-13 (janela de 250 envenenada):
    # mesma regra, janela do HST de 10 mil instâncias.
    "fixed_q10k": dict(hst_window=10_000, hst_trees=25, hst_depth=15, alpha=3.5 / 0.6745, tau_min=0.5,
                       tau_max=None, tau_min_quantile=0.999),
}
PAPER = {
    "aseados": {"VP": 51465, "VN": 260406, "FP": 391, "FN": 0, "accuracy": 0.9987,
                "precision": 0.9925, "recall": 1.0, "f1": 0.9962, "elapsed_s": 189.02},
    "ctu13": {"VP": 2088551, "VN": 3440093, "FP": 6796, "FN": 800954, "accuracy": 0.8725,
              "precision": 0.9967, "recall": 0.7228, "f1": 0.8379, "elapsed_s": 2895.26},
    "edgeiiot": {"VP": 6130307, "VN": 21966507, "FP": 574072, "FN": 2249075, "accuracy": 0.9087,
                 "precision": 0.9144, "recall": 0.7316, "f1": 0.8124, "elapsed_s": 14893.37},
}
DEFAULT_NORM = {"aseados": "global", "ctu13": "none", "edgeiiot": "none"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset", choices=list(PAPER))
    ap.add_argument("--name", required=True)
    ap.add_argument("--order", default=None,
                    help="aseados: paper|chronological|file (padrão paper); ctu13: time|file (padrão time)")
    ap.add_argument("--variant", default="paper", choices=["paper", "clean", "all"],
                    help="edgeiiot: paper (normais 2x + Port Scanning), clean (normais 1x + DDoS), "
                         "all (normais 1x + todos os ataques)")
    ap.add_argument("--classes", default="ddos", choices=["ddos", "all"],
                    help="aseados: só Benign+DDoS (artigo) ou todas as classes")
    ap.add_argument("--features", default="paper", choices=["paper", "online", "plus"],
                    help="paper: 4 atributos do artigo; online: os 4 com log1p e Min-Max online; "
                         "plus: online + taxa global e por destino na janela")
    ap.add_argument("--rate-window", type=float, default=1.0, help="janela (s) dos atributos de taxa")
    ap.add_argument("--preset", default=None, choices=list(PRESETS),
                    help="hiperparâmetros (padrão: os do artigo para o dataset)")
    ap.add_argument("--norm", default=None, choices=["global", "none"])
    ap.add_argument("--no-flag", action="store_true")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--warmup", type=int, default=50_000)
    ap.add_argument("--tau-min", type=float, default=None)
    ap.add_argument("--label-in-stream", action="store_true",
                    help="passa o rótulo verdadeiro ao HST do MOA (vazamento; reproduz as rodadas antigas)")
    # MODUS++ (motor numpy, src/modus_plus.py)
    ap.add_argument("--engine", default="moa", choices=["moa", "numpy"],
                    help="moa: HSTrees do CapyMOA (artigo); numpy: src/hst.py, necessário para as melhorias abaixo")
    ap.add_argument("--pad-class-dim", action="store_true",
                    help="numpy: inclui a dimensão constante do atributo de classe (idêntico ao MOA sem rótulo)")
    ap.add_argument("--window-s", type=float, default=None, help="melhoria: janela de referência do HST em segundos")
    ap.add_argument("--warmup-adaptive", action="store_true", help="melhoria: fim do aquecimento por estabilidade (ADWIN)")
    ap.add_argument("--warmup-min", type=int, default=5_000)
    ap.add_argument("--warmup-stable", type=int, default=5_000)
    ap.add_argument("--train-cap", type=float, default=None,
                    help="melhoria: teto de treino/s = fator x quantil 99%% das contagens/s do aquecimento")
    ap.add_argument("--cap-key", default="dst", choices=["global", "dst"])
    ap.add_argument("--frozen", action="store_true", help="melhoria: modelo de referência congelado no aquecimento")
    ap.add_argument("--frozen-q", type=float, default=0.999,
                    help="limiar do modelo congelado: quantil dos scores na calibração (fim do aquecimento)")
    ap.add_argument("--norm-freeze", action="store_true",
                    help="melhoria: Min-Max online congelado ao fim do aquecimento (--warmup)")
    ap.add_argument("--save-model", action="store_true",
                    help="salva o HST final e o congelado em model.npz (só --engine numpy)")
    args = ap.parse_args()
    # MODUS+ normaliza online; não usa a normalização global (que olha o futuro)
    norm = "none" if args.features != "paper" else (args.norm or DEFAULT_NORM[args.dataset])

    out = Path(__file__).parent / "results" / args.dataset / args.name
    out.mkdir(parents=True, exist_ok=True)
    logf = open(out / "log.txt", "w", encoding="utf-8")

    def log(msg):
        print(msg, flush=True)
        logf.write(msg + "\n")
        logf.flush()

    preset = dict(PRESETS[args.preset or args.dataset])
    if args.tau_min is not None:
        preset["tau_min"] = args.tau_min
    improvements = (args.window_s is not None or args.warmup_adaptive or args.train_cap is not None
                    or args.frozen or args.pad_class_dim)
    if improvements and args.engine != "numpy":
        ap.error("as melhorias do MODUS++ exigem --engine numpy")
    if args.engine == "moa":
        cfg = ModusConfig(use_drift_flag=not args.no_flag, seed=args.seed, warmup=args.warmup,
                          label_in_stream=args.label_in_stream, **preset)
    else:
        cfg = ModusPPConfig(use_drift_flag=not args.no_flag, seed=args.seed, warmup=args.warmup,
                            pad_class_dim=args.pad_class_dim, window_s=args.window_s,
                            warmup_adaptive=args.warmup_adaptive, warmup_min=args.warmup_min,
                            warmup_max=args.warmup, warmup_stable=args.warmup_stable,
                            train_cap=args.train_cap, train_cap_key=args.cap_key, frozen=args.frozen,
                            frozen_q=args.frozen_q, **preset)

    if args.dataset == "aseados":
        data = load_aseados(order=args.order or "paper", normalization=norm, classes=args.classes)
    elif args.dataset == "ctu13":
        data = load_ctu13(order=args.order or "time", normalization=norm)
    else:
        data = load_edgeiiot(variant=args.variant, normalization=norm)
    X, y, feats, drift_col = data["X"], data["y"], data["features"], data["drift_col"]
    if args.features != "paper":
        X, feats, drift_col = modus_plus_features(X, feats, data["ts"], data["dst"], args.rate_window,
                                                  rates=args.features == "plus",
                                                  freeze_at=args.warmup if args.norm_freeze else None)
    log(f"run={args.name} dataset={args.dataset} features={args.features} preset={args.preset or args.dataset} "
        f"order={args.order} variant={args.variant} classes={args.classes} norm={norm} "
        f"n={len(y)} ataques={int(y.sum())}")
    log(f"aquecimento: {int(y[:cfg.warmup].sum())} ataques nas primeiras {cfg.warmup} instâncias")
    log(f"atributos: {feats} (ADWIN em {feats[drift_col]})")
    log(f"config: {cfg.to_dict()}")

    if args.engine == "moa":
        r = run_modus(X, y, X[:, drift_col], cfg, feats, log=log)
        w = cfg.warmup
    else:
        r = run_modus_pp(X, data["ts"], data["dst"], X[:, drift_col], cfg, log=log)
        w = r["warmup_end"]

    m_all = metrics(y, r["pred"])           # convenção do artigo: aquecimento conta como "normal"
    m_post = metrics(y[w:], r["pred"][w:])  # só a fase operacional
    m_score = score_metrics(y[w:], r["score"][w:])
    for label, m in [("total (convenção do artigo)", m_all), ("pós-aquecimento", m_post)]:
        log(f"{label}: VP={m['VP']} VN={m['VN']} FP={m['FP']} FN={m['FN']} "
            f"acc={m['accuracy']:.4f} prec={m['precision']:.4f} rec={m['recall']:.4f} f1={m['f1']:.4f}")
    log(f"scores pós-aquecimento: AUC-ROC={m_score['roc_auc']:.4f} PR-AUC={m_score['pr_auc']:.4f}")
    # trecho comum a todas as rodadas (após as 50 mil instâncias do artigo), para comparar aquecimentos
    m_common = metrics(y[cfg.warmup:], r["pred"][cfg.warmup:])
    if w != cfg.warmup:
        log(f"após t={cfg.warmup} (comum): prec={m_common['precision']:.4f} rec={m_common['recall']:.4f} "
            f"f1={m_common['f1']:.4f}")
    poison = None
    if "trained" in r:
        att = y[w:] == 1
        poison = float(r["trained"][w:][att].mean()) if att.any() else 0.0
        log(f"ataques usados no treino (envenenamento): {100 * poison:.2f}%")

    # taxa de alarme por tipo de tráfego (fase operacional): recall para ataques, FPR para benigno
    per_type = {}
    at, pr = data["atype"][w:], r["pred"][w:]
    for code, name in enumerate(data["atype_names"]):
        sel = at == code
        if sel.any():
            per_type[name] = {"n": int(sel.sum()), "alarm_rate": float(pr[sel].mean())}
            log(f"  {name:24s} n={int(sel.sum()):>10,d}  alarmes={100 * pr[sel].mean():6.2f}%")
    log(f"tempo: {r['elapsed_s']:.1f}s (artigo: {PAPER[args.dataset]['elapsed_s']}s)")

    json.dump({"args": vars(args), "norm": norm, "features": feats, "config": cfg.to_dict(),
               "metrics_total": m_all, "metrics_post_warmup": m_post, "score_metrics": m_score,
               "metrics_after_default_warmup": m_common, "warmup_end": int(w), "attacks_trained": poison,
               "engine": args.engine,
               "per_type_post_warmup": per_type, "elapsed_s": r["elapsed_s"],
               "adwin_changes": int(r["flag"].sum()), "paper": PAPER[args.dataset]},
              open(out / "metrics.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    cols = {"t": np.arange(len(y)), "timestamp": data["timestamp"], "label": y, "atype": data["atype"],
            "score": r["score"], "tau": r["tau"], "pred": r["pred"], "flag": r["flag"]}
    if "trained" in r:
        cols.update(trained=r["trained"].astype(np.int8), score_frozen=r["score_frozen"])
    pd.DataFrame(cols).to_csv(out / "scores.csv.gz", index=False)
    if args.save_model and "hst" in r:
        st = r["hst"].state("adaptive_")
        if r["frozen_hst"] is not None:
            st.update(r["frozen_hst"].state("frozen_"))
            st["frozen_W"] = np.array(r["frozen_hst"].W)
        np.savez_compressed(out / "model.npz", **st, features=np.array(feats),
                            adaptive_W=np.array(r["W_norm"]), tau_final=np.array(r["tau"][-1]),
                            tau_frozen=np.array(r["tau_frozen"]), warmup_end=np.array(w),
                            train_cap=np.array(np.nan if r["train_cap"] is None else r["train_cap"]))
        log(f"modelo salvo em {out / 'model.npz'}")
    logf.close()


if __name__ == "__main__":
    main()
