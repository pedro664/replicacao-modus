# Etapa 2 — Implementação das melhorias (MODUS++)

Resumo do que foi feito na Etapa 2 do trabalho de replicação do MODUS (Dutra, Nakayama e Nogueira,
SBSeg 2026), dos resultados obtidos e do conteúdo dos slides
(`Replicacao_MODUS_CIn_Etapa2.pptx`).

Números: fase operacional (após o aquecimento de cada rodada). Tabela completa:
[`results/modus_pp.md`](results/modus_pp.md).

---

## 1. Ponto de partida (Etapa 1)

- O MODUS foi reimplementado em Python (CapyMOA: ADWIN + Half-Space Trees + limiar MAD) e replicado
  em três bases. ASEADOS e Edge-IIoT reproduziram os números do artigo; o CTU-13 não, porque os rótulos
  do artigo são inconsistentes.
- Achados: a flag do ADWIN não tem efeito; sem normalização o HST separa por protocolo; o limiar fica
  preso num piso ajustado à mão; um *flood* rápido envenena o treino seletivo.
- Melhorias propostas (slide 12 da Etapa 1): (1) normalização online, (2) taxa por janela,
  (3) aquecimento adaptativo, (4) teste com ataques não-DDoS. Trabalhos futuros (slide 13): janela em
  tempo, teto de treino por intervalo, modelo de referência congelado.
- As melhorias 1, 2 e 4 já tinham código na Etapa 1 (MODUS+). A Etapa 2 implementou a 3 e os três
  trabalhos futuros, e reavaliou tudo.

## 2. Achado novo: vazamento de rótulo no HSTrees do MOA

Ao portar o HST para numpy, encontramos o seguinte: o `moa.classifiers.oneclass.HSTrees` monta o espaço
de trabalho com `instance.numAttributes()`, e esse valor **inclui o atributo de classe**. Com o rótulo
verdadeiro no fluxo (uso padrão do CapyMOA, `NumpyStream(X, y)`), parte dos cortes de cada árvore
separa ataque de benigno pelo próprio rótulo, tanto no treino quanto no score.

- Teste direto: mesmo vetor de atributos, só o rótulo trocado → o score muda até 0,10.
- **ASEADOS, config do artigo: F1 99,73% com rótulo → 0,00% sem rótulo** (AUC 1,00 → 0,11).
  O DDoS é o vetor `[0,0,0,0]`, idêntico a 42.740 fluxos benignos; só a dimensão do rótulo os separava.
- **CTU-13: nenhuma predição muda.** O *flood* é ICMP, e o protocolo já separa as classes.
- Não dá para saber se o código dos autores tem o mesmo problema, porque ele não é público. O que se
  pode afirmar é que a **nossa** réplica do 99,62% só existe com o vazamento.

Correção: por padrão o fluxo agora leva um rótulo constante. `--label-in-stream` reproduz as rodadas
antigas. Todas as rodadas da Etapa 2 são sem rótulo (prefixos `nl_*` no MOA e `ppq_*` no motor numpy).

**Consequência:** sem o vazamento, o problema real aparece. O ataque passa no início, treina o modelo
e vira o "normal". No ASEADOS, 99,96% do DDoS entra no treino; no CTU-13, 100% do *flood*. Nas duas
bases a AUC fica abaixo de 0,5: o detector acha o ataque mais normal que o tráfego benigno.

## 3. O que foi implementado (MODUS++)

| # | Componente | Origem | Onde | Flag em `run.py` |
|---|---|---|---|---|
| 0 | HST em numpy, fiel ao MOA (`java.util.Random` bit a bit, mesma construção das árvores, mesma fase inicial); score de uma janela inteira em lote | infraestrutura | `src/hst.py`, `validate_hst.py` | `--engine numpy` |
| 1 | **Janela de referência em tempo**: o HST troca `r ← l` a cada T s do relógio do fluxo (T = 10 s), não a cada 250 instâncias treinadas; normaliza pela massa real da referência | trabalho futuro | `src/modus_plus.py` | `--window-s 10` |
| 2 | **Aquecimento adaptativo**: ADWIN (δ = 0,002) no score do HST; o aquecimento termina após 5.000 instâncias sem mudança, entre 5 mil e 50 mil | melhoria 3 | `src/modus_plus.py` | `--warmup-adaptive` |
| 3 | **Teto de treino**: no máximo c treinos/s por IP de destino; c = percentil 99 das contagens (segundo, destino) do aquecimento | trabalho futuro | `src/modus_plus.py` | `--train-cap 1 --cap-key dst` |
| 4 | **Modelo de referência congelado**: 2º HST treinado em 80% do aquecimento e nunca atualizado; limiar = quantil 0,999 nos 20% restantes. Alarme se qualquer dos dois disparar; só treina o que os dois aceitam | trabalho futuro | `src/modus_plus.py` | `--frozen` (`--frozen-q`) |
| + | **Normalização congelada**: o Min-Max online para de mudar após o aquecimento, para que o *flood* não comprima o resto da escala | consequência de 4 | `src/features.py` | `--norm-freeze` |

Validação do motor numpy:
- `validate_hst.py`: os scores são idênticos aos do MOA em três configurações (diferença máx. 2,2e-16).
- `aseados/np_paper_pad`: as predições são idênticas às do MOA sem rótulo.

Tudo continua causal e de passagem única: a decisão em t usa só as instâncias 1..t.

Protocolo, sem ajuste na base de teste:
- Uma única configuração em todas as bases: `fixed_q` (padrões do HST de Tan et al., limiar
  med + 5,19·MAD de Iglewicz–Hoaglin, piso = quantil 0,999 do aquecimento) e atributos `plus`.
- Os parâmetros novos foram fixados antes das rodadas. As variações aparecem só como sensibilidade,
  sempre rotuladas assim.

## 4. Resultados

### ASEADOS-SDN-IoT (Benign + DDoS)

| Variante | F1 % | Prec % | FP benigno % | Ataque no treino % |
|---|---|---|---|---|
| MODUS, config do artigo, **com rótulo** (Etapa 1) | 99,73 | 99,46 | 0,13 | – |
| MODUS, config do artigo, sem rótulo | 0,00 | 0,00 | 0,13 | – |
| MODUS+ `fixed_q` (base) | 0,08 | 0,43 | 2,39 | 99,96 |
| + janela 10 s | 0,37 | 2,00 | 2,42 | 99,80 |
| + aquecimento adaptativo | 0,05 | 0,96 | 0,53 | 99,97 |
| + teto | 0,12 | 0,67 | 2,38 | 75,21 |
| + congelado | 16,18 | 49,30 | 2,43 | 90,33 |
| **MODUS++ (todas)** | **62,99** | **95,19** | **0,48** | 51,24 |

- Sementes 1/2/3: F1 63,0 / 68,4 / 58,9% (média 63,4%). A base fica em ≈ 0,2% em todas as sementes.
- Leave-one-out: sem o congelado, F1 0,2%; sem o aquecimento adaptativo, 19,7%; sem a janela, 62,5%;
  sem o teto, 62,9%. **O que carrega o resultado é o modelo congelado junto com o aquecimento
  adaptativo.** Janela e teto pesam pouco aqui porque são fluxos de baixa taxa.
- AUC do modelo congelado: 94,4%. A do adaptativo fica em 27%, porque ele continua parcialmente
  envenenado.

### CTU-13, cenário 11 (*flood* ICMP de ~20 mil pacotes/s nos ~2 min finais)

| Variante | F1 % | Ataque no treino % | AUC do score adaptativo % |
|---|---|---|---|
| MODUS+ `fixed_q` (base) | 0,00 | 100,00 | 0,15 |
| + congelado | **69,59** (prec. 90,8%) | 43,58 | 49,78 |
| + janela 10 s + teto | 0,00 | **2,07** | **96,47** (F1 com limiar ideal: 94,8%) |
| MODUS++ (todas), a priori | 0,01 | 2,41 | 72,93 (congelado: 93,95) |
| sens.: MODUS++ com teto 0,1× | 88,26 | 0,05 | 90,41 |
| sens.: MODUS++ com quantil congelado 0,99 | 83,40 | 0,89 | 92,71 |

- **O envenenamento some**: janela em tempo + teto levam a fração do *flood* que entra no treino de
  100% para 2%, e a separabilidade volta (AUC 0,15% → 96,5%).
- **O limiar a priori ainda falha**: no MODUS++ completo o *flood* fica com score 0,774 e o limiar
  congelado é 0,777. É uma margem de navalha. Com teto ou quantil ligeiramente diferentes, o F1 vai
  a 83–88%, mas esses valores são sensibilidade, não resultado.
- Gargalo restante: calibrar o limiar sem rótulos.

### Teste com ataques não-DDoS (melhoria 4) — ASEADOS com 5 classes

| Tipo (taxa de alarme) | MODUS+ `fixed_q` | MODUS++ |
|---|---|---|
| Bot | 0% | 22,9% |
| DDoS | 0% | 38,8% |
| DoS | 0,6% | 11,0% |
| Probe | 0% | 100% |
| Benigno (FP) | 0,08% | 17,9% |
| **F1 geral** | 0,7% | **31,2%** |

### Edge-IIoTset

O F1 de 91,05% (14 ataques, MODUS+ `fixed`) apresentado na Etapa 1 foi medido **com o vazamento**.
As rodadas sem rótulo (`nl_all_fixed_plus`, `ppq_base_all`, `ppq_all_all`, `nl_all_orig`, `nl_clean`)
estão em execução. Os resultados entram em `results/edgeiiot/` e nos slides 8–9 quando terminarem.

## 5. Conteúdo dos slides (`Replicacao_MODUS_CIn_Etapa2.pptx`)

| # | Slide | Mensagem |
|---|---|---|
| 1 | Capa | Etapa 02 — Implementação das melhorias (novembro de 2026) |
| 2 | Onde paramos | 2 de 3 bases replicadas; flag do ADWIN sem efeito; recall ≈ 0% no CTU-13 com as variantes novas |
| 3 | Achado novo: o HST do MOA lê o rótulo | Figura com e sem rótulo; ASEADOS 99,73% → 0%; por que o CTU-13 não muda |
| 4 | O problema real | Envenenamento: 99,96% (ASEADOS) e 100% (CTU-13) do ataque entram no treino; AUC < 0,5 |
| 5 | O que implementamos: MODUS++ | 6 cartões: HST próprio, janela em tempo, aquecimento adaptativo, teto, congelado, normalização congelada |
| 6 | ASEADOS: de 0% a 63% de F1 | Gráfico da ablação; média 63,4% em 3 sementes; precisão 95%; leave-one-out |
| 7 | CTU-13: o envenenamento some, o limiar ainda falha | Linha do tempo do *flood*; 100% → 2% no treino; AUC 96,5%; congelado 69,6%; a priori ≈ 0%; sensibilidade 83–88% |
| 8 | Teste com ataques não-DDoS | Tabela por tipo (5 classes); F1 0,7% → 31,2%; Edge-IIoT pendente |
| 9 | Proposto x implementado | Origem e efeito de cada melhoria nas duas bases |
| 10 | Conclusões e próximos passos | Vazamento, envenenamento, ganhos; limiar sem rótulos, Edge-IIoT, artigo |
| 11 | Encerramento | Do deck original |

## 6. Limitações

- O limiar sem rótulos ainda é frágil: no CTU-13 o resultado a priori depende de milésimos.
- O MODUS++ troca recall por FP quando o tráfego legítimo muda em relação ao aquecimento
  (ASEADOS 5 classes: 17,9% de FP).
- A ordem "temporal" do ASEADOS continua sendo a do artigo, que vem de um erro de leitura de data.
  Na ordem cronológica correta, o DDoS cai no aquecimento.
- Os tempos de execução são indicativos: as rodadas foram feitas em paralelo num único Mac.

## 7. Como reproduzir

```bash
# ambiente: Python 3.13 + OpenJDK 17
export JAVA_HOME=/opt/homebrew/opt/openjdk@17 PATH=$JAVA_HOME/bin:$PATH
.venv/bin/python validate_hst.py                       # motor numpy == MOA

# MODUS sem vazamento (MOA)
.venv/bin/python run.py aseados --name nl_paper
# MODUS+ base e MODUS++ (motor numpy)
.venv/bin/python run.py aseados --name ppq_base --engine numpy --features plus --preset fixed_q
.venv/bin/python run.py aseados --name ppq_all  --engine numpy --features plus --preset fixed_q \
    --window-s 10 --warmup-adaptive --train-cap 1 --frozen --norm-freeze
# o mesmo para ctu13 e edgeiiot (--variant all); ASEADOS com 5 classes: --classes all

.venv/bin/python summarize_pp.py    # results/modus_pp.md
.venv/bin/python paper_figs.py      # paper/figs/*.pdf
.venv/bin/python slides_etapa2.py   # Replicacao_MODUS_CIn_Etapa2.pptx
```

## 8. Próximos passos

1. Fechar o Edge-IIoT sem vazamento e atualizar os slides 8–9.
2. Limiar sem rótulos mais robusto (por exemplo, calibrado na distribuição do modelo congelado com
   margem, ou combinando os scores).
3. Artigo IEEE, coluna dupla, mínimo 8 páginas, até 25/11/2026: o rascunho está em `paper/`
   (fundamentação, replicação, método e metodologia já escritos).
