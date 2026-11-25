"""Amostras pequenas dos scores por instância, para versionar no git.

Os scores.csv.gz completos têm de dezenas a centenas de MB e ficam fora do repositório. Aqui, para as
rodadas principais, sorteia 10 mil instâncias (5 mil benignas e 5 mil de ataque, ou todas quando há
menos) com semente fixa e grava results/<base>/<rodada>/amostra.csv.gz, em ordem de chegada.

  python make_samples.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).parent / "results"
RUNS = [
    ("aseados", "paper"), ("aseados", "nl_paper"), ("aseados", "ppq_base"), ("aseados", "ppq_all"),
    ("aseados", "ppq_all_allcls"),
    ("ctu13", "paper"), ("ctu13", "ppq_base"), ("ctu13", "ppq_frozen"), ("ctu13", "ppq_time10cap"),
    ("ctu13", "ppq_all"),
    ("edgeiiot", "nl_clean"), ("edgeiiot", "nl_all_orig"), ("edgeiiot", "ppq_base_all"),
    ("edgeiiot", "ppq_all_all"),
]
PER_CLASS = 5_000


def main():
    rng = np.random.default_rng(0)
    for ds, run in RUNS:
        f = R / ds / run / "scores.csv.gz"
        if not f.exists():
            print("sem scores:", f)
            continue
        d = pd.read_csv(f)
        idx = []
        for lab in (0, 1):
            pos = np.flatnonzero(d.label.to_numpy() == lab)
            idx.append(rng.choice(pos, min(PER_CLASS, len(pos)), replace=False))
        s = d.iloc[np.sort(np.concatenate(idx))]
        out = R / ds / run / "amostra.csv.gz"
        s.to_csv(out, index=False)
        print(f"{out}  {len(s)} de {len(d):,} linhas  ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
