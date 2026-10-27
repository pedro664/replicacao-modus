# MODUS — Edge-IIoTset

Fonte: pcaps do Edge-IIoTset (zip do Kaggle), todos os quadros (IPv4, IPv6, ARP), ordenados por tempo;
rótulo por arquivo (pcaps `DDoS*` = ataque). Configuração do artigo: HST janela 100k, 80 árvores,
prof. 15; k=6, piso 0,40; MAD sobre 5.000 scores; aquecimento 50k; ADWIN δ=0,001; sem normalização.

## Reconstrução do conjunto do artigo

- Pacotes dos 4 pcaps de DDoS: 229.142 + 2.914.356 + 2.020.152 + 3.215.732 = **8.379.382 = VP+FN do artigo**.
- Negativos do artigo (VN+FP = 22.540.579) = **2 × pcaps normais (11.258.625) + pcap de Port Scanning
  (23.329)**. Total 30.919.961 = nº de instâncias do artigo. Ou seja, o artigo aparentemente contou o
  tráfego normal duas vezes e manteve um ataque (Port Scanning) rotulado como benigno.
- A Tabela 1 do artigo (Normal 93,157%, DDoS 0,948%) não corresponde a esse conjunto (DDoS = 27,1%).
- Variante `clean`: normais uma vez + DDoS = 19.638.007 pacotes.

Métricas na convenção do artigo (aquecimento contado como predição "normal").

| rodada | conjunto | flag ADWIN | VP | VN | FP | FN | Acc % | Prec % | Rec % | F1 % | tempo s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **artigo (Tab. 2/3)** | 30,9 M | sim | 6.130.307 | 21.966.507 | 574.072 | 2.249.075 | 90,87 | 91,44 | 73,16 | 81,24 | 14.893 |
| paper | 30,9 M (normais 2x + PortScan) | sim | **6.130.307** | 22.511.659 | 28.920 | **2.249.075** | 92,63 | 99,53 | 73,16 | 84,33 | 1.265 |
| clean | 19,6 M (normais 1x) | sim | 6.130.307 | 11.245.720 | 12.905 | 2.249.075 | 88,48 | 99,79 | 73,16 | 84,42 | 712 |
| clean_no_flag | 19,6 M (normais 1x) | não | 6.130.306 | 11.245.720 | 12.905 | 2.249.076 | 88,48 | 99,79 | 73,16 | 84,42 | 712 |

## Achados

1. **VP e FN idênticos ao artigo, pacote a pacote.** Só os FP diferem (28.920 vs 574.072).
2. **O detector é um classificador por raridade de protocolo.** Sem normalização o HST degenera
   (204 scores distintos; limiar no piso 0,40 em 99,7% do tempo). O benigno é quase todo TCP:

   | | TCP | ICMP | UDP |
   |---|---|---|---|
   | benigno | 22.403.004 → todos "normal" | raro | 108.175 → todos "normal" |
   | DDoS | 2.248.938 de 2.248.991 **perdidos** | 3.230.827 de 3.230.827 detectados | 2.898.830 de 2.898.967 detectados |

   O recall de 73,16% do artigo é exatamente a fração de pacotes DDoS que não são TCP: floods ICMP e
   UDP são detectados, floods TCP SYN e HTTP passam inteiros. Não há detecção "volumétrica".
3. **A flag do ADWIN não contribui**: sem ela muda 1 pacote em 19,6 M, apesar de 17–22 mil disparos.
4. **Vazão**: 1.265 s aqui vs 14.893 s no artigo para o mesmo fluxo — o custo depende da implementação
   (o cálculo ingênuo do MAD dominava o tempo), não é uma propriedade do método.

Figuras: `paper/scores.png`, `clean/scores.png`.
