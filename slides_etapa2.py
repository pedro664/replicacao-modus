"""Gera os slides da Etapa 2 (implementação das melhorias) a partir do deck da Etapa 1.

Mantém a capa e o encerramento do deck original (identidade visual do CIn) e cria os slides de
conteúdo no mesmo estilo. Números tirados de results/modus_pp.md.

  python slides_etapa2.py   ->  Replicacao_MODUS_CIn_Etapa2.pptx
"""

import copy
from pathlib import Path

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

page = 2

# 2. Onde paramos
s = dark_slide(prs)
box(s, 0, 0.94, 3.6, 0.65, RED)
text(s, 0.35, 0.99, 3.2, 0.54, "Onde paramos", size=30, color="FFFFFF", bold=True, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.36, 1.86, 9.17, 0.83, "Etapa 1 replicou o MODUS e propôs melhorias; a Etapa 2 implementa e mede cada uma",
     size=20, color="FFFFFF", bold=True)
stat(s, 0.36, 2.97, 2.78, "2 de 3", "bases replicadas (ASEADOS e Edge-IIoT); CTU-13 com rótulos inconsistentes")
stat(s, 3.5, 2.97, 2.78, "0", "efeito da flag do ADWIN, a contribuição central do artigo")
stat(s, 6.64, 2.97, 2.78, "≈ 0%", "recall no CTU-13 com as variantes novas: o flood envenena o treino")
page += 1

# 3. Achado novo: vazamento
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
page += 1

# 4. Sem vazamento: envenenamento
s = dark_slide(prs)
box(s, 0, 0.94, 4.3, 0.65, RED)
text(s, 0.35, 0.99, 3.9, 0.54, "O problema real", size=30, color="FFFFFF", bold=True, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.36, 1.86, 9.17, 0.83, "Sem o rótulo, o ataque passa no início, treina o modelo e vira o \"normal\"",
     size=20, color="FFFFFF", bold=True)
stat(s, 0.36, 2.97, 2.78, "99,96%", "do DDoS do ASEADOS entra no treino do HST (MODUS+ fixed_q)")
stat(s, 3.5, 2.97, 2.78, "100%", "do flood do CTU-13 entra no treino; AUC do score: 0,15%")
stat(s, 6.64, 2.97, 2.78, "AUC < 0,5", "nas duas bases: o detector acha o ataque mais normal que o tráfego benigno")
page += 1

# 5. O que implementamos
s = light_slide(prs)
header(s, "O que implementamos: MODUS++", "A melhoria 3 proposta e os 3 trabalhos futuros, todos sem rótulos e de passagem única", page)
cw, ch, gx, gy = 2.92, 1.55, 0.13, 0.13
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
page += 1

# 6. ASEADOS
s = light_slide(prs)
header(s, "ASEADOS: de 0% a 63% de F1", "Ablação: cada melhoria sozinha quase não muda nada; juntas, sim", page)
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
    "Envenenamento: 99,96% → 51% do DDoS no treino",
    [("Sem o congelado: ", {"bold": True}), ("F1 0,2%", {})],
    [("Sem aquec. adaptativo: ", {"bold": True}), ("F1 19,7%", {})],
    "Janela e teto pesam pouco: fluxos de baixa taxa",
], size=12)
page += 1

# 7. CTU-13
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
page += 1

# 8. Edge-IIoT
s = light_slide(prs)
header(s, "Edge-IIoT: 91% de F1 com 14 tipos de ataque", "21 milhões de pacotes; MODUS++ com a mesma config das outras bases", page)
cd = CategoryChartData()
cd.categories = ["MODUS orig.\n(config artigo)", "MODUS+ Et. 1\n(com rótulo)", "MODUS+ Et. 1\nsem rótulo", "MODUS+\nfixed_q", "MODUS++"]
cd.add_series("F1 (%)", (76.66, 91.05, 11.72, 0.01, 91.17))
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
    "MODUS original: 76,7%, sem depender do rótulo, mas perde todo DDoS TCP e HTTP",
    "O MODUS+ da Etapa 1 dependia do rótulo: 91% → 11,7%",
    [("MODUS++: ", {"bold": True}), ("precisão 96%, recall 87%, FP no normal 3,1%", {})],
    "MODUS++: DDoS ICMP, UDP e TCP ≥ 97%; HTTP 68%",
], size=12)
page += 1

# 8. Ataques não-DDoS
s = light_slide(prs)
header(s, "Teste com ataques não-DDoS (melhoria 4)", "Ataques que o aquecimento nunca viu: tabela do ASEADOS (5 classes); Edge-IIoT ao lado", page)
rows = [("Tipo", "MODUS+ fixed_q", "MODUS++"), ("Bot", "0%", "22,9%"), ("DDoS", "0%", "38,8%"),
        ("DoS", "0,6%", "11,0%"), ("Probe", "0%", "100%"), ("Benigno (FP)", "0,08%", "17,9%"),
        ("F1 geral", "0,7%", "31,2%")]
tbl = s.shapes.add_table(len(rows), 3, Inches(0.5), Inches(1.98), Inches(4.6), Inches(3.1)).table
tbl.columns[0].width, tbl.columns[1].width, tbl.columns[2].width = Inches(1.7), Inches(1.45), Inches(1.45)
for i, row in enumerate(rows):
    for j, v in enumerate(row):
        c = tbl.cell(i, j)
        c.fill.solid()
        c.fill.fore_color.rgb = rgb(DARK if i == 0 else ("FFFFFF" if i % 2 else CARD))
        tf = c.text_frame
        tf.paragraphs[0].alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.RIGHT
        r = tf.paragraphs[0].add_run()
        r.text = v
        r.font.size, r.font.name = Pt(12), "Arial"
        r.font.bold = i == 0 or i == len(rows) - 1 or (j == 2 and i > 0)
        r.font.color.rgb = rgb("FFFFFF" if i == 0 else (RED if j == 2 and i == len(rows) - 1 else DARK))
text(s, 5.45, 1.98, 4.05, 0.3, "Taxa de alarme por tipo (fase operacional)", size=11, color=MUTED)
bullets(s, 5.45, 2.4, 4.05, 2.9, [
    "O MODUS original não alarma nenhum ataque novo",
    "O MODUS++ pega todo o Probe e parte de Bot e DDoS, ao custo de 18% de FP",
    [("Edge-IIoT: ", {"bold": True}),
     ("78% do scanner de vulnerabilidades e 43% do ransomware; XSS (4%) e SQL injection (16%) ainda passam", {})],
], size=12)
page += 1

# 9. Resumo: proposta x implementado
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
page += 1

# 10. Conclusões
s = prs.slides.add_slide(BLANK)
box(s, 0, 0, 5.0, 5.63, DARK)
box(s, 4.95, 0, 5.05, 5.63, RED2)
box(s, 0.9, 1.77, 3.2, 0.72, RED2)
text(s, 0.9, 1.84, 3.2, 0.57, "Conclusões", size=24, color="FFFFFF", bold=True, align=PP_ALIGN.CENTER,
     anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.84, 2.85, 3.46, 0.44, "e próximos passos", size=15, color="FFFFFF", bold=True, align=PP_ALIGN.CENTER)
text(s, 5.33, 0.42, 4.33, 0.3, "Conclusões", size=15, color="FFFFFF", bold=True)
bullets(s, 5.33, 0.78, 4.33, 2.6, [
    "Nossa réplica do 99,62% (ASEADOS) só existe com o HST vendo o rótulo; sem ele, 0%",
    "O problema central é o envenenamento: treinar só o \"benigno\" não protege",
    "Modelo congelado + aquecimento adaptativo: ASEADOS 0% → 63%",
    "Janela em tempo + teto: envenenamento no CTU-13 de 100% → 2%",
    "Edge-IIoT, 14 ataques: F1 76,7% (original) → 91,2%",
], size=11, color="FFFFFF", marker="FFFFFF")
text(s, 5.33, 3.5, 4.33, 0.3, "Próximos passos", size=15, color="FFFFFF", bold=True)
bullets(s, 5.33, 3.86, 4.33, 1.5, [
    "Limiar sem rótulos que não fique no fio da navalha",
    "Ataques web no Edge-IIoT (XSS, SQL) e mais sementes",
    "Artigo IEEE (8 páginas) até 25/11",
], size=12, color="FFFFFF", marker="FFFFFF")

# encerramento vai para o fim
ids = list(sldIdLst)
closing_id = ids[1]
sldIdLst.remove(closing_id)
sldIdLst.append(closing_id)

prs.save(str(OUT))
print("salvo", OUT)
