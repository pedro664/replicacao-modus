"""Monta results/tabela_rodadas.md com todas as rodadas (lê results/<dataset>/<nome>/metrics.json)."""

import json
from pathlib import Path

ROOT = Path(__file__).parent / "results"


def pct(x):
    return "–" if x is None or x != x else f"{100 * x:.2f}"


rows = []
for f in sorted(ROOT.glob("*/*/metrics.json")):
    j = json.loads(f.read_text(encoding="utf-8"))
    a, m, sm = j["args"], j["metrics_post_warmup"], j.get("score_metrics", {})
    conj = {"aseados": f"{a.get('classes', 'ddos')}, ordem {a.get('order') or 'paper'}",
            "ctu13": "ddos", "edgeiiot": a.get("variant", "paper")}[f.parts[-3]]
    tipos = ", ".join(f"{k} {100 * v['alarm_rate']:.0f}%" for k, v in j.get("per_type_post_warmup", {}).items())
    rows.append(f"| {f.parts[-3]} | {f.parts[-2]} | {a.get('features', 'paper')} | "
                f"{a.get('preset') or f.parts[-3]} | {'não' if a.get('no_flag') else 'sim'} | {conj} | "
                f"{pct(m['precision'])} | {pct(m['recall'])} | {pct(m['f1'])} | "
                f"{pct(sm.get('roc_auc'))} | {pct(sm.get('pr_auc'))} | {j['elapsed_s']:.0f} | "
                f"{m['VP'] + m['VN'] + m['FP'] + m['FN'] + j['config']['warmup']:,} | {tipos} |")

head = ("# Todas as rodadas\n\nMétricas da fase operacional (pós-aquecimento). Alarmes por tipo: recall para "
        "ataques, taxa de falso positivo para benigno.\n\n"
        "Tempo = segundos do laço MODUS (ADWIN + HST + limiar), sem carregar dados nem gravar saídas.\n\n"
        "| dataset | rodada | atributos | config | flag | conjunto | Prec % | Rec % | F1 % | AUC-ROC % | "
        "PR-AUC % | tempo s | instâncias | alarmes por tipo |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
(ROOT / "tabela_rodadas.md").write_text(head + "\n".join(rows) + "\n", encoding="utf-8")
print(f"{len(rows)} rodadas -> results/tabela_rodadas.md")
