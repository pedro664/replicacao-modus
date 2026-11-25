"""Gera os slides da Etapa 2 (implementação das melhorias) a partir do deck da Etapa 1.

Mantém a capa e o encerramento do deck original (identidade visual do CIn) e cria os slides de
conteúdo no mesmo estilo. Números tirados de results/modus_pp.md.

  python slides_etapa2.py   ->  Replicacao_MODUS_CIn_Etapa2.pptx
"""

import copy
import io
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).parent
SRC = ROOT / "Replicacao_MODUS_CIn_1 (1).pptx"
OUT = ROOT / "Replicacao_MODUS_CIn_Etapa2.pptx"
FIGS = ROOT / "results" / "figs"

DARK, RED, RED2, CARD = "231F20", "DB1E2F", "AF0421", "F2F2F2"
BODY, MUTED, HILITE, LIGHT = "4D4D4D", "8C8C8C", "FF4D5C", "E6E6E6"


def rgb(h):
    return RGBColor.from_string(h)


def box(slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(fill)
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def text(slide, x, y, w, h, runs, size=12, color=BODY, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, space_after=4):
    """runs: str, ou lista de parágrafos; cada parágrafo é str ou lista de (texto, {opções})."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, 0)
    paras = [runs] if isinstance(runs, str) else runs
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        para.space_after = Pt(space_after)
        for t, o in ([(p, {})] if isinstance(p, str) else p):
            r = para.add_run()
            r.text = t
            f = r.font
            f.name = "Arial"
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", False)
            f.color.rgb = rgb(o.get("color", color))
    return tb


def bullets(slide, x, y, w, h, items, size=12, color=BODY, marker=RED):
    """Lista com marcador real (não um caractere literal)."""
    tb = text(slide, x, y, w, h, items, size=size, color=color, space_after=6)
    from pptx.oxml.ns import qn
    for para in tb.text_frame.paragraphs:
        pPr = para._p.get_or_add_pPr()
        pPr.set("marL", str(Inches(0.18)))
        pPr.set("indent", str(-Inches(0.18)))
        bu = pPr.makeelement(qn("a:buChar"), {"char": "•"})
        clr = pPr.makeelement(qn("a:buClr"), {})
        srgb = clr.makeelement(qn("a:srgbClr"), {"val": marker})
        clr.append(srgb)
        pPr.append(clr)
        pPr.append(bu)
    return tb


def header(slide, title, subtitle, page):
    box(slide, -0.02, -0.01, 10.02, 1.76, DARK)
    box(slide, 0.56, 0.56, 8.89, 0.57, "FFFFFF")
    text(slide, 0.69, 0.6, 8.61, 0.5, title, size=22, color=RED, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(slide, 0.83, 1.22, 8.33, 0.33, subtitle, size=15, color="FFFFFF")
    text(slide, 8.89, 5.3, 0.83, 0.2, str(page), size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def num_badge(slide, x, y, label):
    c = box(slide, x, y, 0.31, 0.31, RED, MSO_SHAPE.OVAL)
    tf = c.text_frame
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, 0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size, r.font.bold, r.font.name = Pt(12), True, "Arial"
    r.font.color.rgb = rgb("FFFFFF")


def card(slide, x, y, w, h, badge, title, body, size=11):
    box(slide, x, y, w, h, CARD)
    num_badge(slide, x + 0.15, y + 0.15, badge)
    text(slide, x + 0.56, y + 0.15, w - 0.7, 0.31, title, size=13, color=DARK, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(slide, x + 0.15, y + 0.58, w - 0.3, h - 0.65, body, size=size, color=BODY)


def stat(slide, x, y, w, value, label, value_color=HILITE, label_color=LIGHT):
    box(slide, x, y, w, 0.04, RED)
    text(slide, x, y + 0.14, w, 0.75, value, size=36, color=value_color, bold=True)
    text(slide, x, y + 0.92, w, 0.85, label, size=12, color=label_color)


def picture(slide, path, x, y, h=None, w=None):
    kw = {}
    if h:
        kw["height"] = Inches(h)
    if w:
        kw["width"] = Inches(w)
    return slide.shapes.add_picture(str(path), Inches(x), Inches(y), **kw)


def qr_png(url: str, box_px: int = 24, border: int = 4) -> bytes:
    """QR code do `url` em PNG (nível de correção M), sem dependências além de reportlab e Pillow."""
    from reportlab.graphics.barcode import qrencoder as qe
    qr = qe.QRCode(None, qe.QRErrorCorrectLevel.M)
    qr.addData(url)
    qr.make()
    n = qr.getModuleCount()
    size = (n + 2 * border) * box_px
    im = Image.new("L", (size, size), 255)
    px = im.load()
    for r in range(n):
        for c in range(n):
            if qr.isDark(r, c):
                for dy in range(box_px):
                    for dx in range(box_px):
                        px[(c + border) * box_px + dx, (r + border) * box_px + dy] = 0
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def notes(slide, txt):
    """Notas do apresentador (o roteiro completo está em ETAPA2.md)."""
    slide.notes_slide.notes_text_frame.text = txt


def dark_slide(prs):
    s = prs.slides.add_slide(BLANK)
    box(s, 0, -0.03, 10, 5.66, DARK)
    return s


def light_slide(prs):
    return prs.slides.add_slide(BLANK)


# ------------------------------------------------------------------ deck
prs = Presentation(str(SRC))
BLANK = prs.slides[11].slide_layout  # mesmo layout dos slides de conteúdo
slides = list(prs.slides)
cover, closing = slides[0], slides[-1]

# capa: só troca a linha da etapa e a data
for sh in cover.shapes:
    if not sh.has_text_frame:
        continue
    for p in sh.text_frame.paragraphs:
        full = "".join(r.text for r in p.runs)
        # o texto vem quebrado em vários runs: escreve no 1º e esvazia os demais (mantém a formatação)
        for old, new in [("Etapa 01 — Replicação de artigo científico", "Etapa 02 — Implementação das melhorias"),
                         ("Outubro de 2026", "Novembro de 2026")]:
            if old in full:
                p.runs[0].text = full.replace(old, new)
                for r in p.runs[1:]:
                    r.text = ""

# remove os slides 2..13 da Etapa 1 (ficam capa e encerramento)
sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[1:-1]:
    prs.part.drop_rel(sid.rId)
    sldIdLst.remove(sid)
# o encerramento é slide14.xml no deck original; renomeia para não colidir com os slides novos
from pptx.opc.packuri import PackURI  # noqa: E402
closing.part.partname = PackURI("/ppt/slides/slide99.xml")

REPO = "github.com/pedro664/replicacao-modus"

notes(cover, "Na primeira etapa replicamos o artigo e propusemos melhorias. Hoje mostramos o que aconteceu "
             "quando colocamos essas melhorias em prática.")

page = 2

# 2. Recapitulando a Etapa 1
s = light_slide(prs)
header(s, "Recapitulando a Etapa 1", "O método, a replicação nas três bases e o que propusemos", page)
cols = [(0.5, "O que é o MODUS"), (3.55, "Replicação (F1)"), (6.6, "O que propusemos")]
for x, title in cols:
    box(s, x, 1.95, 2.9, 3.25, CARD)
    text(s, x + 0.15, 2.05, 2.6, 0.3, title, size=13, color=DARK, bold=True)
steps = [("ADWIN", "detecta mudança no tamanho e vira atributo"),
         ("HST", "floresta que mede o quão raro é cada pacote"),
         ("Limiar MAD", "mediana + α·desvio dos scores recentes"),
         ("Treino seletivo", "só aprende com o que parece normal")]
for i, (name, desc) in enumerate(steps):
    y = 2.5 + i * 0.66
    num_badge(s, 0.65, y, str(i + 1))
    text(s, 1.08, y - 0.02, 2.25, 0.62, [[(name, {"bold": True, "color": DARK})], desc], size=10, space_after=1)
rows = [("Base", "Artigo", "Nosso"), ("ASEADOS", "99,62", "99,73"), ("CTU-13", "83,79", "64,55"),
        ("Edge-IIoT", "81,24", "84,33")]
tbl = s.shapes.add_table(len(rows), 3, Inches(3.65), Inches(2.5), Inches(2.7), Inches(1.6)).table
for j, wd in enumerate((1.1, 0.8, 0.8)):
    tbl.columns[j].width = Inches(wd)
for i, row in enumerate(rows):
    for j, v in enumerate(row):
        c = tbl.cell(i, j)
        c.fill.solid()
        c.fill.fore_color.rgb = rgb(DARK if i == 0 else "FFFFFF")
        c.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.RIGHT
        r = c.text_frame.paragraphs[0].add_run()
        r.text = v
        r.font.size, r.font.name, r.font.bold = Pt(11), "Arial", i == 0 or j == 2
        r.font.color.rgb = rgb("FFFFFF" if i == 0 else (RED if j == 2 and i == 2 else DARK))
text(s, 3.7, 4.25, 2.6, 0.9, "CTU-13 não replica: os rótulos do artigo são inconsistentes. "
     "O 99,73% do ASEADOS será revisitado adiante.", size=9, color=MUTED)
bullets(s, 6.7, 2.5, 2.65, 2.7, [
    [("Melhorias: ", {"bold": True}), ("normalização online, taxa por janela, aquecimento adaptativo, "
                                      "teste com ataques não-DDoS", {})],
    [("Trabalhos futuros: ", {"bold": True}), ("janela em tempo, teto de treino, modelo de referência "
                                              "congelado", {})],
    [("Etapa 2: ", {"bold": True, "color": RED}), ("implementar e medir todas", {})],
], size=10)
notes(s, "Slide de contexto para quem não lembra da Etapa 1. O fluxo do MODUS: o ADWIN avisa quando o tráfego muda; o "
         "HST dá uma nota de anormalidade a cada registro; um limiar dinâmico (mediana + α·MAD dos scores recentes) "
         "decide se é alarme; e o treino é seletivo: só aprende com o que julgou benigno. É essa última parte que o "
         "ataque explora: se ele passar despercebido no início, vira exemplo de 'normal'.\n\n"
         "Tabela: o artigo reporta 99,62 / 83,79 / 81,24 e a nossa réplica deu 99,73 / 64,55 / 84,33. O CTU-13 não "
         "replica porque os rótulos do artigo são inconsistentes. O 99,73% do ASEADOS é revisitado no slide do achado "
         "novo (depende do rótulo vazado). Propusemos 4 melhorias e 3 trabalhos futuros; a Etapa 2 implementa e mede "
         "todos.")
page += 1

# 3. Onde paramos
s = dark_slide(prs)
box(s, 0, 0.94, 3.6, 0.65, RED)
text(s, 0.35, 0.99, 3.2, 0.54, "Onde paramos", size=30, color="FFFFFF", bold=True, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.36, 1.86, 9.17, 0.83, "Etapa 1 replicou o MODUS e propôs melhorias; a Etapa 2 implementa e mede cada uma",
     size=20, color="FFFFFF", bold=True)
stat(s, 0.36, 2.97, 2.78, "2 de 3", "bases replicadas (ASEADOS e Edge-IIoT); CTU-13 com rótulos inconsistentes")
stat(s, 3.5, 2.97, 2.78, "0", "efeito da flag do ADWIN, a contribuição central do artigo")
stat(s, 6.64, 2.97, 2.78, "≈ 0%", "recall no CTU-13 com as variantes novas: o flood envenena o treino")
notes(s, "Terminamos a Etapa 1 com uma suspeita: quando o ataque é muito intenso, ele 'contamina' o aprendizado do "
         "detector. A Etapa 2 começou daí.\n\n"
         "2 de 3: reproduzimos o artigo em duas das três bases. 0: a flag do ADWIN, a principal novidade do artigo, "
         "não fez diferença nos nossos resultados. ≈ 0%: com as nossas primeiras melhorias, o detector não pegava "
         "quase nenhum ataque no CTU-13.")
page += 1

# 4. Achado novo: vazamento
s = light_slide(prs)
header(s, "Achado novo: o HST do MOA lê o rótulo", "Ao portar o HST, achamos o atributo de classe entre as dimensões", page)
picture(s, FIGS / "etapa2_leak_aseados.png", 0.5, 1.92, h=3.35)
text(s, 4.3, 1.98, 5.2, 0.6, [[("99,73% ", {"color": DARK}), ("→ 0%", {"color": RED})]], size=32, bold=True)
text(s, 4.3, 2.62, 5.2, 0.3, "F1 no ASEADOS, config do artigo, só tirando o rótulo do fluxo", size=11, color=MUTED)
bullets(s, 4.3, 3.05, 5.2, 2.2, [
    [("O HSTrees do MOA sorteia cortes em ", {}), ("numAttributes()", {"bold": True}),
     (", que inclui a classe: com o rótulo no fluxo, o score depende dele", {})],
    "Mesmo vetor, só o rótulo trocado: o score muda até 0,10",
    "CTU-13 não muda (o protocolo já separa); no ASEADOS o DDoS é [0,0,0,0], idêntico a 42 mil benignos",
    [("Todas as rodadas da Etapa 2 são ", {}), ("sem rótulo", {"bold": True})],
], size=12)
notes(s, "A ideia: para aprender, o detector recebe cada registro da rede. A biblioteca que usamos (a mesma ferramenta "
         "popular de aprendizado em fluxo) entregava junto, sem avisar, a etiqueta 'é ataque / não é ataque'. É como "
         "fazer uma prova com o gabarito grampeado na folha.\n\n"
         "No gráfico: com a 'cola', o ataque (laranja) fica acima da linha de alarme e o acerto é de 99,73%. Sem a "
         "cola, ele despenca para o fundo e o acerto cai para 0%.\n\n"
         "Dizer: achamos isso ao reescrever o detector do zero. Na CTU-13 nada muda, porque o ataque é ICMP e o "
         "protocolo já separa. Não sabemos se os autores tiveram o mesmo problema (o código deles não é público); "
         "o que afirmamos é que a NOSSA réplica dos 99% só existe com a cola. A partir daqui, tudo é sem a cola.")
page += 1

# 5. Sem vazamento: envenenamento
s = dark_slide(prs)
box(s, 0, 0.94, 4.3, 0.65, RED)
text(s, 0.35, 0.99, 3.9, 0.54, "O problema real", size=30, color="FFFFFF", bold=True, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.36, 1.86, 9.17, 0.83, "Sem o rótulo, o ataque passa no início, treina o modelo e vira o \"normal\"",
     size=20, color="FFFFFF", bold=True)
stat(s, 0.36, 2.97, 2.78, "99,96%", "do DDoS do ASEADOS entra no treino do HST (MODUS+ fixed_q)")
stat(s, 3.5, 2.97, 2.78, "100%", "do flood do CTU-13 entra no treino; AUC do score: 0,15%")
stat(s, 6.64, 2.97, 2.78, "AUC < 0,5", "nas duas bases: o detector acha o ataque mais normal que o tráfego benigno")
notes(s, "O detector aprende o tempo todo com o que vê. Para não aprender o ataque, só estuda o que julgou inofensivo. "
         "O problema: se os primeiros segundos do ataque passarem despercebidos, ele estuda esses pacotes, se acostuma "
         "e deixa o resto passar. É como um segurança que, depois de ver a mesma pessoa entrar muitas vezes, passa a "
         "achar que ela trabalha ali. Isso se chama envenenamento.\n\n"
         "99,96% do DDoS do ASEADOS e 100% do flood do CTU-13 viram exemplo de 'normal'. AUC < 0,5 quer dizer que o "
         "detector acha o ataque MAIS normal que o tráfego comum. Esse é o defeito estrutural do método; as melhorias "
         "foram pensadas para ele.")
page += 1

# 6. O que implementamos
s = light_slide(prs)
header(s, "O que implementamos: MODUS++", "A melhoria 3 proposta e os 3 trabalhos futuros, todos sem rótulos e de passagem única", page)
cw, ch, gx, gy = 2.92, 1.45, 0.13, 0.13
cards = [
    ("0", "HST próprio, fiel ao MOA", "Port em numpy bit a bit (diferença 2,2e-16). Dá controle da janela e da massa"),
    ("1", "Janela em tempo", "Referência trocada a cada 10 s, não a cada 250 pacotes: o flood não acelera a troca"),
    ("2", "Aquecimento adaptativo", "ADWIN no score: termina quando estabiliza (5 mil a 50 mil instâncias)"),
    ("3", "Teto de treino", "No máx. c treinos/s por IP de destino; c = percentil 99 do aquecimento"),
    ("4", "Modelo congelado", "2º HST treinado só no aquecimento. Alarme se qualquer um disparar"),
    ("+", "Normalização congelada", "Min-Max online para de mudar após o aquecimento: o flood não comprime o resto"),
]
for i, (b, t, d) in enumerate(cards):
    cx = 0.5 + (i % 3) * (cw + gx)
    cy = 1.94 + (i // 3) * (ch + gy)
    card(s, cx, cy, cw, ch, b, t, d, size=11)
text(s, 0.5, 5.08, 8.2, 0.4, "Protocolo: uma única configuração nas três bases, com os parâmetros novos fixados antes das "
     "rodadas. Variações aparecem só como sensibilidade, sempre rotuladas.", size=10, color=MUTED)
notes(s, "O item 2 (aquecimento adaptativo) é a melhoria 3 que propusemos na Etapa 1. Os itens 1, 3 e 4 eram os "
         "'trabalhos futuros' da Etapa 1. O item 0 é infraestrutura: reescrevemos o detector em numpy, idêntico ao "
         "original (diferença máxima de 2,2e-16 contra o MOA), mas agora sob nosso controle e sem a cola.\n\n"
         "Janela em tempo: antes, um ataque de 20 mil pacotes por segundo fazia o detector 'esquecer' o normal dezenas "
         "de vezes por segundo. Teto de treino: cada destino só pode ensinar um número limitado de exemplos por segundo. "
         "Modelo congelado: um segundo detector aprende só no início e nunca mais muda; se qualquer um dos dois "
         "estranhar, soa o alarme. Escala congelada: a régua dos dados para de mudar depois do início.\n\n"
         "Protocolo: usamos a mesma configuração em todas as bases e escolhemos os valores antes de ver os "
         "resultados, para não ajustar o detector à prova.")
page += 1

# 7. ASEADOS
s = light_slide(prs)
header(s, "ASEADOS: de 0% a 63% de F1, com 95% de precisão", "Ablação com o limiar fixed_q: sozinhas quase nada muda; juntas, sim", page)
cd = CategoryChartData()
cd.categories = ["MODUS+\nfixed_q", "+ janela\n10 s", "+ aquec.\nadapt.", "+ teto", "+ congelado", "MODUS++"]
cd.add_series("F1 (%)", (0.08, 0.37, 0.05, 0.12, 16.18, 62.99))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.45), Inches(1.9), Inches(5.3), Inches(3.4), cd)
ch_ = gf.chart
ch_.has_legend = False
ch_.font.size, ch_.font.name = Pt(10), "Arial"
ch_.font.color.rgb = rgb(BODY)
plot = ch_.plots[0]
plot.gap_width = 60
plot.has_data_labels = True
dl = plot.data_labels
dl.number_format, dl.number_format_is_linked = '0.0', False
dl.position = XL_LABEL_POSITION.OUTSIDE_END
dl.font.size, dl.font.bold = Pt(11), True
ser = plot.series[0]
ser.format.fill.solid()
ser.format.fill.fore_color.rgb = rgb("8C8C8C")
pt = ser.points[5]
pt.format.fill.solid()
pt.format.fill.fore_color.rgb = rgb(RED)
va = ch_.value_axis
va.maximum_scale, va.minimum_scale = 80, 0
va.has_major_gridlines = True
va.major_gridlines.format.line.color.rgb = rgb("E4E2DC")
va.format.line.fill.background()
va.tick_labels.font.size = Pt(9)
ch_.has_title = True
ch_.chart_title.text_frame.text = "F1 a priori na fase operacional (%)"
ch_.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
ch_.chart_title.text_frame.paragraphs[0].runs[0].font.bold = False
text(s, 6.05, 1.98, 3.45, 0.6, "63,4%", size=32, color=RED, bold=True)
text(s, 6.05, 2.58, 3.45, 0.3, "F1 médio em 3 sementes (58,9 a 68,4%)", size=11, color=MUTED)
bullets(s, 6.05, 3.0, 3.45, 2.3, [
    "Precisão 95% e FP no benigno de 0,48% (era 2,4%)",
    [("Limiar fixed da Etapa 1: ", {"bold": True}), ("F1 59,0%, mas precisão 42% e FP de 34%", {})],
    "Envenenamento: 99,96% → 51% do DDoS no treino",
    [("Sem o congelado: ", {"bold": True}), ("F1 0,2%; ", {}), ("sem aquec. adaptativo: ", {"bold": True}),
     ("19,7%", {})],
    "Janela e teto pesam pouco: fluxos de baixa taxa",
], size=11)
notes(s, "Cada barra é o detector com uma melhoria a mais sobre o limiar fixed_q. Sozinhas, quase nenhuma faz diferença; "
         "o modelo congelado sobe para 16%; com todas juntas, 63%. Repetimos com 3 sementes: 59% a 68%, média 63,4%.\n\n"
         "ATENÇÃO ao enquadramento: o '0%' é contra o MODUS original e o fixed_q. O MODUS+ da Etapa 1 com o limiar "
         "'fixed' (sem rótulo) já dá F1 de 59%, mas só porque alarma 34% do tráfego benigno (precisão 42%, recall "
         "100%). O ganho real do MODUS++ é operar de forma utilizável: precisão 95% e 0,48% de falsos alarmes (eram "
         "2,4%). O F1 sozinho não mostra isso.\n\n"
         "Ablação (tirando uma peça por vez): sem o congelado, F1 0,2%; sem o aquecimento adaptativo, 19,7%. Janela e "
         "teto quase não pesam aqui porque o tráfego é lento, com poucos registros por segundo.")
page += 1

# 8. CTU-13
s = light_slide(prs)
header(s, "CTU-13: o envenenamento some, o limiar ainda falha", "Flood ICMP de ~20 mil pacotes/s nos 2 minutos finais", page)
picture(s, FIGS / "etapa2_ctu_timeline.png", 0.5, 1.88, h=3.42)
text(s, 4.0, 1.98, 5.5, 0.6, [[("100% ", {"color": DARK}), ("→ 2%", {"color": RED})]], size=32, bold=True)
text(s, 4.0, 2.62, 5.5, 0.3, "do flood usado no treino (janela de 10 s + teto por destino)", size=11, color=MUTED)
bullets(s, 4.0, 3.02, 5.5, 2.3, [
    [("AUC do score: ", {}), ("0,15% → 96,5%", {"bold": True}), (" (F1 com limiar ideal: 94,8%)", {})],
    [("Só o modelo congelado: ", {}), ("F1 69,6%", {"bold": True}), (" (precisão 91%)", {})],
    [("MODUS++ completo, a priori: ", {}), ("F1 ≈ 0%", {"bold": True}),
     (" — o flood fica em 0,774 e o limiar congelado em 0,777", {})],
    [("Sensibilidade: teto 0,1× → ", {}), ("F1 88,3%", {"bold": True}), ("; quantil 0,99 → 83,4%", {})],
    "Gargalo restante: calibrar o limiar sem rótulos",
], size=12)
notes(s, "À esquerda, a linha do tempo do flood (cerca de 20 mil pacotes por segundo nos dois minutos finais), com quanto "
         "dele cada versão detectou e quanto foi usado no aprendizado.\n\n"
         "Boa notícia: com a janela em tempo e o teto, o ataque usado no aprendizado cai de 100% para 2% e o detector "
         "volta a enxergar a diferença (AUC de 0,15% para 96,5%). Só o modelo congelado já chega a 69,6%.\n\n"
         "Má notícia: com tudo junto e os valores escolhidos de antemão, o alarme não dispara: o flood fica em 0,774 e "
         "o limiar em 0,777, três milésimos de diferença. O problema que queríamos resolver, a contaminação, foi "
         "resolvido; falta calibrar a linha de alarme SEM olhar as respostas.\n\n"
         "Os 83-88% (teto 0,1× e quantil 0,99) são teste de sensibilidade, não resultado, porque esses valores foram "
         "escolhidos depois de ver os dados. Esta é uma única captura (cenário 11).")
page += 1

# 9. Edge-IIoT
s = light_slide(prs)
header(s, "Edge-IIoT: 91% de F1 com 14 tipos de ataque", "21 milhões de pacotes; MODUS++ com a mesma config das outras bases", page)
cd = CategoryChartData()
cd.categories = ["MODUS orig.\n(config artigo)", "MODUS+ Et. 1\n(com rótulo)", "MODUS+ Et. 1\nsem rótulo", "MODUS+\nfixed_q", "MODUS++"]
cd.add_series("F1 (%)", (76.66, 91.05, 11.72, 0.01, 91.17))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.45), Inches(1.9), Inches(5.3), Inches(3.2), cd)
ch_ = gf.chart
ch_.has_legend = False
ch_.font.size, ch_.font.name = Pt(10), "Arial"
ch_.font.color.rgb = rgb(BODY)
plot = ch_.plots[0]
plot.gap_width = 60
plot.has_data_labels = True
dl = plot.data_labels
dl.number_format, dl.number_format_is_linked = '0.0', False
dl.position = XL_LABEL_POSITION.OUTSIDE_END
dl.font.size, dl.font.bold = Pt(11), True
ser = plot.series[0]
ser.format.fill.solid()
ser.format.fill.fore_color.rgb = rgb("8C8C8C")
for k, colr in ((1, "D9D9D9"), (4, RED)):
    pt = ser.points[k]
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = rgb(colr)
va = ch_.value_axis
va.maximum_scale, va.minimum_scale = 100, 0
va.has_major_gridlines = True
va.major_gridlines.format.line.color.rgb = rgb("E4E2DC")
va.format.line.fill.background()
va.tick_labels.font.size = Pt(9)
ch_.has_title = True
ch_.chart_title.text_frame.text = "F1 na fase operacional (%)"
ch_.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
ch_.chart_title.text_frame.paragraphs[0].runs[0].font.bold = False
text(s, 6.05, 1.98, 3.45, 0.6, [[("99,99% ", {"color": DARK}), ("→ 6,9%", {"color": RED})]], size=28, bold=True)
text(s, 6.05, 2.55, 3.45, 0.3, "do ataque usado no treino (fixed_q → MODUS++)", size=11, color=MUTED)
bullets(s, 6.05, 2.95, 3.45, 2.35, [
    "MODUS original: 76,7% (14 ataques), mas perde todo DDoS TCP e HTTP",
    "O MODUS+ da Etapa 1 dependia do rótulo: 91% → 11,7%",
    [("MODUS++: ", {"bold": True}), ("precisão 96%, recall 87%; FP no normal 3,1% (original: 0,12%)", {})],
    "DDoS ICMP, UDP e TCP ≥ 97%; HTTP 68%. Piora em Fingerprinting, MITM e Port scanning",
], size=11)
text(s, 0.5, 5.2, 8.3, 0.3, "* Só com DDoS (variante clean), o MODUS original dá 84,4% (artigo: 81,2%). Os 76,7% usam os 14 "
     "ataques, os mesmos dados do MODUS++.", size=9, color=MUTED)
notes(s, "Da esquerda para a direita: 76,7% é o MODUS original, com a configuração do artigo, nos 14 ataques (na "
         "variante só-DDoS ele dá 84,4%, contra 81,2% do artigo; a 'cola' não muda nada aqui porque o protocolo já "
         "separa). 91,1% é o MODUS+ da Etapa 1, medido com a cola. 11,7% é a mesma versão sem a cola: o resultado "
         "da Etapa 1 dependia dela. 0,0% é o detector-base sem as melhorias: 99,99% do ataque virou 'normal' no "
         "aprendizado. 91,2% é o MODUS++: só 6,9% do ataque contamina o aprendizado.\n\n"
         "MODUS++: precisão 96%, recall 87%, 3,1% de falsos alarmes no normal. Os ataques volumétricos (ICMP, UDP, TCP) "
         "passam de 97%; o DDoS HTTP, 68%. A configuração é a mesma das outras bases.\n\n"
         "Seja franco sobre o custo: o MODUS original tinha só 0,12% de falsos alarmes no normal e vai melhor em "
         "Fingerprinting (69% contra 35%), MITM (67% contra 18%) e Port scanning (11% contra 6%). O F1 de 91% é "
         "dominado pelos ataques volumétricos, que são a maior parte dos pacotes de ataque.")
page += 1

# 10. Ataques não-DDoS
s = light_slide(prs)
header(s, "Teste com ataques não-DDoS (melhoria 4)", "Ataques que o aquecimento nunca viu (ASEADOS com 5 classes)", page)
rows = [("Tipo", "MODUS original", "MODUS+ fixed_q", "MODUS+ fixed", "MODUS++"),
        ("Bot", "0%", "0%", "100%", "22,9%"), ("DDoS", "0%", "0%", "100%", "38,8%"),
        ("DoS", "0%", "0,6%", "16,1%", "11,0%"), ("Probe", "0%", "0%", "100%", "100%"),
        ("Benigno (FP)", "0%", "0,08%", "32,8%", "17,9%"), ("F1 geral", "0%", "0,7%", "50,8%", "31,2%")]
tbl = s.shapes.add_table(len(rows), 5, Inches(0.5), Inches(1.98), Inches(5.4), Inches(3.1)).table
for j, wd in enumerate((1.3, 1.05, 1.05, 1.0, 1.0)):
    tbl.columns[j].width = Inches(wd)
for i, row in enumerate(rows):
    for j, v in enumerate(row):
        c = tbl.cell(i, j)
        c.fill.solid()
        c.fill.fore_color.rgb = rgb(DARK if i == 0 else ("FFFFFF" if i % 2 else CARD))
        tf = c.text_frame
        tf.paragraphs[0].alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.RIGHT
        r = tf.paragraphs[0].add_run()
        r.text = v
        r.font.size, r.font.name = Pt(11), "Arial"
        r.font.bold = i == 0 or i == len(rows) - 1 or (j == 4 and i > 0)
        r.font.color.rgb = rgb("FFFFFF" if i == 0 else (RED if j == 4 and i == len(rows) - 1 else DARK))
text(s, 6.15, 1.98, 3.35, 0.3, "Taxa de alarme por tipo (fase operacional)", size=11, color=MUTED)
bullets(s, 6.15, 2.4, 3.35, 2.9, [
    "MODUS original: nenhum alarme em ataque novo (F1 0%)",
    [("MODUS+ fixed (Etapa 1): ", {"bold": True}), ("F1 50,8%, mas alarma 33% do tráfego benigno", {})],
    "MODUS++: pega todo o Probe e parte de Bot e DDoS, com 18% de FP: ainda alto",
    [("Edge-IIoT: ", {"bold": True}),
     ("78% do scanner de vulnerabilidades e 43% do ransomware; XSS (4%), SQL injection (16%), Password (9%) e "
      "Backdoor (13%) ainda passam", {})],
], size=11)
notes(s, "Por que importa: o artigo diz que o método detectaria ataques nunca vistos ('zero-day'). Para testar, "
         "deixamos entrar na ASEADOS os ataques que o artigo havia removido (Bot, DoS, Probe).\n\n"
         "O MODUS original não alarma nada (F1 0%). O MODUS+ da Etapa 1 com limiar 'fixed' chega a F1 50,8%, mas "
         "alarmando 33% do benigno, então não é utilizável. O MODUS++ pega 100% das varreduras (Probe), 39% do DDoS, "
         "23% dos bots e 11% do DoS; F1 de 31%, com 18% de falsos alarmes, que ainda é alto.\n\n"
         "No Edge-IIoT: 78% do scanner de vulnerabilidades e 43% do ransomware, mas XSS (4%), SQL injection (16%), "
         "Password (9%) e Backdoor (13%) ainda passam. Conclusão: melhorou, mas está longe de detectar qualquer ataque "
         "desconhecido, principalmente os discretos.")
page += 1

# 11. Resumo: proposta x implementado
s = light_slide(prs)
header(s, "Proposto x implementado", "Efeito de cada melhoria, sem vazamento e com a mesma config nas três bases", page)
rows = [("Melhoria", "Origem", "ASEADOS", "CTU-13", "Edge-IIoT"),
        ("Normalização + taxa", "Etapa 1", "não basta", "não basta", "não basta"),
        ("Aquec. adaptativo", "proposta 3", "essencial", "35 mil inst.", "5 mil inst."),
        ("Janela em tempo", "trab. futuro", "pouco efeito", "envenen. → 2%", "envenen. → 6,9%"),
        ("Teto de treino", "trab. futuro", "pouco efeito", "(com a janela)", "(conjunto)"),
        ("Modelo congelado", "trab. futuro", "essencial", "F1 69,6% só", "(conjunto)"),
        ("MODUS++ (todas)", "", "F1 0% → 63%", "F1 ≈ 0% a priori", "F1 76,7% → 91,2%"),
        ("Teste não-DDoS", "proposta 4", "0,7% → 31%", "–", "14 ataques")]
tbl = s.shapes.add_table(len(rows), 5, Inches(0.5), Inches(1.98), Inches(9.0), Inches(3.15)).table
for j, wd in enumerate((2.0, 1.4, 1.8, 1.9, 1.9)):
    tbl.columns[j].width = Inches(wd)
for i, row in enumerate(rows):
    for j, v in enumerate(row):
        c = tbl.cell(i, j)
        c.fill.solid()
        c.fill.fore_color.rgb = rgb(DARK if i == 0 else ("FFFFFF" if i % 2 else CARD))
        r = c.text_frame.paragraphs[0].add_run()
        r.text = v
        r.font.size, r.font.name = Pt(11), "Arial"
        r.font.bold = i == 0 or j == 0 or i == 6
        r.font.color.rgb = rgb("FFFFFF" if i == 0 else (RED if i == 6 and j > 1 else DARK))
notes(s, "Resumo e prestação de contas: tudo o que foi prometido na Etapa 1 foi implementado e medido.\n\n"
         "Normalização e taxa por janela (Etapa 1) não bastam sozinhas. Aquecimento adaptativo e modelo congelado são "
         "decisivos na ASEADOS. Janela em tempo e teto são decisivos contra a contaminação na CTU-13 e na Edge-IIoT. "
         "O teste com outros ataques melhorou, mas ainda tem muito alarme falso.\n\n"
         "Lembrar: o '0% → 63%' do ASEADOS é contra o MODUS original/fixed_q; contra o limiar 'fixed' da Etapa 1 "
         "(F1 59%) o ganho é de precisão (42% → 95%) e de falsos alarmes (34% → 0,5%).")
page += 1

# 12. Limitações
s = light_slide(prs)
header(s, "Limitações e ameaças à validade", "O que ainda pode mudar os números", page)
lim = [
    ("1", "Ordem do ASEADOS", "A ordem do artigo vem de um erro de leitura de data. Na ordem cronológica correta, o DDoS cai no aquecimento: F1 0%."),
    ("2", "Limiar sem rótulos", "CTU-13: flood em 0,774 e limiar em 0,777. O resultado a priori depende de milésimos (F1 ≈ 0%)."),
    ("3", "Falsos alarmes", "ASEADOS (5 classes): 17,9% de FP. Edge-IIoT: 3,1% (MODUS original: 0,12%)."),
    ("4", "Ataques discretos", "XSS (4%), SQL injection (16%), Password (9%) e Backdoor (13%) passam; MITM e Fingerprinting pioram."),
    ("5", "Escopo", "1 cenário no CTU-13; 3 sementes só no ASEADOS; 1 execução no Edge-IIoT; tempos medidos com rodadas em paralelo."),
    ("6", "Avaliação", "Ablação e sensibilidade rodam nos mesmos dados da avaliação; os parâmetros foram fixados antes, mas não há validação separada."),
]
for i, (b, t, d) in enumerate(lim):
    card(s, 0.5 + (i % 3) * (2.92 + 0.13), 1.94 + (i // 3) * (1.55 + 0.13), 2.92, 1.55, b, t, d, size=10.5)
notes(s, "Slide de honestidade: o que ainda pode mudar os números.\n\n"
         "1) A ordem 'temporal' do ASEADOS é a do artigo, que vem de um erro de leitura de data (dd/mm lido como "
         "mm/dd). Na ordem cronológica correta, o DDoS cai no aquecimento e o F1 é 0% para o MODUS original. "
         "2) O limiar sem rótulos ainda é frágil. 3) O MODUS++ troca falsos alarmes por cobertura. 4) Os ataques "
         "discretos continuam passando. 5) Escopo estatístico limitado. 6) Não há conjunto de validação separado.")
page += 1

# 13. Insumos e reprodutibilidade
s = light_slide(prs)
header(s, "Insumos e reprodutibilidade", "Tudo o que foi gerado no estudo está no repositório, por rodada", page)
items = [
    ("Código", "MODUS, MODUS++ e HST em numpy (idêntico ao MOA); run.py roda qualquer config"),
    ("Logs e métricas", "89 rodadas: log.txt e metrics.json com a config exata de cada uma"),
    ("Amostras", "10 mil instâncias por rodada principal (score, limiar, predição, rótulo)"),
    ("Modelos", "HST adaptativo final e HST congelado do MODUS++ nas 3 bases (model.npz)"),
    ("Imagens", "Figuras dos slides e do artigo (results/figs, paper/figs)"),
    ("Tabelas", "modus_pp.md (Etapa 2), tabela_rodadas.md e comparacao.md (Etapa 1)"),
]
for i, (title, body) in enumerate(items):
    x, y = 0.5 + (i % 3) * 3.05, 1.95 + (i // 3) * 1.4
    card(s, x, y, 2.9, 1.28, str(i + 1), title, body, size=10)
text(s, 0.5, 4.85, 9.0, 0.3,
     [[("github.com/pedro664/replicacao-modus", {"bold": True, "color": RED}),
       ("  ·  branch etapa2-melhorias  ·  guia completo em CLAUDE.md e README.md", {})]],
     size=12, color=DARK)
notes(s, "Reprodutibilidade: tudo o que foi gerado está no repositório, por rodada. Código (MODUS, MODUS++ e o HST em "
         "numpy, idêntico ao do MOA), logs e métricas de 89 rodadas com a configuração exata de cada uma, amostras de "
         "10 mil instâncias das rodadas principais, os modelos finais (HST adaptativo e HST congelado) nas 3 bases, "
         "as figuras e as tabelas. O guia completo está no CLAUDE.md e no README.")
page += 1

# 14. Conclusões
s = prs.slides.add_slide(BLANK)
box(s, 0, 0, 5.0, 5.63, DARK)
box(s, 4.95, 0, 5.05, 5.63, RED2)
box(s, 0.9, 1.77, 3.2, 0.72, RED2)
text(s, 0.9, 1.84, 3.2, 0.57, "Conclusões", size=24, color="FFFFFF", bold=True, align=PP_ALIGN.CENTER,
     anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.84, 2.85, 3.46, 0.44, "e próximos passos", size=15, color="FFFFFF", bold=True, align=PP_ALIGN.CENTER)
text(s, 5.33, 0.42, 4.33, 0.3, "Conclusões", size=15, color="FFFFFF", bold=True)
bullets(s, 5.33, 0.78, 4.33, 2.6, [
    "Nossa réplica do ASEADOS (99,73%; artigo: 99,62%) só existe com o HST vendo o rótulo; sem ele, 0%",
    "O problema central é o envenenamento: treinar só o \"benigno\" não protege",
    "Modelo congelado + aquecimento adaptativo: ASEADOS 0% → 63% de F1, com precisão de 95%",
    "Janela em tempo + teto: envenenamento no CTU-13 de 100% → 2%",
    "Edge-IIoT, 14 ataques: F1 76,7% (original) → 91,2%",
], size=11, color="FFFFFF", marker="FFFFFF")
text(s, 5.33, 3.5, 4.33, 0.3, "Próximos passos", size=15, color="FFFFFF", bold=True)
bullets(s, 5.33, 3.86, 4.33, 1.5, [
    "Limiar sem rótulos que não fique no fio da navalha",
    "Ataques web no Edge-IIoT (XSS, SQL) e mais sementes",
    "Artigo IEEE escrito (10 páginas): falta a revisão final",
], size=12, color="FFFFFF", marker="FFFFFF")
notes(s, "Conclusões: (1) a nossa réplica do ASEADOS só existe com o detector vendo o rótulo; sem isso, 0%. (2) O "
         "verdadeiro calcanhar de Aquiles do método é o envenenamento: aprender só com o que parece inofensivo não "
         "protege contra um ataque rápido. (3) Modelo congelado + aquecimento adaptativo levam o ASEADOS de 0% a 63%, "
         "com 95% de precisão. (4) Janela em tempo + teto derrubam a contaminação na CTU-13 de 100% para 2%. "
         "(5) No Edge-IIoT, com 14 tipos de ataque, o F1 vai de 77% (original) para 91%.\n\n"
         "Próximos passos: posicionar a linha de alarme sem depender de sorte nem das respostas; melhorar a detecção "
         "de ataques web discretos e repetir com mais sementes; fazer a revisão final do artigo IEEE (já escrito, 10 páginas).")

# encerramento: troca o QR do template pelo do repositório e acrescenta o roteiro de perguntas às notas
qr_pic = next(sh for sh in closing.shapes if sh.name == "Google Shape;170;p25")
closing.part.related_part(qr_pic._element.blipFill.blip.rEmbed)._blob = qr_png("https://" + REPO)
cx_mid = qr_pic.left + qr_pic.width // 2
qr_pic.width = qr_pic.height = Inches(2.6)
qr_pic.left = cx_mid - qr_pic.width // 2
text(closing, 4.99, 2.78, 4.3, 0.4,
     [[("Código, dados e resultados", {"size": 10, "color": MUTED})],
      [(REPO, {"size": 12, "bold": True, "color": DARK})]],
     align=PP_ALIGN.CENTER, space_after=1)
notes(closing, "Agradecer e abrir para perguntas.\n\n"
               "PERGUNTAS PROVÁVEIS\n"
               "- 'Então o artigo está errado?' Não dá para afirmar: sem o código dos autores não sabemos o que fizeram. "
               "Mostramos que a NOSSA réplica só alcança os 99% quando o detector vê a resposta, e que a ferramenta "
               "mais comum para esse tipo de método tem essa falha.\n"
               "- 'Por que não ajustaram o limiar para dar um número melhor?' Seria ajustar o detector olhando a "
               "resposta da prova, o mesmo erro que estamos apontando. Os números ajustados aparecem só como "
               "sensibilidade.\n"
               "- 'O MODUS+ fixed já dá 59% no ASEADOS.' Dá, mas alarmando 34% do benigno (precisão 42%). O MODUS++ "
               "tem F1 parecido com precisão de 95% e 0,5% de falsos alarmes: o ganho é de utilidade, não de F1.\n"
               "- 'O MODUS++ piora em algo?' Sim: falsos alarmes no normal do Edge-IIoT (0,12% → 3,1%) e detecção de "
               "Fingerprinting, MITM e Port scanning. Ganha nos ataques volumétricos.\n"
               "- 'O que é F1?' Nota de 0 a 100% que equilibra quanto do ataque foi pego e quantos alarmes eram "
               "ataque de fato.\n"
               "- 'O que é AUC?' Mede se o detector dá notas mais altas ao ataque que ao normal, "
               "independentemente do limiar. 100% é separação perfeita, 50% é chute, abaixo de 50% é 'ao contrário'.")

# encerramento vai para o fim
ids = list(sldIdLst)
closing_id = ids[1]
sldIdLst.remove(closing_id)
sldIdLst.append(closing_id)

prs.save(str(OUT))
print("salvo", OUT)
