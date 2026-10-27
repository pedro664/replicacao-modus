"""Melhorias propostas (MODUS+): atributos de taxa por janela e normalização online.

Tudo aqui é causal: o valor na instância t depende só das instâncias 1..t, então pré-computar
as colunas equivale a calculá-las dentro do laço de passagem única.
"""

from __future__ import annotations

import numpy as np


def window_counts(ts: np.ndarray, window_s: float, key: np.ndarray | None = None) -> np.ndarray:
    """Nº de instâncias (incluindo a atual) nos últimos `window_s` segundos.

    Com `key`, conta só as instâncias com a mesma chave (ex.: mesmo IP de destino).
    `ts` precisa estar em ordem não decrescente (a ordem do fluxo).
    """
    n = len(ts)
    t = ts - ts[0]
    if key is None:
        return np.arange(1, n + 1) - np.searchsorted(t, t - window_s, side="right") + 0.0
    # Ordena por (chave, posição no fluxo); dentro de cada chave o tempo segue não decrescente,
    # então uma chave composta monotônica permite um único searchsorted.
    _, k = np.unique(key, return_inverse=True)
    order = np.lexsort((np.arange(n), k))
    span = t[-1] + window_s + 1.0
    comp = k[order] * span + t[order]
    pos = np.arange(n)
    first = np.searchsorted(comp, comp - window_s, side="right")
    out = np.empty(n)
    out[order] = pos - first + 1
    return out


def online_minmax(X: np.ndarray) -> np.ndarray:
    """Min-Max causal: cada coluna escalada pelo mín/máx observados até a instância atual."""
    lo = np.minimum.accumulate(X, axis=0)
    hi = np.maximum.accumulate(X, axis=0)
    rng = hi - lo
    return np.where(rng > 0, (X - lo) / np.where(rng > 0, rng, 1.0), 0.0)


def modus_plus_features(X: np.ndarray, names: list[str], ts: np.ndarray, dst: np.ndarray,
                        window_s: float = 1.0, rates: bool = True) -> tuple[np.ndarray, list[str], int]:
    """Atributos do MODUS+: os 4 originais + taxa global e taxa por destino, com log1p nos
    atributos de magnitude (tamanho e taxas) e Min-Max online em todos.
    rates=False dá só a normalização online dos 4 originais (ablação).

    Retorna (X+, nomes, índice da coluna monitorada pelo ADWIN).
    """
    size_col = names.index("length")
    Xr = X.astype(np.float64).copy()
    Xr[:, size_col] = np.log1p(Xr[:, size_col])
    if not rates:
        return online_minmax(Xr), list(names), size_col
    rate_all = window_counts(ts, window_s)
    rate_dst = window_counts(ts, window_s, key=dst)
    Xp = np.column_stack([Xr, np.log1p(rate_all), np.log1p(rate_dst)])
    return online_minmax(Xp), list(names) + ["rate_all", "rate_dst"], size_col
