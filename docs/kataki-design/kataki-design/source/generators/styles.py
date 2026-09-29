# -*- coding: utf-8 -*-
"""Four style directions for the Sky. 4 x 3 screens = 12 artboards."""
import os
from lib import A, FOCUS, NAME, icon, face, cover, orb, esc

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')

GF = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
      '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
      '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
      'family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,800&amp;'
      'family=Instrument+Sans:wght@400;500;600;700&amp;'
      'family=Instrument+Serif:ital@0;1&amp;'
      'family=Inter+Tight:wght@400;500;600;700&amp;'
      'family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&amp;'
      'family=Plus+Jakarta+Sans:wght@400;500;600;700;800&amp;'
      'family=Young+Serif&amp;'
      'family=Nunito+Sans:wght@400;500;600;700;800&amp;'
      'family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&amp;'
      'family=JetBrains+Mono:wght@400;500&amp;display=swap">')

NR = "Newsreader, Georgia, serif"
MO = "'JetBrains Mono', Consolas, monospace"

# ---------------------------------------------------------------- directions
STYLES = {
 'A': dict(
   id='A', name='Paper & Ink', tag='Editorial · a literary object',
   ui="'Instrument Sans', system-ui, sans-serif",
   disp="Fraunces, Georgia, serif", dw='800', dtrk='-.02em',
   ground='#f3eee4', band='#e9e0d0', card='#fffdf8', raise_='#faf5ea',
   ink='#231d16', mid='#4d4237', mut='#7d7062', faint='#a2968a',
   acc='#8f3020', accink='#ffffff', acc2='#2c4a6e',
   border='#ded3c0', hair='#eae1d1',
   r1='3px', r2='4px', r3='6px', rpill='999px',
   sh='none', shf='0 18px 44px rgba(60,44,24,.18)',
   railw=212, raillabel=True, dark=False,
 ),
 'B': dict(
   id='B', name='Night Theatre', tag='Dark-first · the art is the light',
   ui="'Inter Tight', system-ui, sans-serif",
   disp="'Instrument Serif', Georgia, serif", dw='400', dtrk='-.015em',
   ground='#121010', band='#1a1716', card='#1c1917', raise_='#24201d',
   ink='#f6efe6', mid='#cdc2b5', mut='#9b8f82', faint='#6f655b',
   acc='#e9a martin', accink='#1a1512', acc2='#7fa8b8',
   border='rgba(246,239,230,.10)', hair='rgba(246,239,230,.07)',
   r1='4px', r2='8px', r3='12px', rpill='999px',
   sh='none', shf='0 24px 60px rgba(0,0,0,.6)',
   railw=80, raillabel=False, dark=True,
 ),
 'C': dict(
   id='C', name='Daylight', tag='Calm modern · the quiet evolution',
   ui="'Plus Jakarta Sans', system-ui, sans-serif",
   disp="'Bricolage Grotesque', system-ui, sans-serif", dw='700', dtrk='-.03em',
   ground='#f1f4f6', band='#dfe9f1', card='#ffffff', raise_='#f7f9fb',
   ink='#15202a', mid='#3d4c58', mut='#6b7a86', faint='#98a5af',
   acc='#146b60', accink='#ffffff', acc2='#b4643a',
   border='#dfe5ea', hair='#eceff2',
   r1='6px', r2='10px', r3='16px', rpill='999px',
   sh='0 1px 2px rgba(18,32,44,.05)', shf='0 20px 48px rgba(18,40,60,.16)',
   railw=96, raillabel=True, dark=False,
 ),
 'D': dict(
   id='D', name='Storybook', tag='Illustrated · a thing made by hand',
   ui="'Nunito Sans', system-ui, sans-serif",
   disp="'Young Serif', Georgia, serif", dw='400', dtrk='-.01em',
   ground='#ece0c9', band='#e0d0b2', card='#fdf8ec', raise_='#f7efdd',
   ink='#2c2117', mid='#544636', mut='#7d6c56', faint='#a2917a',
   acc='#2f6c58', accink='#fdf8ec', acc2='#cc7722',
   border='#d8c6a6', hair='#e5d8bf',
   r1='4px', r2='10px', r3='14px', rpill='999px',
   sh='0 2px 0 rgba(90,68,38,.10)', shf='0 20px 40px rgba(80,58,28,.26)',
   railw=196, raillabel=True, dark=False,
 ),
}
STYLES['B']['acc'] = '#e8a54b'

STYLES['E'] = dict(
   id='E', name='Night Storybook', tag='A deck of lit cards, under the night sky',
   ui="'Nunito Sans', system-ui, sans-serif",
   disp="'Young Serif', Georgia, serif", dw='400', dtrk='-.01em',
   ground='#0d1226', band='#141a36', card='#1b1930', raise_='#241f38',
   ink='#f2ebdd', mid='#c7bcab', mut='#95897a', faint='#6e6558',
   acc='#efb35c', accink='#211705', acc2='#9fb8ff',
   border='rgba(236,226,206,.16)', hair='rgba(236,226,206,.10)',
   r1='4px', r2='10px', r3='14px', rpill='999px',
   sh='0 2px 0 rgba(0,0,0,.35)', shf='0 22px 46px rgba(0,0,0,.6)',
   railw=196, raillabel=True, dark=True, night=True,
   plate='#221f36', plateink='#f2ebdd', platemut='#98897a', plateborder='rgba(238,222,192,.24)',
   plateglow='inset 0 1px 0 rgba(255,226,180,.16)',
)
for _k, _t in STYLES.items():
    _t.setdefault('lay', 'D' if _k == 'E' else _k)
    _t.setdefault('night', False)
    _t.setdefault('plate', _t['card'])
    _t.setdefault('plateink', _t['ink'])
    _t.setdefault('platemut', _t['mut'])
    _t.setdefault('plateborder', _t['border'])
    _t.setdefault('plateglow', 'none')
    _t.setdefault('tape', _t['acc'] if _k == 'E' else _t.get('acc2', _t['acc']))

def stars(w, h, n=170, seed=7):
    import random
    r = random.Random(seed)
    d = []
    for _ in range(n):
        x, y = r.random() * w, r.random() * h
        rr = r.choice([0.7, 0.9, 1.1, 1.4])
        o = r.uniform(.22, .78)
        d.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr}" fill="#eef3ff" opacity="{o:.2f}"/>')
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="position: absolute; inset: 0;" aria-hidden="true">{"".join(d)}</svg>'

def night_ground(t, w, h, railw):
    g = (f'<div style="position: absolute; left: {railw}px; top: 0; width: {w - railw}px; height: {h}px; '
         f'background: linear-gradient(168deg, #0b1026 0%, #131a3a 34%, #1b1b3c 64%, #241a2e 100%);"></div>')
    g += box(railw, 0, w - railw, min(h, 620), 'overflow: hidden;', stars(w - railw, min(h, 620)))
    g += box(railw, 0, w - railw, min(h, 620),
             'background: radial-gradient(720px 480px at 88% -8%, rgba(206,218,255,.20), transparent 68%);')
    g += box(railw, 0, w - railw, 150, 'overflow: hidden; opacity: .30;',
             f'<img src="{A["clouds"]}" alt="" style="position: absolute; left: 0; top: -46px; width: 100%; '
             f'filter: brightness(.55) saturate(.5);">')
    return g

def page(title, w, h, body, bg):
    return f'''<!doctype html>
<html lang="en">
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
body{{margin:0;background:{bg}}}
button{{font-family:inherit;cursor:pointer;border:0;background:none;padding:0;color:inherit}}
input,textarea{{font-family:inherit}}
.sr{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}}
</style>
</helmet>
{body}
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

def box(x, y, w, h, css='', inner='', tag='div'):
    return f'<{tag} style="position: absolute; left: {x}px; top: {y}px; width: {w}px; height: {h}px; {css}">{inner}</{tag}>'

def tx(x, y, w, css='', inner=''):
    return f'<div style="position: absolute; left: {x}px; top: {y}px; width: {w}px; {css}">{inner}</div>'

# ------------------------------------------------------------------- pieces
def btn(t, label, kind='primary', ic=None, w=None, h=44, fs=15):
    """kind: primary | secondary | ghost"""
    wcss = f'width: {w}px; justify-content: center;' if w else 'padding: 0 20px;'
    if kind == 'primary':
        sk = f'background: {t["acc"]}; color: {t["accink"]};'
        if t['lay'] == 'D':
            sk += f' box-shadow: 0 3px 0 rgba(0,0,0,.45);'
        rad = t['rpill'] if t['lay'] in ('C', 'D') else t['r2']
    elif kind == 'secondary':
        sk = f'background: {t["card"]}; color: {t["ink"]}; border: 1px solid {t["border"]};'
        rad = t['rpill'] if t['lay'] in ('C', 'D') else t['r2']
    else:
        sk = f'background: transparent; color: {t["mid"]}; border: 1px solid {t["hair"]};'
        rad = t['r2']
    g = icon(ic, 17, 'currentColor', 1.9) if ic else ''
    gap = '<span style="width: 8px;"></span>' if ic else ''
    return (f'<button style="display: inline-flex; align-items: center; height: {h}px; {wcss} border-radius: {rad}; '
            f'font-family: {t["ui"]}; font-size: {fs}px; font-weight: 600; letter-spacing: -.005em; {sk}">{g}{gap}{label}</button>')

def chip(t, label, on=False, ic=None):
    if on:
        sk = f'background: {t["ink"]}; color: {t["ground"]}; border: 1px solid {t["ink"]};'
    else:
        sk = f'background: {t["card"]}; color: {t["mid"]}; border: 1px solid {t["border"]};'
    g = icon(ic, 14, 'currentColor', 2) + '<span style="width: 6px;"></span>' if ic else ''
    rad = t['rpill'] if t['lay'] in ('C', 'D') else t['r2']
    return (f'<span style="display: inline-flex; align-items: center; height: 30px; padding: 0 12px; border-radius: {rad}; '
            f'font-family: {t["ui"]}; font-size: 12.5px; font-weight: 600; {sk}">{g}{label}</span>')

def tag_(t, label):
    return (f'<span style="display: inline-block; padding: 4px 10px; border-radius: {t["r1"]}; '
            f'background: {t["raise_"]}; border: 1px solid {t["hair"]}; color: {t["mut"]}; '
            f'font-family: {t["ui"]}; font-size: 11.5px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase;">{label}</span>')

def surf(t, extra=''):
    return f'background: {t["card"]}; border: 1px solid {t["border"]}; box-shadow: {t["sh"]}; {extra}'

def eyebrow(t, s, col=None):
    return (f'<div style="font-family: {t["ui"]}; font-size: 11px; font-weight: 700; letter-spacing: .14em; '
            f'text-transform: uppercase; color: {col or t["faint"]};">{s}</div>')

def rule(t, y, x=0, w=1440, strong=False):
    c = t['border'] if strong else t['hair']
    if t['lay'] == 'D':
        return box(x, y, w, 2, f'background: repeating-linear-gradient(90deg, {c} 0 7px, transparent 7px 12px);')
    return box(x, y, w, 1, f'background: {c};')

# --------------------------------------------------------------------- rail
RAIL = [('home', 'Home', True), ('chat', 'Stories', False), ('users', 'Characters', False),
        ('map', 'World', False), ('user', 'You', False)]

def rail(t, h):
    w = t['railw']
    lbl = t['raillabel']
    if t['lay'] == 'A':
        bg = f'background: {t["band"]}; border-right: 1px solid {t["border"]};'
    elif t['lay'] == 'B':
        bg = f'background: {t["band"]}; border-right: 1px solid {t["border"]};'
    elif t['lay'] == 'D':
        bg = f'background: {t["band"]}; border-right: 2px solid {t["border"]};'
    else:
        bg = f'background: {t["card"]}; border-right: 1px solid {t["border"]};'
    o = box(0, 0, w, h, bg)
    p = []
    # mark
    if t['lay'] == 'A':
        p.append(tx(20, 26, w - 40, f'font-family: {t["disp"]}; font-weight: 800; font-size: 21px; letter-spacing: -.02em; color: {t["ink"]};', 'Kataki'))
        p.append(tx(20, 52, w - 40, f'font-family: {t["ui"]}; font-size: 9.5px; letter-spacing: .11em; text-transform: uppercase; color: {t["faint"]};', 'Role play, remembered'))
        top = 104
    elif t['lay'] == 'B':
        p.append(box(24, 26, 32, 32, f'border-radius: 50%; background: {t["acc"]}; display: flex; align-items: center; justify-content: center;',
                     f'<span style="font-family: {t["disp"]}; font-size: 19px; color: #1a1512;">K</span>'))
        top = 92
    elif t['lay'] == 'D':
        p.append(tx(22, 24, w - 40, f'font-family: {t["disp"]}; font-size: 23px; color: {t["ink"]};', 'Kataki'))
        p.append(box(22, 56, 46, 3, f'background: {t["acc2"]}; border-radius: 2px;'))
        top = 102
    else:
        p.append(box(28, 24, 40, 40, f'border-radius: 12px; background: {t["acc"]}; display: flex; align-items: center; justify-content: center;',
                     f'<span style="font-family: {t["disp"]}; font-size: 20px; font-weight: 700; color: #fff;">K</span>'))
        top = 96
    y = top
    for ic, label, on in RAIL:
        if lbl and t['lay'] in ('A', 'D'):
            col = t['ink'] if on else t['mut']
            mark = ''
            if on and t['lay'] == 'A':
                mark = box(0, 0, 3, 34, f'background: {t["acc"]}; left: -20px; top: 4px;')
            if on and t['lay'] == 'D':
                bgi = f'background: {t["card"]}; border: 2px solid {t["border"]}; border-radius: {t["r2"]};'
            else:
                bgi = ''
            p.append(box(20, y, w - 40, 40, f'display: flex; align-items: center; gap: 11px; padding: 0 10px; box-sizing: border-box; {bgi} color: {col};',
                         mark + icon(ic, 19, 'currentColor', 1.9) +
                         f'<span style="font-family: {t["ui"]}; font-size: 14.5px; font-weight: {700 if on else 500};">{label}</span>'))
            y += 44
        elif lbl:
            col = t['acc'] if on else t['mut']
            sel = f'background: {t["raise_"]}; border-radius: {t["r3"]};' if on else ''
            p.append(box(16, y, w - 32, 58, f'display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; {sel} color: {col};',
                         icon(ic, 20, 'currentColor', 1.9) +
                         f'<span style="font-family: {t["ui"]}; font-size: 10.5px; font-weight: 700;">{label}</span>'))
            y += 64
        else:
            col = t['ink'] if on else t['mut']
            sel = f'background: {t["raise_"]}; border-radius: 10px;' if on else ''
            p.append(box(20, y, 40, 40, f'display: flex; align-items: center; justify-content: center; {sel} color: {col};', icon(ic, 20, 'currentColor', 1.9)))
            p.append(box(20, y, 40, 40, 'pointer-events: none;', f'<span class="sr">{label}</span>'))
            y += 48
    # footer: settings + feedback + theme
    fy = h - 150
    foot = [('settings', 'Settings'), ('help', 'Feedback'), ('moon' if not t['dark'] else 'sun', 'Dark' if not t['dark'] else 'Light')]
    for ic, label in foot:
        if lbl and t['lay'] in ('A', 'D'):
            p.append(box(20, fy, w - 40, 34, f'display: flex; align-items: center; gap: 11px; padding: 0 10px; box-sizing: border-box; color: {t["faint"]};',
                         icon(ic, 17, 'currentColor', 1.8) + f'<span style="font-family: {t["ui"]}; font-size: 13px; font-weight: 500;">{label}</span>'))
            fy += 36
        elif lbl:
            p.append(box(16, fy, w - 32, 46, f'display: flex; flex-direction: column; align-items: center; gap: 3px; color: {t["faint"]};',
                         icon(ic, 18, 'currentColor', 1.8) + f'<span style="font-family: {t["ui"]}; font-size: 9.5px; font-weight: 600;">{label}</span>'))
            fy += 48
        else:
            p.append(box(20, fy, 40, 36, f'display: flex; align-items: center; justify-content: center; color: {t["faint"]};', icon(ic, 18, 'currentColor', 1.8)))
            fy += 40
    if t['lay'] == 'A':
        p.append(box(20, h - 158, 6, 6, f'border-radius: 50%; background: {t["acc"]};'))
    return o + ''.join(p)

# --------------------------------------------------------------------- HOME
CAST = [('mira', 'Mike', 'Played 2 hours ago', 'Barista at Halcyon'),
        ('tobin', 'Theo', 'Played yesterday', 'Closing shifts, hears everything'),
        ('ilsa', 'Nico', 'Played 4 days ago', 'Your flatmate, paints at 3am'),
        ('oren', 'Jae', 'Played last week', 'Palace press aide'),
        ('wren', 'Dani', 'Draft', 'Florist, back gate twice a week')]

LASTLINE = '&ldquo;&hellip;I could have sworn. Three weeks is a long time to hold one sentence.&rdquo;'
STATE = 'Mike is turning that over. He is not sure you said what he remembers.'

def topbar(t, X, W, y=30):
    p = []
    p.append(tx(X, y, 420, f'font-family: {t["ui"]}; font-size: 13px; font-weight: 600; color: {t["mut"]};', 'Good evening, Liv'))
    # search
    sw = 300
    sx = X + W - sw - 184
    p.append(box(sx, y - 8, sw, 38, surf(t, f'border-radius: {t["r2"]}; display: flex; align-items: center; gap: 9px; padding: 0 12px; box-sizing: border-box;'),
                 icon('search', 16, t['faint'], 1.9) +
                 f'<span style="font-family: {t["ui"]}; font-size: 13.5px; color: {t["faint"]}; flex: 1;">Search everything</span>'
                 f'<span style="font-family: {MO}; font-size: 11px; color: {t["faint"]}; border: 1px solid {t["hair"]}; '
                 f'border-radius: 4px; padding: 2px 6px;">Ctrl K</span>'))
    p.append(box(X + W - 172, y - 8, 172, 38, 'display: flex; justify-content: flex-end;', btn(t, 'Add a character', 'secondary', 'plus', h=38, fs=13.5)))
    return ''.join(p)

def hero(t, X, W, y):
    """The continue block: the hero of Home."""
    H = 372
    p = []
    sid = t['lay']
    if sid == 'B':
        p.append(box(X, y, W, H, f'border-radius: {t["r3"]}; overflow: hidden; position: absolute;',
                     cover('gull-night', 'filter: brightness(.66) saturate(.9);', '50% 40%', 'Corvel Palace at night') +
                     f'<div style="position: absolute; inset: 0; background: linear-gradient(90deg, rgba(18,16,16,.94) 0%, rgba(18,16,16,.78) 42%, rgba(18,16,16,.05) 100%);"></div>'))
        tX, tW = X + 44, 560
        col_ink, col_mid, col_mut = '#f6efe6', '#d6ccc0', '#9b8f82'
    elif sid == 'A':
        p.append(box(X, y, W, H, surf(t, f'border-radius: {t["r2"]};')))
        p.append(box(X + W - 512, y + 24, 488, H - 48, f'border-radius: 2px; overflow: hidden; background: {t["band"]}; box-shadow: 0 0 0 1px {t["border"]};',
                     cover('gull-night', '', '50% 42%', 'Corvel Palace at night')))
        tX, tW = X + 40, W - 592
        col_ink, col_mid, col_mut = t['ink'], t['mid'], t['mut']
    elif sid == 'C':
        p.append(box(X, y, W, H, surf(t, f'border-radius: {t["r3"]}; box-shadow: 0 1px 2px rgba(18,32,44,.05), 0 12px 32px rgba(18,40,60,.07);')))
        p.append(box(X + 16, y + 16, 452, H - 32, f'border-radius: 12px; overflow: hidden; background: {t["band"]};',
                     cover('gull-night', '', '50% 42%', 'Corvel Palace at night')))
        tX, tW = X + 500, W - 548
        col_ink, col_mid, col_mut = t['ink'], t['mid'], t['mut']
    else:  # D
        p.append(box(X, y, W, H, f'background: {t["card"]}; border: 2px solid {t["border"]}; border-radius: {t["r3"]}; box-shadow: 0 3px 0 rgba(90,68,38,.14);'))
        p.append(box(X + W - 470, y + 22, 430, H - 44, f'background: {t["plate"]}; border: 1px solid {t["plateborder"]}; padding: 10px 10px 34px; box-sizing: border-box; transform: rotate(-1.4deg); box-shadow: {t["shf"]}, {t["plateglow"]};',
                     f'<div style="position: relative; width: 100%; height: 100%; overflow: hidden; background: {t["band"]};">' +
                     cover('gull-night', '', '50% 42%', 'Corvel Palace at night') + '</div>' +
                     f'<div style="position: absolute; left: 0; right: 0; bottom: 8px; text-align: center; font-family: {t["disp"]}; font-size: 13px; color: {t["platemut"]};">the gala, three weeks later</div>'))
        p.append(box(X + W - 500, y + 8, 84, 26, f'background: {t["tape"]}2b; border: 1px solid {t["tape"]}44; transform: rotate(-8deg);'))
        tX, tW = X + 40, W - 540
        col_ink, col_mid, col_mut = t['ink'], t['mid'], t['mut']

    p.append(tx(tX, y + 40, tW, '', eyebrow(t, 'Continue &middot; Close to the Crown', col_mut)))
    dsz = 46 if sid != 'B' else 52
    p.append(tx(tX, y + 62, tW, f'font-family: {t["disp"]}; font-weight: {t["dw"]}; font-size: {dsz}px; line-height: 1.06; letter-spacing: {t["dtrk"]}; color: {col_ink};', 'Two Sugars,<br>No Title'))
    p.append(tx(tX, y + 178, tW - 20, f'font-family: {NR}; font-style: italic; font-size: 19.5px; line-height: 1.45; color: {col_mid};', LASTLINE))
    p.append(tx(tX, y + 178, 3, f'height: 52px; background: {t["acc"]}; left: {tX - 18}px;', ''))
    p.append(box(tX, y + 244, tW, 22, 'display: flex; align-items: center; gap: 8px;',
                 icon('thought', 15, t['acc'], 1.9) +
                 f'<span style="font-family: {t["ui"]}; font-size: 13.5px; font-weight: 600; color: {col_mid};">{STATE}</span>'))
    p.append(box(tX, y + 280, tW, 52, 'display: flex; align-items: center; gap: 14px;',
                 orb(46) + '<span style="width: 2px;"></span>' + btn(t, 'Dive back in', 'primary', None, h=46, fs=15.5) +
                 f'<span style="font-family: {t["ui"]}; font-size: 12.5px; color: {col_mut};">Three weeks later &middot; Corvel Palace &middot; 7:22 pm</span>'))
    return ''.join(p)

def cast_section(t, X, W, y):
    p = []
    sid = t['lay']
    p.append(tx(X, y, 400, f'font-family: {t["disp"]}; font-weight: {t["dw"]}; font-size: 25px; letter-spacing: {t["dtrk"]}; color: {t["ink"]};', 'Your characters'))
    p.append(box(X + W - 260, y + 2, 260, 30, 'display: flex; justify-content: flex-end; gap: 8px;',
                 chip(t, 'All', True) + chip(t, 'In a story') + chip(t, 'Drafts')))
    cy = y + 46
    if sid == 'B':
        # key-art posters, first one wide
        widths = [314, 200, 200, 200, 200]
        x = X
        for i, (k, nm, when, blurb) in enumerate(CAST):
            w = widths[i]
            h = 302
            inner = cover(k, 'filter: saturate(1.02);', None, nm + ' portrait')
            inner += f'<div style="position: absolute; inset: 0; background: linear-gradient(to top, rgba(12,10,10,.92) 0%, rgba(12,10,10,.35) 42%, transparent 72%);"></div>'
            fs = 27 if i == 0 else 20
            inner += (f'<div style="position: absolute; left: 16px; right: 14px; bottom: 14px;">'
                      f'<div style="font-family: {t["disp"]}; font-size: {fs}px; color: #f6efe6; line-height: 1;">{nm}</div>'
                      f'<div style="font-family: {t["ui"]}; font-size: 11.5px; color: #9b8f82; margin-top: 6px;">{when}</div></div>')
            if i == 0:
                inner += (f'<div style="position: absolute; left: 16px; top: 14px; padding: 4px 9px; border-radius: 3px; background: {t["acc"]}; '
                          f'font-family: {t["ui"]}; font-size: 10.5px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #1a1512;">In a story</div>')
            if nm == 'Dani':
                inner += (f'<div style="position: absolute; left: 14px; top: 14px; padding: 4px 9px; border-radius: 3px; background: rgba(18,16,16,.82); '
                          f'font-family: {t["ui"]}; font-size: 10.5px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #cdc2b5;">Draft</div>')
            p.append(box(x, cy, w, h, f'border-radius: {t["r2"]}; overflow: hidden; background: {t["raise_"]};', inner))
            x += w + 14
        p.append(box(x, cy, 92, 302, f'border-radius: {t["r2"]}; border: 1px dashed {t["border"]}; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: {t["mut"]};',
                     icon('plus', 22, 'currentColor', 1.8) + f'<span style="font-family: {t["ui"]}; font-size: 11px;">Add</span>'))
    elif sid == 'A':
        # editorial plates: one featured, four in a ruled list
        p.append(box(X, cy, 306, 300, f'background: {t["card"]}; border: 1px solid {t["border"]};',
                     f'<div style="position: relative; width: 100%; height: 202px; overflow: hidden; background: {t["band"]};">' + cover('mira', '', None, 'Mike, leaning on the counter') + '</div>'
                     f'<div style="padding: 14px 16px;">'
                     f'<div style="font-family: {t["disp"]}; font-weight: 800; font-size: 25px; letter-spacing: -.02em; color: {t["ink"]};">Mike</div>'
                     f'<div style="font-family: {t["ui"]}; font-size: 12.5px; color: {t["mut"]}; margin-top: 4px;">Played 2 hours ago &middot; in a story</div></div>'))
        lx = X + 334
        ly = cy
        for k, nm, when, blurb in CAST[1:]:
            drafted = (nm == 'Dani')
            p.append(box(lx, ly, W - 334, 1, f'background: {t["hair"]};'))
            p.append(box(lx, ly + 10, 62, 62, 'overflow: hidden; background: ' + t['band'] + ';',
                         cover(k, '', None, nm + ' portrait')))
            p.append(tx(lx + 78, ly + 16, 300, f'font-family: {t["disp"]}; font-weight: 600; font-size: 21px; letter-spacing: -.015em; color: {t["ink"]};', nm))
            p.append(tx(lx + 78, ly + 44, 420, f'font-family: {t["ui"]}; font-size: 13px; color: {t["mut"]};', blurb))
            rl = 'no secret yet' if drafted else when
            p.append(tx(lx + W - 334 - 200, ly + 26, 190, f'text-align: right; font-family: {t["ui"]}; font-size: 12.5px; font-weight: 600; color: {t["faint"]};', rl))
            if drafted:
                p.append(box(lx + W - 334 - 268, ly + 22, 60, 24, '', tag_(t, 'Draft')))
            ly += 76
        p.append(box(lx, ly, W - 334, 1, f'background: {t["hair"]};'))
    elif sid == 'C':
        p.append(box(X, cy, 340, 302, surf(t, f'border-radius: {t["r3"]}; overflow: hidden;'),
                     f'<div style="position: relative; width: 100%; height: 212px; background: {t["band"]};">' + cover('mira', '', None, 'Mike, leaning on the counter') +
                     f'<div style="position: absolute; left: 12px; top: 12px; padding: 5px 10px; border-radius: 999px; background: rgba(255,255,255,.92); font-family: {t["ui"]}; font-size: 11px; font-weight: 700; color: {t["acc"]};">In a story</div></div>'
                     f'<div style="padding: 14px 16px;"><div style="font-family: {t["disp"]}; font-weight: 700; font-size: 23px; letter-spacing: -.03em; color: {t["ink"]};">Mike</div>'
                     f'<div style="font-family: {t["ui"]}; font-size: 12.5px; color: {t["mut"]}; margin-top: 3px;">Played 2 hours ago</div></div>'))
        x = X + 354
        for k, nm, when, blurb in CAST[1:]:
            inner = (f'<div style="position: relative; width: 100%; height: 196px; background: {t["band"]};">' + cover(k, '', None, nm + ' portrait') + '</div>'
                     f'<div style="padding: 12px 14px;"><div style="font-family: {t["disp"]}; font-weight: 700; font-size: 18px; letter-spacing: -.02em; color: {t["ink"]};">{nm}</div>'
                     f'<div style="font-family: {t["ui"]}; font-size: 11.5px; color: {t["mut"]}; margin-top: 3px;">{"Needs a secret" if nm == "Dani" else when}</div></div>')
            p.append(box(x, cy, 178, 302, surf(t, f'border-radius: {t["r3"]}; overflow: hidden;'), inner))
            x += 192
        p.append(box(x, cy, 130, 302, f'border-radius: {t["r3"]}; border: 1.5px dashed {t["border"]}; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: {t["mut"]};',
                     icon('plus', 22, 'currentColor', 1.8) + f'<span style="font-family: {t["ui"]}; font-size: 12px; font-weight: 600;">Add</span>'))
    else:  # D
        x = X
        rots = ['-1.6deg', '1.2deg', '-.8deg', '1.6deg', '-1.2deg']
        for i, (k, nm, when, blurb) in enumerate(CAST):
            w = 248 if i == 0 else 172
            inner = (f'<div style="position: relative; width: 100%; height: {194 if i == 0 else 176}px; overflow: hidden; background: {t["band"]}; border: 1px solid {t["plateborder"]};">'
                     + cover(k, '', None, nm + ' portrait') + '</div>'
                     f'<div style="padding: 10px 2px 0;"><div style="font-family: {t["disp"]}; font-size: {24 if i == 0 else 19}px; color: {t["plateink"]};">{nm}</div>'
                     f'<div style="font-family: {t["ui"]}; font-size: 12px; color: {t["platemut"]}; margin-top: 2px;">{"no secret yet" if nm == "Dani" else when}</div></div>')
            p.append(box(x, cy, w, 296, f'background: {t["plate"]}; border: 2px solid {t["plateborder"]}; border-radius: {t["r2"]}; padding: 10px; box-sizing: border-box; transform: rotate({rots[i]}); box-shadow: {(t["shf"] + ", " + t["plateglow"]) if t["night"] else "0 4px 0 rgba(90,68,38,.10)"};', inner))
            if i == 0:
                p.append(box(x + w - 70, cy - 8, 78, 26, f'background: {t["acc"]}; color: {t["accink"]}; transform: rotate(6deg); display: flex; align-items: center; justify-content: center; font-family: {t["ui"]}; font-size: 11px; font-weight: 800; letter-spacing: .05em; text-transform: uppercase; border-radius: 3px;', 'In a story'))
            if nm == 'Dani':
                p.append(box(x + w - 62, cy - 6, 66, 24, f'background: {t["acc2"]}; color: #fff; transform: rotate(-7deg); display: flex; align-items: center; justify-content: center; font-family: {t["ui"]}; font-size: 11px; font-weight: 800; text-transform: uppercase; border-radius: 3px;', 'Draft'))
            x += w + 14
        p.append(box(x, cy + 10, 92, 270, f'border: 2px dashed {t["border"]}; border-radius: {t["r2"]}; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: {t["mut"]};',
                     icon('plus', 24, 'currentColor', 1.9) + f'<span style="font-family: {t["ui"]}; font-size: 12px; font-weight: 700;">Add</span>'))
    return ''.join(p)

def threads(t, X, W, y):
    p = []
    p.append(tx(X, y, 400, f'font-family: {t["disp"]}; font-weight: {t["dw"]}; font-size: 25px; letter-spacing: {t["dtrk"]}; color: {t["ink"]};', 'Other threads'))
    rows = [('The Gala List', 'Close to the Crown', 'Liv and Jae, two days before', 'Played last week', 'oren'),
            ('Three in the Morning', 'The Flat on Ardenne', 'Nico will not show you the painting', 'Played 4 days ago', 'ilsa'),
            ('The Long Way Home', 'Not in a book', 'As Cas &middot; the week the engine died', 'Played 3 weeks ago', 'sable')]
    x = X
    cw = (W - 32) // 3
    for title, book, sub, when, k in rows:
        if t['lay'] == 'D':
            css = f'background: {t["card"]}; border: 2px solid {t["border"]}; border-radius: {t["r2"]};'
        elif t['lay'] == 'B':
            css = f'background: {t["card"]}; border: 1px solid {t["border"]}; border-radius: {t["r2"]};'
        else:
            css = surf(t, f'border-radius: {t["r2"] if t["id"] == "A" else t["r3"]};')
        inner = (face(k, 40, 'position: absolute; left: 18px; top: 18px;') +
                 f'<div style="position: absolute; left: 70px; top: 16px; right: 16px;">'
                 f'<div style="font-family: {t["disp"]}; font-weight: {"600" if t["lay"] == "A" else t["dw"]}; font-size: 18px; letter-spacing: {t["dtrk"]}; color: {t["ink"]};">{title}</div>'
                 f'<div style="font-family: {t["ui"]}; font-size: 11.5px; color: {t["faint"]}; margin-top: 2px;">{book}</div></div>'
                 f'<div style="position: absolute; left: 18px; right: 16px; top: 74px; font-family: {NR}; font-size: 15px; color: {t["mid"]};">{sub}</div>'
                 f'<div style="position: absolute; left: 18px; bottom: 14px; font-family: {t["ui"]}; font-size: 11.5px; font-weight: 600; color: {t["faint"]};">{when}</div>')
        p.append(box(x, y + 44, cw, 132, css, inner))
        x += cw + 16
    return ''.join(p)

def build_home(t):
    H = 1160
    sid = t['lay']
    X = t['railw'] + 40
    W = 1440 - X - 40
    body = [box(0, 0, 1440, H, f'background: {t["ground"]};')]
    # sky band, style-specific
    if t['night']:
        body.append(night_ground(t, 1440, H, t['railw']))
    elif t['id'] == 'A':
        body.append(box(t['railw'], 0, 1440 - t['railw'], 96, f'background: linear-gradient(180deg, {t["band"]} 0%, {t["ground"]} 100%);'))
    elif t['id'] == 'C':
        body.append(box(t['railw'], 0, 1440 - t['railw'], 148, f'background: linear-gradient(180deg, {t["band"]} 0%, {t["ground"]} 100%);'))
        body.append(box(t['railw'], 0, 1440 - t['railw'], 148, 'overflow: hidden; opacity: .5;',
                        f'<img src="{A["clouds"]}" alt="" style="position: absolute; left: 0; top: -40px; width: 100%; opacity: .6;">'))
    elif t['id'] == 'D':
        body.append(box(t['railw'], 0, 1440 - t['railw'], 120, f'background: {t["band"]}; border-bottom: 2px solid {t["border"]};'))  # noqa
        body.append(box(t['railw'], 0, 1440 - t['railw'], 120, 'overflow: hidden; opacity: .45;',
                        f'<img src="{A["clouds"]}" alt="" style="position: absolute; left: -30px; top: -30px; width: 108%;">'))
    else:
        body.append(box(t['railw'], 0, 1440 - t['railw'], 120, f'background: linear-gradient(180deg, #1a1716 0%, {t["ground"]} 100%);'))
    body.append(rail(t, H))
    body.append(topbar(t, X, W))
    body.append(hero(t, X, W, 96))
    body.append(cast_section(t, X, W, 512))
    body.append(threads(t, X, W, 872))
    body.append(tx(X, 1104, W, f'font-family: {t["ui"]}; font-size: 12px; color: {t["faint"]};',
                   'Everything here lives on this computer. ' +
                   f'<span style="color: {t["acc"]}; font-weight: 600;">Where is my data?</span>'))
    return page(f'Sky Home &middot; {t["name"]}', 1440, H, ''.join(body), t['ground'])

# ------------------------------------------------------------------ PROFILE
HOLD = [('She did not want to be on the gala list.', 'going hazy', .42),
        ('Her mother is the queen&rsquo;s step-sister.', 'held tight', .88),
        ('She says she never said it.', 'doubted', .55)]

def bubble(t, s, who='him'):
    return (f'<div style="display: inline-block; max-width: 470px; padding: 11px 15px; border-radius: {t["r3"]}; '
            f'border-bottom-left-radius: 4px; background: {t["raise_"]}; border: 1px solid {t["hair"]}; '
            f'font-family: {NR}; font-size: 16.5px; line-height: 1.45; color: {t["mid"]};">{s}</div>')

def living(t, x, y, w):
    p = []
    h = 388
    if t['lay'] == 'D':
        css = f'background: {t["card"]}; border: 2px solid {t["border"]}; border-radius: {t["r3"]}; box-shadow: {t["sh"]};'
    else:
        css = surf(t, f'border-radius: {t["r3"]};')
    p.append(box(x, y, w, h, css))
    p.append(tx(x + 22, y + 20, w - 44, '', eyebrow(t, 'Right now')))
    p.append(box(x + w - 172, y + 16, 150, 28, f'display: flex; align-items: center; justify-content: flex-end; gap: 6px; color: {t["mut"]};',
                 f'<span style="font-family: {t["ui"]}; font-size: 12px; font-weight: 600;">Two Sugars, No Title</span>' + icon('down', 14, 'currentColor', 2)))
    p.append(box(x + 22, y + 46, w - 44, 44, 'display: flex; align-items: center; gap: 12px;',
                 face('mira', 42) +
                 f'<div><div style="font-family: {t["disp"]}; font-weight: {t["dw"]}; font-size: 22px; letter-spacing: {t["dtrk"]}; color: {t["ink"]};">Doubtful</div>'
                 f'<div style="font-family: {t["ui"]}; font-size: 12.5px; color: {t["mut"]};">at the gala, three weeks later</div></div>'))
    p.append(tx(x + 22, y + 112, w - 44, f'font-family: {NR}; font-size: 16.5px; line-height: 1.5; color: {t["mid"]};',
                'He is glad you came and certain you said something you did not say.'))
    p.append(rule(t, y + 172, x + 22, w - 44))
    p.append(tx(x + 22, y + 188, w - 44, '', eyebrow(t, 'What he still holds onto')))
    hy = y + 212
    for text, word, frac in HOLD:
        p.append(tx(x + 22, hy, w - 130, f'font-family: {NR}; font-size: 15.5px; color: {t["mid"]};', text))
        p.append(tx(x + w - 108, hy + 1, 86, f'text-align: right; font-family: {t["ui"]}; font-size: 11.5px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: {t["faint"]};', word))
        bw = w - 44
        p.append(box(x + 22, hy + 26, bw, 4, f'border-radius: 2px; background: {t["hair"]};'))
        col = t['acc'] if frac > .6 else t['faint']
        p.append(box(x + 22, hy + 26, int(bw * frac), 4, f'border-radius: 2px; background: {col};'))
        hy += 50
    p.append(box(x + 22, y + h - 44, w - 44, 26, f'display: flex; align-items: center; gap: 7px; color: {t["acc"]};',
                 icon('layers', 15, 'currentColor', 1.9) +
                 f'<span style="font-family: {t["ui"]}; font-size: 13px; font-weight: 700;">Open Backstage &middot; see how he got there</span>'))
    return ''.join(p)

def build_profile(t):
    H = 1160
    X = t['railw'] + 40
    W = 1440 - X - 40
    sid = t['lay']
    b = [box(0, 0, 1440, H, f'background: {t["ground"]};')]
    if t['night']:
        b.append(night_ground(t, 1440, H, t['railw']))
    b.append(rail(t, H))
    HH = 392
    # ------- hero
    if sid == 'B':
        b.append(box(t['railw'], 0, 1440 - t['railw'], 452, 'overflow: hidden;',
                     cover('gull-dusk', 'filter: brightness(.34) saturate(.7) blur(3px); transform: scale(1.06);', '50% 46%', '') +
                     '<div style="position: absolute; inset: 0; background: linear-gradient(180deg, rgba(18,16,16,.55) 0%, rgba(18,16,16,.86) 74%, #121010 100%);"></div>'))
        b.append(box(1440 - 40 - 392, 40, 392, 372, f'border-radius: {t["r3"]}; overflow: hidden; background: {t["raise_"]}; box-shadow: 0 24px 60px rgba(0,0,0,.6);',
                     cover('mira', '', '50% 26%', 'Mike, leaning on the counter, wary')))
        b.append(tx(X, 62, 700, f'font-family: {t["ui"]}; font-size: 11.5px; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; color: {t["acc"]};', 'Played 2 hours ago'))
        b.append(tx(X, 84, 700, f'font-family: {t["disp"]}; font-size: 74px; line-height: 1; letter-spacing: -.02em; color: #f6efe6;', 'Mike Dorsey'))
        b.append(tx(X, 178, 620, f'font-family: {NR}; font-size: 20px; font-style: italic; line-height: 1.45; color: #cdc2b5;', 'Barista at Halcyon. Son of the queen&rsquo;s hairdresser.'))
        b.append(box(X, 240, 420, 26, 'display: flex; gap: 8px;', tag_(t, 'Barista') + tag_(t, 'Steady') + tag_(t, 'Private')))
        b.append(box(X, 292, 620, 46, 'display: flex; align-items: center; gap: 12px;',
                     btn(t, 'Message Mike', 'primary', None, h=46) + btn(t, 'New story', 'secondary', None, h=46) +
                     f'<span style="display: inline-flex; align-items: center; justify-content: center; width: 46px; height: 46px; border-radius: {t["r2"]}; border: 1px solid {t["border"]}; color: {t["mut"]};">{icon("dots", 18, "currentColor", 2)}</span>'))
        b.append(tx(X, 356, 620, f'font-family: {t["ui"]}; font-size: 13.5px; color: {t["mut"]};', 'Four stories together since May. He has met Theo, and did not like it.'))
        ay = 452
    elif sid == 'A':
        b.append(box(t['railw'], 0, 1440 - t['railw'], 60, f'background: {t["band"]};'))
        b.append(box(X, 40, 300, 352, f'background: {t["card"]}; border: 1px solid {t["border"]}; padding: 12px; box-sizing: border-box;',
                     f'<div style="position: relative; width: 100%; height: 100%; overflow: hidden; background: {t["band"]};">' +
                     cover('mira', '', '50% 24%', 'Mike, leaning on the counter, wary') + '</div>'))
        b.append(tx(X + 336, 44, 620, '', eyebrow(t, 'Character &middot; played 2 hours ago')))
        b.append(tx(X + 336, 66, 640, f'font-family: {t["disp"]}; font-weight: 800; font-size: 62px; line-height: 1; letter-spacing: -.03em; color: {t["ink"]};', 'Mike Dorsey'))
        b.append(rule(t, 144, X + 336, 620, True))
        b.append(tx(X + 336, 160, 600, f'font-family: {NR}; font-size: 20px; font-style: italic; line-height: 1.5; color: {t["mid"]};', 'Barista at Halcyon. Son of the queen&rsquo;s hairdresser.'))
        b.append(box(X + 336, 214, 420, 26, 'display: flex; gap: 8px;', tag_(t, 'Barista') + tag_(t, 'Steady') + tag_(t, 'Private')))
        b.append(box(X + 336, 262, 620, 46, 'display: flex; align-items: center; gap: 12px;',
                     btn(t, 'Message Mike', 'primary', None, h=46) + btn(t, 'New story', 'secondary', None, h=46) +
                     f'<span style="display: inline-flex; align-items: center; justify-content: center; width: 46px; height: 46px; border: 1px solid {t["border"]}; color: {t["mut"]};">{icon("dots", 18, "currentColor", 2)}</span>'))
        b.append(tx(X + 336, 330, 620, f'font-family: {t["ui"]}; font-size: 13.5px; color: {t["mut"]};', 'Four stories together since May. He has met Theo, and did not like it.'))
        ay = 440
    elif sid == 'C':
        b.append(box(t['railw'], 0, 1440 - t['railw'], 150, f'background: linear-gradient(180deg, {t["band"]} 0%, {t["ground"]} 100%);'))
        b.append(box(X, 40, W, 340, surf(t, f'border-radius: {t["r3"]}; box-shadow: 0 1px 2px rgba(18,32,44,.05), 0 12px 32px rgba(18,40,60,.07);')))
        b.append(box(X + 20, 60, 268, 300, f'border-radius: 12px; overflow: hidden; background: {t["band"]};',
                     cover('mira', '', '50% 24%', 'Mike, leaning on the counter, wary')))
        b.append(tx(X + 316, 74, 620, '', eyebrow(t, 'Played 2 hours ago', t['acc'])))
        b.append(tx(X + 316, 96, 640, f'font-family: {t["disp"]}; font-weight: 700; font-size: 54px; line-height: 1.02; letter-spacing: -.035em; color: {t["ink"]};', 'Mike Dorsey'))
        b.append(tx(X + 316, 164, 600, f'font-family: {NR}; font-size: 19px; font-style: italic; color: {t["mid"]};', 'Barista at Halcyon. Son of the queen&rsquo;s hairdresser.'))
        b.append(box(X + 316, 204, 420, 26, 'display: flex; gap: 8px;', tag_(t, 'Barista') + tag_(t, 'Steady') + tag_(t, 'Private')))
        b.append(box(X + 316, 252, 620, 46, 'display: flex; align-items: center; gap: 12px;',
                     btn(t, 'Message Mike', 'primary', None, h=46) + btn(t, 'New story', 'secondary', None, h=46) +
                     f'<span style="display: inline-flex; align-items: center; justify-content: center; width: 46px; height: 46px; border-radius: 999px; border: 1px solid {t["border"]}; color: {t["mut"]};">{icon("dots", 18, "currentColor", 2)}</span>'))
        b.append(tx(X + 316, 316, 620, f'font-family: {t["ui"]}; font-size: 13.5px; color: {t["mut"]};', 'Four stories together since May. He has met Theo, and did not like it.'))
        ay = 424
    else:  # D
        if not t['night']:
            b.append(box(t['railw'], 0, 1440 - t['railw'], 120, f'background: {t["band"]}; border-bottom: 2px solid {t["border"]};'))
        b.append(box(X, 36, 300, 340, f'background: {t["plate"]}; border: 2px solid {t["plateborder"]}; padding: 12px 12px 42px; box-sizing: border-box; transform: rotate(-1.8deg); box-shadow: {t["shf"]}, {t["plateglow"]};',
                     f'<div style="position: relative; width: 100%; height: 100%; overflow: hidden; background: {t["band"]};">' +
                     cover('mira', '', '50% 24%', 'Mike, leaning on the counter, wary') + '</div>'
                     f'<div style="position: absolute; left: 0; right: 0; bottom: 12px; text-align: center; font-family: {t["disp"]}; font-size: 14px; color: {t["platemut"]};">Halcyon, closing time</div>'))
        b.append(box(X + 96, 20, 110, 30, f'background: {t["tape"]}2e; border: 1px solid {t["tape"]}4a; transform: rotate(-5deg);'))
        b.append(tx(X + 348, 48, 620, '', eyebrow(t, 'Played 2 hours ago', t['acc'])))
        b.append(tx(X + 348, 70, 640, f'font-family: {t["disp"]}; font-size: 58px; line-height: 1.02; color: {t["ink"]};', 'Mike Dorsey'))
        b.append(box(X + 348, 152, 180, 4, f'background: {t["acc2"]}; border-radius: 2px;'))
        b.append(tx(X + 348, 174, 600, f'font-family: {NR}; font-size: 19px; font-style: italic; color: {t["mid"]};', 'Barista at Halcyon. Son of the queen&rsquo;s hairdresser.'))
        b.append(box(X + 348, 216, 420, 26, 'display: flex; gap: 8px;', tag_(t, 'Barista') + tag_(t, 'Steady') + tag_(t, 'Private')))
        b.append(box(X + 348, 262, 620, 48, 'display: flex; align-items: center; gap: 12px;',
                     btn(t, 'Message Mike', 'primary', None, h=48) + btn(t, 'New story', 'secondary', None, h=48) +
                     f'<span style="display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; border-radius: 999px; border: 2px solid {t["border"]}; background: {t["card"]}; color: {t["mut"]};">{icon("dots", 18, "currentColor", 2)}</span>'))
        b.append(tx(X + 348, 328, 620, f'font-family: {t["ui"]}; font-size: 13.5px; color: {t["mut"]};', 'Four stories together since May. He has met Theo, and did not like it.'))
        ay = 424
    # ------- tabs
    b.append(box(X, ay, 300, 34, 'display: flex; gap: 22px; align-items: flex-end;',
                 f'<span style="font-family: {t["ui"]}; font-size: 15px; font-weight: 700; color: {t["ink"]}; border-bottom: 2px solid {t["acc"]}; padding-bottom: 7px;">Story</span>'
                 f'<span style="font-family: {t["ui"]}; font-size: 15px; font-weight: 600; color: {t["faint"]}; padding-bottom: 7px;">Profile</span>'))
    b.append(rule(t, ay + 33, X, 660))
    # ------- left column
    LW = 660
    cy = ay + 62
    b.append(tx(X, cy, LW, '', eyebrow(t, 'How he talks')))
    b.append(box(X, cy + 24, LW, 60, '', bubble(t, 'Ten minutes. Drink it fast or I&rsquo;m putting you to work.')))
    b.append(box(X + 40, cy + 86, LW, 60, '', bubble(t, '<em>wipes the counter twice</em> It&rsquo;s fine. It&rsquo;s not fine, but it&rsquo;s fine.')))
    sy = cy + 168
    sc = '#191512' if not t['dark'] else '#0c0a09'
    sb = 'rgba(201,162,39,.38)' if t['dark'] else 'rgba(255,255,255,.08)'
    b.append(box(X, sy, LW, 128, f'background: {sc}; border-radius: {t["r3"]}; border: 1px solid {sb};'))
    b.append(box(X + 22, sy + 20, 20, 20, '', icon('lock', 18, '#c9a227', 1.9)))
    b.append(tx(X + 50, sy + 20, LW - 80, f'font-family: {t["ui"]}; font-size: 11px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #c9a227;', 'Only Mike knows this'))
    b.append(tx(X + 22, sy + 52, LW - 44, f'font-family: {NR}; font-size: 20px; line-height: 1.45; color: #f0e7dc;', 'He cuts the queen&rsquo;s hair now. His mother&rsquo;s hands shake and no one can know.'))
    ry = sy + 156
    b.append(tx(X, ry, LW, '', eyebrow(t, 'Who he knows')))
    rels = [('tobin', 'Theo', 'wary'), ('aren', 'Liv', 'fond'), ('oren', 'Jae', 'not met')]
    rx = X
    for k, nm, how in rels:
        cardcss = f'background: {t["card"]}; border: {"2px" if sid == "D" else "1px"} solid {t["border"]}; border-radius: {t["r2"]};'
        b.append(box(rx, ry + 24, 208, 68, cardcss + ' display: flex; align-items: center; gap: 12px; padding: 0 14px; box-sizing: border-box;',
                     face(k, 38) +
                     f'<div><div style="font-family: {t["disp"]}; font-weight: {t["dw"] if sid != "A" else "600"}; font-size: 17px; color: {t["ink"]};">{nm}</div>'
                     f'<div style="font-family: {t["ui"]}; font-size: 12px; color: {t["mut"]};">{how}</div></div>'))
        rx += 226
    # ------- right column
    RX = X + 700
    RW = W - 700
    b.append(living(t, RX, ay, RW))
    ty = ay + 412
    b.append(tx(RX, ty, RW, '', eyebrow(t, 'Stories together')))
    st = [('Two Sugars, No Title', 'three weeks later', 'Played 2 hours ago'),
          ('The Gala List', 'two days before', 'Played last week'),
          ('The Long Way Home', 'as Cas', 'Played 3 weeks ago')]
    yy = ty + 24
    for title, rel, when in st:
        b.append(rule(t, yy, RX, RW))
        b.append(tx(RX, yy + 14, RW - 140, f'font-family: {t["disp"]}; font-weight: {t["dw"] if sid != "A" else "600"}; font-size: 18px; letter-spacing: {t["dtrk"]}; color: {t["ink"]};', title))
        b.append(tx(RX, yy + 40, RW - 140, f'font-family: {t["ui"]}; font-size: 12.5px; color: {t["mut"]};', rel))
        b.append(tx(RX + RW - 136, yy + 20, 136, f'text-align: right; font-family: {t["ui"]}; font-size: 12px; font-weight: 600; color: {t["faint"]};', when))
        yy += 72
    b.append(rule(t, yy, RX, RW))
    b.append(box(RX, yy + 20, RW, 30, f'display: flex; align-items: center; gap: 7px; color: {t["mut"]};',
                 icon('download', 15, 'currentColor', 1.8) +
                 f'<span style="font-family: {t["ui"]}; font-size: 13px; font-weight: 600;">Export everything about Mike</span>'))
    return page(f'Profile &middot; Mike &middot; {t["name"]}', 1440, H, ''.join(b), t['ground'])

# ----------------------------------------------------------------- FIRST RUN
DOORS = [
 dict(n='1', ic='flame', title='Start now',
      body='Kataki brings a small model with it. 1.2&nbsp;GB, downloads once, runs here. Good enough to meet someone tonight.',
      act='Start now', kind='primary', sub='Recommended'),
 dict(n='2', ic='server', title='Use a model server',
      body='Found <b>llama.cpp</b> on this computer, with <b>qwen3.5-9b</b> loaded. Kataki can use it as it is.',
      act='Use this', kind='secondary', sub='Found on this computer'),
 dict(n='3', ic='globe', title='Use an online model',
      body='OpenRouter, OpenAI, Anthropic, or anything OpenAI-compatible. Your key is kept in this computer&rsquo;s keychain.',
      act='Add a key', kind='secondary', sub='Sends your story elsewhere'),
]

def build_firstrun(t):
    H = 900
    sid = t['lay']
    b = [box(0, 0, 1440, H, f'background: {t["ground"]};')]
    if sid == 'B':
        b.append(box(0, 0, 560, H, 'overflow: hidden;',
                     cover('gull-dusk', 'filter: brightness(.62) saturate(.95);', '54% 46%', 'Halcyon Coffee on a wet evening') +
                     '<div style="position: absolute; inset: 0; background: linear-gradient(90deg, rgba(18,16,16,.3) 0%, rgba(18,16,16,.95) 100%);"></div>'))
        X, W = 616, 760
        HY = 92
    elif sid == 'A':
        b.append(box(0, 0, 1440, 220, f'background: {t["band"]};'))
        b.append(box(0, 0, 1440, 220, 'overflow: hidden; opacity: .45;',
                     f'<img src="{A["clouds"]}" alt="" style="position: absolute; left: 0; top: -60px; width: 100%;">'))
        X, W = 120, 1200
        HY = 62
    elif sid == 'C':
        b.append(box(0, 0, 1440, 300, f'background: linear-gradient(180deg, {t["band"]} 0%, {t["ground"]} 100%);'))
        b.append(box(0, 0, 1440, 300, 'overflow: hidden; opacity: .6;',
                     f'<img src="{A["clouds"]}" alt="" style="position: absolute; left: 0; top: -70px; width: 100%;">'))
        X, W = 160, 1120
        HY = 76
    elif t['night']:
        b = [box(0, 0, 1440, H, f'background: {t["ground"]};')] + [night_ground(t, 1440, H, 0)]
        X, W = 130, 1180
        HY = 78
    else:
        b.append(box(0, 0, 1440, 260, f'background: {t["band"]}; border-bottom: 2px solid {t["border"]};'))
        b.append(box(0, 0, 1440, 260, 'overflow: hidden; opacity: .5;',
                     f'<img src="{A["clouds"]}" alt="" style="position: absolute; left: -20px; top: -50px; width: 106%;">'))
        X, W = 130, 1180
        HY = 62

    ink = '#f6efe6' if sid == 'B' else t['ink']
    mid = '#cdc2b5' if sid == 'B' else t['mid']
    mut = '#9b8f82' if sid == 'B' else t['mut']

    b.append(tx(X, HY - 30, W, f'font-family: {t["ui"]}; font-size: 11.5px; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; color: {t["acc"]};', 'Kataki &middot; step 1 of 2'))
    dsz = {'A': 78, 'B': 70, 'C': 64, 'D': 64}[sid]
    b.append(tx(X, HY, W, f'font-family: {t["disp"]}; font-weight: {t["dw"]}; font-size: {dsz}px; line-height: 1; letter-spacing: {t["dtrk"]}; color: {ink};', 'They&rsquo;ll remember this.'))
    py = HY + dsz + 18
    b.append(tx(X, py, 720, f'font-family: {NR}; font-size: 22px; line-height: 1.45; color: {mid};',
                'Kataki needs something to think with. Pick one &mdash; you can change it later.'))
    # privacy statement, loud
    pv = py + 62
    pvcss = (f'background: {t["raise_"] if sid != "B" else "#1c1917"}; border: 1px solid {t["border"]}; '
             f'border-{"inline-start" if False else "left"}: 3px solid {t["acc"]}; border-radius: {t["r2"]};')
    b.append(box(X, pv, 720, 62, pvcss + ' display: flex; align-items: center; gap: 13px; padding: 0 18px; box-sizing: border-box;',
                 icon('shield', 22, t['acc'], 1.8) +
                 f'<span style="font-family: {t["ui"]}; font-size: 16px; font-weight: 600; line-height: 1.35; color: {ink};">'
                 f'Nothing leaves this computer unless you pick the third door.</span>'))

    # doors
    dy = pv + (118 if sid == 'A' else 96)
    if sid == 'B':
        rh, rgap = 112, 16
        for idx, d in enumerate(DOORS):
            first = d['n'] == '1'
            bd = t['acc'] if first else t['border']
            b.append(box(X, dy, W, rh, f'background: {t["card"]}; border: 1px solid {bd}; border-radius: {t["r3"]};'))
            b.append(box(X + 20, dy + 20, 40, 40, f'border-radius: {t["r2"]}; background: {t["acc"] if first else t["raise_"]}; display: flex; align-items: center; justify-content: center;',
                         icon(d['ic'], 21, t['accink'] if first else t['mut'], 1.9)))
            b.append(tx(X + 76, dy + 18, 360, f'font-family: {t["ui"]}; font-size: 10.5px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: {t["acc"] if first else t["faint"]};', d['sub']))
            b.append(tx(X + 76, dy + 34, 360, f'font-family: {t["disp"]}; font-size: 25px; letter-spacing: {t["dtrk"]}; color: {ink};', d['title']))
            b.append(tx(X + 76, dy + 68, 380, f'font-family: {t["ui"]}; font-size: 13px; line-height: 1.5; color: {mid};', d['body']))
            acts = btn(t, d['act'], d['kind'], h=42, fs=14) + (btn(t, 'Look again', 'ghost', h=42, fs=14) if d['n'] == '2' else '')
            b.append(box(X + W - 292, dy + 35, 272, 42, 'display: flex; justify-content: flex-end; gap: 10px;', acts))
            dy += rh + rgap
        cy = dy + 34
    elif sid == 'A':
        dw = (W - 80) // 3
        x = X
        for d in DOORS:
            b.append(box(x, dy, dw, 3, f'background: {t["ink"] if d["n"] == "1" else t["border"]};'))
            b.append(tx(x, dy + 20, dw, f'font-family: {MO}; font-size: 11.5px; letter-spacing: .06em; color: {t["faint"]};', d['sub'].upper()))
            b.append(tx(x, dy + 46, dw - 30, f'font-family: {t["disp"]}; font-weight: 800; font-size: 34px; letter-spacing: -.025em; color: {t["ink"]};', d['title']))
            b.append(tx(x, dy + 96, dw - 50, f'font-family: {NR}; font-size: 18px; line-height: 1.55; color: {t["mid"]};', d['body']))
            acts = btn(t, d['act'], d['kind'], h=46) + (btn(t, 'Look again', 'ghost', h=46) if d['n'] == '2' else '')
            b.append(box(x, dy + 208, dw, 46, 'display: flex; gap: 10px;', acts))
            x += dw + 40
        cy = dy + 356
    else:
        dw = (W - 40) // 3
        x = X
        for d in DOORS:
            first = d['n'] == '1'
            if sid == 'D':
                css = f'background: {t["card"]}; border: 2px solid {t["acc"] if first else t["border"]}; border-radius: {t["r3"]}; box-shadow: 0 4px 0 rgba(0,0,0,.28);'
            else:
                css = surf(t, f'border-radius: {t["r3"]};' + (f' border-color: {t["acc"]}; box-shadow: 0 0 0 3px {t["acc"]}1a;' if first else ''))
            b.append(box(x, dy, dw, 258, css))
            b.append(box(x + 22, dy + 22, 42, 42, f'border-radius: {t["r2"]}; background: {t["acc"] if first else t["raise_"]}; display: flex; align-items: center; justify-content: center;',
                         icon(d['ic'], 21, t['accink'] if first else t['mut'], 1.9)))
            b.append(tx(x + 22, dy + 78, dw - 44, f'font-family: {t["ui"]}; font-size: 10.5px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: {t["acc"] if first else t["faint"]};', d['sub']))
            b.append(tx(x + 22, dy + 98, dw - 44, f'font-family: {t["disp"]}; font-weight: {t["dw"]}; font-size: 27px; letter-spacing: {t["dtrk"]}; color: {ink};', d['title']))
            b.append(tx(x + 22, dy + 138, dw - 44, f'font-family: {t["ui"]}; font-size: 13.5px; line-height: 1.55; color: {mid};', d['body']))
            b.append(box(x + 22, dy + 200, dw - 44, 42, 'display: flex; gap: 10px;',
                         btn(t, d['act'], d['kind'], h=42, fs=14) + (btn(t, 'Look again', 'ghost', h=42, fs=14) if d['n'] == '2' else '')))
            x += dw + 20
        cy = dy + 258 + 62

    b.append(rule(t, cy - 26, X, W))
    faces = ''.join(face(k, 46, f'margin-left: {0 if i == 0 else -12}px; box-shadow: 0 0 0 3px {t["ground"]};')
                    for i, k in enumerate(['mira', 'tobin', 'ilsa', 'oren', 'aren', 'sable']))
    b.append(box(X, cy, 340, 48, 'display: flex; align-items: center;', faces))
    b.append(tx(X + 318, cy + 4, 380, f'font-family: {t["ui"]}; font-size: 14.5px; font-weight: 600; color: {ink};', 'Six people are already here.'))
    b.append(tx(X + 318, cy + 26, 400, f'font-family: {t["ui"]}; font-size: 13px; color: {mut};', 'Pick one after this. Write your own whenever you like.'))
    imp = (icon('download', 16, t['acc'], 1.9) +
           f'<span style="font-family: {t["ui"]}; font-size: 13.5px; font-weight: 700; color: {t["acc"]};">Coming from somewhere else? Import cards</span>')
    if W < 900:
        b.append(box(X, cy + 60, 400, 30, 'display: flex; align-items: center; gap: 8px;', imp))
    else:
        b.append(box(X + W - 330, cy + 2, 330, 44, 'display: flex; justify-content: flex-end; align-items: center; gap: 8px;', imp))
    b.append(tx(X, H - 46, W, f'font-family: {t["ui"]}; font-size: 12.5px; color: {mut};',
                'All of this lives in Settings afterwards. ' +
                f'<span style="color: {ink}; font-weight: 600;">Skip for now</span>'))
    return page(f'First run &middot; {t["name"]}', 1440, H, ''.join(b), t['ground'])

# --------------------------------------------------------------------- write
def main():
    os.makedirs(OUT, exist_ok=True)
    made = []
    for sid, t in STYLES.items():
        for kind, fn, h in (('Home', build_home, 1160), ('Profile', build_profile, 1160), ('FirstRun', build_firstrun, 900)):
            name = f'Style-{sid}-{kind}.dc.html'
            with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
                f.write(fn(t))
            made.append((name, h, t['name'], kind))
    for m in made:
        print(m[0], m[1])

if __name__ == '__main__':
    main()
