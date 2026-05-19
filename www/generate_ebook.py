"""
Generate rich visual PDF ebook from micro:bit 48 activities
With: colored blocks, LED grids, syntax-highlighted code, diagrams
"""
import re, json, math
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                 Table, TableStyle, KeepTogether, Flowable)
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.graphics.shapes import Drawing, Rect, Circle, String, Group
from reportlab.graphics import renderPDF

W, H = A4

# ── Parse activities from index.html ──
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

js_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
js = js_match.group(1) if js_match else ""

activities = []
mk_pattern = re.compile(
    r'mk\((\d+),"([^"]+)","(\w+)",\{([^}]+)\},\s*"([^"]+)",\s*\[([^\]]+)\],\s*"([^"]+)",\s*\[([^\]]*)\],\s*`((?:\\.|[^`\\])*)`\s*,\s*`((?:\\.|[^`\\])*)`\s*,\s*\[([^\]]*)\]\s*\)',
    re.DOTALL
)
for m in mk_pattern.finditer(js):
    aid = int(m.group(1))
    meta_str = m.group(4)
    diff_m = re.search(r'difficulty:(\d)', meta_str)
    time_m = re.search(r'time:"([^"]+)"', meta_str)
    chal_str = m.group(11)
    challenges = []
    for cm2 in re.finditer(r'\{t:"([^"]+)",d:(\d)\}', chal_str):
        challenges.append({"t": re.sub(r'<[^>]+>', '', cm2.group(1)), "d": int(cm2.group(2))})
    activities.append({
        "id": aid, "title": m.group(2), "part": m.group(3),
        "difficulty": int(diff_m.group(1)) if diff_m else 1,
        "time": time_m.group(1) if time_m else "",
        "v2": "v2:true" in meta_str, "ia": "ia:true" in meta_str,
        "goal": m.group(5), "needs": re.findall(r'"([^"]+)"', m.group(6)),
        "tip": m.group(7), "blocks": re.findall(r'"([^"]+)"', m.group(8)),
        "codeJS": m.group(9).strip(), "codePY": m.group(10).strip(),
        "challenges": challenges
    })
activities.sort(key=lambda a: a["id"])
EXPECTED = 48
assert len(activities) == EXPECTED, f"Parsed {len(activities)}; expected {EXPECTED}. IDs: {[a['id'] for a in activities]}"
print(f"Extracted {len(activities)} activities")

# ── LED Icon Patterns ──
LED_ICONS = {
    "Heart":      [0,1,0,1,0, 1,1,1,1,1, 1,1,1,1,1, 0,1,1,1,0, 0,0,1,0,0],
    "Happy":      [0,0,0,0,0, 0,1,0,1,0, 0,0,0,0,0, 1,0,0,0,1, 0,1,1,1,0],
    "Sad":        [0,0,0,0,0, 0,1,0,1,0, 0,0,0,0,0, 0,1,1,1,0, 1,0,0,0,1],
    "Flash":      [0,0,1,0,0, 0,1,1,0,0, 1,1,1,1,1, 0,0,1,1,0, 0,0,1,0,0],
    "No":         [1,0,0,0,1, 0,1,0,1,0, 0,0,1,0,0, 0,1,0,1,0, 1,0,0,0,1],
    "Yes":        [0,0,0,0,0, 0,0,0,0,1, 0,0,0,1,0, 1,0,1,0,0, 0,1,0,0,0],
    "Asleep":     [0,0,0,0,0, 1,1,0,1,1, 0,0,0,0,0, 0,1,1,1,0, 0,0,0,0,0],
    "Skull":      [0,1,1,1,0, 1,0,1,0,1, 1,1,1,1,1, 0,1,1,1,0, 0,1,1,1,0],
    "ArrowNorth": [0,0,1,0,0, 0,1,1,1,0, 1,0,1,0,1, 0,0,1,0,0, 0,0,1,0,0],
    "Meh":        [0,0,0,0,0, 0,1,0,1,0, 0,0,0,0,0, 0,0,0,0,0, 1,1,1,1,1],
    "Target":     [0,0,1,0,0, 0,1,1,1,0, 1,1,0,1,1, 0,1,1,1,0, 0,0,1,0,0],
}

def detect_led_pattern(code):
    m = re.search(r'showIcon\(IconNames\.(\w+)\)', code)
    if m and m.group(1) in LED_ICONS: return LED_ICONS[m.group(1)]
    m = re.search(r'showLeds\s*\(\s*`([^`]+)`', code)
    if m:
        p = [1 if c == '#' else 0 for c in m.group(1) if c in '#.']
        if len(p) == 25: return p
    return None

# ── Custom Flowable: LED Grid ──
class LEDGrid(Flowable):
    def __init__(self, pattern, size=60):
        Flowable.__init__(self)
        self.pattern = pattern or [0]*25
        self.size = size
        self.width = size
        self.height = size

    def draw(self):
        c = self.canv
        s = self.size
        cell = s / 5
        pad = cell * 0.15
        # Background
        c.setFillColor(HexColor("#111111"))
        c.roundRect(0, 0, s, s, 4, fill=1, stroke=0)
        # LEDs
        for i in range(25):
            x = (i % 5) * cell + pad
            y = s - (i // 5 + 1) * cell + pad
            w = cell - 2*pad
            if self.pattern[i]:
                c.setFillColor(HexColor("#ff1a1a"))
            else:
                c.setFillColor(HexColor("#1a1a1a"))
            c.roundRect(x, y, w, w, w*0.3, fill=1, stroke=0)

# ── Custom Flowable: MakeCode Block ──
class BlockChip(Flowable):
    def __init__(self, text, color="#1E90FF", w=None):
        Flowable.__init__(self)
        self.text = text
        self.color = color
        self.bw = w or (len(text) * 5.5 + 16)
        self.width = self.bw
        self.height = 22

    def draw(self):
        c = self.canv
        c.setFillColor(HexColor(self.color))
        c.roundRect(0, 0, self.bw, 20, 4, fill=1, stroke=0)
        # Dark bottom edge
        c.setFillColor(HexColor("#00000040"))
        c.rect(0, 0, self.bw, 3, fill=1, stroke=0)
        # Text
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(8, 6, self.text)

# ── Custom Flowable: micro:bit board diagram ──
class MicrobitDiagram(Flowable):
    def __init__(self, show_pins=False):
        Flowable.__init__(self)
        self.show_pins = show_pins
        self.width = 180
        self.height = 120

    def draw(self):
        c = self.canv
        # Board
        c.setFillColor(HexColor("#333333"))
        c.roundRect(10, 10, 160, 100, 12, fill=1, stroke=0)
        # LED grid
        c.setFillColor(HexColor("#111111"))
        c.roundRect(50, 40, 80, 50, 4, fill=1, stroke=0)
        for i in range(25):
            x = 54 + (i%5)*15
            y = 75 - (i//5)*10
            c.setFillColor(HexColor("#ff1a1a") if (i%3==0) else HexColor("#330000"))
            c.circle(x, y, 3, fill=1, stroke=0)
        # Buttons
        c.setFillColor(HexColor("#666666"))
        c.circle(30, 65, 8, fill=1, stroke=0)
        c.circle(150, 65, 8, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(30, 63, "A")
        c.drawCentredString(150, 63, "B")
        # Pins
        if self.show_pins:
            pins = ["0","1","2","3V","GND"]
            for i, p in enumerate(pins):
                x = 30 + i*30
                c.setFillColor(HexColor("#FFD700"))
                c.circle(x, 15, 6, fill=1, stroke=0)
                c.setFillColor(black)
                c.setFont("Helvetica", 5)
                c.drawCentredString(x, 13, p)

# ── Styles ──
styles = getSampleStyleSheet()
styles.add(ParagraphStyle('BookTitle', fontSize=32, textColor=HexColor("#1E90FF"),
                           spaceAfter=10, alignment=TA_CENTER, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle('BookSub', fontSize=14, textColor=HexColor("#888"),
                           spaceAfter=30, alignment=TA_CENTER))
styles.add(ParagraphStyle('ActTitle', fontSize=16, textColor=HexColor("#1E90FF"),
                           spaceBefore=0, spaceAfter=4, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle('SecHead', fontSize=10, textColor=HexColor("#1E90FF"),
                           spaceBefore=8, spaceAfter=3, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle('Body', fontSize=9, textColor=black,
                           spaceAfter=3, leading=12))
styles.add(ParagraphStyle('CodeJS', fontSize=7.5, fontName='Courier',
                           textColor=HexColor("#1a1a2e"), leading=10, leftIndent=8,
                           backColor=HexColor("#FFF8E1"), borderColor=HexColor("#F7DF1E"),
                           borderWidth=0.5, borderPadding=4, borderRadius=3))
styles.add(ParagraphStyle('CodePY', fontSize=7.5, fontName='Courier',
                           textColor=HexColor("#1a1a2e"), leading=10, leftIndent=8,
                           backColor=HexColor("#E8F0FE"), borderColor=HexColor("#306998"),
                           borderWidth=0.5, borderPadding=4, borderRadius=3))
styles.add(ParagraphStyle('Tip', fontSize=8.5, textColor=HexColor("#b8860b"),
                           leading=11, leftIndent=12, backColor=HexColor("#FFFDE7"),
                           borderColor=HexColor("#FFD700"), borderWidth=0.5,
                           borderPadding=5, borderRadius=3, spaceAfter=4))
styles.add(ParagraphStyle('Meta', fontSize=8, textColor=HexColor("#888"), spaceAfter=6))
styles.add(ParagraphStyle('ChalStyle', fontSize=8.5, textColor=HexColor("#333"),
                           spaceAfter=2, leading=11, leftIndent=12))
styles.add(ParagraphStyle('TOCEntry', fontSize=9.5, textColor=black, spaceAfter=2, leading=13))
styles.add(ParagraphStyle('TOCHead', fontSize=12, textColor=HexColor("#1E90FF"),
                           spaceBefore=10, spaceAfter=4, fontName='Helvetica-Bold'))

def esc(t): return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

# Block category colors
BLOCK_COLORS = {
    "basic":"#1E90FF","input":"#D400D4","loops":"#00AA00","logic":"#00A4A6",
    "music":"#E63022","radio":"#E3008C","variables":"#DC143C","pins":"#3BDDD4",
    "math":"#9400D3","game":"#7600A8","functions":"#3455DB"
}

def detect_block_chips(code):
    chips = []
    patterns = [
        (r'basic\.showString', "afficher texte", "basic"),
        (r'basic\.showIcon', "montrer icone", "basic"),
        (r'basic\.showNumber', "afficher nombre", "basic"),
        (r'basic\.clearScreen', "effacer ecran", "basic"),
        (r'basic\.pause', "pause", "basic"),
        (r'basic\.forever', "repeter", "loops"),
        (r'input\.onButtonPressed', "bouton", "input"),
        (r'input\.onGesture', "geste", "input"),
        (r'input\.onLogoEvent', "logo", "input"),
        (r'input\.temperature', "temperature", "input"),
        (r'input\.lightLevel', "lumiere", "input"),
        (r'input\.soundLevel', "son", "input"),
        (r'randint', "hasard", "math"),
        (r'music\.', "musique", "music"),
        (r'radio\.', "radio", "radio"),
        (r'pins\.', "broches", "pins"),
        (r'led\.plot', "LED", "game"),
        (r'game\.', "sprite", "game"),
        (r'if\s*\(', "si/sinon", "logic"),
        (r'function\s+\w', "fonction", "functions"),
    ]
    seen = set()
    for pat, label, cat in patterns:
        if re.search(pat, code) and label not in seen:
            seen.add(label)
            chips.append(BlockChip(label, BLOCK_COLORS.get(cat, "#888")))
    return chips

# ── Build PDF ──
output_path = "ebook-microbit-48-activities.pdf"
doc = SimpleDocTemplate(output_path, pagesize=A4,
                        topMargin=1.8*cm, bottomMargin=1.8*cm,
                        leftMargin=1.8*cm, rightMargin=1.8*cm)
story = []

# Cover
story.append(Spacer(1, 3*cm))
story.append(MicrobitDiagram(show_pins=True))
story.append(Spacer(1, 1*cm))
story.append(Paragraph("Micro:bit", styles['BookTitle']))
story.append(Paragraph("48 Activites Pratiques", styles['BookTitle']))
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("Blocs + JavaScript + Python", styles['BookSub']))
story.append(Paragraph("Du clignotement LED aux robots IA", styles['BookSub']))
story.append(Spacer(1, 2*cm))
story.append(Paragraph("Workshop DIY - abourdim", styles['BookSub']))
story.append(PageBreak())

# TOC
story.append(Paragraph("Table des matieres", styles['BookTitle']))
story.append(Spacer(1, 0.3*cm))
cur_part = ""
for a in activities:
    if a["part"] != cur_part:
        cur_part = a["part"]
        story.append(Paragraph("<b>SIMPLE (1-22)</b>" if cur_part=="simple" else "<b>AVANCE (23-48)</b>", styles['TOCHead']))
    stars = "*" * a["difficulty"]
    tags = f"{stars} {a['time']}"
    if a["v2"]: tags += " V2"
    if a["ia"]: tags += " IA"
    story.append(Paragraph(f"<b>#{a['id']}</b> {esc(a['title'])}  <font color='#888' size='7'>{tags}</font>", styles['TOCEntry']))
story.append(PageBreak())

# Activities
for a in activities:
    elems = []
    stars = "*" * a["difficulty"] + " " * (3-a["difficulty"])
    meta = f"{stars} | {a['time']}"
    if a["v2"]: meta += " | V2"
    if a["ia"]: meta += " | IA"

    elems.append(Paragraph(f"<font color='#888' size='8'>Activite #{a['id']} | {a['part'].upper()}</font>", styles['Meta']))
    elems.append(Paragraph(esc(a['title']), styles['ActTitle']))
    elems.append(Paragraph(meta, styles['Meta']))

    # Goal
    elems.append(Paragraph("OBJECTIF", styles['SecHead']))
    elems.append(Paragraph(esc(a['goal']), styles['Body']))

    # LED Preview + Materials side by side
    led = detect_led_pattern(a['codeJS'])
    needs_text = " | ".join(a['needs'])

    if led:
        led_grid = LEDGrid(led, 55)
        needs_para = Paragraph(f"<b>Materiel :</b> {esc(needs_text)}", styles['Body'])
        t = Table([[led_grid, needs_para]], colWidths=[65, W-5.6*cm-65])
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(0,0),0)]))
        elems.append(t)
    else:
        elems.append(Paragraph(f"<b>Materiel :</b> {esc(needs_text)}", styles['Body']))

    # Block chips
    chips = detect_block_chips(a['codeJS'])
    if chips:
        elems.append(Paragraph("BLOCS UTILISES", styles['SecHead']))
        # Render chips as a row (max 5 per row)
        rows = [chips[i:i+5] for i in range(0, len(chips), 5)]
        for row in rows:
            t = Table([row], colWidths=[ch.width+4 for ch in row])
            t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),1),('RIGHTPADDING',(0,0),(-1,-1),1)]))
            elems.append(t)

    # Steps
    if a['blocks']:
        elems.append(Paragraph("ETAPES", styles['SecHead']))
        for i, b in enumerate(a['blocks']):
            elems.append(Paragraph(f"<font color='#1E90FF'><b>{i+1}.</b></font> {esc(b)}", styles['Body']))

    # Tip
    elems.append(Paragraph(f"<b>Astuce :</b> {esc(a['tip'])}", styles['Tip']))

    # Code: JS + Python side by side
    elems.append(Paragraph("CODE", styles['SecHead']))
    js_lines = a['codeJS'].split('\n')[:15]
    py_lines = a['codePY'].split('\n')[:15]
    js_text = '\n'.join(l[:80] for l in js_lines)
    py_text = '\n'.join(l[:80] for l in py_lines)
    if len(a['codeJS'].split('\n')) > 15: js_text += "\n// ..."
    if len(a['codePY'].split('\n')) > 15: py_text += "\n# ..."

    code_table = Table([
        [Paragraph("<font color='#F7DF1E'><b>JS</b></font> JavaScript", styles['Meta']),
         Paragraph("<font color='#306998'><b>PY</b></font> Python", styles['Meta'])],
        [Paragraph(f"<font face='Courier' size='7'>{esc(js_text)}</font>", styles['CodeJS']),
         Paragraph(f"<font face='Courier' size='7'>{esc(py_text)}</font>", styles['CodePY'])]
    ], colWidths=[8.2*cm, 8.2*cm])
    code_table.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),3),
        ('RIGHTPADDING',(0,0),(-1,-1),3),
        ('TOPPADDING',(0,0),(-1,-1),2),
        ('BOTTOMPADDING',(0,0),(-1,-1),2),
    ]))
    elems.append(code_table)

    # Challenges
    if a['challenges']:
        elems.append(Paragraph("DEFIS", styles['SecHead']))
        for ch in a['challenges']:
            color = {1:"#40BF4A",2:"#F7DF1E",3:"#DC143C"}.get(ch['d'],"#888")
            stars_ch = "*" * ch['d']
            elems.append(Paragraph(f"<font color='{color}'><b>{stars_ch}</b></font> {esc(ch['t'])}", styles['ChalStyle']))

    # QR link
    qr_url = f"https://abourdim.github.io/bit-activities/?a={a['id']}"
    elems.append(Spacer(1, 3*mm))
    elems.append(Paragraph(f"<font color='#aaa' size='7'>Ouvrir : {qr_url}</font>", styles['Body']))

    story.extend(elems)
    story.append(PageBreak())

# Page numbers
def footer(c, doc):
    c.saveState()
    c.setFont('Helvetica', 7)
    c.setFillColor(HexColor("#999"))
    c.drawCentredString(W/2, 1.2*cm, f"Micro:bit 48 Activites - p.{c.getPageNumber()}")
    c.restoreState()

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"Ebook generated: {output_path} ({len(activities)} activities)")
