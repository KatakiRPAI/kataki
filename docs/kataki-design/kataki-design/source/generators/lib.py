# Asset map. Keys are the old slot names so the screen generators keep working;
# the art is the new cast: Liv, Mike, Theo, Jae, Nico, Cas, and three places.
LIV='/_blob/0257952de929cbe75593ee4823cc1d4d'
MIKE='/_blob/b46de24970224b00a88bf14b4609ea7b'
THEO='/_blob/95626198a6424b39eff632f60604f9a1'
JAE='/_blob/f72fa63130cb8b10441e48ef74c4a493'
NICO='/_blob/c106e0dd5a453e07a361cd105282f636'
CAS='/_blob/017a32ebf750bb401d649cc54a63a087'
CAFE='/_blob/a65a256ab595122301173c846498d0d9'
PALACE='/_blob/072e4558a8200744a5eec153ad17dd58'
FLAT='/_blob/a27ecb89be8c40fc71d29e1e9362027f'
DANI='/_blob/6df02b229e655a013e4f0e90f703fd0e'
A = {
 'mira':MIKE,'mira-smile':MIKE,'mira-wary':MIKE,'mira-thinking':MIKE,'mira-doubtful':MIKE,
 'tobin':THEO,'tobin-sour':THEO,'ilsa':NICO,'oren':JAE,'wren':DANI,'aren':LIV,'sable':CAS,
 'gull-dusk':CAFE,'gull-night':PALACE,'lighthouse':PALACE,'market':FLAT,
 'table-dusk':CAFE,'table-night':PALACE,
 'clouds':'/_blob/249dcec7fe41970ab9704b8b690e72c3',
}
# Where each portrait's face sits, for circular crops and cover fills
FOCUS = {'mira':'50% 26%','tobin':'50% 30%','ilsa':'52% 30%','oren':'50% 32%','wren':'50% 36%','aren':'52% 24%','sable':'50% 20%'}
BG = {
 'mira':'linear-gradient(160deg,#ecdcb0,#b08a52)','tobin':'linear-gradient(160deg,#ffe2c0,#c98a62)',
 'ilsa':'linear-gradient(160deg,#ffd9c8,#d0785a)','oren':'linear-gradient(160deg,#ded8f8,#8878c4)',
 'wren':'linear-gradient(160deg,#dbe6f5,#9fb0c8)','aren':'linear-gradient(160deg,#ffd9c0,#e07a4a)',
 'sable':'linear-gradient(160deg,#dfe3c8,#7f8456)',
}
NAME={'mira':'Mike','tobin':'Theo','ilsa':'Nico','oren':'Jae','wren':'Dani','aren':'Liv','sable':'Cas'}

FONTS='<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Chewy&amp;family=Figtree:wght@400;500;600;700;800&amp;family=JetBrains+Mono:wght@400;500&amp;family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400;1,6..72,500&amp;display=swap">'

SANS="Figtree, 'Segoe UI', system-ui, sans-serif"
SERIF="Newsreader, Georgia, 'Times New Roman', serif"
MONO="'JetBrains Mono', Consolas, monospace"
DISPLAY="Chewy, 'Segoe UI', system-ui, sans-serif"

def page(title, w, h, body, bodybg='#0e0a08', extra_css=''):
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
{FONTS}
<style>
body{{margin:0;font-family:{SANS};background:{bodybg}}}
a{{color:#2f63f0}}a:hover{{color:#1d44b8}}
button{{font-family:inherit;cursor:pointer}}
textarea,input,select{{font-family:inherit}}
.sr{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}}
{extra_css}
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

I = {
 'home':'<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
 'users':'<circle cx="9" cy="8" r="4"/><path d="M2 21c0-4 3-6 7-6s7 2 7 6"/><path d="M16 3.6a4 4 0 010 8"/><path d="M22 21c0-3-1.8-5-4.5-5.7"/>',
 'chat':'<path d="M4 5h16v11H9l-5 4z"/>',
 'map':'<path d="M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3z"/><path d="M9 3v15"/><path d="M15 6v15"/>',
 'bell':'<path d="M6 16v-5a6 6 0 0112 0v5l2 2H4z"/><path d="M10 20a2 2 0 004 0"/>',
 'user':'<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',
 'cog':'<circle cx="12" cy="12" r="3.1"/><path d="M19.5 14.3a1.5 1.5 0 00.3 1.66l.05.05a1.9 1.9 0 11-2.69 2.69l-.05-.05a1.5 1.5 0 00-1.66-.3 1.5 1.5 0 00-.91 1.38V20a1.9 1.9 0 11-3.8 0v-.1a1.5 1.5 0 00-.98-1.38 1.5 1.5 0 00-1.66.3l-.05.05a1.9 1.9 0 11-2.69-2.69l.05-.05a1.5 1.5 0 00.3-1.66 1.5 1.5 0 00-1.38-.91H4a1.9 1.9 0 110-3.8h.1a1.5 1.5 0 001.38-.98 1.5 1.5 0 00-.3-1.66l-.05-.05a1.9 1.9 0 112.69-2.69l.05.05a1.5 1.5 0 001.66.3h.07a1.5 1.5 0 00.91-1.38V4a1.9 1.9 0 113.8 0v.1a1.5 1.5 0 00.91 1.38 1.5 1.5 0 001.66-.3l.05-.05a1.9 1.9 0 112.69 2.69l-.05.05a1.5 1.5 0 00-.3 1.66v.07a1.5 1.5 0 001.38.91H20a1.9 1.9 0 110 3.8h-.1a1.5 1.5 0 00-1.38.91z"/>',
 'settings':'<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
 'search':'<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
 'plus':'<path d="M12 5v14M5 12h14"/>',
 'heart':'<path d="M12 20s-7-4.5-7-10a4 4 0 017-2.6A4 4 0 0119 10c0 5.5-7 10-7 10z"/>',
 'lock':'<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>',
 'eye':'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
 'eyeoff':'<path d="M3 3l18 18"/><path d="M10.6 5.1A10 10 0 0112 5c6 0 10 7 10 7a17 17 0 01-3.2 4M6.6 6.6C3.9 8.4 2 12 2 12s4 7 10 7a9.6 9.6 0 005.4-1.6"/>',
 'cloud':'<path d="M7 18h10a4 4 0 000-8 6 6 0 00-11.5 1.5A3.5 3.5 0 007 18z"/>',
 'sun':'<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5"/>',
 'moon':'<path d="M20 14A8 8 0 1110 4a6 6 0 0010 10z"/>',
 'volume':'<path d="M4 9h4l5-4v14l-5-4H4z"/><path d="M16.5 9a4 4 0 010 6"/><path d="M19 6.5a8 8 0 010 11"/>',
 'mute':'<path d="M4 9h4l5-4v14l-5-4H4z"/><path d="M17 9l5 6M22 9l-5 6"/>',
 'layers':'<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
 'dots':'<circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/>',
 'send':'<path d="M4 12l16-8-6 16-3-7z"/><path d="M11 13l9-9"/>',
 'stop':'<rect x="7" y="7" width="10" height="10" rx="1.5"/>',
 'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 'spark':'<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 16l.7 1.8 1.8.7-1.8.7L19 21l-.7-1.8-1.8-.7 1.8-.7z"/>',
 'arrow':'<path d="M5 12h14M13 6l6 6-6 6"/>',
 'up':'<path d="M12 19V5M6 11l6-6 6 6"/>',
 'left':'<path d="M15 6l-6 6 6 6"/>','right':'<path d="M9 6l6 6-6 6"/>','down':'<path d="M6 9l6 6 6-6"/>',
 'check':'<path d="M5 12l5 5 9-10"/>','x':'<path d="M6 6l12 12M18 6L6 18"/>',
 'key':'<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3"/>',
 'server':'<rect x="4" y="4" width="16" height="7" rx="2"/><rect x="4" y="13" width="16" height="7" rx="2"/><path d="M8 7.5h.01M8 16.5h.01"/>',
 'refresh':'<path d="M20 11a8 8 0 10-2.3 6"/><path d="M20 4v7h-7"/>',
 'pin':'<path d="M12 21s-7-6-7-11a7 7 0 0114 0c0 5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
 'pushpin':'<path d="M9 3h6l-1 6 4 4H6l4-4z"/><path d="M12 13v8"/>',
 'edit':'<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
 'ear':'<path d="M7 9a5 5 0 0110 0c0 3.5-3.5 4.5-3.5 8a3 3 0 01-5.5 1.6"/><path d="M10 9a2 2 0 014 0"/>',
 'thought':'<path d="M6 14a5 5 0 014-8 5 5 0 019 2.5A3.8 3.8 0 0117 15H8.5A3 3 0 016 14z"/><circle cx="7" cy="19" r="1.3"/><circle cx="4" cy="21.5" r=".8"/>',
 'hand':'<path d="M8 13V5.5a1.5 1.5 0 013 0V11"/><path d="M11 11V4.5a1.5 1.5 0 013 0V11"/><path d="M14 11V6a1.5 1.5 0 013 0v8a7 7 0 01-7 7h-.5a6 6 0 01-5-2.8L3 14.5a1.5 1.5 0 012.5-1.6L8 15"/>',
 'quote':'<path d="M4 5h16v11H9l-5 4z"/><path d="M8.5 9.5h7M8.5 12.5h4"/>',
 'book':'<path d="M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2z"/><path d="M4 19V5"/>',
 'ff':'<path d="M4 6l7 6-7 6z"/><path d="M13 6l7 6-7 6z"/>',
 'quill':'<path d="M20 4C12 4 6 10 6 18"/><path d="M6 18c6 0 12-4 14-14"/><path d="M4 20l2-2"/><path d="M10 14h5"/>',
 'undo':'<path d="M9 14L4 9l5-5"/><path d="M4 9h10a6 6 0 010 12h-3"/>',
 'star':'<path d="M12 3l2.7 5.6 6.2.9-4.5 4.3 1.1 6.2L12 17l-5.5 3 1.1-6.2L3.1 9.5l6.2-.9z"/>',
 'grid':'<rect x="4" y="4" width="7" height="7" rx="2"/><rect x="13" y="4" width="7" height="7" rx="2"/><rect x="4" y="13" width="7" height="7" rx="2"/><rect x="13" y="13" width="7" height="7" rx="2"/>',
 'film':'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 5v14M17 5v14M3 9h4M3 15h4M17 9h4M17 15h4"/>',
 'help':'<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 015 0c0 2-2.5 2-2.5 4"/><path d="M12 17h.01"/>',
 'shield':'<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
 'cpu':'<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
 'globe':'<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 010 18a14 14 0 010-18"/>',
 'drag':'<circle cx="9" cy="6" r="1.2"/><circle cx="15" cy="6" r="1.2"/><circle cx="9" cy="12" r="1.2"/><circle cx="15" cy="12" r="1.2"/><circle cx="9" cy="18" r="1.2"/><circle cx="15" cy="18" r="1.2"/>',
 'image':'<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
 'feather':'<path d="M20 4C12 4 6 10 6 18"/><path d="M6 18c6 0 12-4 14-14"/>',
 'wind':'<path d="M3 8h11a3 3 0 10-3-3"/><path d="M3 12h16a3 3 0 11-3 3"/><path d="M3 16h7"/>',
 'swap':'<path d="M7 7h13l-4-4"/><path d="M17 17H4l4 4"/>',
 'merge':'<circle cx="6" cy="6" r="2.5"/><circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="12" r="2.5"/><path d="M6 8.5v7M8 7l7.5 4M8 17l7.5-4"/>',
 'alert':'<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18h.01"/>',
 'link':'<path d="M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1"/>',
 'filter':'<path d="M4 5h16l-6 8v6l-4-2v-4z"/>',
 'flame':'<path d="M12 21a6 6 0 006-6c0-4-3-6-4-10-1 3-3 4-4 6-1-1-1.5-2-1.5-3C6 10 6 12.5 6 15a6 6 0 006 6z"/>',
 'map-pin':'<path d="M12 21s-7-6-7-11a7 7 0 0114 0c0 5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
 'crown':'<path d="M3 8l4.5 4L12 5l4.5 7L21 8l-2 11H5z"/>',
 'download':'<path d="M12 4v11M7 10l5 5 5-5"/><path d="M4 20h16"/>',
 'mic':'<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0014 0M12 18v3"/>',
}
def icon(name,size=18,color='currentColor',sw=1.8,extra=''):
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex-shrink: 0;{extra}">{I[name]}</svg>'

def face(who, s, extra_style='', img=None, ring=None, bg=True, fstyle=''):
    """Circular crop of a portrait, centred on the face."""
    key = img or who
    base = key.split('-')[0]
    ringcss = f'box-shadow: {ring};' if ring else ''
    b = f'background: {BG.get(base, "#dfe7f7")};' if bg else ''
    return (f'<div style="width: {s}px; height: {s}px; border-radius: 50%; overflow: hidden; position: relative; flex-shrink: 0; {b}{ringcss}{extra_style}">'
            f'<img src="{A[key]}" alt="" style="width: 100%; height: 100%; object-fit: cover; object-position: {FOCUS.get(base, "50% 30%")}; {fstyle}"></div>')

def cover(key, extra='', pos=None, alt=''):
    """A portrait or place filling its box."""
    base = key.split('-')[0]
    return f'<img src="{A[key]}" alt="{alt}" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: {pos or FOCUS.get(base, "50% 30%")}; {extra}">'

def orb(s=56, extra=''):
    return (f'<div style="width: {s}px; height: {s}px; border-radius: 50%; flex-shrink: 0; position: relative; background: radial-gradient(circle at 34% 28%, #e8f1ff 0%, #8fb2ff 12%, #3d63f2 34%, #13238a 66%, #050b33 100%); '
            f'box-shadow: 0 0 0 3px rgba(255,255,255,.75), 0 0 0 7px rgba(120,160,255,.25), 0 12px 32px rgba(40,80,255,.55), inset -6px -8px 18px rgba(0,0,0,.45); {extra}">'
            f'<div style="position: absolute; left: 22%; top: 12%; width: 38%; height: 22%; border-radius: 50%; background: rgba(255,255,255,.55); filter: blur(2px);"></div></div>')

def candy(name, c1, c2, s=44):
    return (f'<div style="width: {s}px; height: {s}px; border-radius: {s*0.3:.0f}px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; '
            f'background: linear-gradient(150deg, {c1} 0%, {c2} 100%); box-shadow: inset 0 2px 0 rgba(255,255,255,.65), inset 0 -3px 6px rgba(0,0,0,.18), 0 6px 14px {c2}66; transform: rotate(-4deg);">'
            f'{icon(name, int(s*0.5), "#ffffff", 2.2)}</div>')

def esc(s): return s.replace('&','&amp;')
