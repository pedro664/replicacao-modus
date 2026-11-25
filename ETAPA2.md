# Etapa 2 — O que fizemos e como explicar os slides

Este texto acompanha a apresentação `Replicacao_MODUS_CIn_Etapa2.pptx`. Ele conta a história da
Etapa 2 em linguagem simples, slide por slide, com o que cada um mostra e o que vale dizer ao
apresentar. Os detalhes técnicos (arquivos, parâmetros e todas as tabelas) estão em
[`results/etapa2_detalhes.md`](results/etapa2_detalhes.md).

---

## A história em um parágrafo

O MODUS é um detector de ataques DDoS que aprende sozinho, sem ninguém dizer o que é ataque. Ele
observa o tráfego da rede e dispara um alarme quando algo foge do "normal". Na Etapa 1 conseguimos
reproduzir os resultados do artigo e propusemos melhorias. Na Etapa 2, ao implementá-las,
descobrimos que a biblioteca usada deixava o detector **espiar a resposta certa**. Tirada essa
"cola", o detector original deixa de funcionar: o ataque engana o modelo, que passa a achá-lo
normal. As melhorias que implementamos atacam justamente esse problema. Em uma base, o acerto sobe
de praticamente zero para 63%. Na Edge-IIoT, com 14 tipos de ataque, o MODUS++ chega a 91%, contra 77% do detector original.
Na CTU-13, o modelo deixa de ser enganado, mas o ajuste do alarme ainda precisa ser refinado.

---

## Slide a slide

### Slide 1 — Capa

**O que mostra:** título do trabalho e a indicação "Etapa 02 — Implementação das melhorias".

**O que dizer:** "Na primeira etapa replicamos o artigo e propusemos melhorias. Hoje mostramos o que
aconteceu quando colocamos essas melhorias em prática."

---

### Slide 2 — Recapitulando a Etapa 1

**O que mostra:** três colunas para quem não viu a Etapa 1.
- **O que é o MODUS:** quatro passos. Um detector de mudança (ADWIN) vira um atributo a mais; uma
  floresta de árvores (HST) dá a cada pacote uma nota de "raridade"; a linha de alarme (limiar MAD)
  se ajusta à mediana das notas recentes; e o modelo só aprende com o que pareceu normal.
- **Replicação:** o F1 do artigo e o nosso nas três bases. ASEADOS e Edge-IIoT bateram; o CTU-13
  não, porque os rótulos do artigo são inconsistentes.
- **O que propusemos:** as quatro melhorias e os três trabalhos futuros que a Etapa 2 implementa.

**O que dizer:** "Na Etapa 1 reimplementamos o MODUS do zero e conseguimos reproduzir duas das três
bases. Propusemos sete mudanças. Hoje mostramos o que aconteceu quando as implementamos, e também
uma surpresa: o 99,73% do ASEADOS não era o que parecia."

---

### Slide 3 — Onde paramos

**O que mostra:** três números que resumem a Etapa 1.

- **2 de 3**: conseguimos reproduzir o artigo em duas das três bases de dados.
- **0**: a principal novidade do artigo, um "sinal de mudança" adicionado aos dados, não fez
  diferença nenhuma nos resultados.
- **≈ 0%**: com as nossas primeiras melhorias, o detector não pegava quase nenhum ataque na base
  CTU-13.

**O que dizer:** "Terminamos a Etapa 1 com uma suspeita: quando o ataque é muito intenso, ele
'contamina' o aprendizado do detector. A Etapa 2 começou daí."

---

### Slide 4 — Achado novo: o detector estava colando

**O que mostra:** dois gráficos lado a lado da mesma base (ASEADOS). Em cima, o detector como
rodamos na Etapa 1; embaixo, o detector corrigido. Os pontos laranjas são o ataque.

**A ideia:** para aprender, o detector recebe cada registro da rede. A biblioteca que usamos (a
mesma ferramenta popular de aprendizado em fluxo) entregava junto, sem avisar, a etiqueta
"é ataque / não é ataque". É como fazer uma prova com o gabarito grampeado na folha. Como o
detector deveria aprender **sem** essa etiqueta, isso é uma falha grave do experimento.

**O que o gráfico mostra:** com a "cola", o ataque fica destacado acima da linha de alarme e o
acerto é de 99,73%. Sem a cola, o ataque despenca para o fundo do gráfico e o acerto cai para 0%.

**O que dizer:**
- "Achamos isso ao reescrever o detector do zero para conseguir implementar as melhorias."
- "Na base CTU-13 nada muda, porque lá o ataque é fácil de distinguir mesmo sem cola."
- "Não sabemos se os autores tiveram o mesmo problema, porque o código deles não é público. Mas a
  nossa réplica dos 99% só existe com a cola."
- "A partir daqui, tudo o que mostramos é sem a cola."

---

### Slide 5 — O problema real

**O que mostra:** três números grandes sobre o detector já corrigido.

- **99,96%** do ataque na ASEADOS e **100%** na CTU-13 acabam sendo usados como exemplo de
  tráfego "normal" no aprendizado.
- **AUC < 0,5**: o detector acha o ataque *mais normal* que o tráfego comum.

**A ideia:** o detector aprende o tempo todo com o que vê. Para não aprender o ataque, ele só
estuda o que julgou inofensivo. O problema é que, se os primeiros segundos do ataque passarem
despercebidos, ele estuda esses pacotes, se acostuma com eles e deixa o resto passar. É como um
segurança que, depois de ver a mesma pessoa entrar muitas vezes, passa a achar que ela trabalha
ali. Isso se chama **envenenamento**.

**O que dizer:** "Esse é o defeito estrutural do método. As melhorias que implementamos foram
pensadas para ele."

---

### Slide 6 — O que implementamos (MODUS++)

**O que mostra:** seis cartões, um por peça do novo detector.

| Cartão | Em palavras simples |
|---|---|
| **0 · Detector próprio** | Reescrevemos o detector do zero, idêntico ao original (conferimos que dá exatamente os mesmos números), mas agora sob nosso controle e sem a cola. |
| **1 · Janela em tempo** | O detector atualiza sua noção de "normal" a cada 10 segundos, e não a cada 250 pacotes. Antes, um ataque com 20 mil pacotes por segundo fazia o detector "esquecer" o normal dezenas de vezes por segundo. |
| **2 · Aquecimento adaptativo** | No começo, o detector só observa. Antes, esse período era fixo (50 mil registros); agora ele termina quando o detector "se sente estável". |
| **3 · Teto de treino** | Cada destino da rede só pode ensinar ao detector um número limitado de exemplos por segundo. Um ataque contra um alvo não consegue dominar o aprendizado. |
| **4 · Modelo congelado** | Um segundo detector aprende só no início e nunca mais muda. Ele é a "memória de como era o normal" e não pode ser contaminado. Se qualquer um dos dois estranhar, soa o alarme. |
| **+ · Escala congelada** | A régua usada para medir os dados também para de mudar depois do início, para que o ataque não distorça a escala. |

**O que dizer:** "O item 2 é a melhoria 3 que propusemos na Etapa 1. Os itens 1, 3 e 4 eram os
'trabalhos futuros' que listamos. Usamos a mesma configuração em todas as bases e escolhemos os
valores antes de ver os resultados, para não ajustar o detector à prova."

---

### Slide 7 — ASEADOS: de 0% a 63%

**O que mostra:** um gráfico de barras com o acerto (F1) a cada melhoria acrescentada, e o número
63,4% em destaque.

**Como ler:** cada barra é o detector com uma melhoria a mais. Sozinhas, quase nenhuma faz
diferença: as barras ficam perto de zero. O modelo congelado sobe para 16%. Com todas juntas, o
acerto chega a 63%.

**O que dizer:**
- "Repetimos com três sementes aleatórias diferentes: o resultado ficou entre 59% e 68%, média
  63,4%."
- "Quando o detector dá alarme, ele acerta 95% das vezes, e os falsos alarmes no tráfego normal
  caíram de 2,4% para 0,5%."
- "Testamos tirar uma peça de cada vez. As duas indispensáveis são o modelo congelado e o
  aquecimento adaptativo. Sem o congelado, o acerto volta a quase zero."
- "A janela em tempo e o teto quase não pesam nesta base porque o tráfego é lento: são poucos
  registros por segundo."

---

### Slide 8 — CTU-13: o envenenamento some, o alarme ainda falha

**O que mostra:** à esquerda, a linha do tempo do ataque (cerca de 20 mil pacotes por segundo nos
dois minutos finais), com quanto de ataque cada versão detectou e quanto dele foi usado no
aprendizado. À direita, os números principais.

**A boa notícia:** com a janela em tempo e o teto, o ataque usado no aprendizado cai de **100% para
2%**. O detector volta a "enxergar" a diferença entre ataque e tráfego normal: o indicador de
separação sobe de praticamente 0% para 96,5%. Só o modelo congelado já chega a 69,6% de acerto.

**A má notícia:** com tudo junto e os valores escolhidos de antemão, o alarme não dispara.
A "nota de estranheza" do ataque ficou em 0,774 e a linha de alarme em 0,777: perdemos por três
milésimos.

**O que dizer:**
- "O problema que queríamos resolver, a contaminação, foi resolvido. O que falta é calibrar onde
  colocar a linha de alarme sem olhar as respostas."
- "Se mudarmos um pouco o teto ou a linha de alarme, o acerto vai a 83–88%. Mostramos isso como
  teste de sensibilidade, não como resultado, porque esses valores foram escolhidos depois de ver
  os dados."

---

### Slide 9 — Edge-IIoT: 91% com 14 tipos de ataque

**O que mostra:** um gráfico de barras com cinco versões do detector na base Edge-IIoT, que tem
14 tipos de ataque e 21 milhões de pacotes.

**Como ler, da esquerda para a direita:**
- **76,7%**: o MODUS original, com a configuração que o artigo escolheu para esta base. Aqui a
  "cola" não muda nada, porque o tipo de protocolo já separa os ataques. Mas ele perde todo o
  DDoS sobre TCP e HTTP.
- **91,1%**: a nossa primeira melhoria (MODUS+), como apresentada na Etapa 1. Ela foi medida com a
  cola.
- **11,7%**: a mesma versão, sem a cola. O resultado da Etapa 1 dependia dela.
- **0,0%**: o detector-base sem as melhorias. Quase todo o ataque (99,99%) virou exemplo de
  "normal" no aprendizado.
- **91,2%**: o MODUS++. Agora só 6,9% do ataque contamina o aprendizado.

**O que dizer:**
- "O MODUS original já ia razoavelmente bem aqui, com 77%, mas só porque detecta os ataques de
  protocolos 'raros', como ICMP e UDP. O MODUS++ chega a 91% e passa a pegar os ataques sobre TCP."
- "Quando o MODUS++ dá alarme, acerta 96% das vezes. Ele pega 87% de todo o ataque, com só 3% de
  alarmes falsos no tráfego normal."
- "Os ataques volumétricos (ICMP, UDP, TCP) são detectados acima de 97%. O que ainda escapa são
  ataques web discretos, como XSS e SQL injection, que se parecem com tráfego comum."
- "A configuração é a mesma das outras bases, sem nenhum ajuste específico."

---

### Slide 10 — Teste com ataques que não são DDoS

**O que mostra:** uma tabela com a porcentagem de alarmes para cada tipo de tráfego na base
ASEADOS completa, que tem cinco tipos: tráfego normal e quatro ataques diferentes.

**Por que importa:** o artigo diz que o método detectaria ataques nunca vistos ("zero-day"). Para
testar isso, deixamos entrar ataques que o artigo havia removido.

**Como ler:**
- O detector original não alarmou praticamente nada: 0% em quase todos os ataques.
- O MODUS++ pegou 100% das varreduras (Probe), 39% do DDoS, 23% dos bots e 11% do DoS.
- O preço foi alto: 18% de alarmes falsos no tráfego normal. Acerto geral: de 0,7% para 31%.

**Edge-IIoT (texto ao lado da tabela):** o MODUS++ pega 78% do scanner de vulnerabilidades e 43% do
ransomware, mas XSS (4%) e SQL injection (16%) ainda passam.

**O que dizer:** "Melhorou muito, mas ainda está longe de um detector que funcione bem contra
qualquer ataque desconhecido, principalmente os discretos."

---

### Slide 11 — Proposto x implementado

**O que mostra:** uma tabela com cada melhoria, de onde ela veio (proposta da Etapa 1 ou trabalho
futuro) e qual foi o efeito em cada uma das três bases. A linha em vermelho é o resultado do
MODUS++ completo: 0% → 63% na ASEADOS, ≈ 0% na CTU-13 (o alarme no fio da navalha) e 77% → 91% na
Edge-IIoT.

**O que dizer:** usar como resumo e "prestação de contas": tudo o que foi prometido foi
implementado e medido. Em resumo:
- Normalização e taxa por janela (Etapa 1) não bastam sozinhas.
- Aquecimento adaptativo e modelo congelado são decisivos na ASEADOS.
- Janela em tempo e teto são decisivos contra a contaminação na CTU-13 e na Edge-IIoT.
- O teste com outros ataques melhorou, mas ainda tem muito alarme falso.

---

### Slide 12 — Insumos e reprodutibilidade

**O que mostra:** seis cartões com o que o estudo gerou e onde está no repositório: código, logs e
métricas das 89 rodadas, amostras de 10 mil instâncias, os modelos treinados do MODUS++ (HST
adaptativo e congelado, nas três bases), as figuras e as tabelas. Embaixo, o link do GitHub.

**O que dizer:** é a prestação de contas do segundo entregável. Qualquer número dos slides pode ser
conferido: cada rodada guarda a configuração exata e pode ser refeita com um comando. O guia do
repositório está no `CLAUDE.md` e no `README.md`.

---

### Slide 13 — Conclusões e próximos passos

**Conclusões:**
1. A nossa réplica do resultado de 99% dependia do detector ver a resposta; sem isso, 0%.
2. O verdadeiro calcanhar de Aquiles do método é o envenenamento: aprender só com o que parece
   inofensivo não protege contra um ataque rápido.
3. Modelo congelado + aquecimento adaptativo: ASEADOS vai de 0% a 63%.
4. Janela em tempo + teto: a contaminação na CTU-13 cai de 100% para 2%.
5. Edge-IIoT, com 14 tipos de ataque: o acerto vai de 77% (original) para 91%.

**Próximos passos:**
- Uma forma de posicionar a linha de alarme que não dependa de sorte nem das respostas.
- Melhorar a detecção de ataques web discretos (XSS, SQL injection) e repetir com mais sementes.
- Artigo final (padrão IEEE) já escrito, com 10 páginas: falta só a revisão final dos autores.

---

### Slide 14 — Encerramento

Agradecimento, perguntas e link para o código.

---

## Perguntas que podem surgir

**"Então o artigo original está errado?"**
Não podemos afirmar isso. Mostramos que a nossa réplica só alcança os números do artigo quando o
detector vê a resposta, e que a ferramenta mais comum para esse tipo de método tem essa falha. Sem
o código dos autores, não dá para saber o que eles fizeram.

**"Por que não ajustaram a linha de alarme para dar um número melhor?"**
Porque seria ajustar o detector olhando a resposta da prova, o mesmo tipo de erro que estamos
apontando. Mostramos os números ajustados só como teste de sensibilidade, com essa identificação.

**"O que é F1?"**
Uma nota de 0 a 100% que equilibra duas coisas: quanto do ataque o detector pegou e quantos dos
alarmes eram de fato ataque.

**"O que é AUC?"**
Mede se o detector dá notas mais altas para ataques do que para tráfego normal, independentemente
de onde fica a linha de alarme. 100% é separação perfeita, 50% é chute e abaixo de 50% é o
detector "ao contrário".
