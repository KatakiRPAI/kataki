import re
from lib import *
INK='#eef2ff'; MUTED='#b3bfdf'; AMBER='#e7b06a'; ACC='#5b86ff'; ACCD='#3558d6'; LILAC='#cbb8ff'; ROSE='#f4a595'; SAGE='#a9dcb8'; SKY='#9cc8ff'
SPK={'aren':'#a9c8ff','mira':'#f2b870','tobin':'#e8cc6a'}
W,H=1440,900
PLACE_ALT={'gull-dusk':'Halcyon Coffee, a corner café in the rain','gull-night':'Corvel Palace on the night of the gala'}
GLASS='background: rgba(19,27,58,.66); border: 1px solid rgba(168,190,255,.14); backdrop-filter: blur(16px);'
PANEL='background: rgba(10,16,40,.80); border: 1px solid rgba(168,190,255,.10); backdrop-filter: blur(20px);'
CX, CW = 320, 800          # chat column
LX, RX, WW = 24, 1144, 272  # widget columns

def btn_round(ic, label, size=40, extra=''):
    return f'<button aria-label="{label}" style="width: {size}px; height: {size}px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: {INK}; {GLASS}{extra}">{icon(ic,size*0.45)}</button>'

# ------------------------------------------------ backdrop + corners
def place(bg, tint='#0a1028', tint_op=.22, blur=3):
    return (f'<img src="{A[bg]}" alt="{PLACE_ALT.get(bg, "the place")}" style="position: absolute; left: -30px; top: -30px; width: {W+60}px; height: {H+60}px; object-fit: cover; object-position: 50% 45%; filter: blur({blur}px) brightness(.55) saturate(.95);">'
            f'<div style="position: absolute; inset: 0; background: {tint}; opacity: {tint_op};"></div>'
            f'<div style="position: absolute; inset: 0; background: radial-gradient(ellipse 80% 90% at 50% 45%, rgba(0,0,0,0) 40%, rgba(0,0,0,.6) 100%); pointer-events: none;"></div>')

def corners(backstage=False, menu_open=False):
    sw_bg = '#7fb7ff' if backstage else 'rgba(255,255,255,.18)'
    knob = 'left: 20px;' if backstage else 'left: 2px;'
    left = f'''<div style="position: absolute; left: {LX}px; top: 20px; display: flex; align-items: center; gap: 12px; color: {INK}; z-index: 5;">
{btn_round('cloud','Float back up to the Sky',44)}
<span style="display: flex; flex-direction: column; gap: 1px;"><span style="font-family: {SERIF}; font-style: italic; font-size: 18px;">Two Sugars, No Title</span><span style="font-size: 12px; color: {MUTED};">as Liv · Close to the Crown</span></span></div>'''
    right = f'''<div style="position: absolute; right: 24px; top: 20px; display: flex; align-items: center; gap: 8px; color: {INK}; z-index: 9;">
<label style="display: flex; align-items: center; gap: 9px; height: 44px; padding: 0 14px; border-radius: 22px; box-sizing: border-box; font-size: 13px; font-weight: 600; {GLASS}">{icon('layers',16)}Backstage<span style="position: relative; width: 38px; height: 20px; border-radius: 10px; background: {sw_bg}; display: block;"><span style="position: absolute; top: 2px; {knob} width: 16px; height: 16px; border-radius: 50%; background: #fff; display: block;"></span></span></label>
{btn_round('dots','Story menu',44, ' box-shadow: 0 0 0 2px #0a1028, 0 0 0 4px '+ACC+';' if menu_open else '')}
</div>'''
    return left + right

# ------------------------------------------------ chat
def stamp(t, tip=None):
    if not tip:
        return f'<span style="font-size: 12px; color: {MUTED}; font-variant-numeric: tabular-nums;">{t}</span>'
    return (f'<span style="position: relative; font-size: 12px; color: {INK}; font-variant-numeric: tabular-nums; border-bottom: 1px dotted {MUTED};">{t}'
            f'<span style="position: absolute; left: -10px; bottom: 22px; white-space: nowrap; padding: 7px 11px; border-radius: 10px; background: #212b57; border: 1px solid rgba(168,190,255,.2); box-shadow: 0 10px 24px rgba(0,0,0,.5); font-size: 12px; color: {INK}; display: flex; flex-direction: column; gap: 2px; z-index: 3;"><b style="font-weight: 700;">{tip[0]}</b><span style="color: {MUTED};">{tip[1]}</span></span></span>')

def prose(text):
    t=esc(text)
    t=re.sub(r'\*(.+?)\*', lambda m: f'<em style="color: #c6d0ec;">{m.group(1)}</em>', t)
    return f'<p style="margin: 6px 0 0; font-family: {SERIF}; font-size: 19px; line-height: 1.55; color: {INK}; text-wrap: pretty;">{t}</p>'

def react(kind, text, who=None, soft=False):
    col={'memory':AMBER,'feeling':ROSE,'warm':SAGE,'belief':LILAC,'mood':SKY}[kind]
    ic={'memory':'spark','feeling':'heart','warm':'heart','belief':'help','mood':'thought'}[kind]
    f = face(who,20) if who else ''
    return f'<span style="display: inline-flex; align-items: center; gap: 7px; height: 28px; padding: 0 12px 0 {5 if who else 10}px; border-radius: 14px; background: {col}1c; border: 1px solid {col}55; font-size: 12.5px; font-weight: 600; color: {col}; white-space: nowrap;{" opacity: .5;" if soft else ""}">{f}{icon(ic,13,col)}{text}</span>'

def reacts(*items):
    return f'<div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 9px;">{"".join(items)}</div>'

def tools():
    return f'''<div style="position: absolute; right: 8px; top: 6px; display: flex; align-items: center; gap: 2px; padding: 4px; border-radius: 12px; background: rgba(26,35,72,.95); border: 1px solid rgba(168,190,255,.14);">
<button aria-label="Previous take" style="width: 30px; height: 30px; border: 0; border-radius: 8px; background: none; color: {INK}; display: flex; align-items: center; justify-content: center;">{icon('left',15)}</button><span style="font-size: 12px; color: {MUTED};">1/1</span><button aria-label="New take" style="width: 30px; height: 30px; border: 0; border-radius: 8px; background: none; color: {INK}; display: flex; align-items: center; justify-content: center;">{icon('right',15)}</button>
<span style="width: 1px; height: 18px; background: rgba(255,255,255,.14); display: block;"></span>
<button style="height: 30px; border: 0; border-radius: 8px; background: none; color: {INK}; font-size: 12px; display: flex; align-items: center; gap: 5px; padding: 0 8px;">{icon('edit',14)}Edit</button>
<button style="height: 30px; border: 0; border-radius: 8px; background: none; color: {INK}; font-size: 12px; display: flex; align-items: center; gap: 5px; padding: 0 8px;">{icon('eyeoff',14)}Hide</button></div>'''

def line(who, t, text, extra='', hover=False, tip=None, spark=False, dim=False, marks=''):
    hb = 'background: rgba(255,255,255,.045); box-shadow: 0 0 0 1px rgba(168,190,255,.1);' if hover else ''
    sp = f'<span aria-label="Drew on memory" style="display: flex;">{icon("spark",14,AMBER)}</span>' if spark else ''
    return f'''<article style="position: relative; display: flex; flex-direction: column; padding: 12px 14px; margin: 0 -14px; border-radius: 14px; {hb}{" opacity: .78;" if dim else ""}">
{tools() if hover else ''}
<div style="display: flex; align-items: baseline; gap: 10px;"><span style="font-size: 13px; font-weight: 700; color: {SPK[who]}; letter-spacing: .02em;">{NAME[who]}</span>{stamp(t,tip)}{sp}{marks}</div>
{prose(text)}{extra}</article>'''

def titlecard(text, extra=''):
    return f'<div style="display: flex; align-items: center; gap: 14px; margin: 10px 0 6px; color: {MUTED};"><span style="flex-grow: 1; height: 1px; background: linear-gradient(90deg, rgba(168,190,255,0), rgba(168,190,255,.3)); display: block;"></span><span style="font-family: {SERIF}; font-size: 14px; letter-spacing: .14em; text-transform: uppercase; white-space: nowrap;">{text}</span>{extra}<span style="flex-grow: 1; height: 1px; background: linear-gradient(90deg, rgba(168,190,255,.3), rgba(168,190,255,0)); display: block;"></span></div>'

def note(who, text, grey=False):
    return f'<div style="display: flex; align-items: center; gap: 10px; margin: 4px 0; padding: 6px 2px; color: {MUTED};">{face(who,22,fstyle="filter: grayscale(.9);" if grey else "")}<span style="font-family: {SERIF}; font-style: italic; font-size: 16px;">{text}</span></div>'

def recallbox(who, head, text, sub):
    return f'''<div style="margin-top: 10px; padding: 12px 14px; border-radius: 14px; background: rgba(30,40,80,.9); border: 1px solid rgba(231,176,106,.3); display: flex; flex-direction: column; gap: 7px; max-width: 520px;">
<div style="display: flex; align-items: center; gap: 8px; font-size: 11.5px; font-weight: 700; color: {AMBER}; letter-spacing: .06em;">{icon('spark',14,AMBER)}{head}</div>
<span style="font-family: {SERIF}; font-size: 16px; color: {INK};">{text}</span>
<span style="font-size: 11.5px; color: {MUTED};">{sub}</span></div>'''

def modechip(label='Auto', detected=None, open_=False):
    d = f'<span style="color: {MUTED}; font-weight: 500;">· {detected}</span>' if detected else ''
    return f'<button aria-haspopup="menu" aria-expanded="{"true" if open_ else "false"}" style="height: 40px; padding: 0 12px 0 14px; border-radius: 20px; border: 1px solid {"rgba(91,134,255,.8)" if open_ else "rgba(168,190,255,.16)"}; background: rgba(255,255,255,.04); color: {INK}; font-size: 13px; font-weight: 700; display: flex; align-items: center; gap: 6px; white-space: nowrap;">{icon("spark",14,AMBER)}{label}{d}{icon("down",14,MUTED)}</button>'

def composer(advanced=False, stop=False, text='', placeholder='Speak or act as Liv…', mode='Auto', detected=None, open_=False, meter=45, hear=(('mira',False),)):
    val = f'<span style="font-family: {SERIF}; font-size: 18px; color: {INK};">{text}</span><span style="display: inline-block; width: 2px; height: 20px; background: {ACC}; vertical-align: -4px; margin-left: 1px;"></span>' if text else f'<span style="font-family: {SERIF}; font-size: 18px; color: {MUTED}; opacity: .8;">{placeholder}</span>'
    seg = ''.join(f'<button aria-pressed="{"true" if (l=="Advanced")==advanced else "false"}" style="height: 26px; padding: 0 10px; border: 0; border-radius: 13px; font-size: 11.5px; font-weight: 700; background: {"rgba(168,190,255,.14)" if (l=="Advanced")==advanced else "none"}; color: {INK if (l=="Advanced")==advanced else MUTED};">{l}</button>' for l in ('Simple','Advanced'))
    act = (f'<button style="height: 40px; padding: 0 18px 0 14px; border-radius: 20px; border: 1px solid rgba(168,190,255,.3); background: rgba(168,190,255,.08); color: {INK}; font-size: 13.5px; font-weight: 700; display: flex; align-items: center; gap: 8px;">{icon("stop",15,INK)}Stop</button>' if stop
           else f'<button aria-label="Send" style="height: 40px; padding: 0 18px 0 16px; border-radius: 20px; border: 0; background: {ACCD}; color: #fff; font-size: 13.5px; font-weight: 700; display: flex; align-items: center; gap: 8px;">Send{icon("send",15,"#fff")}</button>')
    adv = ''
    if advanced:
        hf=''.join(face(w_,24,ring='0 0 0 1.5px rgba(255,255,255,.4)') for w_,away in hear if not away)
        af=''.join(f'<span style="display: flex; align-items: center; gap: 6px; color: {MUTED};">{face(w_,22,fstyle="filter: grayscale(1) brightness(.7);",extra_style="opacity: .55;")}{NAME[w_]} is away</span>' for w_,away in hear if away)
        chips=''.join(f'<button aria-pressed="{"true" if i==0 else "false"}" style="height: 30px; padding: 0 11px 0 {5 if c else 9}px; border-radius: 15px; display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; white-space: nowrap; border: 1px solid {"rgba(91,134,255,.7)" if i==0 else "rgba(168,190,255,.14)"}; background: {"rgba(91,134,255,.2)" if i==0 else "none"}; color: {INK};">{face(c,20) if c else icon(ic,13)}{l}</button>' for i,(l,c,ic) in enumerate([('Whoever fits',None,'users'),('Mike','mira',None),('Narrator',None,'quill')]))
        adv = f'''<div style="display: flex; align-items: center; justify-content: space-between; gap: 10px; padding-bottom: 10px; border-bottom: 1px solid rgba(168,190,255,.08); font-size: 12.5px;">
<span style="display: flex; align-items: center; gap: 8px;"><span style="display: flex; gap: 4px;">{hf}</span><b style="font-weight: 600;">Only Mike will hear this</b>{af}</span>
<span style="display: flex; align-items: center; gap: 6px;"><span style="font-size: 10.5px; font-weight: 700; letter-spacing: .1em; color: {MUTED};">ANSWERS</span>{chips}</span></div>'''
        meterbar = f'<div style="height: 3px; background: rgba(255,255,255,.08);"><div style="width: {meter}%; height: 3px; background: {ACC};"></div></div>'
    else:
        meterbar = ''
    extra_btns = (f'<button style="height: 32px; padding: 0 11px 0 9px; border-radius: 16px; border: 1px solid rgba(168,190,255,.14); background: none; color: {INK}; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 6px;">{icon("clock",14)}Pass time</button>'
                  f'<span style="font-size: 11.5px; color: {MUTED}; font-variant-numeric: tabular-nums;">~7,300 / 16,384 tokens</span>') if advanced else ''
    return f'''<div style="position: absolute; left: 20px; right: 20px; bottom: 20px; border-radius: 20px; overflow: hidden; color: {INK}; background: rgba(22,30,64,.94); border: 1px solid rgba(168,190,255,.14);">
{meterbar}<div style="padding: 14px 16px 12px; display: flex; flex-direction: column; gap: 10px;">
{adv}
<label style="display: block; min-height: 52px;"><span class="sr">Your line</span>{val}</label>
<div style="display: flex; align-items: center; justify-content: space-between; gap: 10px;">
<div style="display: flex; align-items: center; gap: 8px;"><div role="group" aria-label="Composer detail" style="display: flex; gap: 2px; padding: 2px; border-radius: 15px; background: rgba(0,0,0,.28);">{seg}</div>
<button aria-label="Continue the story" style="width: 32px; height: 32px; border-radius: 50%; border: 1px solid rgba(168,190,255,.14); background: none; color: {INK}; display: flex; align-items: center; justify-content: center;">{icon('ff',14)}</button>{extra_btns}</div>
<div style="display: flex; align-items: center; gap: 8px;">{modechip(mode,detected,open_)}{act}</div>
</div></div></div>'''

def chat(lines, comp, comp_h=150, x=CX, w=CW):
    return f'''<section aria-label="The story" style="position: absolute; left: {x}px; top: 16px; width: {w}px; height: {H-32}px; box-sizing: border-box; border-radius: 30px; overflow: hidden; color: {INK}; {PANEL}">
<div style="position: absolute; left: 0; right: 0; top: 0; bottom: {comp_h+36}px; padding: 24px 0 8px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: flex-end; overflow: hidden;">
<div style="width: 100%; max-width: 680px; margin: 0 auto; display: flex; flex-direction: column; gap: 2px;">
{lines}
</div></div>
<div style="position: absolute; left: 0; right: 0; top: 0; height: 70px; background: linear-gradient(180deg, rgba(10,16,40,.96), rgba(10,16,40,0)); pointer-events: none;"></div>
{comp}
</section>'''

# ------------------------------------------------ widgets
def wframe(x, y, w, inner, edit=False, pinned=True, dragging=False, h=None):
    hh = f'height: {h}px; ' if h else ''
    ring = f'outline: 2px dashed {ACC}; outline-offset: 3px;' if edit else ''
    if dragging: ring += ' transform: rotate(-1.5deg); box-shadow: 0 30px 60px rgba(0,0,0,.6);'
    ctl = ''
    if edit:
        ctl = f'''<div style="position: absolute; left: -12px; top: -14px; z-index: 3; width: 30px; height: 30px; border-radius: 10px; background: rgba(8,13,32,.8); color: {INK}; display: flex; align-items: center; justify-content: center; cursor: grab;" aria-label="Drag to move">{icon('drag',15)}</div>
<div style="position: absolute; right: -12px; top: -14px; z-index: 3; display: flex; gap: 6px;"><button aria-label="{"Unpin" if pinned else "Pin"}" aria-pressed="{"true" if pinned else "false"}" style="width: 30px; height: 30px; border-radius: 10px; border: 0; background: {"rgba(231,176,106,.9)" if pinned else "rgba(8,13,32,.8)"}; color: {"#2a1606" if pinned else INK}; display: flex; align-items: center; justify-content: center;">{icon('pushpin',14)}</button><button aria-label="Remove widget" style="width: 30px; height: 30px; border-radius: 10px; border: 0; background: #b8443a; color: #fff; display: flex; align-items: center; justify-content: center;">{icon('x',14)}</button></div>'''
    ov = 'visible' if edit else 'hidden'
    return f'<div style="position: absolute; left: {x}px; top: {y}px; width: {w}px; {hh}box-sizing: border-box; border-radius: 24px; overflow: {ov}; color: {INK}; z-index: 4; {GLASS}{ring}">{ctl}{inner}</div>'

def w_character(who, img, expr, mood, x=RX, y=84, w=WW, art=226, edit=False, pinned=True, state='present', thinking=False, badge=None, dragging=False):
    col = {'wary':ROSE,'doubtful':LILAC,'glad':SAGE,'thinking':SKY,'grinning':AMBER,'calm':SAGE,'uneasy':ROSE,'sour':ROSE}.get(expr, AMBER)
    grey = 'filter: grayscale(.9) brightness(.6);' if state=='away' else 'filter: saturate(1.02) brightness(.96);'
    pin = '' if edit else f'<button aria-label="{"Unpin" if pinned else "Pin"} {NAME[who]}" aria-pressed="{"true" if pinned else "false"}" style="position: absolute; right: 10px; top: 10px; width: 30px; height: 30px; border-radius: 50%; border: 0; background: rgba(8,13,32,.55); color: {AMBER if pinned else INK}; display: flex; align-items: center; justify-content: center;">{icon("pushpin",14, AMBER if pinned else INK)}</button>'
    th = f'<span style="position: absolute; left: 12px; top: 12px; height: 26px; padding: 0 10px; border-radius: 13px; background: rgba(8,13,32,.7); color: {SKY}; font-size: 11.5px; font-weight: 700; display: flex; align-items: center; gap: 5px;">{icon("thought",13,SKY)}thinking…</span>' if thinking else ''
    bd = f'<span style="position: absolute; left: 12px; top: 12px; height: 26px; padding: 0 10px; border-radius: 13px; background: {AMBER}; color: #2a1606; font-size: 11.5px; font-weight: 800; display: flex; align-items: center; gap: 5px;">{badge}</span>' if badge else ''
    inner = f'''<div style="position: relative; height: {art}px; overflow: hidden; border-radius: 24px 24px 0 0; background: linear-gradient(170deg, rgba(231,176,106,.2), rgba(8,13,32,.45));">
<img src="{A[img]}" alt="{NAME[who]}, {expr}" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: {FOCUS.get(img.split('-')[0], '50% 28%')}; {grey}">
<div style="position: absolute; inset: 0; background: linear-gradient(180deg, rgba(19,27,58,0) 60%, rgba(19,27,58,.9));"></div>{pin}{th}{bd}</div>
<div style="padding: 10px 14px 13px; display: flex; flex-direction: column; gap: 4px;">
<div style="display: flex; align-items: center; gap: 8px;"><span style="font-family: {SERIF}; font-size: 20px;">{NAME[who]}</span><span style="height: 20px; padding: 0 8px; border-radius: 10px; background: {col}22; color: {col}; font-size: 11px; font-weight: 700; display: flex; align-items: center;">{expr}</span></div>
<span style="font-size: 12.5px; color: {MUTED};">{mood}</span></div>'''
    return wframe(x,y,w,inner,edit,pinned,dragging)

def w_character_row(who, status, x=RX, y=420, w=WW, edit=False, pinned=False, grey=True, dragging=False):
    inner = f'<div style="display: flex; align-items: center; gap: 12px; padding: 10px 14px;">{face(who,40,fstyle="filter: grayscale(.9) brightness(.7);" if grey else "")}<span style="display: flex; flex-direction: column; gap: 1px;"><span style="font-size: 14px; font-weight: 700;">{NAME[who]}</span><span style="font-size: 12px; color: {MUTED};">{status}</span></span></div>'
    return wframe(x,y,w,inner,edit,pinned,dragging)

def w_clock(t='7:04 pm', rel='The evening it rained', t24='19:04', real='24 May · the café', kind='dusk', x=LX, y=654, w=WW, edit=False, hover=False, place='Halcyon Coffee'):
    if kind=='night':
        dot='<circle cx="60" cy="8" r="6" fill="#e3e9ff"/><circle cx="63" cy="6" r="5" fill="#1a2348"/>'
    else:
        dot='<circle cx="106" cy="30" r="6" fill="#ffb35a"/><circle cx="106" cy="30" r="12" fill="#ffb35a" opacity=".2"/>'
    arc=f'<svg width="96" height="32" viewBox="0 0 120 40" aria-hidden="true"><path d="M6 38 A56 56 0 0 1 114 38" fill="none" stroke="rgba(168,190,255,.3)" stroke-width="1.5" stroke-dasharray="3 4"/><path d="M0 38h120" stroke="rgba(168,190,255,.2)"/>{dot}</svg>'
    tip = f'<span style="position: absolute; left: 14px; top: -40px; white-space: nowrap; padding: 7px 11px; border-radius: 10px; background: #212b57; border: 1px solid rgba(168,190,255,.2); font-size: 12px; color: {INK}; box-shadow: 0 10px 24px rgba(0,0,0,.5);"><b>{t24}</b> · {real}</span>' if hover else ''
    inner = f'''<div style="position: relative; padding: 14px 16px 14px; display: flex; flex-direction: column; gap: 4px;">
<div style="display: flex; align-items: flex-end; justify-content: space-between;"><span style="position: relative; font-family: {SERIF}; font-size: 34px; line-height: 1; font-variant-numeric: tabular-nums;{" border-bottom: 1px dotted "+MUTED+";" if hover else ""}">{t}{tip}</span>{arc}</div>
<span style="font-size: 13.5px; font-weight: 600;">{rel}</span>
<div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px;"><span style="font-size: 12px; color: {MUTED};">{place}</span><button style="height: 30px; padding: 0 11px 0 9px; border-radius: 15px; border: 1px solid rgba(168,190,255,.16); background: none; color: {INK}; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 6px;">{icon('clock',13)}Pass time</button></div></div>'''
    return wframe(x,y,w,inner,edit)

def w_music(track='Rain on a café window', src='Matched to the scene', x=LX, y=806, w=WW, edit=False, open_=False, playing=True):
    bars=''.join(f'<span style="width: 3px; height: {h}px; border-radius: 2px; background: {AMBER}; display: block;"></span>' for h in (8,14,10,16,7))
    inner = f'''<div style="display: flex; align-items: center; gap: 12px; padding: 12px 14px;">
<button aria-label="{"Pause" if playing else "Play"}" style="width: 40px; height: 40px; border-radius: 50%; border: 0; background: rgba(231,176,106,.16); color: {AMBER}; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">{icon("stop" if playing else "ff",16,AMBER)}</button>
<button aria-haspopup="dialog" aria-expanded="{"true" if open_ else "false"}" style="flex-grow: 1; min-width: 0; border: 0; background: none; padding: 0; text-align: left; color: {INK}; display: flex; flex-direction: column; gap: 2px;"><span style="display: flex; align-items: center; gap: 8px; font-size: 13.5px; font-weight: 700; white-space: nowrap; min-width: 0;"><span style="overflow: hidden; text-overflow: ellipsis;">{track}</span><span style="display: flex; align-items: flex-end; gap: 2px; height: 16px;">{bars}</span></span><span style="font-size: 11.5px; color: {MUTED}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px;">{src}</span></button>
<button aria-label="Mute" style="width: 34px; height: 34px; border-radius: 50%; border: 0; background: none; color: {INK}; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">{icon("volume",16)}</button></div>'''
    return wframe(x,y,w,inner,edit)

def shell(title, inner):
    return page(title, W, H, f'<div style="width: {W}px; height: {H}px; position: relative; overflow: hidden; background: #0a1028; font-family: {SANS};">{inner}</div>')

# ------------------------------------------------ sample content
TIP02 = ('19:02','24 May · the evening it rained')
T0 = titlecard('Halcyon Coffee · the evening it rained')
def l02(**k): return line('aren','7:02 pm','Still open? I’ll take anything hot, I don’t care what.', **k)
def l04(**k): return line('mira','7:04 pm','*flips the sign back around and goes for a cup* Ten minutes. Drink it fast or I’m putting you to work.', **k)
def l06(**k): return line('tobin','7:06 pm','*drops his backpack on the counter* Did someone say free labour?', **k)
def l08(**k): return line('aren','7:08 pm','Theo, would you grab the milk from the back? All of it.', **k)
def l10(**k): return line('tobin','7:10 pm','*picks up the crates, grinning* Anything for a paying customer.', **k)
SECRET='Quickly, while he’s gone. My mother is the queen’s step-sister. I’m on the gala list and I don’t want to be. Tell no one.'
def l12(**k): return line('aren','7:12 pm',SECRET, **k)
def l14(**k): return line('mira','7:14 pm','*sets the cup down very carefully* Then stop saying it so loud. My mother cuts her hair.', **k)
R06 = reacts(react('feeling','Mike is wary of Theo', who='mira'))
R08 = reacts(react('feeling','Theo didn’t like that', who='tobin'))
R10 = reacts(react('feeling','Theo is suspicious of you', who='tobin'))
R12 = reacts(react('memory','Mike will remember this', who='mira'), react('warm','Mike trusts you a little more', who='mira'))
R14 = reacts(react('mood','Mike is worried for you', who='mira'))
LEFT = note('tobin','Theo went out to the back.', grey=True)
JOIN = note('tobin','Theo joins.')
files={}

def dusk_widgets(mira_img='mira', expr='calm', mood='Here · fond of you', tobin=None, clock=None, music=None, thinking=False, badge=None):
    out = w_character('mira', mira_img, expr, mood, thinking=thinking, badge=badge)
    if tobin: out += tobin
    out += clock if clock is not None else w_clock()
    out += music if music is not None else w_music()
    return out

# 1 · the default: full-height chat, widgets either side
lines = T0 + l02(hover=True, tip=TIP02) + l04()
files['Main.dc.html'] = shell('Scene · the chat and its widgets',
    place('gull-dusk') + corners()
    + chat(lines, composer())
    + dusk_widgets(tobin=w_character_row('tobin','Out back · could join', y=406)))

# 2 · Theo joins: his widget pops in
lines = T0 + l02() + l04() + JOIN + l06(extra=R06)
files['Scene-Group-Joins.dc.html'] = shell('Scene · Theo joins',
    place('gull-dusk') + corners()
    + chat(lines, composer())
    + w_character('mira','mira-wary','wary','Here · wary of Theo', art=150)
    + w_character('tobin','tobin','grinning','Joined · 2 min ago', y=346, art=150, pinned=False, badge='Joined')
    + w_clock(t='7:06 pm', t24='19:06') + w_music())

# 3 · the secret: feelings, not hearing
lines = l08(extra=R08) + l10(extra=R10) + LEFT + l12(extra=R12) + l14(extra=R14, hover=False)
files['Scene-Group-Secret.dc.html'] = shell('Scene · the secret',
    place('gull-dusk') + corners()
    + chat(lines, composer())
    + dusk_widgets('mira-wary','uneasy','Here · trust +6 this scene', tobin=w_character_row('tobin','Out back · away', y=406), clock=w_clock(t='7:14 pm', t24='19:14')))

# 4 · advanced composer: hearing + answering + receipts only here
rc = lambda: f'''<div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 9px;"><span style="display: inline-flex; align-items: center; gap: 6px; height: 26px; padding: 0 10px 0 3px; border-radius: 13px; background: rgba(255,255,255,.07); font-size: 12px;">{face('mira',20,ring='0 0 0 1.5px '+AMBER)}Mike heard it</span><span style="display: inline-flex; align-items: center; gap: 6px; height: 26px; padding: 0 10px 0 3px; border-radius: 13px; background: rgba(255,255,255,.07); font-size: 12px; color: {MUTED};"><span style="width: 20px; height: 20px; border-radius: 50%; border: 1.5px dashed rgba(168,190,255,.45); box-sizing: border-box; font-size: 9px; font-weight: 700; display: flex; align-items: center; justify-content: center;">T</span>Theo wasn’t there</span></div>'''
lines = l08(extra=R08) + l10() + LEFT + l12(hover=True, extra=rc()+R12) + l14(extra=R14)
files['Scene-Advanced.dc.html'] = shell('Scene · advanced composer',
    place('gull-dusk') + corners()
    + chat(lines, composer(advanced=True, hear=(('mira',False),('tobin',True))), comp_h=210)
    + dusk_widgets('mira-wary','uneasy','Here · trust +6 this scene', tobin=w_character_row('tobin','Out back · away', y=406), clock=w_clock(t='7:14 pm', t24='19:14')))

# 5 · the Auto mode picker
modes = [('Auto','spark','Reads your formatting','*action*  “speech”  (thought)',True),('Say','quote','Speak out loud','plain text',False),('Do','hand','An action','*like this*',False),('Whisper','ear','Only one person hears','@Mike like this',False),('Think','thought','No one hears','(like this)',False),('Narrate','quill','Direct the story','>> like this',False)]
mi=''.join(f'<button role="menuitemradio" aria-checked="{"true" if on else "false"}" style="display: flex; align-items: center; gap: 12px; width: 100%; padding: 9px 12px; border: 0; border-radius: 12px; background: {"rgba(231,176,106,.12)" if on else "none"}; color: {INK}; text-align: left;"><span style="width: 30px; height: 30px; border-radius: 10px; background: rgba(255,255,255,.06); display: flex; align-items: center; justify-content: center; color: {AMBER if on else INK};">{icon(ic,15)}</span><span style="display: flex; flex-direction: column; gap: 1px; flex-grow: 1;"><span style="font-size: 13.5px; font-weight: 700;">{l}</span><span style="font-size: 11.5px; color: {MUTED};">{d}</span></span><code style="font-family: {MONO}; font-size: 11px; color: {MUTED};">{syn}</code>{icon("check",15,AMBER) if on else ""}</button>' for l,ic,d,syn,on in modes)
menu = f'<div role="menu" aria-label="How your line is read" style="position: absolute; left: {CX+800-20-120-400}px; top: {H-16-20-150-384}px; width: 400px; padding: 8px; box-sizing: border-box; border-radius: 18px; z-index: 12; background: rgba(22,30,64,.98); border: 1px solid rgba(168,190,255,.18); box-shadow: 0 24px 60px rgba(0,0,0,.6); display: flex; flex-direction: column; gap: 2px;">{mi}<span style="font-size: 11px; color: {MUTED}; padding: 8px 12px 4px; line-height: 1.4;">Auto works it out from how you write. Pick a mode to override it for this line.</span></div>'
lines = l08(extra=R08) + l10(extra=R10) + LEFT + l12(extra=R12) + l14(extra=R14)
files['Scene-ModePicker.dc.html'] = shell('Scene · Auto and the mode picker',
    place('gull-dusk') + corners()
    + chat(lines, composer(text='*leans over the counter* Then don’t tell anyone you saw me here.', detected='Do + Say', open_=True))
    + menu
    + dusk_widgets('mira-wary','uneasy','Here · trust +6 this scene', tobin=w_character_row('tobin','Out back · away', y=406), clock=w_clock(t='7:14 pm', t24='19:14')))

# 6 · edit a line: edit vs edit and regenerate
editbox = f'''<div style="margin-top: 8px; padding: 12px; border-radius: 14px; background: rgba(0,0,0,.28); border: 1px solid rgba(231,176,106,.45); display: flex; flex-direction: column; gap: 10px;">
<label><span class="sr">Edit line</span><span style="font-family: {SERIF}; font-size: 18px; line-height: 1.5; color: {INK};">Theo, would you grab the milk from the back? All of it. Take your time.</span><span style="display: inline-block; width: 2px; height: 20px; background: {ACC}; vertical-align: -4px;"></span></label>
<div style="display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px; border-radius: 12px; background: rgba(231,176,106,.1); border: 1px solid rgba(231,176,106,.3); font-size: 12.5px; line-height: 1.45;">{icon('alert',16,AMBER)}<span><b style="color: {AMBER};">Regenerating from here rewrites the 5 messages after this one.</b> They’ll be kept as the previous take, so you can flip back.</span></div>
<div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;"><button style="height: 36px; padding: 0 12px; border: 0; background: none; color: {MUTED}; font-size: 12.5px; font-weight: 600;">Cancel</button>
<div style="display: flex; gap: 8px;"><button style="height: 36px; padding: 0 14px; border-radius: 18px; border: 1px solid rgba(168,190,255,.2); background: none; color: {INK}; font-size: 12.5px; font-weight: 700; display: flex; flex-direction: column; justify-content: center; line-height: 1.1;">Save edit</button>
<button style="height: 36px; padding: 0 14px; border-radius: 18px; border: 0; background: {AMBER}; color: #2a1606; font-size: 12.5px; font-weight: 700; display: flex; align-items: center; gap: 6px;">{icon('refresh',14,'#2a1606')}Save and regenerate from here</button></div></div>
<span style="font-size: 11.5px; color: {MUTED};"><b style="color: {INK}; font-weight: 600;">Save edit</b> only changes what the model reads from now on. The story after it stays as written.</span></div>'''
edit_line = f'''<article style="position: relative; display: flex; flex-direction: column; padding: 12px 14px; margin: 0 -14px; border-radius: 14px; background: rgba(255,255,255,.05);">
<div style="display: flex; align-items: baseline; gap: 10px;"><span style="font-size: 13px; font-weight: 700; color: {SPK['aren']};">Liv</span>{stamp('7:08 pm')}<span style="font-size: 11px; color: {AMBER}; font-weight: 700;">editing</span></div>{editbox}</article>'''
lines = JOIN + l06(extra=R06) + edit_line + l10(dim=True) + note('tobin','Theo went out to the back.', grey=True) + l12(dim=True) + l14(dim=True)
files['Scene-EditLine.dc.html'] = shell('Scene · editing a line',
    place('gull-dusk') + corners()
    + chat(lines, composer())
    + dusk_widgets('mira-wary','uneasy','Here · trust +6 this scene', tobin=w_character_row('tobin','Out back · away', y=406), clock=w_clock(t='7:14 pm', t24='19:14')))

# 7 · a reply arriving
caret = f'<span style="display: inline-block; width: 9px; height: 20px; margin-left: 3px; vertical-align: -3px; background: {AMBER}; border-radius: 2px;"></span>'
stream = f'''<article style="display: flex; flex-direction: column; padding: 12px 14px; margin: 0 -14px;">
<div style="display: flex; align-items: baseline; gap: 10px;"><span style="font-size: 13px; font-weight: 700; color: {SPK['mira']};">Mike</span><span style="font-size: 12px; color: {AMBER};">writing…</span></div>
<p style="margin: 6px 0 0; font-family: {SERIF}; font-size: 19px; line-height: 1.55; color: {INK};"><em style="color: #c6d0ec;">sets the cup down very carefully</em> Then stop saying{caret}</p>
<button style="align-self: flex-start; margin-top: 8px; height: 26px; padding: 0 10px; border-radius: 13px; border: 1px solid rgba(168,190,255,.2); background: none; color: {MUTED}; font-size: 12px; display: flex; align-items: center; gap: 6px;">{icon('thought',13)}Thought for 4 s</button></article>'''
lines = l08(extra=R08) + l10(extra=R10) + LEFT + l12() + stream
files['Scene-Reply.dc.html'] = shell('Scene · a reply arriving',
    place('gull-dusk') + corners()
    + chat(lines, composer(stop=True))
    + dusk_widgets('mira-thinking','thinking','Choosing his words', thinking=True, tobin=w_character_row('tobin','Out back · away', y=406), clock=w_clock(t='7:14 pm', t24='19:14')))

# 8 · time skip, readable
skip = f'''<div aria-hidden="false" style="position: absolute; inset: 0; z-index: 20;"><div style="position: absolute; inset: 0; background: rgba(8,13,34,.84);"></div>
<img src="{A['clouds']}" alt="" style="position: absolute; left: -220px; top: -330px; width: 1880px; height: 1175px; opacity: .7; filter: brightness(.5) saturate(.35);">
<img src="{A['clouds']}" alt="" style="position: absolute; left: -140px; top: 300px; width: 1720px; height: 1075px; opacity: .7; filter: brightness(.45) saturate(.35); transform: scaleX(-1);">
<div style="position: absolute; left: 0; bottom: 0; width: 1440px; height: 300px; background: linear-gradient(180deg, rgba(10,16,40,0), #0a1028 70%);"></div>
<div role="status" style="position: absolute; left: 440px; top: 226px; width: 560px; box-sizing: border-box; padding: 34px 40px 30px; border-radius: 32px; background: #131b3a; border: 1px solid rgba(168,190,255,.16); box-shadow: 0 30px 80px rgba(0,0,0,.55); display: flex; flex-direction: column; align-items: center; gap: 16px; color: {INK}; text-align: center;">
<span style="font-size: 12px; font-weight: 800; letter-spacing: .22em; text-transform: uppercase; color: #a6b3d6;">Two Sugars, No Title</span>
<span style="font-family: {SERIF}; font-style: italic; font-size: 68px; line-height: 1; color: {INK};">Three weeks later</span>
<div style="display: flex; align-items: center; gap: 12px; font-size: 16px; color: {INK};"><span style="color: #a6b3d6;">The evening it rained</span>{icon('arrow',18,'#a6b3d6')}<b>Three weeks later · the gala</b></div>
<span style="font-size: 14px; color: #c6d0ec;">Mike’s memory of that evening is going hazy.</span>
<button style="height: 44px; padding: 0 20px; border-radius: 22px; border: 1px solid rgba(168,190,255,.16); background: #1a2348; color: {INK}; font-size: 14px; font-weight: 700; display: flex; align-items: center; gap: 8px;">{icon('undo',16,INK)}Undo</button>
</div></div>'''
files['Scene-TimeSkip.dc.html'] = shell('Scene · three weeks later',
    place('gull-dusk', blur=8) + chat(l12(extra=R12) + l14(extra=R14), composer()) + dusk_widgets('mira-wary','uneasy','') + skip)

# 9 · after the skip
lines = l14(dim=True) \
    + titlecard('Three weeks later · Corvel Palace', f'<button style="height: 24px; padding: 0 9px; border-radius: 12px; border: 1px solid rgba(168,190,255,.25); background: none; color: {MUTED}; font-size: 11px; display: flex; align-items: center; gap: 4px;">{icon("undo",11)}Undo</button>') \
    + line('mira','7:18 pm','You? *he looks at the jacket he borrowed, then at you* The list. You said you weren’t coming to this.', spark=True, tip=('19:18','Three weeks after the café · the night of the gala'),
           extra=recallbox('mira','MIKE REMEMBERED, VAGUELY','She didn’t want to be on the gala list.','sharp 3 weeks ago · hazy now · witnessed') + reacts(react('warm','Mike is glad to see you', who='mira'))) \
    + line('aren','7:20 pm','I never said that. I said I didn’t want to be on it.') \
    + line('mira','7:22 pm','*frowns* …I could have sworn. Three weeks is a long time to hold one sentence.', extra=reacts(react('belief','Mike has his doubts', who='mira')))
AFTER = lines
files['Scene-AfterSkip.dc.html'] = shell('Scene · three weeks later, the gala',
    place('gull-night', tint='#2a4a9a', tint_op=.12) + corners()
    + chat(lines, composer())
    + w_character('mira','mira-doubtful','doubtful','Here · doubt +12 this scene')
    + w_character_row('tobin','Not invited · three weeks', y=406)
    + w_clock(t='7:22 pm', rel='Three weeks later · the gala', t24='19:22', real='14 June · night two of the gala', kind='night', hover=True, place='Corvel Palace')
    + w_music(track='A string quartet, two rooms away'))

# 10 · the music picker
tracks=[('A string quartet, two rooms away','Matched to Corvel Palace',True),('Rain on a café window','Ambience',False),('Espresso machine, low murmur','Ambience',False),('Late night drive','Music · slow',False),('Liv’s stadium playlist','Music · your upload',False)]
ti=''.join(f'<button role="menuitemradio" aria-checked="{"true" if on else "false"}" style="display: flex; align-items: center; gap: 12px; width: 100%; padding: 9px 10px; border: 0; border-radius: 12px; background: {"rgba(231,176,106,.12)" if on else "none"}; color: {INK}; text-align: left;"><span style="width: 32px; height: 32px; border-radius: 9px; background: rgba(255,255,255,.06); display: flex; align-items: center; justify-content: center; color: {AMBER if on else INK};">{icon("volume" if on else "ff",14)}</span><span style="display: flex; flex-direction: column; gap: 1px; flex-grow: 1;"><span style="font-size: 13.5px; font-weight: 700;">{t}</span><span style="font-size: 11.5px; color: {MUTED};">{s}</span></span>{icon("check",15,AMBER) if on else ""}</button>' for t,s,on in tracks)
picker = f'''<div role="dialog" aria-label="Choose music" style="position: absolute; left: {LX}px; top: 330px; width: 360px; padding: 10px; box-sizing: border-box; border-radius: 20px; z-index: 12; background: rgba(22,30,64,.98); border: 1px solid rgba(168,190,255,.18); box-shadow: 0 24px 60px rgba(0,0,0,.6); display: flex; flex-direction: column; gap: 4px; color: {INK};">
<div style="display: flex; flex-direction: column; gap: 8px; padding: 6px 8px 8px;"><span style="font-size: 14px; font-weight: 800;">Music and ambience</span><label style="display: flex; align-items: center; gap: 8px; font-size: 12px; color: {MUTED};">Match the scene<span style="position: relative; width: 34px; height: 18px; border-radius: 9px; background: {AMBER}; display: block;"><span style="position: absolute; top: 2px; left: 18px; width: 14px; height: 14px; border-radius: 50%; background: #fff; display: block;"></span></span></label></div>
{ti}
<div style="height: 1px; background: rgba(168,190,255,.1); margin: 6px 0;"></div>
<button style="display: flex; align-items: center; gap: 10px; width: 100%; padding: 10px; border: 1px dashed rgba(168,190,255,.28); border-radius: 12px; background: none; color: {INK}; font-size: 13px; font-weight: 700;">{icon('download',16)}Upload a track…<span style="margin-left: auto; font-size: 11px; font-weight: 500; color: {MUTED};">mp3, ogg, wav</span></button>
<div style="display: flex; align-items: center; gap: 10px; padding: 8px 10px 4px; font-size: 12px; color: {MUTED};">{icon('volume',14)}<span style="flex-grow: 1; height: 4px; border-radius: 2px; background: linear-gradient(90deg, {AMBER} 62%, rgba(255,255,255,.12) 62%); display: block;"></span>62%</div>
</div>'''
files['Scene-MusicPicker.dc.html'] = shell('Scene · choosing music',
    place('gull-night', tint='#2a4a9a', tint_op=.12) + corners()
    + chat(AFTER, composer())
    + w_character('mira','mira-doubtful','doubtful','Here · doubt +12 this scene')
    + w_character_row('tobin','Not invited · three weeks', y=406)
    + w_clock(t='7:22 pm', rel='Three weeks later · the gala', t24='19:22', real='14 June · night two of the gala', kind='night', place='Corvel Palace')
    + w_music(track='A string quartet, two rooms away', src='Matched to Corvel Palace', open_=True) + picker)

# 11 · the story menu
mitems=[('layers','Edit widgets','Move, pin, remove or add'),('book','Reading mode','Just the story'),('image','Scene and place',''),('settings','Story settings',''),('download','Export story','')]
mm=''.join(f'<button role="menuitem" style="display: flex; align-items: center; gap: 12px; width: 100%; padding: 10px 12px; border: 0; border-radius: 12px; background: {"rgba(231,176,106,.12)" if i==0 else "none"}; color: {INK}; text-align: left;">{icon(ic,17, AMBER if i==0 else INK)}<span style="display: flex; flex-direction: column; flex-grow: 1;"><span style="font-size: 14px; font-weight: 700;">{l}</span>{("<span style=&#34;font-size: 11.5px; color: "+MUTED+";&#34;>"+d+"</span>") if d else ""}</span></button>' for i,(ic,l,d) in enumerate(mitems))
mm=mm.replace('&#34;','"')
menu2 = f'''<div role="menu" aria-label="Story menu" style="position: absolute; right: 24px; top: 72px; width: 260px; padding: 8px; box-sizing: border-box; border-radius: 18px; z-index: 12; background: rgba(22,30,64,.98); border: 1px solid rgba(168,190,255,.18); box-shadow: 0 24px 60px rgba(0,0,0,.6); display: flex; flex-direction: column; gap: 2px;">{mm}
<div style="height: 1px; background: rgba(168,190,255,.1); margin: 4px 0;"></div>
<button role="menuitem" style="display: flex; align-items: center; gap: 12px; width: 100%; padding: 10px 12px; border: 0; border-radius: 12px; background: none; color: #f08a7a; font-size: 14px; font-weight: 700;">{icon('x',17,'#f08a7a')}Delete story</button></div>'''
lines = T0 + l02() + l04()
files['Scene-Menu.dc.html'] = shell('Scene · story menu',
    place('gull-dusk') + corners(menu_open=True)
    + chat(lines, composer())
    + dusk_widgets(tobin=w_character_row('tobin','Out back · could join', y=406)) + menu2)

# 12 · edit widgets
dots = 'background-image: radial-gradient(rgba(168,190,255,.18) 1px, transparent 1.2px); background-size: 24px 24px;'
types=[('user','Character','Pick who. Add as many as you like.'),('clock','Story clock','Time, and how it relates to the story'),('volume','Music','What’s playing, and a picker'),('image','Place','The scene, full colour'),('users','Cast','Everyone here, as faces'),('edit','Notes','Your own notes for this story')]
ty=''.join(f'<button style="display: flex; align-items: center; gap: 12px; width: 100%; padding: 9px 10px; border: 0; border-radius: 12px; background: {"rgba(231,176,106,.12)" if i==0 else "none"}; color: {INK}; text-align: left;"><span style="width: 34px; height: 34px; border-radius: 10px; background: rgba(255,255,255,.06); display: flex; align-items: center; justify-content: center;">{icon(ic,16)}</span><span style="display: flex; flex-direction: column; gap: 1px; flex-grow: 1;"><span style="font-size: 13.5px; font-weight: 700;">{l}</span><span style="font-size: 11.5px; color: {MUTED};">{d}</span></span>{icon("plus",16,AMBER)}</button>' for i,(ic,l,d) in enumerate(types))
pickwho=''.join(f'<button style="display: flex; align-items: center; gap: 6px; height: 32px; padding: 0 10px 0 4px; border-radius: 16px; border: 1px solid rgba(168,190,255,.16); background: none; color: {INK}; font-size: 12px; font-weight: 600;">{face(w_,24)}{NAME[w_]}</button>' for w_ in ('mira','tobin','ilsa','oren'))
tray = f'''<div role="dialog" aria-label="Add a widget" style="position: absolute; left: {LX}px; top: 150px; width: 300px; padding: 10px; box-sizing: border-box; border-radius: 20px; z-index: 12; background: rgba(22,30,64,.98); border: 1px solid rgba(168,190,255,.18); box-shadow: 0 24px 60px rgba(0,0,0,.6); display: flex; flex-direction: column; gap: 2px; color: {INK};">
<span style="font-size: 14px; font-weight: 800; padding: 6px 8px 8px;">Add a widget</span>{ty}
<div style="margin: 6px 4px 4px; padding: 10px; border-radius: 12px; background: rgba(255,255,255,.04); display: flex; flex-direction: column; gap: 8px;"><span style="font-size: 11.5px; color: {MUTED};">Character widget for…</span><div style="display: flex; flex-wrap: wrap; gap: 6px;">{pickwho}</div></div></div>'''
bar = f'''<div style="position: absolute; left: 50%; top: 20px; transform: translateX(-50%); z-index: 13; display: flex; align-items: center; gap: 10px; height: 48px; padding: 0 8px 0 18px; border-radius: 24px; background: rgba(22,30,64,.98); border: 1px solid rgba(231,176,106,.5); box-shadow: 0 16px 40px rgba(0,0,0,.5); color: {INK}; font-size: 13.5px; font-weight: 700; white-space: nowrap;">{icon('layers',16,AMBER)}Editing widgets<span style="font-weight: 500; color: {MUTED};">Drag anywhere · pinned ones stay visible, unpinned ones appear when something happens</span>
<button style="height: 34px; padding: 0 14px; border-radius: 17px; border: 1px solid rgba(168,190,255,.2); background: none; color: {INK}; font-size: 12.5px; font-weight: 700;">Reset layout</button><button style="height: 34px; padding: 0 16px; border-radius: 17px; border: 0; background: {AMBER}; color: #2a1606; font-size: 12.5px; font-weight: 800;">Done</button></div>'''
addbtn = f'<button style="position: absolute; left: {LX}px; top: 92px; z-index: 12; height: 44px; padding: 0 16px 0 12px; border-radius: 22px; border: 1px dashed {AMBER}; background: rgba(22,30,64,.9); color: {AMBER}; font-size: 13.5px; font-weight: 800; display: flex; align-items: center; gap: 8px;">{icon("plus",16,AMBER)}Add widget</button>'
lines = T0 + l02() + l04()
files['Scene-EditWidgets.dc.html'] = shell('Scene · editing widgets',
    place('gull-dusk') + f'<div style="position: absolute; inset: 0; {dots} background-color: rgba(0,0,0,.35);"></div>'
    + f'<div inert aria-hidden="true" data-inactive style="opacity: .5;">{chat(lines, composer())}</div>'
    + w_character('mira','mira','calm','Here · fond of you', edit=True)
    + w_character_row('tobin','At the bar · could join', x=820, y=150, edit=True, pinned=False, dragging=True)
    + f'<div style="position: absolute; left: {RX}px; top: 406px; width: {WW}px; height: 64px; box-sizing: border-box; border-radius: 24px; border: 2px dashed rgba(168,190,255,.25); z-index: 3;"></div>'
    + w_clock(edit=True) + w_music(edit=True)
    + bar + addbtn + tray)

# 13 · her card
def prow(ic,k,v): return f'<div style="display: flex; align-items: flex-start; gap: 10px;"><span style="color: {MUTED}; display: flex; padding-top: 1px;">{icon(ic,15)}</span><span style="width: 74px; font-size: 12px; color: {MUTED}; flex-shrink: 0;">{k}</span><span style="font-size: 13.5px; color: {INK};">{v}</span></div>'
def feel(l,v,c): return f'<div style="display: flex; align-items: center; gap: 10px; font-size: 12.5px;"><span style="width: 86px; color: {MUTED};">{l}</span><span style="flex-grow: 1; height: 6px; border-radius: 3px; background: rgba(255,255,255,.08); display: block;"><span style="width: {v}%; height: 6px; border-radius: 3px; background: {c}; display: block;"></span></span></div>'
card = f'''<div role="dialog" aria-label="Mike" style="position: absolute; left: 510px; top: 64px; width: 420px; border-radius: 26px; color: {INK}; z-index: 8; display: flex; flex-direction: column; gap: 16px; padding-bottom: 18px; {GLASS} background: rgba(19,27,58,.94); box-shadow: 0 30px 80px rgba(0,0,0,.6);">
<div style="position: relative; height: 220px; border-radius: 26px 26px 0 0; overflow: hidden; background: linear-gradient(170deg, rgba(231,176,106,.22), rgba(8,13,32,.5));">
<img src="{A['mira-doubtful']}" alt="Mike, doubtful" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 24%;">
<div style="position: absolute; inset: 0; background: linear-gradient(180deg, rgba(19,27,58,0) 50%, rgba(19,27,58,.95));"></div>
<div style="position: absolute; left: 18px; bottom: 10px; display: flex; align-items: center; gap: 10px;"><span style="font-family: {SERIF}; font-size: 28px;">Mike</span><span style="height: 22px; padding: 0 9px; border-radius: 11px; background: rgba(203,184,255,.18); color: {LILAC}; font-size: 11.5px; font-weight: 700; display: flex; align-items: center;">doubtful</span><span style="font-size: 12px; color: {MUTED};">Barista</span></div>
<div style="position: absolute; right: 12px; top: 12px; display: flex; gap: 6px;"><button style="height: 34px; padding: 0 12px; border-radius: 17px; border: 1px solid rgba(168,190,255,.25); background: rgba(8,13,32,.5); color: {INK}; font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px;">{icon('plus',14)}Add as widget</button><button aria-label="Close" style="width: 34px; height: 34px; border-radius: 50%; border: 0; background: rgba(255,255,255,.1); color: {INK}; display: flex; align-items: center; justify-content: center;">{icon('x',16)}</button></div></div>
<div style="padding: 0 18px; display: flex; flex-direction: column; gap: 8px;"><span style="font-size: 11px; font-weight: 700; letter-spacing: .12em; color: {MUTED};">RIGHT NOW</span>
{prow('map-pin','Where','Corvel Palace')}{prow('book','Scene','the gala · three weeks later')}{prow('clock','Here since','7:14 pm')}</div>
<div style="padding: 0 18px; display: flex; flex-direction: column; gap: 8px;"><span style="font-size: 11px; font-weight: 700; letter-spacing: .12em; color: {MUTED};">HOW HE FEELS ABOUT YOU</span>
{feel('Warmth',72,SAGE)}{feel('Trust',54,AMBER)}{feel('Doubt',46,LILAC)}</div>
<div style="padding: 0 18px; display: flex; flex-direction: column; gap: 6px;"><span style="font-size: 11px; font-weight: 700; letter-spacing: .12em; color: {MUTED};">HOLDING ONTO · 3 OF 41</span><span style="font-family: {SERIF}; font-size: 16px;">She says she never said it. <span style="font-family: inherit; font-size: 11px; font-weight: 700; letter-spacing: .06em; color: {LILAC};">DOUBTED</span></span></div>
<div style="padding: 0 18px; display: flex; gap: 8px; flex-wrap: wrap;"><span style="height: 28px; padding: 0 12px; border-radius: 14px; background: rgba(169,220,184,.12); color: {SAGE}; font-size: 12.5px; font-weight: 600; display: flex; align-items: center;">Fond of Liv</span><span style="height: 28px; padding: 0 12px; border-radius: 14px; background: rgba(244,165,149,.12); color: {ROSE}; font-size: 12.5px; font-weight: 600; display: flex; align-items: center;">Wary of Theo</span></div>
<div style="margin: 0 18px; padding: 12px 14px; border-radius: 14px; background: rgba(255,255,255,.04); border: 1px solid rgba(168,190,255,.12); display: flex; align-items: center; gap: 12px;">{icon("lock",18,MUTED)}<span style="flex-grow: 1; display: flex; flex-direction: column; gap: 4px;"><span style="font-size: 12px; font-weight: 700; color: {MUTED}; letter-spacing: .06em;">ONLY MIKE KNOWS THIS</span><span style="font-family: {SERIF}; font-size: 15px; filter: blur(5px);">He cuts the queen’s hair now. His mother’s hands shake.</span></span><button style="height: 32px; padding: 0 12px; border-radius: 16px; border: 1px solid rgba(168,190,255,.25); background: none; color: {INK}; font-size: 12px; font-weight: 600;">Reveal</button></div>
<div style="padding: 0 18px; display: flex; gap: 8px;"><button style="flex-grow: 1; height: 44px; border-radius: 22px; border: 0; background: {AMBER}; color: #2a1606; font-size: 13.5px; font-weight: 700;">Let him answer next</button><button style="height: 44px; padding: 0 16px; border-radius: 22px; border: 1px solid rgba(168,190,255,.2); background: none; color: {INK}; font-size: 13.5px; font-weight: 600;">Send away</button><button aria-label="Edit Mike" style="width: 44px; height: 44px; border-radius: 22px; border: 1px solid rgba(168,190,255,.2); background: none; color: {INK}; display: flex; align-items: center; justify-content: center;">{icon('edit',16)}</button></div>
</div>'''
files['Scene-Peek.dc.html'] = shell('Scene · Mike’s card',
    place('gull-night', tint='#2a4a9a', tint_op=.12) + corners()
    + chat(AFTER, composer())
    + w_character('mira','mira-doubtful','doubtful','Here · doubt +12 this scene')
    + w_clock(t='7:22 pm', rel='Three weeks later · the gala', t24='19:22', real='14 June · night two of the gala', kind='night', place='Corvel Palace') + w_music(track='A string quartet, two rooms away')
    + '<div style="position: absolute; inset: 0; background: rgba(4,7,20,.55); z-index: 7;"></div>' + card)

# 14 · backstage: the mind first
BP='#8cc3ff'; BPD='rgba(140,195,255,.28)'; BT='#e4f0ff'; BM='#9db8d8'; GOLD='#ffd08a'
PNL=f'background: rgba(8,28,54,.88); border: 1px solid {BPD}; border-radius: 16px;'
def pt(t, extra=''): return f'<div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px 10px; border-bottom: 1px dashed {BPD};"><span style="font-family: {MONO}; font-size: 12px; letter-spacing: .14em; color: {BP};">{t}</span>{extra}</div>'
def bb(t, ic=None, primary=False): return f'<button style="height: 28px; padding: 0 10px; border-radius: 8px; border: 1px solid {BP if primary else BPD}; background: {"rgba(140,195,255,.16)" if primary else "none"}; color: {BT}; font-family: {MONO}; font-size: 11px; display: flex; align-items: center; gap: 6px; white-space: nowrap;">{icon(ic,12) if ic else ""}{t}</button>'

# nodes: id -> (x, y, w, label, detail, activation, hot)
N = {
 'in1':(24,70,190,'HEARD','Liv: “I never said that”',.92,True),
 'in2':(24,168,190,'SAW','Liv here, three weeks later',.88,True),
 'in3':(24,266,190,'PLACE','Corvel Palace · the gala',.34,False),
 'in4':(24,364,190,'TIME','Three weeks since the café',.70,False),
 'p1':(258,118,180,'PERCEPTION','A claim that clashes with what she knows',.86,True),
 'p2':(258,284,180,'ATTENTION','On Liv, not the room',.78,False),
 'm1':(482,40,170,'RECALL','“Not coming to the gala” · hazy',.42,True),
 'm2':(482,132,170,'FEELING','Warmth .72 · doubt .46',.74,True),
 'm3':(482,224,170,'BELIEF','What she said that night: contested',.61,True),
 'm4':(482,316,170,'GOALS','Protect his mother · see her again',.57,False),
 'm5':(482,408,170,'PERSONA','Terse, wry, keeps his head down',.50,False),
 'd1':(690,150,150,'INTENT','Question it, gently',.81,True),
 'd2':(690,280,150,'EXPRESSION','doubtful',.66,True),
}
E = [('in1','p1',.9),('in2','p2',.7),('in2','m2',.6),('in3','p2',.2),('in4','m1',.5),('p1','m1',.7),('p1','m3',.85),('p1','m2',.4),('p2','m2',.5),('p2','m5',.3),
     ('m1','m3',.6),('m2','d1',.55),('m3','d1',.9),('m4','d1',.45),('m5','d1',.35),('m2','d2',.6),('m3','d2',.5)]
def center(n, side):
    x,y,w,*_ = N[n]; h=74
    return (x+w, y+h/2) if side=='r' else (x, y+h/2)
edges=''
for a,b,wt in E:
    x1,y1=center(a,'r'); x2,y2=center(b,'l'); mx=(x1+x2)/2
    hot = N[a][6] and N[b][6] and wt>=.55
    edges+=f'<path d="M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}" fill="none" stroke="{GOLD if hot else BP}" stroke-opacity="{.85 if hot else .35}" stroke-width="{1+wt*3:.1f}"/>'
nodes=''
for k,(x,y,w,l,d,a,hot) in N.items():
    nodes+=f'''<div style="position: absolute; left: {x}px; top: {y}px; width: {w}px; height: 74px; box-sizing: border-box; padding: 9px 11px; border-radius: 12px; background: rgba(6,32,63,.95); border: 1px solid {GOLD if hot else BPD}; {"box-shadow: 0 0 18px rgba(231,176,106,.25);" if hot else ""} display: flex; flex-direction: column; gap: 5px;">
<span style="display: flex; justify-content: space-between; font-family: {MONO}; font-size: 10px; letter-spacing: .12em; color: {GOLD if hot else BP};"><span>{l}</span><span>{a:.2f}</span></span>
<span style="font-size: 12px; line-height: 1.3; color: {BT};">{d}</span>
<span style="height: 3px; border-radius: 2px; background: rgba(140,195,255,.15); display: block; margin-top: auto;"><span style="width: {a*100:.0f}%; height: 3px; border-radius: 2px; background: {GOLD if hot else BP}; display: block;"></span></span></div>'''
out = f'''<div style="position: absolute; left: 24px; top: 500px; width: 816px; padding: 12px 16px; box-sizing: border-box; border-radius: 12px; border: 1px dashed {GOLD}; background: rgba(231,176,106,.06); display: flex; align-items: center; gap: 14px;">
<span style="font-family: {MONO}; font-size: 10px; letter-spacing: .12em; color: {GOLD};">SPOKE</span><span style="font-family: {SERIF}; font-size: 17px; color: {BT}; flex-grow: 1;"><em>frowns</em> …I could have sworn. Three weeks is a long time to hold one sentence.</span><span style="font-family: {MONO}; font-size: 11px; color: {BM};">1.9 s · 64 tok</span></div>'''
def spark_line(vals, col):
    pts=' '.join(f'{i*(760/(len(vals)-1)):.0f},{60-v*74:.0f}' for i,v in enumerate(vals))
    return f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round"/>'
feel = f'''<div style="position: absolute; left: 24px; top: 588px; width: 816px; box-sizing: border-box; padding: 10px 16px 12px; border-radius: 12px; border: 1px solid {BPD};">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;"><span style="font-family: {MONO}; font-size: 10px; letter-spacing: .12em; color: {BP};">HOW HE FEELS ABOUT LIV, ACROSS THE STORY</span><span style="display: flex; gap: 14px; font-family: {MONO}; font-size: 10.5px; color: {BM};"><span style="color: #a9e0c8;">— warmth</span><span style="color: {GOLD};">— trust</span><span style="color: #c7b8ff;">— doubt</span></span></div>
<svg width="780" height="64" viewBox="0 0 780 64" aria-hidden="true" style="display: block;"><line x1="470" y1="0" x2="470" y2="56" stroke="{BPD}" stroke-dasharray="3 4"/><text x="476" y="10" fill="{BM}" font-family="JetBrains Mono, monospace" font-size="10">three weeks later</text>
{spark_line([.40,.45,.52,.55,.62,.68,.66,.60,.64,.72],'#a9e0c8')}{spark_line([.30,.34,.40,.48,.60,.66,.64,.50,.52,.54],GOLD)}{spark_line([.10,.12,.15,.12,.10,.08,.10,.30,.40,.46],'#c7b8ff')}</svg></div>'''
tabs=''.join(f'<button aria-pressed="{"true" if w_=="mira" else "false"}" style="height: 30px; padding: 0 11px 0 4px; border-radius: 15px; border: 1px solid {BP if w_=="mira" else BPD}; background: {"rgba(140,195,255,.14)" if w_=="mira" else "none"}; color: {BT}; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 6px;">{face(w_,22)}{NAME[w_]}</button>' for w_ in ('mira','tobin'))
tabs+=f'<button style="height: 30px; padding: 0 11px; border-radius: 15px; border: 1px solid {BPD}; background: none; color: {BT}; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 6px;">{icon("quill",13)}Narrator</button>'
mind = f'''<section style="position: absolute; left: 24px; top: 84px; width: 864px; height: 792px; {PNL} overflow: hidden;">
{pt('MIND · MIKE’S LAST REPLY, 7:22 PM', '<div style="display: flex; gap: 6px;">'+tabs+'</div>')}
<div style="position: absolute; left: 0; top: 52px; width: 864px; height: 740px;">
<div style="position: absolute; left: 24px; top: 12px; width: 816px; display: flex; font-family: {MONO}; font-size: 10px; letter-spacing: .14em; color: {BM};"><span style="width: 234px;">IN</span><span style="width: 224px;">SENSE</span><span style="width: 208px;">INSIDE</span><span>DECIDE</span></div>
<svg width="864" height="500" viewBox="0 0 864 500" aria-hidden="true" style="position: absolute; left: 0; top: 0; pointer-events: none;">{edges}</svg>
{nodes}{out}{feel}
<div style="position: absolute; left: 24px; top: 700px; width: 816px; display: flex; align-items: center; gap: 8px; font-family: {MONO}; font-size: 11px; color: {BM};">Gold is the path that won. Click any part to see what went in and out of it.<span style="margin-left: auto; display: flex; gap: 6px;">{bb('Memory · 41','book')}{bb('Replay this turn','refresh')}</span></div>
</div></section>'''
segs=[('rules',600,900,'#6aa8ff'),('cards',1450,2000,'#8cc3ff'),('mind',820,1600,'#ffd08a'),('examples',540,800,'#a9e0c8'),('history',3600,9000,'#c7b8ff'),('tail',290,400,'#f4a595')]
bar=''.join(f'<span style="width: {v/16384*100:.2f}%; height: 12px; background: {c}; display: block;"></span>' for n,v,l,c in segs)
leg=''.join(f'<span style="display: flex; align-items: center; gap: 6px; font-family: {MONO}; font-size: 11px; color: {BT};"><span style="width: 8px; height: 8px; border-radius: 2px; background: {c}; display: block;"></span>{n} {v:,}<span style="color: {BM};">/ {l:,}</span></span>' for n,v,l,c in segs)
prompt = f'''<section style="position: absolute; left: 904px; top: 84px; width: 512px; height: 232px; {PNL} overflow: hidden;">
{pt('PROMPT', bb('full prompt','eye'))}
<div style="padding: 12px 16px; display: flex; flex-direction: column; gap: 10px;">
<div style="display: flex; justify-content: space-between; font-family: {MONO}; font-size: 12px; color: {BT};"><span>~7,300 / 16,384 tokens</span><span style="color: {BM};">cache reuse 81%</span></div>
<div style="display: flex; border-radius: 6px; overflow: hidden; background: rgba(140,195,255,.1);">{bar}</div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px 10px;">{leg}</div>
<div style="font-family: {MONO}; font-size: 11px; color: {BM};">cut: nothing · 3 memories and 4 feeling notes included</div></div></section>'''
def castrow(ic,name,kind,state,badge=''):
    b = f'<span style="height: 18px; padding: 0 7px; border-radius: 9px; background: rgba(231,176,106,.18); color: {GOLD}; font-family: {MONO}; font-size: 10px; display: flex; align-items: center;">{badge}</span>' if badge else ''
    return f'<div style="display: flex; align-items: center; gap: 10px; padding: 6px 16px;">{ic}<span style="font-size: 13px; font-weight: 600; color: {BT}; width: 104px;">{name}</span><span style="font-family: {MONO}; font-size: 10.5px; color: {BM}; width: 62px;">{kind}</span><span style="font-family: {MONO}; font-size: 11px; color: {BT}; flex-grow: 1;">{state}</span>{b}</div>'
pin = lambda n: '<span style="width: 24px; display: flex; justify-content: center; color: '+BP+';">'+icon(n,16)+'</span>'
cast = f'''<section style="position: absolute; left: 904px; top: 332px; width: 512px; height: 240px; {PNL} overflow: hidden;">
{pt('CAST', bb('these two are the same','merge'))}
{castrow(face('mira',24),'Mike','character','here · doubtful · borrowed jacket')}
{castrow(face('tobin',24),'Theo','character','away · not invited')}
{castrow(face('aren',24),'Liv','persona','here · on the list')}
{castrow(pin('map-pin'),'Corvel Palace','place','night · the gala')}
{castrow(pin('book'),'the gala list','item','who is on it: disputed','found')}
</section>'''
def run(job,model,stat,detail,col='#a9e0c8'):
    return f'<div style="display: grid; grid-template-columns: 116px 104px minmax(0,1fr); gap: 8px; align-items: center; padding: 7px 16px; font-family: {MONO}; font-size: 11px; color: {BT};"><span style="display: flex; align-items: center; gap: 7px;"><span style="width: 7px; height: 7px; border-radius: 4px; background: {col}; display: block;"></span>{job}</span><span style="color: {BM};">{model}</span><span>{stat} <span style="color: {BM};">{detail}</span></span></div>'
engine = f'''<section style="position: absolute; left: 904px; top: 588px; width: 512px; height: 288px; {PNL} overflow: hidden; display: flex; flex-direction: column;">
{pt('ENGINE · THIS TURN', '<span style="font-family: '+MONO+'; font-size: 11px; color: #a9e0c8;">engine ok</span>')}
{run('Characters','qwen3.5-9b','1.9 s','· 64 tok · 34 tok/s')}
{run('Reasoning','qwen3.5-9b','4.1 s','· thought 212 tok')}
{run('Recall','qwen3.5-9b','0.2 s','· 3 of 41 matched')}
{run('Feelings','qwen3.5-9b','0.6 s','· warmth ↑ doubt ↑')}
{run('Memory reader','qwen3.5-9b','waiting','· 2 new lines','#ffd08a')}
{run('Narrator','—','idle','')}
<div style="display: flex; gap: 8px; padding: 10px 16px; margin-top: auto;">{bb('Read what is waiting now','refresh',True)}{bb('Logs','book')}</div>
</section>'''
bgrid = "background-color: #06203f; background-image: linear-gradient(rgba(140,195,255,.08) 1px, transparent 1px), linear-gradient(90deg, rgba(140,195,255,.08) 1px, transparent 1px), linear-gradient(rgba(140,195,255,.04) 1px, transparent 1px), linear-gradient(90deg, rgba(140,195,255,.04) 1px, transparent 1px); background-size: 120px 120px, 120px 120px, 24px 24px, 24px 24px;"
files['Scene-Backstage.dc.html'] = shell('Scene · the backstage lens',
    f'<div style="position: absolute; inset: 0; {bgrid}"></div>' + corners(backstage=True) + mind + prompt + cast + engine)

for k,v in files.items(): open(f'root/project/{k}','w').write(v)
print(list(files))
