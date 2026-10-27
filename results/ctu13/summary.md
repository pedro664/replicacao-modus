# MODUS — CTU-13 cenário 11 (Rbot)

Fonte: `capture20110818-2.truncated.pcap` (pcapng, payload truncado; tamanho original preservado).
6.336.398 pacotes, dos quais **6.336.394 IPv4 = exatamente o nº de instâncias do artigo**.
Rótulo: ataque se origem ou destino ∈ {147.32.84.165, .191, .192} (hosts infectados, README do CTU-13);
Background e Normal = benignos. Configuração do artigo: HST janela 100k, 80 árvores, prof. 15;
k=6, piso 0,40, sem teto; MAD sobre 5.000 scores; aquecimento 50k; ADWIN δ=0,001 no tamanho do pacote.

Métricas na convenção do artigo (aquecimento contado como predição "normal").

| rodada | normalização | flag ADWIN | VP | VN | FP | FN | Acc % | Prec % | Rec % | F1 % | tempo s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **artigo (Tab. 2/3)** | nenhuma | sim | 2.088.551 | 3.440.093 | 6.796 | 800.954 | 87,25 | 99,67 | 72,28 | 83,79 | 2.895 |
| paper | nenhuma | sim | 2.029.718 | 2.077.314 | 2.228.763 | 599 | 64,82 | 47,66 | 99,97 | 64,55 | 1.853 |
| no_flag | nenhuma | não | 2.029.718 | 2.077.314 | 2.228.763 | 599 | 64,82 | 47,66 | 99,97 | 64,55 | 1.827 |
| norm_global | Min-Max global | sim | 2.030.313 | 1.376.754 | 2.929.323 | 4 | 53,77 | 40,94 | 100,00 | 58,09 | 1.892 |

## Achados

1. **Replicação não bate.** Recall ~100% (artigo 72%) e precisão 48% (artigo 99,7%): perfil de erro oposto.
2. **Os rótulos do artigo são inconsistentes entre si.** A regra oficial (IPs infectados) dá 2.030.317
   ataques = **32,04%** do total — o número que a Tabela 1 chama de "Benigno 32,03%" (rótulos trocados).
   Já a matriz de confusão do artigo implica 2.889.505 ataques (45,6%), que não sai de nenhuma regra
   testada: IPs infectados (2.030.317), pacotes envolvendo o alvo 147.32.96.69 (2.032.396) ou janela
   temporal do flood (2.630.426).
3. **Com atributos brutos o HST degenera.** O HSTrees do MOA sorteia os cortes em [0,1]; portas
   (0–65535) e tamanho (60–1514) caem sempre do mesmo lado. O score assume só 126 valores e vira um
   classificador de protocolo: TCP ≈ 0 (normal), UDP ≈ 0,56 (> piso 0,40 → 99,4% dos UDP benignos viram
   FP), ICMP = 1,0 (ataque). Como o DDoS do Rbot é um flood ICMP (2.029.687 pacotes de 1066 bytes para
   147.32.96.69), o recall fica ~100% "de graça".
4. **A flag do ADWIN não muda nenhuma predição** (`paper` = `no_flag` em todas as 6,3 M instâncias),
   apesar de 3.056 disparos do ADWIN.
5. **Normalizar não resolve**: com Min-Max o F1 cai para 58% (mais FP em TCP e UDP).
6. **O limiar fica no piso 0,40 quase o tempo todo**, de novo um hiperparâmetro manual decide tudo.
7. Ataque concentrado nos ~2 min finais (t = 800–920 s de 971 s); aquecimento tem 1 pacote de ataque.

Figuras: `paper/scores.png`, `norm_global/scores.png`.
