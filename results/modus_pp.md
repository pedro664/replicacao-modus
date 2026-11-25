# Etapa 2 — MODUS++ e reavaliação sem vazamento de rótulo

Fase operacional (após o aquecimento de cada rodada). `F1 oráculo` usa rótulos para escolher o melhor limiar fixo do score adaptativo: é um teto, não um resultado do método.

| base | rodada | descrição | aquec. | Prec % | Rec % | F1 % | FPR % | envenen. % | AUC adapt. % | AUC cong. % | F1 oráculo % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| aseados | paper | MODUS, config do artigo, MOA com rótulo (Etapa 1) | 50,000 | 99.46 | 100.00 | 99.73 | 0.13 | – | 100.00 | – | 99.99 |
| aseados | nl_paper | MODUS, config do artigo, sem rótulo | 50,000 | 0.00 | 0.00 | 0.00 | 0.13 | – | 10.70 | – | 32.81 |
| aseados | nl_no_flag | MODUS sem flag ADWIN, sem rótulo | 50,000 | 0.00 | 0.00 | 0.00 | 0.26 | – | 11.16 | – | 32.81 |
| aseados | nl_fixedq_paper | MODUS fixed_q, sem rótulo | 50,000 | 0.00 | 0.00 | 0.00 | 0.24 | – | 7.74 | – | 32.81 |
| aseados | nl_fixedq_plus | MODUS+ fixed_q (MOA), sem rótulo | 50,000 | 3.80 | 0.07 | 0.14 | 0.44 | – | 16.30 | – | 33.06 |
| aseados | ppq_base | MODUS+ fixed_q (numpy) | 50,000 | 0.43 | 0.04 | 0.08 | 2.39 | 99.96 | 17.88 | – | 33.34 |
| aseados | ppq_time10 | + janela 10 s | 50,000 | 2.00 | 0.20 | 0.37 | 2.42 | 99.80 | 23.44 | – | 33.82 |
| aseados | ppq_warmad | + aquecimento adaptativo | 6,651 | 0.96 | 0.03 | 0.05 | 0.53 | 99.97 | 16.84 | – | 29.21 |
| aseados | ppq_cap | + teto de treino | 50,000 | 0.67 | 0.07 | 0.12 | 2.38 | 75.21 | 19.47 | – | 33.39 |
| aseados | ppq_normfreeze | + normalização congelada | 50,000 | 0.81 | 0.08 | 0.15 | 2.43 | 99.92 | 17.29 | – | 32.82 |
| aseados | ppq_frozen | + modelo congelado (c/ norm. congelada) | 50,000 | 49.30 | 9.67 | 16.18 | 2.43 | 90.33 | 18.54 | 90.73 | 32.82 |
| aseados | ppq_all | MODUS++ (todas) | 6,651 | 95.19 | 47.07 | 62.99 | 0.48 | 51.24 | 27.33 | 94.44 | 29.14 |
| aseados | ppq_all_notime | MODUS++ sem janela em tempo | 6,651 | 93.00 | 47.01 | 62.45 | 0.72 | 51.30 | 22.76 | 94.44 | 29.04 |
| aseados | ppq_all_nowarm | MODUS++ sem aquecimento adaptativo | 50,000 | 54.39 | 12.05 | 19.72 | 2.47 | 74.16 | 26.03 | 90.73 | 32.92 |
| aseados | ppq_all_nocap | MODUS++ sem teto | 6,651 | 94.67 | 47.07 | 62.88 | 0.54 | 52.93 | 27.04 | 94.44 | 29.14 |
| aseados | ppq_all_nofrozen | MODUS++ sem modelo congelado | 6,651 | 8.15 | 0.12 | 0.24 | 0.28 | 65.12 | 26.40 | – | 29.13 |
| aseados | ppq_all_seed2 | MODUS++ semente 2 | 6,587 | 81.72 | 58.75 | 68.36 | 2.66 | 39.36 | 43.11 | 93.03 | 29.31 |
| aseados | ppq_all_seed3 | MODUS++ semente 3 | 6,651 | 95.70 | 42.50 | 58.86 | 0.39 | 55.07 | 28.73 | 96.43 | 29.08 |
| aseados | ppq_base_seed2 | MODUS+ fixed_q semente 2 | 50,000 | 1.24 | 0.10 | 0.18 | 1.93 | 99.90 | 18.31 | – | 32.81 |
| aseados | ppq_base_seed3 | MODUS+ fixed_q semente 3 | 50,000 | 1.64 | 0.13 | 0.24 | 1.90 | 99.87 | 10.98 | – | 32.82 |
| aseados | ppq_all_w1 | sens.: MODUS++ janela 1 s | 12,025 | 99.01 | 9.88 | 17.97 | 0.02 | 67.66 | 20.81 | 91.27 | 29.52 |
| aseados | ppq_all_w60 | sens.: MODUS++ janela 60 s | 6,660 | 93.85 | 47.19 | 62.80 | 0.63 | 51.12 | 52.15 | 94.44 | 41.29 |
| aseados | ppq_all_q99 | sens.: MODUS++ quantil congelado 0,99 | 6,651 | 81.69 | 48.83 | 61.12 | 2.22 | 50.06 | 27.06 | 94.44 | 29.08 |
| aseados | nl_all_orig | 5 classes: MODUS artigo, sem rótulo | 50,000 | 0.00 | 0.00 | 0.00 | 0.00 | – | 21.14 | – | 60.26 |
| aseados | ppq_base_allcls | 5 classes: MODUS+ fixed_q | 50,000 | 77.78 | 0.35 | 0.71 | 0.08 | 99.65 | 23.06 | – | 61.21 |
| aseados | ppq_all_allcls | 5 classes: MODUS++ | 11,092 | 47.83 | 23.09 | 31.15 | 17.88 | 66.02 | 25.21 | 50.05 | 58.68 |
| ctu13 | paper | MODUS, config do artigo, MOA com rótulo (Etapa 1) | 50,000 | 47.66 | 99.97 | 64.55 | 52.37 | – | – | – | – |
| ctu13 | nl_paper | MODUS, config do artigo, sem rótulo | 50,000 | 47.66 | 99.97 | 64.55 | 52.37 | – | 99.86 | – | 99.76 |
| ctu13 | nl_cfg_aseados | MODUS, config do ASEADOS, sem rótulo | 50,000 | 99.51 | 99.97 | 99.74 | 0.24 | – | 99.89 | – | 99.75 |
| ctu13 | nl_fixedq_plus | MODUS+ fixed_q (MOA), sem rótulo | 50,000 | 0.00 | 0.00 | 0.00 | 5.37 | – | 0.04 | – | 48.82 |
| ctu13 | nl_fixed_plus | MODUS+ fixed (MOA), sem rótulo | 50,000 | 0.01 | 0.00 | 0.00 | 6.43 | – | 0.04 | – | 48.82 |
| ctu13 | ppq_base | MODUS+ fixed_q (numpy) | 50,000 | 0.01 | 0.00 | 0.00 | 3.12 | 100.00 | 0.15 | – | 48.82 |
| ctu13 | ppq_frozen | + modelo congelado (c/ norm. congelada) | 50,000 | 90.79 | 56.42 | 69.59 | 2.73 | 43.58 | 49.78 | 96.32 | 55.54 |
| ctu13 | ppq_time10cap | + janela 10 s + teto | 50,000 | 0.00 | 0.00 | 0.00 | 0.04 | 2.07 | 96.47 | – | 94.81 |
| ctu13 | ppq_all | MODUS++ (todas) | 35,318 | 0.06 | 0.00 | 0.01 | 2.60 | 2.41 | 72.93 | 93.95 | 71.14 |
| ctu13 | ppq_all_cap01 | sens.: MODUS++ teto 0,1x | 35,318 | 82.96 | 94.29 | 88.26 | 9.21 | 0.05 | 90.41 | 93.95 | 87.16 |
| ctu13 | ppq_all_q99 | sens.: MODUS++ quantil congelado 0,99 | 35,318 | 88.24 | 79.07 | 83.40 | 5.01 | 0.89 | 92.71 | 93.95 | 86.06 |
