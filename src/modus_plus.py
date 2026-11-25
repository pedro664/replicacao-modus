"""MODUS++: o laço do MODUS (Algoritmo 1) sobre o HST em numpy (src/hst.py), com as melhorias:

1. janela de referência em TEMPO (`window_s`): o HST troca r <- l a cada `window_s` segundos do
   fluxo, e não a cada W instâncias treinadas. Um flood não "acelera" a troca de janela;
2. aquecimento ADAPTATIVO (`warmup_adaptive`): o ADWIN monitora o score do HST durante o
   aquecimento; ele termina quando o score fica `warmup_stable` instâncias sem mudança detectada
   (entre `warmup_min` e `warmup_max`);
3. TETO de treino por intervalo (`train_cap`): no máximo c instâncias treinam por segundo (global ou
   por IP de destino); c = quantil `train_cap_q` das contagens por segundo do aquecimento, sem rótulos;
4. modelo de REFERÊNCIA CONGELADO (`frozen`): um segundo HST treinado só no aquecimento e nunca mais
   atualizado. Alarme se qualquer um dos dois disparar; só treina o que os dois aceitam.

Com window_s=None, warmup_adaptive=False, train_cap=None e frozen=False, o laço é o do MODUS
(mesmas decisões do run_modus com o MOA quando pad_class_dim=True; ver validate_hst.py).
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass

import numpy as np

from hst import HST
from modus import ScoreWindow, adwin_flags


@dataclass
class ModusPPConfig:
    # HST
    hst_window: int = 250            # modo contagem: W instâncias treinadas por janela
    hst_trees: int = 25
    hst_depth: int = 15
    hst_size_limit: float = 0.1
    seed: int = 1
    pad_class_dim: bool = False      # dimensão constante extra (o atributo de classe do MOA)
    window_s: float | None = None    # melhoria 1: janela em segundos (None = contagem, como no MOA)
    min_window_mass: int = 50        # modo tempo: só troca a referência se a janela tiver >= isso
    # ADWIN (flag de mudança de conceito como atributo)
    adwin_delta: float = 0.001
    use_drift_flag: bool = True
    # Limiar MAD
    alpha: float = 3.5 / 0.6745
    tau_min: float = 0.5
    tau_max: float | None = None
    mad_window: int = 5000
    n_min: int = 1000
    tau_min_quantile: float | None = None
    # Aquecimento
    warmup: int = 50_000             # fixo (artigo)
    warmup_adaptive: bool = False    # melhoria 2
    warmup_min: int = 5_000
    warmup_max: int = 50_000
    warmup_stable: int = 5_000
    warmup_delta: float = 0.002
    # Melhoria 3: teto de treino por segundo
    train_cap: float | None = None   # fator sobre o quantil do aquecimento (None = sem teto)
    train_cap_key: str = "dst"       # "global" ou "dst"
    train_cap_q: float = 0.99
    # Melhoria 4: modelo congelado
    frozen: bool = False
    frozen_calib: float = 0.2        # fração final do aquecimento usada só para calibrar o limiar
    frozen_q: float = 0.999

    def to_dict(self) -> dict:
        return asdict(self)


def _cap_from_warmup(ts: np.ndarray, key: np.ndarray, q: float) -> float:
    """Quantil q das contagens de instâncias por (segundo, chave) no aquecimento."""
    sec = np.floor(ts).astype(np.int64)
    _, k = np.unique(key, return_inverse=True)
    _, counts = np.unique(sec * (int(k.max()) + 1) + k, return_counts=True)
    return float(np.quantile(counts, q))


def run_modus_pp(X: np.ndarray, ts: np.ndarray, dst: np.ndarray, drift_values: np.ndarray,
                 cfg: ModusPPConfig, log=print) -> dict:
    t0 = time.perf_counter()
    if cfg.use_drift_flag:
        flags = adwin_flags(drift_values, cfg.adwin_delta)
        Xa = np.column_stack([X, flags])
    else:
        flags = np.zeros(len(X))
        Xa = np.asarray(X, dtype=np.float64)
    if cfg.pad_class_dim:
        Xa = np.column_stack([Xa, np.zeros(len(Xa))])
    Xa = np.ascontiguousarray(Xa, dtype=np.float64)
    log(f"ADWIN: {int(flags.sum())} mudanças detectadas")

    n = len(Xa)
    hst = HST(Xa.shape[1], cfg.hst_trees, cfg.hst_depth, cfg.hst_size_limit, cfg.seed)
    time_mode = cfg.window_s is not None
    win_id = np.floor(ts / cfg.window_s).astype(np.int64) if time_mode else None
    cap_key = np.zeros(n, dtype=np.int64) if cfg.train_cap_key == "global" else np.asarray(dst)
    sec_of = np.floor(ts).astype(np.int64)

    scores = np.empty(n)
    scores_f = np.full(n, np.nan)
    taus = np.empty(n)
    preds = np.zeros(n, dtype=np.int8)
    trained = np.zeros(n, dtype=bool)
    S = ScoreWindow(cfg.mad_window)
    tau = tau_floor = cfg.tau_min

    # estado do HST
    k = 0                      # nº de instâncias treinadas (modo contagem, numInstances do MOA)
    ref_phase = True           # sem referência ainda: score 0,5
    W_norm = float(cfg.hst_window)
    cur_win = win_id[0] if time_mode else None

    # aquecimento / melhorias que dependem dele
    in_warmup = True
    warm_end = None
    adw = None
    last_change = 0
    if cfg.warmup_adaptive:
        from capymoa.drift.detectors import ADWIN
        adw = ADWIN(delta=cfg.warmup_delta)
    cap = None
    cap_sec, cap_cnt = -1, {}
    frozen = None
    tau_f = np.inf

    def end_warmup(t_end: int):
        nonlocal in_warmup, warm_end, tau_floor, cap, frozen, tau_f
        in_warmup, warm_end = False, t_end
        log(f"fim do aquecimento em t={t_end}")
        if cfg.tau_min_quantile is not None:
            tau_floor = float(np.quantile(S.buf[:len(S)], cfg.tau_min_quantile))
            S.dirty = True
            log(f"piso automático (quantil {cfg.tau_min_quantile}): {tau_floor:.4f}")
        if cfg.train_cap is not None:
            cap = max(1.0, cfg.train_cap * _cap_from_warmup(ts[:t_end], cap_key[:t_end], cfg.train_cap_q))
            log(f"teto de treino: {cap:.1f} instâncias/s por {cfg.train_cap_key}")
        if cfg.frozen:
            cut = int(t_end * (1 - cfg.frozen_calib))
            frozen = HST(Xa.shape[1], cfg.hst_trees, cfg.hst_depth, cfg.hst_size_limit, cfg.seed + 1000)
            frozen.add(Xa[:cut], to_reference=True)
            cal = frozen.score(Xa[cut:t_end], cut)
            tau_f = float(np.quantile(cal, cfg.frozen_q))
            frozen.W = cut
            log(f"modelo congelado: {cut} instâncias, limiar {tau_f:.4f} (quantil {cfg.frozen_q} de {t_end - cut})")

    pos = 0
    last_log = 0
    while pos < n:
        # ---- segmento em que a referência r não muda
        if time_mode:
            if win_id[pos] != cur_win:
                # nova janela de tempo: troca a referência se a anterior tem massa suficiente
                if hst.l[0, 0] >= cfg.min_window_mass:
                    hst.swap()
                    W_norm = float(hst.r[0, 0])
                    ref_phase = False
                cur_win = win_id[pos]
            end = int(np.searchsorted(win_id, cur_win, side="right"))
        elif ref_phase:
            end = pos + 1
        else:
            end = min(n, pos + (cfg.hst_window - (k - 1) % cfg.hst_window))
        seg = slice(pos, end)
        per_instance = ref_phase and not time_mode  # massa já somada instância a instância
        if ref_phase:
            s_seg = np.full(end - pos, 0.5)
        else:
            s_seg = hst.score(Xa[seg], W_norm)
        sf_seg = frozen.score(Xa[seg], frozen.W) if frozen is not None else None

        swap_after = None
        for j in range(end - pos):
            t = pos + j
            s = s_seg[j]
            if in_warmup and cfg.warmup_adaptive and not ref_phase:
                adw.add_element(float(s))
                if adw.detected_change():
                    last_change = t
            if in_warmup and (
                (not cfg.warmup_adaptive and t == cfg.warmup) or
                (cfg.warmup_adaptive and not ref_phase and t >= cfg.warmup_min and
                 (t - max(last_change, 0) >= cfg.warmup_stable or t >= cfg.warmup_max))):
                end_warmup(t)
                if frozen is not None:
                    # o restante do segmento precisa do score congelado
                    sf_seg = np.full(end - pos, np.nan)
                    sf_seg[j:] = frozen.score(Xa[t:end], frozen.W)
            if len(S) >= cfg.n_min and S.dirty:
                med, mad = S.median_mad()
                tau = max(tau_floor, med + cfg.alpha * mad)
                if cfg.tau_max is not None:
                    tau = min(cfg.tau_max, tau)
                S.dirty = False
            scores[t], taus[t] = s, tau
            if in_warmup:
                train = True
            else:
                sf = sf_seg[j] if sf_seg is not None else -np.inf
                if sf_seg is not None:
                    scores_f[t] = sf
                if s > tau or sf > tau_f:
                    preds[t] = 1
                    train = False
                else:
                    train = True
                    if cap is not None:
                        if sec_of[t] != cap_sec:
                            cap_sec, cap_cnt = sec_of[t], {}
                        c = cap_cnt.get(cap_key[t], 0)
                        if c >= cap:
                            train = False
                        else:
                            cap_cnt[cap_key[t]] = c + 1
            if not train:
                continue
            trained[t] = True
            S.append(s)
            if time_mode:
                continue  # massa somada em lote no fim do segmento
            if ref_phase:  # fase de referência do MOA: massa direto em r, troca em k == 0
                hst.add(Xa[t:t + 1], to_reference=True)
                if k > 50:
                    ref_phase = False
                if k % cfg.hst_window == 0:
                    hst.swap()
                k += 1
                continue
            k += 1
            if (k - 1) % cfg.hst_window == 0:
                swap_after = t
                break

        stop = (swap_after + 1) if swap_after is not None else end
        if not per_instance:
            hst.add(Xa[np.flatnonzero(trained[pos:stop]) + pos])
        if swap_after is not None:
            hst.swap()
        pos = stop
        if pos - last_log >= 500_000:
            last_log = pos
            log(f"  {pos}/{n} instâncias  ({time.perf_counter() - t0:.1f}s)")

    if in_warmup:
        warm_end = n
    return {"score": scores, "score_frozen": scores_f, "tau": taus, "pred": preds, "flag": flags,
            "trained": trained, "warmup_end": warm_end, "tau_frozen": tau_f, "train_cap": cap,
            "elapsed_s": time.perf_counter() - t0}
