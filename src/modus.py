"""Reimplementação do MODUS (Dutra, Nakayama, Nogueira — SBSeg 2026).

Fase (b): ADWIN monitora o tamanho do pacote/fluxo e gera uma flag binária de
mudança de conceito, concatenada ao vetor de atributos.
Fase (c): Half-Space Trees (CapyMOA) pontua cada instância; limiar dinâmico
tau = clip(mediana(S) + alpha * MAD(S), piso, teto) sobre uma janela de scores S;
aquecimento de B instâncias; Test-Then-Train treinando só com o que foi
predito como benigno (Algoritmo 1 do artigo).
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass

import numpy as np


def _median_inplace(a: np.ndarray) -> float:
    """Mediana igual à de np.median, mas reordenando `a` no lugar (sem cópia)."""
    n = len(a)
    h = n // 2
    if n % 2:
        a.partition(h)
        return float(a[h])
    a.partition((h - 1, h))
    return 0.5 * (float(a[h - 1]) + float(a[h]))


class ScoreWindow:
    """Janela deslizante S de scores com limiar MAD (Eq. 2 e 3), em buffer circular.

    Só recalcula tau quando S muda; o valor é idêntico a
    median(S) + alpha * median(|S - median(S)|).
    """

    def __init__(self, size: int):
        self.buf = np.empty(size)
        self.tmp = np.empty(size)
        self.n = self.pos = 0
        self.dirty = True

    def __len__(self):
        return self.n

    def append(self, s: float):
        self.buf[self.pos] = s
        self.pos = (self.pos + 1) % len(self.buf)
        self.n = min(self.n + 1, len(self.buf))
        self.dirty = True

    def median_mad(self) -> tuple[float, float]:
        w, t = self.buf[:self.n], self.tmp[:self.n]
        np.copyto(t, w)
        med = _median_inplace(t)
        np.subtract(w, med, out=t)
        np.abs(t, out=t)
        return med, _median_inplace(t)


@dataclass
class ModusConfig:
    # HST
    hst_window: int = 2500
    hst_trees: int = 150
    hst_depth: int = 12
    hst_size_limit: float = 0.1
    seed: int = 1
    # ADWIN
    adwin_delta: float = 0.001
    use_drift_flag: bool = True
    # Limiar MAD
    alpha: float = 8.0
    tau_min: float = 0.75
    tau_max: float | None = 0.95
    mad_window: int = 5000
    n_min: int = 1000  # não informado no artigo; irrelevante após o aquecimento (B >> mad_window)
    # Melhoria: piso automático = quantil dos scores da janela S ao fim do aquecimento (sem rótulos).
    # None mantém o piso fixo tau_min, como no artigo.
    tau_min_quantile: float | None = None
    # Aquecimento
    warmup: int = 50_000

    def to_dict(self) -> dict:
        return asdict(self)


def adwin_flags(values: np.ndarray, delta: float) -> np.ndarray:
    """Fase (b): flag_t = 1 se o ADWIN detecta mudança ao receber values[t].

    É causal (depende só de values[:t+1]), então pré-computar a coluna equivale
    a calculá-la dentro do laço principal.
    """
    from capymoa.drift.detectors import ADWIN

    det = ADWIN(delta=delta)
    flags = np.zeros(len(values), dtype=np.float64)
    for t, v in enumerate(values):
        det.add_element(float(v))
        if det.detected_change():
            flags[t] = 1.0
    return flags


def run_modus(X: np.ndarray, y: np.ndarray, drift_values: np.ndarray, cfg: ModusConfig,
              feature_names: list[str], log=print) -> dict:
    """Executa o MODUS em passagem única sobre X (já ordenado e pré-processado).

    Retorna arrays por instância (score, tau, pred, flag) e o tempo total.
    """
    from capymoa.anomaly import HalfSpaceTrees
    from capymoa.stream import NumpyStream

    t0 = time.perf_counter()
    if cfg.use_drift_flag:
        flags = adwin_flags(drift_values, cfg.adwin_delta)
        Xa = np.column_stack([X, flags])
        names = list(feature_names) + ["drift_flag"]
    else:
        flags = np.zeros(len(X))
        Xa = X
        names = list(feature_names)
    log(f"ADWIN: {int(flags.sum())} mudanças detectadas")

    stream = NumpyStream(Xa.astype(np.float64), y.astype(int), feature_names=names)
    hst = HalfSpaceTrees(stream.get_schema(), random_seed=cfg.seed, window_size=cfg.hst_window,
                         number_of_trees=cfg.hst_trees, max_depth=cfg.hst_depth,
                         size_limit=cfg.hst_size_limit)

    n = len(Xa)
    scores = np.empty(n)
    taus = np.empty(n)
    preds = np.zeros(n, dtype=np.int8)
    S = ScoreWindow(cfg.mad_window)
    tau = tau_floor = cfg.tau_min

    t = 0
    while stream.has_more_instances():
        inst = stream.next_instance()
        s = float(hst.score_instance(inst))
        if t == cfg.warmup and cfg.tau_min_quantile is not None:
            tau_floor = float(np.quantile(S.buf[:len(S)], cfg.tau_min_quantile))
            log(f"piso automático (quantil {cfg.tau_min_quantile} do aquecimento): {tau_floor:.4f}")
            S.dirty = True
        if len(S) >= cfg.n_min and S.dirty:
            med, mad = S.median_mad()
            tau = max(tau_floor, med + cfg.alpha * mad)
            if cfg.tau_max is not None:
                tau = min(cfg.tau_max, tau)
            S.dirty = False
        scores[t], taus[t] = s, tau
        if t < cfg.warmup:
            hst.train(inst)
            S.append(s)
        elif s > tau:
            preds[t] = 1  # ataque: descartado do treino e da janela S
        else:
            hst.train(inst)
            S.append(s)
        t += 1
        if t % 50_000 == 0:
            log(f"  {t}/{n} instâncias  ({time.perf_counter() - t0:.1f}s)")

    return {"score": scores, "tau": taus, "pred": preds, "flag": flags,
            "elapsed_s": time.perf_counter() - t0}


def score_metrics(y: np.ndarray, score: np.ndarray) -> dict:
    """Métricas independentes de limiar: AUC-ROC (com empates) e PR-AUC (average precision)."""
    pos = int(y.sum())
    neg = len(y) - pos
    if pos == 0 or neg == 0:
        return {"roc_auc": float("nan"), "pr_auc": float("nan")}
    order = np.argsort(score, kind="mergesort")
    s = score[order]
    # postos médios para empates
    starts = np.r_[0, np.flatnonzero(np.diff(s)) + 1]
    ends = np.r_[starts[1:], len(s)]
    avg = (starts + ends + 1) / 2.0
    ranks = np.empty(len(s))
    ranks[order] = np.repeat(avg, ends - starts)
    roc = (ranks[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg)
    # average precision agrupando scores empatados (ordem decrescente)
    yd = y[order][::-1]
    sd = s[::-1]
    grp = np.r_[np.flatnonzero(np.diff(sd)), len(sd) - 1]
    tp = np.cumsum(yd)[grp]
    fp = (grp + 1) - tp
    prec = tp / (tp + fp)
    rec = tp / pos
    ap = float(np.sum(np.diff(np.r_[0.0, rec]) * prec))
    return {"roc_auc": float(roc), "pr_auc": ap}


def metrics(y: np.ndarray, pred: np.ndarray) -> dict:
    tp = int(((pred == 1) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    acc = (tp + tn) / max(1, tp + tn + fp + fn)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"VP": tp, "VN": tn, "FP": fp, "FN": fn, "accuracy": acc, "precision": prec,
            "recall": rec, "f1": f1}
