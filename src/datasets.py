"""Fase (a) do MODUS: ordenação temporal, seleção/codificação de atributos e vetorização.

Todos os carregadores devolvem um dicionário com:
  X (atributos do artigo), y (0/1), features, drift_col, timestamp (para os CSVs de saída),
  ts (segundos, ordem do fluxo), dst (chave do destino, para a taxa por destino),
  atype (código do tipo de tráfego por instância) e atype_names.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _minmax_global(X: np.ndarray) -> np.ndarray:
    lo, hi = X.min(axis=0), X.max(axis=0)
    return (X - lo) / np.where(hi > lo, hi - lo, 1.0)


def _normalize(X: np.ndarray, normalization: str) -> np.ndarray:
    if normalization == "global":
        return _minmax_global(X)
    if normalization != "none":
        raise ValueError(normalization)
    return X


def _codes(labels) -> tuple[np.ndarray, list[str]]:
    names, codes = np.unique(np.asarray(labels), return_inverse=True)
    return codes.astype(np.int16), [str(n) for n in names]


# ---------------------------------------------------------------- ASEADOS-SDN-IoT

ASEADOS_CSV = ROOT / "data" / "aseados" / "ASEADOS_SDN_IoT.csv"
# Artigo: "porta de origem, porta de destino, protocolo e tamanho médio dos pacotes do fluxo"
ASEADOS_FEATURES = ["Src Port", "Dst Port", "Protocol", "Pkt Size Avg"]


def load_aseados(order: str = "paper", normalization: str = "global", classes: str = "ddos") -> dict:
    """Carrega o ASEADOS-SDN-IoT.

    order:
      - "paper": parse de data "misto" do pandas (mês/dia quando possível). É a única
        ordenação que reproduz FN = 0 do artigo: 10/03 e 12/03 viram 3/out e 3/dez,
        jogando o DDoS para depois de 233 mil benignos.
      - "chronological": parse correto dd/mm/aaaa (os ataques ocorrem antes do benigno).
      - "file": ordem do CSV.
    normalization: "global" (Min-Max com mín/máx do conjunto inteiro, como no artigo) ou "none".
    classes: "ddos" (Benign + DDoS, como no artigo) ou "all" (todas as classes; ataque = não-Benign).
    """
    df = pd.read_csv(ASEADOS_CSV, usecols=ASEADOS_FEATURES + ["Timestamp", "Label", "Dst IP"])
    if classes == "ddos":
        df = df[df["Label"].isin(["Benign", "DDoS"])]
    elif classes != "all":
        raise ValueError(classes)
    df = df.reset_index(drop=True)

    if order == "paper":
        ts = pd.to_datetime(df["Timestamp"], format="mixed")
    elif order == "chronological":
        ts = pd.to_datetime(df["Timestamp"], format="%d/%m/%Y %I:%M:%S %p")
    elif order == "file":
        ts = pd.Series(pd.to_datetime(np.arange(len(df)), unit="s"))
    else:
        raise ValueError(order)
    df = df.assign(_ts=ts).sort_values("_ts", kind="stable").reset_index(drop=True)

    X = _normalize(df[ASEADOS_FEATURES].to_numpy(dtype=np.float64), normalization)
    y = (df["Label"] != "Benign").to_numpy(dtype=np.int8)
    secs = (df["_ts"] - df["_ts"].iloc[0]).dt.total_seconds().to_numpy()
    atype, names = _codes(df["Label"])
    return {"X": X, "y": y, "features": ["sport", "dport", "proto", "length"], "drift_col": 3,
            "timestamp": df["_ts"].astype(str).to_numpy(), "ts": secs,
            "dst": _codes(df["Dst IP"])[0], "atype": atype, "atype_names": names}


# ---------------------------------------------------------------- CTU-13 cenário 11

CTU13_NPZ = ROOT / "data" / "ctu13" / "c11_packets.npz"
# README do cenário 11 (CTU-Malware-Capture-Botnet-52): hosts infectados com o RBot
CTU13_BOTS = ["147.32.84.165", "147.32.84.191", "147.32.84.192"]


def load_ctu13(order: str = "time", normalization: str = "none") -> dict:
    """CTU-13 cenário 11 em nível de pacote (6.336.394 pacotes IPv4 do pcap truncado).

    Rótulo: ataque se origem ou destino é um host infectado (regra do CTU-13); Background
    e Normal são benignos, como no artigo. Gerar o .npz com src/pcap_to_npz.py.
    """
    import ipaddress

    d = np.load(CTU13_NPZ)
    idx = np.argsort(d["ts"], kind="stable") if order == "time" else np.arange(len(d["ts"]))
    bots = np.array([int(ipaddress.IPv4Address(a)) for a in CTU13_BOTS], dtype=np.uint32)
    y = (np.isin(d["src"], bots) | np.isin(d["dst"], bots))[idx].astype(np.int8)
    proto = np.unique(d["proto"], return_inverse=True)[1]  # codificação discreta do protocolo
    X = np.column_stack([d["sport"], d["dport"], d["length"], proto]).astype(np.float64)[idx]
    ts = d["ts"][idx] - d["ts"][idx][0]
    return {"X": _normalize(X, normalization), "y": y, "features": ["sport", "dport", "length", "proto"],
            "drift_col": 2, "timestamp": np.round(ts, 6), "ts": ts, "dst": d["dst"][idx],
            "atype": y.astype(np.int16), "atype_names": ["Benign", "Botnet"]}


# ---------------------------------------------------------------- Edge-IIoTset

EDGE_DIR = ROOT / "data" / "edgeiiot"


def _edge_type(path: Path) -> str:
    n = path.stem.lower()
    for key, name in [("http", "DDoS_HTTP"), ("icmp", "DDoS_ICMP"), ("tcp syn", "DDoS_TCP"),
                      ("udp", "DDoS_UDP"), ("backdoor", "Backdoor"), ("mitm", "MITM"),
                      ("fingerprint", "Fingerprinting"), ("password", "Password"),
                      ("port scan", "Port_Scanning"), ("ransomware", "Ransomware"),
                      ("sql", "SQL_injection"), ("upload", "Uploading"),
                      ("vulnerability", "Vulnerability_scanner"), ("xss", "XSS")]:
        if key in n:
            return name
    raise ValueError(path)


def load_edgeiiot(variant: str = "paper", normalization: str = "none") -> dict:
    """Edge-IIoTset em nível de pacote (todos os quadros dos pcaps, ordenados por tempo).

    Rótulo por arquivo: pacotes dos pcaps de ataque = ataque.
    variant:
      - "paper": reproduz as 30.919.961 instâncias do artigo = pcaps normais DUAS vezes
        + Port Scanning (como benigno) + DDoS. Única combinação encontrada que fecha os negativos
        (22.540.579) exatamente.
      - "clean": pcaps normais uma vez + DDoS (19.638.007).
      - "all": pcaps normais uma vez + todos os 14 ataques (teste com ataques não-DDoS).
    Gerar os .npz com src/pcap_to_npz.py --all-frames.
    """
    normal = sorted((EDGE_DIR / "normal").glob("*.npz"))
    ddos = sorted((EDGE_DIR / "ddos").glob("*.npz"))
    other = sorted((EDGE_DIR / "other").glob("*.npz"))
    files = [(f, 0, "Normal") for f in normal] + [(f, 1, _edge_type(f)) for f in ddos]
    if variant == "paper":
        files += [(f, 0, "Normal") for f in normal]
        files += [(EDGE_DIR / "other" / "Port Scanning attack.npz", 0, "Normal")]
    elif variant == "all":
        files += [(f, 1, _edge_type(f)) for f in other]
    elif variant != "clean":
        raise ValueError(variant)
    names = sorted({t for _, _, t in files})
    parts = []
    for f, lab, typ in files:
        d = np.load(f)
        n = len(d["ts"])
        parts.append((d["ts"], np.column_stack([d["sport"], d["dport"], d["length"], d["proto"]]),
                      np.full(n, lab, np.int8), np.full(n, names.index(typ), np.int16), d["dst"]))
    ts = np.concatenate([p[0] for p in parts])
    idx = np.argsort(ts, kind="stable")
    X = np.concatenate([p[1] for p in parts])[idx].astype(np.float64)
    X[:, 3] = np.unique(X[:, 3], return_inverse=True)[1]  # codificação discreta do protocolo
    ts = ts[idx] - ts[idx][0]
    return {"X": _normalize(X, normalization), "y": np.concatenate([p[2] for p in parts])[idx],
            "features": ["sport", "dport", "length", "proto"], "drift_col": 2,
            "timestamp": np.round(ts, 6), "ts": ts, "dst": np.concatenate([p[4] for p in parts])[idx],
            "atype": np.concatenate([p[3] for p in parts])[idx], "atype_names": names}
