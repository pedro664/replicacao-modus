# Todas as rodadas

Métricas da fase operacional (pós-aquecimento). Alarmes por tipo: recall para ataques, taxa de falso positivo para benigno.

Tempo = segundos do laço MODUS (ADWIN + HST + limiar), sem carregar dados nem gravar saídas.

| dataset | rodada | atributos | config | flag | conjunto | Prec % | Rec % | F1 % | AUC-ROC % | PR-AUC % | tempo s | instâncias | alarmes por tipo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aseados | all_fixed_plus | plus | fixed | sim | all, ordem paper | 60.53 | 44.34 | 51.18 | 46.68 | 42.48 | 34 | 457,044 | Benign 22%, Bot 100%, DDoS 85%, Dos 16%, Prob 95% |
| aseados | all_fixedq10k_plus | plus | fixed_q10k | sim | all, ordem paper | 21.56 | 0.39 | 0.76 | 24.19 | 32.64 | 44 | 457,044 | Benign 1%, Bot 0%, DDoS 0%, Dos 1%, Prob 0% |
| aseados | all_fixedq_plus | plus | fixed_q | sim | all, ordem paper | 53.77 | 0.33 | 0.65 | 19.44 | 29.26 | 73 | 457,044 | Benign 0%, Bot 0%, DDoS 0%, Dos 1%, Prob 0% |
| aseados | all_orig | paper | aseados | sim | all, ordem paper | 99.66 | 0.33 | 0.66 | 16.53 | 29.97 | 40 | 457,044 | Benign 0%, Bot 0%, DDoS 0%, Dos 1%, Prob 0% |
| aseados | cfg_ctu13 | paper | ctu13 | sim | ddos, ordem paper | 45.58 | 100.00 | 62.61 | 76.28 | 50.72 | 19 | 312,262 | Benign 29%, DDoS 100% |
| aseados | chronological | paper | aseados | sim | ddos, ordem chronological | 0.00 | 0.00 | 0.00 | – | – | 162 | 312,262 |  |
| aseados | chronological_no_flag | paper | aseados | não | ddos, ordem chronological | 0.00 | 0.00 | 0.00 | – | – | 152 | 312,262 |  |
| aseados | fixed_online | online | fixed | sim | ddos, ordem paper | 41.58 | 100.00 | 58.74 | 100.00 | 99.99 | 27 | 312,262 | Benign 34%, DDoS 100% |
| aseados | fixed_paper | paper | fixed | sim | ddos, ordem paper | 41.56 | 100.00 | 58.72 | 99.98 | 99.92 | 26 | 312,262 | Benign 34%, DDoS 100% |
| aseados | fixed_plus | plus | fixed | sim | ddos, ordem paper | 41.87 | 100.00 | 59.03 | 97.47 | 91.22 | 26 | 312,262 | Benign 34%, DDoS 100% |
| aseados | fixed_plus_chrono | plus | fixed | sim | ddos, ordem chronological | 0.00 | 0.00 | 0.00 | 0.00 | 0.28 | 9 | 312,262 | Benign 100%, DDoS 0% |
| aseados | fixedq10k_plus | plus | fixed_q10k | sim | ddos, ordem paper | 76.81 | 100.00 | 86.88 | 99.32 | 97.09 | 25 | 312,262 | Benign 7%, DDoS 100% |
| aseados | fixedq_online | online | fixed_q | sim | ddos, ordem paper | 98.97 | 100.00 | 99.48 | 100.00 | 99.98 | 45 | 312,262 | Benign 0%, DDoS 100% |
| aseados | fixedq_paper | paper | fixed_q | sim | ddos, ordem paper | 99.03 | 100.00 | 99.51 | 99.99 | 99.97 | 44 | 312,262 | Benign 0%, DDoS 100% |
| aseados | fixedq_plus | plus | fixed_q | sim | ddos, ordem paper | 97.79 | 100.00 | 98.88 | 99.93 | 99.58 | 45 | 312,262 | Benign 1%, DDoS 100% |
| aseados | no_flag | paper | aseados | não | ddos, ordem paper | 98.95 | 100.00 | 99.47 | – | – | 162 | 312,262 |  |
| aseados | paper | paper | aseados | sim | ddos, ordem paper | 99.46 | 100.00 | 99.73 | 100.00 | 99.99 | 29 | 312,262 | Benign 0%, DDoS 100% |
| aseados | paper_seed2 | paper | aseados | sim | ddos, ordem paper | 99.00 | 100.00 | 99.50 | – | – | 165 | 312,262 |  |
| aseados | paper_seed3 | paper | aseados | sim | ddos, ordem paper | 92.78 | 100.00 | 96.26 | – | – | 165 | 312,262 |  |
| aseados | tau_min_0.81 | paper | aseados | sim | ddos, ordem paper | 0.00 | 0.00 | 0.00 | – | – | 152 | 312,262 |  |
| ctu13 | cfg_aseados | paper | aseados | sim | ddos | 99.51 | 99.97 | 99.74 | 100.00 | 100.00 | 435 | 6,336,394 | Benign 0%, Botnet 100% |
| ctu13 | fixed_plus | plus | fixed | sim | ddos | 0.06 | 0.01 | 0.02 | 0.06 | 18.37 | 508 | 6,336,394 | Benign 8%, Botnet 0% |
| ctu13 | fixedq10k_plus | plus | fixed_q10k | sim | ddos | 0.05 | 0.01 | 0.01 | 0.40 | 18.30 | 371 | 6,336,394 | Benign 6%, Botnet 0% |
| ctu13 | fixedq_online | online | fixed_q | sim | ddos | 0.00 | 0.00 | 0.00 | 0.32 | 18.26 | 521 | 6,336,394 | Benign 5%, Botnet 0% |
| ctu13 | fixedq_plus | plus | fixed_q | sim | ddos | 0.10 | 0.01 | 0.02 | 0.10 | 18.25 | 648 | 6,336,394 | Benign 6%, Botnet 0% |
| ctu13 | no_flag | paper | ctu13 | não | ddos | 47.66 | 99.97 | 64.55 | – | – | 1826 | 6,336,394 |  |
| ctu13 | norm_global | paper | ctu13 | sim | ddos | 40.94 | 100.00 | 58.09 | – | – | 1892 | 6,336,394 |  |
| ctu13 | paper | paper | ctu13 | sim | ddos | 47.66 | 99.97 | 64.55 | – | – | 1853 | 6,336,394 |  |
| edgeiiot | all_fixed_plus | plus | fixed | sim | all | 94.45 | 87.89 | 91.05 | 92.50 | 92.89 | 995 | 21,124,493 | Backdoor 3%, DDoS_HTTP 100%, DDoS_ICMP 100%, DDoS_TCP 100%, DDoS_UDP 100%, Fingerprinting 51%, MITM 100%, Normal 5%, Password 17%, Port_Scanning 100%, Ransomware 100%, SQL_injection 100%, Uploading 1%, Vulnerability_scanner 1%, XSS 100% |
| edgeiiot | all_fixedq_plus | plus | fixed_q | sim | all | 0.19 | 0.00 | 0.00 | 19.34 | 33.04 | 2167 | 21,124,493 | Backdoor 0%, DDoS_HTTP 0%, DDoS_ICMP 0%, DDoS_TCP 0%, DDoS_UDP 0%, Fingerprinting 17%, MITM 0%, Normal 1%, Password 0%, Port_Scanning 0%, Ransomware 0%, SQL_injection 0%, Uploading 0%, Vulnerability_scanner 0%, XSS 0% |
| edgeiiot | all_orig | paper | edgeiiot | sim | all | 99.79 | 62.23 | 76.66 | 89.57 | 91.73 | 2906 | 21,124,493 | Backdoor 3%, DDoS_HTTP 0%, DDoS_ICMP 100%, DDoS_TCP 0%, DDoS_UDP 100%, Fingerprinting 69%, MITM 67%, Normal 0%, Password 0%, Port_Scanning 11%, Ransomware 11%, SQL_injection 0%, Uploading 0%, Vulnerability_scanner 0%, XSS 5% |
| edgeiiot | cfg_aseados | paper | aseados | sim | clean | 99.79 | 73.16 | 84.42 | 91.80 | 91.38 | 732 | 19,638,007 | DDoS_HTTP 0%, DDoS_ICMP 100%, DDoS_TCP 0%, DDoS_UDP 100%, Normal 0% |
| edgeiiot | clean | paper | edgeiiot | sim | clean | 99.79 | 73.16 | 84.42 | – | – | 712 | 19,638,007 |  |
| edgeiiot | clean_no_flag | paper | edgeiiot | não | clean | 99.79 | 73.16 | 84.42 | – | – | 712 | 19,638,007 |  |
| edgeiiot | fixedq10k_plus | plus | fixed_q10k | sim | clean | 76.27 | 0.03 | 0.06 | 29.45 | 33.85 | 877 | 19,638,007 | DDoS_HTTP 0%, DDoS_ICMP 0%, DDoS_TCP 0%, DDoS_UDP 0%, Normal 0% |
| edgeiiot | fixedq_online | online | fixed_q | sim | clean | 0.00 | 0.00 | 0.00 | 4.03 | 27.06 | 1376 | 19,638,007 | DDoS_HTTP 0%, DDoS_ICMP 0%, DDoS_TCP 0%, DDoS_UDP 0%, Normal 0% |
| edgeiiot | fixedq_plus | plus | fixed_q | sim | clean | 38.08 | 0.00 | 0.00 | 15.58 | 29.42 | 1593 | 19,638,007 | DDoS_HTTP 0%, DDoS_ICMP 0%, DDoS_TCP 0%, DDoS_UDP 0%, Normal 0% |
| edgeiiot | paper | paper | edgeiiot | sim | paper | 99.53 | 73.16 | 84.33 | – | – | 1265 | 30,919,961 |  |
