# MODUS — replicação vs. artigo (visão geral)

Métricas na convenção do artigo (aquecimento contado como "normal"). Detalhes em `<dataset>/summary.md`.

| Dataset | Instâncias | | VP | FP | FN | Prec % | Rec % | F1 % | Tempo s |
|---|---|---|---|---|---|---|---|---|---|
| ASEADOS-SDN-IoT | 312.262 | artigo | 51.465 | 391 | 0 | 99,25 | 100,00 | 99,62 | 189 |
| | | replicação | 51.465 | 281 | 0 | 99,46 | 100,00 | 99,73 | 37 |
| CTU-13 (C11) | 6.336.394 | artigo | 2.088.551 | 6.796 | 800.954 | 99,67 | 72,28 | 83,79 | 2.895 |
| | | replicação | 2.029.718 | 2.228.763 | 599 | 47,66 | 99,97 | 64,55 | 1.853* |
| Edge-IIoT | 30.919.961 | artigo | 6.130.307 | 574.072 | 2.249.075 | 91,44 | 73,16 | 81,24 | 14.893 |
| | | replicação | 6.130.307 | 28.920 | 2.249.075 | 99,53 | 73,16 | 84,33 | 1.265 |

\* antes da otimização do cálculo do MAD (resultado idêntico, só mais lento).

## Status da replicação

- **ASEADOS: replica** — mas só com a ordenação gerada por um erro de parse de data (dd/mm lido como
  mm/dd). Na ordem cronológica correta, F1 = 0%.
- **CTU-13: não replica** — mesmo nº de pacotes, mas rótulos do artigo inconsistentes (Tabela 1 com
  classes trocadas; matriz implica 2,89 M ataques, a regra oficial dá 2,03 M).
- **Edge-IIoT: replica nos ataques (VP e FN idênticos)** — com o conjunto reconstruído (normais 2x +
  Port Scanning como benigno).

## Achados transversais (para "propor melhorias")

1. **A flag do ADWIN — a contribuição central — não tem efeito mensurável** em nenhuma base
   (ASEADOS: dentro da variação entre sementes; CTU-13: predições idênticas; Edge-IIoT: 1 pacote em 19,6 M).
2. **Sem normalização o HST do MOA degenera** (cortes sorteados em [0,1]) e vira um classificador por
   raridade de protocolo: CTU-13 → ICMP=ataque, UDP=FP; Edge-IIoT → TCP=normal, resto=ataque.
3. **O limiar fica preso no piso ajustado à mão** quase o tempo todo (0,75 / 0,40). No ASEADOS, piso
   0,81 → recall 0%.
4. **Ataques com vetor constante + treino só com "benignos" congelam o modelo**: todo o DDoS do ASEADOS
   recebe o mesmo score.
5. **Hiperparâmetros ajustados por base** e ataques não-DDoS removidos: a tese de zero-day não foi testada.
6. **Vazamento**: Min-Max com mín/máx globais no ASEADOS.
