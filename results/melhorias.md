# MODUS — melhorias propostas e resultados

Métricas da fase operacional (pós-aquecimento). Tabela completa: `tabela_rodadas.md`.
Configurações (`run.py`, `PRESETS`):
- **artigo**: hiperparâmetros por base, como na Seção 4.1.
- **fixed**: uma config para todas as bases, escolhida a priori: padrões do HS-Trees (janela 250,
  25 árvores, prof. 15), limiar med + 5,19·MAD (z-score modificado de Iglewicz & Hoaglin), piso 0,5.
- **fixed_q**: `fixed` com piso automático = quantil 99,9% dos scores do aquecimento (sem rótulos).
  *Definida depois de ver o `fixed` no ASEADOS.*
- **fixed_q10k**: `fixed_q` com janela de 10 mil. *Definida depois de ver o `fixed_q` falhar no CTU-13.*

Atributos: **paper** (4 do artigo) · **online** (log no tamanho + Min-Max causal) · **plus** (online +
pacotes/s global e por IP de destino em janela de 1 s).

## 1. Config fixa entre bases (F1 %, só DDoS)

| config | atributos | ASEADOS | CTU-13 | Edge-IIoT |
|---|---|---|---|---|
| artigo (cada base com a sua) | paper | 99,73 | 64,55 | 84,42 |
| config do ASEADOS em todas | paper | 99,73 | **99,74** | 84,42 |
| config do CTU-13 em todas | paper | 62,61 | 64,55 | 84,42 |
| fixed | plus | 59,03 | 0,02 | (91,05 com os 14 ataques) |
| fixed_q | plus | 98,88 | 0,02 | 0,00 |
| fixed_q10k | plus | 86,88 | 0,01 | 0,06 |

- A config do próprio artigo para o ASEADOS, aplicada às três bases, é melhor que a escolhida pelos
  autores para o CTU-13 (99,74% vs 64,55%). O motivo é o piso 0,75 cortar o UDP; o detector continua
  separando por protocolo (CTU-13: ICMP = ataque).
- Nenhuma config com os atributos novos funciona nas três bases.

## 2. Normalização online

- Remove o vazamento (Min-Max global olha o futuro) **sem custo**: ASEADOS F1 99,48% (online) vs 99,51%
  (global), ambos com `fixed_q`; AUC 1,00 nos dois.
- Sozinha não resolve CTU-13 nem Edge-IIoT (F1 0% com janela 250): o problema lá é envenenamento.

## 3. Atributo de taxa por janela

- **Edge-IIoT com os 14 ataques (config `fixed`)**: F1 **91,05%** vs 76,66% do MODUS original; passa a
  detectar ataques sobre TCP: DDoS TCP e HTTP, SQL injection, XSS, Port Scanning, Ransomware, MITM = 100%
  (original: ≤ 11%). Custo: FP no benigno de 0,12% → 4,54%.
- ASEADOS: piora levemente (AUC 0,999 → 0,975 com `fixed`; F1 99,51 → 98,88 com `fixed_q`).
- CTU-13: não ajuda (F1 ≈ 0% em todas as variantes).

## 4. Teste com ataques não-DDoS ("zero-day")

| base | método | Rec % | FP benigno % | por tipo (alarmes) |
|---|---|---|---|---|
| ASEADOS (5 classes) | MODUS original | 0,33 | 0,00 | tudo ≈ 0% |
| ASEADOS (5 classes) | MODUS+ `fixed` | 44,34 | 21,92 | Bot 100, Probe 95, DDoS 85, DoS 16 |
| Edge-IIoT (14 ataques) | MODUS original | 62,23 | 0,12 | só não-TCP: ICMP/UDP 100, Fingerprinting 69, MITM 67; web ≤ 5 |
| Edge-IIoT (14 ataques) | MODUS+ `fixed` | 87,89 | 4,54 | 100% em 10 tipos; Password 17, Backdoor 3, Uploading 1, Vuln. scanner 1 |

- O MODUS original **não detecta ataques novos sobre TCP** (web, injeção, força bruta): a tese de zero-day
  não se sustenta.
- No ASEADOS o aquecimento já contém 20.711 fluxos de DoS: qualquer método que aprende o "normal" no
  aquecimento herda o ataque.

## 5. Limitação estrutural encontrada: envenenamento por flood

Treinar só o que foi predito como benigno protege o modelo **apenas se o alarme dispara já nos primeiros
pacotes do ataque**. Se eles passam (piso alto ou modelo ainda incerto), entram no treino, viram o
"normal" e o resto do flood é aceito:

- CTU-13 (flood de ~17 mil pacotes/s): janela de 250 e de 10 mil (< 1 s de flood) → recall ≈ 0%.
- Edge-IIoT: piso automático 0,76–0,90 → recall 0%; piso 0,5 → recall 88%.

Janelas medidas em nº de pacotes são sempre curtas demais para floods rápidos. Próximos passos naturais:
janela em tempo (segundos), limitar a fração de treino por intervalo, ou um modelo de referência congelado
ao lado do adaptativo.
