# OpenPrep video renderer. Reads a script JSON (see SPEC-FOR-CHATGPT.md) and makes an MP4.
#   python render.py scripts/<id>.json            validate, then render to out/<id>.mp4
#   python render.py scripts/<id>.json --check    validate only
import os, sys, re, json, math, hashlib, asyncio, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache"); os.makedirs(CACHE, exist_ok=True)
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
VOICE, RATE = "en-US-AriaNeural", "-4%"
W, H, FPS = 1280, 720, 24

# ---------------------------------------------------------------- theme (black / white / gray only)
BG, INK, G1, G2, G3, PAN, LINE = (255, 255, 255), (17, 17, 17), (80, 80, 80), (130, 130, 130), (185, 185, 185), (241, 241, 241), (60, 60, 60)
_fc = {}
_FONT_BOLD = ["C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
_FONT_REG = ["C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
def _font_path(bold):
    for p in (_FONT_BOLD if bold else _FONT_REG):
        if os.path.exists(p): return p
    raise FileNotFoundError("no usable font found (on Linux: apt install fonts-dejavu-core)")
def F(size, bold=True):
    k = (int(size), bold)
    if k not in _fc: _fc[k] = ImageFont.truetype(_font_path(bold), int(size))
    return _fc[k]
def mix(c, a): a = max(0.0, min(1.0, a)); return tuple(int(BG[i] + (c[i] - BG[i]) * a) for i in range(3))
def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def back(x): x = max(0.0, min(1.0, x)); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
_m = Image.new("RGB", (4, 4)); _md = ImageDraw.Draw(_m)
def tw(s, f): return _md.textlength(s, font=f)

# ---------------------------------------------------------------- math line parsing / drawing
def parse(s):
    items, buf, i = [], "", 0
    def flush():
        nonlocal buf
        if buf: items.append(("t", buf)); buf = ""
    while i < len(s):
        hit = False
        for name in ("frac(", "sqrt(", "abs("):
            if s.startswith(name, i):
                j = i + len(name); depth = 1; k = j; comma = None
                while k < len(s) and depth:
                    ch = s[k]
                    if ch == "(": depth += 1
                    elif ch == ")": depth -= 1
                    elif ch == "," and depth == 1 and name == "frac(" and comma is None: comma = k
                    k += 1
                inner = s[j:k - 1]; flush()
                if name == "frac(": items.append(("f", inner[:comma - j], inner[comma - j + 1:]))
                elif name == "sqrt(": items.append(("rt", inner))
                else: items.append(("t", "|")); items.extend(parse(inner)); items.append(("t", "|"))
                i = k; hit = True; break
        if hit: continue
        if s[i] == "^":
            if i + 1 < len(s) and s[i + 1] == "(":
                k = s.index(")", i); sup = s[i + 2:k]; i = k + 1
            else:
                m = re.match(r"[A-Za-z0-9]", s[i + 1:]); sup = m.group(0) if m else ""; i += 1 + len(sup)
            flush(); items.append(("sup", sup)); continue
        buf += s[i]; i += 1
    flush(); return items

def sub(f, r): return F(f.size * r, "bold" in f.path.lower() or f.path.lower().endswith("b.ttf"))
def item_w(it, f):
    k = it[0]
    if k == "t": return tw(it[1], f)
    if k == "sup": return tw(it[1], sub(f, .62)) + 2
    if k == "f": fs = sub(f, .66); return max(tw(it[1], fs), tw(it[2], fs)) + 16
    if k == "rt": return tw(it[1], f) + f.size * .55
def math_w(s, f): return sum(item_w(it, f) for it in parse(s))

def draw_math(d, cx, y, s, f, col=INK, al=1.0, strikes=(), anchor="c"):
    """strikes: list of (term, progress). Returns width."""
    items = parse(s); w = sum(item_w(it, f) for it in items)
    x = cx - w / 2 if anchor == "c" else cx; x0 = x; c0 = mix(col, al); cy = y + f.size * .62
    spans = []
    for term, p in strikes:
        at = s.find(term)
        if at >= 0: spans.append((math_w(s[:at], f), math_w(term, f), p))
    for it in items:
        k = it[0]; iw = item_w(it, f)
        if k == "t": d.text((x, y), it[1], font=f, fill=c0)
        elif k == "sup": d.text((x + 1, y - f.size * .22), it[1], font=sub(f, .62), fill=c0)
        elif k == "f":
            fs = sub(f, .66); nw, dw = tw(it[1], fs), tw(it[2], fs)
            d.text((x + iw / 2 - nw / 2, cy - fs.size * 1.38), it[1], font=fs, fill=c0); d.text((x + iw / 2 - dw / 2, cy - fs.size * .12), it[2], font=fs, fill=c0)
            d.line([(x + 3, cy), (x + iw - 3, cy)], fill=c0, width=max(2, int(f.size / 22)))
        elif k == "rt":
            d.text((x, y), "√", font=f, fill=c0); rw = tw(it[1], f); sx = x + f.size * .55
            d.text((sx, y), it[1], font=f, fill=c0); d.line([(sx - 2, y + f.size * .16), (sx + rw, y + f.size * .16)], fill=c0, width=max(2, int(f.size / 22)))
        x += iw
    for off, tl, p in spans:
        if p > 0: d.line([(x0 + off + 3, cy), (x0 + off + 3 + (tl - 6) * p, cy)], fill=INK, width=max(4, int(f.size / 11)))
    return w

# ---------------------------------------------------------------- drawing context
def wrap(s, f, maxw):
    out, cur = [], ""
    for w in s.split(" "):
        t = (cur + " " + w).strip()
        if tw(t, f) <= maxw: cur = t
        else: out.append(cur); cur = w
    return out + [cur]

class Ctx:
    def __init__(s, im, t, bt, bd): s.im, s.d, s.t, s.bt, s.bd = im, ImageDraw.Draw(im), t, bt, bd
    def started(s, i): return s.t >= s.bt[i]
    def since(s, i): return s.t - s.bt[i]
    def a(s, i, delay=0.0, dur=0.5): return ease((s.t - s.bt[i] - delay) / dur)
    def pop(s, i, delay=0.0, dur=0.5): return back((s.t - s.bt[i] - delay) / dur)
    def cur(s): return max([i for i, b in enumerate(s.bt) if b <= s.t] or [0])
    def text(s, cx, y, txt, f, col=INK, al=1.0, anchor="c"):
        w = tw(txt, f); x = cx - w / 2 if anchor == "c" else (cx if anchor == "l" else cx - w); s.d.text((x, y), txt, font=f, fill=mix(col, al)); return w
    def chip(s, cx, cy, txt, al=1.0, size=26):
        if al <= .03: return
        f = F(size); w = tw(txt, f) + 36; h = size * 1.75
        s.d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], h / 2.8, fill=mix(INK, al)); s.text(cx, cy - size * .72, txt, f, BG if al > .6 else mix(INK, al))
    def tick(s, x, y, size, p, wd=8, col=INK):
        pts = [(0, .55), (.35, .9), (1, .1)]; L = [math.dist(pts[i], pts[i + 1]) for i in range(2)]; tot = p * sum(L); out = [pts[0]]
        for i in range(2):
            if tot <= 0: break
            u = min(1, tot / L[i]); out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u)); tot -= L[i]
        if len(out) > 1: s.d.line([(x + a * size, y + b * size) for a, b in out], fill=col, width=wd, joint="curve")
    def cross(s, x, y, size, p, wd=8, col=INK):
        p1, p2 = min(1, p * 2), max(0, p * 2 - 1)
        if p1 > 0: s.d.line([(x, y), (x + size * p1, y + size * p1)], fill=col, width=wd)
        if p2 > 0: s.d.line([(x + size, y), (x + size - size * p2, y + size * p2)], fill=col, width=wd)

ZONE_Y, ZONE_H = 124, 452   # content zone, between the title and the caption
ZC = ZONE_Y + ZONE_H / 2
def fitF(txt, size, maxw, bold=True):
    while size > 22 and math_w(txt, F(size, bold)) > maxw: size -= 2
    return F(size, bold)

def panel(c, x0, y0, x1, y1, al=1.0, fill=PAN, outline=G3, width=3, r=26):
    c.d.rounded_rectangle([x0, y0, x1, y1], r, fill=mix(fill, al) if fill else None, outline=mix(outline, al) if outline else None, width=width)

def _nvis(c, ids):
    vis = [i for i in ids if c.started(i)]
    return max(len(vis) - 1 + (c.a(vis[-1], 0, .45) if vis else 0), 1.0)

# ---------------------------------------------------------------- scene renderers
def r_cards(c, sc):
    cards = [(i, b["card"]) for i, b in enumerate(sc["beats"]) if "card" in b]; gap = 30
    base = [160 if cd.get("sub") else 124 for _, cd in cards]
    k = min(1.0, (ZONE_H - 6) / (sum(base) + gap * (len(cards) - 1))); hs = [h * k for h in base]; gap *= k
    nv = min(_nvis(c, [i for i, _ in cards]), len(hs)); kk = int(nv + 1e-9); fr = nv - kk
    used = sum(hs[:kk]) + gap * (kk - 1) + ((hs[kk] + gap) * fr if kk < len(hs) else 0)
    y = ZC - used / 2; last = max([i for i, _ in cards if c.started(i)] or [-1])
    for (i, cd), h in zip(cards, hs):
        if c.started(i):
            p = min(1, c.pop(i, 0, .45)); al = c.a(i, 0, .35); w = 1080 * (.92 + .08 * p); yy = y + (1 - p) * 22; cur = i == last
            panel(c, 640 - w / 2, yy, 640 + w / 2, yy + h, al, PAN, INK if cur else G3, 4 if cur else 3)
            c.d.rounded_rectangle([640 - w / 2 + 16, yy + 18, 640 - w / 2 + 25, yy + h - 18], 4, fill=mix(INK if cur else G3, al))
            ft = fitF(cd["text"], int(62 * k), 900)
            if cd.get("sub"):
                top = yy + h * .16; draw_math(c.d, 640, top, cd["text"], ft, INK, al); c.text(640, top + ft.size * 1.38, cd["sub"], fitF(cd["sub"], int(32 * k), 900, False), G1, al)
            else: draw_math(c.d, 640, yy + (h - ft.size * 1.3) / 2, cd["text"], ft, INK, al)
        y += h + gap

def r_list(c, sc):
    items = [(i, b["item"]) for i, b in enumerate(sc["beats"]) if "item" in b]; n = len(items); gap = 22
    h = min(110, (ZONE_H - 6 - gap * (n - 1)) / n); fs = int(min(44, h * .46))
    nv = min(_nvis(c, [i for i, _ in items]), n); used = nv * (h + gap) - gap; y = ZC - used / 2; last = max([i for i, _ in items if c.started(i)] or [-1])
    for k, (i, txt) in enumerate(items):
        if c.started(i):
            p = min(1, c.pop(i, 0, .45)); al = c.a(i, 0, .35); yy = y + (1 - p) * 22; cur = i == last
            panel(c, 110, yy, 1170, yy + h, al, PAN, INK if cur else G3, 4 if cur else 3, h * .28)
            d = h * .6; c.d.ellipse([110 + h * .22, yy + (h - d) / 2, 110 + h * .22 + d, yy + (h + d) / 2], fill=mix(INK, al))
            c.text(110 + h * .22 + d / 2, yy + (h - d) / 2 + d * .16, str(k + 1), F(d * .55), BG, 1)
            ft = fitF(txt, fs, 800, False); c.text(690, yy + (h - ft.size * 1.3) / 2, txt, ft, INK, al)
        y += h + gap

def r_steps(c, sc):
    lines = [(0, sc["start"], None)] + [(i, b["result"], b) for i, b in enumerate(sc["beats"]) if "result" in b]; n = len(lines)
    slot = min(138, (ZONE_H - 4) / n); fs0 = int(min(80, (slot - (36 if n > 1 else 0)) / 1.25))
    wid = max(lines, key=lambda l: math_w(l[1], F(fs0)))[1]; f = fitF(wid, fs0, 980); fs = f.size
    y0 = ZC - n * slot / 2 + (slot - fs * 1.25) / 2
    newest = max(j for j, (i2, _, _) in enumerate(lines) if c.started(i2) and (j == 0 or c.since(i2) > .9))
    for k, (i, txt, b) in enumerate(lines):
        appear = c.a(i, .9 if k else 0, .5) if k else c.a(0, 0, .6); yy = y0 + k * slot + (1 - appear) * 18
        if appear <= 0.01: continue
        col = INK if k == newest else G1
        if k == newest and n > 1 and not (b and b.get('final')): panel(c, 150, yy - 8, 1130, yy + fs * 1.2, appear, PAN, None, 0, 22)
        strikes = []
        if k + 1 < n:
            nb = lines[k + 1][2]; ni = lines[k + 1][0]
            if nb and nb.get("strike") and c.started(ni): strikes = [(t, c.a(ni, .15, .5)) for t in nb["strike"]]
        draw_math(c.d, 640, yy, txt, f, col, appear, strikes)
        if b and b.get("op"):
            c.chip(640, y0 + k * slot - (slot - fs * 1.25) / 2 - 2, b["op"], c.a(i, .1, .4), int(max(16, min(26, (slot - fs * 1.25) * .5))))
        if b and b.get("note"): c.text(640, y0 + k * slot + fs * 1.18, b["note"], F(max(15, fs * .34), False), G2, appear)
        if b and b.get("final") and appear > .9:
            w = math_w(txt, f) + 44; p = min(1, c.pop(i, 1.2, .5)); c.d.rounded_rectangle([640 - w / 2 * p, yy - 8, 640 + w / 2 * p, yy + fs * 1.3 + 4], 16, outline=INK, width=5)

def r_check(c, sc):
    rows = [(i, ln) for i, b in enumerate(sc["beats"]) for ln in b.get("lines", [])]; verdicts = [(i, b["verdict"]) for i, b in enumerate(sc["beats"]) if "verdict" in b]
    if not rows: return
    n = len(rows); h = min(108, (ZONE_H - 150) / n); top = ZC - (n * h + 96) / 2
    panel(c, 140, top - 24, 1140, top + n * h + 96, 1, PAN, G3, 3, 30)
    for k, (i, ln) in enumerate(rows):
        if not c.started(i): continue
        al = c.a(i, k * .01, .4); ft = fitF(ln, int(min(56, h * .56)), 700); draw_math(c.d, 545, top + k * h + (h - ft.size * 1.25) / 2, ln, ft, INK, al); c.tick(955, top + k * h + (h - 56) / 2, 56, c.a(i, 1.0 + k * .6, .45), 8)
    for i, v in verdicts:
        if c.started(i): c.chip(640, top + n * h + 52, v, c.a(i, 2.0 + n * .4, .5), 32)

def r_compare(c, sc):
    wr = [(i, b) for i, b in enumerate(sc["beats"]) if "wrong" in b]; rt = [(i, b) for i, b in enumerate(sc["beats"]) if "right" in b]
    texts = [b["wrong"] for _, b in wr] + [b["right"] for _, b in rt] + ["x"]; f = fitF(max(texts, key=lambda t: math_w(t, F(58))), 58, 780)
    ph, gap = 184, 34; top = ZC - (2 * ph + gap) / 2
    if wr and c.started(wr[0][0]):
        i, b = wr[0]; al = c.a(i, 0, .5); y = top + (1 - c.pop(i, 0, .5)) * 20
        panel(c, 120, y, 1160, y + ph, al, PAN, G3, 3)
        c.text(160, y + 18, "COMMON MISTAKE", F(20), G2, al, "l"); draw_math(c.d, 590, y + 52, b["wrong"], f, G1, al)
        cx_, cy_ = 1085, y + ph / 2; c.d.ellipse([cx_ - 38, cy_ - 38, cx_ + 38, cy_ + 38], outline=mix(G1, al), width=5); c.cross(cx_ - 17, cy_ - 17, 34, c.a(i, .8, .5), 8, G1)
        if b.get("wrong_why"): c.text(590, y + ph - 56, b["wrong_why"], F(28, False), G2, c.a(i, 1.0))
    if rt and c.started(rt[0][0]):
        i, b = rt[0]; al = c.a(i, 0, .5); y = top + ph + gap + (1 - c.pop(i, 0, .5)) * 20
        panel(c, 120, y, 1160, y + ph, al, INK, INK, 3)
        if al > .55:
            c.d.text((160, y + 18), "DO THIS", font=F(20), fill=G3); draw_math(c.d, 590, y + 52, b["right"], f, BG, 1)
            cx_, cy_ = 1085, y + ph / 2; c.d.ellipse([cx_ - 38, cy_ - 38, cx_ + 38, cy_ + 38], fill=BG); c.tick(cx_ - 26, cy_ - 30, 56, c.a(i, .8, .5), 8)
            if b.get("right_why"): c.d.text((590 - tw(b["right_why"], F(28, False)) / 2, y + ph - 56), b["right_why"], font=F(28, False), fill=G3)

def r_table(c, sc):
    cols, rows = sc["columns"], sc["rows"]; fs0 = 34
    while True:
        f = F(fs0, False); fb = F(fs0)
        cw = [max([tw(cols[j], fb)] + [math_w(r[j], f) for r in rows]) + 76 for j in range(len(cols))]
        if sum(cw) <= 1120 or fs0 <= 20: break
        fs0 -= 2
    rh = min(84, (ZONE_H - 20) / (len(rows) + 1)); total_w = sum(cw); x0 = 640 - total_w / 2
    top = ZC - (len(rows) + 1) * rh / 2; vis = -1; hl = None
    for i, b in enumerate(sc["beats"]):
        if c.started(i):
            if "reveal_row" in b: vis = max(vis, b["reveal_row"])
            if "highlight" in b: hl = (i, b["highlight"])
    c.d.rounded_rectangle([x0, top, x0 + total_w, top + rh], 14, fill=INK)
    x = x0
    for j, col in enumerate(cols): c.text(x + cw[j] / 2, top + (rh - fs0 * 1.3) / 2, col, fb, BG); x += cw[j]
    for r, row in enumerate(rows):
        yy = top + (r + 1) * rh
        c.d.rectangle([x0, yy, x0 + total_w, yy + rh], fill=PAN if r % 2 == 0 else BG, outline=G3)
        if r <= vis:
            x = x0
            for j, cell in enumerate(row): draw_math(c.d, x + cw[j] / 2, yy + (rh - fs0 * 1.3) / 2, cell, f, INK, 1); x += cw[j]
            if r == vis: c.d.rectangle([x0, yy, x0 + 8, yy + rh], fill=INK)
    if hl:
        r, cc = hl[1]; yy = top + (r + 1) * rh; xx = x0 + sum(cw[:cc]); a = c.a(hl[0], 0, .3)
        c.d.rectangle([xx, yy, xx + cw[cc], yy + rh], outline=mix(INK, a), width=6)

# ---- figures
def fig_balance(c, sc):
    dt = sc["data"]; left = [{"k": s, "gone": None} for s in dt["left"]]; right = [{"k": s, "gone": None} for s in dt["right"]]; tilt = 0.0; tilts = []
    for i, b in enumerate(sc["beats"]):
        if not c.started(i): continue
        for r in b.get("remove", []):
            for side in (("left", "right") if r["side"] == "both" else (r["side"],)):
                lst = left if side == "left" else right; cnt = r["count"]
                for it in reversed(lst):
                    if cnt and it["k"] != "x" and it["gone"] is None: it["gone"] = c.a(i, .5, .9); cnt -= 1
                    elif cnt and it["k"] != "x" and it["gone"] is not None and it["gone"] < 1 and False: pass
        if "tilt" in b: tilts.append((i, {"left": 8, "right": -8, "none": 0}[b["tilt"]]))
    for lst in (left, right):
        for it in lst:
            if it["gone"] is not None and it["gone"] <= 0: it["gone"] = None
    prev = 0.0
    for i, new in tilts:
        if c.started(i): tilt = prev + (new - prev) * c.a(i, .3, .7); prev = new
    d = c.d; cx, cy, arm, th = 640, 235, 330, math.radians(tilt)
    pts = [(cx - arm * math.cos(th), cy + arm * math.sin(th)), (cx + arm * math.cos(th), cy - arm * math.sin(th))]
    d.polygon([(cx, cy), (cx - 55, cy + 260), (cx + 55, cy + 260)], fill=G2); d.rectangle([cx - 120, cy + 256, cx + 120, cy + 274], fill=G1)
    d.line([pts[0], pts[1]], fill=INK, width=12); d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=INK)
    for (ex, ey), lst in zip(pts, (left, right)):
        py = ey + 125; d.line([(ex - 120, py), (ex, ey)], fill=G2, width=3); d.line([(ex + 120, py), (ex, ey)], fill=G2, width=3); d.rounded_rectangle([ex - 135, py, ex + 135, py + 16], 8, fill=INK)
        wts = [66 if it["k"] == "x" else 28 for it in lst]; x = ex - sum(wts) / 2 - 2 * (len(lst) - 1)
        for it, w in zip(lst, wts):
            g = it["gone"] if it["gone"] is not None else 0; al = 1 - g
            if al > .02:
                d.rounded_rectangle([x, py - 40 - 90 * g, x + w, py - 2 - 90 * g], 6, fill=mix(INK if it["k"] == "x" else G2, al))
                if it["k"] == "x": c.text(x + w / 2, py - 41 - 90 * g, "x", F(26), BG, al)
            x += w + 4

def fig_number_line(c, sc):
    dt = sc["data"]; mn, mx, st = dt["min"], dt["max"], dt.get("step", 1); x0, x1, y = 160, 1120, 360; sx = lambda v: x0 + (v - mn) / (mx - mn) * (x1 - x0); d = c.d
    d.line([(x0 - 20, y), (x1 + 20, y)], fill=INK, width=5); v = mn
    while v <= mx + 1e-9: d.line([(sx(v), y - 12), (sx(v), y + 12)], fill=INK, width=3); c.text(sx(v), y + 22, f"{v:g}".replace("-", "−"), F(26, False), G1); v += st
    for i, b in enumerate(sc["beats"]):
        if not c.started(i): continue
        p = c.a(i, .2, .6)
        if "ray" in b:
            r = b["ray"]; xa = sx(r["from"]); xb = x0 - 20 if r["dir"] == "left" else x1 + 20; xe = xa + (xb - xa) * p; d.line([(xa, y), (xe, y)], fill=INK, width=12)
            d.ellipse([xa - 16, y - 16, xa + 16, y + 16], fill=INK if r["style"] == "closed" else BG, outline=INK, width=5)
        if "point" in b:
            pt = b["point"]; xa = sx(pt["at"]); rr = 16 * min(1, c.pop(i, .2, .4)); d.ellipse([xa - rr, y - rr, xa + rr, y + rr], fill=INK if pt.get("style") == "closed" else BG, outline=INK, width=5)
        if "label" in b: c.text(640, 215, b["label"], F(56), INK, c.a(i, .4, .5))

def fig_bar_model(c, sc):
    dt = sc["data"]; total = dt["total"]; x0, x1, y0, bh = 140, 1140, 320, 100; per = (x1 - x0) / total; d = c.d; cur = x0; reveal = {}
    for i, b in enumerate(sc["beats"]):
        for sid in b.get("reveal", []): reveal[sid] = i
    d.rounded_rectangle([x0 - 2, y0 - 2, x1 + 2, y0 + bh + 2], 6, outline=G3, width=2)
    for k, sg in enumerate(dt["segments"]):
        rep = sg.get("repeat", 1)
        for r in range(rep):
            w = sg["value"] * per; i = reveal.get(sg["id"])
            if i is not None and c.started(i):
                span = max(1.0, c.bd[i] * .75); p = c.a(i, r * span / rep, .4) if rep > 1 else c.a(i, 0, .5)
                if p > .01:
                    shade = INK if k % 2 == 0 else G1 if r % 2 == 0 else G2
                    d.rectangle([cur, y0 - (1 - p) * 40, cur + w - 3, y0 + bh - (1 - p) * 40], fill=mix(shade, p))
                    lab = sg["label"] if (rep == 1 or r == 0) and rep == 1 else f"{dt.get('unit','')}{sg['value']}"
                    if p > .9: c.text(cur + w / 2 - 2, y0 + bh / 2 - 17, lab, F(26), BG)
            cur += w
    d.line([(x0, y0 + bh + 34), (x1, y0 + bh + 34)], fill=INK, width=4)
    for xx in (x0, x1): d.line([(xx, y0 + bh + 24), (xx, y0 + bh + 44)], fill=INK, width=4)
    c.text(640, y0 + bh + 54, f"total: {dt.get('unit','')}{total}", F(30), INK)

def fig_rectangle(c, sc):
    dt = sc["data"]; wv, hv = dt["w"], dt["h"]; k = min(560 / wv, 330 / hv); w, h = wv * k, hv * k; x0, y0 = 640 - w / 2, 370 - h / 2; shown = set(); d = c.d
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=PAN, outline=INK, width=6)
    for i, b in enumerate(sc["beats"]):
        for s in b.get("show", []):
            if c.started(i): shown.add((s, i))
    for s, i in shown:
        al = c.a(i, .2, .5)
        if s == "w": c.text(640, y0 + h + 14, str(dt.get("labels", {}).get("w", wv)), F(36), INK, al)
        if s == "h": c.text(x0 - 30, 370 - 22, str(dt.get("labels", {}).get("h", hv)), F(36), INK, al, "r")

def fig_right_triangle(c, sc):
    dt = sc["data"]; a, b = dt["a"], dt["b"]; k = min(520 / a, 330 / b); wa, hb = a * k, b * k; x0, y0 = 640 - wa / 2, 470; P = [(x0, y0), (x0 + wa, y0), (x0 + wa, y0 - hb)]; d = c.d
    d.polygon(P, fill=PAN); d.line(P + [P[0]], fill=INK, width=6)
    for i, bt in enumerate(sc["beats"]):
        if not c.started(i): continue
        al = c.a(i, .2, .5)
        for s in bt.get("show", []):
            if s == "a": c.text(640, y0 + 12, str(dt["a"]), F(36), INK, al)
            if s == "b": c.text(P[1][0] + 18, y0 - hb / 2 - 22, str(dt["b"]), F(36), INK, al, "l")
            if s == "c": c.text(640 - 40, y0 - hb / 2 - 56, str(dt["c"]), F(36), INK, al, "r")
            if s == "right_mark": d.rectangle([P[1][0] - 30, y0 - 30, P[1][0], y0], outline=mix(INK, al), width=4)
            if s == "angle": d.arc([x0 - 40, y0 - 40, x0 + 40, y0 + 40], -math.degrees(math.atan2(hb, wa)), 0, fill=mix(INK, al), width=5); c.text(x0 + 62, y0 - 36, dt.get("angle", "A"), F(30), INK, al)


# ---- statistics, probability and geometry figures
def _axis(c, x0, x1, y, vmin, vmax, step, labels=True):
    d = c.d; sx = lambda v: x0 + (v - vmin) / (vmax - vmin) * (x1 - x0)
    d.line([(x0 - 10, y), (x1 + 10, y)], fill=INK, width=4); v = vmin
    while v <= vmax + 1e-9:
        d.line([(sx(v), y - 8), (sx(v), y + 8)], fill=INK, width=3)
        if labels: c.text(sx(v), y + 14, f"{v:g}".replace("-", "−"), F(22, False), G1)
        v += step
    return sx

def _shows(sc, c):
    out = {}
    for i, b in enumerate(sc["beats"]):
        if c.started(i):
            for s_ in b.get("show", []): out.setdefault(s_, i)
    return out

def _median(v):
    v = sorted(v); n = len(v); return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2

def _nice(lo, hi):
    span = hi - lo; step = 1
    for st in (1, 2, 5, 10, 20, 25, 50, 100, 200, 500, 1000):
        step = st
        if span / st <= 10: break
    return step

def fig_dot_plot(c, sc):
    vals = sorted(sc["data"]["values"]); lo = math.floor(min(vals)) - 1; hi = math.ceil(max(vals)) + 1; step = max(1, round((hi - lo) / 12))
    yb = 480; sx = _axis(c, 140, 1140, yb, lo, hi, step); sh = _shows(sc, c); d = c.d; cnt = {}; r = min(18, 1000 / (hi - lo) / 2.6)
    for k, v in enumerate(vals):
        cnt[v] = cnt.get(v, 0) + 1; i = sh.get("points")
        if i is None: continue
        p = c.a(i, .1 + k * .12, .3)
        if p <= 0: continue
        cx = sx(v); cy = yb - 26 - (cnt[v] - 1) * (2 * r + 4) - (1 - p) * 30; d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=mix(INK, p))
    if "median" in sh:
        m = _median(vals); x = sx(m); a = c.a(sh["median"], 0, .5); d.line([(x, 215), (x, yb)], fill=mix(G1, a), width=5); c.text(x, 165, f"median = {m:g}", F(30), G1, a)
    if "mean" in sh:
        m = sum(vals) / len(vals); x = sx(m); a = c.a(sh["mean"], 0, .5); d.polygon([(x, yb + 46), (x - 14, yb + 74), (x + 14, yb + 74)], fill=mix(INK, a)); c.text(x, yb + 80, f"mean = {round(m, 2):g}", F(30), INK, a)
    if "range" in sh:
        a = c.a(sh["range"], 0, .5); xa, xb = sx(vals[0]), sx(vals[-1]); y = 290
        d.line([(xa, y), (xb, y)], fill=mix(INK, a), width=5)
        for xx in (xa, xb): d.line([(xx, y - 12), (xx, y + 12)], fill=mix(INK, a), width=5)
        c.text((xa + xb) / 2, y - 48, f"range = {vals[-1] - vals[0]:g}", F(30), INK, a)

def fig_histogram(c, sc):
    dt = sc["data"]; vals, bins = dt["values"], dt["bins"]; nb = len(bins) - 1
    counts = [sum(1 for v in vals if bins[i] <= v < bins[i + 1] or (i == nb - 1 and v == bins[-1])) for i in range(nb)]
    yb = 480; sx = _axis(c, 160, 1120, yb, bins[0], bins[-1], bins[1] - bins[0]); mx = max(counts); sh = _shows(sc, c); i = sh.get("bars")
    for k, n in enumerate(counts):
        if i is None: break
        p = c.a(i, k * .18, .4); h = n / mx * 270 * p; xa, xb = sx(bins[k]), sx(bins[k + 1])
        c.d.rectangle([xa + 2, yb - h, xb - 2, yb], fill=INK if k % 2 == 0 else G1)
        if p > .9: c.text((xa + xb) / 2, yb - h - 38, str(n), F(28), INK)
    if "labels" in sh: c.text(640, yb + 56, "frequency shown above each bar", F(24, False), G1, c.a(sh["labels"], 0, .5))

def fig_box_plot(c, sc):
    v = sorted(sc["data"]["values"]); n = len(v); q1 = _median(v[:n // 2]); q3 = _median(v[(n + 1) // 2:]); med = _median(v)
    lo = math.floor(v[0]) - 1; hi = math.ceil(v[-1]) + 1; step = max(1, round((hi - lo) / 12)); yb = 480; sx = _axis(c, 140, 1140, yb, lo, hi, step); sh = _shows(sc, c); d = c.d; ya, yc = 250, 360; ym = (ya + yc) / 2
    if "range" in sh:
        a = c.a(sh["range"], 0, .6); d.line([(sx(v[0]), ym), (sx(q1), ym)], fill=mix(INK, a), width=5); d.line([(sx(q3), ym), (sx(v[-1]), ym)], fill=mix(INK, a), width=5)
        for xx, lab in ((v[0], "min"), (v[-1], "max")): d.line([(sx(xx), ym - 24), (sx(xx), ym + 24)], fill=mix(INK, a), width=5); c.text(sx(xx), ya - 44, f"{lab} = {xx:g}", F(26), INK, a)
    if "q1" in sh and "q3" in sh:
        a = min(c.a(sh["q1"], 0, .5), c.a(sh["q3"], 0, .5)); d.rectangle([sx(q1), ya, sx(q3), yc], fill=mix(PAN, a), outline=mix(INK, a), width=5)
    for key, val in (("q1", q1), ("q3", q3)):
        if key in sh: a = c.a(sh[key], 0, .5); d.line([(sx(val), ya), (sx(val), yc)], fill=mix(INK, a), width=5); c.text(sx(val), yc + 14, f"{key.upper()} = {val:g}", F(26), INK, a)
    if "median" in sh: a = c.a(sh["median"], 0, .5); d.line([(sx(med), ya), (sx(med), yc)], fill=mix(INK, a), width=9); c.text(sx(med), ya - 44, f"median = {med:g}", F(26), INK, a)

def fig_scatter(c, sc):
    dt = sc["data"]; pts = dt["points"]; xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; ln = dt.get("line")
    xmax = max(xs) + 1; ymax = max(ys + ([ln["slope"] * xmax + ln["intercept"], ln["intercept"]] if ln else [0])) + 1; x0, x1, y0, y1 = 200, 1080, 150, 520
    sx = lambda v: x0 + v / xmax * (x1 - x0); sy = lambda v: y1 - v / ymax * (y1 - y0); d = c.d; sh = _shows(sc, c)
    d.line([(x0, y1), (x1 + 10, y1)], fill=INK, width=4); d.line([(x0, y0 - 10), (x0, y1)], fill=INK, width=4)
    stx = _nice(0, xmax); sty = _nice(0, ymax); v = 0
    while v <= xmax: d.line([(sx(v), y1 - 6), (sx(v), y1 + 6)], fill=INK, width=3); c.text(sx(v), y1 + 12, f"{v:g}", F(22, False), G1); v += stx
    v = 0
    while v <= ymax: d.line([(x0 - 6, sy(v)), (x0 + 6, sy(v))], fill=INK, width=3); c.text(x0 - 14, sy(v) - 13, f"{v:g}", F(22, False), G1, 1, "r"); v += sty
    if "line" in sh and ln:
        a = c.a(sh["line"], 0, .7); xe = xmax * a; d.line([(sx(0), sy(ln["intercept"])), (sx(xe), sy(ln["slope"] * xe + ln["intercept"]))], fill=INK, width=6)
    if "residual" in sh and ln:
        a = c.a(sh["residual"], 0, .6)
        for px_, py_ in pts: d.line([(sx(px_), sy(py_)), (sx(px_), sy(py_ + (ln["slope"] * px_ + ln["intercept"] - py_) * a))], fill=G2, width=3)
    if "points" in sh:
        for k, (px_, py_) in enumerate(pts):
            p = c.a(sh["points"], .1 + k * .1, .3)
            if p > 0: r = 9 * min(1, p); d.ellipse([sx(px_) - r, sy(py_) - r, sx(px_) + r, sy(py_) + r], fill=INK)

def fig_two_way_table(c, sc):
    dt = sc["data"]; rows, cols, cells = dt["rows"], dt["cols"], dt["cells"]; sh = _shows(sc, c); tot = "totals" in sh
    nr = len(rows) + 1 + (1 if tot else 0); nc = len(cols) + 1 + (1 if tot else 0); cw, rh = 170, 70; x0 = 640 - nc * cw / 2; y0 = ZONE_Y + (ZONE_H - nr * rh) / 2; d = c.d
    grid = [[""] + list(cols) + (["Total"] if tot else [])]
    for r, nm in enumerate(rows): grid.append([nm] + [str(v) for v in cells[r]] + ([str(sum(cells[r]))] if tot else []))
    if tot: grid.append(["Total"] + [str(sum(cells[r][j] for r in range(len(rows)))) for j in range(len(cols))] + [str(sum(sum(rw) for rw in cells))])
    hl = [(k.split(":")[1], i) for k, i in sh.items() if k.startswith("cell:")]
    for r in range(nr):
        for j in range(nc):
            xa, ya = x0 + j * cw, y0 + r * rh; head = r == 0 or j == 0
            d.rectangle([xa, ya, xa + cw, ya + rh], fill=INK if (r == 0 and j > 0) else PAN if head else BG, outline=G3, width=2)
            c.text(xa + cw / 2, ya + 16, grid[r][j], F(30), BG if (r == 0 and j > 0) else INK)
    for key, i in hl:
        rr, cc = [int(t) for t in key.split(",")]; xa, ya = x0 + (cc + 1) * cw, y0 + (rr + 1) * rh; d.rectangle([xa, ya, xa + cw, ya + rh], outline=mix(INK, c.a(i, 0, .3)), width=7)

def fig_tree(c, sc):
    br = sc["data"]["branches"]; sh = _shows(sc, c); d = c.d; rx, ry = 260, 340; n = len(br); d.ellipse([rx - 12, ry - 12, rx + 12, ry + 12], fill=INK)
    for k, b in enumerate(br):
        ty = ry + (k - (n - 1) / 2) * 150; i = sh.get("branches")
        if i is None: break
        p = c.a(i, k * .3, .5); ex = rx + (760 - rx) * p; ey = ry + (ty - ry) * p; d.line([(rx, ry), (ex, ey)], fill=INK, width=5)
        if p > .95:
            d.rounded_rectangle([760, ty - 32, 960, ty + 32], 14, fill=PAN, outline=INK, width=3); c.text(860, ty - 18, b["label"], F(30), INK)
            c.text(500, (ry + ty) / 2 - 44, b["p"], F(30), INK)

def fig_triangle(c, sc):
    dt = sc["data"]; A, B, C = dt["angles"]; labs = dt.get("labels", ["A", "B", "C"]); sh = _shows(sc, c); d = c.d
    a = 1.0; cc = a * math.sin(math.radians(C)) / math.sin(math.radians(A))
    Bp = (0, 0); Cp = (a, 0); Ap = (cc * math.cos(math.radians(B)), -cc * math.sin(math.radians(B))); xs = [Bp[0], Cp[0], Ap[0]]; ys = [Bp[1], Cp[1], Ap[1]]
    k = min(620 / (max(xs) - min(xs)), 300 / (max(ys) - min(ys))); ox = 640 - (max(xs) + min(xs)) / 2 * k; oy = 470
    P = {n_: (ox + p[0] * k, oy + p[1] * k) for n_, p in zip((labs[0], labs[1], labs[2]), (Ap, Bp, Cp))}; pts = [P[labs[0]], P[labs[1]], P[labs[2]]]
    d.polygon(pts, fill=PAN); d.line(pts + [pts[0]], fill=INK, width=6)
    cxm = sum(p[0] for p in pts) / 3; cym = sum(p[1] for p in pts) / 3
    for nm, ang in zip(labs, (A, B, C)):
        x, y = P[nm]; vx, vy = cxm - x, cym - y; ln_ = math.hypot(vx, vy) or 1
        c.text(x - vx / ln_ * 40, y - vy / ln_ * 40 - 16, nm, F(30), G1)
        if nm in sh: c.text(x + vx / ln_ * 62, y + vy / ln_ * 62 - 16, f"{ang}°", F(28), INK, c.a(sh[nm], 0, .5))
    if "sum" in sh: c.text(640, 560, f"{A}° + {B}° + {C}° = {A + B + C}°", F(40), INK, c.a(sh["sum"], 0, .5))

def fig_circle(c, sc):
    dt = sc["data"]; sh = _shows(sc, c); d = c.d; cx, cy, r = 640, 340, 190; sec = (dt.get("sectors") or [{"deg": 90}])[0]["deg"]
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=6, fill=PAN)
    if "sector" in sh:
        a = c.a(sh["sector"], 0, .6); d.pieslice([cx - r, cy - r, cx + r, cy + r], -sec * a, 0, fill=mix(G3, a), outline=INK, width=5)
    if "arc" in sh: a = c.a(sh["arc"], 0, .6); d.arc([cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8], -sec * a, 0, fill=INK, width=14)
    if "diameter" in sh: a = c.a(sh["diameter"], 0, .5); d.line([(cx - r, cy), (cx - r + 2 * r * a, cy)], fill=INK, width=5); c.text(cx, cy + 12, "diameter", F(26), INK, a)
    if "radius" in sh: a = c.a(sh["radius"], 0, .5); d.line([(cx, cy), (cx - r * .7 * a, cy - r * .7 * a)], fill=INK, width=5); c.text(cx - r * .45, cy - r * .62 - 30, f"r = {dt.get('radius', '')}", F(28), INK, a)
    if "chord" in sh:
        a = c.a(sh["chord"], 0, .5); p1 = (cx + r * math.cos(math.radians(210)), cy - r * math.sin(math.radians(210))); p2 = (cx + r * math.cos(math.radians(330)), cy - r * math.sin(math.radians(330)))
        d.line([p1, (p1[0] + (p2[0] - p1[0]) * a, p1[1] + (p2[1] - p1[1]) * a)], fill=INK, width=5); c.text(cx, p1[1] + 12, "chord", F(26), INK, a)
    if "tangent" in sh: a = c.a(sh["tangent"], 0, .5); d.line([(cx + r, cy - 150 * a), (cx + r, cy + 150 * a)], fill=INK, width=5); c.text(cx + r + 14, cy - 15, "tangent", F(26), INK, a, "l")
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=INK); c.text(cx + 14, cy - 40, dt.get("center", "O"), F(28), INK, 1, "l")

def fig_parallel_lines(c, sc):
    A = sc["data"]["angle"]; sh = _shows(sc, c); d = c.d; ya, yb_ = 250, 450; x1_, x2_ = 700, 700 - 200 / math.tan(math.radians(A))
    d.line([(180, ya), (1100, ya)], fill=INK, width=5); d.line([(180, yb_), (1100, yb_)], fill=INK, width=5)
    if "transversal" in sh:
        a = c.a(sh["transversal"], 0, .6); dx, dy = x1_ - x2_, ya - yb_; d.line([(x2_ - dx * .35, yb_ - dy * .35), (x2_ - dx * .35 + (dx * 1.7) * a, yb_ - dy * .35 + (dy * 1.7) * a)], fill=INK, width=5)
    vals = {1: 180 - A, 2: A, 3: A, 4: 180 - A}; offs = {1: (-62, -50), 2: (22, -50), 3: (-62, 14), 4: (22, 14)}
    for k in range(1, 9):
        key = f"angle{k}"
        if key in sh:
            base = 1 if k <= 4 else 5; ix, iy = (x1_, ya) if k <= 4 else (x2_, yb_); kk = k - base + 1; ox, oy = offs[kk]
            c.text(ix + ox + 20, iy + oy, f"{vals[kk]}°", F(28), INK, c.a(sh[key], 0, .4)); c.text(ix + ox + 20, iy + oy + (32 if oy < 0 else -26), str(k), F(18, False), G2, c.a(sh[key], 0, .4))
    if "equal_pairs" in sh:
        a = c.a(sh["equal_pairs"], 0, .5)
        for k in (2, 3, 6, 7):
            base = 1 if k <= 4 else 5; ix, iy = (x1_, ya) if k <= 4 else (x2_, yb_); ox, oy = offs[k - base + 1]; d.ellipse([ix + ox + 6, iy + oy - 8, ix + ox + 84, iy + oy + 40], outline=mix(INK, a), width=4)

FIGS = {"balance": fig_balance, "number_line": fig_number_line, "bar_model": fig_bar_model, "rectangle": fig_rectangle, "right_triangle": fig_right_triangle, "dot_plot": fig_dot_plot, "histogram": fig_histogram, "box_plot": fig_box_plot, "scatter": fig_scatter, "two_way_table": fig_two_way_table, "tree": fig_tree, "triangle": fig_triangle, "circle": fig_circle, "parallel_lines": fig_parallel_lines}
_figbox = {}
def _fig_draw(sc, fn, t, bt, bd):
    im2 = Image.new("RGB", (W, H), BG); fn(Ctx(im2, t, bt, bd), sc); return im2
def r_figure(c, sc):
    fn = FIGS.get(sc["kind"])
    if not fn: c.text(640, 330, f"[figure: {sc['kind']}: not built yet]", F(32), G2); return
    key = id(sc)
    if key not in _figbox:
        blank = Image.new("RGB", (W, H), BG); box = None
        for tt in [0] + [c.bt[i] + 1.2 for i in range(len(c.bt))] + [1e6]:
            bb = ImageChops.difference(_fig_draw(sc, fn, tt, c.bt, c.bd), blank).getbbox()
            if bb: box = bb if box is None else (min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3]))
        _figbox[key] = box or (0, 0, W, H)
    x0, y0, x1, y1 = _figbox[key]; pad = 36; x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    cut = _fig_draw(sc, fn, c.t, c.bt, c.bd).crop((x0, y0, x1, y1)); w, h = cut.size; k = min(1060 / w, (ZONE_H - 10) / h, 1.55)
    cut = cut.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS); c.im.paste(cut, (int(640 - cut.width / 2), int(ZC - cut.height / 2)))

# ---- reading and writing
def text_layout(text, f, maxw, cx, y):
    words, x, lines, cur, cw = [], 0, [], [], 0; pos = 0
    for w in text.split(" "):
        at = text.index(w, pos); pos = at + len(w); ww = tw(w, f); sp = tw(" ", f)
        if cur and cw + sp + ww > maxw: lines.append((cur, cw)); cur, cw = [], 0
        cur.append((w, at, ww)); cw += (sp if len(cur) > 1 else 0) + ww
    lines.append((cur, cw)); out = []; yy = y; lh = f.size * 1.55
    for ln, lw in lines:
        x = cx - lw / 2
        for w, at, ww in ln: out.append((w, at, x, yy, ww)); x += ww + tw(" ", f)
        yy += lh
    return out, yy

def r_passage(c, sc):
    text = sc["text"]
    for fs in (36, 34, 32, 30, 28, 26, 24):
        f = F(fs, False); words, yend = text_layout(text, f, 920, 640, 0)
        if yend <= 330: break
    hh = yend; top = ZC - hh / 2 - 14; words = [(w, at, x, y + top, ww) for w, at, x, y, ww in words]
    panel(c, 110, top - 44, 1170, top + hh + 34, 1, PAN, G3, 3, 28)
    c.d.text((138, top - 52), "“", font=F(110), fill=G3)
    hl, ul = [], []
    for i, b in enumerate(sc["beats"]):
        if c.started(i):
            if b.get("highlight") and text.find(b["highlight"]) >= 0: hl.append((text.find(b["highlight"]), len(b["highlight"]), c.a(i, .1, .4)))
            if b.get("underline") and text.find(b["underline"]) >= 0: ul.append((text.find(b["underline"]), len(b["underline"]), c.a(i, .1, .4)))
    for w, at, x, y, ww in words:
        inh = max([a for s, l, a in hl if s <= at < s + l] or [0]); inu = max([a for s, l, a in ul if s <= at < s + l] or [0])
        if inh > 0: c.d.rectangle([x - 4, y + 2, x + ww + 4, y + f.size * 1.35], fill=mix(INK, inh))
        c.d.text((x, y), w, font=f, fill=BG if inh > .5 else INK)
        if inu > 0: c.d.line([(x, y + f.size * 1.3), (x + ww * inu, y + f.size * 1.3)], fill=INK, width=4)
    if sc.get("source"): c.text(640, top + hh + 46, sc["source"].upper(), F(20), G2)

def r_choices(c, sc):
    q = sc["question"]; fq = F(32); ql = wrap(q, fq, 1020); opts = sc["options"]; n = len(opts)
    qh = len(ql) * 44; h = min(92, (ZONE_H - qh - 26) / n); y = ZC - (qh + 26 + n * h) / 2
    for ln in ql: c.text(640, y, ln, fq, INK); y += 44
    y += 26; fo = F(30 if h >= 80 else 26, False); st = {k: None for k in opts}; pick = None; point = None
    for i, b in enumerate(sc["beats"]):
        if not c.started(i): continue
        if "eliminate" in b: st[b["eliminate"]] = (i, b.get("why", ""))
        if "pick" in b: pick = (i, b["pick"])
        if "point" in b: point = (i, b["point"])
    for k, txt in opts.items():
        e = st[k]; isp = pick and pick[1] == k; al = 1 - .6 * c.a(e[0], 0, .5) if e else 1; rh = h - 14
        fill = INK if (isp and c.a(pick[0], 0, .4) > .5) else PAN; tc = BG if fill == INK else INK
        c.d.rounded_rectangle([140, y, 1140, y + rh], 20, fill=fill if isp else mix(PAN, al), outline=mix(INK if (point and point[1] == k) else G3, al), width=4 if point and point[1] == k else 3)
        d = rh * .62; c.d.ellipse([140 + 20, y + (rh - d) / 2, 140 + 20 + d, y + (rh + d) / 2], outline=mix(tc if isp else INK, al), width=3); c.text(140 + 20 + d / 2, y + (rh - d) / 2 + d * .17, k, F(d * .5), tc if isp else mix(INK, al))
        lines = wrap(txt, fo, 620); ty = y + rh / 2 - len(lines) * fo.size * .62
        for ln in lines: c.text(560, ty, ln, fo, tc if isp else mix(INK, al)); ty += fo.size * 1.24
        if e:
            p = c.a(e[0], .2, .5); wd = tw(lines[0], fo); c.d.line([(560 - wd / 2, y + rh / 2), (560 - wd / 2 + wd * p, y + rh / 2)], fill=G1, width=4)
            if e[1]:
                wl = wrap(e[1], F(21, False), 210); wy = y + rh / 2 - len(wl) * 14
                for ln in wl: c.text(1010, wy, ln, F(21, False), G1, c.a(e[0], .6, .4)); wy += 28
        y += h

# ---- desmos (real recordings)
def desmos_frames(sc):
    key = hashlib.sha1(json.dumps([b.get("actions") for b in sc["beats"]]).encode()).hexdigest()[:12]; d = os.path.join(CACHE, "desmos_" + key); meta = os.path.join(d, "marks.json")
    if os.path.exists(meta): return d, json.load(open(meta))
    from playwright.sync_api import sync_playwright
    os.makedirs(d, exist_ok=True); GR = ["#111111", "#8c8c8c", "#444444", "#b0b0b0"]
    CUR = """(()=>{const c=document.createElement('div');c.style.cssText='position:fixed;left:0;top:0;z-index:99999;pointer-events:none;width:28px;height:28px;';c.innerHTML='<svg width="28" height="28" viewBox="0 0 24 24"><path d="M3 2l16 9-7 2 4 8-3 1-4-8-6 5z" fill="#111" stroke="#fff" stroke-width="1.5"/></svg>';document.body.appendChild(c);window.__mv=(x,y)=>{c.style.transform='translate('+x+'px,'+y+'px)'};window.__mv(520,420)})()"""
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True, **({"channel": "chrome"} if sys.platform == "win32" else {"args": ["--no-sandbox"]})); pg = br.new_page(viewport={"width": 1100, "height": 620})
        pg.goto("https://www.desmos.com/calculator", wait_until="networkidle"); pg.wait_for_timeout(2500); pg.mouse.click(303, 523); pg.wait_for_timeout(300); pg.evaluate(CUR)
        n = [0]; cur = [520, 420]; marks = []; lost = [False]
        def snap(k=1):
            for _ in range(k): pg.screenshot(path=os.path.join(d, f"{n[0]:04d}.jpg"), type="jpeg", quality=88); n[0] += 1
        def recolor(): pg.evaluate("Calc.getState().expressions.list.forEach((e,i)=>{if(e.type==='expression'&&!/^[a-z]=-?[0-9.]+$/.test(e.latex||''))Calc.setExpression({id:e.id,color:%s[i%%4]})})" % json.dumps(GR))
        def focus_last():
            r = pg.evaluate("(()=>{const e=[...document.querySelectorAll('.dcg-expressionitem')];const b=e[e.length-1].getBoundingClientRect();return [b.x+b.width*0.5,b.y+b.height*0.5]})()"); pg.mouse.click(r[0], r[1]); pg.wait_for_timeout(150)
        def move(x, y, fr=14):
            x0, y0 = cur
            for i in range(1, fr + 1):
                t = i / fr; t = t * t * (3 - 2 * t); pg.evaluate(f"__mv({x0+(x-x0)*t},{y0+(y-y0)*t})"); pg.mouse.move(x0 + (x - x0) * t, y0 + (y - y0) * t); snap()
            cur[:] = [x, y]
        def px(mx, my):
            g = pg.evaluate("Calc.graphpaperBounds"); pc, mc = g["pixelCoordinates"], g["mathCoordinates"]
            return (pc["left"] + (mx - mc["left"]) / (mc["right"] - mc["left"]) * (pc["right"] - pc["left"]), 46 + pc["top"] + (mc["top"] - my) / (mc["top"] - mc["bottom"]) * (pc["bottom"] - pc["top"]))
        for b in sc["beats"]:
            marks.append(n[0])
            for act in b.get("actions", []):
                kind, _, arg = act.partition(":"); arg = arg.strip(); kind = kind.strip()
                if kind == "type":
                    if lost[0]: focus_last(); lost[0] = False
                    snap(3)
                    for ch in arg:
                        pg.keyboard.press("ArrowRight") if ch == ">" else pg.keyboard.type(ch); snap()
                    pg.keyboard.press("Enter"); snap(3)
                    m = re.search(r"\b([a-z])\b(?![^()]*=)", arg)
                    recolor(); pg.wait_for_timeout(150); snap(12)
                elif kind == "slider":
                    lost[0] = True
                    m = re.match(r"(\w)\s+from\s+(-?[\d.]+)\s+to\s+(-?[\d.]+)\s+step\s+([\d.]+)", arg); name, a, z, st = m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4)); lo, hi = min(a, z), max(a, z)
                    pg.evaluate("(()=>{const l=Calc.getState().expressions.list.find(e=>new RegExp('^%s=').test((e.latex||'').replace(/\\s/g,'')));const id=l?l.id:'s_%s';Calc.setExpression({id,latex:'%s=%s',sliderBounds:{min:%s,max:%s,step:%s}});window.__sid=id})()" % (name, name, name, a, min(lo, -10), max(hi, 10), st)); pg.wait_for_timeout(300); snap(10)
                    v = a; sgn = 1 if z >= a else -1
                    while (v - z) * sgn <= 1e-9:
                        pg.evaluate("Calc.setExpression({id:window.__sid,latex:'%s=%s'})" % (name, v)); snap(3); v += sgn * st
                    snap(10)
                elif kind == "bounds":
                    lost[0] = True
                    kv = dict(re.findall(r"(\w+)=(-?[\d.]+)", arg)); pg.evaluate("Calc.setMathBounds({left:%s,right:%s,bottom:%s,top:%s})" % (kv["left"], kv["right"], kv["bottom"], kv["top"])); pg.wait_for_timeout(400); snap(10)
                elif kind == "click":
                    lost[0] = True
                    mx, my = [float(v) for v in arg.split(",")]; x, y = px(mx, my); move(x, y); snap(4); pg.mouse.click(x, y); snap(8); pg.mouse.click(x, y); snap(14)
                elif kind == "table":
                    lost[0] = True
                    pg.evaluate("Calc.setExpression({type:'table',columns:[%s]})" % ",".join("{latex:'%s',values:[%s]}" % (seg.split()[0], ",".join(f"'{v}'" for v in seg.split()[1:])) for seg in arg.split(";"))); pg.wait_for_timeout(500); snap(14)
                elif kind == "hold": snap(max(6, int(float(arg) * 12)))
            snap(6)
        marks.append(n[0]); br.close()
    json.dump({"marks": marks, "fps": 12}, open(meta, "w")); return d, {"marks": marks, "fps": 12}

_dc = {}
def r_desmos(c, sc):
    d, meta = sc["_frames"]; marks = meta["marks"]; b = c.cur(); k = min(len(marks) - 2, b); lo, hi = marks[k], max(marks[k], marks[k + 1] - 1)
    p = min(1.0, c.since(b) / max(0.5, c.bd[b] * .8)); fr = lo + int(p * (hi - lo)); key = (d, fr)
    if key not in _dc:
        if len(_dc) > 8: _dc.pop(next(iter(_dc)))
        _dc[key] = Image.open(os.path.join(d, f"{fr:04d}.jpg")).convert("RGB").resize((960, 541), Image.LANCZOS)
    c.d.rounded_rectangle([150, 126, 1130, 681 - 8], 16, fill=G3); c.im.paste(_dc[key], (160, 132))

RENDER = {"cards": r_cards, "list": r_list, "steps": r_steps, "check": r_check, "compare": r_compare, "table": r_table, "figure": r_figure, "desmos": r_desmos, "passage": r_passage, "choices": r_choices}

# ---------------------------------------------------------------- validation
KINDS = set(FIGS) | {"triangle", "circle", "parallel_lines", "dot_plot", "histogram", "box_plot", "scatter", "two_way_table", "tree"}
def to_sympy(line):
    import sympy as sp
    from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
    s = line.replace("−", "-").replace("×", "*").replace("÷", "/").replace("π", "pi")
    def conv(s):
        while "frac(" in s:
            i = s.index("frac("); depth = 1; k = i + 5; comma = None
            while depth:
                ch = s[k]; depth += (ch == "(") - (ch == ")")
                if ch == "," and depth == 1 and comma is None: comma = k
                k += 1
            s = s[:i] + "((" + s[i + 5:comma] + ")/(" + s[comma + 1:k - 1] + "))" + s[k:]
        return s.replace("sqrt(", "sqrt(").replace("abs(", "Abs(")
    s = conv(s); tr = standard_transformations + (implicit_multiplication_application, convert_xor)
    import sympy as sp
    return sp.nsimplify(parse_expr(s, transformations=tr), rational=True)

def equivalent(a, b):
    import sympy as sp
    try:
        la, ra = a.split("="); lb, rb = b.split("=")
        ea, eb = to_sympy(la) - to_sympy(ra), to_sympy(lb) - to_sympy(rb); fs = sorted(ea.free_symbols | eb.free_symbols, key=str)
        if len(fs) != 1: return None
        return sp.solveset(ea, fs[0], sp.S.Reals) == sp.solveset(eb, fs[0], sp.S.Reals)
    except Exception: return None

def equivalent_expr(a, b):
    import sympy as sp
    try: return bool(sp.simplify(to_sympy(a) - to_sympy(b)) == 0)
    except Exception: return None

def validate(js):
    errs, warns = [], []; total = 0
    for k in ("id", "skill", "part", "title", "section_label", "scenes"):
        if k not in js: errs.append(f"missing key: {k}")
    if errs: return errs, warns
    for si, sc in enumerate(js["scenes"]):
        P = f"scene {si + 1} ({sc.get('type')})"
        if sc.get("type") not in RENDER: errs.append(f"{P}: unknown scene type"); continue
        if len(sc.get("title", "")) > 40: errs.append(f"{P}: title over 40 characters")
        if sc["type"] == "figure" and sc.get("kind") not in KINDS: errs.append(f"{P}: unknown figure kind {sc.get('kind')}")
        if sc["type"] == "figure" and sc.get("kind") not in FIGS: warns.append(f"{P}: figure kind '{sc.get('kind')}' is not built yet")
        prev = sc.get("start")
        for bi, b in enumerate(sc.get("beats", [])):
            Q = f"{P} beat {bi + 1}"; say = b.get("say", ""); n = len(say.split()); total += n
            if not 12 <= n <= 45: errs.append(f"{Q}: say has {n} words (need 12 to 45)")
            if re.search(r"[0-9+=×÷−^<>≤≥%$/*]", say): errs.append(f"{Q}: say contains digits or symbols; spell them out")
            if "!" in say: errs.append(f"{Q}: say contains an exclamation mark")
            for fld in ("start", "result", "wrong", "right", "text"):
                v = b.get(fld) or (sc.get(fld) if bi == 0 and fld == "start" else None)
                if isinstance(v, str) and sc["type"] != "passage" and len(v) > 40: errs.append(f"{Q}: {fld} over 40 characters")
            for ln in b.get("lines", []):
                if len(ln) > 40: errs.append(f"{Q}: check line over 40 characters")
            if sc["type"] == "steps" and "result" in b:
                for t in b.get("strike", []):
                    if prev is None or t not in prev: errs.append(f"{Q}: strike term '{t}' not in previous line '{prev}'")
                skip = "square both" in b.get("op", "").lower()
                if prev and not skip and "=" in prev and "=" in b["result"] and not re.search(r"[<>≤≥]", prev):
                    eqv = equivalent(prev, b["result"])
                    if eqv is False: errs.append(f"{Q}: MATH ERROR: '{b['result']}' is not equivalent to '{prev}'")
                    elif eqv is None: warns.append(f"{Q}: could not verify '{prev}' -> '{b['result']}'")
                if prev and not skip and "=" not in prev and "=" not in b["result"] and not re.search(r"[<>≤≥≠]", prev + b["result"]):
                    eqv = equivalent_expr(prev, b["result"])
                    if eqv is False: errs.append(f"{Q}: MATH ERROR: '{b['result']}' is not equivalent to '{prev}'")
                    elif eqv is None: warns.append(f"{Q}: could not verify '{prev}' -> '{b['result']}'")
                prev = b["result"]
            if sc["type"] == "passage":
                for fld in ("highlight", "underline"):
                    if b.get(fld) and b[fld] not in sc.get("text", ""): errs.append(f"{Q}: {fld} text is not in the passage")
            if sc["type"] == "desmos" and not b.get("actions"): errs.append(f"{Q}: desmos beat has no actions")
            if sc["type"] == "choices":
                for fld in ("eliminate", "pick", "point"):
                    if b.get(fld) and b[fld] not in sc.get("options", {}): errs.append(f"{Q}: {fld} '{b[fld]}' is not an option")
    warns.append(f"total narration: {total} words (about {total / 150:.1f} minutes)")
    return errs, warns

# ---------------------------------------------------------------- audio + plan
async def _tts(items):
    import edge_tts
    for text, path in items:
        if not os.path.exists(path): await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)

def tts_speak(text, path):
    """Windows: VoiceBox (Teacher profile). Linux, or OPENPREP_TTS=kokoro: the Kokoro package directly (same voice, af_heart)."""
    if os.environ.get("OPENPREP_TTS") == "chatterbox":
        import chatterbox_wrap; chatterbox_wrap.speak(text, path)
    elif os.environ.get("OPENPREP_TTS") == "kokoro" or sys.platform != "win32":
        import kokoro_tts; kokoro_tts.speak(text, path)
    else:
        import vb_tts; vb_tts.speak(text, path)

def build_plan(js):
    from moviepy.editor import AudioFileClip
    paths = []
    for sc in js["scenes"]:
        for b in sc["beats"]:
            p = os.path.join(CACHE, "vb_" + hashlib.sha1((b["say"] + "teacher-af_heart" + os.environ.get("OPENPREP_TTS", "")).encode()).hexdigest()[:16] + ".wav")
            if not os.path.exists(p): tts_speak(b["say"], p)
            paths.append(p)
    durs = [AudioFileClip(p).duration for p in paths]; plan = []; t0 = .7; k = 0
    for sc in js["scenes"]:
        bt, bd, acc = [], [], 0.0
        for b in sc["beats"]: dd = durs[k] + .6; bt.append(acc); bd.append(dd); acc += dd; k += 1
        plan.append({"sc": sc, "bt": bt, "bd": bd, "t0": t0, "len": acc + .5, "paths": paths[k - len(bt):k]}); t0 += acc + .5
    return plan, t0

DARK_TYPES = {"cards", "list"}
KIND_LABEL = {"cards": "CONCEPT", "list": "KEY IDEAS", "table": "AT A GLANCE", "figure": "DIAGRAM", "desmos": "IN DESMOS", "passage": "READ THE TEXT", "choices": "QUESTION", "steps": "WORKED SOLUTION", "check": "CHECK", "compare": "COMMON MISTAKE"}
def scene_tag(sc):
    t = sc.get("title", "").lower()
    m = re.match(r"(easy|medium|hard)\b", t)
    if m: return m.group(1).upper(), {"easy": 1, "medium": 2, "hard": 3}[m.group(1)]
    m = re.match(r"trap (\d+)", t)
    if m: return "TRAP " + m.group(1), 0
    if t.startswith("practice"): return "PRACTICE", 0
    if "recap" in t: return "RECAP", 0
    return KIND_LABEL.get(sc["type"], ""), 0

_grid = None
def bg_grid():
    global _grid
    if _grid is None:
        im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
        for x in range(24, W, 32):
            for y in range(24, H, 32): d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(226, 226, 226))
        _grid = im
    return _grid.copy()

def draw_header(c, sc, lt):
    label, lvl = scene_tag(sc); a = min(1, lt / .4 + .001); d = c.d
    if label:
        f = F(20); w = tw(label, f) + 40 + (58 if lvl else 0); x0 = 640 - w / 2
        d.rounded_rectangle([x0, 16, x0 + w, 52], 18, fill=mix(INK, a)); d.text((x0 + 20, 21), label, font=f, fill=BG)
        if lvl:
            for k in range(3): d.rounded_rectangle([x0 + 20 + tw(label, f) + 12 + k * 14, 28 + (2 - k) * 2, x0 + 20 + tw(label, f) + 22 + k * 14, 44], 2, fill=BG if k < lvl else G1)
    c.text(640, 60, sc.get("title", ""), fitF(sc.get("title", ""), 42, 1100), INK, a)
    ww = 90 + 150 * ease(lt / .7); d.line([(640 - ww / 2, 119), (640 + ww / 2, 119)], fill=INK, width=4)

def draw_caption(c, sc):
    b = c.cur(); say = sc["beats"][b]["say"]; dur = max(1.0, c.bd[b] - .6); tt = c.since(b) / dur
    sents = re.split(r"(?<=[.?!])\s+", say.strip()); lens = [max(1, len(s)) for s in sents]; tot = sum(lens); acc = 0; cur = len(sents) - 1
    for k, l in enumerate(lens):
        if tt < (acc + l) / tot: cur = k; break
        acc += l
    frac = min(1, max(0, (tt - acc / tot) / (lens[cur] / tot))); words = sents[cur].split()
    for fs in (30, 27, 24):
        f = F(fs, False); lines, curl = [], ""
        for w in words:
            t2 = (curl + " " + w).strip()
            if tw(t2, f) <= 1040: curl = t2
            else: lines.append(curl); curl = w
        lines.append(curl)
        if len(lines) <= 2 or fs == 24: break
    lh = f.size * 1.35; hgt = len(lines) * lh + 26; y0 = 590 + (86 - hgt) / 2
    c.d.rounded_rectangle([110, y0, 1170, y0 + hgt], 22, fill=PAN)
    spoken = int(frac * len(words) * 1.12) + 1; n = 0; y = y0 + 13
    for ln in lines:
        x = 640 - tw(ln, f) / 2
        for w in ln.split(" "):
            c.d.text((x, y), w, font=f, fill=INK if n < spoken else G2); x += tw(w + " ", f); n += 1
        y += lh

def frame(t, plan, total, label):
    s = next((p for p in plan if p["t0"] <= t < p["t0"] + p["len"]), plan[-1]); lt = t - s["t0"]; sc = s["sc"]
    im = bg_grid(); c = Ctx(im, lt, s["bt"], s["bd"]); d = c.d
    draw_header(c, sc, lt)
    RENDER[sc["type"]](c, sc)
    if sc["type"] != "desmos": draw_caption(c, sc)
    c.text(640, 686, f"OpenPrep  ·  {label}", F(17, False), G2)
    x = 40; gap = 4; usable = W - 80
    for p in plan:
        w = usable * p["len"] / total - gap; fillw = max(0, min(1, (t - p["t0"]) / p["len"])) * w
        d.rounded_rectangle([x, 708, x + w, 714], 3, fill=(220, 220, 220));
        if fillw > 1: d.rounded_rectangle([x, 708, x + fillw, 714], 3, fill=INK)
        x += w + gap
    if sc["type"] in DARK_TYPES: im = ImageOps.invert(im)
    return np.array(im)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; path = args[0]; js = json.load(open(path, encoding="utf-8")); errs, warns = validate(js)
    for w in warns: print("note:", w)
    for e in errs: print("ERROR:", e)
    if errs: print(f"{len(errs)} error(s). Fix these and resend the full JSON."); sys.exit(1)
    if "--check" in sys.argv: print("OK"); return
    from moviepy.editor import VideoClip, AudioFileClip, CompositeAudioClip
    for sc in js["scenes"]:
        if sc["type"] == "desmos": sc["_frames"] = desmos_frames(sc)
    plan, total = build_plan(js); auds = []
    for p in plan:
        for t, f in zip(p["bt"], p["paths"]): auds.append(AudioFileClip(f).set_start(p["t0"] + t + .1))
    clip = VideoClip(lambda t: frame(min(t, total - .01), plan, total, js["section_label"]), duration=total).set_fps(FPS).set_audio(CompositeAudioClip(auds))
    out = os.path.join(OUT, js["id"] + ".mp4"); clip.write_videofile(out, fps=FPS, codec="libx264", audio_codec="aac", preset="veryfast", logger=None); print("done", out, round(total, 1), "s")

if __name__ == "__main__":
    main()
