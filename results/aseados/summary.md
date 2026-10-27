# MODUS — ASEADOS-SDN-IoT

Métricas na convenção do artigo (aquecimento contado como predição 'normal').

| rodada | ordem | flag ADWIN | seed | τ_min | VP | VN | FP | FN | Acc % | Prec % | Rec % | F1 % | tempo s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **artigo (Tab. 2/3)** | ? | sim | ? | 0.75 | 51,465 | 260,406 | 391 | 0 | 99.87 | 99.25 | 100.00 | 99.62 | 189 |
| chronological | chronological | sim | 1 | 0.75 | 0 | 260,508 | 289 | 51,465 | 83.43 | 0.00 | 0.00 | 0.00 | 162 |
| chronological_no_flag | chronological | não | 1 | 0.75 | 0 | 260,155 | 642 | 51,465 | 83.31 | 0.00 | 0.00 | 0.00 | 152 |
| no_flag | paper | não | 1 | 0.75 | 51,465 | 260,253 | 544 | 0 | 99.83 | 98.95 | 100.00 | 99.47 | 162 |
| paper | paper | sim | 1 | 0.75 | 51,465 | 260,516 | 281 | 0 | 99.91 | 99.46 | 100.00 | 99.73 | 174 |
| paper_seed2 | paper | sim | 2 | 0.75 | 51,465 | 260,276 | 521 | 0 | 99.83 | 99.00 | 100.00 | 99.50 | 165 |
| paper_seed3 | paper | sim | 3 | 0.75 | 51,465 | 256,793 | 4,004 | 0 | 98.72 | 92.78 | 100.00 | 96.26 | 165 |
| tau_min_0.81 | paper | sim | 1 | 0.81 | 0 | 260,792 | 5 | 51,465 | 83.52 | 0.00 | 0.00 | 0.00 | 152 |

## Achados

1. **Replicação bem-sucedida.** Com HST (janela 2.500, 150 árvores, prof. 12), ADWIN δ=0,001,
   k=8, piso 0,75, teto 0,95, janela MAD 5.000, aquecimento 50k e Min-Max global, obtivemos
   VP=51.465 e FN=0 idênticos ao artigo; FP 281 vs 391; F1 99,73% vs 99,62%; 174 s vs 189 s.
2. **A ordem "temporal" do artigo vem de um erro de parse de data.** O CSV usa `dd/mm/aaaa`.
   Só o parse misto do pandas (lê `10/03` como 3/out e `12/03` como 3/dez) produz um aquecimento
   100% benigno e FN=0. Na ordem cronológica correta o DDoS ocorre primeiro, o aquecimento
   aprende o ataque como normal e o **F1 cai para 0%** (`chronological`).
3. **Todo fluxo DDoS é o vetor [0,0,0,0]** (portas, protocolo e tamanho médio = 0), e 42.740
   fluxos benignos são idênticos a ele. Como instâncias sinalizadas não treinam o modelo, o HST
   congela no início do ataque e **todas as 51.465 instâncias recebem o mesmo score (0,8064)**.
4. **O recall de 100% depende do piso ajustado à mão.** O limiar fica no piso 0,75 durante todo o
   ataque; com piso 0,81 o **recall vai a 0%** (`tau_min_0.81`).
5. **A flag do ADWIN não contribui.** O ADWIN não dispara nenhuma vez dentro do ataque; sem a flag
   o F1 é 99,47% vs 99,73%, diferença menor que a variação entre sementes (96,26%–99,73%).
6. **Vazamento:** a normalização Min-Max usa mín/máx do conjunto inteiro (viola passagem única).

Figuras: `paper/scores.png`, `chronological/scores.png`, `tau_min_0.81/scores.png`.
