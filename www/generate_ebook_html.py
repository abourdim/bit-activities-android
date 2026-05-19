"""
Generate a beautiful standalone interactive HTML web-book from micro:bit 48 activities.
Dark elegant theme with sidebar navigation, glassmorphism cards, and scroll-spy.
"""
import re, html as html_mod, json, os

# ── Parse activities from index.html ──
with open("index.html", "r", encoding="utf-8") as f:
    raw_html = f.read()

js_match = re.search(r'<script>(.*?)</script>', raw_html, re.DOTALL)
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
        challenges.append({"t": cm2.group(1), "d": int(cm2.group(2))})
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

# ── LED Patterns ──
LED_ICONS = {
    "Heart":[0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,0,0,0,1,0,0],
    "SmallHeart":[0,0,0,0,0,0,1,0,1,0,0,1,1,1,0,0,0,1,0,0,0,0,0,0,0],
    "Happy":[0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,1,0,0,0,1,0,1,1,1,0],
    "Sad":[0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,1,1,1,0,1,0,0,0,1],
    "Flash":[0,0,1,0,0,0,1,1,0,0,1,1,1,1,1,0,0,1,1,0,0,0,1,0,0],
    "No":[1,0,0,0,1,0,1,0,1,0,0,0,1,0,0,0,1,0,1,0,1,0,0,0,1],
    "Yes":[0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1,0,1,0,0,0,1,0,0,0],
    "Asleep":[0,0,0,0,0,1,1,0,1,1,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0],
    "Skull":[0,1,1,1,0,1,0,1,0,1,1,1,1,1,1,0,1,1,1,0,0,1,1,1,0],
    "ArrowNorth":[0,0,1,0,0,0,1,1,1,0,1,0,1,0,1,0,0,1,0,0,0,0,1,0,0],
    "Meh":[0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1],
    "Target":[0,0,1,0,0,0,1,1,1,0,1,1,0,1,1,0,1,1,1,0,0,0,1,0,0],
    "Square":[1,1,1,1,1,1,0,0,0,1,1,0,0,0,1,1,0,0,0,1,1,1,1,1,1],
    "SmallSquare":[0,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0,1,1,1,0,0,0,0,0,0],
    "Scissors":[1,0,0,0,1,0,1,0,1,0,0,0,1,0,0,0,1,0,1,0,1,0,0,0,1],
    "Duck":[0,1,1,0,0,1,1,1,0,0,0,1,1,1,1,0,1,1,1,0,0,0,0,0,0],
}

def detect_led(code):
    m = re.search(r'showIcon\(IconNames\.(\w+)\)', code)
    if m and m.group(1) in LED_ICONS: return LED_ICONS[m.group(1)]
    m = re.search(r'showLeds\s*\(\s*`([^`]+)`', code)
    if m:
        p = [1 if c=='#' else 0 for c in m.group(1) if c in '#.']
        if len(p)==25: return p
    return None

def led_svg(pattern):
    """Generate an inline SVG for a 5x5 LED grid."""
    if not pattern:
        return ""
    cells = ""
    for i in range(25):
        x = 4 + (i % 5) * 18
        y = 4 + (i // 5) * 18
        if pattern[i]:
            cells += f'<circle cx="{x+8}" cy="{y+8}" r="7" fill="#ff1a1a" filter="url(#ledglow)"/>'
        else:
            cells += f'<circle cx="{x+8}" cy="{y+8}" r="7" fill="#1a1a2e" opacity="0.4"/>'
    return f'''<svg class="led-svg" width="96" height="96" viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg">
  <defs><filter id="ledglow"><feGaussianBlur stdDeviation="2" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
  <rect width="96" height="96" rx="8" fill="#050510"/>
  {cells}
</svg>'''

# ── Block detection ──
# pattern, label, color, MakeCode JS snippet (renders one block), description
BLOCK_MAP = [
    (r'basic\.showString',"afficher texte","#1E90FF",'basic.showString("Hello")',"Fait defiler un texte sur les 25 LEDs, lettre par lettre."),
    (r'basic\.showIcon',"montrer icone","#1E90FF",'basic.showIcon(IconNames.Heart)',"Affiche une icone predefinie (coeur, sourire, eclair...)."),
    (r'basic\.showNumber',"afficher nombre","#1E90FF",'basic.showNumber(42)',"Affiche un nombre sur les LEDs."),
    (r'basic\.showLeds',"montrer LEDs","#1E90FF",'basic.showLeds(`# . # . #\\n. # . # .\\n# . # . #\\n. # . # .\\n# . # . #`)',"Allume des LEDs specifiques avec un motif 5x5 personnalise."),
    (r'basic\.clearScreen',"effacer ecran","#1E90FF",'basic.clearScreen()',"Eteint toutes les 25 LEDs."),
    (r'basic\.pause',"pause","#1E90FF",'basic.pause(1000)',"Attend un nombre de millisecondes (1000 = 1 seconde)."),
    (r'basic\.forever',"repeter indefiniment","#00AA00",'basic.forever(function(){})',"Boucle infinie : le code se repete sans fin."),
    (r'input\.onButtonPressed',"quand bouton presse","#D400D4",'input.onButtonPressed(Button.A, function(){})',"Declenche du code quand on appuie sur A, B ou A+B."),
    (r'input\.onGesture',"quand secouer","#D400D4",'input.onGesture(Gesture.Shake, function(){})',"Declenche du code quand on secoue la carte."),
    (r'input\.onLogoEvent',"quand logo touche","#D400D4",'input.onLogoEvent(TouchButtonEvent.Pressed, function(){})',"Declenche du code quand on touche le logo dore (V2)."),
    (r'input\.temperature',"temperature","#D400D4",'basic.showNumber(input.temperature())',"Retourne la temperature mesuree par le processeur."),
    (r'input\.lightLevel',"niveau de lumiere","#D400D4",'basic.showNumber(input.lightLevel())',"Retourne le niveau de lumiere (0-255)."),
    (r'input\.soundLevel',"niveau sonore V2","#D400D4",'basic.showNumber(input.soundLevel())',"Retourne le niveau sonore ambiant (0-255, V2)."),
    (r'input\.compassHeading',"direction boussole","#D400D4",'basic.showNumber(input.compassHeading())',"Retourne l'angle de la boussole (0-359)."),
    (r'input\.acceleration',"acceleration","#D400D4",'basic.showNumber(input.acceleration(Dimension.Strength))',"Retourne la force d'acceleration (mouvement)."),
    (r'randint',"au hasard","#9400D3",'basic.showNumber(randint(1, 6))',"Genere un nombre aleatoire entre min et max."),
    (r'music\.playTone',"jouer tonalite","#E63022",'music.playTone(262, 500)',"Joue une note a une frequence et duree donnees."),
    (r'music\.startMelody',"jouer melodie","#E63022",'music.startMelody(music.builtInMelody(Melodies.Dadadadum), MelodyOptions.Once)',"Joue une melodie predefinie."),
    (r'radio\.setGroup',"radio groupe","#E3008C",'radio.setGroup(7)',"Definit le groupe radio (meme numero = communication)."),
    (r'radio\.sendNumber',"radio envoyer","#E3008C",'radio.sendNumber(1)',"Envoie un nombre par radio."),
    (r'radio\.onReceived',"radio recu","#E3008C",'radio.onReceivedNumber(function(n){})',"Declenche du code quand un nombre est recu."),
    (r'pins\.analogReadPin',"lire analogique","#3BDDD4",'basic.showNumber(pins.analogReadPin(AnalogPin.P0))',"Lit une valeur analogique (0-1023) sur une broche."),
    (r'pins\.digitalReadPin',"lire numerique","#3BDDD4",'basic.showNumber(pins.digitalReadPin(DigitalPin.P0))',"Lit 0 ou 1 sur une broche."),
    (r'pins\.digitalWritePin',"ecriture numerique","#3BDDD4",'pins.digitalWritePin(DigitalPin.P0, 1)',"Ecrit 0 ou 1 sur une broche."),
    (r'pins\.analogWritePin',"ecriture analogique","#3BDDD4",'pins.analogWritePin(AnalogPin.P0, 512)',"Ecrit une valeur (0-1023) sur une broche."),
    (r'pins\.servoWritePin',"servo","#3BDDD4",'pins.servoWritePin(AnalogPin.P0, 90)',"Positionne un servomoteur (0-180 degres)."),
    (r'led\.plot',"allumer LED","#7600A8",'led.plot(2, 2)',"Allume une LED a la position (x, y)."),
    (r'led\.plotBarGraph',"graphique barres","#7600A8",'led.plotBarGraph(128, 255)',"Affiche une valeur en barres sur les LEDs."),
    (r'game\.createSprite',"creer sprite","#7600A8",'let s = game.createSprite(2, 2)',"Cree un point lumineux deplacable."),
    (r'neopixel',"NeoPixel","#7B2D8E",'let strip = neopixel.create(DigitalPin.P0, 8, NeoPixelMode.RGB)',"Controle des LEDs RGB (NeoPixel)."),
    (r'bluetooth',"Bluetooth","#0082FB",'bluetooth.startUartService()',"Services de communication Bluetooth."),
    (r'sonar\.ping',"sonar distance","#00A4A6",'basic.showNumber(sonar.ping(DigitalPin.P1, DigitalPin.P2, PingUnit.Centimeters))',"Mesure la distance avec un capteur ultrason."),
]

def detect_blocks(code):
    """Returns list of (label, color, snippet, description) for blocks found in code"""
    seen = set()
    result = []
    for pat, label, color, snippet, desc in BLOCK_MAP:
        if re.search(pat, code) and label not in seen:
            seen.add(label)
            result.append((label, color, snippet, desc))
    return result

def esc(t):
    return html_mod.escape(t)

# ── Extract BT (block trees) from index.html ──
bt_match = re.search(r'const BT = \{(.+?)\};\s*\n', js, re.DOTALL)
bt_raw = bt_match.group(1) if bt_match else ""

# Simple BT parser — extract structure for each activity
import json

def parse_bt_for_activity(aid):
    """Extract block tree for an activity from BT raw JS"""
    # Find the entry: N:[{...}]
    pattern = rf'(?:^|\n){aid}:\[(.*?)(?=\n\d+:\[|\Z)'
    m = re.search(pattern, bt_raw, re.DOTALL)
    if not m: return None
    return m.group(1)

def render_block_html(bt_text):
    """Convert BT JS notation to visual HTML blocks (simplified)"""
    if not bt_text: return ""
    # Extract top-level blocks by finding hat/cblock/stack patterns
    blocks = []

    # Find hat blocks: {cat:"X",type:"hat",label:"Y",children:[...]}
    for m in re.finditer(r'\{cat:"(\w+)",type:"hat",label:"([^"]+)"', bt_text):
        cat, label = m.group(1), m.group(2)
        blocks.append(("hat", cat, label))

    # Find cblock: {cat:"X",type:"cblock",label:"Y"
    for m in re.finditer(r'\{cat:"(\w+)",type:"cblock",label:"([^"]+)"', bt_text):
        cat, label = m.group(1), m.group(2)
        blocks.append(("cblock", cat, label))

    # Find stack blocks: {cat:"X",type:"stack",label:"Y"
    for m in re.finditer(r'\{cat:"(\w+)",type:"stack",label:"([^"]+)"', bt_text):
        cat, label = m.group(1), m.group(2)
        blocks.append(("stack", cat, label))

    # Find args: ,arg:"Y" or ,arg:{...label:"Y"
    args = {}
    for m in re.finditer(r'label:"([^"]+)"[^}]*?,arg:"([^"]+)"', bt_text):
        args[m.group(1)] = m.group(2)
    for m in re.finditer(r'label:"([^"]+)"[^}]*?,arg:\{[^}]*?label:"([^"]+)"', bt_text):
        args[m.group(1)] = m.group(2)

    if not blocks: return ""

    html = '<div class="vblock-canvas">'
    seen = set()
    for btype, cat, label in blocks:
        key = f"{btype}-{label}"
        if key in seen: continue
        seen.add(key)
        arg_html = ""
        if label in args:
            is_str = not args[label].replace(" ","").replace("–","").replace(".","").isdigit()
            arg_cls = "varg str" if is_str and len(args[label]) > 2 else "varg"
            arg_html = f' <span class="{arg_cls}">{esc(args[label])}</span>'

        if btype == "hat":
            html += f'<div class="vb hat cat-{cat}"><div class="hat-label">{esc(label)}{arg_html}</div></div>'
        elif btype == "cblock":
            html += f'<div class="vb cblock cat-{cat}"><div class="cb-row">{esc(label)}{arg_html}</div><div class="cb-body"></div><div class="cb-cap"></div></div>'
        else:
            html += f'<div class="vb cat-{cat}">{esc(label)}{arg_html}</div>'
    html += '</div>'
    return html

def generate_flowchart(code):
    """Generate HTML flowchart from JS code"""
    nodes = []
    arrow = '<div class="fc-arrow"></div>'
    node = lambda cls, txt: f'<div class="fc-node {cls}">{esc(txt)}</div>'

    nodes.append(node("start", "DEBUT"))
    nodes.append(arrow)

    if "onButtonPressed(Button.A" in code: nodes += [node("io", "Bouton A presse"), arrow]
    if "onButtonPressed(Button.B" in code: nodes += [node("io", "Bouton B presse"), arrow]
    if "onGesture(Gesture.Shake" in code: nodes += [node("io", "Secouer"), arrow]
    if "onLogoEvent" in code: nodes += [node("io", "Logo touche"), arrow]
    if "forever" in code: nodes += [node("loop", "Repeter indefiniment"), arrow]

    if "showString" in code: nodes += [node("process", "Afficher texte"), arrow]
    elif "showIcon" in code: nodes += [node("process", "Montrer icone"), arrow]
    elif "showNumber" in code: nodes += [node("process", "Afficher nombre"), arrow]

    if "if" in code:
        cond = re.search(r'if\s*\(([^)]{1,35})\)', code)
        cond_text = cond.group(1) if cond else "condition"
        nodes += [node("decision", f"SI {cond_text} ?"), arrow]

    if "music." in code: nodes += [node("process", "Jouer son"), arrow]
    if "radio.send" in code: nodes += [node("process", "Envoyer radio"), arrow]
    if "pause(" in code: nodes += [node("process", "Pause"), arrow]

    nodes.append(node("end", "FIN"))
    return '<div class="flowchart">' + ''.join(nodes) + '</div>'

def generate_pseudocode(code):
    """Generate colored pseudocode from JS code"""
    pk = lambda t: f'<span class="pk">{t}</span>'
    pv = lambda t: f'<span class="pv">{t}</span>'
    pc = lambda t: f'<span class="pc">{t}</span>'

    lines = [pk("DEBUT")]

    # Variables
    for m in re.finditer(r'let\s+(\w+)\s*=\s*([^;\n]+)', code):
        lines.append(f"  {pk('DEFINIR')} {m.group(1)} ← {pv(m.group(2).strip())}")

    if "forever" in code: lines.append(f"\n{pk('REPETER INDEFINIMENT')} :")
    if "onButtonPressed(Button.A" in code: lines.append(f"{pk('QUAND')} bouton A :")
    if "onButtonPressed(Button.B" in code: lines.append(f"{pk('QUAND')} bouton B :")
    if "onGesture(Gesture.Shake" in code: lines.append(f"{pk('QUAND')} secouer :")

    m = re.search(r'showString\("([^"]+)"\)', code)
    if m: lines.append(f"  {pk('AFFICHER')} {pv(m.group(1))}")
    m = re.search(r'showIcon\(IconNames\.(\w+)\)', code)
    if m: lines.append(f"  {pk('MONTRER')} icone {pv(m.group(1))}")
    m = re.search(r'showNumber\((\w+)\)', code)
    if m: lines.append(f"  {pk('AFFICHER')} {pv(m.group(1))}")

    m = re.search(r'if\s*\(([^)]{1,50})\)', code)
    if m:
        lines.append(f"  {pk('SI')} {pv(m.group(1).strip())} {pk('ALORS')}")
        lines.append(f"    {pc('// actions...')}")
        if "} else" in code:
            lines.append(f"  {pk('SINON')}")
            lines.append(f"    {pc('// actions...')}")

    if "pause(" in code: lines.append(f"  {pk('ATTENDRE')} {pv('ms')}")
    if "music." in code: lines.append(f"  {pk('JOUER')} son")
    if "radio.send" in code: lines.append(f"  {pk('ENVOYER')} radio")

    lines.append(f"\n{pk('FIN')}")
    return '<div class="pseudo-box">' + '\n'.join(lines) + '</div>'

def diff_label(d):
    return {1:"Debutant",2:"Intermediaire",3:"Avance"}.get(d,"")

def diff_color(d):
    return {1:"#40BF4A",2:"#F7DF1E",3:"#DC143C"}.get(d,"#888")

def diff_stars(d):
    return "&#9733;" * d + "&#9734;" * (3 - d)

# ── Syntax highlighting ──
def hl_js(code):
    code = esc(code)
    code = re.sub(r'(\/\/[^\n]*)', r'<span class="hl-cmt">\1</span>', code)
    code = re.sub(r'(&quot;[^&]*?&quot;|&#x27;[^&]*?&#x27;)', r'<span class="hl-str">\1</span>', code)
    code = re.sub(r'\b(function|let|var|const|if|else|while|for|return|true|false|new|of|in)\b', r'<span class="hl-kw">\1</span>', code)
    code = re.sub(r'(?<!\w)(\d+)(?!\w)', r'<span class="hl-num">\1</span>', code)
    return code

def hl_py(code):
    e = esc(code)
    tokens = []
    r = e
    while r:
        m = re.match(r'(#[^\n]*)', r)
        if m: tokens.append(f'<span class="hl-cmt">{m.group(1)}</span>'); r=r[len(m.group(0)):]; continue
        m = re.match(r'(&quot;[^&]*?&quot;)', r)
        if m: tokens.append(f'<span class="hl-str">{m.group(1)}</span>'); r=r[len(m.group(0)):]; continue
        m = re.match(r"(&#x27;[^&]*?&#x27;)", r)
        if m: tokens.append(f'<span class="hl-str">{m.group(1)}</span>'); r=r[len(m.group(0)):]; continue
        m = re.match(r'\b(def|if|elif|else|while|for|in|return|import|from|global|not|and|or|True|False|None|range|len|min|max|abs)\b', r)
        if m: tokens.append(f'<span class="hl-kw">{m.group(1)}</span>'); r=r[len(m.group(0)):]; continue
        m = re.match(r'(\d+)', r)
        if m: tokens.append(f'<span class="hl-num">{m.group(1)}</span>'); r=r[len(m.group(0)):]; continue
        tokens.append(r[0]); r=r[1:]
    return ''.join(tokens)


# ── Build sidebar nav items ──
activities = [a for a in activities if a["id"] <= 48]

# Load pre-rendered blocks if available
prerendered_blocks = {}
if os.path.exists("blocks.json"):
    with open("blocks.json", "r", encoding="utf-8") as bf:
        prerendered_blocks = json.load(bf)
    print(f"Loaded {len(prerendered_blocks)} pre-rendered blocks from blocks.json")
else:
    print("No blocks.json found — will use MakeCode iframe (slow)")
simple_acts = [a for a in activities if a["part"] == "simple"]
advanced_acts = [a for a in activities if a["part"] != "simple"]

def sidebar_links(act_list):
    links = []
    for a in act_list:
        links.append(f'<a class="nav-link" href="#act-{a["id"]}" data-id="{a["id"]}">{a["id"]}. {esc(a["title"])}</a>')
    return "\n".join(links)


# ── Generate HTML ──
out = []

# --- HEAD ---
out.append('''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Micro:bit - 48 Activites - Web Book</title>
<style>
/* ===== RESET & BASE ===== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; scroll-padding-top: 20px; }
body {
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  background: #0a0f1e;
  color: #d0ddf0;
  line-height: 1.65;
  font-size: 15px;
  overflow-x: hidden;
}
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #0a0f1e; }
::-webkit-scrollbar-thumb { background: #1e2a4a; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #3b82f6; }

/* ===== SIDEBAR ===== */
.sidebar {
  position: fixed; top: 0; left: 0; bottom: 0;
  width: 260px;
  background: rgba(8, 12, 28, 0.95);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-right: 1px solid rgba(59, 130, 246, 0.15);
  z-index: 100;
  display: flex; flex-direction: column;
  transition: transform 0.3s ease;
  overflow: hidden;
}
.sidebar-header {
  padding: 24px 20px 16px;
  border-bottom: 1px solid rgba(59, 130, 246, 0.1);
  flex-shrink: 0;
}
.sidebar-header h1 {
  font-size: 18px; font-weight: 700;
  background: linear-gradient(135deg, #3b82f6, #60a5fa, #93c5fd);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.3px;
}
.sidebar-header .sub {
  font-size: 11px; color: #5a6a8a; margin-top: 2px; letter-spacing: 0.5px; text-transform: uppercase;
}
.sidebar-nav {
  flex: 1; overflow-y: auto; padding: 8px 0;
  scrollbar-width: thin; scrollbar-color: #1e2a4a transparent;
}
.sidebar-nav::-webkit-scrollbar { width: 4px; }
.sidebar-nav::-webkit-scrollbar-thumb { background: #1e2a4a; border-radius: 2px; }
.nav-section {
  cursor: pointer; user-select: none;
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 20px; font-size: 12px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.8px;
  color: #7a8aaa;
  transition: color 0.2s;
}
.nav-section:hover { color: #d0ddf0; }
.nav-section .arrow {
  display: inline-block; transition: transform 0.25s; font-size: 10px;
}
.nav-section.open .arrow { transform: rotate(90deg); }
.nav-group { overflow: hidden; max-height: 0; transition: max-height 0.4s ease; }
.nav-group.open { max-height: 3000px; }
.nav-link {
  display: block;
  padding: 5px 20px 5px 28px;
  font-size: 13px; color: #6a7a9a;
  text-decoration: none;
  border-left: 2px solid transparent;
  transition: all 0.2s;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.nav-link:hover { color: #d0ddf0; background: rgba(59, 130, 246, 0.05); }
.nav-link.active {
  color: #3b82f6; border-left-color: #3b82f6;
  background: rgba(59, 130, 246, 0.08);
  font-weight: 600;
}
.nav-cover-link {
  display: block; padding: 8px 20px; font-size: 13px; color: #6a7a9a;
  text-decoration: none; transition: color 0.2s;
}
.nav-cover-link:hover { color: #d0ddf0; }
.sidebar-footer {
  padding: 12px 20px;
  border-top: 1px solid rgba(59, 130, 246, 0.1);
  font-size: 11px; color: #3a4a6a; flex-shrink: 0;
}

/* Mobile toggle */
.mobile-toggle {
  display: none; position: fixed; top: 12px; left: 12px; z-index: 200;
  width: 42px; height: 42px; border-radius: 10px; border: none;
  background: rgba(59, 130, 246, 0.2); backdrop-filter: blur(8px);
  color: #3b82f6; font-size: 20px; cursor: pointer;
  align-items: center; justify-content: center;
  transition: background 0.2s;
}
.mobile-toggle:hover { background: rgba(59, 130, 246, 0.35); }
.mobile-overlay {
  display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  z-index: 90; opacity: 0; transition: opacity 0.3s;
}
.mobile-overlay.show { display: block; opacity: 1; }

/* ===== MAIN CONTENT ===== */
.main {
  margin-left: 260px;
  min-height: 100vh;
}

/* ===== COVER ===== */
.cover {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 100vh; text-align: center; padding: 60px 24px;
  position: relative; overflow: hidden;
}
.cover::before {
  content: ""; position: absolute; inset: 0;
  background:
    radial-gradient(ellipse 600px 400px at 30% 40%, rgba(59,130,246,0.08), transparent),
    radial-gradient(ellipse 500px 350px at 70% 60%, rgba(147,51,234,0.06), transparent);
  pointer-events: none;
}
.cover-board { position: relative; z-index: 1; margin-bottom: 40px; }
.cover h1 {
  position: relative; z-index: 1;
  font-size: 56px; font-weight: 800; letter-spacing: -1.5px;
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 30%, #a78bfa 60%, #3b82f6 100%);
  background-size: 200% auto;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradientShift 4s ease infinite;
  margin-bottom: 8px;
}
@keyframes gradientShift {
  0%, 100% { background-position: 0% center; }
  50% { background-position: 200% center; }
}
.cover h2 {
  position: relative; z-index: 1;
  font-size: 22px; font-weight: 400; color: #7a8aaa;
  margin-bottom: 8px;
}
.cover .cover-sub {
  position: relative; z-index: 1;
  font-size: 14px; color: #4a5a7a; margin-bottom: 8px;
}
.cover .cover-author {
  position: relative; z-index: 1;
  font-size: 13px; color: #3a4a6a; margin-top: 32px;
  letter-spacing: 1px; text-transform: uppercase;
}
.cover .scroll-hint {
  position: relative; z-index: 1;
  margin-top: 48px; font-size: 12px; color: #3a4a6a;
  animation: bounce 2s infinite;
}
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(6px); }
}

/* ===== ACTIVITY SECTION ===== */
.act-section {
  padding: 48px 40px 32px;
  border-bottom: 1px solid rgba(59, 130, 246, 0.06);
  max-width: 960px; margin: 0 auto;
}

/* Header bar */
.act-header-bar {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 20px; border-radius: 12px;
  margin-bottom: 24px; position: relative; overflow: hidden;
}
.act-header-bar::before {
  content: ""; position: absolute; inset: 0;
  background: linear-gradient(135deg, var(--hdr-color) 0%, transparent 100%);
  opacity: 0.12;
}
.act-header-bar::after {
  content: ""; position: absolute; inset: 0;
  border: 1px solid var(--hdr-color); opacity: 0.2; border-radius: 12px;
}
.act-num-badge {
  position: relative; z-index: 1;
  width: 40px; height: 40px; border-radius: 10px;
  background: var(--hdr-color); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 800; flex-shrink: 0;
}
.act-title-area { position: relative; z-index: 1; flex: 1; min-width: 0; }
.act-title-text {
  font-size: 20px; font-weight: 700; color: #e8edf5;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.act-header-tags {
  display: flex; gap: 6px; margin-top: 4px; flex-wrap: wrap;
}
.tag-chip {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 2px 8px; border-radius: 6px;
  font-size: 11px; font-weight: 600;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
}
.tag-chip.diff { color: var(--dc); border-color: rgba(255,255,255,0.08); }
.tag-chip.time { color: #7a8aaa; }
.tag-chip.v2 { color: #40BF4A; }
.tag-chip.ia { color: #eab308; }
.tag-stars { font-size: 12px; letter-spacing: 1px; }

/* Glass card */
.glass-card {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px; padding: 16px 20px; margin-bottom: 20px;
}

/* Section label */
.sec-label {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.2px; color: #3b82f6; margin-bottom: 8px;
  display: flex; align-items: center; gap: 8px;
}
.sec-label::after {
  content: ""; flex: 1; height: 1px;
  background: linear-gradient(to right, rgba(59,130,246,0.2), transparent);
}

/* Goal */
.goal-text { font-size: 15px; line-height: 1.7; color: #b0c0e0; }

/* LED SVG */
.led-svg { display: block; }

/* Content row */
.content-row {
  display: flex; gap: 20px; align-items: flex-start; margin-bottom: 20px;
}
.content-row .led-col { flex-shrink: 0; }
.content-row .info-col { flex: 1; min-width: 0; }

/* Block chips */
.blocks-wrap { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px; }
.block-chip {
  display: inline-block; padding: 4px 12px; border-radius: 6px;
  color: #fff; font-size: 12px; font-weight: 600;
  border-bottom: 2px solid rgba(0,0,0,0.25);
  letter-spacing: 0.2px;
}

/* MakeCode Rendered Blocks */
.mc-blocks { min-height: 60px; padding: 12px; background: rgba(0,0,0,0.1); border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 16px; text-align: center; }
.mc-blocks img { width: 40%; width: auto; height: auto; border-radius: 4px; object-fit: contain; }
.mc-loading { font-size: 12px; color: #5e7499; padding: 20px; }
.mc-loading::after { content: ""; display: inline-block; width: 12px; height: 12px; border: 2px solid #3b82f6; border-top-color: transparent; border-radius: 50%; animation: spin 0.6s linear infinite; margin-left: 8px; vertical-align: middle; }
@keyframes spin { to { transform: rotate(360deg); } }

/* CSS Fallback Blocks (hidden when MakeCode loads) */
.vblock-canvas { display: flex; flex-direction: column; gap: 3px; padding: 12px; background: rgba(0,0,0,0.15); border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 16px; }
.vb { position: relative; border-radius: 4px; padding: 6px 10px; font-size: 12px; font-weight: 600; color: #fff; display: flex; flex-wrap: wrap; align-items: center; gap: 5px; line-height: 1.5; border-bottom: 2px solid rgba(0,0,0,0.25); font-family: system-ui, sans-serif; }
.vb.hat { border-radius: 14px 14px 4px 4px; padding: 7px 12px 4px; flex-direction: column; align-items: stretch; }
.vb .hat-label { display: flex; align-items: center; gap: 5px; min-height: 28px; }
.vb .hat-body { display: flex; flex-direction: column; gap: 2px; padding-bottom: 3px; }
.vb.cblock { padding: 6px 10px 0; flex-direction: column; align-items: stretch; border-bottom: none; }
.vb .cb-row { display: flex; flex-wrap: wrap; align-items: center; gap: 5px; }
.vb .cb-body { margin: 3px 0; padding: 5px 4px 5px 14px; background: rgba(0,0,0,0.15); border-left: 3px solid rgba(255,255,255,0.15); min-height: 28px; display: flex; flex-direction: column; gap: 2px; border-radius: 0 3px 3px 0; }
.vb .cb-cap { height: 6px; border-radius: 0 0 4px 4px; background: inherit; filter: brightness(0.9); margin: 0 -10px; }
.vb .cb-else { padding: 3px 8px; color: rgba(255,255,255,0.85); font-weight: 700; background: rgba(0,0,0,0.08); font-size: 11px; }
.vb .varg { display: inline-flex; padding: 1px 8px; border-radius: 10px; background: rgba(255,255,255,0.92); color: #333; font-size: 11px; font-weight: 600; }
.vb .varg.str { background: #a31515; color: #fff; border-radius: 10px; }
.vb.cat-basic { background: #1E90FF; } .vb.cat-input { background: #D400D4; }
.vb.cat-loops { background: #00AA00; } .vb.cat-logic { background: #00A4A6; }
.vb.cat-music { background: #E63022; } .vb.cat-radio { background: #E3008C; }
.vb.cat-variables { background: #DC143C; } .vb.cat-pins { background: #3BDDD4; color: #111; }
.vb.cat-math { background: #9400D3; } .vb.cat-game { background: #7600A8; }
.vb.cat-functions { background: #3455DB; } .vb.cat-bluetooth { background: #0082FB; }
.vb.cat-sonar { background: #00A4A6; } .vb.cat-neopixel { background: #7B2D8E; }

/* Block reference cards */
.blocks-ref-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; }
.block-ref-item { display: flex; gap: 12px; align-items: center; padding: 10px 14px; border-radius: 10px; background: rgba(0,0,0,0.12); border: 1px solid rgba(255,255,255,0.05); }
.block-ref-render { flex-shrink: 0; width: 150px; }
.block-ref-render img { width: 100%; width: auto; height: auto; object-fit: contain; }
.block-ref-info { flex: 1; }
.block-ref-name { font-size: 13px; font-weight: 700; margin-bottom: 2px; }
.block-ref-desc { font-size: 11px; color: #8899aa; line-height: 1.4; }

/* Flowchart */
.flowchart { display: flex; flex-direction: column; align-items: center; gap: 0; padding: 14px; background: rgba(0,0,0,0.1); border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 16px; }
.fc-node { padding: 5px 16px; font-size: 11px; font-weight: 600; color: #fff; text-align: center; max-width: 240px; }
.fc-node.start { background: #40BF4A; border-radius: 20px; }
.fc-node.end { background: #DC143C; border-radius: 20px; }
.fc-node.process { background: #1E90FF; border-radius: 5px; }
.fc-node.decision { background: #9400D3; border-radius: 4px; border: 1.5px solid rgba(255,255,255,0.2); padding: 4px 12px; }
.fc-node.io { background: #D400D4; border-radius: 5px 16px 5px 16px; }
.fc-node.loop { background: #00AA00; border-radius: 5px; border-left: 3px solid rgba(255,255,255,0.3); }
.fc-arrow { width: 2px; height: 12px; background: #3b82f6; position: relative; }
.fc-arrow::after { content: "\\25BC"; position: absolute; bottom: -6px; left: 50%; transform: translateX(-50%); font-size: 7px; color: #3b82f6; }

/* Pseudocode */
.pseudo-box { font-family: 'SF Mono', 'Fira Code', Consolas, monospace; font-size: 11px; line-height: 1.6; padding: 12px 14px; background: rgba(0,0,0,0.15); border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); white-space: pre; overflow-x: auto; margin-bottom: 16px; color: #d0ddf0; }
.pk { color: #569CD6; font-weight: 700; }
.pv { color: #CE9178; }
.pc { color: #6A9955; font-style: italic; }

/* Steps */
.steps-list { list-style: none; margin-bottom: 20px; }
.step-item {
  display: flex; gap: 12px; align-items: flex-start;
  padding: 6px 0;
}
.step-num {
  width: 24px; height: 24px; border-radius: 50%;
  background: rgba(59, 130, 246, 0.15); color: #3b82f6;
  font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 1px;
  border: 1px solid rgba(59, 130, 246, 0.25);
}
.step-text { font-size: 14px; color: #a0b0d0; line-height: 1.6; }

/* Tip */
.tip-box {
  padding: 14px 18px; border-radius: 10px;
  background: rgba(234, 179, 8, 0.06);
  border: 1px solid rgba(234, 179, 8, 0.2);
  color: #eab308; font-size: 13px; line-height: 1.6;
  margin-bottom: 20px;
}
.tip-box .tip-icon { margin-right: 6px; }

/* Code area — stacked vertically for full width */
.code-grid {
  display: flex; flex-direction: column; gap: 12px;
  margin-bottom: 20px;
}
.code-panel { border-radius: 10px; overflow: hidden; position: relative; }
.copy-btn { position: absolute; top: 8px; right: 8px; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.15); color: #aaa; cursor: pointer; z-index: 2; transition: all 0.2s; }
.copy-btn:hover { background: rgba(255,255,255,0.2); color: #fff; }
.code-panel-header {
  padding: 8px 14px; display: flex; align-items: center; gap: 8px;
  font-size: 12px; font-weight: 700;
}
.code-panel-header.js-header { background: rgba(247, 223, 30, 0.12); color: #f7df1e; }
.code-panel-header.py-header { background: rgba(48, 105, 152, 0.2); color: #60a5fa; }
.code-lang-dot {
  width: 8px; height: 8px; border-radius: 50%;
}
.code-lang-dot.js-dot { background: #f7df1e; }
.code-lang-dot.py-dot { background: #306998; }
.code-block {
  padding: 14px 16px;
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
  font-size: 12.5px; line-height: 1.65;
  overflow-x: auto; white-space: pre;
}
.code-block.js-code { background: rgba(247, 223, 30, 0.04); border: 1px solid rgba(247, 223, 30, 0.08); border-top: none; border-radius: 0 0 10px 10px; }
.code-block.py-code { background: rgba(48, 105, 152, 0.06); border: 1px solid rgba(48, 105, 152, 0.12); border-top: none; border-radius: 0 0 10px 10px; }

/* Syntax tokens */
.hl-kw { color: #c084fc; font-weight: 600; }
.hl-str { color: #34d399; }
.hl-cmt { color: #4a6a5a; font-style: italic; }
.hl-num { color: #f59e0b; }

/* Challenges */
.chal-list { margin-bottom: 20px; }
.chal-item {
  display: flex; gap: 10px; align-items: flex-start;
  padding: 5px 0; font-size: 13px; color: #a0b0d0;
}
.chal-dot {
  width: 10px; height: 10px; border-radius: 50%;
  flex-shrink: 0; margin-top: 5px;
}

/* Materials */
.needs-wrap { display: flex; flex-wrap: wrap; gap: 6px; }
.need-pill {
  padding: 4px 12px; border-radius: 20px;
  font-size: 12px; font-weight: 500;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #8a9aba;
}

/* Activity footer */
.act-footer {
  margin-top: 20px; padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  font-size: 11px; color: #2a3a5a;
  display: flex; justify-content: space-between;
}

/* ===== RESPONSIVE ===== */
@media (max-width: 860px) {
  .sidebar { transform: translateX(-100%); }
  .sidebar.open { transform: translateX(0); }
  .mobile-toggle { display: flex; }
  .main { margin-left: 0; }
  .act-section { padding: 32px 20px 24px; }
  .code-grid { grid-template-columns: 1fr; }
  .cover h1 { font-size: 36px; }
  .content-row { flex-direction: column; }
}

/* ===== PRINT ===== */
@media print {
  @page { size: A4; margin: 1.5cm 1.8cm; }
  body { background: #fff; color: #1a1a2e; font-size: 10pt; }
  .sidebar, .mobile-toggle, .mobile-overlay, .scroll-hint { display: none !important; }
  .main { margin-left: 0; }
  .cover { min-height: auto; padding: 2cm 0; }
  .cover::before { display: none; }
  .cover h1 { -webkit-text-fill-color: #1E90FF; color: #1E90FF; font-size: 3em; background: none; animation: none; }
  .cover h2 { color: #444; }
  .cover .cover-sub, .cover .cover-author { color: #888; }
  .act-section { padding: 0.5cm 0; page-break-inside: avoid; border-bottom: 1px solid #eee; max-width: 100%; }
  .act-header-bar { background: none !important; }
  .act-header-bar::before, .act-header-bar::after { display: none; }
  .act-num-badge { background: #1E90FF !important; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  .act-title-text { color: #1a1a2e; }
  .glass-card { background: #f9f9f9; border: 1px solid #ddd; backdrop-filter: none; }
  .goal-text { color: #333; }
  .step-text { color: #333; }
  .tip-box { background: #fffde7; border: 1px dashed #daa520; color: #8b6914; }
  .code-block { border: 1px solid #ddd !important; }
  .code-block.js-code { background: #fffde7 !important; }
  .code-block.py-code { background: #e8f0fe !important; }
  .hl-kw { color: #0000ff; }
  .hl-str { color: #a31515; }
  .hl-cmt { color: #008000; }
  .hl-num { color: #098658; }
  .tag-chip { border: 1px solid #ccc; }
  .tag-chip.diff { color: var(--dc); }
  .block-chip { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  .chal-dot { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  .need-pill { background: #f5f5f5; border: 1px solid #ddd; color: #555; }
  .act-footer { color: #bbb; border-top-color: #eee; }
  .nav-link, .blocks-wrap, .content-row .led-col svg { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  .sec-label { color: #1E90FF; }
  .sec-label::after { background: #eee; }
  .step-num { background: #e8f0fe; color: #1E90FF; border-color: #c0d0f0; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
}
</style>
</head>
<body>
<script>var mcQueue = [];</script>
''')

# --- SIDEBAR ---
out.append('''
<button class="mobile-toggle" id="mobileToggle" aria-label="Toggle sidebar">&#9776;</button>
<div class="mobile-overlay" id="mobileOverlay"></div>

<aside class="sidebar" id="sidebar">
  <div class="sidebar-header">
    <h1>Micro:bit</h1>
    <div class="sub">48 Activites Pratiques</div>
  </div>
  <nav class="sidebar-nav">
    <a class="nav-cover-link" href="#cover">Couverture</a>
    <div class="nav-section open" data-target="simple-group">
      Simple (1-22) <span class="arrow">&#9654;</span>
    </div>
    <div class="nav-group open" id="simple-group">
''')
out.append(sidebar_links(simple_acts))
out.append('''
    </div>
    <div class="nav-section open" data-target="advanced-group">
      Avance (23-48) <span class="arrow">&#9654;</span>
    </div>
    <div class="nav-group open" id="advanced-group">
''')
out.append(sidebar_links(advanced_acts))
out.append('''
    </div>
  </nav>
  <div class="sidebar-footer">
    Workshop DIY &mdash; abourdim
  </div>
</aside>
''')

# --- MAIN ---
out.append('<div class="main">')

# --- COVER ---
out.append('''
<section class="cover" id="cover">
  <div class="cover-board">
    <svg width="220" height="176" viewBox="0 0 220 176" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <filter id="coverglow"><feGaussianBlur stdDeviation="3" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
        <linearGradient id="boardgrd" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#2a2a3a"/>
          <stop offset="100%" style="stop-color:#1a1a2a"/>
        </linearGradient>
      </defs>
      <rect x="10" y="10" width="200" height="130" rx="16" fill="url(#boardgrd)" stroke="#3b82f6" stroke-opacity="0.2" stroke-width="1"/>
      <rect x="65" y="32" width="90" height="68" rx="6" fill="#050510"/>
''')
heart = [0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,0,0,0,1,0,0]
for i in range(25):
    x = 72 + (i % 5) * 16
    y = 39 + (i // 5) * 12
    if heart[i]:
        out.append(f'      <circle cx="{x}" cy="{y}" r="5" fill="#ff1a1a" filter="url(#coverglow)"/>')
    else:
        out.append(f'      <circle cx="{x}" cy="{y}" r="5" fill="#1a1a2e" opacity="0.3"/>')

out.append('''
      <circle cx="38" cy="70" r="12" fill="#222" stroke="#444" stroke-width="1"/>
      <text x="38" y="74" text-anchor="middle" fill="#888" font-size="11" font-weight="bold" font-family="system-ui">A</text>
      <circle cx="182" cy="70" r="12" fill="#222" stroke="#444" stroke-width="1"/>
      <text x="182" y="74" text-anchor="middle" fill="#888" font-size="11" font-weight="bold" font-family="system-ui">B</text>
      <circle cx="30" cy="155" r="9" fill="#333" stroke="#555" stroke-width="0.5"/>
      <text x="30" y="158" text-anchor="middle" fill="#888" font-size="7" font-family="system-ui">0</text>
      <circle cx="65" cy="155" r="9" fill="#333" stroke="#555" stroke-width="0.5"/>
      <text x="65" y="158" text-anchor="middle" fill="#888" font-size="7" font-family="system-ui">1</text>
      <circle cx="100" cy="155" r="9" fill="#333" stroke="#555" stroke-width="0.5"/>
      <text x="100" y="158" text-anchor="middle" fill="#888" font-size="7" font-family="system-ui">2</text>
      <circle cx="155" cy="155" r="9" fill="#333" stroke="#555" stroke-width="0.5"/>
      <text x="155" y="158" text-anchor="middle" fill="#888" font-size="6" font-family="system-ui">3V</text>
      <circle cx="190" cy="155" r="9" fill="#333" stroke="#555" stroke-width="0.5"/>
      <text x="190" y="158" text-anchor="middle" fill="#888" font-size="5.5" font-family="system-ui">GND</text>
    </svg>
  </div>
  <h1>Micro:bit</h1>
  <h2>48 Activites Pratiques</h2>
  <div class="cover-sub">Blocs &middot; JavaScript &middot; Python</div>
  <div class="cover-sub">Du clignotement LED aux robots IA</div>
  <div class="cover-author">Workshop DIY &mdash; abourdim</div>
  <div class="scroll-hint">&#8595; Faites defiler pour commencer</div>
</section>
''')

# --- ACTIVITY SECTIONS ---
for a in activities:
    dc = diff_color(a["difficulty"])
    hdr_color = dc
    aid = a["id"]

    out.append(f'<section class="act-section" id="act-{aid}">')

    # Header bar
    out.append(f'<div class="act-header-bar" style="--hdr-color:{hdr_color}">')
    out.append(f'  <div class="act-num-badge" style="background:{hdr_color}">{aid}</div>')
    out.append(f'  <div class="act-title-area">')
    out.append(f'    <div class="act-title-text">{esc(a["title"])}</div>')
    out.append(f'    <div class="act-header-tags">')
    out.append(f'      <span class="tag-chip diff" style="--dc:{dc}"><span class="tag-stars">{diff_stars(a["difficulty"])}</span> {diff_label(a["difficulty"])}</span>')
    out.append(f'      <span class="tag-chip time">{esc(a["time"])}</span>')
    if a["v2"]:
        out.append('      <span class="tag-chip v2">V2</span>')
    if a["ia"]:
        out.append('      <span class="tag-chip ia">IA</span>')
    out.append(f'    </div>')
    out.append(f'  </div>')
    out.append(f'</div>')

    # Goal
    out.append('<div class="glass-card">')
    out.append('  <div class="sec-label">Objectif</div>')
    out.append(f'  <div class="goal-text">{esc(a["goal"])}</div>')
    out.append('</div>')

    # LED + Materials row
    led = detect_led(a["codeJS"])
    out.append('<div class="content-row">')
    if led:
        out.append(f'<div class="led-col">{led_svg(led)}</div>')
    out.append('<div class="info-col">')
    out.append('  <div class="sec-label">Materiel</div>')
    out.append('  <div class="needs-wrap">')
    for n in a["needs"]:
        out.append(f'    <span class="need-pill">{esc(n)}</span>')
    out.append('  </div>')
    out.append('</div></div>')

    # Program blocks — use pre-rendered image if available, else iframe
    block_key = f"act-{aid}"
    if block_key in prerendered_blocks:
        b = prerendered_blocks[block_key]
        out.append('<div class="sec-label">Programme (Blocs)</div>')
        out.append(f'<div class="mc-blocks"><img src="{b["uri"]}" width="{b.get("width","")}" height="{b.get("height","")}" alt="MakeCode blocks" style="width:40%;height:auto"></div>')
    else:
        out.append('<div class="sec-label">Programme (Blocs)</div>')
        out.append(f'<div class="mc-blocks" id="mc-{aid}"><div class="mc-loading">Chargement des blocs...</div></div>')
        out.append(f'<script>mcQueue.push({{id:"mc-{aid}",code:{json.dumps(a["codeJS"])}}});</script>')

    # Blocks used — text-only (no MakeCode render, fast)
    blocks_used = detect_blocks(a["codeJS"])
    if blocks_used:
        out.append('<div class="sec-label">Blocs utilises</div>')
        out.append('<div class="blocks-ref-list">')
        for label, color, snippet, desc in blocks_used:
            out.append(f'<div class="block-ref-item">')
            out.append(f'  <div class="block-ref-chip" style="background:{color}">{esc(label)}</div>')
            out.append(f'  <div class="block-ref-desc">{esc(desc)}</div>')
            out.append(f'</div>')
        out.append('</div>')

    # Flowchart
    out.append('<div class="sec-label">Algorithme</div>')
    out.append(generate_flowchart(a["codeJS"]))

    # Pseudocode
    out.append('<div class="sec-label">Pseudo-code</div>')
    out.append(generate_pseudocode(a["codeJS"]))

    # Steps
    if a["blocks"]:
        out.append('<div class="sec-label">Etapes</div>')
        out.append('<ol class="steps-list">')
        for i, b in enumerate(a["blocks"]):
            out.append(f'  <li class="step-item"><span class="step-num">{i+1}</span><span class="step-text">{esc(b)}</span></li>')
        out.append('</ol>')

    # Tip
    out.append(f'<div class="tip-box"><span class="tip-icon">&#128161;</span> {esc(a["tip"])}</div>')

    # Code — stacked vertically, full width, with copy buttons
    out.append('<div class="sec-label">Code</div>')
    js_code = a["codeJS"]
    py_code = a["codePY"]

    out.append('<div class="code-grid">')
    # JS panel
    out.append('<div class="code-panel">')
    out.append('  <div class="code-panel-header js-header"><span class="code-lang-dot js-dot"></span> JavaScript</div>')
    out.append(f'  <button class="copy-btn no-print" onclick="navigator.clipboard.writeText(this.parentElement.querySelector(&quot;.code-block&quot;).textContent);this.textContent=&quot;Copie!&quot;;setTimeout(()=&gt;this.textContent=&quot;Copier&quot;,2000)">Copier</button>')
    out.append(f'  <div class="code-block js-code">{hl_js(js_code)}</div>')
    out.append('</div>')
    # PY panel
    out.append('<div class="code-panel">')
    out.append('  <div class="code-panel-header py-header"><span class="code-lang-dot py-dot"></span> Python</div>')
    out.append(f'  <button class="copy-btn no-print" onclick="navigator.clipboard.writeText(this.parentElement.querySelector(&quot;.code-block&quot;).textContent);this.textContent=&quot;Copie!&quot;;setTimeout(()=&gt;this.textContent=&quot;Copier&quot;,2000)">Copier</button>')
    out.append(f'  <div class="code-block py-code">{hl_py(py_code)}</div>')
    out.append('</div>')
    out.append('</div>')

    # Challenges
    if a["challenges"]:
        out.append('<div class="sec-label">Defis</div>')
        out.append('<div class="chal-list">')
        for ch in a["challenges"]:
            color = {1:"#40BF4A",2:"#F7DF1E",3:"#DC143C"}.get(ch["d"],"#888")
            text = re.sub(r'<[^>]+>', '', ch["t"])
            out.append(f'  <div class="chal-item"><span class="chal-dot" style="background:{color}"></span><span>{esc(text)}</span></div>')
        out.append('</div>')

    # Footer
    out.append(f'<div class="act-footer"><span>Activite #{aid}</span><span>micro:bit &middot; 48 Activites</span></div>')

    out.append('</section>')

# --- CLOSE MAIN ---
out.append('</div>')

# --- JAVASCRIPT ---
out.append('''
<script>
(function() {
  // Sidebar toggle (mobile)
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('mobileToggle');
  const overlay = document.getElementById('mobileOverlay');

  function openSidebar() {
    sidebar.classList.add('open');
    overlay.classList.add('show');
  }
  function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
  }
  toggle.addEventListener('click', function() {
    if (sidebar.classList.contains('open')) closeSidebar();
    else openSidebar();
  });
  overlay.addEventListener('click', closeSidebar);

  // Nav section expand/collapse
  document.querySelectorAll('.nav-section').forEach(function(sec) {
    sec.addEventListener('click', function() {
      var tgt = document.getElementById(this.dataset.target);
      if (tgt) {
        this.classList.toggle('open');
        tgt.classList.toggle('open');
      }
    });
  });

  // Close sidebar on link click (mobile)
  document.querySelectorAll('.nav-link, .nav-cover-link').forEach(function(link) {
    link.addEventListener('click', function() {
      if (window.innerWidth <= 860) closeSidebar();
    });
  });

  // Single-activity view: show one at a time
  var sections = document.querySelectorAll('.act-section');
  var cover = document.getElementById('cover');
  var navLinks = document.querySelectorAll('.nav-link');
  var coverLink = document.querySelector('.nav-cover-link');
  var linkMap = {};
  navLinks.forEach(function(l) { linkMap[l.dataset.id] = l; });

  // Hide all sections initially
  sections.forEach(function(s) { s.style.display = 'none'; });

  function showActivity(id) {
    sections.forEach(function(s) { s.style.display = 'none'; });
    if (cover) cover.style.display = 'none';
    var target = document.getElementById('act-' + id);
    if (target) { target.style.display = 'block'; window.scrollTo(0,0); }
    navLinks.forEach(function(l) { l.classList.remove('active'); });
    if (linkMap[id]) linkMap[id].classList.add('active');
  }

  function showCover() {
    sections.forEach(function(s) { s.style.display = 'none'; });
    if (cover) cover.style.display = '';
    navLinks.forEach(function(l) { l.classList.remove('active'); });
    window.scrollTo(0,0);
  }

  navLinks.forEach(function(link) {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      showActivity(this.dataset.id);
    });
  });

  if (coverLink) {
    coverLink.addEventListener('click', function(e) {
      e.preventDefault();
      showCover();
    });
  }

  if (window.location.hash) {
    var m = window.location.hash.match(/act-(\\d+)/);
    if (m) showActivity(m[1]);
  }

})();
</script>
''')

# MakeCode block renderer iframe + JS
out.append("""
<!-- MakeCode block renderer -->
<iframe id="mcRenderFrame" src="https://makecode.microbit.org/--docs?render=1" style="position:absolute;width:1px;height:1px;border:0;opacity:0;pointer-events:none"></iframe>
<script>
var mcQueue = window.mcQueue || [];
var mcReady = false;

window.addEventListener("message", function(ev){
  var msg = ev.data;
  if(!msg || typeof msg !== "object") return;
  if(msg.source === "makecode" || msg.type === "renderready"){
    mcReady = true;
    processQueue();
  }
  if(msg.type === "renderblocks" && msg.id){
    var container = document.getElementById(msg.id);
    if(container && msg.uri){
      var img = document.createElement("img");
      img.src = msg.uri;
      img.style.maxWidth = "100%";
      img.style.height = "auto";
      img.alt = "MakeCode blocks";
      container.innerHTML = "";
      container.appendChild(img);
    }
  }
});

function processQueue(){
  if(!mcReady) return;
  var frame = document.getElementById("mcRenderFrame");
  if(!frame || !frame.contentWindow) return;
  while(mcQueue.length > 0){
    var req = mcQueue.shift();
    frame.contentWindow.postMessage({
      type: "renderblocks",
      id: req.id,
      code: req.code
    }, "https://makecode.microbit.org");
  }
}
// Try processing after delay if ready signal was missed
setTimeout(function(){ mcReady = true; processQueue(); }, 10000);
</script>
""")

out.append('</body>\n</html>')

# ── Write ──
with open("ebook.html", "w", encoding="utf-8") as f:
    f.write('\n'.join(out))

print(f"Web book generated: ebook.html ({len(activities)} activities)")
print("Open ebook.html in a browser to view the interactive web book")
