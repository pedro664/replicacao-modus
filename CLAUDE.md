# CLAUDE.md — guia do repositório

Projeto da disciplina Auditoria e Segurança de SI (CIn/UFPE). Replica e estende o MODUS, um detector
online e não supervisionado de DDoS (Dutra, Nakayama e Nogueira, SBSeg 2026). Não há código dos
autores: tudo foi escrito a partir do texto do artigo.

- **Etapa 1** (commit `3ecaabf`): replicação nas três bases, comparação com o artigo, melhorias propostas.
- **Etapa 2** (branch `etapa2-melhorias`): implementação das melhorias (MODUS++), descoberta e
  correção do vazamento de rótulo, slides e artigo IEEE.

## Estrutura

```
src/
  pcap_to_npz.py   pcap/pcapng -> npz (portas, tamanho, protocolo, IPs, timestamp por pacote)
  datasets.py      carga das 3 bases: ordenação, atributos, rótulos, normalização (Fase a)
  modus.py         MODUS original: ADWIN -> flag, HST do MOA (CapyMOA), limiar MAD,
                   test-then-train seletivo (Fases b e c). ModusConfig, run_modus, metrics
  features.py      atributos MODUS+: log1p, Min-Max online (com freeze_at), rate_all, rate_dst
  hst.py           Half-Space Trees em numpy, bit a bit igual ao HSTrees do MOA
                   (reproduz o java.util.Random). Suporta lote, troca de referência e janela em tempo
  modus_plus.py    MODUS++: ModusPPConfig e run_modus_pp (todas as melhorias da Etapa 2)
run.py             roda uma configuração e salva em results/<base>/<nome>/
summarize.py       tabela de todas as rodadas -> results/tabela_rodadas.md (Etapa 1)
summarize_pp.py    tabela da Etapa 2 (lista RUNS) -> results/modus_pp.md, com AUC e F1 oráculo
validate_hst.py    compara src/hst.py com o MOA (diferença máxima esperada ~1e-16)
plot_run.py        figura score x limiar de uma rodada
figures_slides.py  figuras dos slides da Etapa 1 (results/figs/)
paper_figs.py      figuras do artigo (paper/figs/*.pdf)
slides_etapa2.py   gera Replicacao_MODUS_CIn_Etapa2.pptx a partir do deck da Etapa 1
paper/             artigo IEEE (main.tex, refs.bib, sections/, figs/)
results/           insumos de todas as rodadas (ver abaixo)
data/              datasets (link simbólico, fora do git; ver README)
```

Documentos:
- `README.md`: visão geral, instalação, dados, comandos.
- `ETAPA2.md`: roteiro da apresentação da Etapa 2, slide a slide, em linguagem simples.
- `results/etapa2_detalhes.md`: resumo técnico da Etapa 2.
- `results/comparacao.md`, `results/melhorias.md`: Etapa 1 (replicação e propostas).
- `results/modus_pp.md`: tabela de resultados da Etapa 2.
- `results/<base>/summary.md`: achados por base (Etapa 1).

## Ambiente

- Python 3.13 em `.venv/` (`capymoa pandas matplotlib python-pptx`).
- Java 17 para o CapyMOA (motor `--engine moa`). No macOS:
  `export JAVA_HOME=/opt/homebrew/opt/openjdk@17 PATH=$JAVA_HOME/bin:$PATH`.
  O motor `--engine numpy` (src/hst.py) não precisa de Java.
- Artigo: `cd paper && tectonic main.tex`.
- Render de slides: LibreOffice em `/Applications/LibreOffice.app/Contents/MacOS/soffice`.

## Saída de cada rodada

`results/<base>/<nome>/`:
- `log.txt`: configuração, métricas e alarmes por classe.
- `metrics.json`: `config` (todos os argumentos), `metrics_post_warmup`, `metrics_after_default_warmup`,
  `warmup_end`, `attacks_trained` (fração do ataque usada no treino = envenenamento), `engine`.
- `scores.csv.gz`: por instância `t, label, score, tau, pred, flag, trained, score_frozen`.
  Fica fora do git (centenas de MB); é regenerado por `run.py`.

Métricas são sempre da fase operacional (após o aquecimento). "F1 oráculo" em `modus_pp.md` usa
rótulos para escolher o limiar: é só um teto, não resultado do método.

## Achados centrais

1. **Vazamento de rótulo (Etapa 2).** O HSTrees do MOA dimensiona o espaço com `numAttributes()`,
   que inclui o atributo de classe. Se o rótulo verdadeiro vai no fluxo, o HST o usa como dimensão de
   corte. Na Etapa 1 o rótulo ia no fluxo. Correção: `ModusConfig.label_in_stream=False` (padrão);
   `--label-in-stream` reproduz o comportamento antigo.
   - ASEADOS, config do artigo: F1 99,73% com rótulo -> 0,00% sem rótulo.
   - CTU-13: sem efeito (64,55% nos dois casos).
   - Edge-IIoT config do artigo: sem efeito (84,42% sem rótulo). Já o MODUS+ da Etapa 1 com 14
     ataques cai de 91,05% para 11,72%.
2. **Envenenamento por inundação.** O ataque entra no treino e vira o perfil "normal"
   (MODUS+ fixed_q: 99,9% do ataque treinado, F1 ~0).
3. **MODUS++** combate o envenenamento com quatro peças (`run_modus_pp`):
   - `--window-s 10`: janela de referência do HST em segundos, não em contagem;
   - `--warmup-adaptive`: o aquecimento termina quando o score fica estável (ADWIN);
   - `--train-cap 1.0 --cap-key dst`: teto de treino por destino (p99 do aquecimento);
   - `--frozen`: HST de referência congelado no aquecimento, com limiar no quantil 0,999.
     O congelado é treinado com 80% do aquecimento e calibrado com os 20% finais.
   - `--norm-freeze` completa o conjunto: congela a normalização no fim do aquecimento.

## Resultados da Etapa 2 (sem vazamento, F1 pós-aquecimento)

| Base | Base de comparação | MODUS++ |
|---|---|---|
| ASEADOS (DDoS) | MODUS+ fixed_q 0,08% | 62,99% (prec. 95,19%, FPR 0,48%; sementes 63,0/68,4/58,9) |
| ASEADOS (5 classes) | 0,71% | 31,15% |
| CTU-13 | MODUS+ fixed_q 0% | 0,01%; o congelado sozinho dá 69,59%; teto 0,1x dá 88,26% |
| Edge-IIoT (14 ataques) | MODUS original 76,66% | 91,17% (prec. 96,03%, rec. 86,77%) |

Ablação no ASEADOS (MODUS++ sem uma peça): sem congelado 0,24%; sem aquecimento adaptativo 19,72%;
sem janela em tempo 62,45%; sem teto 62,88%. O modelo congelado é a peça decisiva.
No CTU-13 o score do flood (0,774) fica logo abaixo de τ_f (0,777): o limiar é o gargalo.

## Comandos da Etapa 2

Prefixo comum do MODUS++: `--engine numpy --preset fixed_q --features plus`.

```
# reavaliação sem rótulo (motor MOA)
python run.py aseados --name nl_paper
python run.py edgeiiot --name nl_clean --variant clean

# MODUS+ base (numpy) e MODUS++ completo
python run.py aseados --name ppq_base --engine numpy --preset fixed_q --features plus
python run.py aseados --name ppq_all  --engine numpy --preset fixed_q --features plus \
    --window-s 10 --warmup-adaptive --train-cap 1.0 --cap-key dst --frozen --norm-freeze
# mesma linha para ctu13; Edge-IIoT com --variant all; 5 classes do ASEADOS com --classes all

python summarize_pp.py   # results/modus_pp.md
python paper_figs.py     # paper/figs/
python slides_etapa2.py  # Replicacao_MODUS_CIn_Etapa2.pptx
```

As ablações (`ppq_all_no*`), as sementes (`--seed 2/3`) e a sensibilidade (`--window-s 1/60`,
`--frozen-q 0.99`, `--train-cap 0.1`) seguem o mesmo padrão. A configuração exata de qualquer rodada
está em `results/<base>/<nome>/metrics.json` -> `config`.

## Pendências

- Artigo (`paper/`): faltam `sections/{abstract,intro,results,discussion,conclusion}.tex`.
  Em `sections/replication.tex` falta trocar `\EDGENL` por 84,42. Depois, compilar e conferir o
  mínimo de 8 páginas.
- Modelos treinados ainda não são salvos em disco (podem ser refeitos com a mesma semente).

## Convenções

- Textos, logs e comentários em português.
- Não citar números sem rodada salva em `results/`.
- Rodadas grandes (Edge-IIoT, 21 M pacotes) levam horas: rodar em segundo plano.
