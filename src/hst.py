"""Half-Space Trees em numpy, fiel ao moa.classifiers.oneclass.HSTrees (MOA 24.x, usado pelo CapyMOA).

Por que reimplementar: o HSTrees do MOA só troca a janela de referência por contagem de instâncias
treinadas e normaliza o score pelo tamanho nominal da janela. As melhorias do MODUS++ (janela em
tempo, modelo de referência congelado, teto de treino) precisam controlar a troca de janela e a
massa de referência. Com a mesma semente, este código sorteia as mesmas árvores que o MOA
(`java.util.Random` reproduzido bit a bit) e dá os mesmos scores (ver `validate_hst.py`).

Detalhes do MOA reproduzidos de propósito:
- espaço de trabalho por dimensão: s ~ U[0,1], [s - 2·max(s, 1-s), s + 2·max(s, 1-s)];
- corte no ponto médio do atributo sorteado; os vetores mín/máx são compartilhados entre os nós e
  o construtor restaura o máx após o filho esquerdo, mas não restaura o mín após o direito;
- raiz na profundidade 1, folhas na profundidade `max_depth`;
- score de uma árvore = r·2^prof no primeiro nó com r <= ceil(size_limit·W) (ou na folha);
  score final = 1 - média_árvores(score / (W·2^max_depth));
- modo contagem: o 1º treino zera a janela, as instâncias 1..51 entram direto na referência
  (score 0,5 até lá), e a referência é trocada a cada W treinos (r <- l, l <- 0).
"""

from __future__ import annotations

import math

import numpy as np

_MASK48 = (1 << 48) - 1
_MULT = 0x5DEECE66D


class JavaRandom:
    """java.util.Random (LCG de 48 bits); só o necessário para nextDouble()."""

    def __init__(self, seed: int):
        self.seed = (seed ^ _MULT) & _MASK48

    def _next(self, bits: int) -> int:
        self.seed = (self.seed * _MULT + 0xB) & _MASK48
        return self.seed >> (48 - bits)

    def next_double(self) -> float:
        return ((self._next(26) << 27) + self._next(27)) * (1.0 / (1 << 53))


class HST:
    """Floresta de Half-Space Trees em vetores (árvore completa em heap: filhos de i são 2i+1, 2i+2).

    `score(X)` usa a massa de referência r (fixa entre trocas); `add(X)` soma massa à janela
    corrente l (ou a r durante a fase de referência inicial do MOA); `swap()` faz r <- l.
    """

    def __init__(self, n_dims: int, n_trees: int = 25, max_depth: int = 15, size_limit: float = 0.1,
                 seed: int = 1):
        self.T, self.D, self.d = n_trees, max_depth, n_dims
        self.size_limit = size_limit
        self.n_nodes = (1 << max_depth) - 1
        self.attr = np.full((n_trees, self.n_nodes), -1, dtype=np.int32)
        self.split = np.zeros((n_trees, self.n_nodes))
        rnd = JavaRandom(seed)
        for t in range(n_trees):
            mn, mx = np.empty(n_dims), np.empty(n_dims)
            for k in range(n_dims):
                s = rnd.next_double()
                w = 2.0 * max(s, 1.0 - s)
                mn[k], mx[k] = s - w, s + w
            self._build(t, 0, 1, mn, mx, rnd)
        self.r = np.zeros((n_trees, self.n_nodes), dtype=np.int64)
        self.l = np.zeros((n_trees, self.n_nodes), dtype=np.int64)
        # profundidade de cada posição do heap (raiz = 1)
        self.depth_of = np.floor(np.log2(np.arange(self.n_nodes) + 1)).astype(np.int64) + 1

    def _build(self, t: int, i: int, depth: int, mn: np.ndarray, mx: np.ndarray, rnd: JavaRandom):
        # Recursão em pré-ordem, igual ao construtor de HSTreeNode (consome o RNG na mesma ordem).
        if depth >= self.D:
            return
        a = int(math.floor(rnd.next_double() * self.d))
        sv = (mn[a] + mx[a]) / 2.0
        self.attr[t, i], self.split[t, i] = a, sv
        tmp = mx[a]
        mx[a] = sv
        self._build(t, 2 * i + 1, depth + 1, mn, mx, rnd)
        mx[a] = tmp
        mn[a] = sv  # não restaurado, como no MOA
        self._build(t, 2 * i + 2, depth + 1, mn, mx, rnd)

    # ------------------------------------------------------------------ massa
    def _paths(self, X: np.ndarray):
        """Gera, nível a nível, o índice do nó (T, n) que cada instância visita."""
        n = len(X)
        idx = np.zeros((self.T, n), dtype=np.int64)
        rows = np.arange(self.T)[:, None]
        cols = np.arange(n)[None, :]
        for depth in range(1, self.D + 1):
            yield idx
            if depth == self.D:
                return
            a = self.attr[rows, idx]
            go_right = X[cols, a] > self.split[rows, idx]
            idx = 2 * idx + 1 + go_right

    def _add_mass(self, target: np.ndarray, X: np.ndarray):
        flat = target.reshape(-1)  # visão (target é contíguo)
        off = (np.arange(self.T) * self.n_nodes)[:, None]
        big = len(X) * self.D > self.n_nodes  # lote grande: bincount; pequeno: add.at
        for idx in self._paths(X):
            if big:
                flat += np.bincount((idx + off).ravel(), minlength=flat.size)
            else:
                np.add.at(flat, (idx + off).ravel(), 1)

    def add(self, X: np.ndarray, to_reference: bool = False):
        if len(X):
            self._add_mass(self.r if to_reference else self.l, X)

    def state(self, prefix: str = "") -> dict:
        """Arrays que definem o modelo (estrutura das árvores e massas), para np.savez."""
        return {f"{prefix}attr": self.attr, f"{prefix}split": self.split, f"{prefix}r": self.r,
                f"{prefix}l": self.l, f"{prefix}shape": np.array([self.T, self.D, self.d]),
                f"{prefix}size_limit": np.array(self.size_limit)}

    def swap(self):
        self.r, self.l = self.l, np.zeros_like(self.l)

    # ------------------------------------------------------------------ score
    def score(self, X: np.ndarray, window: float, chunk: int = 200_000) -> np.ndarray:
        """Score de anomalia (0..1) de cada linha de X com a massa de referência r atual.

        `window` é o W da normalização: o tamanho nominal da janela (modo contagem, como no MOA)
        ou a massa real da referência (modo tempo / modelo congelado).
        """
        out = np.empty(len(X))
        limit = math.ceil(self.size_limit * window)
        norm = window * 2.0 ** self.D * self.T
        rows = np.arange(self.T)[:, None]
        for s in range(0, len(X), chunk):
            Xc = X[s:s + chunk]
            n = len(Xc)
            cols = np.arange(n)[None, :]
            idx = np.zeros((self.T, n), dtype=np.int64)
            for depth in range(1, self.D):
                rr = self.r[rows, idx]
                a = self.attr[rows, idx]
                descend = rr > limit
                if not descend.any():
                    break
                go_right = Xc[cols, a] > self.split[rows, idx]
                idx = np.where(descend, 2 * idx + 1 + go_right, idx)
            tot = (self.r[rows, idx] * (2.0 ** self.depth_of[idx])).sum(axis=0)
            out[s:s + n] = 1.0 - tot / norm
        return out
