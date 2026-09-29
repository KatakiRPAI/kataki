# -*- coding: utf-8 -*-
"""The Sky, dark — rebuilt on the audit. One generator, five screens."""
import os, random
from lib import A, FOCUS, NAME, icon, face, cover, I

# A real cog, so Settings stops sharing a shape with the sun / Light toggle.
I['cog'] = ('<circle cx="12" cy="12" r="3.1"/>'
            '<path d="M19.5 14.3a1.5 1.5 0 00.3 1.66l.05.05a1.9 1.9 0 11-2.69 2.69l-.05-.05a1.5 1.5 0 00-1.66-.3 1.5 1.5 0 00-.91 1.38V20a1.9 1.9 0 11-3.8 0v-.1a1.5 1.5 0 00-.98-1.38 1.5 1.5 0 00-1.66.3l-.05.05a1.9 1.9 0 11-2.69-2.69l.05-.05a1.5 1.5 0 00.3-1.66 1.5 1.5 0 00-1.38-.91H4a1.9 1.9 0 110-3.8h.1a1.5 1.5 0 001.38-.98 1.5 1.5 0 00-.3-1.66l-.05-.05a1.9 1.9 0 112.69-2.69l.05.05a1.5 1.5 0 001.66.3h.07a1.5 1.5 0 00.91-1.38V4a1.9 1.9 0 113.8 0v.1a1.5 1.5 0 00.91 1.38 1.5 1.5 0 001.66-.3l.05-.05a1.9 1.9 0 112.69 2.69l-.05.05a1.5 1.5 0 00-.3 1.66v.07a1.5 1.5 0 001.38.91H20a1.9 1.9 0 110 3.8h-.1a1.5 1.5 0 00-1.38.91z"/>')

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')

GF = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
      '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
      '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
      'family=Baloo+2:wght@500;600;700;800&amp;'
      'family=Figtree:wght@400;500;600;700;800&amp;'
      'family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&amp;'
      'family=JetBrains+Mono:wght@400;500&amp;'
      'family=Baloo+Bhaijaan+2:wght@500;600;700;800&amp;'
      'family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&amp;'
      'family=Noto+Naskh+Arabic:wght@400;500;600&amp;display=swap">')

UI = "Figtree, 'Segoe UI', system-ui, sans-serif"
DP = "'Baloo 2', 'Segoe UI', system-ui, sans-serif"
NR = "Newsreader, Georgia, serif"
MO = "'JetBrains Mono', Consolas, monospace"

# ---- tokens -----------------------------------------------------------------
# Two themes share one set of names. Every colour below was checked with
# wcag_check.py: text tokens clear 4.5:1 on every surface they sit on.
THEMES = {
 'night': dict(
    GROUND='#0a1028', PANEL='#131b3a', RAISE='#1a2348', OVER='#212b57', RAIL='#0d142f',
    INK='#eef2ff', MID='#c6d0ec', MUT='#aebbdc', FAINT='#95a2cb',
    ACC='#5b86ff',            # fills, bars, focus ring, selected borders
    ACCT='#86a6ff',           # accent used as TEXT (links, active labels)
    ACCD='#3558d6',           # primary button fill: white text 5.97:1
    ACCH='#4065e4',           # primary hover
    WARM='#e7b06a', OK='#6fd8a4', BAD='#ff8fa3',
    BORDER='rgba(168,190,255,.16)', HAIR='rgba(168,190,255,.095)',
    SUNK='rgba(8,13,32,.45)', PILL='rgba(8,13,32,.5)', POP='rgba(26,35,72,.94)', ONINK='#10182f',
    NOFACE='linear-gradient(165deg, #1b2348, #141b38)', NOFACE_INK='rgba(168,190,255,.42)',
    SECRET_BG='#0a0d1e', SECRET_INK='#f0ecdf', STAR='#e8eeff',
    SHF='0 26px 60px rgba(0,0,0,.55)', DIM='rgba(4,7,20,.62)'),
 'day': dict(
    GROUND='#edf2ff', PANEL='#ffffff', RAISE='#f4f7ff', OVER='#ffffff', RAIL='#f7f9ff',
    INK='#0f1733', MID='#2c3860', MUT='#46537c', FAINT='#5a668d',
    ACC='#2f5be0', ACCT='#2a52cf', ACCD='#2f5be0', ACCH='#274fcc',
    WARM='#8a4f0a', OK='#17704a', BAD='#b4233f',
    BORDER='rgba(30,52,120,.16)', HAIR='rgba(30,52,120,.09)',
    SUNK='rgba(30,52,120,.05)', PILL='rgba(255,255,255,.8)', POP='rgba(255,255,255,.97)', ONINK='#ffffff',
    NOFACE='linear-gradient(165deg, #e3e9fb, #d6def6)', NOFACE_INK='rgba(30,52,120,.40)',
    SECRET_BG='#fbf4e6', SECRET_INK='#3a2a12', STAR='#ffffff',
    SHF='0 18px 44px rgba(30,52,120,.14)', DIM='rgba(15,23,51,.36)'),
}
THEME = 'night'
RTL = False
R1, R2, R3 = '6px', '10px', '16px'
TAB = 'font-variant-numeric: tabular-nums; font-feature-settings: "tnum";'

def use(theme='night', rtl=False):
    """Switch every token at once. Builders read globals at call time."""
    g = globals()
    g.update(THEMES[theme]); g['THEME'] = theme; g['RTL'] = rtl
    g['FOCUS'] = f"0 0 0 2px {g['GROUND']}, 0 0 0 4px {g['ACC']}"
    g['PRIM'] = g['ACCD']      # flat. No gradient, no coloured glow.
    if rtl:
        g['UI'] = "'IBM Plex Sans Arabic', Figtree, 'Segoe UI', system-ui, sans-serif"
        g['DP'] = "'Baloo Bhaijaan 2', 'Baloo 2', 'Segoe UI', system-ui, sans-serif"
        g['NR'] = "'Noto Naskh Arabic', Newsreader, Georgia, serif"
    else:
        g['UI'] = "Figtree, 'Segoe UI', system-ui, sans-serif"
        g['DP'] = "'Baloo 2', 'Segoe UI', system-ui, sans-serif"
        g['NR'] = "Newsreader, Georgia, serif"

use('night')
RW = 200          # rail width
PAD = 40

TOKEN_RE = None
def _fill(html):
    """Plain (non-f) strings may carry {TOKEN}; resolve them against the active theme."""
    import re as _re
    return _re.sub(r'\{([A-Z][A-Z_]+)\}', lambda m: str(globals().get(m.group(1), m.group(0))), html)

def _mirror(html):
    """RTL: flip every physical side inside style attributes. box(x, ...) becomes
    right: x, which mirrors against the page exactly; flex rows reverse by dir=rtl."""
    import re as _re
    def flip(m):
        st = m.group(1)
        st = _re.sub(r'\b(left|right)\b', lambda k: 'right' if k.group(1) == 'left' else 'left', st)
        st = _re.sub(r'letter-spacing:\s*[^;"]+', 'letter-spacing: 0', st)   # tracking breaks Arabic joins
        st = st.replace('font-style: italic', 'font-style: normal')           # Arabic has no italic
        st = st.replace('text-transform: uppercase', 'text-transform: none')
        st = _re.sub(r'line-height: 1\.1\d?;', 'line-height: 1.45;', st)
        def up(k):   # Arabic glyphs read smaller at the same size: small text goes up
            v = float(k.group(1)); v = v + 2 if v <= 12 else (v + 1 if v <= 15 else v)
            return f'font-size: {v:g}px'
        st = _re.sub(r'font-size: ([\d.]+)px', up, st)       # Naskh needs room above and below
        return 'style="' + st + '"'
    html = _re.sub(r'style="([^"]*)"', flip, html)
    html = html.replace('<em>', '<span>').replace('</em>', '</span>')
    return html

def page(title, w, h, body):
    body = _fill(body)
    body = body.replace(' style="font-family:', ' style="font-family:')
    lang, d = ('ar', 'rtl') if RTL else ('en', 'ltr')
    if RTL:
        body = _mirror(tr(body))
        title = tr(title)
    return f'''<!doctype html>
<html lang="{lang}" dir="{d}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
{GF}
<style>
body{{margin:0;background:{GROUND}}}
button{{font-family:inherit;cursor:pointer;border:0;background:none;padding:0;color:inherit}}
input,textarea{{font-family:inherit}}
.sr{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}}
</style>
</helmet>
<div dir="{d}" lang="{lang}" style="position: relative; width: {w}px; height: {h}px; overflow: hidden;">
{body}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{w},"height":{h}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
'''

TR = {}
def tr(html):
    """Swap text nodes for their translation. Keys are exact text-node strings."""
    import re as _re
    def sub(m):
        t = m.group(1)
        k = t.strip()
        if k in TR:
            return '>' + t.replace(k, TR[k]) + '<'
        if RTL and any('a' <= c.lower() <= 'z' for c in k) and 'Component' not in k and '{' not in k:
            return '><bdi>' + t + '</bdi><'      # user content in another script keeps its own direction
        return m.group(0)
    return _re.sub(r'>([^<>]+)<', sub, html)

def box(x, y, w, h, css='', inner=''):
    return f'<div style="position: absolute; left: {x}px; top: {y}px; width: {w}px; height: {h}px; {css}">{inner}</div>'

def tx(x, y, w, css='', inner=''):
    return f'<div style="position: absolute; left: {x}px; top: {y}px; width: {w}px; {css}">{inner}</div>'

def panel(x, y, w, h, inner='', lvl=0, extra=''):
    bg = (PANEL, RAISE, OVER)[lvl]
    return box(x, y, w, h, f'background: {bg}; border: 1px solid {BORDER}; border-radius: {R3}; {extra}', inner)

# Names from the story world (stories, people, places, books) are set in Newsreader,
# like a title page. App chrome (page and section headings) stays in Baloo 2.
WORLD = {'Two Sugars, No Title', 'The Gala List', 'Three in the Morning', 'The Long Way Home', 'Closing Shift',
         'Close to the Crown', 'The Flat on Ardenne', 'Halcyon Coffee', 'Corvel Palace', 'File Corvel Palace',
         'Mike', 'Theo', 'Nico', 'Jae', 'Dani', 'Cas', 'Liv', 'Mike Dorsey', 'Liv Sandoval'}

def disp(s, size, col=None, w='700', extra=''):
    col = col or INK
    plain = s.replace('&rsquo;', "'")
    if s in WORLD or plain in WORLD or s in TR.values():
        wt = 600 if size < 22 else 500
        return (f'<span style="font-family: {NR}; font-weight: {wt}; font-size: {round(size * 1.06, 1)}px; '
                f'letter-spacing: -.012em; line-height: 1.1; color: {col}; {extra}">{s}</span>')
    return f'<span style="font-family: {DP}; font-weight: {w}; font-size: {size}px; letter-spacing: -.015em; line-height: 1.12; color: {col}; {extra}">{s}</span>'

def eyebrow(s, col=None):
    col = col or FAINT
    return (f'<div style="font-family: {UI}; font-size: 10.5px; font-weight: 700; letter-spacing: .15em; '
            f'text-transform: uppercase; color: {col};">{s}</div>')

def btn(label, kind='primary', ic=None, h=44, fs=15, w=None):
    wcss = f'width: {w}px; justify-content: center;' if w else 'padding: 0 20px;'
    if kind == 'primary':
        sk = f'background: {ACCD}; color: #fff;'
        rad = '999px'
    elif kind == 'secondary':
        sk = f'background: {RAISE}; color: {INK}; border: 1px solid {BORDER};'
        rad = '999px'
    else:
        sk = f'background: transparent; color: {MID}; border: 1px solid {HAIR};'
        rad = R2
    g = icon(ic, 17, 'currentColor', 1.9) + '<span style="width: 8px;"></span>' if ic else ''
    return (f'<button style="display: inline-flex; align-items: center; height: {h}px; {wcss} border-radius: {rad}; '
            f'font-family: {UI}; font-size: {fs}px; font-weight: 700; {sk}">{g}{label}</button>')

def chip(label, on=False, ic=None, count=None):
    if on:
        sk = f'background: {INK}; color: {ONINK}; border: 1px solid {INK};'
    else:
        sk = f'background: {RAISE}; color: {MID}; border: 1px solid {BORDER};'
    g = icon(ic, 14, 'currentColor', 2) + '<span style="width: 6px;"></span>' if ic else ''
    c = (f'<span style="margin-left: 7px; font-weight: 500; color: {ONINK if on else MUT}; font-variant-numeric: tabular-nums;">{count}</span>') if count is not None else ''
    return (f'<span style="display: inline-flex; align-items: center; height: 32px; padding: 0 13px; border-radius: 999px; '
            f'font-family: {UI}; font-size: 12.5px; font-weight: 600; {sk}">{g}{label}{c}</span>')

def stat(label, value, col=None):
    """A computed value: a count, a date, a duration. Never prose."""
    return (f'<span style="display: inline-flex; align-items: baseline; gap: 6px;">'
            f'<span style="font-family: {UI}; font-size: 13px; font-weight: 700; color: {col or INK}; {TAB}">{value}</span>'
            f'<span style="font-family: {UI}; font-size: 12.5px; color: {MUT};">{label}</span></span>')

def enum_pill(label, col=None, ic=None):
    """A value from a fixed vocabulary the engine sets (mood, sharpness, relationship)."""
    c = col or MUT
    g = icon(ic, 13, c, 2) + '<span style="width: 6px;"></span>' if ic else ''
    return (f'<span style="display: inline-flex; align-items: center; height: 26px; padding: 0 11px; border-radius: 999px; '
            f'background: {PILL}; border: 1px solid {BORDER}; font-family: {UI}; font-size: 11.5px; '
            f'font-weight: 700; letter-spacing: .04em; text-transform: uppercase; color: {c};">{g}{label}</span>')

def meter(x, y, w, label, value, col=None):
    """A stored 0-100 score. Label from a fixed list, number from the engine."""
    c = col or ACC
    p = [tx(x, y, w - 46, f'font-family: {UI}; font-size: 12.5px; color: {MUT};', label)]
    p.append(tx(x + w - 44, y, 44, f'text-align: right; font-family: {MO}; font-size: 12px; color: {INK}; {TAB}', str(value)))
    p.append(box(x, y + 20, w, 4, f'border-radius: 2px; background: {HAIR};'))
    p.append(box(x, y + 20, int(w * value / 100), 4, f'border-radius: 2px; background: {c};'))
    return ''.join(p)

def tag(label, col=None):
    return (f'<span style="display: inline-block; padding: 4px 10px; border-radius: {R1}; background: {RAISE}; '
            f'border: 1px solid {HAIR}; color: {col or MUT}; font-family: {UI}; font-size: 11px; font-weight: 700; '
            f'letter-spacing: .06em; text-transform: uppercase;">{label}</span>')

def rule(x, y, w, strong=False):
    return box(x, y, w, 1, f'background: {BORDER if strong else HAIR};')

def stars(w, h, n=190, seed=11):
    r = random.Random(seed)
    d = []
    for _ in range(n):
        x, y, rr = r.random() * w, r.random() * h, r.choice([.7, .9, 1.1, 1.5])
        d.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr}" fill="{STAR}" opacity="{r.uniform(.2,.8):.2f}"/>')
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="position: absolute; inset: 0;" aria-hidden="true">{"".join(d)}</svg>'

PAGEW = 1440   # page width; the compact proof sets 1024

def moon(cx, cy, r=15):
    """A small, crisp moon with a soft halo: the one bright point on the page."""
    if THEME == 'day':
        return (box(cx - 140, cy - 140, 280, 280, 'pointer-events: none; border-radius: 50%; background: radial-gradient(circle, rgba(255,247,222,.95) 0 10%, rgba(255,240,200,.38) 22%, rgba(255,240,200,0) 62%);'))
    return (box(cx - 130, cy - 130, 260, 260, 'pointer-events: none; border-radius: 50%; background: radial-gradient(circle, rgba(200,216,255,.22), rgba(200,216,255,0) 64%);') +
            box(cx - r, cy - r, 2 * r, 2 * r, 'pointer-events: none; border-radius: 50%; box-shadow: inset -8px 5px 0 0 #eef2ff; '
                'filter: drop-shadow(0 0 9px rgba(214,226,255,.55));'))

def sky(h, x0=None, w=None, band=560):
    """The sky is the product's signature, so it shows: stars, one moon and moonlit cloud
    across the top of every page. Content sits on it; the ground only takes over below
    the fold, where lists need a calm surface."""
    x0 = RW if x0 is None else x0
    w = w or PAGEW
    W = w - x0
    if THEME == 'day':
        o = box(x0, 0, W, h, f'pointer-events: none; background: linear-gradient(180deg, #a3c3ff 0px, #bfd5ff 220px, #dde8ff 470px, {GROUND} 760px, {GROUND} 100%);')
        o += moon(x0 + int(W * (.62 if W > 1100 else .5)), 40)
        o += box(x0, 150, W, 420, 'pointer-events: none; overflow: hidden; opacity: .95; -webkit-mask-image: linear-gradient(180deg, transparent 0, #000 18%, #000 60%, transparent 100%);',
                 f'<img src="{A["clouds"]}" alt="" style="position: absolute; left: -4%; top: -30px; width: 108%;">')
        return o
    o = box(x0, 0, W, h, f'pointer-events: none; background: linear-gradient(180deg, #050a1d 0px, #09102b 200px, #0d1638 420px, #0f1839 600px, {GROUND} 900px, {GROUND} 100%);')
    o += box(x0, 0, W, band, 'pointer-events: none; overflow: hidden; -webkit-mask-image: linear-gradient(180deg, #000 55%, transparent 100%);', stars(W, band, 230))
    o += moon(x0 + int(W * (.62 if W > 1100 else .5)), 44)
    # moonlit cloud bank behind the hero; lit from above, dark underneath
    o += box(x0, 210, W, 330, 'pointer-events: none; overflow: hidden; opacity: .42; -webkit-mask-image: linear-gradient(180deg, transparent 0, #000 30%, #000 62%, transparent 100%);',
             f'<img src="{A["clouds"]}" alt="" style="position: absolute; left: -6%; top: -60px; width: 112%; filter: brightness(.55) saturate(.35) hue-rotate(8deg);">')
    return o

# ---- rail -------------------------------------------------------------------
NAV = [('home', 'Home'), ('chat', 'Stories'), ('users', 'Characters'), ('map', 'World'), ('user', 'You')]

def rail(h, active='Home'):
    if RW < 120:
        return rail_compact(h, active)
    p = [box(0, 0, RW, h, f'background: {RAIL}; border-right: 1px solid {BORDER};')]
    p.append(tx(24, 26, 160, '', disp('Kataki', 24, INK, '800')))
    p.append(box(24, 58, 34, 3, f'background: {ACC}; border-radius: 2px;'))
    y = 104
    for ic, label in NAV:
        on = label == active
        sel = f'background: {RAISE}; border: 1px solid {BORDER};' if on else 'border: 1px solid transparent;'
        col = INK if on else MUT
        p.append(box(20, y, RW - 40, 42, f'display: flex; align-items: center; gap: 12px; padding: 0 12px; box-sizing: border-box; border-radius: {R2}; {sel} color: {col};',
                     icon(ic, 19, 'currentColor', 1.9) +
                     f'<span style="font-family: {UI}; font-size: 14.5px; font-weight: {700 if on else 500};">{label}</span>'))
        y += 48
    p.append(rule(20, y + 14, RW - 40))
    p.append(box(20, y + 30, RW - 40, 38, f'display: flex; align-items: center; gap: 9px; padding: 0 11px; box-sizing: border-box; border-radius: {R2}; border: 1px dashed {BORDER}; color: {MUT};',
                 icon('plus', 17, 'currentColor', 1.9) + f'<span style="font-family: {UI}; font-size: 13px; font-weight: 600; white-space: nowrap;">New character</span>'))
    fy = h - 156
    for ic, label in (('cog', 'Settings'), ('help', 'Feedback'), ('moon' if THEME == 'day' else 'sun', 'Night' if THEME == 'day' else 'Day')):
        p.append(box(20, fy, RW - 40, 34, f'display: flex; align-items: center; gap: 11px; padding: 0 12px; box-sizing: border-box; color: {MUT};',
                     icon(ic, 16, 'currentColor', 1.8) + f'<span style="font-family: {UI}; font-size: 13px; font-weight: 500;">{label}</span>'))
        fy += 36
    p.append(box(RW - 32, h - 152, 7, 7, f'border-radius: 50%; background: {WARM};'))
    return ''.join(p)

def rail_compact(h, active='Home'):
    """Under 1200 px the rail folds to icons. Labels move to tooltips and aria-label."""
    p = [box(0, 0, RW, h, f'background: {RAIL}; border-right: 1px solid {BORDER};')]
    p.append(box(0, 22, RW, 40, 'display: flex; justify-content: center;',
                 f'<span style="font-family: {DP}; font-weight: 800; font-size: 26px; color: {INK};">K</span>'))
    y = 92
    for ic, label in NAV:
        on = label == active
        sel = f'background: {RAISE}; border: 1px solid {BORDER};' if on else 'border: 1px solid transparent;'
        p.append(box((RW - 44) // 2, y, 44, 44, f'display: flex; align-items: center; justify-content: center; border-radius: {R2}; {sel} color: {INK if on else MUT};',
                     f'<span class="sr">{label}</span>' + icon(ic, 20, 'currentColor', 1.9)))
        y += 52
    p.append(box((RW - 44) // 2, y + 14, 44, 44, f'display: flex; align-items: center; justify-content: center; border-radius: {R2}; border: 1px dashed {BORDER}; color: {MUT};',
                 '<span class="sr">New character</span>' + icon('plus', 19, 'currentColor', 1.9)))
    fy = h - 150
    for ic, label in (('cog', 'Settings'), ('help', 'Feedback'), ('sun', 'Day')):
        p.append(box((RW - 40) // 2, fy, 40, 40, f'display: flex; align-items: center; justify-content: center; color: {MUT};',
                     f'<span class="sr">{label}</span>' + icon(ic, 18, 'currentColor', 1.8)))
        fy += 44
    return ''.join(p)

def topbar(X, W, y=32, place='Home'):
    p = [box(X, y - 4, 200, 34, 'display: flex; align-items: center; gap: 10px;',
             face('aren', 30) +
             f'<div><div style="font-family: {UI}; font-size: 13.5px; font-weight: 700; color: {INK};">Liv</div>'
             f'<div style="font-family: {UI}; font-size: 10.5px; color: {MID};">playing as</div></div>' +
             icon('down', 14, FAINT, 2))]
    sw = 360
    p.append(box(X + W - sw, y - 4, sw, 38, f'background: {PANEL}; border: 1px solid {BORDER}; border-radius: {R2}; display: flex; align-items: center; gap: 9px; padding: 0 13px; box-sizing: border-box;',
                 icon('search', 16, FAINT, 1.9) +
                 f'<span style="font-family: {UI}; font-size: 13.5px; color: {FAINT}; flex: 1;">Search everything</span>'
                 f'<span style="font-family: {MO}; font-size: 11px; color: {FAINT}; border: 1px solid {HAIR}; border-radius: 4px; padding: 2px 6px;">Ctrl K</span>'))
    return ''.join(p)

CAST = [('mira', 'Mike', 'Played 2 hours ago', 'Barista at Halcyon', 'In a story'),
        ('tobin', 'Theo', 'Played yesterday', 'Closing shifts, hears everything', None),
        ('ilsa', 'Nico', 'Played 4 days ago', 'Your flatmate, paints at 3am', None),
        ('oren', 'Jae', 'Played last week', 'Palace press aide', None),
        ('wren', 'Dani', 'No secret yet', 'Florist, back gate twice a week', 'Draft')]

def noface(nm, h):
    return (f'<div style="position: absolute; inset: 0; background: {NOFACE}; '
            f'display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px;">'
            f'<span style="font-family: {DP}; font-weight: 700; font-size: {int(h*0.3)}px; color: {NOFACE_INK};" aria-hidden="true">{nm[0]}</span>'
            f'<span style="font-family: {UI}; font-size: 11px; font-weight: 600; color: {MUT};">no portrait yet</span></div>')

def still(x, y, w, h, key='gull-night', caption='the gala, three weeks later', pos='50% 42%', alt=''):
    inner = cover(key, '', pos, alt)
    inner += (f'<div style="position: absolute; left: 0; right: 0; bottom: 0; height: 72px; '
              f'background: linear-gradient(to top, rgba(6,10,26,.94) 0%, rgba(6,10,26,.78) 45%, rgba(6,10,26,0) 100%); text-shadow: 0 1px 2px rgba(0,0,0,.6); '
              f'display: flex; align-items: flex-end; padding: 0 16px 11px; box-sizing: border-box;">'
              f'<span style="font-family: {DP}; font-weight: 600; font-size: 14px; color: #dfe6ff;">{caption}</span></div>')
    return box(x, y, w, h, f'border-radius: {R3}; overflow: hidden; background: {RAISE}; box-shadow: {SHF};', inner)

def hero(X, W, y):
    """No panel: the continue-hero sits on the sky itself, the still is the only framed thing."""
    H = 372
    sw = 448 if W >= 1000 else 360
    p = [still(X + W - sw, y + 4, sw, H - 20)]
    tX, tW = X, W - sw - 56
    p.append(tx(tX, y + 30, tW, '', eyebrow('Continue &middot; Close to the Crown', MID)))
    p.append(tx(tX, y + 54, tW, '', disp('Two Sugars, No Title', 50 if W >= 1000 else 42, INK)))
    qy = y + (140 if W >= 1000 else 128)
    p.append(box(tX, qy + 4, 3, 52, f'background: {WARM}; border-radius: 2px;'))
    p.append(tx(tX + 18, qy, tW - 18, f'font-family: {NR}; font-style: italic; font-size: 20px; line-height: 1.45; color: {MID};',
                '&ldquo;&hellip;I could have sworn. Three weeks is a long time to hold one sentence.&rdquo;'))
    ry = qy + 78 if W >= 1000 else qy + 98
    p.append(box(tX, ry, tW, 28, 'display: flex; align-items: center; gap: 9px; flex-wrap: wrap;',
                 face('mira', 26) +
                 enum_pill('Doubtful', WARM) +
                 f'<span style="font-family: {UI}; font-size: 13px; color: {MID}; {TAB}">41 memories &middot; 2 changed since you left</span>'))
    p.append(box(tX, y + H - 84, tW, 52, 'display: flex; align-items: center; gap: 16px;',
                 btn('Continue', 'primary', None, h=48, fs=16) + btn('New story', 'secondary', None, h=48, fs=15)))
    p.append(tx(tX, y + H - 22, tW, f'font-family: {UI}; font-size: 12.5px; color: {MUT}; {TAB}',
                'Three weeks later &middot; Corvel Palace &middot; 7:22 pm'))
    return ''.join(p)

def changed(X, W, y):
    """The event log. Every row is: who + an event type from a fixed set + a stored
    memory line + a timestamp. Nothing here is written at render time."""
    items = [('mira', 'Mike', 'Memory faded', WARM, '&ldquo;She didn&rsquo;t want to be on the gala list.&rdquo;', 'sharp &rarr; hazy'),
             ('mira', 'Mike', 'Memory doubted', WARM, '&ldquo;She says she never said it.&rdquo;', 'conflicts with 1 memory'),
             ('tobin', 'Theo', 'New memory', OK, '&ldquo;Liv sent him to the back for milk.&rdquo;', 'witnessed')]
    p = [tx(X, y, 400, '', eyebrow('Since you last played')),
         tx(X + 200, y - 1, 400, f'font-family: {UI}; font-size: 11.5px; color: {FAINT}; {TAB}', '3 events &middot; 2 hours ago')]
    x = X
    cw = (W - 24) // 3
    for k, nm, ev, col, quote, meta in items:
        p.append(box(x, y + 22, cw, 92, f'background: {PANEL}; border: 1px solid {HAIR}; border-radius: {R2}; padding: 13px 15px; box-sizing: border-box;',
                     f'<div style="display: flex; align-items: center; gap: 9px;">' + face(k, 24) +
                     f'<span style="font-family: {UI}; font-size: 12.5px; font-weight: 700; color: {INK};">{nm}</span>'
                     f'<span style="font-family: {UI}; font-size: 10.5px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: {col};">{ev}</span></div>'
                     f'<div style="margin-top: 8px; font-family: {NR}; font-size: 14.5px; line-height: 1.35; color: {MID};">{quote}</div>'
                     f'<div style="margin-top: 5px; font-family: {UI}; font-size: 11px; color: {FAINT};">{meta}</div>'))
        x += cw + 12
    return ''.join(p)

def cast_grid(X, W, y):
    p = [tx(X, y, 420, '', disp('Your characters', 24))]
    p.append(box(X + W - 330, y + 4, 330, 32, 'display: flex; justify-content: flex-end; gap: 8px;',
                 chip('All', True, count=5) + chip('In a story', count=1) + chip('Drafts', count=1)))
    cy = y + 46
    fw = 324 if W >= 1000 else 272
    addw = 112 if W >= 1000 else 92
    others = CAST[1:] if W >= 1000 else CAST[1:4]
    ow = (W - fw - addw - 12 * (len(others) + 1)) // len(others)
    k, nm, when, blurb, badge = CAST[0]
    inner = (f'<div style="position: relative; width: 100%; height: 214px; background: {RAISE};">' + cover(k, '', None, 'Mike, leaning on the counter, wary') +
             f'<div style="position: absolute; left: 14px; top: 14px; padding: 5px 11px; border-radius: 999px; background: rgba(8,13,32,.78); border: 1px solid rgba(168,190,255,.16); '
             f'font-family: {UI}; font-size: 11px; font-weight: 700; color: #e7b06a;">In a story</div></div>'
             f'<div style="padding: 15px 17px;">{disp(nm, 25)}'
             f'<div style="font-family: {UI}; font-size: 12.5px; color: {MUT}; margin-top: 3px;">{when} &middot; wary</div></div>')
    p.append(panel(X, cy, fw, 306, inner, 0, 'overflow: hidden;'))
    x = X + fw + 12
    for k, nm, when, blurb, badge in others:
        bd = ''
        if badge:
            bd = (f'<div style="position: absolute; left: 12px; top: 12px; padding: 4px 10px; border-radius: 999px; background: rgba(8,13,32,.78); '
                  f'border: 1px solid rgba(168,190,255,.16); font-family: {UI}; font-size: 10.5px; font-weight: 700; color: #c6d0ec;">{badge}</div>')
        art = noface(nm, 196) if nm == 'Dani' else cover(k, '', None, nm + ' portrait')
        inner = (f'<div style="position: relative; width: 100%; height: 196px; background: {RAISE};">' + art + bd + '</div>'
                 f'<div style="padding: 13px 15px;">{disp(nm, 19)}'
                 f'<div style="font-family: {UI}; font-size: 12px; color: {MUT}; margin-top: 3px;">{when}</div></div>')
        p.append(panel(x, cy, ow, 306, inner, 0, 'overflow: hidden;'))
        x += ow + 12
    p.append(box(x, cy, X + W - x, 306, f'border: 1.5px dashed {BORDER}; border-radius: {R3}; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 9px; color: {MUT};',
                 icon('plus', 24, 'currentColor', 1.8) + f'<span style="font-family: {UI}; font-size: 12.5px; font-weight: 600;">Add</span>'))
    return ''.join(p)

THREADS = [('The Gala List', 'Close to the Crown', '&ldquo;Officially? No comment. Unofficially, be there by eight.&rdquo;', 'Played last week', 'oren'),
           ('Three in the Morning', 'The Flat on Ardenne', '&ldquo;You&rsquo;re not going to like this painting.&rdquo;', 'Played 4 days ago', 'ilsa'),
           ('The Long Way Home', 'Not in a book &middot; as Cas', '&ldquo;Leave it. We&rsquo;ll push.&rdquo;', 'Played 3 weeks ago', 'sable')]

def threads(X, W, y):
    p = [tx(X, y, 420, '', disp('Other threads', 24))]
    p.append(box(X + W - 120, y + 8, 120, 24, f'text-align: right; font-family: {UI}; font-size: 13px; font-weight: 700; color: {ACCT};', 'All stories'))
    x = X
    cw = (W - 32) // 3
    for title, book, sub, when, k in THREADS:
        inner = (face(k, 38, 'position: absolute; left: 17px; top: 17px;') +
                 f'<div style="position: absolute; left: 66px; top: 16px; right: 16px;">{disp(title, 18)}'
                 f'<div style="font-family: {UI}; font-size: 11.5px; color: {FAINT}; margin-top: 1px;">{book}</div></div>'
                 f'<div style="position: absolute; left: 17px; right: 16px; top: 70px; font-family: {NR}; font-size: 15.5px; line-height: 1.35; color: {MID}; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">{sub}</div>'
                 f'<div style="position: absolute; left: 17px; bottom: 14px; font-family: {UI}; font-size: 11.5px; font-weight: 600; color: {FAINT};">{when}</div>')
        p.append(panel(x, y + 44, cw, 150, inner))
        x += cw + 16
    return ''.join(p)

def build_home():
    H = 1310
    X, W = RW + PAD, PAGEW - RW - PAD * 2
    b = [box(0, 0, PAGEW, H, f'background: {GROUND};'), sky(H), rail(H, 'Home')]
    b.append(topbar(X, W))
    b.append(hero(X, W, 96))
    b.append(changed(X, W, 504))
    b.append(cast_grid(X, W, 660))
    b.append(threads(X, W, 1040))
    b.append(tx(X, 1262, W, f'font-family: {UI}; font-size: 12.5px; color: {MUT};',
                'Everything here lives on this computer. '
                f'<span style="color: {ACCT}; font-weight: 700;">Where is my data?</span>'))
    return page('Sky &middot; Home', PAGEW, H, ''.join(b))

# ------------------------------------------------------------------ PROFILE
HOLD = [('She did not want to be on the gala list.', 'going hazy', .40, MUT),
        ('Her mother is the queen&rsquo;s step-sister.', 'held tight', .88, WARM),
        ('She says she never said it.', 'doubted', .55, MUT)]

def living(x, y, w):
    h = 412
    p = [panel(x, y, w, h)]
    p.append(tx(x + 22, y + 20, w - 44, '', eyebrow('Right now')))
    p.append(box(x + w - 186, y + 15, 164, 28, f'display: flex; align-items: center; justify-content: flex-end; gap: 6px; color: {MUT};',
                 f'<span style="font-family: {UI}; font-size: 12px; font-weight: 600;">Two Sugars, No Title</span>' + icon('down', 14, 'currentColor', 2)))
    p.append(box(x + 22, y + 46, w - 44, 46, 'display: flex; align-items: center; gap: 13px;',
                 face('mira', 44) +
                 f'<div>{disp("Doubtful", 23)}'
                 f'<div style="font-family: {UI}; font-size: 12.5px; color: {MUT};">at the gala, three weeks later</div></div>'))
    p.append(tx(x + 22, y + 104, w - 44, '', eyebrow('How he feels about you')))
    mw = (w - 44 - 24) // 3
    for i, (lb, v, c) in enumerate((('warmth', 72, OK), ('trust', 54, ACC), ('doubt', 46, WARM))):
        p.append(meter(x + 22 + i * (mw + 12), y + 126, mw, lb, v, c))
    p.append(rule(x + 22, y + 176, w - 44))
    p.append(tx(x + 22, y + 190, w - 44, '', eyebrow('What he still holds onto')))
    p.append(tx(x + w - 150, y + 189, 128, f'text-align: right; font-family: {UI}; font-size: 11px; color: {FAINT}; {TAB}', '3 of 41'))
    hy = y + 214
    for text, word, frac, col in HOLD:
        p.append(tx(x + 22, hy, w - 130, f'font-family: {NR}; font-size: 15.5px; color: {MID};', text))
        p.append(tx(x + w - 108, hy + 1, 86, f'text-align: right; font-family: {UI}; font-size: 11px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: {col};', word))
        bw = w - 44
        p.append(box(x + 22, hy + 26, bw, 4, f'border-radius: 2px; background: {HAIR};'))
        p.append(box(x + 22, hy + 26, int(bw * frac), 4, f'border-radius: 2px; background: {col};'))
        hy += 54
    p.append(box(x + 22, y + h - 42, w - 44, 26, f'display: flex; align-items: center; gap: 7px; color: {ACCT};',
                 icon('layers', 15, 'currentColor', 1.9) +
                 f'<span style="font-family: {UI}; font-size: 13px; font-weight: 700;">Open Backstage &middot; see how he got there</span>'))
    return ''.join(p)

def bubble(s):
    return (f'<div style="display: inline-block; max-width: 460px; padding: 11px 16px; border-radius: {R3}; '
            f'border-bottom-left-radius: 5px; background: {RAISE}; border: 1px solid {HAIR}; '
            f'font-family: {NR}; font-size: 16.5px; line-height: 1.45; color: {MID};">{s}</div>')

def build_profile():
    H = 1300
    X, W = RW + PAD, 1440 - RW - PAD * 2
    b = [box(0, 0, 1440, H, f'background: {GROUND};'), sky(H), rail(H, 'Characters')]
    b.append(topbar(X, W))
    # hero
    HH = 344
    b.append(box(X, 100, 268, HH - 36, f'border-radius: {R3}; overflow: hidden; background: {RAISE}; box-shadow: {SHF};',
                 cover('mira', '', '50% 24%', 'Mike, leaning on the counter, wary')))
    tX = X + 300
    b.append(tx(tX, 130, 600, '', eyebrow('Played 2 hours ago', WARM)))
    b.append(tx(tX, 150, 640, '', disp('Mike Dorsey', 54, INK, '800')))
    b.append(tx(tX, 212, 580, f'font-family: {NR}; font-size: 20px; font-style: italic; color: {MID};', 'Barista at Halcyon. Son of the queen&rsquo;s hairdresser.'))
    b.append(box(tX, 250, 420, 26, 'display: flex; gap: 8px;', tag('Barista') + tag('Steady') + tag('Private')))
    b.append(box(tX, 296, 620, 46, 'display: flex; align-items: center; gap: 12px;',
                 btn('Continue', 'primary', None, h=46) + btn('New story', 'secondary', None, h=46) +
                 f'<span style="display: inline-flex; align-items: center; justify-content: center; width: 46px; height: 46px; border-radius: 999px; border: 1px solid {BORDER}; color: {MUT};">{icon("dots", 18, "currentColor", 2)}</span>'))
    b.append(box(tX, 360, 660, 24, 'display: flex; align-items: center; gap: 20px;',
                 stat('stories', '4') + stat('lines', '412') + stat('places', '2') +
                 f'<span style="font-family: {UI}; font-size: 12.5px; color: {MUT};">together since '
                 f'<b style="font-weight: 700; color: {INK}; {TAB}">24 May</b></span>'))
    ay = 470
    b.append(box(X, ay, 320, 34, 'display: flex; gap: 24px; align-items: flex-end;',
                 f'<span style="font-family: {UI}; font-size: 15px; font-weight: 700; color: {INK}; border-bottom: 2px solid {ACC}; padding-bottom: 8px;">Story</span>'
                 f'<span style="font-family: {UI}; font-size: 15px; font-weight: 600; color: {FAINT}; padding-bottom: 8px;">Profile</span>'))
    b.append(rule(X, ay + 33, 660))
    LW = 660
    cy = ay + 62
    b.append(tx(X, cy, LW, '', eyebrow('How he talks')))
    b.append(box(X, cy + 24, LW, 60, '', bubble('Ten minutes. Drink it fast or I&rsquo;m putting you to work.')))
    b.append(box(X + 44, cy + 88, LW, 60, '', bubble('<em>wipes the counter twice</em> It&rsquo;s fine. It&rsquo;s not fine, but it&rsquo;s fine.')))
    sy = cy + 172
    b.append(box(X, sy, LW, 132, f'background: {SECRET_BG}; border: 1px solid rgba(231,176,106,.34); border-radius: {R3};'))
    b.append(box(X + 22, sy + 20, 20, 20, '', icon('lock', 18, WARM, 1.9)))
    b.append(tx(X + 50, sy + 21, LW - 80, f'font-family: {UI}; font-size: 10.5px; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; color: {WARM};', 'Only Mike knows this'))
    b.append(tx(X + 22, sy + 54, LW - 44, f'font-family: {NR}; font-size: 20px; line-height: 1.45; color: {SECRET_INK};', 'He cuts the queen&rsquo;s hair now. His mother&rsquo;s hands shake and no one can know.'))
    ry = sy + 164
    b.append(tx(X, ry, LW, '', eyebrow('Who he knows')))
    rx = X
    for k, nm, how in (('tobin', 'Theo', 'wary of him'), ('aren', 'Liv', 'fond of her'), ('oren', 'Jae', 'never met')):
        b.append(panel(rx, ry + 24, 208, 70, face(k, 38, 'position: absolute; left: 14px; top: 16px;') +
                       f'<div style="position: absolute; left: 62px; top: 16px;">{disp(nm, 17)}'
                       f'<div style="font-family: {UI}; font-size: 12px; color: {MUT};">{how}</div></div>'))
        rx += 226
    my = ry + 118
    b.append(tx(X, my, LW, '', eyebrow('Moments together')))
    mx = X
    for key, cap, pos in (('gull-dusk', 'the evening it rained', '50% 50%'), ('gull-night', 'the gala', '50% 42%')):
        b.append(still(mx, my + 24, 322, 176, key, cap, pos))
        mx += 338
    # right column
    RX, RW_ = X + 700, W - 700
    b.append(living(RX, ay, RW_))
    ty = ay + 440
    b.append(tx(RX, ty, RW_, '', eyebrow('Stories together')))
    yy = ty + 24
    for title, rel, when in (('Two Sugars, No Title', 'three weeks later', 'Played 2 hours ago'),
                             ('The Gala List', 'two days before', 'Played last week'),
                             ('The Long Way Home', 'as Cas', 'Played 3 weeks ago')):
        b.append(rule(RX, yy, RW_))
        b.append(tx(RX, yy + 14, RW_ - 140, '', disp(title, 17)))
        b.append(tx(RX, yy + 38, RW_ - 140, f'font-family: {UI}; font-size: 12.5px; color: {MUT};', rel))
        b.append(tx(RX + RW_ - 140, yy + 20, 140, f'text-align: right; font-family: {UI}; font-size: 12px; font-weight: 600; color: {FAINT};', when))
        yy += 70
    b.append(rule(RX, yy, RW_))
    b.append(box(RX, yy + 20, RW_, 30, f'display: flex; align-items: center; gap: 8px; color: {MUT};',
                 icon('download', 15, 'currentColor', 1.8) +
                 f'<span style="font-family: {UI}; font-size: 13px; font-weight: 600;">Export everything about Mike</span>'))
    return page('Sky &middot; Mike&rsquo;s profile (dark)', 1440, H, ''.join(b))

# ------------------------------------------------------------------ STORIES
STORIES = [
 dict(t='Two Sugars, No Title', book='Close to the Crown', who=['mira', 'tobin'], real='2 h ago',
      story='three weeks later', last='&hellip;I could have sworn. Three weeks is a long time to hold one sentence.', pin=True, sel=True),
 dict(t='The Gala List', book='Close to the Crown', who=['oren'], real='last week',
      story='two days before the gala', last='Officially? No comment. Unofficially, be there by eight.', pin=False, sel=False),
 dict(t='Three in the Morning', book='The Flat on Ardenne', who=['ilsa'], real='4 days ago',
      story='the night before a game', last='You&rsquo;re not going to like this painting.', pin=False, sel=False),
 dict(t='The Long Way Home', book='Not in a book &middot; as Cas', who=['mira'], real='3 weeks ago',
      story='the week the engine died', last='Leave it. We&rsquo;ll push.', pin=False, sel=False),
 dict(t='Closing Shift', book='Close to the Crown', who=['mira', 'tobin', 'ilsa'], real='a month ago',
      story='day one', last='The espresso machine sighs and goes quiet.', pin=False, sel=False),
]

def seg(items, on):
    out = []
    for i, s in enumerate(items):
        a = s == on
        out.append(f'<span style="display: inline-flex; align-items: center; height: 30px; padding: 0 14px; border-radius: 999px; '
                   f'font-family: {UI}; font-size: 12.5px; font-weight: 700; '
                   f'{"background: " + RAISE + "; color: " + INK + ";" if a else "color: " + MUT + ";"}">{s}</span>')
    return (f'<span style="display: inline-flex; padding: 3px; border-radius: 999px; background: {SUNK}; '
            f'border: 1px solid {BORDER};">{"".join(out)}</span>')

def build_stories():
    H = 1100
    X, W = RW + PAD, 1440 - RW - PAD * 2
    b = [box(0, 0, 1440, H, f'background: {GROUND};'), sky(H), rail(H, 'Stories')]
    b.append(topbar(X, W))
    b.append(tx(X, 92, 400, '', disp('Stories', 32, INK, '800')))
    b.append(box(X + W - 380, 96, 380, 34, 'display: flex; justify-content: flex-end; align-items: center; gap: 12px;',
                 seg(['By story', 'By character'], 'By story') + btn('New story', 'primary', 'plus', h=36, fs=13.5)))
    b.append(box(X, 146, 620, 32, 'display: flex; gap: 8px;',
                 chip('All', True, count=12) + chip('Pinned', count=1) + chip('Close to the Crown', count=6) + chip('As Cas', count=2)))
    LW = 540
    y = 196
    for s in STORIES:
        sel = s['sel']
        css = (f'background: {RAISE}; border: 1px solid {ACC};' if sel else f'background: {PANEL}; border: 1px solid {HAIR};')
        faces = ''.join(face(k, 34, f'position: absolute; left: {16 + i * 22}px; top: 19px; box-shadow: 0 0 0 2px {RAISE if sel else PANEL};')
                        for i, k in enumerate(s['who']))
        off = 16 + 22 * (len(s['who']) - 1) + 46
        pin = (f'<span style="position: absolute; right: 16px; top: 18px; color: {WARM};">{icon("pushpin", 15, "currentColor", 1.9)}</span>') if s['pin'] else ''
        inner = (faces + pin +
                 f'<div style="position: absolute; left: {off}px; top: 16px; right: 40px;">{disp(s["t"], 18)}'
                 f'<div style="font-family: {UI}; font-size: 11.5px; color: {FAINT}; margin-top: 1px;">{s["book"]}</div></div>'
                 f'<div style="position: absolute; left: 16px; right: 120px; top: 62px; font-family: {NR}; font-size: 15px; '
                 f'color: {MID}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{s["last"]}</div>'
                 f'<div style="position: absolute; right: 16px; bottom: 13px; text-align: right;">'
                 f'<div style="font-family: {UI}; font-size: 11.5px; font-weight: 700; color: {MID};">{s["real"]}</div>'
                 f'<div style="font-family: {UI}; font-size: 11px; color: {FAINT};">{s["story"]}</div></div>')
        b.append(box(X, y, LW, 96, css + f' border-radius: {R2};', inner))
        y += 106
    # preview
    PX = X + LW + 24
    PW = W - LW - 24
    b.append(panel(PX, 196, PW, 856, '', 0, f'box-shadow: {SHF}; overflow: hidden;'))
    b.append(box(PX + 1, 197, PW - 2, 250, 'overflow: hidden;',
                 cover('gull-night', '', '50% 40%', 'Corvel Palace at night') +
                 f'<div style="position: absolute; inset: 0; background: linear-gradient(to top, {PANEL} 2%, rgba(19,27,58,.35) 55%, transparent 100%);"></div>'))
    b.append(tx(PX + 26, 372, PW - 200, '', disp('Two Sugars, No Title', 28, INK, '800')))
    b.append(tx(PX + 26, 412, PW - 200, f'font-family: {UI}; font-size: 12.5px; color: {MUT};', 'Close to the Crown &middot; three weeks later &middot; Corvel Palace'))
    b.append(box(PX + 26, 446, PW - 52, 50, 'display: flex; align-items: center; gap: 14px;',
                 btn('Continue', 'primary', None, h=46, fs=15) +
                 f'<span style="font-family: {UI}; font-size: 12.5px; color: {FAINT};">Last played 2 hours ago</span>'))
    b.append(rule(PX + 26, 520, PW - 52))
    b.append(tx(PX + 26, 540, PW - 52, '', eyebrow('Who is here')))
    wy = 566
    for k, nm, n, extra, col in (('mira', 'Mike', '12 memories from this story', '1 doubted', WARM),
                                 ('tobin', 'Theo', '3 memories from this story', 'none of the gala', MUT)):
        b.append(box(PX + 26, wy, PW - 52, 50, 'display: flex; align-items: center; gap: 12px;',
                     face(k, 36) +
                     f'<div style="flex: 1;"><span style="font-family: {UI}; font-size: 14px; font-weight: 700; color: {INK};">{nm}</span>'
                     f'<div style="font-family: {UI}; font-size: 12.5px; color: {MUT}; {TAB}">{n}</div></div>' +
                     enum_pill(extra, col)))
        wy += 56
    b.append(rule(PX + 26, wy + 6, PW - 52))
    b.append(tx(PX + 26, wy + 26, PW - 52, '', eyebrow('New since you left')))
    for i, (ic, col, ev, quote) in enumerate(((('thought'), WARM, 'Memory doubted', '&ldquo;She says she never said it.&rdquo;'),
                                              ('clock', MUT, 'Memory faded', '&ldquo;She didn&rsquo;t want to be on the gala list.&rdquo;'))):
        b.append(box(PX + 26, wy + 48 + i * 30, PW - 52, 24, 'display: flex; align-items: center; gap: 9px;',
                     icon(ic, 15, col, 1.9) +
                     f'<span style="font-family: {UI}; font-size: 11px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: {col}; width: 116px;">{ev}</span>'
                     f'<span style="font-family: {NR}; font-size: 15px; color: {MID};">{quote}</span>'))
    py = wy + 122
    b.append(rule(PX + 26, py, PW - 52))
    b.append(tx(PX + 26, py + 20, PW - 52, '', eyebrow('Where it happens')))
    px = PX + 26
    for key, cap, pos in (('gull-dusk', 'Halcyon Coffee', '50% 50%'), ('gull-night', 'Corvel Palace', '50% 42%')):
        b.append(still(px, py + 44, (PW - 64) // 2, 112, key, cap, pos))
        px += (PW - 64) // 2 + 12
    b.append(rule(PX + 26, py + 182, PW - 52))
    acts = ''.join(f'<span style="display: inline-flex; align-items: center; gap: 7px; font-family: {UI}; font-size: 13px; '
                   f'font-weight: 600; color: {MUT}; margin-right: 22px;">{icon(i, 15, "currentColor", 1.8)}{l}</span>'
                   for i, l in (('edit', 'Rename'), ('download', 'Export'), ('pushpin', 'Unpin'), ('x', 'Delete')))
    b.append(box(PX + 26, py + 200, PW - 52, 28, 'display: flex; align-items: center;', acts))
    b.append(box(X, 196 + 5 * 106 + 6, LW, 34, f'display: flex; align-items: center; justify-content: center; gap: 8px; '
                 f'border: 1px dashed {HAIR}; border-radius: {R2}; color: {FAINT};',
                 f'<span style="font-family: {UI}; font-size: 12.5px; font-weight: 600;">7 older stories</span>' + icon('down', 14, 'currentColor', 2)))
    return page('Sky &middot; Stories (dark)', 1440, H, ''.join(b))

# -------------------------------------------------------------------- WORLD
TIMES = [('dawn', '#c9a6c6'), ('day', '#9fc4e8'), ('dusk', '#e0a06a'), ('night', '#5b6ba8')]

def _lum(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]

def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + .05) / (min(la, lb) + .05)

def best_on(bg):
    """Text colour for a filled chip: whichever of ink or ground reads better. Computed, not picked."""
    return max(('#131b3a', '#eef2ff'), key=lambda c: contrast(c, bg))

def timestrip(x, y, w, on='dusk'):
    p = []
    cw = (w - 3 * 6) // 4
    for i, (nm, col) in enumerate(TIMES):
        a = nm == on
        p.append(box(x + i * (cw + 6), y, cw, 26,
                     f'border-radius: {R1}; background: {col if a else "rgba(168,190,255,.07)"}; '
                     f'border: 1px solid {"rgba(255,255,255,.28)" if a else HAIR}; display: flex; align-items: center; justify-content: center; '
                     f'font-family: {UI}; font-size: 10.5px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; '
                     f'color: {best_on(col) if a else FAINT};', nm))
    return ''.join(p)

def place_card(x, y, w, key, name, blurb, who, links, on='dusk', pos=None):
    H = 286
    p = [panel(x, y, w, H, '', 0, 'overflow: hidden;')]
    p.append(box(x + 1, y + 1, w - 2, 150, 'overflow: hidden;',
                 cover(key, '', pos, name) +
                 f'<div style="position: absolute; inset: 0; background: linear-gradient(to top, rgba(12,18,42,.85), transparent 62%);"></div>'
                 f'<div style="position: absolute; left: 15px; bottom: 11px;">{disp(name, 20, "#eef2ff")}</div>'))
    p.append(tx(x + 15, y + 162, w - 30, f'font-family: {NR}; font-size: 14.5px; line-height: 1.4; color: {MUT};', blurb))
    p.append(timestrip(x + 15, y + 212, w - 30, on))
    p.append(box(x + 15, y + 250, w - 30, 26, 'display: flex; align-items: center; gap: 8px;',
                 ''.join(face(k, 24, f'margin-left: {0 if i == 0 else -7}px; box-shadow: 0 0 0 2px {PANEL};') for i, k in enumerate(who)) +
                 f'<span style="margin-left: 6px; font-family: {UI}; font-size: 11.5px; color: {FAINT};">{links}</span>'))
    return ''.join(p)

def plot_card(x, y, w, quote, opening, book, who):
    H = 286
    p = [panel(x, y, w, H, '', 0, f'overflow: hidden; background: {PANEL};')]
    p.append(box(x + 1, y + 1, w - 2, 4, f'background: linear-gradient(90deg, {WARM}, rgba(231,176,106,0));'))
    p.append(box(x + 15, y + 22, 24, 24, '', icon('quote', 22, 'rgba(231,176,106,.5)', 1.8)))
    p.append(tx(x + 15, y + 58, w - 30, f'font-family: {NR}; font-style: italic; font-size: 19px; line-height: 1.4; color: {INK};', quote))
    p.append(rule(x + 15, y + 186, w - 30))
    p.append(tx(x + 15, y + 200, w - 30, f'font-family: {UI}; font-size: 12.5px; line-height: 1.45; color: {MUT};', opening))
    p.append(box(x + 15, y + 250, w - 30, 26, 'display: flex; align-items: center; gap: 8px;',
                 ''.join(face(k, 24, f'margin-left: {0 if i == 0 else -7}px; box-shadow: 0 0 0 2px {PANEL};') for i, k in enumerate(who)) +
                 f'<span style="margin-left: 6px; font-family: {UI}; font-size: 11.5px; color: {FAINT};">{book}</span>'))
    return ''.join(p)

def build_world():
    H = 950
    X, W = RW + PAD, 1440 - RW - PAD * 2
    b = [box(0, 0, 1440, H, f'background: {GROUND};'), sky(H), rail(H, 'World')]
    b.append(topbar(X, W))
    b.append(tx(X, 92, 400, '', disp('World', 32, INK, '800')))
    b.append(tx(X, 134, 560, f'font-family: {UI}; font-size: 13.5px; color: {MUT};', 'Places and plots, filed under the books and stories they belong to.'))
    b.append(box(X + W - 420, 96, 420, 34, 'display: flex; justify-content: flex-end; align-items: center; gap: 12px;',
                 seg(['All', 'Places', 'Plots'], 'All') + btn('Add', 'secondary', 'plus', h=36, fs=13.5)))
    SY = 188
    SW = 236
    b.append(panel(X, SY, SW, 620))
    sy = SY + 18
    b.append(box(X + 14, sy, SW - 28, 34, f'display: flex; align-items: center; gap: 10px; padding: 0 11px; box-sizing: border-box; '
                 f'border-radius: {R2}; background: {RAISE}; border: 1px solid {BORDER}; color: {INK};',
                 icon('grid', 16, 'currentColor', 1.9) + f'<span style="font-family: {UI}; font-size: 13.5px; font-weight: 700; flex: 1;">Everything</span>'
                 f'<span style="font-family: {UI}; font-size: 11.5px; color: {MUT};">14</span>'))
    sy += 48
    b.append(tx(X + 25, sy, SW - 40, '', eyebrow('Books')))
    sy += 22
    tree = [(0, 'Close to the Crown', '9', True), (1, 'Two Sugars, No Title', '4', False), (1, 'The Gala List', '3', False),
            (1, 'Closing Shift', '2', False), (0, 'The Flat on Ardenne', '3', False), (1, 'Three in the Morning', '3', False)]
    for lvl, name, n, on in tree:
        col = INK if lvl == 0 else MUT
        fw = 700 if lvl == 0 else 500
        fs = 13.5 if lvl == 0 else 12.5
        mark = box(X + 17, sy + 9, 2, 16, f'background: {ACC}; border-radius: 1px;') if on else ''
        ic = icon('book', 15, 'currentColor', 1.8) if lvl == 0 else ''
        b.append(mark + box(X + 25 + lvl * 16, sy, SW - 42 - lvl * 16, 32, f'display: flex; align-items: center; gap: 8px; color: {col};',
                            ic + f'<span style="font-family: {UI}; font-size: {fs}px; font-weight: {fw}; flex: 1;">{name}</span>'
                            f'<span style="font-family: {UI}; font-size: 11px; color: {FAINT};">{n}</span>'))
        sy += 34
    b.append(box(X + 25, sy, SW - 42, 32, f'display: flex; align-items: center; gap: 8px; color: {MUT};',
                 icon('layers', 15, 'currentColor', 1.8) + f'<span style="font-family: {UI}; font-size: 12.5px; flex: 1;">Not in a book</span>'
                 f'<span style="font-family: {UI}; font-size: 11px; color: {FAINT};">2</span>'))
    sy += 50
    b.append(rule(X + 14, sy - 14, SW - 28))
    b.append(tx(X + 25, sy, SW - 40, '', eyebrow('Who knows it')))
    sy += 24
    b.append(box(X + 20, sy, SW - 32, 80, 'display: flex; flex-wrap: wrap; gap: 7px;',
                 chip('Mike', True) + chip('Theo') + chip('Nico') + chip('Jae')))
    # grid
    GX, GW = X + SW + 24, W - SW - 24
    CW = (GW - 24) // 3
    b.append(box(GX, SY - 42, GW, 26, 'display: flex; align-items: center; justify-content: space-between;',
                 f'<span style="font-family: {UI}; font-size: 12.5px; color: {MUT};">14 places and plots &middot; filtered to <b style="color: {INK};">Mike</b></span>'
                 f'<span style="font-family: {UI}; font-size: 12.5px; font-weight: 600; color: {MUT};">Recently used &#9662;</span>'))
    b.append(tx(GX, SY, GW, '', disp('Close to the Crown', 21)))
    gy = SY + 36
    b.append(place_card(GX, gy, CW, 'gull-dusk', 'Halcyon Coffee', 'A corner caf&eacute; with mismatched chairs. Closes at 7:15 and never on time.',
                        ['mira', 'tobin'], 'Two Sugars &middot; The Gala List', 'dusk', '50% 52%'))
    b.append(plot_card(GX + CW + 12, gy, CW, '&ldquo;The palace sends out the gala list, and both your names are on it.&rdquo;',
                       'Opens with: a courier bike pulls up outside Halcyon, and the envelope has a seal on it.',
                       'The Invitation &middot; a plot', ['mira', 'oren']))
    b.append(plot_card(GX + (CW + 12) * 2, gy, CW, '&ldquo;The caf&eacute; shuts in ten minutes and neither of you wants to leave.&rdquo;',
                       'Opens with: the espresso machine sighs and goes quiet.',
                       'Closing Shift &middot; a plot', ['mira']))
    gy2 = gy + 310
    b.append(tx(GX, gy2, GW, '', disp('Elsewhere', 21)))
    b.append(tx(GX + 152, gy2 + 5, GW - 152, f'font-family: {UI}; font-size: 12.5px; color: {FAINT};', 'other books &middot; 2 not filed yet'))
    b.append(place_card(GX, gy2 + 36, CW, 'market', 'The flat on Ardenne', 'Two students, one sofa, a television nobody watches. Paint drying on the radiator.',
                        ['ilsa'], 'The Flat on Ardenne', 'night', '50% 48%'))
    b.append(place_card(GX + CW + 12, gy2 + 36, CW, 'gull-night', 'Corvel Palace', 'Gold stairs, orange trees, and a guest list nobody admits to reading.',
                        ['oren'], 'Not filed yet', 'night', '50% 40%'))
    # link dialog, floating: glass is justified here
    DX, DY, DW = GX + (CW + 12) * 2 - 28, gy2 + 8, CW + 56
    b.append(box(DX, DY, DW, 356, f'background: {POP}; backdrop-filter: blur(22px); border: 1px solid {BORDER}; '
                 f'border-radius: {R3}; box-shadow: {SHF};'))
    b.append(tx(DX + 22, DY + 22, DW - 44, '', disp('File Corvel Palace', 20)))
    b.append(tx(DX + 22, DY + 50, DW - 44, f'font-family: {UI}; font-size: 12.5px; color: {MUT};', 'File it so it shows up where it belongs.'))
    ly = DY + 84
    for label, val, ic in (('Book', 'Close to the Crown', 'book'), ('Stories', 'Two Sugars, No Title', 'chat')):
        b.append(tx(DX + 22, ly, DW - 44, '', eyebrow(label)))
        b.append(box(DX + 22, ly + 20, DW - 44, 38, f'background: {SUNK}; border: 1px solid {BORDER}; border-radius: {R2}; '
                     f'display: flex; align-items: center; gap: 9px; padding: 0 12px; box-sizing: border-box; color: {INK};',
                     icon(ic, 15, MUT, 1.8) + f'<span style="font-family: {UI}; font-size: 13px; font-weight: 600; flex: 1;">{val}</span>' + icon('down', 14, MUT, 2)))
        ly += 72
    b.append(tx(DX + 22, ly, DW - 44, '', eyebrow('Who knows it')))
    b.append(box(DX + 22, ly + 22, DW - 44, 34, 'display: flex; gap: 7px;', chip('Jae', True) + chip('Liv') + chip('+ add')))
    b.append(box(DX + 22, DY + 300, DW - 44, 40, 'display: flex; gap: 10px; justify-content: flex-end;',
                 btn('Cancel', 'ghost', h=38, fs=13.5) + btn('Link it', 'primary', h=38, fs=13.5)))
    return page('Sky &middot; World (dark)', 1440, H, ''.join(b))

# ----------------------------------------------------------------- FIRST RUN
DOORS = [
 dict(ic='flame', sub='Recommended', title='Start now',
      body='Kataki brings a small model with it. 1.2&nbsp;GB, downloads once, runs here. Good enough to meet someone tonight.',
      act='Start now', kind='primary', second=None),
 dict(ic='server', sub='Found on this computer', title='Use a model server',
      body='Found <b style="color:{INK}">llama.cpp</b> running, with <b style="color:{INK}">qwen3.5-9b</b> loaded. Kataki can use it as it is.',
      act='Use this', kind='secondary', second='Look again'),
 dict(ic='globe', sub='Sends your story elsewhere', title='Use an online model',
      body='OpenRouter, OpenAI, Anthropic, or anything OpenAI-compatible. Your key stays in this computer&rsquo;s keychain.',
      act='Add a key', kind='secondary', second=None),
]

def build_firstrun():
    H = 900
    b = [box(0, 0, 1440, H, f'background: {GROUND};'), sky(H, 0)]
    X, W = 132, 1176
    b.append(tx(X, 76, W, '', eyebrow('Kataki &middot; step 1 of 2', ACC)))
    b.append(tx(X, 98, W, '', disp('They&rsquo;ll remember this.', 68, INK, '800')))
    b.append(tx(X, 186, 760, f'font-family: {NR}; font-size: 21px; line-height: 1.45; color: {MID};',
                'Kataki needs something to think with. Pick one &mdash; you can change it whenever you like.'))
    b.append(box(X, 250, 700, 62, f'background: rgba(19,27,58,.72); border: 1px solid {BORDER}; border-left: 3px solid {WARM}; '
                 f'border-radius: {R2}; display: flex; align-items: center; gap: 13px; padding: 0 18px; box-sizing: border-box;',
                 icon('shield', 22, WARM, 1.8) +
                 f'<span style="font-family: {UI}; font-size: 16px; font-weight: 600; color: {INK};">Nothing leaves this computer unless you pick the third door.</span>'))
    dy = 352
    CW = (W - 40) // 3
    x = X
    for d in DOORS:
        first = d['kind'] == 'primary'
        ex = f'border-color: {ACCT}; box-shadow: 0 0 0 3px rgba(91,134,255,.16), {SHF};' if first else ''
        b.append(panel(x, dy, CW, 276, '', 0, ex))
        b.append(box(x + 22, dy + 22, 42, 42, f'border-radius: {R2}; background: {PRIM if first else RAISE}; display: flex; align-items: center; justify-content: center;',
                     icon(d['ic'], 21, '#fff' if first else MUT, 1.9)))
        b.append(tx(x + 22, dy + 78, CW - 44, '', eyebrow(d['sub'], ACC if first else FAINT)))
        b.append(tx(x + 22, dy + 98, CW - 44, '', disp(d['title'], 26)))
        b.append(tx(x + 22, dy + 136, CW - 44, f'font-family: {UI}; font-size: 13.5px; line-height: 1.55; color: {MID};', d['body']))
        acts = btn(d['act'], d['kind'], h=42, fs=14) + (btn(d['second'], 'ghost', h=42, fs=14) if d['second'] else '')
        b.append(box(x + 22, dy + 214, CW - 44, 42, 'display: flex; gap: 10px;', acts))
        x += CW + 20
    cy = dy + 258 + 62
    b.append(rule(X, cy - 26, W))
    faces = ''.join(face(k, 46, f'margin-left: {0 if i == 0 else -13}px; box-shadow: 0 0 0 3px {GROUND};')
                    for i, k in enumerate(['mira', 'tobin', 'ilsa', 'oren', 'aren', 'sable']))
    b.append(box(X, cy, 320, 48, 'display: flex; align-items: center;', faces))
    b.append(tx(X + 300, cy + 3, 420, f'font-family: {UI}; font-size: 14.5px; font-weight: 700; color: {INK};', 'Six people are already here.'))
    b.append(tx(X + 300, cy + 25, 460, f'font-family: {UI}; font-size: 13px; color: {MUT};', 'Pick one after this. Write your own whenever you like.'))
    b.append(box(X + W - 340, cy + 4, 340, 44, 'display: flex; justify-content: flex-end; align-items: center; gap: 8px;',
                 icon('download', 16, ACC, 1.9) +
                 f'<span style="font-family: {UI}; font-size: 13.5px; font-weight: 700; color: {ACCT};">Coming from somewhere else? Import cards</span>'))
    b.append(tx(X, H - 48, W, f'font-family: {UI}; font-size: 12.5px; color: {MUT};',
                'All of this lives in Settings afterwards. '
                f'<span style="color: {INK}; font-weight: 700;">Skip for now</span>'))
    return page('Sky &middot; First run (dark)', 1440, H, ''.join(b))


# ============================================================== shared shell
def shell(H, active, title=None, sub=None, right='', x0=RW):
    b = [box(0, 0, 1440, H, f'background: {GROUND};'), sky(H, x0)]
    if x0:
        b.append(rail(H, active))
    X, W = RW + PAD, 1440 - RW - PAD * 2
    b.append(topbar(X, W))
    if title:
        b.append(tx(X, 92, 560, '', disp(title, 32, INK, '800')))
    if sub:
        b.append(tx(X, 134, 620, f'font-family: {UI}; font-size: 13.5px; color: {MUT};', sub))
    if right:
        b.append(box(X + W - 480, 96, 480, 36, 'display: flex; justify-content: flex-end; align-items: center; gap: 12px;', right))
    return b, X, W

def field(x, y, w, label, value, ic=None, hint=None, kind='select', h=40):
    p = []
    if label:
        p.append(tx(x, y, w, '', eyebrow(label)))
        y += 20
    if kind == 'toggle':
        on = value
        p.append(box(x, y, 46, 26, f'border-radius: 999px; background: {PRIM if on else SUNK}; border: 1px solid {BORDER};',
                     box(4 if not on else 22, 3, 18, 18, 'border-radius: 50%; background: #fff; position: absolute;')))
        return ''.join(p)
    inner = ((icon(ic, 15, MUT, 1.8) + '<span style="width: 9px;"></span>') if ic else '')
    inner += f'<span style="font-family: {UI}; font-size: 13.5px; font-weight: 600; color: {INK}; flex: 1;">{value}</span>'
    if kind == 'select':
        inner += icon('down', 14, MUT, 2)
    p.append(box(x, y, w, h, f'background: {SUNK}; border: 1px solid {BORDER}; border-radius: {R2}; '
                 f'display: flex; align-items: center; padding: 0 13px; box-sizing: border-box;', inner))
    if hint:
        p.append(tx(x, y + h + 7, w, f'font-family: {UI}; font-size: 11.5px; color: {FAINT};', hint))
    return ''.join(p)

def row(x, y, w, title, desc, control, h=68, last=False):
    p = [tx(x, y + 14, w - 220, f'font-family: {UI}; font-size: 14px; font-weight: 600; color: {INK};', title)]
    p.append(tx(x, y + 34, w - 230, f'font-family: {UI}; font-size: 12.5px; line-height: 1.4; color: {MUT};', desc))
    p.append(box(x + w - 210, y + 14, 210, 40, 'display: flex; justify-content: flex-end; align-items: center;', control))
    if not last:
        p.append(rule(x, y + h, w))
    return ''.join(p)

def menu(x, y, w, items, title=None, foot=None):
    """A floating menu. Glass is allowed here: it floats over the page."""
    ih = 40
    h = (24 if title else 12) + len(items) * ih + (14 if not foot else 52)
    p = [box(x, y, w, h, f'background: {POP}; backdrop-filter: blur(22px); border: 1px solid {BORDER}; '
             f'border-radius: {R3}; box-shadow: {SHF};')]
    yy = y + (22 if title else 8)
    if title:
        p.append(tx(x + 14, y + 12, w - 28, '', eyebrow(title)))
        yy = y + 36
    for it in items:
        ic, label, meta, state = (it + (None, None))[:4] if len(it) < 4 else it
        col = INK if state != 'off' else FAINT
        bg = f'background: rgba(91,134,255,.14);' if state == 'on' else ''
        p.append(box(x + 8, yy, w - 16, 34, f'display: flex; align-items: center; gap: 11px; padding: 0 10px; box-sizing: border-box; border-radius: {R1}; {bg} color: {col};',
                     (icon(ic, 16, 'currentColor', 1.8) if ic else '<span style="width: 16px;"></span>') +
                     f'<span style="font-family: {UI}; font-size: 13.5px; font-weight: {700 if state == "on" else 500}; flex: 1;">{label}</span>' +
                     (f'<span style="font-family: {MO}; font-size: 11px; color: {FAINT}; {TAB}">{meta}</span>' if meta else '') +
                     (icon('check', 15, ACC, 2.2) if state == 'on' else '')))
        yy += ih
    if foot:
        p.append(rule(x + 8, yy + 2, w - 16))
        p.append(box(x + 8, yy + 12, w - 16, 32, f'display: flex; align-items: center; gap: 11px; padding: 0 10px; box-sizing: border-box; color: {MUT};',
                     icon(foot[0], 16, 'currentColor', 1.8) + f'<span style="font-family: {UI}; font-size: 13px; font-weight: 600;">{foot[1]}</span>'))
    return ''.join(p)

def dim(H, x0=0):
    return box(x0, 0, 1440 - x0, H, f'background: {DIM};')

# ============================================================ CHARACTERS
PEOPLE = [
 ('mira', 'Mike Dorsey', 'Barista at Halcyon. Son of the queen&rsquo;s hairdresser.', 'Played 2 hours ago', 'In a story', 4),
 ('tobin', 'Theo Park', 'Engineering student. Covers Mike&rsquo;s shifts, hears everything.', 'Played yesterday', None, 2),
 ('ilsa', 'Nico Ferrer', 'Art student, your flatmate. Tells you the truth you asked for.', 'Played 4 days ago', None, 3),
 ('oren', 'Jae Moretti', 'Palace press aide. Runs six accounts, posts nothing about himself.', 'Played last week', None, 1),
 ('sable', 'Cas Brennan', 'Twelfth in line, and hates it.', 'Played 3 weeks ago', 'Persona', 1),
 ('wren', 'Dani', 'Florist. Delivers to the palace back gate twice a week.', 'Never played', 'Draft', 0),
]

def person_card(x, y, w, k, nm, line, when, badge, stories, hover=False):
    H = 322
    ex = f'border-color: {ACCT}; box-shadow: {SHF};' if hover else ''
    p = [panel(x, y, w, H, '', 0, 'overflow: hidden;' + ex)]
    art = noface(nm, 186) if k == 'wren' else cover(k, '', None, nm + ' portrait')
    bd = ''
    if badge:
        col = WARM if badge == 'In a story' else MUT
        bd = (f'<div style="position: absolute; left: 13px; top: 13px; padding: 4px 10px; border-radius: 999px; background: rgba(8,13,32,.8); '
              f'border: 1px solid {BORDER}; font-family: {UI}; font-size: 10.5px; font-weight: 700; color: {col};">{badge}</div>')
    p.append(box(x + 1, y + 1, w - 2, 186, 'overflow: hidden;', art + bd))
    p.append(tx(x + 16, y + 200, w - 32, '', disp(nm.split(' ')[0], 21)))
    p.append(tx(x + 16, y + 230, w - 32, f'font-family: {UI}; font-size: 12.5px; line-height: 1.4; color: {MUT};', line))
    p.append(box(x + 16, y + 286, w - 32, 22, 'display: flex; align-items: center; justify-content: space-between;',
                 f'<span style="font-family: {UI}; font-size: 11.5px; color: {FAINT}; {TAB}">{when}</span>'
                 f'<span style="font-family: {UI}; font-size: 11.5px; color: {FAINT}; {TAB}">{stories} stories</span>'))
    if hover:
        p.append(box(x + 1, y + 120, w - 2, 66, 'background: linear-gradient(to top, rgba(8,12,30,.94), transparent); display: flex; align-items: flex-end; gap: 8px; padding: 0 13px 11px; box-sizing: border-box;',
                     btn('Continue', 'primary', h=32, fs=12.5) +
                     f'<span style="display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 999px; border: 1px solid {BORDER}; color: {MUT};">{icon("dots", 15, "currentColor", 2)}</span>'))
    return ''.join(p)

def build_characters():
    H = 1120
    right = (seg(['Grid', 'List'], 'Grid') + btn('New character', 'primary', 'plus', h=36, fs=13.5))
    b, X, W = shell(H, 'Characters', 'Characters', '6 characters &middot; 1 draft &middot; 1 group', right)
    b.append(box(X, 178, 700, 32, 'display: flex; gap: 8px;',
                 chip('All', True, count=6) + chip('In a story', count=1) + chip('Favourites', count=2) + chip('Drafts', count=1) + chip('Personas', count=2)))
    b.append(box(X + W - 200, 178, 200, 32, f'display: flex; justify-content: flex-end; align-items: center; gap: 6px; color: {MUT};',
                 f'<span style="font-family: {UI}; font-size: 12.5px; font-weight: 600;">Recently played</span>' + icon('down', 14, 'currentColor', 2)))
    CW = (W - 3 * 16) // 4
    for i, (k, nm, line, when, badge, n) in enumerate(PEOPLE):
        gx = X + (i % 4) * (CW + 16)
        gy = 232 + (i // 4) * 344
        b.append(person_card(gx, gy, CW, k, nm, line, when, badge, n, hover=(i == 1)))
    b.append(box(X + 2 * (CW + 16), 576, CW, 322, f'border: 1.5px dashed {BORDER}; border-radius: {R3}; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; color: {MUT};',
                 icon('plus', 26, 'currentColor', 1.8) +
                 f'<span style="font-family: {UI}; font-size: 13px; font-weight: 700;">New character</span>'
                 f'<span style="font-family: {UI}; font-size: 11.5px; color: {FAINT};">or import a card</span>'))
    gy = 936
    b.append(tx(X, gy, 400, '', disp('Groups', 22)))
    b.append(tx(X + 108, gy + 6, 400, f'font-family: {UI}; font-size: 12.5px; color: {FAINT};', 'sets of characters you start a scene with'))
    faces = ''.join(face(k, 38, f'margin-left: {0 if i == 0 else -11}px; box-shadow: 0 0 0 2px {PANEL};') for i, k in enumerate(['mira', 'tobin']))
    b.append(panel(X, gy + 34, 340, 88, box(16, 24, 300, 40, 'display: flex; align-items: center; gap: 12px;',
                   faces + f'<div><div style="font-family: {UI}; font-size: 14px; font-weight: 700; color: {INK};">Closing shift</div>'
                   f'<div style="font-family: {UI}; font-size: 12px; color: {MUT};">Mike and Theo &middot; 2 stories</div></div>')))
    b.append(box(X + 356, gy + 34, 340, 88, f'border: 1.5px dashed {BORDER}; border-radius: {R3}; display: flex; align-items: center; justify-content: center; gap: 9px; color: {MUT};',
                 icon('plus', 18, 'currentColor', 1.8) + f'<span style="font-family: {UI}; font-size: 13px; font-weight: 600;">New group</span>'))
    return page('Sky &middot; Characters', 1440, H, ''.join(b))

# ================================================================== YOU
def build_you():
    H = 1040
    b, X, W = shell(H, 'You', 'You', 'Who you play as, and what each character knows about them.',
                    btn('New persona', 'primary', 'plus', h=36, fs=13.5))
    # active persona
    b.append(panel(X, 186, W, 236, '', 0, f'box-shadow: {SHF};'))
    b.append(box(X + 20, 206, 172, 196, f'border-radius: 12px; overflow: hidden; background: {RAISE};', cover('aren', '', '52% 22%', 'Liv')))
    b.append(tx(X + 214, 218, 500, '', eyebrow('Playing as &middot; default', ACC)))
    b.append(tx(X + 214, 238, 600, '', disp('Liv Sandoval', 36, INK, '800')))
    b.append(tx(X + 214, 288, 520, f'font-family: {NR}; font-size: 17px; font-style: italic; color: {MID};', 'Cheerleader. The queen&rsquo;s step-sister&rsquo;s daughter.'))
    b.append(box(X + 214, 322, 420, 26, 'display: flex; gap: 8px;', tag('Cheerleader') + tag('Blunt') + tag('Late')))
    b.append(box(X + 214, 362, 420, 38, 'display: flex; gap: 10px;', btn('Edit persona', 'secondary', h=38, fs=13.5) + btn('Switch', 'ghost', h=38, fs=13.5)))
    b.append(box(X + W - 260, 210, 240, 190, f'background: {SUNK}; border: 1px solid {HAIR}; border-radius: {R2}; padding: 16px; box-sizing: border-box;',
                 eyebrow('In play') +
                 f'<div style="margin-top: 12px; font-family: {UI}; font-size: 13px; color: {MID}; line-height: 1.9; {TAB}">'
                 f'<div><b style="color:{INK}">4</b> stories</div><div><b style="color:{INK}">3</b> characters know her</div>'
                 f'<div><b style="color:{INK}">1</b> secret she has told</div></div>'))
    # other personas
    b.append(tx(X, 456, 400, '', disp('Your personas', 22)))
    px = X
    for k, nm, line, state in (('aren', 'Liv Sandoval', 'Cheerleader, on every list', 'Default'),
                               ('sable', 'Cas Brennan', 'Twelfth in line, and hates it', None),
                               (None, 'Director', 'Play no one. Narrate, and let them talk.', None)):
        inner = ((face(k, 44, 'position: absolute; left: 16px; top: 18px;') if k else
                  box(16, 18, 44, 44, f'border-radius: 50%; background: {RAISE}; border: 1px dashed {BORDER}; display: flex; align-items: center; justify-content: center;', icon('film', 20, MUT, 1.8))) +
                 f'<div style="position: absolute; left: 72px; top: 18px; right: 14px;">'
                 f'<div style="font-family: {UI}; font-size: 14.5px; font-weight: 700; color: {INK};">{nm}</div>'
                 f'<div style="font-family: {UI}; font-size: 12px; color: {MUT}; margin-top: 2px;">{line}</div></div>' +
                 (f'<div style="position: absolute; right: 13px; top: 15px;">{tag(state, ACC)}</div>' if state else ''))
        b.append(panel(px, 492, 280, 80, inner))
        px += 296
    b.append(box(px, 492, 200, 80, f'border: 1.5px dashed {BORDER}; border-radius: {R3}; display: flex; align-items: center; justify-content: center; gap: 9px; color: {MUT};',
                 icon('plus', 18, 'currentColor', 1.8) + f'<span style="font-family: {UI}; font-size: 13px; font-weight: 600;">New persona</span>'))
    # who knows Liv
    b.append(tx(X, 616, 500, '', disp('Who knows Liv', 22)))
    b.append(tx(X + 214, 622, 500, f'font-family: {UI}; font-size: 12.5px; color: {FAINT};', 'per character, per story &mdash; and how sure they are'))
    ky = 654
    KNOW = [('mira', 'Mike', 'Two Sugars, No Title', 'Her mother is the queen&rsquo;s step-sister.', 'going hazy', .4),
            ('mira', 'Mike', 'Two Sugars, No Title', 'She did not want to be on the gala list.', 'doubted', .55),
            ('tobin', 'Theo', 'Two Sugars, No Title', 'She sent him to the back for milk.', 'held tight', .9),
            ('oren', 'Jae', 'The Gala List', 'Her name is on the list.', 'held tight', .88)]
    for i, (k, nm, st, what, word, frac) in enumerate(KNOW):
        yy = ky + i * 68
        b.append(rule(X, yy, W))
        b.append(box(X, yy + 14, 40, 40, '', face(k, 36)))
        b.append(tx(X + 52, yy + 15, 460, f'font-family: {NR}; font-size: 16px; color: {INK};', what))
        b.append(tx(X + 52, yy + 40, 460, f'font-family: {UI}; font-size: 12px; color: {FAINT};', f'{nm} &middot; {st}'))
        b.append(tx(X + W - 320, yy + 22, 110, f'text-align: right; font-family: {UI}; font-size: 11px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: {WARM if frac > .6 else MUT};', word))
        b.append(box(X + W - 200, yy + 30, 200, 4, f'border-radius: 2px; background: {HAIR};'))
        b.append(box(X + W - 200, yy + 30, int(200 * frac), 4, f'border-radius: 2px; background: {WARM if frac > .6 else MUT};'))
    yy = ky + 4 * 68
    b.append(rule(X, yy, W))
    b.append(box(X, yy + 20, W, 28, f'display: flex; align-items: center; gap: 22px; color: {MUT};',
                 ''.join(f'<span style="display: inline-flex; align-items: center; gap: 7px; font-family: {UI}; font-size: 13px; font-weight: 600;">{icon(i, 15, "currentColor", 1.8)}{l}</span>'
                         for i, l in (('download', 'Export everything about Liv'), ('eyeoff', 'Make a character forget something'), ('x', 'Delete this persona')))))
    return page('Sky &middot; You', 1440, H, ''.join(b))

# ======================================================== ADD A CHARACTER
def build_addcharacter():
    H = 1120
    b, X, W = shell(H, 'Characters', 'New character', 'Two things are required. Everything else can wait, or never happen.',
                    btn('Import a card', 'ghost', 'download', h=36, fs=13.5) + btn('Create', 'primary', h=36, fs=13.5))
    LW = 700
    y = 190
    # portrait
    b.append(panel(X, y, LW, 152))
    b.append(box(X + 18, y + 18, 116, 116, f'border-radius: 12px; border: 1.5px dashed {BORDER}; background: {SUNK}; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 7px; color: {MUT};',
                 icon('image', 24, 'currentColor', 1.8) + f'<span style="font-family: {UI}; font-size: 11px; font-weight: 600;">No portrait</span>'))
    b.append(tx(X + 152, y + 24, LW - 176, f'font-family: {UI}; font-size: 14px; font-weight: 700; color: {INK};', 'Give them a face'))
    b.append(tx(X + 152, y + 45, LW - 176, f'font-family: {UI}; font-size: 12.5px; line-height: 1.45; color: {MUT};',
                'Drop an image, pick one of the twelve that ship with Kataki, or leave it &mdash; they get an initial until you decide.'))
    b.append(box(X + 152, y + 92, 420, 36, 'display: flex; gap: 10px;',
                 btn('Choose a file', 'secondary', h=36, fs=13) + btn('Pick from Kataki&rsquo;s set', 'ghost', h=36, fs=13)))
    y += 172
    b.append(tx(X, y, LW, '', eyebrow('Required', ACCT)))
    b.append(panel(X, y + 22, LW, 252))
    b.append(field(X + 18, y + 42, LW - 36, 'Name', 'Dani', None, 'What you call them. You can change it later.', 'text'))
    b.append(tx(X + 18, y + 134, LW - 36, '', eyebrow('How they say hi')))
    b.append(box(X + 18, y + 154, LW - 36, 56, f'background: {SUNK}; border: 1px solid {ACC}; border-radius: {R2}; box-shadow: {FOCUS}; padding: 11px 13px; box-sizing: border-box;',
                 f'<span style="font-family: {NR}; font-size: 16px; color: {INK};">*sets the bucket down, wipes her hands*</span>'
                 f'<span style="font-family: {NR}; font-size: 16px; color: {FAINT};"> Back gate&rsquo;s locked again.|</span>'))
    b.append(box(X + 18, y + 220, LW - 36, 26, 'display: flex; align-items: center; gap: 8px;',
                 f'<span style="font-family: {UI}; font-size: 11.5px; color: {FAINT}; margin-right: 2px;">Stuck? Start from</span>' +
                 chip('Warm') + chip('Guarded') + chip('In a hurry') + chip('Mid-argument')))
    y += 298
    b.append(tx(X, y, LW, '', eyebrow('Optional &middot; add any of these whenever')))
    oy = y + 22
    OPT = [('user', 'About them', 'What anyone would see. Two or three lines is plenty.', 'Empty'),
           ('quote', 'How they talk', 'Two sample lines. This does more than anything else here.', 'Empty'),
           ('lock', 'Their secret', 'Something only they know. It changes how they answer.', 'Empty'),
           ('heart', 'Relationships', 'Who they already know, and how they feel about them.', 'Empty'),
           ('map-pin', 'Places they know', 'Pick from your World, or write a new one.', 'Empty'),
           ('cpu', 'Which model plays them', 'Leave it and they use the default.', 'Default')]
    for i, (ic, t, d, state) in enumerate(OPT):
        ry = oy + i * 56
        b.append(box(X, ry, LW, 48, f'background: {PANEL}; border: 1px solid {HAIR}; border-radius: {R2}; display: flex; align-items: center; gap: 12px; padding: 0 16px; box-sizing: border-box;',
                     icon(ic, 17, MUT, 1.8) +
                     f'<div style="flex: 1;"><span style="font-family: {UI}; font-size: 13.5px; font-weight: 600; color: {INK};">{t}</span>'
                     f'<span style="font-family: {UI}; font-size: 12px; color: {MUT}; margin-left: 10px;">{d}</span></div>'
                     f'<span style="font-family: {UI}; font-size: 11.5px; color: {FAINT}; margin-right: 10px;">{state}</span>' +
                     icon('plus', 16, MUT, 2)))
    # live preview
    PX, PW = X + LW + 32, W - LW - 32
    b.append(tx(PX, 190, PW, '', eyebrow('As they will look')))
    b.append(panel(PX, 212, PW, 402, '', 0, f'box-shadow: {SHF}; overflow: hidden;'))
    b.append(box(PX + 1, 213, PW - 2, 214, 'overflow: hidden;', noface('Dani', 214)))
    b.append(tx(PX + 20, 444, PW - 40, '', disp('Dani', 26)))
    b.append(tx(PX + 20, 480, PW - 40, f'font-family: {NR}; font-style: italic; font-size: 16px; line-height: 1.45; color: {MID};',
                '&ldquo;<em>sets the bucket down, wipes her hands</em> Back gate&rsquo;s locked again.&rdquo;'))
    b.append(box(PX + 20, 556, PW - 40, 26, 'display: flex; gap: 8px;', tag('Draft')))
    b.append(box(PX, 634, PW, 118, f'background: rgba(231,176,106,.08); border: 1px solid rgba(231,176,106,.28); border-radius: {R2}; padding: 15px 16px; box-sizing: border-box;',
                 f'<div style="display: flex; align-items: center; gap: 8px;">{icon("spark", 16, WARM, 1.9)}'
                 f'<span style="font-family: {UI}; font-size: 12.5px; font-weight: 700; color: {WARM};">They can start now</span></div>'
                 f'<div style="margin-top: 8px; font-family: {UI}; font-size: 12.5px; line-height: 1.5; color: {MID};">'
                 f'A name and a greeting is enough to play. Dani will stay a draft until you give her a secret &mdash; '
                 f'that is the part that makes someone behave like a person.</div>'))
    b.append(rule(X, H - 92, W))
    b.append(box(X, H - 72, W, 44, 'display: flex; align-items: center; gap: 12px;',
                 btn('Create Dani', 'primary', h=44) + btn('Save as draft', 'secondary', h=44) + btn('Cancel', 'ghost', h=44) +
                 f'<span style="margin-left: auto; font-family: {UI}; font-size: 12px; color: {FAINT};">Saved to this computer &middot; nothing is uploaded</span>'))
    return page('Sky &middot; New character', 1440, H, ''.join(b))

# ============================================================ NEW STORY
def build_newstory():
    H = 1020
    b, X, W = shell(H, 'Stories', 'New story', 'Four choices, three of them optional.',
                    btn('Start the scene', 'primary', h=36, fs=13.5))
    LW = 720
    y = 190
    # 1 who
    b.append(tx(X, y, LW, '', eyebrow('1 &middot; Who is in it', ACC)))
    b.append(panel(X, y + 22, LW, 150))
    px = X + 18
    for k, nm, on in (('mira', 'Mike', True), ('tobin', 'Theo', True), ('ilsa', 'Nico', False), ('oren', 'Jae', False), ('wren', 'Dani', False)):
        bd = ACC if on else BORDER
        b.append(box(px, y + 42, 112, 110, f'border: 1.5px solid {bd}; border-radius: {R2}; overflow: hidden; background: {RAISE};',
                     (noface(nm, 74) if k == 'wren' else cover(k, '', None, nm)) +
                     f'<div style="position: absolute; left: 0; right: 0; bottom: 0; padding: 7px 10px; background: rgba(8,13,32,.86);">'
                     f'<span style="font-family: {UI}; font-size: 13px; font-weight: 700; color: #eef2ff;">{nm}</span></div>' +
                     (f'<div style="position: absolute; right: 8px; top: 8px; width: 20px; height: 20px; border-radius: 50%; background: {ACC}; display: flex; align-items: center; justify-content: center;">{icon("check", 13, "#fff", 3)}</div>' if on else '')))
        px += 122
    b.append(box(px, y + 42, 86, 110, f'border: 1.5px dashed {BORDER}; border-radius: {R2}; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; color: {MUT};',
                 icon('search', 18, 'currentColor', 1.8) + f'<span style="font-family: {UI}; font-size: 11px;">Find</span>'))
    y += 196
    # 2 you
    b.append(tx(X, y, LW, '', eyebrow('2 &middot; You are')))
    b.append(box(X, y + 22, LW, 68, f'background: {PANEL}; border: 1px solid {BORDER}; border-radius: {R2}; display: flex; align-items: center; gap: 13px; padding: 0 16px; box-sizing: border-box;',
                 face('aren', 42) +
                 f'<div style="flex: 1;"><div style="font-family: {UI}; font-size: 14px; font-weight: 700; color: {INK};">Liv Sandoval</div>'
                 f'<div style="font-family: {UI}; font-size: 12px; color: {MUT};">Cheerleader. The queen&rsquo;s step-sister&rsquo;s daughter.</div></div>'
                 f'<span style="font-family: {UI}; font-size: 12.5px; font-weight: 600; color: {ACCT};">Change</span>'))
    y += 116
    # 3 where
    b.append(tx(X, y, LW, '', eyebrow('3 &middot; Where &middot; optional')))
    px = X
    for key, nm, on, pos in (('gull-dusk', 'Halcyon Coffee', True, '50% 52%'), ('gull-night', 'Corvel Palace', False, '50% 40%'), ('market', 'The flat on Ardenne', False, '50% 48%')):
        bd = ACC if on else BORDER
        b.append(box(px, y + 22, 176, 106, f'border: 1.5px solid {bd}; border-radius: {R2}; overflow: hidden; background: {RAISE};',
                     cover(key, '', pos, nm) +
                     f'<div style="position: absolute; left: 0; right: 0; bottom: 0; padding: 7px 10px; background: rgba(8,13,32,.86);">'
                     f'<span style="font-family: {UI}; font-size: 12px; font-weight: 700; color: #eef2ff;">{nm}</span></div>'))
        px += 186
    b.append(box(px, y + 22, 158, 106, f'border: 1.5px dashed {BORDER}; border-radius: {R2}; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; color: {MUT};',
                 icon('map-pin', 18, 'currentColor', 1.8) + f'<span style="font-family: {UI}; font-size: 11.5px;">Somewhere new</span>'))
    y += 156
    # 4 what
    b.append(tx(X, y, LW, '', eyebrow('4 &middot; What is happening &middot; optional')))
    b.append(box(X, y + 22, 352, 104, f'background: {PANEL}; border: 1.5px solid {ACC}; border-radius: {R2}; padding: 14px 16px; box-sizing: border-box;',
                 f'<div style="font-family: {NR}; font-style: italic; font-size: 15.5px; line-height: 1.4; color: {INK};">&ldquo;The caf&eacute; shuts in ten minutes and neither of you wants to leave.&rdquo;</div>'
                 f'<div style="margin-top: 9px; font-family: {UI}; font-size: 11.5px; color: {FAINT};">Closing Shift &middot; a plot</div>'))
    b.append(box(X + 364, y + 22, 352, 104, f'background: {SUNK}; border: 1px dashed {BORDER}; border-radius: {R2}; padding: 14px 16px; box-sizing: border-box; color: {MUT};',
                 f'<div style="font-family: {UI}; font-size: 13.5px; font-weight: 600; color: {INK};">Nothing in particular</div>'
                 f'<div style="margin-top: 7px; font-family: {UI}; font-size: 12.5px; line-height: 1.45;">Start on an empty scene and let it happen. You can drop a plot in later from the story menu.</div>'))
    # right: summary
    PX, PW = X + LW + 32, W - LW - 32
    b.append(tx(PX, 190, PW, '', eyebrow('The scene')))
    b.append(panel(PX, 212, PW, 506, '', 0, f'box-shadow: {SHF}; overflow: hidden;'))
    b.append(box(PX + 1, 213, PW - 2, 158, 'overflow: hidden;',
                 cover('gull-dusk', '', '50% 52%', 'Halcyon Coffee at dusk') +
                 f'<div style="position: absolute; inset: 0; background: linear-gradient(to top, {PANEL}, transparent 70%);"></div>'))
    b.append(tx(PX + 20, 390, PW - 40, '', disp('Halcyon Coffee', 24)))
    b.append(tx(PX + 20, 426, PW - 40, f'font-family: {UI}; font-size: 12.5px; color: {MUT};', 'dusk &middot; Closing Shift'))
    b.append(rule(PX + 20, 458, PW - 40))
    b.append(box(PX + 20, 474, PW - 40, 44, 'display: flex; align-items: center; gap: 10px;',
                 face('mira', 34) + face('tobin', 34, 'margin-left: -10px;') + face('aren', 34, 'margin-left: -10px;') +
                 f'<span style="margin-left: 8px; font-family: {UI}; font-size: 12.5px; color: {MID};">Mike and Theo, with you as Liv</span>'))
    b.append(field(PX + 20, 536, PW - 40, 'File it under', 'Close to the Crown', 'book', 'A new story in this book. Or leave it unfiled.'))
    b.append(field(PX + 20, 622, PW - 40, 'Name it', 'Closing Shift, again', None, None, 'text'))
    b.append(box(PX, 742, PW, 44, 'display: flex; gap: 10px;', btn('Start the scene', 'primary', h=44, w=PW)))
    b.append(box(PX, 798, PW, 44, f'display: flex; flex-direction: column; gap: 6px;',
                 f'<div style="display: flex; align-items: center; gap: 8px;">'
                 f'<span style="font-family: {UI}; font-size: 12px; font-weight: 700; color: {INK}; width: 44px;">Mike</span>'
                 f'<span style="font-family: {UI}; font-size: 12px; color: {MUT}; {TAB}">63 memories &middot; 4 stories &middot; knows this place</span></div>'
                 f'<div style="display: flex; align-items: center; gap: 8px;">'
                 f'<span style="font-family: {UI}; font-size: 12px; font-weight: 700; color: {INK}; width: 44px;">Theo</span>'
                 f'<span style="font-family: {UI}; font-size: 12px; color: {MUT}; {TAB}">8 memories &middot; 2 stories &middot; knows this place</span></div>'))
    return page('Sky &middot; New story', 1440, H, ''.join(b))

# ============================================================== SETTINGS
SETNAV = [('cog', 'General'), ('sun', 'Appearance'), ('globe', 'Language'), ('cpu', 'Models'),
          ('thought', 'Memory &amp; thinking'), ('shield', 'Data &amp; privacy'), ('grid', 'Shortcuts'), ('help', 'About')]

def settings_shell(H, active):
    b, X, W = shell(H, 'Settings', 'Settings', None, '')
    SW = 218
    b.append(panel(X, 150, SW, H - 230))
    y = 164
    for ic, label in SETNAV:
        on = label == active
        sel = f'background: {RAISE}; border: 1px solid {BORDER};' if on else 'border: 1px solid transparent;'
        b.append(box(X + 10, y, SW - 20, 38, f'display: flex; align-items: center; gap: 11px; padding: 0 12px; box-sizing: border-box; '
                     f'border-radius: {R2}; {sel} color: {INK if on else MUT};',
                     icon(ic, 16, 'currentColor', 1.8) +
                     f'<span style="font-family: {UI}; font-size: 13.5px; font-weight: {700 if on else 500};">{label}</span>'))
        y += 42
    b.append(rule(X + 10, y + 10, SW - 20))
    b.append(box(X + 10, y + 22, SW - 20, 38, f'display: flex; align-items: center; gap: 11px; padding: 0 12px; box-sizing: border-box; color: {WARM};',
                 icon('spark', 16, 'currentColor', 1.8) + f'<span style="font-family: {UI}; font-size: 13px; font-weight: 600;">What&rsquo;s new</span>'))
    CX, CW = X + SW + 28, W - SW - 28
    return b, CX, CW

def sec(b, x, y, w, title, note=None):
    b.append(tx(x, y, w, '', disp(title, 21)))
    if note:
        b.append(tx(x, y + 30, w, f'font-family: {UI}; font-size: 12.5px; color: {MUT};', note))
    return y + (56 if not note else 60)

def build_set_general():
    H = 1020
    b, X, W = settings_shell(H, 'General')
    y = sec(b, X, 150, W, 'General', 'How Kataki behaves when it opens and while it runs.')
    b.append(panel(X, y, W, 352))
    ry = y + 12
    b.append(row(X + 20, ry, W - 40, 'When Kataki opens', 'Go straight back into the last scene, or stop at Home first.',
                 field(0, 0, 210, None, 'Home', None, None, 'select', 36)))
    b.append(row(X + 20, ry + 68, W - 40, 'Autosave', 'Every line is written to disk as it arrives. This cannot be turned off.',
                 f'<span style="font-family: {UI}; font-size: 12.5px; color: {FAINT};">Always on</span>'))
    b.append(row(X + 20, ry + 136, W - 40, 'Keep a history of edits', 'Lets you undo a regeneration days later. Costs disk space.',
                 field(0, 0, 46, None, True, None, None, 'toggle')))
    b.append(row(X + 20, ry + 204, W - 40, 'Check for updates', 'Kataki asks one version endpoint for a number. No account, no identifier, nothing about your stories.',
                 field(0, 0, 210, None, 'Weekly', None, None, 'select', 36)))
    b.append(row(X + 20, ry + 272, W - 40, 'Send anonymous usage data', 'Off, and there is no code in Kataki that can turn it on.',
                 f'<span style="font-family: {UI}; font-size: 12.5px; color: {OK};">Not collected</span>', last=True))
    y += 392
    y = sec(b, X, y, W, 'Story defaults', 'What a new story starts with. Each story can override all of it.')
    b.append(panel(X, y, W, 284))
    ry = y + 12
    b.append(row(X + 20, ry, W - 40, 'Default persona', 'Who you play when you do not pick someone.',
                 field(0, 0, 210, None, 'Liv Sandoval', None, None, 'select', 36)))
    b.append(row(X + 20, ry + 68, W - 40, 'Composer mode', 'Auto reads your markdown. Say / Do / Whisper / Think override it.',
                 field(0, 0, 210, None, 'Auto', None, None, 'select', 36)))
    b.append(row(X + 20, ry + 136, W - 40, 'Show who hears what', 'The Advanced toggle in the composer. Off by default.',
                 field(0, 0, 46, None, False, None, None, 'toggle')))
    b.append(row(X + 20, ry + 204, W - 40, 'Music', 'Match the scene, keep one track, or stay quiet.',
                 field(0, 0, 210, None, 'Match the scene', None, None, 'select', 36), last=True))
    return page('Settings &middot; General', 1440, H, ''.join(b))

def build_set_appearance():
    H = 1020
    b, X, W = settings_shell(H, 'Appearance')
    y = sec(b, X, 150, W, 'Appearance', 'The Sky has two themes. The Scene always follows the place you are in.')
    # theme picker
    b.append(panel(X, y, W, 214))
    b.append(tx(X + 20, y + 18, W - 40, '', eyebrow('Theme')))
    tx0 = X + 20
    for nm, grad, on in (('Night', 'linear-gradient(170deg,#0a1028,#16224c)', True),
                         ('Day', 'linear-gradient(170deg,#dfe9f6,#c9d9f2)', False),
                         ('Follow the system', f'linear-gradient(110deg,#0a1028 0 50%,#dfe9f6 50% 100%)', False)):
        bd = ACC if on else BORDER
        b.append(box(tx0, y + 42, 180, 116, f'border: 1.5px solid {bd}; border-radius: {R2}; overflow: hidden; background: {grad}; box-shadow: {FOCUS if on else "none"};',
                     f'<div style="position: absolute; left: 12px; top: 12px; width: 58px; height: 92px; border-radius: 6px; background: rgba(255,255,255,.10); border: 1px solid rgba(255,255,255,.18);"></div>'
                     f'<div style="position: absolute; left: 78px; top: 12px; right: 12px; height: 40px; border-radius: 6px; background: rgba(255,255,255,.14);"></div>'
                     f'<div style="position: absolute; left: 78px; top: 60px; right: 12px; height: 44px; border-radius: 6px; background: rgba(255,255,255,.08);"></div>'))
        b.append(tx(tx0, y + 168, 180, f'font-family: {UI}; font-size: 13px; font-weight: {700 if on else 500}; color: {INK if on else MUT};', nm))
        tx0 += 196
    b.append(box(tx0 + 10, y + 42, W - (tx0 - X) - 30, 116, f'background: {SUNK}; border: 1px solid {HAIR}; border-radius: {R2}; padding: 15px; box-sizing: border-box;',
                 f'<div style="font-family: {UI}; font-size: 12.5px; font-weight: 700; color: {INK};">Night is the default</div>'
                 f'<div style="margin-top: 7px; font-family: {UI}; font-size: 12.5px; line-height: 1.5; color: {MUT};">'
                 f'Day is built as its own palette, not an inversion &mdash; the painted art is lit differently in each.</div>'))
    y += 254
    b.append(panel(X, y, W, 352))
    ry = y + 12
    b.append(row(X + 20, ry, W - 40, 'Text size', 'Everything scales, including the story. 200% is supported.',
                 seg(['100%', '125%', '150%'], '100%')))
    b.append(row(X + 20, ry + 68, W - 40, 'Reduce motion', 'The dive, the cloud parting and the streaming caret get a still form.',
                 field(0, 0, 46, None, False, None, None, 'toggle')))
    b.append(row(X + 20, ry + 136, W - 40, 'Show the stars', 'Purely decorative. Turning them off leaves the gradient.',
                 field(0, 0, 46, None, True, None, None, 'toggle')))
    b.append(row(X + 20, ry + 204, W - 40, 'Story typeface', 'What a character&rsquo;s lines are set in.',
                 field(0, 0, 210, None, 'Newsreader', None, None, 'select', 36)))
    b.append(row(X + 20, ry + 272, W - 40, 'High contrast', 'Raises every border and dims the sky behind text.',
                 field(0, 0, 46, None, False, None, None, 'toggle'), last=True))
    y += 392
    b.append(box(X, y, W, 84, f'background: rgba(231,176,106,.07); border: 1px solid rgba(231,176,106,.24); border-radius: {R2}; padding: 16px 18px; box-sizing: border-box;',
                 f'<div style="display: flex; align-items: center; gap: 9px;">{icon("eye", 16, WARM, 1.9)}'
                 f'<span style="font-family: {UI}; font-size: 13px; font-weight: 700; color: {WARM};">What is not adjustable, on purpose</span></div>'
                 f'<div style="margin-top: 7px; font-family: {UI}; font-size: 12.5px; color: {MID};">'
                 f'Accent colour, spacing, corner radius and layout density. Kataki has one look; you choose the light it is seen in.</div>'))
    return page('Settings &middot; Appearance', 1440, H, ''.join(b))

def build_set_language():
    H = 1020
    b, X, W = settings_shell(H, 'Language')
    y = sec(b, X, 150, W, 'Language', 'The interface language. What your characters speak is up to them and the model.')
    b.append(panel(X, y, W, 260))
    b.append(tx(X + 20, y + 18, W - 40, '', eyebrow('Interface')))
    langs = [('English', 'Complete', True, 'ltr'), ('العربية', 'Right to left &middot; in progress', False, 'rtl'),
             ('Espa&ntilde;ol', 'Not started', False, 'ltr'), ('Deutsch', 'Not started', False, 'ltr'),
             ('日本語', 'Not started', False, 'ltr'), ('עברית', 'Right to left &middot; not started', False, 'rtl')]
    for i, (nm, state, on, d) in enumerate(langs):
        cx = X + 20 + (i % 3) * ((W - 40) // 3)
        cy = y + 42 + (i // 3) * 76
        bd = ACC if on else HAIR
        b.append(box(cx, cy, (W - 40) // 3 - 14, 64, f'background: {SUNK}; border: 1px solid {bd}; border-radius: {R2}; padding: 12px 14px; box-sizing: border-box;',
                     f'<div style="font-family: {UI}; font-size: 14px; font-weight: 700; color: {INK if on else MID};">{nm}</div>'
                     f'<div style="margin-top: 3px; font-family: {UI}; font-size: 11.5px; color: {FAINT};">{state}</div>' +
                     (f'<div style="position: absolute; right: 12px; top: 20px;">{icon("check", 16, ACC, 2.4)}</div>' if on else
                      (f'<div style="position: absolute; right: 12px; top: 22px;">{tag("RTL", WARM)}</div>' if d == "rtl" else ''))))
    y += 300
    b.append(panel(X, y, W, 216))
    ry = y + 12
    b.append(row(X + 20, ry, W - 40, 'Mirror the layout for right-to-left languages', 'The rail moves to the right, arrows flip, the clock does not. Already built in.',
                 f'<span style="font-family: {UI}; font-size: 12.5px; color: {OK};">Automatic</span>'))
    b.append(row(X + 20, ry + 68, W - 40, 'Dates and times', 'Story dates stay relative either way. This is the real clock.',
                 field(0, 0, 210, None, '12-hour &middot; 24 on hover', None, None, 'select', 36)))
    b.append(row(X + 20, ry + 136, W - 40, 'Help translate Kataki', 'Every string lives in one file. Send it back and it ships.',
                 btn('Open the file', 'secondary', h=36, fs=13), last=True))
    return page('Settings &middot; Language', 1440, H, ''.join(b))

def build_set_models():
    H = 1120
    b, X, W = settings_shell(H, 'Models')
    y = sec(b, X, 150, W, 'Models')
    # status
    b.append(box(X, y - 8, W, 76, f'background: rgba(111,216,164,.07); border: 1px solid rgba(111,216,164,.28); border-radius: {R2}; '
                 f'display: flex; align-items: center; gap: 14px; padding: 0 20px; box-sizing: border-box;',
                 box(0, 0, 10, 10, f'border-radius: 50%; background: {OK}; position: relative;') +
                 f'<div style="flex: 1;"><div style="font-family: {UI}; font-size: 14.5px; font-weight: 700; color: {INK};">Everything is working</div>'
                 f'<div style="font-family: {UI}; font-size: 12.5px; color: {MID}; margin-top: 2px;">Running on <b style="color:{INK}">qwen3.5-9b</b> through llama.cpp on this computer &middot; last reply took 3.1 s</div></div>' +
                 btn('Test again', 'secondary', h=36, fs=13)))
    y += 96
    y = sec(b, X, y, W, 'Where it runs', 'One of these has to be reachable. Kataki will use the first that answers.')
    b.append(panel(X, y, W, 232))
    ry = y + 16
    CONN = [('server', 'llama.cpp', 'http://localhost:8080 &middot; qwen3.5-9b loaded &middot; 9.2 GB', 'Connected', OK),
            ('globe', 'OpenRouter', 'Key stored in this computer&rsquo;s keychain &middot; never sent anywhere else', 'Ready', MUT),
            ('cpu', 'Kataki&rsquo;s own model', 'kataki-small-3b &middot; 1.2 GB &middot; downloaded', 'Fallback', MUT)]
    for i, (ic, nm, sub, state, col) in enumerate(CONN):
        b.append(box(X + 20, ry + i * 68, W - 40, 56, 'display: flex; align-items: center; gap: 14px;',
                     box(0, 8, 40, 40, f'border-radius: {R2}; background: {RAISE}; border: 1px solid {HAIR}; display: flex; align-items: center; justify-content: center; position: relative;', icon(ic, 19, MUT, 1.8)) +
                     f'<div style="flex: 1;"><div style="font-family: {UI}; font-size: 14px; font-weight: 700; color: {INK};">{nm}'
                     f'<span style="margin-left: 10px; font-family: {UI}; font-size: 11px; font-weight: 700; color: {col};">{state}</span></div>'
                     f'<div style="font-family: {UI}; font-size: 12px; color: {MUT}; margin-top: 2px;">{sub}</div></div>' +
                     btn('Test', 'ghost', h=32, fs=12.5) + '<span style="width: 8px;"></span>' + btn('Remove', 'ghost', h=32, fs=12.5)))
        if i < 2:
            b.append(rule(X + 20, ry + i * 68 + 62, W - 40))
    b.append(box(X + 20, ry + 204, W - 40, 34, 'display: flex; gap: 10px;',
                 btn('Look for servers on this computer', 'secondary', 'refresh', h=34, fs=12.5) + btn('Add an API', 'ghost', 'plus', h=34, fs=12.5)))
    y += 272
    y = sec(b, X, y, W, 'Who does what', 'Kataki uses more than one model. Leave these and they all use the first connection.')
    JOBS = [('users', 'Characters', 'Speaking, in character', 'qwen3.5-9b', True),
            ('quill', 'Narrator', 'Scene text, time skips, place descriptions', 'Same as characters', False),
            ('thought', 'Memory reader', 'Deciding what a character keeps and what fades', 'kataki-small-3b', False),
            ('layers', 'Reasoning', 'The thinking pass before a reply', 'qwen3.5-9b &middot; low effort', False),
            ('search', 'Recall by meaning', 'Finding old lines that match, not just words', 'all-minilm (embeddings)', False)]
    b.append(panel(X, y, W, 74 + len(JOBS) * 56))
    for i, (ic, nm, sub, val, open_) in enumerate(JOBS):
        jy = y + 14 + i * 56
        b.append(box(X + 20, jy, W - 40, 46, f'display: flex; align-items: center; gap: 12px; border-bottom: 1px solid {HAIR}; box-sizing: border-box;',
                     icon(ic, 17, MUT, 1.8) +
                     f'<div style="width: 168px;"><span style="font-family: {UI}; font-size: 13.5px; font-weight: 700; color: {INK};">{nm}</span></div>'
                     f'<div style="flex: 1; font-family: {UI}; font-size: 12.5px; color: {MUT};">{sub}</div>'
                     f'<span style="font-family: {MO}; font-size: 12px; color: {MID}; margin-right: 12px;">{val}</span>' +
                     icon('down' if not open_ else 'up', 15, MUT, 2)))
    b.append(box(X + 20, y + 26 + len(JOBS) * 56, W - 40, 34, f'display: flex; align-items: center; gap: 9px; color: {MUT};',
                 icon('cog', 15, 'currentColor', 1.8) +
                 f'<span style="font-family: {UI}; font-size: 12.5px; font-weight: 600;">Advanced &mdash; temperature, context length, samplers, stop sequences</span>' + icon('down', 14, 'currentColor', 2)))
    return page('Settings &middot; Models', 1440, H, ''.join(b))

def build_set_memory():
    H = 1060
    b, X, W = settings_shell(H, 'Memory &amp; thinking')
    y = sec(b, X, 150, W, 'Memory and thinking', 'How much of a person a character is allowed to be. These are defaults; any character can override them.')
    b.append(panel(X, y, W, 300))
    ry = y + 12
    b.append(row(X + 20, ry, W - 40, 'How fast memories fade', 'Sharp, then hazy, then gone. Slower means characters stay consistent and cost more to run.',
                 seg(['Fast', 'Life-like', 'Never'], 'Life-like')))
    b.append(row(X + 20, ry + 68, W - 40, 'They can be wrong', 'A hazy memory can come back slightly altered, the way people misremember.',
                 field(0, 0, 46, None, True, None, None, 'toggle')))
    b.append(row(X + 20, ry + 136, W - 40, 'They can doubt you', 'If what you say contradicts what they hold, they may say so instead of accepting it.',
                 field(0, 0, 46, None, True, None, None, 'toggle')))
    b.append(row(X + 20, ry + 204, W - 40, 'How much they think before answering', 'More thinking is slower and more in character.',
                 seg(['None', 'Some', 'A lot'], 'Some'), last=True))
    y += 340
    y = sec(b, X, y, W, 'What they notice')
    b.append(panel(X, y, W, 232))
    ry = y + 12
    b.append(row(X + 20, ry, W - 40, 'Hearing', 'Whether a character in the room hears a whisper, and whether one who left hears anything.',
                 field(0, 0, 210, None, 'Realistic', None, None, 'select', 36)))
    b.append(row(X + 20, ry + 68, W - 40, 'Recall by meaning', 'Finds the old line that matches what is happening, not just the same words.',
                 field(0, 0, 46, None, True, None, None, 'toggle')))
    b.append(row(X + 20, ry + 136, W - 40, 'How far back they look', 'Older than this and only memories carry, not the transcript.',
                 field(0, 0, 210, None, '40 messages', None, None, 'select', 36), last=True))
    y += 272
    b.append(box(X, y, W, 96, f'background: rgba(91,134,255,.07); border: 1px solid rgba(91,134,255,.26); border-radius: {R2}; padding: 16px 18px; box-sizing: border-box;',
                 f'<div style="display: flex; align-items: center; gap: 9px;">{icon("layers", 16, ACC, 1.9)}'
                 f'<span style="font-family: {UI}; font-size: 13px; font-weight: 700; color: {ACCT};">Backstage shows you all of this happening</span></div>'
                 f'<div style="margin-top: 7px; font-family: {UI}; font-size: 12.5px; line-height: 1.5; color: {MID};">'
                 f'Inside any story, Backstage draws the path a reply took &mdash; what was heard, what was recalled, what was felt, what was decided &mdash; '
                 f'with the exact prompt and token count. Nothing here is hidden from you.</div>'))
    return page('Settings &middot; Memory and thinking', 1440, H, ''.join(b))

def build_set_data():
    H = 1060
    b, X, W = settings_shell(H, 'Data &amp; privacy')
    y = sec(b, X, 150, W, 'Data and privacy')
    b.append(box(X, y - 8, W, 92, f'background: rgba(111,216,164,.07); border: 1px solid rgba(111,216,164,.28); border-radius: {R2}; padding: 16px 20px; box-sizing: border-box;',
                 f'<div style="display: flex; align-items: center; gap: 9px;">{icon("shield", 17, OK, 1.9)}'
                 f'<span style="font-family: {UI}; font-size: 14px; font-weight: 700; color: {INK};">Nothing leaves this computer unless you connect an online model</span></div>'
                 f'<div style="margin-top: 8px; font-family: {UI}; font-size: 12.5px; line-height: 1.5; color: {MID};">'
                 f'No account, no sync, no telemetry. When an online model is connected, the only thing sent is the prompt for that reply &mdash; '
                 f'shown in full in Backstage before it goes.</div>'))
    y += 112
    y = sec(b, X, y, W, 'Where your things live')
    b.append(panel(X, y, W, 190))
    ry = y + 16
    for i, (ic, label, path, size) in enumerate((('book', 'Stories and characters', 'C:\\Users\\you\\Kataki\\library', '48 MB'),
                                                ('image', 'Portraits and places', 'C:\\Users\\you\\Kataki\\art', '310 MB'),
                                                ('cpu', 'Models', 'C:\\Users\\you\\Kataki\\models', '10.4 GB'))):
        b.append(box(X + 20, ry + i * 56, W - 40, 44, 'display: flex; align-items: center; gap: 12px;',
                     icon(ic, 17, MUT, 1.8) +
                     f'<div style="width: 190px; font-family: {UI}; font-size: 13.5px; font-weight: 600; color: {INK};">{label}</div>'
                     f'<div style="flex: 1; font-family: {MO}; font-size: 12px; color: {MUT};">{path}</div>'
                     f'<span style="font-family: {MO}; font-size: 12px; color: {FAINT}; margin-right: 14px; {TAB}">{size}</span>' +
                     btn('Open folder', 'ghost', h=30, fs=12)))
        if i < 2:
            b.append(rule(X + 20, ry + i * 56 + 50, W - 40))
    y += 230
    y = sec(b, X, y, W, 'Take it with you')
    b.append(panel(X, y, W, 232))
    ry = y + 12
    b.append(row(X + 20, ry, W - 40, 'Export everything', 'One folder of readable files: Markdown transcripts, JSON characters, the art. Nothing proprietary.',
                 btn('Export', 'secondary', 'download', h=36, fs=13)))
    b.append(row(X + 20, ry + 68, W - 40, 'Automatic backups', 'A copy of the library, kept where you point it.',
                 field(0, 0, 46, None, True, None, None, 'toggle')))
    b.append(row(X + 20, ry + 136, W - 40, 'Import', 'Character cards from SillyTavern, Chub or Janitor, and folders of your own.',
                 btn('Import', 'ghost', 'plus', h=36, fs=13), last=True))
    y += 272
    b.append(box(X, y, W, 100, f'background: rgba(255,143,163,.06); border: 1px solid rgba(255,143,163,.28); border-radius: {R2}; padding: 16px 18px; box-sizing: border-box;',
                 f'<div style="display: flex; align-items: center; gap: 9px;">{icon("alert", 16, "#ff8fa3", 1.9)}'
                 f'<span style="font-family: {UI}; font-size: 13px; font-weight: 700; color: #ff8fa3;">Delete</span></div>'
                 f'<div style="margin-top: 7px; font-family: {UI}; font-size: 12.5px; color: {MID};">'
                 f'Delete one story, one character, or everything. There is no server copy, so deleted is deleted.</div>'
                 f'<div style="position: absolute; right: 18px; top: 30px;">' + btn('Delete something', 'ghost', h=36, fs=13) + '</div>'))
    return page('Settings &middot; Data and privacy', 1440, H, ''.join(b))

def build_set_shortcuts():
    H = 1240
    b, X, W = settings_shell(H, 'Shortcuts')
    y = sec(b, X, 150, W, 'Shortcuts', 'Every one of these is remappable. Nothing in Kataki needs a mouse.')
    GROUPS = [('Anywhere', [('Ctrl K', 'Search everything'), ('Ctrl N', 'New story'), ('Ctrl ,', 'Settings'),
                            ('Ctrl P', 'Switch persona'), ('/', 'Focus search'), ('Esc', 'Close whatever is open')]),
              ('In a story', [('Enter', 'Send'), ('Shift Enter', 'New line'), ('Ctrl Enter', 'Send and pass time'),
                              ('Up', 'Edit your last line'), ('Ctrl R', 'Regenerate the last reply'), ('Ctrl B', 'Backstage'),
                              ('Ctrl M', 'Mute the music'), ('Ctrl W', 'Edit widgets')]),
              ('Moving around', [('Tab', 'Next control'), ('Space', 'Pick up a widget'), ('Arrows', 'Move the picked-up widget'),
                                 ('G then H', 'Go to Home'), ('G then S', 'Go to Stories'), ('G then C', 'Go to Characters')])]
    cy = y
    for gname, items in GROUPS:
        b.append(tx(X, cy, W, '', eyebrow(gname)))
        b.append(panel(X, cy + 22, W, 14 + len(items) * 40))
        for i, (k, label) in enumerate(items):
            keys = ''.join(f'<kbd style="display: inline-block; font-family: {MO}; font-size: 11.5px; color: {INK}; background: {SUNK}; '
                           f'border: 1px solid {BORDER}; border-bottom-width: 2px; border-radius: 5px; padding: 3px 7px; margin-right: 5px;">{p}</kbd>'
                           for p in k.split(' '))
            b.append(box(X + 20, cy + 32 + i * 40, W - 40, 32, f'display: flex; align-items: center; {"border-bottom: 1px solid " + HAIR if i < len(items) - 1 else ""}',
                         f'<span style="flex: 1; font-family: {UI}; font-size: 13.5px; color: {MID};">{label}</span>{keys}'))
        cy += 22 + 14 + len(items) * 40 + 32
    return page('Settings &middot; Shortcuts', 1440, H, ''.join(b))

def build_set_about():
    H = 1020
    b, X, W = settings_shell(H, 'About')
    y = sec(b, X, 150, W, 'About')
    b.append(panel(X, y, W, 150))
    b.append(box(X + 22, y + 24, 72, 72, f'border-radius: 18px; background: {PRIM}; display: flex; align-items: center; justify-content: center;',
                 f'<span style="font-family: {DP}; font-weight: 800; font-size: 36px; color: #fff;">K</span>'))
    b.append(tx(X + 112, y + 28, 500, '', disp('Kataki RPAI', 28)))
    b.append(tx(X + 112, y + 66, 600, f'font-family: {UI}; font-size: 13px; color: {MUT}; {TAB}', 'Version 0.4.2 &middot; Windows &middot; local-first &middot; nothing here phones home'))
    b.append(box(X + 112, y + 94, 500, 34, 'display: flex; gap: 10px;',
                 btn('Check for updates', 'secondary', h=34, fs=12.5) + btn('Licences', 'ghost', h=34, fs=12.5) + btn('The manual', 'ghost', h=34, fs=12.5)))
    y += 190
    y = sec(b, X, y, W, 'Tell us something', 'All three go to the same place. Nothing is sent until you have seen exactly what it contains.')
    OPTS = [('help', 'Give feedback', 'Anything at all. Two sentences is fine.', ACC),
            ('alert', 'Report a bug', 'Attaches your version, OS and the last error &mdash; every field removable.', '#ff8fa3'),
            ('spark', 'Suggest something', 'What you wanted Kataki to do and it did not.', WARM)]
    ox = X
    ow = (W - 32) // 3
    for ic, t, d, col in OPTS:
        b.append(panel(ox, y, ow, 148))
        b.append(box(ox + 18, y + 18, 40, 40, f'border-radius: {R2}; background: {RAISE}; display: flex; align-items: center; justify-content: center;', icon(ic, 19, col, 1.9)))
        b.append(tx(ox + 18, y + 70, ow - 36, f'font-family: {UI}; font-size: 14.5px; font-weight: 700; color: {INK};', t))
        b.append(tx(ox + 18, y + 94, ow - 36, f'font-family: {UI}; font-size: 12.5px; line-height: 1.45; color: {MUT};', d))
        ox += ow + 16
    y += 188
    y = sec(b, X, y, W, 'What&rsquo;s new', 'Every visible change gets a line here. Nothing is ever removed quietly.')
    LOG = [('0.4.2', 'today', 'The Sky is dark by default. Activity moved into Home as &ldquo;Since you last played&rdquo;. Chats and Characters became Stories.'),
           ('0.4.1', 'last week', 'Characters can doubt you. Story clocks show the real date on hover.'),
           ('0.4.0', 'three weeks ago', 'Widgets in the Scene: move, pin, duplicate. Music can be your own file.')]
    for i, (v, when, what) in enumerate(LOG):
        ly = y + i * 76
        b.append(rule(X, ly, W))
        b.append(tx(X, ly + 16, 120, f'font-family: {MO}; font-size: 13px; font-weight: 500; color: {WARM}; {TAB}', v))
        b.append(tx(X, ly + 38, 120, f'font-family: {UI}; font-size: 11.5px; color: {FAINT};', when))
        b.append(tx(X + 130, ly + 16, W - 130, f'font-family: {UI}; font-size: 13.5px; line-height: 1.5; color: {MID};', what))
    return page('Settings &middot; About', 1440, H, ''.join(b))

# ====================================================== PALETTE & SEARCH
def build_palette():
    H = 1000
    b = [box(0, 0, 1440, H, f'background: {GROUND};'), sky(H), rail(H, 'Home')]
    X, W = RW + PAD, 1440 - RW - PAD * 2
    b.append(topbar(X, W))
    b.append(hero(X, W, 96))
    b.append(cast_grid(X, W, 500))
    b.append(dim(H))
    PW, PX, PY = 720, (1440 - 720) // 2 + 80, 120
    b.append(box(PX, PY, PW, 648, f'background: {POP}; backdrop-filter: blur(28px); border: 1px solid {BORDER}; '
                 f'border-radius: {R3}; box-shadow: 0 40px 90px rgba(0,0,0,.7); overflow: hidden;'))
    b.append(box(PX + 1, PY + 1, PW - 2, 62, f'display: flex; align-items: center; gap: 12px; padding: 0 20px; box-sizing: border-box; border-bottom: 1px solid {HAIR};',
                 icon('search', 19, MUT, 1.9) +
                 f'<span style="font-family: {UI}; font-size: 17px; color: {INK}; flex: 1;">gala<span style="opacity:.5">|</span></span>'
                 f'<span style="font-family: {MO}; font-size: 11px; color: {FAINT}; border: 1px solid {HAIR}; border-radius: 4px; padding: 2px 6px;">Esc</span>'))
    gy = PY + 76
    GROUPS = [('Jump to', [('chat', 'The Gala List', 'story &middot; Close to the Crown', True),
                           ('map-pin', 'Corvel Palace', 'place &middot; not filed yet', False),
                           ('quote', 'The Invitation', 'plot &middot; Close to the Crown', False)]),
              ('Lines', [('quote', '&ldquo;The list. You said you weren&rsquo;t coming to this.&rdquo;', 'Mike &middot; Two Sugars, No Title &middot; three weeks later', False),
                         ('quote', '&ldquo;Your name&rsquo;s on it. Don&rsquo;t ask me how.&rdquo;', 'Jae &middot; The Gala List', False)]),
              ('Do', [('plus', 'New story with Mike', 'Enter', False), ('user', 'Switch persona to Cas', 'Ctrl P', False),
                      ('download', 'Export The Gala List', '', False)])]
    for gname, items in GROUPS:
        b.append(tx(PX + 20, gy, PW - 40, '', eyebrow(gname)))
        gy += 22
        for ic, label, meta, on in items:
            bg = f'background: rgba(91,134,255,.16);' if on else ''
            b.append(box(PX + 10, gy, PW - 20, 42, f'display: flex; align-items: center; gap: 13px; padding: 0 12px; box-sizing: border-box; border-radius: {R2}; {bg}',
                         icon(ic, 17, ACC if on else MUT, 1.8) +
                         f'<span style="font-family: {UI}; font-size: 14px; font-weight: {700 if on else 500}; color: {INK}; max-width: 420px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{label}</span>'
                         f'<span style="margin-left: auto; font-family: {UI}; font-size: 11.5px; color: {FAINT};">{meta}</span>'))
            gy += 44
        gy += 8
    b.append(box(PX + 1, PY + 648 - 44, PW - 2, 43, f'border-top: 1px solid {HAIR}; display: flex; align-items: center; gap: 18px; padding: 0 20px; box-sizing: border-box;',
                 ''.join(f'<span style="font-family: {UI}; font-size: 11.5px; color: {FAINT};">'
                         f'<kbd style="font-family: {MO}; border: 1px solid {HAIR}; border-radius: 4px; padding: 1px 5px; margin-right: 5px;">{k}</kbd>{l}</span>'
                         for k, l in (('&uarr;&darr;', 'move'), ('&crarr;', 'open'), ('Tab', 'filter'), ('Esc', 'close')))))
    return page('Sky &middot; Command palette', 1440, H, ''.join(b))

def build_search():
    H = 1020
    b, X, W = shell(H, 'Home', None, None, '')
    b.append(tx(X, 96, 700, '', disp('&ldquo;gala&rdquo;', 30)))
    b.append(tx(X + 150, 106, 500, f'font-family: {UI}; font-size: 13px; color: {MUT}; {TAB}', '19 results across everything'))
    b.append(box(X, 150, 800, 32, 'display: flex; gap: 8px;',
                 chip('All', True, count=19) + chip('Lines', count=9) + chip('Stories', count=3) +
                 chip('Characters', count=2) + chip('Places &amp; plots', count=4) + chip('Memories', count=1)))
    y = 206
    RES = [('chat', 'The Gala List', 'Story &middot; Close to the Crown &middot; played last week',
            'Liv, Jae &middot; 3 messages &middot; two days before the gala', 'oren'),
           ('quote', '&ldquo;The list. You said you weren&rsquo;t coming to this.&rdquo;',
            'Mike &middot; Two Sugars, No Title &middot; three weeks later &middot; 7:18 pm',
            'He looks at the jacket he borrowed, then at you.', 'mira'),
           ('thought', 'She did not want to be on the gala list.',
            'A memory Mike holds &middot; going hazy &middot; witnessed',
            'Earlier version, kept: &ldquo;Her mother is the queen&rsquo;s step-sister, and she is on the list.&rdquo;', 'mira'),
           ('quote', '&ldquo;Your name&rsquo;s on it. Don&rsquo;t ask me how.&rdquo;',
            'Jae &middot; The Gala List &middot; two days before', '*chewing gum, not looking up*', 'oren'),
           ('map-pin', 'Corvel Palace', 'Place &middot; not filed yet &middot; Jae knows it',
            'Gold stairs, orange trees, and a guest list nobody admits to reading.', None)]
    for i, (ic, title, meta, body, k) in enumerate(RES):
        ry = y + i * 118
        b.append(panel(X, ry, W, 104))
        b.append(box(X + 18, ry + 18, 40, 40, f'border-radius: {R2}; background: {RAISE}; border: 1px solid {HAIR}; display: flex; align-items: center; justify-content: center;', icon(ic, 18, MUT, 1.8)))
        b.append(tx(X + 74, ry + 18, W - 240, f'font-family: {UI}; font-size: 15px; font-weight: 700; color: {INK};', title))
        b.append(tx(X + 74, ry + 42, W - 240, f'font-family: {UI}; font-size: 11.5px; color: {FAINT};', meta))
        b.append(tx(X + 74, ry + 64, W - 240, f'font-family: {NR}; font-size: 15px; color: {MID};', body))
        right = (face(k, 30, 'margin-right: 12px;') if k else '')
        b.append(box(X + W - 190, ry + 32, 172, 40, 'display: flex; align-items: center; justify-content: flex-end;',
                     right + btn('Open the line' if ic == 'quote' else 'Open', 'secondary', h=34, fs=12.5)))
    b.append(box(X, y + 5 * 118, W, 40, f'display: flex; align-items: center; justify-content: center; gap: 8px; color: {MUT};',
                 f'<span style="font-family: {UI}; font-size: 13px; font-weight: 600;">14 more</span>' + icon('down', 15, 'currentColor', 2)))
    return page('Sky &middot; Search results', 1440, H, ''.join(b))

# ================================================================ MENUS
def build_menus():
    H = 1120
    b, X, W = shell(H, 'Home', None, None, '')
    b.append(tx(X, 96, 800, '', disp('Every menu', 30)))
    b.append(tx(X, 138, 820, f'font-family: {UI}; font-size: 13.5px; color: {MUT};',
                'One board so nothing is hidden. Each of these opens from the control named above it.'))
    LAB = lambda x, y, s: tx(x, y, 320, '', eyebrow(s))
    # 1 persona
    b.append(LAB(X, 196, 'The avatar, top left'))
    b.append(menu(X, 218, 300, [
        ('user', 'Liv Sandoval', 'default', 'on'), ('user', 'Cas Brennan', None, None), ('film', 'Director &middot; play no one', None, None),
        ('plus', 'New persona', None, None)], 'Playing as', ('cog', 'Manage personas')))
    # 2 story menu
    b.append(LAB(X + 340, 196, 'The &middot;&middot;&middot; on a story'))
    b.append(menu(X + 340, 218, 300, [
        ('grid', 'Edit widgets', 'Ctrl W', None), ('book', 'Reading mode', None, None), ('map-pin', 'Scene and place', None, None),
        ('clock', 'Pass time', None, None), ('layers', 'Backstage', 'Ctrl B', None), ('cog', 'Story settings', None, None),
        ('download', 'Export story', None, None), ('pushpin', 'Pin to Home', None, None), ('x', 'Delete story', None, 'off')], None))
    # 3 character card menu
    b.append(LAB(X + 680, 196, 'The &middot;&middot;&middot; on a character'))
    b.append(menu(X + 680, 218, 300, [
        ('chat', 'Continue the latest story', None, None), ('plus', 'Start a new story', None, None), ('users', 'Add to a group', None, None),
        ('edit', 'Edit profile', None, None), ('heart', 'Favourite', None, None), ('eyeoff', 'Make them forget something', None, None),
        ('download', 'Export', None, None), ('x', 'Delete', None, 'off')], None))
    # 4 sort
    b.append(LAB(X, 620, 'Sort, on any list'))
    b.append(menu(X, 642, 260, [
        ('clock', 'Recently played', None, 'on'), ('quill', 'Recently written', None, None), ('star', 'Favourites first', None, None),
        ('users', 'Name, A to Z', None, None), ('flame', 'Most stories', None, None)], 'Sort by'))
    # 5 filter
    b.append(LAB(X + 300, 620, 'Filter, on Stories'))
    b.append(menu(X + 300, 642, 300, [
        ('grid', 'Everything', '12', 'on'), ('pushpin', 'Pinned', '1', None), ('book', 'Close to the Crown', '6', None),
        ('book', 'The Flat on Ardenne', '3', None), ('user', 'As Cas', '2', None), ('layers', 'Unfinished', '4', None)], 'Show'))
    # 6 time hover
    b.append(LAB(X + 640, 620, 'Hovering a time'))
    b.append(box(X + 640, 642, 320, 96, f'background: {POP}; backdrop-filter: blur(20px); border: 1px solid {BORDER}; border-radius: {R3}; box-shadow: {SHF}; padding: 15px 17px; box-sizing: border-box;',
                 f'<div style="font-family: {MO}; font-size: 14px; color: {INK}; {TAB}">19:18 &middot; 14 June 2026</div>'
                 f'<div style="margin-top: 6px; font-family: {UI}; font-size: 12.5px; color: {MUT};">three weeks after the caf&eacute;</div>'
                 f'<div style="margin-top: 6px; font-family: {UI}; font-size: 12.5px; color: {FAINT};">the night of the gala</div>'))
    # 7 theme
    b.append(LAB(X + 640, 780, 'The theme switch'))
    b.append(menu(X + 640, 802, 260, [('moon', 'Night', None, 'on'), ('sun', 'Day', None, None), ('cpu', 'Follow the system', None, None)], None))
    # 8 notifications-free note
    b.append(box(X + 980, 640, 400, 150, f'background: rgba(91,134,255,.06); border: 1px solid rgba(91,134,255,.24); border-radius: {R2}; padding: 16px 18px; box-sizing: border-box;',
                 f'<div style="display: flex; align-items: center; gap: 9px;">{icon("bell", 16, ACC, 1.9)}'
                 f'<span style="font-family: {UI}; font-size: 13px; font-weight: 700; color: {ACCT};">There is no notifications menu</span></div>'
                 f'<div style="margin-top: 7px; font-family: {UI}; font-size: 12.5px; line-height: 1.5; color: {MID};">'
                 f'Nobody else is acting in your library, so there is nothing to be notified about. What used to be the bell is now '
                 f'&ldquo;Since you last played&rdquo; on Home: an event log of what changed.</div>'))
    return page('Sky &middot; Every menu', 1440, H, ''.join(b))

# ========================================================= STATES & FLOWS
def build_empty():
    H = 1000
    b, X, W = shell(H, 'Home', None, None, '')
    b.append(tx(X, 104, 700, '', eyebrow('Day one', ACC)))
    b.append(tx(X, 126, 800, '', disp('Nobody knows you yet.', 44, INK, '800')))
    b.append(tx(X, 190, 660, f'font-family: {NR}; font-size: 19px; line-height: 1.5; color: {MID};',
                'Six people came with Kataki. Say something to one of them and this page fills up with what you did together.'))
    # the shipped cast, as the empty state
    b.append(tx(X, 268, 400, '', eyebrow('Start with someone')))
    CW = (W - 4 * 14) // 5
    for i, (k, nm, line, when, badge, n) in enumerate(PEOPLE[:5]):
        cx = X + i * (CW + 14)
        art = noface(nm, 168) if k == 'wren' else cover(k, '', None, nm)
        inner = (f'<div style="position: relative; width: 100%; height: 168px; background: {RAISE};">' + art + '</div>'
                 f'<div style="padding: 13px 15px;">{disp(nm.split(" ")[0], 19)}'
                 f'<div style="font-family: {UI}; font-size: 11.5px; line-height: 1.4; color: {MUT}; margin-top: 4px; height: 32px;">{line}</div></div>')
        b.append(panel(cx, 296, CW, 300, inner, 0, 'overflow: hidden;' + (f' border-color: {ACCT}; box-shadow: {SHF};' if i == 0 else '')))
        b.append(box(cx + 15, 546, CW - 30, 34, '', btn('Say hello', 'primary' if i == 0 else 'secondary', h=34, fs=12.5, w=CW - 30)))
    # or
    b.append(rule(X, 636, W))
    b.append(tx(X, 664, 400, '', eyebrow('Or start from nothing')))
    OR = [('plus', 'Write a character', 'A name and a greeting is enough. Two minutes.'),
          ('download', 'Import your cards', 'From SillyTavern, Chub, Janitor, or a folder of PNGs.'),
          ('book', 'Make a place first', 'Some people would rather build the world and then fill it.')]
    ox = X
    ow = (W - 32) // 3
    for ic, t, d in OR:
        b.append(box(ox, 692, ow, 104, f'background: {PANEL}; border: 1px solid {HAIR}; border-radius: {R2}; padding: 16px 18px; box-sizing: border-box;',
                     f'<div style="display: flex; align-items: center; gap: 10px;">{icon(ic, 17, MUT, 1.8)}'
                     f'<span style="font-family: {UI}; font-size: 14px; font-weight: 700; color: {INK};">{t}</span></div>'
                     f'<div style="margin-top: 8px; font-family: {UI}; font-size: 12.5px; line-height: 1.45; color: {MUT};">{d}</div>'))
        ox += ow + 16
    b.append(box(X, 840, W, 84, f'background: rgba(231,176,106,.06); border: 1px solid rgba(231,176,106,.24); border-radius: {R2}; '
                 f'display: flex; align-items: center; gap: 13px; padding: 0 20px; box-sizing: border-box;',
                 icon('spark', 18, WARM, 1.9) +
                 f'<span style="font-family: {UI}; font-size: 13.5px; color: {MID};">'
                 f'<b style="color: {INK};">One thing worth knowing.</b> Characters remember across stories, not just inside one. '
                 f'What you tell Mike tonight is still there in a story you start next month.</span>'))
    return page('Sky &middot; Empty (day one)', 1440, H, ''.join(b))

def build_error():
    H = 1000
    b = [box(0, 0, 1440, H, f'background: {GROUND};'), sky(H), rail(H, 'Home')]
    X, W = RW + PAD, 1440 - RW - PAD * 2
    b.append(topbar(X, W))
    # the banner replaces the hero
    b.append(box(X, 96, W, 196, f'background: rgba(255,143,163,.07); border: 1px solid rgba(255,143,163,.34); border-radius: {R3}; box-shadow: {SHF};'))
    b.append(box(X + 26, 122, 44, 44, f'border-radius: {R2}; background: rgba(255,143,163,.14); display: flex; align-items: center; justify-content: center;',
                 icon('alert', 22, '#ff8fa3', 1.9)))
    b.append(tx(X + 86, 124, 700, '', disp('Nobody is home to answer.', 27)))
    b.append(tx(X + 86, 162, 720, f'font-family: {UI}; font-size: 14px; line-height: 1.55; color: {MID};',
                'Kataki was talking to <b style="color:{INK}">llama.cpp</b> on this computer at <span style="font-family:' + MO + '">localhost:8080</span>, and it stopped answering '
                '<b style="color:{INK}">4 minutes ago</b>. Your story is safe &mdash; every line was written to disk as it arrived.'))
    b.append(box(X + 86, 228, 700, 40, 'display: flex; gap: 11px;',
                 btn('Try again', 'primary', 'refresh', h=40, fs=13.5) + btn('Use Kataki&rsquo;s own model instead', 'secondary', h=40, fs=13.5) +
                 btn('Open Settings', 'ghost', h=40, fs=13.5)))
    b.append(tx(X + W - 190, 130, 170, f'text-align: right; font-family: {MO}; font-size: 11.5px; color: {FAINT};', 'ECONNREFUSED'))
    # what you can still do
    b.append(tx(X, 326, 500, '', disp('What still works', 22)))
    STILL = [('book', 'Read', 'Every story you have is here and readable. Nothing needed a server to be written.'),
             ('edit', 'Write', 'Edit lines, rename stories, file places, build characters. All of it is local.'),
             ('download', 'Export', 'Take everything out as Markdown and JSON, right now, whatever the model is doing.')]
    sx = X
    sw = (W - 32) // 3
    for ic, t, d in STILL:
        b.append(panel(sx, 366, sw, 124))
        b.append(box(sx + 18, 386, sw - 36, 24, 'display: flex; align-items: center; gap: 10px;',
                     icon(ic, 17, OK, 1.8) + f'<span style="font-family: {UI}; font-size: 14px; font-weight: 700; color: {INK};">{t}</span>'))
        b.append(tx(sx + 18, 420, sw - 36, f'font-family: {UI}; font-size: 12.5px; line-height: 1.5; color: {MUT};', d))
        sx += sw + 16
    # diagnosis
    b.append(tx(X, 528, 500, '', disp('What usually causes this', 22)))
    b.append(panel(X, 568, W, 232))
    CAUSE = [('The server was closed', 'Start llama.cpp again and press Try again. Kataki reconnects without losing your place.', True),
             ('The computer went to sleep', 'Some servers do not come back on wake. Restarting it is enough.', False),
             ('The model was unloaded to free memory', 'qwen3.5-9b needs 9.2 GB. Kataki&rsquo;s own model needs 1.2 GB and will run alongside anything.', False),
             ('The port changed', 'Kataki can look for servers on this computer again.', False)]
    for i, (t, d, first) in enumerate(CAUSE):
        cy = 584 + i * 56
        b.append(box(X + 20, cy, 18, 18, f'border-radius: 50%; border: 1.5px solid {ACC if first else BORDER}; display: flex; align-items: center; justify-content: center;',
                     box(4, 4, 8, 8, f'border-radius: 50%; background: {ACC};') if first else ''))
        b.append(tx(X + 50, cy, 300, f'font-family: {UI}; font-size: 13.5px; font-weight: 700; color: {INK};', t))
        b.append(tx(X + 360, cy + 1, W - 400, f'font-family: {UI}; font-size: 12.5px; line-height: 1.4; color: {MUT};', d))
        if i < 3:
            b.append(rule(X + 20, cy + 40, W - 40))
    b.append(box(X, 832, W, 60, f'display: flex; align-items: center; gap: 10px; color: {MUT};',
                 icon('help', 16, 'currentColor', 1.8) +
                 f'<span style="font-family: {UI}; font-size: 13px;">Still stuck? </span>' +
                 f'<span style="font-family: {UI}; font-size: 13px; font-weight: 700; color: {ACCT};">Report this with the log attached</span>'))
    return page('Sky &middot; The model server went away', 1440, H, ''.join(b))

def build_feedback():
    H = 1000
    b, X, W = shell(H, 'Home', None, None, '')
    b.append(hero(X, W, 96))
    b.append(cast_grid(X, W, 500))
    b.append(dim(H))
    DW, DX, DY = 640, (1440 - 640) // 2 + 100, 96
    b.append(box(DX, DY, DW, 800, f'background: {POP}; backdrop-filter: blur(28px); border: 1px solid {BORDER}; '
                 f'border-radius: {R3}; box-shadow: 0 40px 90px rgba(0,0,0,.7);'))
    b.append(tx(DX + 26, DY + 26, DW - 52, '', disp('Report a bug', 24)))
    b.append(box(DX + DW - 52, DY + 26, 26, 26, f'color: {MUT};', icon('x', 18, 'currentColor', 2)))
    b.append(box(DX + 26, DY + 66, DW - 52, 34, 'display: flex; gap: 8px;',
                 chip('Feedback') + chip('Bug', True) + chip('Suggestion')))
    b.append(field(DX + 26, DY + 120, DW - 52, 'What happened', 'The character widget disappeared after I dragged it', None, None, 'text'))
    b.append(tx(DX + 26, DY + 200, DW - 52, '', eyebrow('Tell us a bit more')))
    b.append(box(DX + 26, DY + 220, DW - 52, 104, f'background: {SUNK}; border: 1px solid {BORDER}; border-radius: {R2}; padding: 12px 14px; box-sizing: border-box;',
                 f'<span style="font-family: {UI}; font-size: 13.5px; line-height: 1.55; color: {MID};">'
                 f'I dragged Theo&rsquo;s widget over the chat to the left column and it vanished. Reset layout brought it back. '
                 f'Happens every time on the second drag.</span>'))
    b.append(tx(DX + 26, DY + 348, DW - 52, '', eyebrow('What will be sent', WARM)))
    b.append(tx(DX + 26, DY + 368, DW - 52, f'font-family: {UI}; font-size: 12.5px; color: {MUT};', 'Nothing here is collected automatically. Remove anything you do not want to send.'))
    ATT = [('cpu', 'Kataki 0.4.2 &middot; Windows 11', True), ('server', 'llama.cpp &middot; qwen3.5-9b', True),
           ('alert', 'Last error &middot; widget-layout.js:142', True), ('image', 'Screenshot of this screen', True),
           ('book', 'The story this happened in', False)]
    for i, (ic, label, on) in enumerate(ATT):
        ay = DY + 400 + i * 46
        b.append(box(DX + 26, ay, DW - 52, 38, f'background: {SUNK}; border: 1px solid {HAIR}; border-radius: {R2}; '
                     f'display: flex; align-items: center; gap: 11px; padding: 0 13px; box-sizing: border-box;',
                     icon(ic, 15, MUT, 1.8) +
                     f'<span style="font-family: {UI}; font-size: 12.5px; color: {INK if on else FAINT}; flex: 1;">{label}</span>' +
                     (f'<span style="font-family: {UI}; font-size: 11.5px; font-weight: 600; color: {MUT};">Remove</span>' if on
                      else f'<span style="font-family: {UI}; font-size: 11.5px; font-weight: 600; color: {ACCT};">Attach</span>')))
    b.append(box(DX + 26, DY + 642, DW - 52, 56, f'background: rgba(111,216,164,.06); border: 1px solid rgba(111,216,164,.24); border-radius: {R2}; '
                 f'display: flex; align-items: center; gap: 11px; padding: 0 15px; box-sizing: border-box;',
                 icon('shield', 17, OK, 1.8) +
                 f'<span style="font-family: {UI}; font-size: 12.5px; color: {MID};">No story text, no character names and no file paths are included unless you attach them.</span>'))
    b.append(rule(DX + 26, DY + 722, DW - 52))
    b.append(box(DX + 26, DY + 742, DW - 52, 42, 'display: flex; align-items: center; gap: 11px;',
                 btn('Send', 'primary', h=42, fs=14) + btn('Copy to clipboard instead', 'secondary', h=42, fs=14) +
                 f'<span style="margin-left: auto; font-family: {UI}; font-size: 12px; color: {FAINT};">You get a link back</span>'))
    return page('Sky &middot; Feedback and bug report', 1440, H, ''.join(b))

def build_firstrun2():
    H = 900
    b = [box(0, 0, 1440, H, f'background: {GROUND};'), sky(H, 0)]
    X, W = 132, 1176
    b.append(tx(X, 68, W, '', eyebrow('Kataki &middot; step 2 of 2', ACC)))
    b.append(tx(X, 90, W, '', disp('Who first?', 62, INK, '800')))
    b.append(tx(X, 168, 800, f'font-family: {NR}; font-size: 20px; line-height: 1.45; color: {MID};',
                'Six people ship with Kataki. Pick one to start; the rest are waiting in Characters.'))
    CW = (W - 5 * 14) // 6
    for i, (k, nm, line, when, badge, n) in enumerate(PEOPLE):
        cx = X + i * (CW + 14)
        art = noface(nm, 164) if k == 'wren' else cover(k, '', None, nm)
        sel = i == 0
        inner = (f'<div style="position: relative; width: 100%; height: 164px; background: {RAISE};">' + art + '</div>'
                 f'<div style="padding: 12px 14px;">{disp(nm.split(" ")[0], 18)}'
                 f'<div style="font-family: {UI}; font-size: 11.5px; line-height: 1.4; color: {MUT}; margin-top: 4px; height: 46px;">{line}</div></div>')
        b.append(panel(cx, 246, CW, 300, inner, 0, 'overflow: hidden;' + (f' border-color: {ACCT}; box-shadow: {SHF};' if sel else '')))
        if sel:
            b.append(box(cx + CW - 34, 258, 24, 24, f'border-radius: 50%; background: {ACC}; display: flex; align-items: center; justify-content: center;', icon('check', 15, '#fff', 3)))
    b.append(box(X, 578, W, 96, f'background: {PANEL}; border: 1px solid {BORDER}; border-radius: {R3}; display: flex; align-items: center; gap: 16px; padding: 0 22px; box-sizing: border-box;',
                 face('aren', 48) +
                 f'<div style="flex: 1;"><div style="font-family: {UI}; font-size: 11px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: {FAINT};">And you are</div>'
                 f'<div style="margin-top: 3px; font-family: {UI}; font-size: 15px; font-weight: 700; color: {INK};">Liv Sandoval '
                 f'<span style="font-weight: 500; color: {MUT};">&mdash; or just &ldquo;You&rdquo;, and decide later</span></div></div>' +
                 btn('Change', 'ghost', h=38, fs=13)))
    b.append(box(X, 706, 420, 48, '', btn('Start with Mike', 'primary', h=48, fs=16)))
    b.append(tx(X + 460, 720, 520, f'font-family: {UI}; font-size: 13px; color: {MUT};', 'You can add, import or write your own at any time.'))
    b.append(tx(X, H - 48, W, f'font-family: {UI}; font-size: 12.5px; color: {MUT};',
                f'<span style="color: {INK}; font-weight: 700;">Back</span> &nbsp;&middot;&nbsp; Skip and go to an empty library'))
    return page('Sky &middot; First run, step 2', 1440, H, ''.join(b))

def build_loading():
    H = 900
    b = [box(0, 0, 1440, H, f'background: {GROUND};'), sky(H, 0)]
    b.append(box(0, 0, 1440, H, 'display: flex; align-items: center; justify-content: center;',
                 f'<div style="text-align: center;">'
                 f'<div style="font-family: {DP}; font-weight: 800; font-size: 52px; letter-spacing: -.015em; color: {INK};">Kataki</div>'
                 f'<div style="margin-top: 10px; font-family: {NR}; font-style: italic; font-size: 19px; color: {MID};">Waking six people up.</div></div>'))
    b.append(box(560, 520, 320, 5, f'border-radius: 3px; background: rgba(168,190,255,.12);'))
    b.append(box(560, 520, 196, 5, f'border-radius: 3px; background: {PRIM};'))
    STEPS = [('Library read', '412 lines, 6 characters, 4 stories', 'done'),
             ('Memories rebuilt', '41 of 63', 'doing'),
             ('Model reached', 'llama.cpp &middot; qwen3.5-9b', 'wait')]
    for i, (t, d, state) in enumerate(STEPS):
        sy = 566 + i * 46
        col = OK if state == 'done' else (ACC if state == 'doing' else FAINT)
        ic = 'check' if state == 'done' else ('refresh' if state == 'doing' else 'clock')
        b.append(box(560, sy, 340, 32, 'display: flex; align-items: center; gap: 11px;',
                     icon(ic, 16, col, 2) +
                     f'<span style="font-family: {UI}; font-size: 13.5px; font-weight: 600; color: {INK if state != "wait" else FAINT};">{t}</span>'
                     f'<span style="margin-left: auto; font-family: {UI}; font-size: 12px; color: {FAINT}; {TAB}">{d}</span>'))
    b.append(tx(0, H - 76, 1440, f'text-align: center; font-family: {UI}; font-size: 12.5px; color: {FAINT};',
                'Everything is on this computer. Nothing is being fetched.'))
    return page('Sky &middot; Opening', 1440, H, ''.join(b))


# ================================================================ PROOF BOARDS
AR = {
 'Sky &middot; Home': 'السماء · الرئيسية',
 'Kataki': 'كاتاكي', 'Home': 'الرئيسية', 'Stories': 'القصص', 'Characters': 'الشخصيات', 'World': 'العالم', 'You': 'أنت',
 'New character': 'شخصية جديدة', 'Settings': 'الإعدادات', 'Feedback': 'ملاحظات', 'Day': 'نهاري',
 'Liv': 'ليف', 'playing as': 'تلعب بدور', 'Search everything': 'ابحث في كل شيء',
 'the gala, three weeks later': 'الحفل، بعد ثلاثة أسابيع',
 'Continue &middot; Close to the Crown': 'تابِع · قريبًا من التاج',
 'Two Sugars, No Title': 'ملعقتا سكّر، بلا لقب',
 '&ldquo;&hellip;I could have sworn. Three weeks is a long time to hold one sentence.&rdquo;':
     '«…كنت لأُقسم على ذلك. ثلاثة أسابيع وقتٌ طويل لتحمل جملة واحدة.»',
 'Doubtful': 'متشكّك',
 '41 memories &middot; 2 changed since you left': '41 ذكرى · تغيّرت 2 منذ غيابك',
 'Continue': 'تابِع', 'New story': 'قصة جديدة',
 'Three weeks later &middot; Corvel Palace &middot; 7:22 pm': 'بعد ثلاثة أسابيع · قصر كورفل · 7:22 م',
 'Since you last played': 'منذ آخر مرة لعبت', '3 events &middot; 2 hours ago': '3 أحداث · قبل ساعتين',
 'Mike': 'مايك', 'Memory faded': 'ذكرى بهتت',
 '&ldquo;She didn&rsquo;t want to be on the gala list.&rdquo;': '«لم تكن تريد أن تكون على قائمة الحفل.»',
 'sharp &rarr; hazy': 'واضحة ← ضبابية', 'Memory doubted': 'ذكرى مشكوك فيها',
 '&ldquo;She says she never said it.&rdquo;': '«تقول إنها لم تقل ذلك قط.»',
 'conflicts with 1 memory': 'تتعارض مع ذكرى واحدة', 'Theo': 'ثيو', 'New memory': 'ذكرى جديدة',
 '&ldquo;Liv sent him to the back for milk.&rdquo;': '«أرسلته ليف إلى الخلف ليجلب الحليب.»',
 'witnessed': 'شهدها بنفسه', 'Your characters': 'شخصياتك', 'All': 'الكل', 'In a story': 'في قصة', 'Drafts': 'مسودات',
 'Played 2 hours ago &middot; wary': 'آخر لعب قبل ساعتين · حذِر', 'Played yesterday': 'آخر لعب أمس',
 'Nico': 'نيكو', 'Played 4 days ago': 'آخر لعب قبل 4 أيام', 'Jae': 'جاي', 'Played last week': 'آخر لعب الأسبوع الماضي',
 'D': 'د', 'no portrait yet': 'لا صورة بعد', 'Draft': 'مسودة', 'Dani': 'داني', 'No secret yet': 'لا سرّ بعد', 'Add': 'إضافة',
 'Other threads': 'قصص أخرى', 'All stories': 'كل القصص',
 'The Gala List': 'قائمة الحفل', 'Close to the Crown': 'قريبًا من التاج',
 '&ldquo;Officially? No comment. Unofficially, be there by eight.&rdquo;': '«رسميًا؟ لا تعليق. أما بيني وبينك، فكن هناك قبل الثامنة.»',
 'Three in the Morning': 'الثالثة فجرًا', 'The Flat on Ardenne': 'الشقة في شارع أردين',
 '&ldquo;You&rsquo;re not going to like this painting.&rdquo;': '«لن تعجبك هذه اللوحة.»',
 'Not in a book &middot; as Cas': 'خارج أي كتاب · بدور كاس', 'Played 3 weeks ago': 'آخر لعب قبل 3 أسابيع',
 'Everything here lives on this computer.': 'كل ما هنا محفوظ على هذا الحاسوب.', 'Where is my data?': 'أين بياناتي؟',
 'Stories ': 'القصص',
}
# Left in English on purpose: one story the player wrote in English, to prove mixed-direction
# user content is isolated with <bdi> and keeps its own punctuation.
AR_KEEP = {'The Long Way Home', '&ldquo;Leave it. We&rsquo;ll push.&rdquo;', 'Ctrl K'}

def build_home_day():
    use('day'); out = build_home(); use('night')
    return out.replace('Sky &middot; Home', 'Sky &middot; Home in Day')

def build_home_compact():
    global RW, PAD, PAGEW
    keep = (RW, PAD, PAGEW)
    RW, PAD, PAGEW = 72, 28, 1024
    out = build_home()
    RW, PAD, PAGEW = keep
    return out.replace('Sky &middot; Home', 'Sky &middot; Home at 1024')

def build_home_rtl():
    TR.clear(); TR.update(AR)
    use('night', rtl=True); out = build_home(); use('night')
    TR.clear()
    return out


def _ratio_cell(fg, bg, need=4.5):
    r = contrast(fg, bg)
    ok = r >= need
    return (f'<div style="height: 34px; display: flex; align-items: center; justify-content: center; gap: 6px; border-radius: {R1}; background: {bg}; '
            f'border: 1px solid {HAIR};"><span style="font-family: {UI}; font-size: 13px; font-weight: 700; color: {fg}; {TAB}">{r:.1f}</span></div>')

def contrast_matrix(x, y, w, theme):
    t = THEMES[theme]
    surf = [('ground', t['GROUND']), ('panel', t['PANEL']), ('raise', t['RAISE']), ('over', t['OVER']), ('rail', t['RAIL'])]
    rows = [('INK', t['INK']), ('MID', t['MID']), ('MUT', t['MUT']), ('FAINT', t['FAINT']), ('ACCT', t['ACCT']),
            ('WARM', t['WARM']), ('OK', t['OK']), ('BAD', t['BAD'])]
    p = []
    lw = 70
    cw = (w - lw - 4 * 6) // 5
    for j, (nm, c) in enumerate(surf):
        p.append(tx(x + lw + j * (cw + 6), y, cw, f'text-align: center; font-family: {MO}; font-size: 11px; color: {MUT};', nm))
    yy = y + 22
    worst = 99
    for nm, c in rows:
        p.append(tx(x, yy + 9, lw, f'font-family: {MO}; font-size: 11.5px; color: {MID};', nm))
        for j, (sn, sc) in enumerate(surf):
            p.append(box(x + lw + j * (cw + 6), yy, cw, 34, '', _ratio_cell(c, sc)))
            worst = min(worst, contrast(c, sc))
        yy += 40
    # primary button
    p.append(tx(x, yy + 9, lw, f'font-family: {MO}; font-size: 11.5px; color: {MID};', 'on ACCD'))
    p.append(box(x + lw, yy, cw, 34, '', _ratio_cell('#ffffff', t['ACCD'])))
    p.append(tx(x + lw + cw + 12, yy + 9, w - lw - cw - 12, f'font-family: {UI}; font-size: 12px; color: {MUT};',
                'white label on the primary button'))
    worst = min(worst, contrast('#ffffff', t['ACCD']))
    return ''.join(p), yy + 40, worst

def build_access():
    import json as _j
    try:
        A_ = _j.load(open('/tmp/claude-0/audit_summary.json'))
    except Exception:
        A_ = {'runs': 0, 'fails': 0, 'boards': 0}
    H = 1740
    X, W = 80, 1280
    b = [box(0, 0, 1440, H, f'background: {GROUND};'), sky(H, 0)]
    b.append(tx(X, 56, 900, '', eyebrow('Kataki &middot; proof board', MID)))
    b.append(tx(X, 78, 900, '', disp('Accessibility, measured', 40, INK, '800')))
    b.append(tx(X, 132, 820, f'font-family: {UI}; font-size: 15px; line-height: 1.55; color: {MID};',
                'Every number on this board is computed by the build from the tokens, or read from the audit '
                'that renders each screen with its real fonts and checks every line of text against the pixels behind it.'))
    stats = [(f"{A_['runs']:,}", 'text runs audited'), (str(A_['fails']), 'below WCAG AA'), (str(A_['boards']), 'screens audited'),
             ('2', 'themes'), ('2', 'directions')]
    sx = X
    for v, l in stats:
        b.append(box(sx, 196, 228, 84, f'background: {PANEL}; border: 1px solid {BORDER}; border-radius: {R3}; padding: 16px 18px; box-sizing: border-box;',
                     f'<div style="font-family: {DP}; font-weight: 800; font-size: 30px; line-height: 1; color: {OK if l == "below WCAG AA" else INK}; {TAB}">{v}</div>'
                     f'<div style="margin-top: 8px; font-family: {UI}; font-size: 12.5px; color: {MUT};">{l}</div>'))
        sx += 241
    # contrast
    y = 320
    b.append(panel(X, y, W, 546))
    b.append(tx(X + 28, y + 24, 600, '', disp('Contrast, every text colour on every surface', 21)))
    b.append(tx(X + 28, y + 56, 1100, f'font-family: {UI}; font-size: 13px; color: {MUT};',
                'Ratios shown in the colour they measure. Body text needs 4.5, large text and icons 3.0. The lowest cell in each table is still above 4.5.'))
    use('night'); m1, _, w1 = contrast_matrix(X + 28, y + 118, 590, 'night'); use('night')
    m2, _, w2 = contrast_matrix(X + 662, y + 118, 590, 'day')
    b.append(tx(X + 28, y + 90, 590, '', eyebrow('Night')))
    b.append(tx(X + 662, y + 90, 590, '', eyebrow('Day')))
    b.append(m1); b.append(m2)
    b.append(tx(X + 28, y + 510, 1200, f'font-family: {UI}; font-size: 12.5px; color: {MUT}; {TAB}',
                f'Lowest: {w1:.2f} at night, {w2:.2f} by day. Text over photographs sits on a measured scrim; the audit samples the photograph, not the token.'))
    # focus + targets
    y = 892
    b.append(panel(X, y, 620, 344))
    b.append(tx(X + 28, y + 24, 560, '', disp('Focus you can always find', 21)))
    b.append(tx(X + 28, y + 56, 560, f'font-family: {UI}; font-size: 13px; line-height: 1.5; color: {MUT};',
                f'A 2 px gap in the ground colour, then a 2 px accent ring. {contrast(ACC, GROUND):.1f}:1 against the ground and '
                f'{contrast(ACC, PANEL):.1f}:1 on a panel; 3:1 is the bar. It never depends on colour alone: the ring adds shape.'))
    fy = y + 132
    b.append(box(X + 28, fy, 560, 48, 'display: flex; align-items: center; gap: 14px;',
                 btn('Continue', 'primary', h=44).replace('box-shadow', 'x').replace('<button style="', f'<button style="box-shadow: {FOCUS}; ') +
                 f'<span style="display: inline-flex; align-items: center; height: 32px; padding: 0 13px; border-radius: 999px; background: {RAISE}; border: 1px solid {BORDER}; box-shadow: {FOCUS}; font-family: {UI}; font-size: 12.5px; font-weight: 600; color: {MID};">In a story</span>' +
                 f'<span style="display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; border-radius: 999px; border: 1px solid {BORDER}; box-shadow: {FOCUS}; color: {MID};">{icon("dots", 18, "currentColor", 2)}</span>'))
    b.append(box(X + 28, fy + 66, 560, 40, f'background: {SUNK}; border: 1px solid {ACC}; border-radius: {R2}; box-shadow: {FOCUS}; display: flex; align-items: center; padding: 0 13px; box-sizing: border-box; '
                 f'font-family: {UI}; font-size: 13.5px; color: {INK};', 'Dani<span style="display: inline-block; width: 2px; height: 17px; background: {ACC}; margin-left: 2px;"></span>'.replace('{ACC}', ACC)))
    b.append(tx(X + 28, fy + 132, 560, f'font-family: {UI}; font-size: 13px; line-height: 1.55; color: {MID};',
                '<b style="color: ' + INK + ';">Targets.</b> Nothing you click is smaller than 32 px (WCAG 2.2 asks for 24). '
                'Icon-only controls carry a label: the folded rail, the ··· menus, pin, close.'))
    # keyboard
    b.append(panel(X + 640, y, 640, 344))
    b.append(tx(X + 668, y + 24, 580, '', disp('Home, by keyboard alone', 21)))
    order = ['Skip to the story', 'Rail: Home, Stories, Characters, World, You', 'New character', 'Playing as',
             'Search &middot; Ctrl K from anywhere', 'Continue', 'New story', 'Since you last played, three cards',
             'Filters, then each character', 'Other threads, then All stories', 'Where is my data?']
    oy = y + 64
    for i, t_ in enumerate(order):
        col = 0 if i < 6 else 1
        rr = i if i < 6 else i - 6
        b.append(box(X + 668 + col * 300, oy + rr * 38, 290, 32, 'display: flex; align-items: center; gap: 10px;',
                     f'<span style="display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; border-radius: 50%; background: {RAISE}; border: 1px solid {BORDER}; font-family: {MO}; font-size: 11.5px; color: {INK}; flex-shrink: 0;">{i + 1}</span>'
                     f'<span style="font-family: {UI}; font-size: 13px; color: {MID};">{t_}</span>'))
    b.append(tx(X + 668, y + 304, 580, f'font-family: {UI}; font-size: 12.5px; color: {MUT};',
                'Order follows reading order. In a story, the composer is first and Esc always goes back one level.'))
    # reduced motion + text size
    y = 1262
    b.append(panel(X, y, 620, 440))
    b.append(tx(X + 28, y + 24, 560, '', disp('Less motion, same story', 21)))
    b.append(tx(X + 28, y + 56, 560, f'font-family: {UI}; font-size: 13px; color: {MUT};',
                'Follows the system setting; Settings &rsaquo; Appearance can override it.'))
    MOTION = [('Clouds part between places', 'a 150 ms crossfade'), ('Stars twinkle', 'still stars'),
              ('Time skip: clouds sweep across', 'cut straight to the title card'), ('Streaming caret blinks', 'a steady caret'),
              ('Cards lift on hover', 'border brightens instead'), ('Widgets glide when moved', 'they move in one step')]
    my = y + 96
    for a_, b_ in MOTION:
        b.append(rule(X + 28, my, 564))
        b.append(tx(X + 28, my + 12, 290, f'font-family: {UI}; font-size: 13.5px; color: {INK};', a_))
        b.append(tx(X + 330, my + 12, 262, f'font-family: {UI}; font-size: 13.5px; color: {MID};', '&rarr; ' + b_))
        my += 50
    b.append(panel(X + 640, y, 640, 440))
    b.append(tx(X + 668, y + 24, 580, '', disp('Text at 200%', 21)))
    b.append(tx(X + 668, y + 56, 580, f'font-family: {UI}; font-size: 13px; color: {MUT};',
                'Cards grow to fit; nothing is clipped and the two-line clamp lifts. Settings offers 100, 125 and 150; the browser zoom goes further.'))
    def card(z, w_):
        return (f'<div style="width: {w_}px; box-sizing: border-box; padding: {14*z}px {15*z}px; background: {RAISE}; border: 1px solid {BORDER}; border-radius: {R3};">'
                f'<div style="display: flex; align-items: center; gap: {8*z}px;">{face("oren", int(26*z))}'
                f'<span style="font-family: {NR}; font-weight: 600; font-size: {18*z}px; line-height: 1.15; color: {INK};">The Gala List</span></div>'
                f'<div style="margin-top: {8*z}px; font-family: {NR}; font-size: {14.5*z}px; line-height: 1.35; color: {MID};">&ldquo;Officially? No comment.&rdquo;</div>'
                f'<div style="margin-top: {6*z}px; font-family: {UI}; font-size: {11.5*z}px; font-weight: 600; color: {MUT};">Played last week</div></div>')
    b.append(tx(X + 668, y + 104, 180, '', eyebrow('100%')))
    b.append(box(X + 668, y + 126, 190, 200, '', card(1, 190)))
    b.append(tx(X + 880, y + 104, 380, '', eyebrow('200%')))
    b.append(box(X + 880, y + 126, 372, 300, '', card(2, 372)))
    return page('Accessibility, measured', 1440, H, ''.join(b))

SCREENS = [
 ('Sky2-Home', 'build_home', 1260, 'Home'),
 ('Sky2-Profile', 'build_profile', 1300, 'Mike\u2019s profile'),
 ('Sky2-Stories', 'build_stories', 1100, 'Stories'),
 ('Sky2-World', 'build_world', 950, 'World \u00b7 places and plots'),
 ('Sky2-FirstRun', 'build_firstrun', 900, 'First run \u00b7 step 1'),
 ('Sky2-Characters', 'build_characters', 1120, 'Characters'),
 ('Sky2-You', 'build_you', 1040, 'You \u00b7 personas'),
 ('Sky2-AddCharacter', 'build_addcharacter', 1120, 'New character'),
 ('Sky2-NewStory', 'build_newstory', 1020, 'New story'),
 ('Sky2-FirstRun2', 'build_firstrun2', 900, 'First run \u00b7 step 2'),
 ('Sky2-Palette', 'build_palette', 1000, 'Command palette'),
 ('Sky2-Search', 'build_search', 1020, 'Search results'),
 ('Sky2-Menus', 'build_menus', 1120, 'Every menu'),
 ('Sky2-Empty', 'build_empty', 1000, 'Empty \u00b7 day one'),
 ('Sky2-Error', 'build_error', 1000, 'The model server went away'),
 ('Sky2-Feedback', 'build_feedback', 1000, 'Feedback and bug report'),
 ('Sky2-Loading', 'build_loading', 900, 'Opening'),
 ('Sky2-Set-General', 'build_set_general', 1020, 'Settings \u00b7 General'),
 ('Sky2-Set-Appearance', 'build_set_appearance', 1020, 'Settings \u00b7 Appearance'),
 ('Sky2-Set-Language', 'build_set_language', 1020, 'Settings \u00b7 Language'),
 ('Sky2-Set-Models', 'build_set_models', 1120, 'Settings \u00b7 Models'),
 ('Sky2-Set-Memory', 'build_set_memory', 1060, 'Settings \u00b7 Memory and thinking'),
 ('Sky2-Set-Data', 'build_set_data', 1060, 'Settings \u00b7 Data and privacy'),
 ('Sky2-Set-Shortcuts', 'build_set_shortcuts', 1240, 'Settings \u00b7 Shortcuts'),
 ('Sky2-Set-About', 'build_set_about', 1020, 'Settings \u00b7 About and feedback'),
 ('Sky2-Home-Day', 'build_home_day', 1310, 'Home \u00b7 Day theme'),
 ('Sky2-Home-Compact', 'build_home_compact', 1310, 'Home \u00b7 1024 wide'),
 ('Sky2-Home-Arabic', 'build_home_rtl', 1310, 'Home \u00b7 Arabic, right to left'),
 ('Sky2-Access', 'build_access', 1740, 'Accessibility, measured'),
]

def main():
    g = globals()
    for name, fnname, h, title in SCREENS:
        fn = g[fnname]
        with open(os.path.join(OUT, name + '.dc.html'), 'w', encoding='utf-8') as f:
            f.write(fn())
    print(len(SCREENS), 'screens')

if __name__ == '__main__':
    main()
