from lib import *
INK='#f4e9da'; MUTED='#cdbba4'; AMBER='#f0b35a'; LILAC='#cbb8ff'; ROSE='#f4a595'
SPK={'aren':'#a9c8ff','mira':'#f2b870','tobin':'#e8cc6a'}
W,H=1440,900
GLASS='background: rgba(26,19,15,.62); border: 1px solid rgba(255,236,210,.16); backdrop-filter: blur(14px);'

def arc(kind):
    if kind=='night':
        dot='<circle cx="22" cy="5" r="4" fill="#e3e9ff"/><circle cx="24" cy="4" r="3.4" fill="#1c1a24"/>'
    else:
        dot='<circle cx="37" cy="13" r="4" fill="#ffb35a"/>'
    return f'<svg width="44" height="22" viewBox="0 0 44 22" aria-hidden="true"><path d="M3 20 A19 19 0 0 1 41 20" fill="none" stroke="rgba(255,255,255,.35)" stroke-width="1.5" stroke-dasharray="2 3"/><path d="M1 20h42" stroke="rgba(255,255,255,.25)"/>{dot}</svg>'

def topbar(clock, kind='dusk', backstage=False, place='The Gull'):
    sw_bg = '#7fb7ff' if backstage else 'rgba(255,255,255,.18)'
    knob = 'left: 20px;' if backstage else 'left: 2px;'
    return f'''<div style="position: absolute; left: 0; top: 0; width: {W}px; height: 88px; box-sizing: border-box; padding: 18px 24px 0; display: flex; align-items: flex-start; justify-content: space-between; background: linear-gradient(180deg, rgba(8,5,3,.72) 0%, rgba(8,5,3,0) 100%); color: {INK}; z-index: 5;">
<div style="display: flex; align-items: center; gap: 14px;">
<button aria-label="Float back up to the Sky" style="width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: {INK}; {GLASS}">{icon('cloud',20)}</button>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span style="font-family: {SERIF}; font-style: italic; font-size: 19px; line-height: 1.2;">The Third Floorboard</span>
<span style="font-size: 12px; color: {MUTED}; letter-spacing: .02em;">with Mira · as Aren</span>
</div>
</div>
<div style="display: flex; align-items: center; gap: 10px;">
<div style="display: flex; align-items: center; gap: 10px; height: 44px; padding: 0 16px 0 12px; border-radius: 22px; box-sizing: border-box; {GLASS}">{arc(kind)}<span style="font-size: 14px; font-weight: 600;">{place}</span><span style="font-size: 14px; color: {MUTED};">{clock}</span></div>
<div style="display: flex; align-items: center; gap: 8px; height: 44px; padding: 0 6px 0 14px; border-radius: 22px; box-sizing: border-box; {GLASS}"><span style="font-size: 13px; color: {MUTED};">Playing</span><span style="font-size: 13px; font-weight: 600;">{"Night rain, empty harbour" if kind=="night" else "Rain on the harbour"}</span><button aria-label="Mute sound" style="width: 34px; height: 34px; border-radius: 50%; border: 0; background: rgba(255,255,255,.1); color: {INK}; display: flex; align-items: center; justify-content: center;">{icon('volume',16)}</button></div>
</div>
<div style="display: flex; align-items: center; gap: 10px;">
<label style="display: flex; align-items: center; gap: 10px; height: 44px; padding: 0 14px; border-radius: 22px; box-sizing: border-box; font-size: 13px; font-weight: 600; {GLASS}">{icon('layers',16)}Backstage<span style="position: relative; width: 38px; height: 20px; border-radius: 10px; background: {sw_bg}; display: block;"><span style="position: absolute; top: 2px; {knob} width: 16px; height: 16px; border-radius: 50%; background: #fff; display: block;"></span></span></label>
<button aria-label="Reading mode" style="width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: {INK}; {GLASS}">{icon('book',18)}</button>
<button aria-label="Story menu" style="width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: {INK}; {GLASS}">{icon('dots',18)}</button>
</div>
</div>'''

def stage(bg, chars, table=None, extra=''):
    ch=''
    for c in chars:
        ch+=f'<img src="{A[c["img"]]}" alt="{c.get("alt","")}" style="position: absolute; left: {c["x"]}px; top: {c["y"]}px; width: {c["w"]}px; height: {c["w"]*1.125:.0f}px; {c.get("style","filter: drop-shadow(0 30px 50px rgba(0,0,0,.55)) sepia(.14) saturate(1.05);")}">'
    t = f'<img src="{A[table]}" alt="" style="position: absolute; left: -160px; top: 640px; width: 1440px; height: 300px;">' if table else ''
    return (f'<img src="{A[bg]}" alt="The Gull, a smoky dockside tavern" style="position: absolute; left: 0; top: 0; width: {W}px; height: {H}px; object-fit: cover;">'
            f'{ch}{t}{extra}'
            f'<div style="position: absolute; inset: 0; background: radial-gradient(ellipse 70% 80% at 35% 45%, rgba(0,0,0,0) 50%, rgba(0,0,0,.55) 100%); pointer-events: none;"></div>')

def tray(items, label='Nearby'):
    rows=''
    for who,note,away in items:
        f = face(who,44, fstyle='filter: grayscale(.85) brightness(.8);' if away else '', ring='0 0 0 2px rgba(255,255,255,.18)')
        rows+=f'<button style="display: flex; align-items: center; gap: 10px; background: none; border: 0; padding: 0; color: {INK}; text-align: left;">{f}<span style="display: flex; flex-direction: column; gap: 1px;"><span style="font-size: 13px; font-weight: 600;">{NAME[who]}</span><span style="font-size: 11px; color: {MUTED};">{note}</span></span></button>'
    return f'''<div style="position: absolute; left: 24px; top: 300px; width: 206px; box-sizing: border-box; padding: 14px; border-radius: 22px; display: flex; flex-direction: column; gap: 12px; color: {INK}; z-index: 4; {GLASS}">
<div style="display: flex; align-items: center; justify-content: space-between;"><span style="font-size: 11px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: {MUTED};">{label}</span>{icon('drag',14,MUTED)}</div>
{rows}
<button style="display: flex; align-items: center; gap: 8px; height: 36px; padding: 0 12px; border-radius: 18px; border: 1px dashed rgba(255,236,210,.3); background: none; color: {INK}; font-size: 12px; font-weight: 600; white-space: nowrap;">{icon('plus',14)}Bring someone in</button>
<span style="font-size: 11px; color: {MUTED}; line-height: 1.35;">Drag onto the stage to bring in, off it to send away.</span>
</div>'''

def rface(who, state, s=20):
    if state=='absent':
        return f'<div style="width: {s}px; height: {s}px; border-radius: 50%; border: 1.5px dashed rgba(255,236,210,.45); box-sizing: border-box; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: 700; color: {MUTED}; flex-shrink: 0;">{NAME[who][0]}</div>'
    ring={'lit':f'0 0 0 1.5px {AMBER}, 0 0 10px rgba(240,179,90,.75)','heard':'0 0 0 1.5px rgba(255,255,255,.4)','hazy':'0 0 0 1.5px rgba(240,179,90,.3)'}[state]
    st={'lit':'','heard':'opacity: .85;','hazy':'opacity: .42; filter: blur(.5px);'}[state]
    return face(who,s,extra_style=st,ring=ring)

def receipts(items, expanded=False, pending=False):
    """items: list of (who,state,label)"""
    if expanded:
        chips=''.join(f'<span style="display: flex; align-items: center; gap: 6px; height: 26px; padding: 0 10px 0 3px; border-radius: 13px; background: rgba(255,255,255,.07); font-size: 12px; color: {INK if st!="absent" else MUTED};">{rface(w,st)}{lab}</span>' for w,st,lab in items)
        return f'<div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px;">{chips}</div>'
    faces=''.join(rface(w,st,16) for w,st,lab in items)
    note=' · '.join(lab for w,st,lab in items)
    dots = f'<span style="display: flex; gap: 3px;"><span style="width: 4px; height: 4px; border-radius: 2px; background: {MUTED}; display: block;"></span><span style="width: 4px; height: 4px; border-radius: 2px; background: {MUTED}; opacity: .6; display: block;"></span><span style="width: 4px; height: 4px; border-radius: 2px; background: {MUTED}; opacity: .3; display: block;"></span></span>' if pending else ''
    return f'<div style="display: flex; align-items: center; gap: 6px; margin-top: 8px; opacity: .8;"><span style="display: flex; gap: 4px;">{faces}</span><span style="font-size: 11px; color: {MUTED};">{note}</span>{dots}</div>'

def callout(kind, text, who=None, soft=False):
    col={'memory':AMBER,'feeling':ROSE,'belief':LILAC}[kind]
    ic={'memory':'spark','feeling':'heart','belief':'help'}[kind]
    f = face(who,20) if who else icon(ic,14,col)
    op = 'opacity: .45;' if soft else ''
    lead = f if who else '<span style="width: 6px;"></span>'
    return f'<div style="display: flex; align-self: flex-start; align-items: center; gap: 7px; height: 28px; padding: 0 12px 0 5px; margin-top: 8px; border-radius: 14px; background: {col}1f; border: 1px solid {col}66; font-size: 12.5px; font-weight: 600; color: {col}; {op}">{lead}{icon(ic,13,col) if who else f}{text}</div>'

def body(text, dim=False):
    import re
    t=esc(text)
    t=re.sub(r'\*(.+?)\*', lambda m: f'<em style="color: #dcc8ad;">{m.group(1)}</em>', t)
    return f'<p style="margin: 6px 0 0; font-family: {SERIF}; font-size: 19px; line-height: 1.5; color: {INK}; text-wrap: pretty;{" opacity: .55;" if dim else ""}">{t}</p>'

def line(who, stamp, text, rec=None, extra='', hover=False, spark=False, dim=False, marks='', tail=''):
    tb=''
    if hover:
        tb=f'''<div style="position: absolute; right: 8px; top: 6px; display: flex; align-items: center; gap: 2px; padding: 4px; border-radius: 12px; {GLASS} background: rgba(30,22,17,.92);">
<button aria-label="Previous take" style="width: 30px; height: 30px; border: 0; border-radius: 8px; background: none; color: {INK}; display: flex; align-items: center; justify-content: center;">{icon('left',15)}</button><span style="font-size: 12px; color: {MUTED}; font-variant-numeric: tabular-nums;">1/1</span><button aria-label="New take" style="width: 30px; height: 30px; border: 0; border-radius: 8px; background: none; color: {INK}; display: flex; align-items: center; justify-content: center;">{icon('right',15)}</button>
<span style="width: 1px; height: 18px; background: rgba(255,255,255,.14); display: block;"></span>
<button style="height: 30px; border: 0; border-radius: 8px; background: none; color: {INK}; font-size: 12px; display: flex; align-items: center; gap: 5px; padding: 0 8px;">{icon('edit',14)}Edit</button>
<button style="height: 30px; border: 0; border-radius: 8px; background: none; color: {INK}; font-size: 12px; display: flex; align-items: center; gap: 5px; padding: 0 8px;">{icon('eyeoff',14)}Hide</button>
</div>'''
    hovbg = 'background: rgba(255,255,255,.045); border-radius: 14px; box-shadow: 0 0 0 1px rgba(255,236,210,.1);' if hover else ''
    sp = f'<span aria-label="Drew on memory" style="display: flex; color: {AMBER};">{icon("spark",14,AMBER)}</span>' if spark else ''
    return f'''<article style="position: relative; display: flex; flex-direction: column; padding: 12px 14px; margin: 0 -14px; {hovbg}{" opacity: .6;" if dim else ""}">
{tb}
<div style="display: flex; align-items: baseline; gap: 10px;"><span style="font-size: 13px; font-weight: 700; color: {SPK[who]}; letter-spacing: .02em;">{NAME[who]}</span><span style="font-size: 12px; color: {MUTED}; font-variant-numeric: tabular-nums;">{stamp}</span>{sp}{marks}</div>
{body(text)}
{rec or ''}
{extra}
</article>{tail}'''

def titlecard(text, extra=''):
    return f'<div style="display: flex; align-items: center; gap: 14px; margin: 10px 0; color: {MUTED};"><span style="flex-grow: 1; height: 1px; background: linear-gradient(90deg, rgba(255,236,210,0), rgba(255,236,210,.3)); display: block;"></span><span style="font-family: {SERIF}; font-size: 14px; letter-spacing: .14em; text-transform: uppercase;">{text}</span>{extra}<span style="flex-grow: 1; height: 1px; background: linear-gradient(90deg, rgba(255,236,210,.3), rgba(255,236,210,0)); display: block;"></span></div>'

def sysnote(who, text, sub='', away=False, undo=False):
    f=face(who,24,fstyle='filter: grayscale(.9);' if away else '')
    subh = ('<span style="font-size: 12px; color: '+MUTED+';">'+sub+'</span>') if sub else ''
    u=f'<button style="height: 26px; padding: 0 10px; border-radius: 13px; border: 1px solid rgba(255,236,210,.25); background: none; color: {INK}; font-size: 12px; display: flex; align-items: center; gap: 5px;">{icon("undo",12)}Undo</button>' if undo else ''
    return f'<div style="display: flex; align-items: center; gap: 10px; margin: 6px 0; padding: 8px 12px; border-radius: 14px; background: rgba(255,255,255,.04);">{f}<span style="display: flex; flex-direction: column; gap: 1px; flex-grow: 1;"><span style="font-family: {SERIF}; font-style: italic; font-size: 16px; color: {INK};">{text}</span>{subh}</span>{u}</div>'

def composer(hear, hear_text, mode='Say', stop=False, next_sel='Whoever fits', next_chars=('mira',), meter=45, placeholder='Speak or act as Aren…', stopnote=False):
    hf=''.join(rface(w,'heard',24) for w,away in hear if not away)
    af=''.join(f'<span style="display: flex; align-items: center; gap: 6px; font-size: 12px; color: {MUTED}; margin-left: 6px; white-space: nowrap;">{face(w,22,fstyle="filter: grayscale(1) brightness(.7);",extra_style="opacity: .55;")}{NAME[w]} is away</span>' for w,away in hear if away)
    modes=''
    for m,ic in (('Say','quote'),('Do','hand'),('Whisper','ear'),('Think','thought')):
        on = m==mode
        modes+=f'<button aria-pressed="{"true" if on else "false"}" style="height: 32px; padding: 0 12px; border: 0; border-radius: 16px; display: flex; align-items: center; gap: 6px; font-size: 12.5px; font-weight: 600; white-space: nowrap; background: {"rgba(240,179,90,.2)" if on else "none"}; color: {AMBER if on else MUTED};">{icon(ic,14)}{m}</button>'
    nx=''
    opts=[('Whoever fits',None)]+[(NAME[c],c) for c in next_chars]
    for lab,c in opts:
        on= lab==next_sel
        inner = face(c,22) if c else icon('users',14)
        nx+=f'<button aria-pressed="{"true" if on else "false"}" style="height: 34px; padding: 0 12px 0 {6 if c else 10}px; border-radius: 17px; display: flex; align-items: center; gap: 7px; font-size: 12.5px; font-weight: 600; white-space: nowrap; border: 1px solid {"rgba(240,179,90,.55)" if on else "rgba(255,236,210,.14)"}; background: {"rgba(240,179,90,.14)" if on else "rgba(255,255,255,.03)"}; color: {INK};">{inner}{lab}</button>'
    nx+=f'<button style="height: 34px; padding: 0 12px 0 10px; border-radius: 17px; display: flex; align-items: center; gap: 7px; font-size: 12.5px; font-weight: 600; white-space: nowrap; border: 1px solid rgba(255,236,210,.14); background: rgba(255,255,255,.03); color: {INK};">{icon("quill",14)}Narrator</button>'
    if stop:
        act=f'''<button style="height: 44px; padding: 0 20px 0 16px; border-radius: 22px; border: 1px solid rgba(240,179,90,.6); background: rgba(240,179,90,.12); color: {AMBER}; font-size: 14px; font-weight: 700; display: flex; align-items: center; gap: 8px;">{icon('stop',16,AMBER)}Stop</button>'''
    else:
        act=f'''<button style="height: 44px; padding: 0 20px 0 18px; border-radius: 22px; border: 0; background: {AMBER}; color: #2a1606; font-size: 14px; font-weight: 700; display: flex; align-items: center; gap: 8px;">Send{icon('send',16,'#2a1606')}</button>'''
    sn = f'<span style="font-size: 11.5px; color: {MUTED};">Stopping keeps what Mira has written so far.</span>' if stopnote else ''
    return f'''<div style="position: absolute; left: 822px; right: 24px; bottom: 24px; border-radius: 22px; overflow: hidden; color: {INK}; {GLASS} background: rgba(24,17,13,.84);">
<div style="height: 3px; background: rgba(255,255,255,.08);"><div style="width: {meter}%; height: 3px; background: linear-gradient(90deg, {AMBER}, #f7d9a0);"></div></div>
<div style="padding: 14px 16px 14px; display: flex; flex-direction: column; gap: 12px;">
<div style="display: flex; align-items: center; justify-content: space-between;">
<div style="display: flex; align-items: center; gap: 8px;"><span style="display: flex; gap: 6px; align-items: center;">{hf}</span><span style="font-size: 13px; font-weight: 600; white-space: nowrap;">{hear_text}</span>{af}</div>
<div style="display: flex; align-items: center; gap: 6px;">
<button style="height: 34px; padding: 0 12px 0 10px; border-radius: 17px; border: 1px solid rgba(255,236,210,.14); background: rgba(255,255,255,.03); color: {INK}; font-size: 12.5px; font-weight: 600; display: flex; align-items: center; gap: 6px; white-space: nowrap;">{icon('clock',15)}Pass time</button>
<button style="height: 34px; padding: 0 12px 0 10px; border-radius: 17px; border: 1px solid rgba(255,236,210,.14); background: rgba(255,255,255,.03); color: {INK}; font-size: 12.5px; font-weight: 600; display: flex; align-items: center; gap: 6px; white-space: nowrap;">{icon('ff',15)}Continue</button>
</div>
</div>
<label style="display: flex; flex-direction: column;"><span class="sr">Your line</span><textarea rows="2" placeholder="{placeholder}" style="resize: none; border: 0; outline: none; background: transparent; color: {INK}; font-family: {SERIF}; font-size: 18px; line-height: 1.45; padding: 0;"></textarea></label>
<div style="display: flex; align-items: center; justify-content: space-between; gap: 10px;">
<div style="display: flex; gap: 2px; padding: 3px; border-radius: 19px; background: rgba(0,0,0,.25);">{modes}</div>
{act}
</div>
<div style="display: flex; align-items: center; gap: 6px; padding-top: 12px; border-top: 1px solid rgba(255,236,210,.08);"><span style="font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: {MUTED}; margin-right: 4px; white-space: nowrap;">Who answers</span>{nx}</div>
{sn}
</div>
</div>'''

def panel(lines, top_fade=True):
    return f'''<div style="position: absolute; left: 740px; top: 0; width: 700px; height: {H}px; background: linear-gradient(90deg, rgba(14,10,8,0) 0%, rgba(14,10,8,.74) 11%, rgba(14,10,8,.9) 100%);"></div>
<div style="position: absolute; left: 836px; top: 96px; width: 560px; height: 500px; overflow: hidden; display: flex; flex-direction: column; justify-content: flex-end; gap: 4px;">
{lines}
</div>
{'<div style="position: absolute; left: 800px; top: 88px; width: 640px; height: 90px; background: linear-gradient(180deg, rgba(14,10,8,.92), rgba(14,10,8,0)); pointer-events: none;"></div>' if top_fade else ''}'''

def shell(title, inner):
    return page(title, W, H, f'<div style="width: {W}px; height: {H}px; position: relative; overflow: hidden; background: #0e0a08; font-family: {SANS};">{inner}</div>')

# sample lines
L = {}
L['t0'] = titlecard('The Gull · Day 1, 19:00')
def l02(**k): return line('aren','19:02','Evening, Mira. Rough night on the docks?', **k)
def l04(**k): return line('mira','19:04','*slides a sealed letter across the table* Rough enough. Coin first. Questions after.', **k)
def l06(**k): return line('tobin','19:06','*drops into the chair beside her* Did someone say coin?', **k)
def l08(**k): return line('aren','19:08','Tobin, would you fetch us a round from the bar?', **k)
def l10(**k): return line('tobin','19:10','*pushes back his chair, grinning* Anything for a paying customer.', **k)
SECRET='Quickly, while he’s gone. I hid the guild ledger under the third floorboard behind the bar. Tell no one, least of all Tobin.'
def l12(**k): return line('aren','19:12',SECRET, **k)
def l14(**k): return line('mira','19:14','*her eyes flick to the bar and back* Then stop saying it so loud.', **k)

R_m_lit = receipts([('mira','lit','Mira will remember')])
files={}

# 1 one-to-one
lines = L['t0'] + l02(rec=receipts([('mira','lit','Heard by Mira · she’ll remember'),], expanded=True), hover=True) + l04(rec=receipts([('mira','heard','Heard by Mira')], pending=True))
files['Main.dc.html'] = shell('Scene · one-to-one', 
    stage('gull-dusk',[dict(img='mira',x=90,y=190,w=640,alt='Mira, at the corner table')],'table-dusk')
    + topbar('Day 1, 19:04') + tray([('tobin','at the bar · could join',True),('ilsa','not in this story',True),('oren','not in this story',True)])
    + panel(lines) + composer([('mira',False)],'Only Mira will hear this'))

# 2 group joins
lines = L['t0'] + l02(rec=R_m_lit) + l04(rec=receipts([('mira','lit','Mira will remember')])) \
    + sysnote('tobin','Tobin joins','Brought in by you · he hears everything from here on', undo=True) \
    + l06(rec=receipts([('mira','heard','Mira'),('tobin','heard','Tobin')], pending=True))
namecard = f'''<div style="position: absolute; left: 440px; top: 640px; display: flex; align-items: center; gap: 12px; padding: 10px 18px 10px 10px; border-radius: 28px; color: {INK}; z-index: 3; {GLASS} background: rgba(30,22,17,.7); box-shadow: 0 10px 30px rgba(0,0,0,.4);">{face('tobin',40,ring='0 0 0 2px '+SPK['tobin'])}<span style="display: flex; flex-direction: column;"><span style="font-family: {SERIF}; font-size: 22px; font-style: italic;">Tobin joins</span><span style="font-size: 12px; color: {MUTED};">Cheerful smuggler. Hears everything eventually.</span></span></div>'''
files['Scene-Group-Joins.dc.html'] = shell('Scene · Tobin joins',
    stage('gull-dusk',[dict(img='mira-smile',x=-60,y=230,w=560,style='filter: brightness(.62) blur(1.5px) sepia(.2);'),
                       dict(img='tobin',x=440,y=190,w=600,style='opacity: .22; filter: blur(3px);'),
                       dict(img='tobin',x=370,y=190,w=600)],'table-dusk', namecard)
    + topbar('Day 1, 19:06') + tray([('ilsa','not in this story',True),('oren','not in this story',True)])
    + panel(lines) + composer([('mira',False),('tobin',False)],'Mira and Tobin will hear this', next_chars=('mira','tobin')))

# 3 secret
reac = callout('feeling','Tobin didn’t like that', who='tobin')
lines = l08(rec=receipts([('mira','lit','Mira'),('tobin','lit','Tobin will remember')]), extra=reac) \
    + l10(rec=receipts([('mira','lit','Mira'),('tobin','lit','Tobin')])) \
    + sysnote('tobin','Tobin left. He won’t hear what’s said now.','He’s at the bar, out of earshot', away=True, undo=True) \
    + l12(rec=receipts([('mira','lit','Mira heard · will remember'),('tobin','absent','Tobin wasn’t there')], expanded=True), hover=True, extra=callout('memory','Mira will remember this', who='mira')) \
    + l14(rec=receipts([('mira','heard','Heard by Mira')], pending=True))
leaving = f'''<div style="position: absolute; left: 600px; top: 596px; display: flex; align-items: center; gap: 8px; padding: 6px 12px 6px 6px; border-radius: 18px; color: {INK}; font-size: 12px; z-index: 3; {GLASS}">{face('tobin',24,fstyle='filter: grayscale(.9);')}Tobin · away, at the bar</div>'''
files['Scene-Group-Secret.dc.html'] = shell('Scene · the secret, Tobin away',
    stage('gull-dusk',[dict(img='tobin',x=560,y=330,w=240,style='opacity: .5; filter: blur(2.5px) grayscale(.5) brightness(.6);'),
                       dict(img='mira-wary',x=80,y=190,w=640)],'table-dusk', leaving)
    + topbar('Day 1, 19:14') + tray([('tobin','away · at the bar',True),('ilsa','not in this story',True),('oren','not in this story',True)])
    + panel(lines) + composer([('mira',False),('tobin',True)],'Only Mira will hear this'))

# 4 thinking
thinking = f'''<div style="display: flex; align-items: center; gap: 12px; padding: 14px 0 6px;">{face('mira',32,ring='0 0 0 2px '+SPK['mira'])}<span style="display: flex; flex-direction: column; gap: 2px;"><span style="font-family: {SERIF}; font-style: italic; font-size: 18px; color: {INK};">Mira is thinking…</span><span style="font-size: 12px; color: {MUTED};">Her notes stay backstage · <a href="Scene-Backstage.dc.html" style="color: {AMBER};">read them</a></span></span><span style="display: flex; gap: 5px; margin-left: auto;"><span style="width: 7px; height: 7px; border-radius: 4px; background: {AMBER}; display: block;"></span><span style="width: 7px; height: 7px; border-radius: 4px; background: {AMBER}; opacity: .55; display: block;"></span><span style="width: 7px; height: 7px; border-radius: 4px; background: {AMBER}; opacity: .25; display: block;"></span></span></div>'''
lines = l08(rec=receipts([('mira','lit','Mira'),('tobin','lit','Tobin')]), extra=reac) + l10(rec=receipts([('mira','lit','Mira'),('tobin','lit','Tobin')])) \
    + sysnote('tobin','Tobin left. He won’t hear what’s said now.', away=True) \
    + l12(rec=receipts([('mira','heard','Heard by Mira'),('tobin','absent','Tobin wasn’t there')], pending=True)) + thinking
files['Scene-Reply-Thinking.dc.html'] = shell('Scene · Mira is thinking',
    stage('gull-dusk',[dict(img='mira-thinking',x=90,y=190,w=640)],'table-dusk')
    + topbar('Day 1, 19:12') + tray([('tobin','away · at the bar',True),('ilsa','not in this story',True),('oren','not in this story',True)])
    + panel(lines) + composer([('mira',False),('tobin',True)],'Only Mira will hear this', stop=True, next_sel='Mira'))

# 5 streaming
caret = f'<span style="display: inline-block; width: 9px; height: 20px; margin-left: 3px; vertical-align: -3px; background: {AMBER}; border-radius: 2px;"></span>'
stream = f'''<article style="display: flex; flex-direction: column; padding: 12px 0;">
<div style="display: flex; align-items: baseline; gap: 10px;"><span style="font-size: 13px; font-weight: 700; color: {SPK['mira']};">Mira</span><span style="font-size: 12px; color: {MUTED};">19:14</span><span style="font-size: 12px; color: {AMBER};">writing…</span></div>
<p style="margin: 6px 0 0; font-family: {SERIF}; font-size: 19px; line-height: 1.5; color: {INK};"><em style="color: #dcc8ad;">her eyes flick to the bar and back</em> Then stop saying{caret}</p>
<button style="align-self: flex-start; margin-top: 8px; height: 26px; padding: 0 10px; border-radius: 13px; border: 1px solid rgba(255,236,210,.2); background: none; color: {MUTED}; font-size: 12px; display: flex; align-items: center; gap: 6px;">{icon('thought',13)}Thought for 4 s</button>
</article>'''
lines = l08(rec=receipts([('mira','lit','Mira'),('tobin','lit','Tobin')]), extra=reac) + l10(rec=receipts([('mira','lit','Mira'),('tobin','lit','Tobin')])) \
    + sysnote('tobin','Tobin left. He won’t hear what’s said now.', away=True) \
    + l12(rec=receipts([('mira','heard','Heard by Mira'),('tobin','absent','Tobin wasn’t there')], pending=True)) + stream
files['Scene-Reply-Streaming.dc.html'] = shell('Scene · reply streaming',
    stage('gull-dusk',[dict(img='mira-wary',x=90,y=190,w=640)],'table-dusk')
    + topbar('Day 1, 19:14') + tray([('tobin','away · at the bar',True),('ilsa','not in this story',True),('oren','not in this story',True)])
    + panel(lines) + composer([('mira',False),('tobin',True)],'Only Mira will hear this', stop=True, next_sel='Mira', stopnote=True))

# 6 time skip transition
hazy_lines = l12(rec=receipts([('mira','hazy','Mira · fading'),('tobin','absent','Tobin wasn’t there')]), extra=callout('memory','Mira will remember this', who='mira', soft=True)) + l14(rec=receipts([('mira','hazy','Mira · fading')]))
skipcard = f'''<div style="position: absolute; left: 0; top: 0; width: {W}px; height: {H}px; background: radial-gradient(ellipse 60% 55% at 45% 50%, rgba(246,248,255,.72) 0%, rgba(230,236,252,.55) 45%, rgba(200,212,240,.25) 100%);"></div>
<img src="{A['clouds']}" alt="" style="position: absolute; left: -200px; top: -260px; width: 1840px; height: 1150px; opacity: .95;">
<img src="{A['clouds']}" alt="" style="position: absolute; left: -120px; top: 180px; width: 1700px; height: 1060px; opacity: .9; transform: scaleX(-1);">
<div style="position: absolute; left: 0; bottom: 0; width: 1440px; height: 260px; background: linear-gradient(180deg, rgba(240,244,255,0), rgba(240,244,255,.95));"></div>
<div style="position: absolute; left: 280px; top: 250px; width: 660px; display: flex; flex-direction: column; align-items: center; gap: 18px; color: #2a2230; text-align: center;">
<span style="font-size: 12px; font-weight: 700; letter-spacing: .22em; text-transform: uppercase; color: #5a5068;">The Third Floorboard</span>
<span style="font-family: {SERIF}; font-style: italic; font-size: 76px; line-height: 1; letter-spacing: -.01em;">Six years later</span>
<div style="display: flex; align-items: center; gap: 14px; font-size: 16px; font-variant-numeric: tabular-nums;"><span style="color: #6a6078; text-decoration: line-through;">Day 1, 19:14</span>{icon('arrow',18,'#6a6078')}<span style="font-weight: 700;">Year 7, Day 1, 19:14</span></div>
<div style="display: flex; align-items: center; gap: 10px; padding: 10px 16px; border-radius: 16px; background: rgba(255,255,255,.6); border: 1px solid rgba(255,255,255,.9);">{face('mira',28,extra_style='opacity: .55;')}<span style="font-size: 14px; color: #3a3346;">12 of Mira’s memories are going hazy. 3 are fading out.</span></div>
<button style="height: 44px; padding: 0 20px; border-radius: 22px; border: 1px solid rgba(42,34,48,.25); background: rgba(255,255,255,.7); color: #2a2230; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px;">{icon('undo',16)}Undo the time skip</button>
</div>'''
files['Scene-TimeSkip.dc.html'] = shell('Scene · six years later',
    stage('gull-dusk',[dict(img='mira-wary',x=90,y=190,w=640,style='filter: blur(6px) brightness(.8);')],'table-dusk')
    + panel(hazy_lines) + skipcard)

# 7 after skip
tooltip = f'''<div style="margin-top: 10px; padding: 12px 14px; border-radius: 14px; background: rgba(40,30,22,.95); border: 1px solid rgba(240,179,90,.35); display: flex; flex-direction: column; gap: 8px;">
<div style="display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 700; color: {AMBER}; letter-spacing: .04em;">{icon('spark',14,AMBER)}MIRA REMEMBERED, VAGUELY</div>
<span style="font-family: {SERIF}; font-size: 16px; color: {INK};">The ledger is somewhere behind the bar.</span>
<div style="display: flex; align-items: center; gap: 10px; font-size: 11.5px; color: {MUTED};"><span style="display: flex; gap: 3px;"><span style="width: 18px; height: 5px; border-radius: 3px; background: {AMBER}; display: block;"></span><span style="width: 18px; height: 5px; border-radius: 3px; background: {AMBER}; opacity: .35; display: block;"></span><span style="width: 18px; height: 5px; border-radius: 3px; background: rgba(255,255,255,.12); display: block;"></span></span>hazy · witnessed Day 1 · once sharp: “under the third floorboard”</div>
</div>'''
lines = l12(rec=receipts([('mira','hazy','Mira remembers this vaguely'),('tobin','absent','Tobin wasn’t there')]), dim=True) \
    + titlecard('Six years later · Year 7', f'<button style="height: 24px; padding: 0 9px; border-radius: 12px; border: 1px solid rgba(255,236,210,.25); background: none; color: {MUTED}; font-size: 11px; display: flex; align-items: center; gap: 4px;">{icon("undo",11)}Undo</button>') \
    + line('mira','Year 7 · 19:18','Aren? Gods, it’s been years. That ledger of yours… behind the bar, wasn’t it? Somewhere back there.', spark=True, extra=tooltip) \
    + line('aren','19:20','It was never behind the bar. I buried it by the lighthouse, remember?', rec=receipts([('mira','lit','Mira will remember')])) \
    + line('mira','19:22','*frowns* The lighthouse? I could have sworn… Six years is a long time.', extra=callout('belief','Mira has her doubts', who='mira') + f'<span style="font-size: 11.5px; color: {MUTED}; margin-top: 6px;">Her memory of where the ledger is has gone hazy, so she can be talked out of it.</span>')
files['Scene-AfterSkip.dc.html'] = shell('Scene · Year 7, Mira has her doubts',
    stage('gull-night',[dict(img='mira-doubtful',x=90,y=190,w=640,style='filter: drop-shadow(0 30px 50px rgba(0,0,0,.6)) brightness(.82) saturate(.9) hue-rotate(-6deg);')],'table-night')
    + topbar('Year 7, Day 1, 19:22','night') + tray([('tobin','away · not seen in years',True),('ilsa','not in this story',True),('oren','not in this story',True)])
    + panel(lines) + composer([('mira',False)],'Only Mira will hear this', meter=58))

# 8 peek
def prow(ic,k,v): return f'<div style="display: flex; align-items: flex-start; gap: 10px;"><span style="color: {MUTED}; display: flex; padding-top: 1px;">{icon(ic,15)}</span><span style="width: 74px; font-size: 12px; color: {MUTED}; flex-shrink: 0;">{k}</span><span style="font-size: 13.5px; color: {INK};">{v}</span></div>'
def tier(t):
    c={'sharp':(AMBER,'1'),'hazy':(AMBER,'.45'),'forgotten':('#8a7e70','1')}[t[0]] if isinstance(t,tuple) else None
    col,op={'sharp':(AMBER,1),'hazy':(AMBER,.5),'forgotten':('#8a7e70',1)}[t]
    return f'<span style="display: inline-flex; align-items: center; gap: 5px; height: 20px; padding: 0 8px; border-radius: 10px; border: 1px solid {col}; color: {col}; opacity: {op if t!="hazy" else 1}; font-size: 11px; font-weight: 700; letter-spacing: .04em; {"border-style: dashed;" if t=="hazy" else ""}">{t.upper()}</span>'
sec = f'<div style="margin: 0 18px; padding: 12px 14px; border-radius: 14px; background: rgba(255,255,255,.04); border: 1px solid rgba(255,236,210,.12); display: flex; align-items: center; gap: 12px;">{icon("lock",18,MUTED)}<span style="flex-grow: 1; display: flex; flex-direction: column; gap: 4px;"><span style="font-size: 12px; font-weight: 700; color: {MUTED}; letter-spacing: .06em;">ONLY MIRA KNOWS THIS</span><span style="font-family: {SERIF}; font-size: 15px; color: {INK}; filter: blur(5px);">She reads every letter she carries.</span></span><button style="height: 32px; padding: 0 12px; border-radius: 16px; border: 1px solid rgba(255,236,210,.25); background: none; color: {INK}; font-size: 12px; font-weight: 600;">Reveal</button></div>'
peek = f'''<div style="position: absolute; left: 400px; top: 104px; width: 420px; border-radius: 26px; color: {INK}; z-index: 6; display: flex; flex-direction: column; gap: 16px; padding-bottom: 18px; {GLASS} background: rgba(28,20,16,.8); box-shadow: 0 30px 80px rgba(0,0,0,.55);">
<div style="display: flex; align-items: center; gap: 14px; padding: 18px 18px 0;">{face('mira-doubtful' and 'mira',56,img='mira-doubtful',ring='0 0 0 2px '+SPK['mira'])}<span style="display: flex; flex-direction: column; gap: 4px; flex-grow: 1;"><span style="font-family: {SERIF}; font-size: 26px; line-height: 1;">Mira</span><span style="display: flex; gap: 6px; align-items: center; font-size: 12px; color: {MUTED};"><span style="height: 20px; padding: 0 8px; border-radius: 10px; background: rgba(203,184,255,.16); color: {LILAC}; font-weight: 700; display: flex; align-items: center;">doubtful</span>Guild courier · present</span></span><button aria-label="Close" style="width: 36px; height: 36px; border-radius: 50%; border: 0; background: rgba(255,255,255,.08); color: {INK}; display: flex; align-items: center; justify-content: center;">{icon('x',16)}</button></div>
<div style="padding: 0 18px; display: flex; flex-direction: column; gap: 8px;"><span style="font-size: 11px; font-weight: 700; letter-spacing: .12em; color: {MUTED};">RIGHT NOW</span>
{prow('hand','Holding','A mug she hasn’t touched')}{prow('user','Wearing','Rain-dark courier’s cloak, guild badge')}{prow('map-pin','Where','The Gull, the corner table by the window')}{prow('heart','Injury','None')}</div>
<div style="padding: 0 18px; display: flex; flex-direction: column; gap: 8px;"><span style="font-size: 11px; font-weight: 700; letter-spacing: .12em; color: {MUTED};">ON HER MIND</span>
<div style="display: flex; align-items: center; gap: 10px;">{tier('hazy')}<span style="font-family: {SERIF}; font-size: 16px;">The ledger is somewhere behind the bar.</span></div></div>
<div style="padding: 0 18px; display: flex; flex-direction: column; gap: 8px;"><div style="display: flex; justify-content: space-between; align-items: baseline;"><span style="font-size: 11px; font-weight: 700; letter-spacing: .12em; color: {MUTED};">WHAT SHE KNOWS ABOUT YOU</span><a href="Scene-Backstage.dc.html" style="font-size: 12px; color: {AMBER};">38 memories · 12 hazy</a></div>
<div style="display: flex; align-items: flex-start; gap: 10px;">{tier('sharp')}<span style="font-size: 13.5px; line-height: 1.4;">Aren says the ledger is buried by the lighthouse. <span style="color: {LILAC};">Doubted.</span></span></div>
<div style="display: flex; align-items: flex-start; gap: 10px;">{tier('hazy')}<span style="font-size: 13.5px; line-height: 1.4;">Aren hid the guild ledger somewhere behind the bar.</span></div></div>
<div style="padding: 0 18px; display: flex; gap: 8px; flex-wrap: wrap;"><span style="height: 28px; padding: 0 12px; border-radius: 14px; background: rgba(240,179,90,.12); color: {AMBER}; font-size: 12.5px; font-weight: 600; display: flex; align-items: center;">Trusts Aren</span><span style="height: 28px; padding: 0 12px; border-radius: 14px; background: rgba(244,165,149,.12); color: {ROSE}; font-size: 12.5px; font-weight: 600; display: flex; align-items: center;">Distrusts Tobin</span></div>
{sec}
<div style="padding: 0 18px; display: flex; gap: 8px;"><button style="flex-grow: 1; height: 44px; border-radius: 22px; border: 0; background: {AMBER}; color: #2a1606; font-size: 13.5px; font-weight: 700;">Let her answer next</button><button style="height: 44px; padding: 0 16px; border-radius: 22px; border: 1px solid rgba(255,236,210,.2); background: none; color: {INK}; font-size: 13.5px; font-weight: 600;">Send away</button><button aria-label="Edit Mira" style="width: 44px; height: 44px; border-radius: 22px; border: 1px solid rgba(255,236,210,.2); background: none; color: {INK}; display: flex; align-items: center; justify-content: center;">{icon('edit',16)}</button></div>
</div>'''
lines = line('mira','Year 7 · 19:18','Aren? Gods, it’s been years. That ledger of yours… behind the bar, wasn’t it? Somewhere back there.', spark=True) \
    + line('aren','19:20','It was never behind the bar. I buried it by the lighthouse, remember?', rec=receipts([('mira','lit','Mira will remember')])) \
    + line('mira','19:22','*frowns* The lighthouse? I could have sworn… Six years is a long time.', extra=callout('belief','Mira has her doubts', who='mira'))
files['Scene-Peek.dc.html'] = shell('Scene · Mira’s peek card',
    stage('gull-night',[dict(img='mira-doubtful',x=-40,y=190,w=600,style='filter: drop-shadow(0 30px 50px rgba(0,0,0,.6)) brightness(.9) saturate(.9);')],'table-night')
    + topbar('Year 7, Day 1, 19:22','night') + panel(lines) + composer([('mira',False)],'Only Mira will hear this', meter=58) + peek)

# 9 backstage
BP='#8cc3ff'; BPD='rgba(140,195,255,.28)'; BTXT='#e4f0ff'; BMUT='#9db8d8'
PNL=f'background: rgba(8,28,54,.86); border: 1px solid {BPD}; border-radius: 16px;'
def ptitle(t, extra=''):
    return f'<div style="display: flex; align-items: center; justify-content: space-between; padding: 14px 16px 10px; border-bottom: 1px dashed {BPD};"><span style="font-family: {MONO}; font-size: 12px; letter-spacing: .14em; color: {BP};">{t}</span>{extra}</div>'
def btn(t, ic=None, primary=False):
    return f'<button style="height: 32px; padding: 0 12px; border-radius: 8px; border: 1px solid {BP if primary else BPD}; background: {"rgba(140,195,255,.16)" if primary else "none"}; color: {BTXT}; font-family: {MONO}; font-size: 11.5px; display: flex; align-items: center; gap: 6px; white-space: nowrap;">{icon(ic,13) if ic else ""}{t}</button>'
def btier(t):
    c={'sharp':'#ffd08a','hazy':'#ffd08a','forgotten':'#7f8fa6'}[t]
    st={'sharp':'solid','hazy':'dashed','forgotten':'dotted'}[t]
    return f'<span style="display: inline-flex; align-items: center; justify-content: center; width: 78px; height: 22px; border-radius: 11px; border: 1px {st} {c}; color: {c}; font-family: {MONO}; font-size: 11px; {"opacity: .7;" if t=="forgotten" else ""}">{t}</span>'
def imp(n):
    return '<span style="display: flex; gap: 2px;">'+''.join(f'<span style="width: 5px; height: 12px; border-radius: 1px; background: {BP if i<n else "rgba(140,195,255,.18)"}; display: block;"></span>' for i in range(10))+'</span>'
def mrow(t, text, how, n, score, when, was=None, pinned=False):
    wasl = f'<span style="font-size: 12px; color: {BMUT}; text-decoration: line-through; text-decoration-color: rgba(157,184,216,.5);">was sharp: {was}</span>' if was else ''
    return f"""<div style="display: grid; grid-template-columns: 86px minmax(0, 1fr) 150px 84px 70px; gap: 12px; align-items: center; padding: 12px 16px; border-bottom: 1px dashed {BPD};">
{btier(t)}
<span style="display: flex; flex-direction: column; gap: 4px;"><span style="font-size: 14px; color: {BTXT}; line-height: 1.35;{" opacity: .55;" if t=="forgotten" else ""}">{text}</span>{wasl}<span style="font-family: {MONO}; font-size: 11px; color: {BMUT};">{when}</span></span>
<span style="font-family: {MONO}; font-size: 11.5px; color: {BTXT}; line-height: 1.5;">{how}</span>
<span style="display: flex; flex-direction: column; gap: 4px;">{imp(n)}<span style="font-family: {MONO}; font-size: 11px; color: {BMUT};">importance {n}</span></span>
<span style="display: flex; gap: 4px;"><button aria-label="Pin" style="width: 30px; height: 30px; border-radius: 8px; border: 1px solid {BP if pinned else BPD}; background: none; color: {BTXT}; display: flex; align-items: center; justify-content: center;">{icon('pushpin',13)}</button><button aria-label="Hide" style="width: 30px; height: 30px; border-radius: 8px; border: 1px solid {BPD}; background: none; color: {BTXT}; display: flex; align-items: center; justify-content: center;">{icon('eyeoff',13)}</button></span>
</div>"""
tabs = ''.join(f'<button aria-pressed="{"true" if w=="mira" else "false"}" style="height: 34px; padding: 0 12px 0 5px; border-radius: 17px; border: 1px solid {BP if w=="mira" else BPD}; background: {"rgba(140,195,255,.14)" if w=="mira" else "none"}; color: {BTXT}; font-size: 12.5px; font-weight: 600; display: flex; align-items: center; gap: 7px;">{face(w,24)}{NAME[w]}</button>' for w in ('mira','tobin'))
memory = f"""<section style="position: absolute; left: 24px; top: 104px; width: 820px; height: 772px; {PNL} display: flex; flex-direction: column; overflow: hidden;">
{ptitle('MEMORY', '<span style="font-family: '+MONO+'; font-size: 11px; color: '+BMUT+';">branch: main · take 1</span>')}
<div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px;"><div style="display: flex; gap: 8px;">{tabs}</div><div style="display: flex; gap: 6px;">{btn('all 41')}{btn('sharp 23')}{btn('hazy 12')}{btn('forgotten 6')}</div></div>
<div style="display: grid; grid-template-columns: 86px minmax(0, 1fr) 150px 84px 70px; gap: 12px; padding: 8px 16px; font-family: {MONO}; font-size: 10.5px; letter-spacing: .1em; color: {BMUT}; border-bottom: 1px solid {BPD};"><span>TIER</span><span>MEMORY · STORY TIME</span><span>HOW SHE LEARNED IT</span><span>WEIGHT</span><span></span></div>
{mrow('hazy','Aren hid the guild ledger somewhere behind the bar.','witnessed<br>recall 0.82',9,.82,'Day 1, 19:12 · faded Year 7','under the third floorboard behind the bar, kept from Tobin')}
{mrow('sharp','Aren says the ledger is buried by the lighthouse.','told by Aren<br><span style="color: #cbb8ff;">doubted</span> · recall 0.64',6,.64,'Year 7, Day 1, 19:20')}
{mrow('sharp','Aren is a newcomer to the docks, and pays in coin.','told by Aren<br>recall 0.31',4,.31,'Day 1, 19:02', pinned=True)}
{mrow('hazy','Tobin went to the bar when Aren asked him to, and didn’t like it.','witnessed<br>recall 0.12',3,.12,'Day 1, 19:10')}
{mrow('forgotten','Tobin wore a green apron.','witnessed',2,0,'Day 1, 19:06')}
<div style="padding: 10px 16px; font-family: {MONO}; font-size: 11px; color: {BMUT}; display: flex; align-items: center; gap: 8px;">{icon('pushpin',12,BMUT)}Pinned facts sit in every prompt. · Tobin: 0 memories of the ledger (he wasn’t there).</div>
<div style="margin: auto 16px 16px; padding: 14px; border-radius: 12px; border: 1px dashed {BP}; display: flex; flex-direction: column; gap: 10px;">
<span style="font-family: {MONO}; font-size: 11px; letter-spacing: .12em; color: {BP};">WRITE A MEMORY</span>
<label style="display: flex; flex-direction: column; gap: 4px;"><span class="sr">Memory text</span><input type="text" placeholder="What does she know?" style="height: 38px; border-radius: 8px; border: 1px solid {BPD}; background: rgba(0,0,0,.2); color: {BTXT}; padding: 0 12px; font-size: 14px;"></label>
<div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
<label style="display: flex; align-items: center; gap: 8px; font-family: {MONO}; font-size: 11.5px; color: {BTXT};">importance<input type="range" min="1" max="10" value="5" style="width: 120px; accent-color: {BP};">5</label>
<label style="display: flex; align-items: center; gap: 8px; font-family: {MONO}; font-size: 11.5px; color: {BTXT};">who knows<select style="height: 30px; border-radius: 8px; border: 1px solid {BPD}; background: rgba(0,0,0,.2); color: {BTXT};"><option>Mira</option><option>Everyone knows it</option></select></label>
<label style="display: flex; align-items: center; gap: 6px; font-family: {MONO}; font-size: 11.5px; color: {BTXT};"><input type="checkbox" style="accent-color: {BP};">keep it in every prompt</label>
<span style="margin-left: auto;">{btn('Save memory','plus',True)}</span>
</div></div>
</section>"""
segs=[('rules',600,900,'#6aa8ff'),('cards',1450,2000,'#8cc3ff'),('memory',820,1600,'#ffd08a'),('examples',540,800,'#a9e0c8'),('history',3600,9000,'#c7b8ff'),('tail',290,400,'#f4a595')]
bar=''.join(f'<span style="width: {v/16384*100:.2f}%; height: 12px; background: {c}; display: block;"></span>' for n,v,l,c in segs)
leg=''.join(f'<span style="display: flex; align-items: center; gap: 6px; font-family: {MONO}; font-size: 11px; color: {BTXT};"><span style="width: 8px; height: 8px; border-radius: 2px; background: {c}; display: block;"></span>{n} {v:,}<span style="color: {BMUT};">/ {l:,}</span></span>' for n,v,l,c in segs)
prompt = f"""<section style="position: absolute; left: 868px; top: 104px; width: 548px; height: 236px; {PNL} overflow: hidden;">
{ptitle('PROMPT', btn('full prompt','eye'))}
<div style="padding: 12px 16px; display: flex; flex-direction: column; gap: 10px;">
<div style="display: flex; justify-content: space-between; font-family: {MONO}; font-size: 12px; color: {BTXT};"><span>~7,300 / 16,384 tokens</span><span style="color: {BMUT};">counted 7,288 · cache reuse 81%</span></div>
<div style="display: flex; border-radius: 6px; overflow: hidden; background: rgba(140,195,255,.1);">{bar}</div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px 10px;">{leg}</div>
<div style="font-family: {MONO}; font-size: 11px; color: {BMUT}; line-height: 1.6;">recalled 3 · 0.82 ledger behind the bar · 0.64 lighthouse · 0.31 newcomer (pinned)<br>cut: nothing</div>
</div></section>"""
def cast(ic,name,kind,state,badge=''):
    b = f'<span style="height: 18px; padding: 0 7px; border-radius: 9px; background: rgba(255,208,138,.18); color: #ffd08a; font-family: {MONO}; font-size: 10px; display: flex; align-items: center;">{badge}</span>' if badge else ''
    return f'<div style="display: flex; align-items: center; gap: 10px; padding: 7px 16px;">{ic}<span style="font-size: 13px; font-weight: 600; color: {BTXT}; width: 110px;">{name}</span><span style="font-family: {MONO}; font-size: 10.5px; color: {BMUT}; width: 64px;">{kind}</span><span style="font-family: {MONO}; font-size: 11px; color: {BTXT}; flex-grow: 1;">{state}</span>{b}</div>'
castp = f"""<section style="position: absolute; left: 868px; top: 356px; width: 548px; height: 262px; {PNL} overflow: hidden;">
{ptitle('CAST', btn('these two are the same','merge'))}
{cast(face('mira',24),'Mira','character','location: The Gull · holding: mug')}
{cast(face('tobin',24),'Tobin','character','location: unknown · away')}
{cast(face('aren',24),'Aren','persona','location: The Gull')}
{cast('<span style="width: 24px; display: flex; justify-content: center; color: '+BP+';">'+icon('map-pin',16)+'</span>','The Gull','place','time: night · rain')}
{cast('<span style="width: 24px; display: flex; justify-content: center; color: '+BP+';">'+icon('book',16)+'</span>','guild ledger','item','location: disputed','found')}
{cast('<span style="width: 24px; display: flex; justify-content: center; color: '+BP+';">'+icon('users',16)+'</span>','the courier','alias?','same as Mira?','found')}
</section>"""
def run(n,status,trig,detail,badge=''):
    col={'done':'#a9e0c8','waiting':'#ffd08a','error':'#f4a595'}[status]
    b = f'<span style="height: 18px; padding: 0 7px; border-radius: 9px; border: 1px solid #ffd08a; color: #ffd08a; font-family: {MONO}; font-size: 10px; display: flex; align-items: center;">{badge}</span>' if badge else ''
    return f'<div style="display: flex; align-items: center; gap: 10px; padding: 7px 16px; font-family: {MONO}; font-size: 11.5px; color: {BTXT};"><span style="width: 8px; height: 8px; border-radius: 4px; background: {col}; display: block;"></span><span style="width: 34px;">#{n}</span><span style="width: 62px; color: {col};">{status}</span><span style="color: {BMUT}; flex-grow: 1;">{trig} · {detail}</span>{b}</div>'
reading = f"""<section style="position: absolute; left: 868px; top: 634px; width: 548px; height: 242px; {PNL} overflow: hidden; display: flex; flex-direction: column;">
{ptitle('READING', '<span style="font-family: '+MONO+'; font-size: 11px; color: '+BMUT+';">memory reader · qwen3.5-9b · thinking off</span>')}
{run(15,'waiting','2 new lines','after the time skip','stale')}
{run(14,'done','every 4 turns','1 attempt · 6 filed · 1 skipped')}
{run(13,'done','Tobin left','1 attempt · 3 filed')}
{run(12,'done','every 4 turns','2 attempts · 5 filed')}
<div style="display: flex; gap: 8px; padding: 10px 16px; margin-top: auto;">{btn('Read what is waiting now','refresh',True)}{btn('Read again carefully','search')}</div>
</section>"""
bgrid = "background-color: #06203f; background-image: linear-gradient(rgba(140,195,255,.08) 1px, transparent 1px), linear-gradient(90deg, rgba(140,195,255,.08) 1px, transparent 1px), linear-gradient(rgba(140,195,255,.04) 1px, transparent 1px), linear-gradient(90deg, rgba(140,195,255,.04) 1px, transparent 1px); background-size: 120px 120px, 120px 120px, 24px 24px, 24px 24px;"
ghost = f'<img src="{A["mira-doubtful"]}" alt="" style="position: absolute; left: 180px; top: 200px; width: 640px; height: 720px; filter: grayscale(1) brightness(2.4) contrast(.5); opacity: .08;">'
files['Scene-Backstage.dc.html'] = shell('Scene · the backstage lens',
    f'<div style="position: absolute; inset: 0; {bgrid}"></div>' + ghost + topbar('Year 7, Day 1, 19:22','night',backstage=True) + memory + prompt + castp + reading)
import json
for k,v in files.items(): open(f'root/project/{k}','w').write(v)
print(list(files))
