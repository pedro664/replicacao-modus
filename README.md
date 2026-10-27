# Replicação do MODUS (SBSeg 2026)

Dutra, Nakayama, Nogueira — "Um Método para Detecção Online Não Supervisionada de Ataques DDoS em
Fluxos de Dados". https://sol.sbc.org.br/index.php/sbseg/article/view/44353

Reimplementação do MODUS (ADWIN + Half-Space Trees + limiar MAD, via CapyMOA), replicação nas três
bases do artigo, análise crítica e melhorias propostas. Não há código dos autores; tudo aqui foi
escrito do zero a partir do texto do artigo.

## Resultados

| Base | F1 artigo | F1 replicação | Situação |
|---|---|---|---|
| ASEADOS-SDN-IoT | 99,62% | 99,73% | Replica, mas só com a ordem gerada por um erro de parse de data |
| CTU-13 (cenário 11) | 83,79% | 64,55% | Não replica; rótulos do artigo inconsistentes |
| Edge-IIoTset | 81,24% | 84,33% | Replica: VP e FN idênticos ao artigo |

Principais achados: a flag do ADWIN (contribuição central) não muda o resultado; sem normalização o
HST separa por protocolo, não por volume; o limiar fica preso num piso ajustado à mão. Com atributos
de taxa por janela e normalização online (MODUS+), o F1 no Edge-IIoT com 14 tipos de ataque sobe de
76,66% para 91,05%.

- [`results/comparacao.md`](results/comparacao.md) — replicação vs. artigo
- [`results/melhorias.md`](results/melhorias.md) — melhorias propostas e limites
- [`results/tabela_rodadas.md`](results/tabela_rodadas.md) — todas as 38 rodadas
- `results/<base>/summary.md` — achados por base; `results/<base>/<rodada>/` — log e métricas

Os datasets não estão no repositório (tamanho e licenças de terceiros); veja abaixo como obtê-los.
Os scores por instância (`scores.csv.gz`) também ficaram de fora e são regenerados por `run.py`.

## Ambiente

Requer Python 3.13 e Java 11+ (CapyMOA usa o MOA via JPype).

```
py -3.13 -m venv .venv
.venv/Scripts/python -m pip install capymoa pandas matplotlib
```

## Dados

- ASEADOS-SDN-IoT: `data/aseados/ASEADOS_SDN_IoT.csv` (https://aseados.ucd.ie/datasets/SDN-IoT/)
- CTU-13 cenário 11: `data/ctu13/capture20110818-2.truncated.pcap` (pcapng com payload truncado,
  https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-52/). Converter uma vez:

```
.venv/Scripts/python src/pcap_to_npz.py data/ctu13/capture20110818-2.truncated.pcap data/ctu13/c11_packets.npz
```

- Edge-IIoTset: zip do Kaggle (login necessário,
  https://www.kaggle.com/datasets/mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot).
  Extrair os pcaps de `Normal traffic/` para `data/edgeiiot/normal/`, os 4 pcaps `DDoS*` para
  `data/edgeiiot/ddos/` e os demais pcaps de `Attack traffic/` para `data/edgeiiot/other/`; converter
  cada um com `--all-frames` (o artigo conta também ARP e IPv6):

```
.venv/Scripts/python src/pcap_to_npz.py "data/edgeiiot/ddos/DDoS UDP Flood Attacks.pcap" "data/edgeiiot/ddos/DDoS UDP Flood Attacks.npz" --all-frames
```

## Rodar

```
.venv/Scripts/python run.py aseados --name paper
.venv/Scripts/python run.py aseados --name chronological --order chronological
.venv/Scripts/python run.py aseados --name no_flag --no-flag
.venv/Scripts/python run.py ctu13 --name paper
.venv/Scripts/python run.py ctu13 --name norm_global --norm global
.venv/Scripts/python run.py edgeiiot --name paper --variant paper
.venv/Scripts/python run.py edgeiiot --name clean --variant clean
.venv/Scripts/python plot_run.py results/aseados/paper
```

Melhorias (atributos `online`/`plus`, config fixa `--preset`, teste com todos os ataques):

```
.venv/Scripts/python run.py ctu13 --name cfg_aseados --preset aseados
.venv/Scripts/python run.py aseados --name fixedq_plus --preset fixed_q --features plus
.venv/Scripts/python run.py edgeiiot --name all_orig --variant all
.venv/Scripts/python run.py edgeiiot --name all_fixed_plus --variant all --preset fixed --features plus
.venv/Scripts/python summarize.py
```

Os hiperparâmetros de cada dataset (Seção 4.1 do artigo) e as configs fixas ficam em `PRESETS` no `run.py`.
Cada rodada salva em `results/<dataset>/<nome>/`: `log.txt`, `metrics.json`, `scores.csv.gz`
(score, limiar, predição e flag ADWIN por instância). Resumo e achados: `results/<dataset>/summary.md`.

## Código

- `src/pcap_to_npz.py` — Fase (a) para pcap/pcapng: extrai portas, tamanho, protocolo, IPs por pacote.
- `src/datasets.py` — Fase (a): ordenação, seleção de atributos, rótulos, normalização.
- `src/modus.py` — Fases (b) e (c): ADWIN → flag, HST, limiar MAD, Test-Then-Train seletivo.
- `src/features.py` — melhorias: taxa por janela (global e por destino) e Min-Max online.
- `run.py` — roda uma configuração e salva log, métricas e scores; `summarize.py` monta a tabela geral.
- `plot_run.py`, `figures_slides.py` — figuras por rodada e as da apresentação (`results/figs/`).
