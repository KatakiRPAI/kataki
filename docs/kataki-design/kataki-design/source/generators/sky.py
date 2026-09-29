from lib import *
import os, re as _re
DARK = os.environ.get('KATAKI_THEME') == 'dark'
if DARK:
    INK='#e9eeff'; MUT='#a9bce0'; ACC='#82a8ff'; ACCH='#b9cdff'
    CARD='#1c2450'                      # solid cards, menus, inputs, active nav
    SOFT1='rgba(255,255,255,.045)'      # faintest fill
    SOFT2='rgba(255,255,255,.07)'
    SOFT3='rgba(255,255,255,.10)'
    SOFT4='rgba(20,27,58,.86)'           # name plates over art
    BORDER='rgba(158,186,255,.18)'
    HAIR='rgba(158,186,255,.14)'
    IBORDER='rgba(158,186,255,.22)'
    SEGBG='rgba(0,0,0,.28)'
    OKINK='#8fe6b8'; WARNINK='#ffd08a'; DANGER='#ff8ea0'
    PRIM='linear-gradient(160deg, #6f96ff, #3a62f0)'; PRIMSH='0 10px 22px rgba(20,40,110,.5)'
    SKYGRAD='linear-gradient(165deg, #0d1330 0%, #141c42 38%, #1b2352 70%, #241f52 100%)'
    SKYSOLID='#141c42'
    CLOUDFILTER='filter: brightness(.42) saturate(.55) contrast(1.05);'
    CLOUD1='.55'; CLOUD2='.3'; CLOUD3='.5'
else:
    INK='#14264d'; MUT='#4b5d82'; ACC='#2f63f0'; ACCH='#1d44b8'
    CARD='#ffffff'
    SOFT1='rgba(255,255,255,.45)'
    SOFT2='rgba(255,255,255,.6)'
    SOFT3='rgba(255,255,255,.75)'
    SOFT4='rgba(255,255,255,.84)'
    BORDER='rgba(255,255,255,.95)'
    HAIR='rgba(20,38,77,.08)'
    IBORDER='rgba(20,38,77,.14)'
    SEGBG='rgba(20,38,77,.06)'
    OKINK='#11804b'; WARNINK='#9a6206'; DANGER='#c43c5c'
    PRIM='#14264d'; PRIMSH='0 10px 22px rgba(20,38,77,.28)'
    SKYGRAD='linear-gradient(165deg, #e4f0ff 0%, #c3dafc 38%, #aec4f7 70%, #b9b3f2 100%)'
    SKYSOLID='#c3dafc'
    CLOUDFILTER=''
    CLOUD1='.9'; CLOUD2='.45'; CLOUD3='.8'
GL=f'background: {SOFT2}; border: 1px solid {BORDER}; box-shadow: 0 14px 34px rgba(62,92,170,.14); backdrop-filter: blur(16px);'
files={}

import random as _rnd
def _stars(w,h):
    _rnd.seed(3)
    dots=''.join(f'<circle cx="{_rnd.uniform(0,w):.0f}" cy="{_rnd.uniform(0,h*.8):.0f}" r="{_rnd.choice([.8,1,1,1.4,1.8]):.1f}" fill="#fff" opacity="{_rnd.uniform(.25,.9):.2f}"/>' for _ in range(150))
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-hidden="true" style="position: absolute; inset: 0;">{dots}</svg>'
            f'<div style="position: absolute; inset: 0; background: radial-gradient(760px 520px at 88% -6%, rgba(196,212,255,.20), rgba(196,212,255,0) 70%);"></div>')

def skybg(w,h):
    return (f'<div style="position: absolute; inset: 0; background: {SKYGRAD};"></div>'
            + (_stars(w,h) if DARK else '')
            + f'<img src="{A["clouds"]}" alt="" style="position: absolute; left: -120px; top: {h-620}px; width: {w+240}px; height: 900px; opacity: {CLOUD1}; {CLOUDFILTER}">'
            f'<img src="{A["clouds"]}" alt="" style="position: absolute; left: 300px; top: -420px; width: 1400px; height: 875px; opacity: {CLOUD2}; transform: scaleY(-1); {CLOUDFILTER}">')

def rail(active, h):
    items=[('Home','home'),('Characters','users'),('Chats','chat'),('Places &amp;<br>Plots','map'),('Activity','bell'),('You','user')]
    it=''
    for lab,ic in items:
        on = lab==active
        it+=f'<a href="{ {"Home":"Sky-Home.dc.html","Chats":"Sky-Chats.dc.html","Activity":"Sky-Activity.dc.html","You":"Sky-You.dc.html","Characters":"Sky-Profile-Mike.dc.html","Places &amp;<br>Plots":"Sky-Library.dc.html"}[lab] }" style="width: 76px; height: 68px; border-radius: 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; text-decoration: none; font-size: 11.5px; line-height: 1.2; text-align: center; font-weight: {700 if on else 600}; color: {ACC if on else MUT}; background: {CARD if on else "transparent"}; {"box-shadow: 0 6px 16px rgba(47,99,240,.18);" if on else ""}">{icon(ic,21, ACC if on else MUT, 2 if on else 1.8)}{lab}</a>'
    set_on = active=='Settings'
    return f'''<nav aria-label="Main" style="position: absolute; left: 20px; top: 20px; width: 92px; height: {h-40}px; box-sizing: border-box; border-radius: 32px; padding: 18px 0; display: flex; flex-direction: column; align-items: center; gap: 6px; z-index: 5; {GL}">
<div style="display: flex; flex-direction: column; align-items: center; gap: 6px; margin-bottom: 14px;"><div style="width: 34px; height: 34px; border-radius: 12px; background: linear-gradient(150deg, #7fb0ff, #3d63f2); display: flex; align-items: center; justify-content: center; box-shadow: inset 0 2px 0 rgba(255,255,255,.6);">{icon('cloud',20,'#fff',2.2)}</div><span style="font-family: {DISPLAY}; font-size: 15px; color: {INK};">Kataki</span></div>
{it}
<div style="flex-grow: 1;"></div>
<a href="Sky-Models.dc.html" style="width: 72px; height: 54px; border-radius: 18px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; text-decoration: none; font-size: 11px; font-weight: 600; color: {ACC if set_on else MUT}; background: {CARD if set_on else "transparent"};">{icon('settings',19, ACC if set_on else MUT)}Settings</a>
<a href="Main.dc.html" aria-label="Dive back into your last scene" style="display: flex; flex-direction: column; align-items: center; gap: 6px; text-decoration: none; margin-top: 8px;">{orb(54)}<span style="font-size: 11px; font-weight: 700; color: {INK};">Dive in</span></a>
</nav>'''

def shell(title, w, h, inner, active='Home', norail=False):
    body=f'<div style="width: {w}px; height: {h}px; position: relative; overflow: hidden; font-family: {SANS}; color: {INK};">{skybg(w,h)}{"" if norail else rail(active,h)}{inner}</div>'
    return page(title, w, h, body, bodybg=SKYSOLID)

def pill(text, ic=None, primary=False, dark=False, h=44, extra='', href=None):
    if dark: st=f'background: {PRIM}; color: #fff; border: 0; box-shadow: {PRIMSH};'
    elif primary: st=f'background: {ACC}; color: #fff; border: 0; box-shadow: 0 10px 22px rgba(47,99,240,.3);'
    else: st=f'background: {SOFT3}; color: {INK}; border: 1px solid {BORDER}; box-shadow: 0 4px 12px rgba(62,92,170,.1);'
    inner=f'{icon(ic,17) if ic else ""}{text}'
    base=f'height: {h}px; padding: 0 {h*0.42:.0f}px; border-radius: {h/2:.0f}px; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 14px; font-weight: 700; white-space: nowrap; text-decoration: none; box-sizing: border-box; {st}{extra}'
    if href: return f'<a href="{href}" style="{base}">{inner}</a>'
    return f'<button style="{base}">{inner}</button>'

def chip(text, on=False, ic=None):
    return f'<button aria-pressed="{"true" if on else "false"}" style="height: 38px; padding: 0 16px; border-radius: 19px; font-size: 13.5px; font-weight: 700; display: flex; align-items: center; gap: 7px; white-space: nowrap; border: 1px solid {BORDER}; background: {CARD if on else "rgba(255,255,255,.45)"}; color: {INK if on else MUT}; {"box-shadow: 0 6px 14px rgba(62,92,170,.14);" if on else ""}">{icon(ic,15) if ic else ""}{text}</button>'

def h2(t, right=''):
    return f'<div style="display: flex; align-items: center; justify-content: space-between;"><h2 style="margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -.01em;">{t}</h2>{right}</div>'

def portrait_card(who, w, h, img=None, style=''):
    key = img or who
    pos = FOCUS.get(key.split('-')[0], '50% 26%')
    return f'<div style="position: relative; width: {w}px; height: {h}px; border-radius: 28px; overflow: hidden; background: {BG[who]}; flex-shrink: 0; {style}"><img src="{A[key]}" alt="{NAME[who]}" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: {pos};"><div style="position: absolute; inset: 0; background: radial-gradient(circle at 30% 10%, rgba(255,255,255,.45), rgba(255,255,255,0) 45%);"></div></div>'

def ring(pct, s=56, sw=6, col=ACC, label=None):
    import math
    r=(s-sw)/2; c=2*math.pi*r
    return f'<div style="position: relative; width: {s}px; height: {s}px; flex-shrink: 0;"><svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" aria-hidden="true"><circle cx="{s/2}" cy="{s/2}" r="{r}" fill="none" stroke="rgba(47,99,240,.14)" stroke-width="{sw}"/><circle cx="{s/2}" cy="{s/2}" r="{r}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" stroke-dasharray="{c*pct/100:.1f} {c:.1f}" transform="rotate(-90 {s/2} {s/2})"/></svg><span style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: {s*0.26:.0f}px; font-weight: 800; color: {INK};">{label or str(pct)+"%"}</span></div>'

# ---------- HOME ----------
W,H=1440,1190
def friend_card(who, tag, status, tip='', fav=False, in_story=True, pct=None):
    POS = FOCUS.get(who, '50% 26%')
    st_dot = '#23b26d' if in_story else '#9aa6bf'
    fav_btn = f'<button aria-label="Favourite {NAME[who]}" style="position: absolute; right: 12px; top: 12px; width: 36px; height: 36px; border-radius: 50%; border: 0; background: {SOFT3}; color: {"#ff4f7b" if fav else MUT}; display: flex; align-items: center; justify-content: center;">{icon("heart",17,"#ff4f7b" if fav else MUT)}</button>'
    extra = f'<div style="position: absolute; left: 12px; top: 12px;">{ring(pct,40,4,label=str(pct))}</div>' if pct else ''
    return f'''<a href="Sky-Profile-Mike.dc.html" style="position: relative; display: block; width: 196px; height: 268px; border-radius: 28px; overflow: hidden; background: {BG[who]}; text-decoration: none; color: {INK}; box-shadow: 0 14px 30px rgba(62,92,170,.18);">
<img src="{A[who]}" alt="" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: {POS};">
{fav_btn}{extra}
<div style="position: absolute; left: 8px; right: 8px; bottom: 8px; padding: 10px 12px; border-radius: 20px; display: flex; flex-direction: column; gap: 3px; {GL} background: {SOFT3};">
<span style="font-size: 16px; font-weight: 800;">{NAME[who]}</span>
<span style="font-size: 11.5px; color: {MUT}; line-height: 1.3; height: 30px; overflow: hidden;">{tag}</span>
<span title="{tip}" style="display: flex; align-items: center; gap: 6px; font-size: 11.5px; font-weight: 700; color: {INK};"><span style="width: 7px; height: 7px; border-radius: 4px; background: {st_dot}; display: block;"></span>{status}</span>
</div></a>'''

def act_item(who, text, story, clock, kind, compact=True):
    col={'memory':'#e59a1e','feeling':'#ff5d7e','belief':'#8a63f0','time':'#2f9bd6'}[kind]
    ic={'memory':'spark','feeling':'heart','belief':'help','time':'clock'}[kind]
    return f'''<a href="Scene-AfterSkip.dc.html" style="display: flex; align-items: center; gap: 12px; padding: 10px; border-radius: 18px; text-decoration: none; color: {INK}; background: {SOFT2};">
<div style="position: relative; flex-shrink: 0;">{face(who,44)}<span style="position: absolute; right: -4px; bottom: -4px; width: 22px; height: 22px; border-radius: 50%; background: {col}; border: 2px solid #fff; display: flex; align-items: center; justify-content: center;">{icon(ic,12,'#fff',2.4)}</span></div>
<span style="display: flex; flex-direction: column; gap: 2px; flex-grow: 1;"><span style="font-size: 14px; font-weight: 600; line-height: 1.35;">{text}</span><span style="font-size: 12px; color: {MUT};">{story} · {clock}</span></span></a>'''

filters = [('All','grid','#7fb0ff','#3d63f2'),('Favourites','heart','#ff9fb8','#f0487a'),('In a story','book','#c4a4ff','#7c4ff0'),('New','spark','#8fe0b0','#22b26d'),('Groups','users','#ffc98a','#f08a2a')]
fchips=''.join(f'<button aria-pressed="{"true" if i==0 else "false"}" style="display: flex; flex-direction: column; align-items: center; gap: 6px; border: 0; background: none; padding: 0; font-size: 12.5px; font-weight: {800 if i==0 else 600}; color: {INK if i==0 else MUT};">{candy(ic,c1,c2,46)}{lab}</button>' for i,(lab,ic,c1,c2) in enumerate(filters))

moment = lambda title, sub, layers, mbg='gull-night': f'''<a href="Scene-Group-Secret.dc.html" style="position: relative; display: block; width: 604px; height: 220px; border-radius: 28px; overflow: hidden; text-decoration: none; box-shadow: 0 14px 30px rgba(62,92,170,.2);">
<img src="{A[mbg]}" alt="" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 45%;">{layers}
<div style="position: absolute; left: 12px; bottom: 12px; padding: 10px 14px; border-radius: 18px; display: flex; flex-direction: column; gap: 2px; {GL} background: {SOFT4};"><span style="font-size: 15px; font-weight: 800; color: {INK};">{title}</span><span style="font-size: 12px; color: {MUT};">{sub}</span></div></a>'''
def duo(a,b):
    return (f'<div style="position: absolute; inset: 0; background: linear-gradient(90deg, rgba(8,6,12,.1), rgba(8,6,12,.55));"></div>'
            f'<img src="{A[a]}" alt="" style="position: absolute; left: 40px; top: 10px; width: 210px; height: 210px; object-fit: cover; object-position: 50% 24%; border-radius: 50%; box-shadow: 0 16px 34px rgba(0,0,0,.45);">'
            f'<img src="{A[b]}" alt="" style="position: absolute; left: 210px; top: 34px; width: 180px; height: 180px; object-fit: cover; object-position: 50% 24%; border-radius: 50%; box-shadow: 0 16px 34px rgba(0,0,0,.45);">')
m1 = moment('A secret at Halcyon','Two Sugars, No Title · the evening it rained', duo('aren','mira'), 'gull-dusk')
m2 = moment('The gala, three weeks later','Two Sugars, No Title · three weeks later', duo('mira','aren'), 'gull-night')

home = f'''<div style="position: absolute; left: 144px; top: 28px; width: 1272px; display: flex; flex-direction: column; gap: 30px;">
<header style="display: flex; align-items: center; justify-content: space-between;">
<div style="display: flex; align-items: center; gap: 16px;">
<a href="Sky-You.dc.html" aria-label="Switch who you are" style="position: relative; display: block; text-decoration: none;">{face('aren',62,ring='0 0 0 4px #fff, 0 10px 24px rgba(62,92,170,.25)')}<span style="position: absolute; right: -4px; bottom: -2px; width: 24px; height: 24px; border-radius: 50%; background: {INK}; color: #fff; display: flex; align-items: center; justify-content: center; border: 2px solid #fff;">{icon('swap',12,'#fff',2.4)}</span></a>
<div style="display: flex; flex-direction: column;"><span style="font-size: 14px; font-weight: 600; color: {MUT};">Good evening,</span><span style="font-family: {DISPLAY}; font-size: 44px; line-height: 1; color: {INK};">Liv</span></div>
</div>
<div style="display: flex; align-items: center; gap: 10px;">
<label style="display: flex; align-items: center; gap: 10px; width: 340px; height: 48px; padding: 0 18px; box-sizing: border-box; border-radius: 24px; {GL}">{icon('search',18,MUT)}<span class="sr">Search</span><input type="search" placeholder="Search characters, stories, places" style="border: 0; outline: none; background: transparent; font-size: 14px; color: {INK}; flex-grow: 1;"></label>
<a href="Sky-Activity.dc.html" aria-label="Activity, 4 new" style="position: relative; width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: {INK}; {GL}">{icon('bell',20)}<span style="position: absolute; right: -2px; top: -2px; min-width: 20px; height: 20px; border-radius: 10px; background: #ff4f7b; color: #fff; font-size: 11px; font-weight: 800; display: flex; align-items: center; justify-content: center; border: 2px solid #fff;">4</span></a>
{pill('Add a character','plus',dark=True,h=48,href='Sky-AddCharacter.dc.html')}
</div>
</header>
<div style="display: flex; gap: 24px;">
<section aria-label="Continue your last scene" style="position: relative; width: 780px; height: 372px; border-radius: 34px; overflow: hidden; box-shadow: 0 24px 50px rgba(30,50,120,.3); flex-shrink: 0;">
<img src="{A['gull-night']}" alt="Corvel Palace at night" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 45%; filter: brightness(.8);">
<img src="{A['mira-doubtful']}" alt="Mike" style="position: absolute; left: 0; top: 0; width: 360px; height: 372px; object-fit: cover; object-position: 50% 24%; -webkit-mask-image: linear-gradient(90deg, #000 62%, transparent); mask-image: linear-gradient(90deg, #000 62%, transparent);">
<div style="position: absolute; inset: 0; background: linear-gradient(90deg, rgba(10,8,14,0) 35%, rgba(10,8,14,.78) 62%);"></div>
<div style="position: absolute; left: 380px; top: 34px; width: 360px; display: flex; flex-direction: column; gap: 12px; color: #fff;">
<span style="align-self: flex-start; height: 28px; padding: 0 12px; border-radius: 14px; background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.3); font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px;">{icon('spark',13,'#ffd08a')}Continue · 3 new memory events</span>
<span style="font-family: {SERIF}; font-size: 34px; line-height: 1.05;">Two Sugars, No Title</span>
<span style="font-size: 13px; color: rgba(255,255,255,.78);" title="Today, 7:12 pm">Corvel Palace · three weeks later · with Mike · as Liv</span>
<p style="margin: 6px 0 0; font-family: {SERIF}; font-size: 19px; line-height: 1.45; color: #f4e9da;"><span style="font-weight: 600; color: #f2b870; font-family: {SANS}; font-size: 13px;">Mike&#160;&#160;</span><em>frowns</em> …I could have sworn. Three weeks is a long time to hold one sentence.</p>
</div>
<a href="Main.dc.html" style="position: absolute; right: 28px; bottom: 26px; display: flex; align-items: center; gap: 14px; text-decoration: none; color: #fff;"><span style="font-size: 15px; font-weight: 800;">Dive back in</span>{orb(74)}</a>
</section>
<section style="flex-grow: 1; height: 372px; box-sizing: border-box; border-radius: 34px; padding: 22px; display: flex; flex-direction: column; gap: 10px; {GL}">
{h2('Activity','<a href="Sky-Activity.dc.html" style="font-size: 13px; font-weight: 700; text-decoration: none;">See all</a>')}
{act_item('mira','Mike has his doubts about what you said.','Two Sugars, No Title','2 h ago','belief')}
{act_item('mira','Three weeks passed. 12 of Mike’s memories went hazy.','Two Sugars, No Title','2 h ago','time')}
{act_item('tobin','Theo didn’t like being sent out back.','Two Sugars, No Title','yesterday','feeling')}
</section>
</div>
<section style="display: flex; flex-direction: column; gap: 18px;">
<div style="display: flex; align-items: flex-end; justify-content: space-between;"><h2 style="margin: 0; font-size: 22px; font-weight: 800;">Characters</h2><div style="display: flex; gap: 22px;">{fchips}</div></div>
<div style="display: flex; gap: 17px;">
{friend_card('mira','Barista at Halcyon. Son of the queen’s hairdresser.','Played 2 hours ago','Today, 7:12 pm · Corvel Palace',fav=True)}
{friend_card('tobin','Engineering student. Covers Mike’s shifts, hears everything.','Played 2 hours ago','Today, 6:48 pm · Halcyon Coffee')}
{friend_card('ilsa','Art student, your flatmate. Tells you the truth you asked for.','Played yesterday','22 Sep, 10:20 pm · the flat',fav=True)}
{friend_card('oren','Palace press aide. Runs six accounts, posts nothing about himself.','Played 5 days ago','18 Sep, 11:35 pm · Corvel Palace')}
{friend_card('wren','Just added. No portrait yet.','Never played','Added 21 Sep',in_story=False,pct=60)}
<a href="Sky-AddCharacter.dc.html" style="width: 196px; height: 268px; box-sizing: border-box; border-radius: 28px; border: 2px dashed rgba(47,99,240,.35); background: {SOFT1}; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; text-decoration: none; color: {INK};">{candy('plus','#7fb0ff','#3d63f2',56)}<span style="font-size: 15px; font-weight: 800;">Add a character</span><span style="font-size: 12px; color: {MUT}; text-align: center; width: 140px;">Build them like a profile, one step at a time</span></a>
</div>
</section>
<section style="display: flex; flex-direction: column; gap: 18px;">
{h2('Moments','<a href="Sky-Chats.dc.html" style="font-size: 13px; font-weight: 700; text-decoration: none;">All moments</a>')}
<div style="display: flex; gap: 24px;">{m1}{m2}</div>
</section>
</div>'''
files['Sky-Home.dc.html']=shell('Home',W,H,home,'Home')

# ---------- PROFILE ----------
PW,PH=1440,1500
def stat(ic,c1,c2,big,small):
    return f'<div style="flex: 1 1 0; display: flex; align-items: center; gap: 14px; padding: 18px; border-radius: 24px; {GL}">{candy(ic,c1,c2,48)}<span style="display: flex; flex-direction: column; gap: 2px;"><span style="font-size: 16px; font-weight: 800; line-height: 1.25;">{big}</span><span style="font-size: 12.5px; color: {MUT};">{small}</span></span></div>'
def card(title, inner, extra='', right=''):
    return f'<section style="border-radius: 28px; padding: 22px; display: flex; flex-direction: column; gap: 14px; box-sizing: border-box; {GL}{extra}"><div style="display: flex; align-items: center; justify-content: space-between;"><h3 style="margin: 0; font-size: 16px; font-weight: 800;">{title}</h3>{right}</div>{inner}</section>'
def bubble(t, who='mira'):
    import re
    t=re.sub(r'\*(.+?)\*', r'<em style="color: #5a6a8e;">\1</em>', esc(t))
    return f'<div style="display: flex; align-items: flex-end; gap: 8px;">{face(who,30)}<span style="padding: 10px 14px; border-radius: 18px 18px 18px 6px; background: {CARD}; font-size: 14.5px; line-height: 1.4; box-shadow: 0 4px 10px rgba(62,92,170,.08);">{t}</span></div>'
def tagc(t): return f'<span style="height: 30px; padding: 0 14px; border-radius: 15px; background: {SOFT4}; font-size: 13px; font-weight: 700; display: flex; align-items: center;">{t}</span>'
def lrow(ic,k,v): return f'<div style="display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid rgba(20,38,77,.07);"><span style="width: 34px; height: 34px; border-radius: 12px; background: rgba(47,99,240,.1); color: {ACC}; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">{icon(ic,17)}</span><span style="width: 110px; font-size: 13px; color: {MUT};">{k}</span><span style="font-size: 14.5px; font-weight: 600;">{v}</span></div>'
membar = f'''<div style="display: flex; flex-direction: column; gap: 8px; padding-top: 6px;"><div style="display: flex; justify-content: space-between; font-size: 13px;"><span style="font-weight: 700;">Remembers 38 things about Liv</span><a href="Scene-Backstage.dc.html" style="font-weight: 700; text-decoration: none;">See his memories</a></div>
<div style="display: flex; height: 12px; border-radius: 6px; overflow: hidden; background: {HAIR};"><span style="width: 60%; background: {ACC}; display: block;"></span><span style="width: 32%; background: repeating-linear-gradient(135deg, rgba(47,99,240,.5) 0 4px, rgba(47,99,240,.25) 4px 8px); display: block;"></span></div>
<div style="display: flex; gap: 16px; font-size: 12px; color: {MUT};"><span>23 sharp</span><span>12 hazy</span><span>3 forgotten</span></div></div>'''
living = card('Right now', 
    lrow('map-pin','Last seen','Corvel Palace, the edge of the ballroom · <span title="14 June, 7:22 pm" style="border-bottom: 1px dotted '+MUT+';">three weeks later</span>')+lrow('hand','Holding','A cloth he keeps folding')+lrow('user','Wearing','A borrowed jacket, one size out')+lrow('heart','Feels about you','Fond of you, not sure he believes you')+membar,
    right=f'<button style="height: 34px; padding: 0 14px; border-radius: 17px; border: 1px solid {BORDER}; background: {SOFT4}; color: {INK}; font-size: 12.5px; font-weight: 700; display: flex; align-items: center; gap: 6px;">{icon("book",14)}In Two Sugars, No Title{icon("down",14)}</button>')
secret = f'''<section style="position: relative; border-radius: 28px; padding: 22px; overflow: hidden; background: linear-gradient(150deg, #2a2f5c, #151a3a); color: #fff; display: flex; flex-direction: column; gap: 12px;">
<div style="display: flex; align-items: center; justify-content: space-between;"><span style="display: flex; align-items: center; gap: 10px; font-size: 16px; font-weight: 800;">{icon('lock',18,'#ffd08a')}Only Mike knows this</span><button style="height: 36px; padding: 0 14px; border-radius: 18px; border: 1px solid rgba(255,255,255,.35); background: rgba(255,255,255,.08); color: #fff; font-size: 13px; font-weight: 700; display: flex; align-items: center; gap: 6px;">{icon('eye',15)}Reveal as author</button></div>
<span style="font-family: {SERIF}; font-size: 20px; filter: blur(7px); user-select: none;">He cuts the queen’s hair now. His mother’s hands shake and no one can know.</span>
<span style="font-size: 12px; color: rgba(255,255,255,.7);">Other characters never see it. Mike acts on it.</span></section>'''
stories = ''.join(f'<a href="{href}" style="display: flex; align-items: center; gap: 12px; padding: 8px; border-radius: 18px; background: {SOFT2}; text-decoration: none; color: {INK};"><div style="width: 64px; height: 48px; border-radius: 12px; overflow: hidden; position: relative; flex-shrink: 0;"><img src="{A[bg]}" alt="" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 45%;"></div><span style="display: flex; flex-direction: column; gap: 2px;"><span style="font-size: 14px; font-weight: 800;">{t}</span><span style="font-size: 12px; color: {MUT};">{sub}</span></span></a>' for t,sub,bg,href in [('Two Sugars, No Title','with Theo · as Liv · played 2 h ago','gull-dusk','Main.dc.html'),('The Long Way Home','as Cas · played 2 weeks ago','market','Sky-Chats.dc.html')])
places = ''.join(f'<div style="display: flex; flex-direction: column; gap: 6px; width: 150px;"><div style="width: 150px; height: 96px; border-radius: 16px; overflow: hidden; position: relative;"><img src="{A[bg]}" alt="" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 45%;"></div><span style="font-size: 13px; font-weight: 700;">{t}</span></div>' for t,bg in [('Halcyon Coffee','gull-dusk'),('Corvel Palace','gull-night')])
profile = f'''<div style="position: absolute; left: 144px; top: 28px; width: 1272px; display: flex; gap: 28px;">
<div style="width: 420px; display: flex; flex-direction: column; gap: 16px; flex-shrink: 0;">
<a href="Sky-Home.dc.html" style="display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 700; text-decoration: none; color: {INK};">{icon('left',18)}Characters</a>
<div style="position: relative;">{portrait_card('mira',420,540,style='box-shadow: 0 24px 50px rgba(30,50,120,.25);')}
<div style="position: absolute; left: 14px; right: 14px; bottom: 14px; padding: 16px 18px; border-radius: 24px; display: flex; flex-direction: column; gap: 8px; {GL} background: {SOFT4};">
<div style="display: flex; align-items: center; gap: 10px;"><span style="font-family: {DISPLAY}; font-size: 46px; line-height: 1;">Mike</span><span style="height: 26px; padding: 0 10px; border-radius: 13px; background: rgba(35,178,109,.14); color: {OKINK}; font-size: 12px; font-weight: 800; display: flex; align-items: center; gap: 6px;"><span style="width: 7px; height: 7px; border-radius: 4px; background: #23b26d; display: block;"></span>Played 2 hours ago</span></div>
<span style="font-size: 15px; color: {MUT};">Barista at Halcyon Coffee. Son of the queen’s hairdresser.</span>
<div style="display: flex; gap: 6px;">{tagc('Barista')}{tagc('Steady')}{tagc('Private')}</div>
</div></div>
<a href="Main.dc.html" style="height: 64px; border-radius: 32px; background: {PRIM}; color: #fff; display: flex; align-items: center; justify-content: space-between; padding: 0 8px 0 26px; text-decoration: none; box-shadow: 0 14px 30px rgba(20,38,77,.3);"><span style="display: flex; flex-direction: column;"><span style="font-size: 17px; font-weight: 800;">Message Mike</span><span style="font-size: 12px; color: rgba(255,255,255,.7);">Continues Two Sugars, No Title</span></span>{orb(48)}</a>
<div style="display: flex; gap: 10px;">{pill('Start a new story','plus',extra=' flex: 1 1 0;')}{pill('Start a group scene','users',extra=' flex: 1 1 0;')}</div>
<button style="align-self: center; height: 40px; padding: 0 14px; border: 0; background: none; color: {MUT}; font-size: 13.5px; font-weight: 700; display: flex; align-items: center; gap: 6px;">{icon('edit',15)}Edit profile</button>
</div>
<div style="flex-grow: 1; display: flex; flex-direction: column; gap: 18px; padding-top: 36px;">
<div style="display: flex; gap: 14px;">{stat('book','#c4a4ff','#7c4ff0','2 stories together','as Liv and as Cas')}{stat('spark','#ffd58a','#f0a020','Remembers 38 things','about Liv')}{stat('clock','#8fe0b0','#22b26d','Last played 2 hours ago','Today, 7:12 pm · Corvel Palace')}</div>
{living}
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px;">
{card('About', f'<p style="margin: 0; font-size: 15px; line-height: 1.5;">Barista at Halcyon Coffee, six days a week. His mother does the queen’s hair, which makes him family in the way the palace means it: invited, never photographed.</p><span style="font-size: 12px; color: {MUT};">What anyone in a scene can see or know.</span><div style="display: flex; align-items: center; gap: 8px; font-size: 13px;"><span style="color: {MUT};">Also known as</span>{tagc("Michael")}</div>')}
{card('How he talks', bubble('Ten minutes. Drink it fast.')+bubble('*wipes the counter twice* It’s fine. It’s not fine, but it’s fine.'))}
{card('How he says hi', bubble('*flips the sign back around* You’re lucky I’m slow at closing.'))}
{secret}
{card('Relationships', f'<div style="display: flex; flex-direction: column; gap: 10px;"><div style="display: flex; align-items: center; gap: 10px;">{face("aren",36)}<span style="font-size: 14.5px; font-weight: 700; flex-grow: 1;">Fond of Liv</span><span style="font-size: 12px; color: {MUT};">has his doubts · three weeks later</span></div><div style="display: flex; align-items: center; gap: 10px;">{face("tobin",36)}<span style="font-size: 14.5px; font-weight: 700; flex-grow: 1;">Wary of Theo</span><span style="font-size: 12px; color: {MUT};">since the evening it rained</span></div></div>', right=f'<span style="font-size: 12px; color: {MUT};">Two Sugars, No Title</span>')}
{card('Stories together', f'<div style="display: flex; flex-direction: column; gap: 8px;">{stories}</div>')}
{card('Places he’s been', f'<div style="display: flex; gap: 12px;">{places}</div>')}
{card('Moments', f'<div style="display: flex; gap: 12px;"><div style="width: 150px; height: 96px; border-radius: 16px; overflow: hidden; position: relative;"><img src="{A["gull-dusk"]}" alt="" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;"></div><div style="width: 150px; height: 96px; border-radius: 16px; overflow: hidden; position: relative;"><img src="{A["gull-night"]}" alt="" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;"></div></div><span style="font-size: 12px; color: {MUT};">A secret at The Gull · Reunion, six years later</span>')}
</div>
</div>
</div>'''
files['Sky-Profile-Mike.dc.html']=shell('Mike’s profile',PW,PH,profile,'Characters')

# ---------- ADD A FRIEND ----------
SW,SH=1440,900
steps=[('Name and portrait','done'),('Who they are','done'),('Their secret','now'),('How they talk','todo'),('How they say hi','todo'),('Other names and tags','todo')]
st=''
for i,(t,s) in enumerate(steps):
    dot = (f'<span style="width: 30px; height: 30px; border-radius: 50%; background: #23b26d; display: flex; align-items: center; justify-content: center;">{icon("check",15,"#fff",2.6)}</span>' if s=='done'
           else f'<span style="width: 30px; height: 30px; border-radius: 50%; background: {ACC}; color: #fff; font-size: 13px; font-weight: 800; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 5px rgba(47,99,240,.18);">{i+1}</span>' if s=='now'
           else f'<span style="width: 30px; height: 30px; border-radius: 50%; border: 2px solid {IBORDER}; box-sizing: border-box; color: {MUT}; font-size: 13px; font-weight: 800; display: flex; align-items: center; justify-content: center;">{i+1}</span>')
    st+=f'<button style="display: flex; align-items: center; gap: 12px; height: 52px; padding: 0 12px; border: 0; border-radius: 18px; background: {CARD if s=="now" else "transparent"}; color: {INK}; font-size: 14.5px; font-weight: {800 if s=="now" else 600}; text-align: left;">{dot}{t}</button>'
prompts=''.join(f'<button style="height: 36px; padding: 0 14px; border-radius: 18px; border: 1px solid {BORDER}; background: {SOFT3}; color: {INK}; font-size: 13px; font-weight: 700;">{t}</button>' for t in ['A fear','A debt','Something they did','Someone they protect','What they want'])
addf = f'''<div style="position: absolute; left: 144px; top: 28px; width: 1272px; display: flex; flex-direction: column; gap: 22px;">
<div style="display: flex; align-items: center; justify-content: space-between;"><a href="Sky-Home.dc.html" style="display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 700; text-decoration: none; color: {INK};">{icon('left',18)}Characters</a><span style="font-size: 13px; color: {MUT};">Saved as you go</span></div>
<div style="display: flex; gap: 24px; align-items: flex-start;">
<nav aria-label="Steps" style="width: 260px; padding: 14px; box-sizing: border-box; border-radius: 28px; display: flex; flex-direction: column; gap: 4px; {GL}"><span style="font-family: {DISPLAY}; font-size: 26px; padding: 6px 12px 12px;">Add a character</span>{st}</nav>
<section style="flex-grow: 1; height: 700px; box-sizing: border-box; padding: 36px 40px; border-radius: 34px; display: flex; flex-direction: column; gap: 20px; {GL}">
<span style="font-size: 13px; font-weight: 800; letter-spacing: .1em; color: {ACC};">STEP 3 OF 6</span>
<h1 style="margin: 0; font-family: {DISPLAY}; font-weight: 400; font-size: 48px; line-height: 1;">Their secret</h1>
<p style="margin: 0; font-size: 16px; line-height: 1.5; color: {MUT}; max-width: 520px;">Something only Dani knows. Other characters never see it, but Dani acts on it, and you can reveal it as the author.</p>
<label style="display: flex; flex-direction: column; gap: 8px;"><span style="font-size: 13px; font-weight: 800;">Only Dani knows…</span><textarea rows="5" placeholder="Write it the way Dani would never say it out loud." style="resize: none; border-radius: 22px; border: 2px solid rgba(47,99,240,.4); background: {SOFT4}; padding: 18px 20px; font-size: 17px; line-height: 1.5; color: {INK}; outline: none; box-shadow: 0 0 0 5px rgba(47,99,240,.12);"></textarea></label>
<div style="display: flex; flex-direction: column; gap: 10px;"><span style="font-size: 13px; color: {MUT}; font-weight: 700;">Stuck? Start from</span><div style="display: flex; gap: 8px; flex-wrap: wrap;">{prompts}</div></div>
<div style="margin-top: auto; display: flex; align-items: center; justify-content: space-between;">{pill('Back','left')}<div style="display: flex; gap: 10px;"><button style="height: 48px; padding: 0 18px; border: 0; background: none; color: {MUT}; font-size: 14px; font-weight: 700;">Skip for now</button>{pill('Next: How they talk','arrow',dark=True,h=48)}</div></div>
</section>
<aside aria-label="Live profile preview" style="width: 320px; flex-shrink: 0; display: flex; flex-direction: column; gap: 14px;">
<div style="position: relative;">{portrait_card('wren',320,360)}
<div style="position: absolute; left: 12px; right: 12px; bottom: 12px; padding: 14px 16px; border-radius: 22px; display: flex; flex-direction: column; gap: 4px; {GL} background: {SOFT4};"><span style="font-family: {DISPLAY}; font-size: 34px; line-height: 1;">Dani</span><span style="font-size: 13.5px; color: {MUT};">Florist. Delivers to the palace back gate twice a week.</span></div></div>
<div style="padding: 16px; border-radius: 24px; display: flex; align-items: center; gap: 14px; {GL}">{ring(60,62,7)}<span style="display: flex; flex-direction: column; gap: 3px;"><span style="font-size: 14.5px; font-weight: 800;">Add a secret to make Dani more real</span><span style="font-size: 12.5px; color: {MUT};">Characters with secrets hold back, and it shows.</span></span></div>
<div style="padding: 16px; border-radius: 24px; display: flex; flex-direction: column; gap: 10px; {GL}">
<div style="display: flex; align-items: center; gap: 10px; font-size: 13.5px; font-weight: 700;">{icon('check',16,'#23b26d',2.4)}Name and portrait</div>
<div style="display: flex; align-items: center; gap: 10px; font-size: 13.5px; font-weight: 700;">{icon('check',16,'#23b26d',2.4)}Who they are</div>
<div style="display: flex; align-items: center; gap: 10px; font-size: 13.5px; font-weight: 700; color: {ACC};">{icon('lock',16,ACC)}Secret · writing now</div>
<div style="display: flex; align-items: center; gap: 10px; font-size: 13.5px; color: {MUT};">{icon('chat',16,MUT)}How they talk</div>
</div>
</aside>
</div></div>'''
files['Sky-AddCharacter.dc.html']=shell('Add a character',SW,SH,addf,'Characters')

# ---------- CHATS ----------
def stack(ws, s=48):
    if len(ws)==1: return face(ws[0],s,ring='0 0 0 3px #fff')
    return f'<div style="position: relative; width: {s+14}px; height: {s}px; flex-shrink: 0;"><div style="position: absolute; left: 0; top: 0;">{face(ws[0],s-8,ring="0 0 0 3px #fff")}</div><div style="position: absolute; left: 18px; top: 12px;">{face(ws[1],s-8,ring="0 0 0 3px #fff")}</div></div>'
def thread(ws, title, last, ago, tip, persona, badge=0, sel=False, pinned=False):
    b = f'<span style="min-width: 24px; height: 24px; padding: 0 7px; box-sizing: border-box; border-radius: 12px; background: #f0a020; color: #fff; font-size: 11.5px; font-weight: 800; display: flex; align-items: center; gap: 3px;">{icon("spark",11,"#fff",2.4)}{badge}</span>' if badge else ''
    pn = icon('pushpin',13,MUT) if pinned else ''
    return f'''<a href="Main.dc.html" style="display: flex; align-items: center; gap: 14px; padding: 14px; border-radius: 22px; text-decoration: none; color: {INK}; background: {CARD if sel else "transparent"}; {"box-shadow: 0 8px 20px rgba(62,92,170,.14);" if sel else ""}">
{stack(ws)}
<span style="display: flex; flex-direction: column; gap: 3px; flex-grow: 1; min-width: 0;"><span style="display: flex; align-items: center; justify-content: space-between; gap: 8px;"><span style="font-size: 15px; font-weight: 800; display: flex; align-items: center; gap: 6px;">{title}{pn}</span><span title="{tip}" style="font-size: 12px; color: {MUT}; white-space: nowrap; font-variant-numeric: tabular-nums;">{ago}</span></span>
<span style="display: flex; align-items: center; justify-content: space-between; gap: 8px;"><span style="font-size: 13.5px; color: {MUT}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{last}</span>{b}</span>
<span style="font-size: 11.5px; font-weight: 700; color: {ACC};">as {persona}</span></span></a>'''
chats = f'''<div style="position: absolute; left: 144px; top: 28px; width: 1272px; height: 844px; display: flex; gap: 24px;">
<section style="width: 500px; box-sizing: border-box; padding: 22px; border-radius: 34px; display: flex; flex-direction: column; gap: 14px; {GL}">
<h1 style="margin: 0; font-family: {DISPLAY}; font-weight: 400; font-size: 40px; line-height: 1;">Chats</h1><div style="display: flex; gap: 8px;">{pill('New chat','plus',dark=True,h=42)}{pill('New group scene','users',h=42)}</div>
<div style="display: flex; gap: 6px;">{chip('All',True)}{chip('One-to-one')}{chip('Groups')}</div>
<span style="font-size: 11.5px; font-weight: 800; letter-spacing: .12em; color: {MUT}; padding: 6px 4px 0;">PINNED</span>
{thread(['mira','tobin'],'Two Sugars, No Title','Mike: …I could have sworn. Three weeks is a long time.','2 h ago','Today, 7:12 pm','Liv · three weeks later',3,True,True)}
<span style="font-size: 11.5px; font-weight: 800; letter-spacing: .12em; color: {MUT}; padding: 6px 4px 0;">ALL STORIES</span>
{thread(['oren'],'The Gala List','Jae: Your name is on it. Don’t ask me how.','Yesterday','22 Sep, 10:20 pm','Liv · two days before the gala',1)}
{thread(['ilsa'],'Three in the Morning','Nico: You’re not going to like this painting.','5 d ago','18 Sep, 11:35 pm','Liv · the night before the game')}
{thread(['mira'],'The Long Way Home','Mike: You can’t park there.','2 w ago','8 Sep, 9:05 pm','Cas · the week the engine died')}
</section>
<section style="flex-grow: 1; border-radius: 34px; overflow: hidden; display: flex; flex-direction: column; {GL} background: {SOFT3};">
<div style="position: relative; height: 380px; flex-shrink: 0; overflow: hidden;">
<img src="{A['gull-night']}" alt="Corvel Palace at night" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 45%; filter: brightness(.82);">
<img src="{A['mira-doubtful']}" alt="Mike" style="position: absolute; left: 40px; top: 0; width: 320px; height: 380px; object-fit: cover; object-position: 50% 22%; -webkit-mask-image: linear-gradient(180deg, #000 70%, transparent); mask-image: linear-gradient(180deg, #000 70%, transparent);">
<div style="position: absolute; inset: 0; background: linear-gradient(180deg, rgba(10,8,14,0) 45%, rgba(10,8,14,.72));"></div>
<span style="position: absolute; left: 22px; top: 20px; height: 28px; padding: 0 12px; border-radius: 14px; background: rgba(255,255,255,.2); border: 1px solid rgba(255,255,255,.35); color: #fff; font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px;">{icon('image',13,'#fff')}Last moment</span>
<div style="position: absolute; left: 26px; bottom: 22px; display: flex; flex-direction: column; gap: 6px; color: #fff;"><span style="font-family: {SERIF}; font-size: 34px; line-height: 1;">Two Sugars, No Title</span><span style="font-size: 13.5px; color: rgba(255,255,255,.82);" title="14 June, 7:22 pm">Corvel Palace · three weeks later · as Liv</span></div>
<a href="Main.dc.html" style="position: absolute; right: 26px; bottom: 20px; display: flex; align-items: center; gap: 12px; text-decoration: none; color: #fff; font-size: 15px; font-weight: 800;">Dive in{orb(70)}</a>
</div>
<div style="padding: 24px 26px; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px;">
<div style="display: flex; flex-direction: column; gap: 12px;"><span style="font-size: 11.5px; font-weight: 800; letter-spacing: .12em; color: {MUT};">IN THIS STORY</span>
<div style="display: flex; align-items: center; gap: 10px;">{face('mira',40)}<span style="display: flex; flex-direction: column;"><span style="font-size: 14.5px; font-weight: 800;">Mike</span><span style="font-size: 12px; color: {MUT};">Here · remembers 38 things about you</span></span></div>
<div style="display: flex; align-items: center; gap: 10px;">{face('tobin',40,fstyle='filter: grayscale(.8);')}<span style="display: flex; flex-direction: column;"><span style="font-size: 14.5px; font-weight: 800;">Theo</span><span style="font-size: 12px; color: {MUT};">Away since the café · knows nothing about the list</span></span></div>
<a href="Sky-Profile-Mike.dc.html" style="margin-top: 6px; font-size: 13px; font-weight: 700; text-decoration: none;">Start a fresh story with Mike</a></div>
<div style="display: flex; flex-direction: column; gap: 8px;"><span style="font-size: 11.5px; font-weight: 800; letter-spacing: .12em; color: {MUT};">NEW SINCE YOU LEFT</span>
{act_item('mira','Mike has his doubts about what you said.','2 hours ago','7:22 pm, three weeks later','belief')}
{act_item('mira','Mike will remember that you never said it.','2 hours ago','7:20 pm','memory')}
{act_item('mira','12 of Mike’s memories went hazy.','2 hours ago','the time skip','time')}
</div></div>
</section></div>'''
files['Sky-Chats.dc.html']=shell('Chats',SW,SH,chats,'Chats')

# ---------- YOU + PERSONA SWITCHER ----------
def known(who, n, sub):
    return f'<div style="display: flex; align-items: center; gap: 12px; padding: 10px; border-radius: 18px; background: {SOFT2};">{face(who,44)}<span style="display: flex; flex-direction: column; gap: 2px; flex-grow: 1;"><span style="font-size: 14.5px; font-weight: 800;">{NAME[who]} remembers {n} things</span><span style="font-size: 12px; color: {MUT};">{sub}</span></span>{icon("right",16,MUT)}</div>'
def pers(who, tag, on=False, sub=''):
    ic = face(who,48) if who else f'<span style="width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(150deg,#e8ecf6,#c4cde2); display: flex; align-items: center; justify-content: center; color: {INK}; flex-shrink: 0;">{icon("quill",22)}</span>'
    nm = NAME[who] if who else 'Director'
    return f'<button aria-pressed="{"true" if on else "false"}" style="display: flex; align-items: center; gap: 12px; padding: 10px; border-radius: 20px; border: {"2px solid "+ACC if on else "2px solid transparent"}; background: {"rgba(47,99,240,.07)" if on else "transparent"}; color: {INK}; text-align: left; width: 100%;">{ic}<span style="display: flex; flex-direction: column; gap: 2px; flex-grow: 1;"><span style="font-size: 15px; font-weight: 800;">{nm}</span><span style="font-size: 12.5px; color: {MUT};">{tag}</span></span>{icon("check",18,ACC,2.6) if on else ""}</button>'
switcher = f'''<div role="dialog" aria-label="Switch who you are" style="position: absolute; left: 150px; top: 108px; width: 380px; padding: 16px; box-sizing: border-box; border-radius: 30px; display: flex; flex-direction: column; gap: 6px; z-index: 8; background: {CARD}; border: 1px solid {BORDER}; box-shadow: 0 30px 70px rgba(30,50,120,.3);">
<span style="font-size: 12px; font-weight: 800; letter-spacing: .12em; color: {MUT}; padding: 4px 8px 8px;">WHO ARE YOU IN NEW CHATS?</span>
{pers('aren','Cheerleader. The queen’s step-sister’s daughter.',True)}
{pers('sable','Twelfth in line, and hates it.')}
{pers(None,'Play no one. Direct the story.')}
<div style="height: 1px; background: {HAIR}; margin: 6px 0;"></div>
<button style="display: flex; align-items: center; gap: 12px; padding: 10px; border: 0; border-radius: 20px; background: none; color: {ACC}; font-size: 14.5px; font-weight: 800;"><span style="width: 48px; height: 48px; border-radius: 50%; border: 2px dashed rgba(47,99,240,.4); box-sizing: border-box; display: flex; align-items: center; justify-content: center;">{icon('plus',20,ACC)}</span>New persona</button>
<span style="font-size: 12px; color: {MUT}; padding: 4px 10px 2px; line-height: 1.4;">Each chat keeps the persona it started with. Characters know each of your personas separately.</span>
</div>'''
you = f'''<div style="position: absolute; left: 144px; top: 28px; width: 1272px; display: flex; flex-direction: column; gap: 22px;">
<header style="display: flex; align-items: center; gap: 14px;"><button aria-label="Switch who you are" aria-expanded="true" style="position: relative; border: 0; background: none; padding: 0;">{face('aren',62,ring='0 0 0 4px #fff, 0 0 0 7px rgba(47,99,240,.4)')}</button><div style="display: flex; flex-direction: column;"><span style="font-size: 14px; font-weight: 600; color: {MUT};">You are playing</span><span style="font-family: {DISPLAY}; font-size: 40px; line-height: 1;">Liv</span></div></header>
<div style="display: flex; gap: 28px; margin-left: 420px;">
<div style="width: 360px; flex-shrink: 0; display: flex; flex-direction: column; gap: 14px;">
<div style="position: relative;">{portrait_card('aren',360,440)}<span style="position: absolute; left: 14px; top: 14px; height: 32px; padding: 0 14px; border-radius: 16px; background: {INK}; color: #fff; font-size: 12.5px; font-weight: 800; display: flex; align-items: center; gap: 6px;">{icon('user',14,'#fff')}Played by you</span>
<div style="position: absolute; left: 12px; right: 12px; bottom: 12px; padding: 14px 16px; border-radius: 22px; display: flex; flex-direction: column; gap: 4px; {GL} background: {SOFT4};"><span style="font-family: {DISPLAY}; font-size: 36px; line-height: 1;">Liv</span><span style="font-size: 14px; color: {MUT};">Cheerleader. The queen’s step-sister’s daughter.</span></div></div>
{pill('Edit Liv','edit',extra=' width: 100%;')}
</div>
<div style="flex-grow: 1; display: flex; flex-direction: column; gap: 18px;">
{card('Who knows Liv', known('mira',38,'Two Sugars, No Title · 12 hazy after the skip')+known('tobin',11,'Two Sugars, No Title · nothing about the list')+known('ilsa',17,'Three in the Morning'))}
{card('Liv’s chats', stories.replace('with Theo · as Liv · played 2 h ago','Mike and Theo · 2 h ago').replace('The Long Way Home','The Gala List').replace('as Cas · played 2 weeks ago','Jae · yesterday'))}
</div></div></div>{switcher}'''
files['Sky-You.dc.html']=shell('You and your personas',SW,SH,you,'You')

# ---------- ACTIVITY ----------
def aitem(who, text, story, clock, kind, open_=False, quote=None):
    col={'memory':'#e59a1e','feeling':'#ff5d7e','belief':'#8a63f0','time':'#2f9bd6'}[kind]
    ic={'memory':'spark','feeling':'heart','belief':'help','time':'clock'}[kind]
    q = f'''<div style="margin: 4px 0 0 66px; padding: 14px 18px; border-radius: 18px; background: #1a1411; color: #f4e9da; display: flex; flex-direction: column; gap: 6px;"><span style="font-size: 12px; font-weight: 700; color: #a9c8ff;">Liv · the evening it rained, 7:12 pm</span><span style="font-family: {SERIF}; font-size: 17px; line-height: 1.45;">{quote}</span><a href="Scene-Group-Secret.dc.html" style="align-self: flex-start; margin-top: 4px; font-size: 13px; font-weight: 700; color: #f0b35a; text-decoration: none; display: flex; align-items: center; gap: 6px;">Open the line{icon("arrow",14,"#f0b35a")}</a></div>''' if quote else ''
    return f'''<div style="display: flex; flex-direction: column; padding: 14px; border-radius: 22px; background: {CARD if open_ else SOFT1}; {"box-shadow: 0 10px 24px rgba(62,92,170,.14);" if open_ else ""}">
<a href="Scene-AfterSkip.dc.html" style="display: flex; align-items: center; gap: 14px; text-decoration: none; color: {INK};"><div style="position: relative; flex-shrink: 0;">{face(who,52)}<span style="position: absolute; right: -4px; bottom: -4px; width: 26px; height: 26px; border-radius: 50%; background: {col}; border: 3px solid #fff; display: flex; align-items: center; justify-content: center;">{icon(ic,13,'#fff',2.4)}</span></div>
<span style="display: flex; flex-direction: column; gap: 3px; flex-grow: 1;"><span style="font-size: 16px; font-weight: 700; line-height: 1.35;">{text}</span><span style="font-size: 12.5px; color: {MUT};">{story} · {clock}</span></span>{icon("right",18,MUT)}</a>{q}</div>'''
legend = f'''<div style="display: flex; flex-direction: column; gap: 10px; font-size: 13.5px;"><div style="display: flex; align-items: center; gap: 10px;">{face("mira",28,ring="0 0 0 2px #f0b35a, 0 0 8px rgba(240,179,90,.8)")}<span><b>Sharp</b> · she recalls the detail</span></div><div style="display: flex; align-items: center; gap: 10px;">{face("mira",28,extra_style="opacity: .4;")}<span><b>Hazy</b> · only the gist</span></div><div style="display: flex; align-items: center; gap: 10px;"><span style="width: 28px; height: 28px; border-radius: 50%; border: 2px dotted rgba(20,38,77,.3); box-sizing: border-box; display: block;"></span><span><b>Forgotten</b></span></div><div style="display: flex; align-items: center; gap: 10px;"><span style="width: 28px; height: 28px; border-radius: 50%; border: 2px dashed rgba(20,38,77,.35); box-sizing: border-box; font-size: 11px; font-weight: 800; color: {MUT}; display: flex; align-items: center; justify-content: center;">T</span><span><b>Wasn’t there</b> · never heard it</span></div></div>'''
activity = f'''<div style="position: absolute; left: 144px; top: 28px; width: 1272px; display: flex; gap: 24px;">
<section style="width: 820px; display: flex; flex-direction: column; gap: 14px;">
<div style="display: flex; align-items: center; justify-content: space-between;"><h1 style="margin: 0; font-family: {DISPLAY}; font-weight: 400; font-size: 44px; line-height: 1;">Activity</h1><div style="display: flex; gap: 6px;">{chip('All',True)}{chip('Memories',ic='spark')}{chip('Feelings',ic='heart')}{chip('Beliefs',ic='help')}{chip('Time',ic='clock')}</div></div>
<span style="font-size: 11.5px; font-weight: 800; letter-spacing: .12em; color: {MUT}; padding-top: 8px;">TODAY · TWO SUGARS, NO TITLE</span>
{aitem('mira','Mike has his doubts about what you said.','His memory of it is hazy, so he can be talked round','2 hours ago','belief')}
{aitem('mira','Three weeks passed in Two Sugars, No Title. 12 of Mike’s memories went hazy.','Time skip · three weeks later','2 hours ago','time')}
<span style="font-size: 11.5px; font-weight: 800; letter-spacing: .12em; color: {MUT}; padding-top: 8px;">YESTERDAY · TWO SUGARS, NO TITLE</span>
{aitem('mira','Mike will remember that your mother is the queen’s step-sister.','The evening it rained, 7:12 pm','Yesterday, 9:40 pm','memory',True,'Quickly, while he’s gone. My mother is the queen’s step-sister. I’m on the gala list and I don’t want to be. Tell no one.')}
{aitem('tobin','Theo didn’t like being sent out back.','The evening it rained, 7:08 pm','Yesterday, 9:36 pm','feeling')}
</section>
<aside style="flex-grow: 1; display: flex; flex-direction: column; gap: 16px; padding-top: 70px;">
{card('Still being read', f'<p style="margin: 0; font-size: 14px; line-height: 1.5; color: {MUT};">The memory reader files new lines every few turns. These will show up here, and on the lines they belong to, once it has.</p><div style="display: flex; align-items: center; gap: 10px;">{face("mira",36)}<span style="font-size: 14px; font-weight: 700; flex-grow: 1;">2 lines in Two Sugars, No Title</span></div>{pill("Read now","refresh",h=42)}')}
{card('How receipts fade', legend)}
</aside></div>'''
files['Sky-Activity.dc.html']=shell('Activity',SW,SH,activity,'Activity')

# ---------- FIRST RUN ----------
def step(n, title, body, state):
    on = state=='now'
    head = f'<div style="display: flex; align-items: center; gap: 12px;"><span style="width: 36px; height: 36px; border-radius: 50%; background: {ACC if on else HAIR}; color: {"#fff" if on else MUT}; font-size: 15px; font-weight: 800; display: flex; align-items: center; justify-content: center;">{n}</span><span style="font-size: 19px; font-weight: 800; color: {INK if on else MUT};">{title}</span></div>'
    return f'<section style="flex: {"1.6 1 0" if on else "1 1 0"}; box-sizing: border-box; padding: 24px; border-radius: 32px; display: flex; flex-direction: column; gap: 16px; {GL}{"" if on else " opacity: .78;"}">{head}{body}</section>'
found = f'''<div style="display: flex; align-items: center; gap: 14px; padding: 14px; border-radius: 20px; background: {CARD}; box-shadow: 0 6px 16px rgba(62,92,170,.1);">{candy('server','#8fe0b0','#22b26d',48)}<span style="display: flex; flex-direction: column; gap: 2px; flex-grow: 1;"><span style="font-size: 15px; font-weight: 800;">llama.cpp on this computer</span><span style="font-size: 12.5px; color: {MUT}; font-family: {MONO};">127.0.0.1:8080 · qwen3.5-9b</span></span>{pill('Use this','check',dark=True,h=42)}</div>
<div style="display: flex; align-items: center; gap: 10px; font-size: 13px; color: {MUT};">{icon('search',15,MUT)}Looked for model servers on this computer · found 1<button style="margin-left: auto; height: 32px; padding: 0 10px; border: 0; background: none; color: {ACC}; font-size: 13px; font-weight: 700;">Look again</button></div>
<div style="height: 1px; background: {HAIR};"></div>
<div style="display: flex; align-items: center; gap: 12px;">{candy('globe','#c4a4ff','#7c4ff0',40)}<span style="display: flex; flex-direction: column; flex-grow: 1;"><span style="font-size: 14.5px; font-weight: 800;">Or add an online API</span><span style="font-size: 12.5px; color: {MUT};">OpenRouter and others. Keys stay in your system keychain.</span></span>{pill('Add an API','plus',h=40)}</div>'''
me = f'<div style="display: flex; align-items: center; gap: 12px;">{face("aren",56,extra_style="opacity: .7;")}<span style="font-size: 14px; color: {MUT}; line-height: 1.4;">Your first persona: a name, a portrait, one line about who you are.</span></div>'
fr = f'<div style="display: flex; align-items: center; gap: 12px;"><div style="position: relative; width: 84px; height: 56px; flex-shrink: 0;"><div style="position: absolute; left: 0;">{face("mira",56,extra_style="opacity: .7;")}</div><div style="position: absolute; left: 28px;">{face("wren",56,extra_style="opacity: .7;",ring="0 0 0 3px #fff")}</div></div><span style="font-size: 14px; color: {MUT}; line-height: 1.4;">Then add your first character, and message them.</span></div>'
first = f'''<img src="{A['clouds']}" alt="" style="position: absolute; left: -200px; top: 60px; width: 1840px; height: 1150px; opacity: {CLOUD3}; {CLOUDFILTER}">
<div style="position: absolute; left: 0; top: 70px; width: 1440px; display: flex; flex-direction: column; align-items: center; gap: 14px; text-align: center;">
<div style="display: flex; align-items: center; gap: 10px; font-family: {DISPLAY}; font-size: 22px; color: {INK};"><div style="width: 34px; height: 34px; border-radius: 12px; background: linear-gradient(150deg, #7fb0ff, #3d63f2); display: flex; align-items: center; justify-content: center;">{icon('cloud',20,'#fff',2.2)}</div>Kataki</div>
<h1 style="margin: 0; font-family: {DISPLAY}; font-weight: 400; font-size: 104px; line-height: 1; color: #fff; text-shadow: 0 4px 0 #6c8ff5, 0 18px 40px rgba(40,70,200,.35); transform: rotate(-2deg);">They’ll remember this.</h1>
<p style="margin: 0; font-size: 20px; font-weight: 600; color: {INK};">Characters who see, hear, remember and forget, like people do.</p>
</div>
<div style="position: absolute; left: 90px; right: 90px; top: 380px; display: flex; gap: 20px; align-items: flex-start;">
{step(1,'Connect a model',found,'now')}{step(2,'Make yourself',me,'todo')}{step(3,'Add your first character',fr,'todo')}
</div>
<div style="position: absolute; left: 90px; right: 90px; bottom: 44px; display: flex; align-items: center; justify-content: space-between;"><span style="display: flex; align-items: center; gap: 8px; font-size: 13px; color: {INK}; font-weight: 600;">{icon('shield',16)}Everything runs on your computer. Text only leaves it for the models you connect.</span>{pill('Continue','arrow',dark=True,h=52)}</div>'''
files['Sky-FirstRun.dc.html']=shell('First run',SW,SH,first,norail=True)

# ---------- MODELS ----------
MW,MH=1440,1000
def field(lab, ctl): return f'<label style="display: flex; flex-direction: column; gap: 6px;"><span style="font-size: 12px; font-weight: 800; color: {MUT};">{lab}</span>{ctl}</label>'
SEL=f'height: 42px; border-radius: 14px; border: 1px solid {IBORDER}; background: {CARD}; color: {INK}; padding: 0 12px; font-size: 14px; font-weight: 600;'
def seg(opts, on):
    return f'<div style="display: flex; gap: 3px; padding: 3px; border-radius: 16px; background: {SEGBG};">'+''.join(f'<button aria-pressed="{"true" if o==on else "false"}" style="height: 36px; padding: 0 12px; border: 0; border-radius: 13px; font-size: 12.5px; font-weight: 700; white-space: nowrap; background: {CARD if o==on else "transparent"}; color: {INK if o==on else MUT}; {"box-shadow: 0 2px 6px rgba(62,92,170,.15);" if o==on else ""}">{o}</button>' for o in opts)+'</div>'
def server(ic,c1,c2,name,sub,badges):
    b=''.join(f'<span style="height: 24px; padding: 0 10px; border-radius: 12px; background: {bg}; color: {fg}; font-size: 11.5px; font-weight: 800; display: flex; align-items: center; gap: 5px;">{t}</span>' for t,bg,fg in badges)
    return f'<div style="flex: 1 1 0; display: flex; align-items: center; gap: 14px; padding: 16px; border-radius: 24px; background: {SOFT3};">{candy(ic,c1,c2,48)}<span style="display: flex; flex-direction: column; gap: 5px; flex-grow: 1;"><span style="font-size: 15.5px; font-weight: 800;">{name}</span><span style="font-size: 12px; color: {MUT}; font-family: {MONO};">{sub}</span><span style="display: flex; gap: 6px;">{b}</span></span><div style="display: flex; flex-direction: column; gap: 6px;">{pill("Test",h=34)}<button style="height: 30px; border: 0; background: none; color: {DANGER}; font-size: 12.5px; font-weight: 700;">Remove</button></div></div>'
def job(ic,c1,c2,name,uses,detail):
    return f'<div style="display: flex; align-items: center; gap: 14px; padding: 16px; border-radius: 24px; background: {SOFT3};">{candy(ic,c1,c2,46)}<span style="display: flex; flex-direction: column; gap: 3px; flex-grow: 1;"><span style="font-size: 15px; font-weight: 800;">{name}</span><span style="font-size: 13px; font-weight: 600;">{uses}</span><span style="font-size: 12px; color: {MUT};">{detail}</span></span>{icon("right",18,MUT)}</div>'
ok = ('connected','rgba(35,178,109,.14)','{OKINK}')
subnav=''.join(f'<a href="Sky-Models.dc.html" style="height: 44px; padding: 0 14px; border-radius: 14px; display: flex; align-items: center; gap: 10px; text-decoration: none; font-size: 14px; font-weight: {800 if t=="Models" else 600}; color: {INK if t=="Models" else MUT}; background: {CARD if t=="Models" else "transparent"};">{icon(ic,17)}{t}</a>' for t,ic in [('General','settings'),('Models','cpu'),('Sound','volume'),('Privacy and keys','key'),('About','help')])
models = f'''<div style="position: absolute; left: 144px; top: 28px; width: 1272px; display: flex; gap: 24px;">
<nav aria-label="Settings" style="width: 220px; flex-shrink: 0; padding: 16px; box-sizing: border-box; border-radius: 28px; display: flex; flex-direction: column; gap: 4px; align-self: flex-start; {GL}"><span style="font-family: {DISPLAY}; font-size: 28px; padding: 4px 10px 12px;">Settings</span>{subnav}</nav>
<div style="flex-grow: 1; display: flex; flex-direction: column; gap: 20px;">
<div style="display: flex; align-items: center; justify-content: space-between;"><div style="display: flex; flex-direction: column; gap: 4px;"><h1 style="margin: 0; font-family: {DISPLAY}; font-weight: 400; font-size: 44px; line-height: 1;">Models</h1><span style="font-size: 14px; color: {MUT};">Kataki ships no model. Connect one, and pick which does each job. One is enough to start.</span></div><span style="height: 34px; padding: 0 14px; border-radius: 17px; background: rgba(35,178,109,.16); color: {OKINK}; font-size: 13px; font-weight: 800; display: flex; align-items: center; gap: 8px;"><span style="width: 8px; height: 8px; border-radius: 4px; background: #23b26d; display: block;"></span>engine ok</span></div>
<section style="padding: 22px; border-radius: 30px; display: flex; flex-direction: column; gap: 14px; {GL}">
{h2('Model servers and APIs', '<div style="display: flex; gap: 8px;">'+pill('Look for model servers on this computer','search',h=40)+pill('Add an API','plus',dark=True,h=40)+'</div>')}
<div style="display: flex; gap: 14px;">{server('server','#8fe0b0','#22b26d','llama.cpp','this computer · 127.0.0.1:8080',[ok,('qwen3.5-9b loaded','rgba(47,99,240,.1)',ACC)])}{server('globe','#c4a4ff','#7c4ff0','OpenRouter','online API · openrouter.ai/api/v1',[ok,('key stored','rgba(240,160,32,.16)','{WARNINK}')])}</div>
</section>
<section style="padding: 22px; border-radius: 30px; display: flex; flex-direction: column; gap: 14px; {GL}">
{h2('Jobs')}
<div style="display: flex; gap: 16px; align-items: flex-start;">
<div style="flex: 1.25 1 0; padding: 20px; border-radius: 26px; background: {CARD}; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 10px 24px rgba(62,92,170,.12);">
<div style="display: flex; align-items: center; gap: 14px;">{candy('users','#ff9fb8','#f0487a',48)}<span style="display: flex; flex-direction: column;"><span style="font-size: 17px; font-weight: 800;">Characters</span><span style="font-size: 12.5px; color: {MUT};">Speaks for everyone you’ve added</span></span></div>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px;">
{field('Server', f'<select style="{SEL}"><option>llama.cpp · this computer</option><option>OpenRouter</option></select>')}
{field('Model', f'<select style="{SEL}"><option>qwen3.5-9b</option></select>')}
{field('Context size', f'<input type="text" value="16,384" style="{SEL} font-family: {MONO};">')}
{field('Thinking', seg(['As the model likes','On','Off'],'Off'))}
</div>
<div style="display: flex; flex-direction: column; gap: 6px;"><span style="font-size: 12px; font-weight: 800; color: {MUT};">Kind</span><div style="display: flex; align-items: center; gap: 10px;">{seg(['Detect automatically','Standard','Reasoning'],'Detect automatically')}<button style="height: 36px; padding: 0 12px; border: 0; background: none; color: {ACC}; font-size: 13px; font-weight: 700; display: flex; align-items: center; gap: 6px;">{icon('refresh',14)}Detect now</button><span style="font-size: 12px; color: {MUT};">found: Standard</span></div></div>
<div style="display: flex; flex-direction: column; gap: 6px;"><span style="font-size: 12px; font-weight: 800; color: {MUT};">Sampler</span>{seg(['Balanced','Balanced + DRY','Creative + XTC','Focused'],'Balanced + DRY')}</div>
{field('Sent with every request (JSON)', f'<textarea rows="2" style="resize: none; border-radius: 14px; border: 1px solid {IBORDER}; background: #f6f8fd; color: {INK}; padding: 10px 12px; font-family: {MONO}; font-size: 13px;">{{ "min_p": 0.05 }}</textarea>')}
</div>
<div style="flex: 1 1 0; display: flex; flex-direction: column; gap: 10px;">
{job('quill','#ffd58a','#f0a020','Narrator','Same as Characters','llama.cpp · qwen3.5-9b')}
{job('book','#8fe0b0','#22b26d','Memory reader','qwen3.5-9b · thinking off','Files what happened every few turns')}
{job('spark','#c4a4ff','#7c4ff0','Reasoning','qwen3.5-9b · thinking on','Room to think 2,048 · effort medium')}
{job('search','#7fb0ff','#3d63f2','Recall by meaning','Same as Characters','Finds memories that fit the moment')}
</div></div></section>
</div></div>'''
files['Sky-Models.dc.html']=shell('Models',MW,MH,models,'Settings')

DARK_SCREENS={'Sky-Home.dc.html','Sky-Profile-Mike.dc.html','Sky-Chats.dc.html','Sky-Library.dc.html'}
def polish(v):
    for a,b in [('rgba(62,92,170,','rgba(0,0,0,'),('rgba(30,50,120,','rgba(0,0,0,'),('rgba(20,38,77,.28)','rgba(0,0,0,.5)'),
                ('rgba(47,99,240,','rgba(130,168,255,'),('rgba(35,178,109,.14)','rgba(53,201,138,.18)'),('rgba(35,178,109,.16)','rgba(53,201,138,.2)'),
                ('rgba(240,160,32,.16)','rgba(240,179,90,.2)'),('#e59a1e','#ffc86a'),('#ff5d7e','#ff7fa0'),('#8a63f0','#a98bff'),('#2f9bd6','#6fc0ff'),
                ('background: #14264d','background: linear-gradient(160deg, #5b86ff, #3a62f0)')]:
        v=v.replace(a,b)
    return v
for k,v in files.items():
    if DARK:
        if k not in DARK_SCREENS: continue
        open(f"root/project/{k.replace('.dc.html','-Dark.dc.html')}",'w').write(polish(v))
    else:
        open(f'root/project/{k}','w').write(v)
print(list(files))

# ---------- PLACES AND PLOTS (the library) ----------
LW,LH=1440,1400
def facechip(w_, s=26): return face(w_,s,ring='0 0 0 2px #fff')
def linkchips(items):
    out=''
    for kind,label in items:
        ic={'book':'book','story':'chat','character':'user'}[kind]
        out+=f'<span style="display: inline-flex; align-items: center; gap: 6px; height: 26px; padding: 0 10px; border-radius: 13px; background: {SOFT3}; font-size: 11.5px; font-weight: 700; color: {INK}; white-space: nowrap;">{icon(ic,13,MUT)}{label}</span>'
    return out

def place_card(name, desc, bg, times, chips, faces, w=396):  # times kept for the API; the strip is tinted from bg
    TOD=[('dawn','saturate(1.1) brightness(1.15) sepia(.25) hue-rotate(-12deg)'),('day','brightness(1.3) saturate(1.05)'),('dusk','brightness(.95)'),('night','brightness(.5) saturate(.8) hue-rotate(200deg)')]
    strip=''.join(f'<span style="flex: 1 1 0; height: 100%; position: relative; overflow: hidden; border-right: 1px solid rgba(255,255,255,.5);"><img src="{A[bg]}" alt="" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 45%; filter: {f};"><span style="position: absolute; left: 6px; bottom: 4px; font-size: 9.5px; font-weight: 800; color: #fff; text-shadow: 0 1px 3px rgba(0,0,0,.7);">{l}</span></span>' for l,f in TOD)
    ff=''.join(f'<span style="margin-left: -8px;">{facechip(x)}</span>' for x in faces)
    return f'''<article style="width: {w}px; border-radius: 28px; overflow: hidden; display: flex; flex-direction: column; {GL}">
<div style="position: relative; height: 150px; overflow: hidden;"><img src="{A[bg]}" alt="{name}" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 45%;">
<div style="position: absolute; inset: 0; background: linear-gradient(180deg, rgba(10,12,30,0) 40%, rgba(10,12,30,.6));"></div>
<span style="position: absolute; left: 14px; bottom: 10px; font-family: {DISPLAY}; font-size: 26px; color: #fff; text-shadow: 0 2px 8px rgba(0,0,0,.5);">{name}</span>
<button aria-label="Place options" style="position: absolute; right: 10px; top: 10px; width: 32px; height: 32px; border-radius: 50%; border: 0; background: {SOFT4}; color: {INK}; display: flex; align-items: center; justify-content: center;">{icon('dots',16)}</button></div>
<div style="display: flex; height: 34px;">{strip}</div>
<div style="padding: 14px 16px 16px; display: flex; flex-direction: column; gap: 10px;">
<span style="font-size: 13.5px; color: {MUT};">{desc}</span>
<div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">{linkchips(chips)}<span style="display: flex; margin-left: 8px; padding-left: 8px;">{ff}</span></div>
<div style="display: flex; gap: 8px;">{pill('Start a scene here','play' if 'play' in I else 'ff',dark=True,h=38,extra=' flex-grow: 1;')}{pill('Edit','edit',h=38)}</div>
</div></article>'''

def plot_card(name, premise, opening, chips, faces, w=396):
    ff=''.join(f'<span style="margin-left: -8px;">{facechip(x)}</span>' for x in faces)
    return f'''<article style="width: {w}px; border-radius: 28px; overflow: hidden; display: flex; flex-direction: column; {GL}">
<div style="position: relative; padding: 18px 16px 14px; background: linear-gradient(150deg, rgba(196,164,255,.5), rgba(124,79,240,.28));">
<span style="display: flex; align-items: center; gap: 10px;">{candy('spark','#c4a4ff','#7c4ff0',40)}<span style="font-family: {DISPLAY}; font-size: 24px;">{name}</span></span>
<button aria-label="Plot options" style="position: absolute; right: 10px; top: 10px; width: 32px; height: 32px; border-radius: 50%; border: 0; background: {SOFT4}; color: {INK}; display: flex; align-items: center; justify-content: center;">{icon('dots',16)}</button></div>
<div style="padding: 14px 16px 16px; display: flex; flex-direction: column; gap: 10px;">
<span style="font-family: {SERIF}; font-size: 16px; line-height: 1.4;">“{premise}”</span>
<span style="font-size: 12px; color: {MUT};">Opening narration · {opening}</span>
<div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">{linkchips(chips)}<span style="display: flex; margin-left: 8px;">{ff}</span></div>
<div style="display: flex; gap: 8px;">{pill('Start this plot','arrow',dark=True,h=38,extra=' flex-grow: 1;')}{pill('Edit','edit',h=38)}</div>
</div></article>'''

def treerow(label, sub='', level=0, sel=False, ic=None, count=''):
    pad = 12 + level*18
    return f'''<button aria-pressed="{"true" if sel else "false"}" style="display: flex; align-items: center; gap: 10px; width: 100%; height: {44 if level==0 else 38}px; padding: 0 12px 0 {pad}px; box-sizing: border-box; border: 0; border-radius: 14px; background: {CARD if sel else "none"}; color: {INK}; text-align: left; {"box-shadow: 0 6px 14px rgba(62,92,170,.12);" if sel else ""}">
{icon(ic,16, ACC if sel else MUT) if ic else ""}<span style="flex-grow: 1; font-size: {13.5 if level==0 else 13}px; font-weight: {800 if sel else 600};">{label}</span>{f'<span style="font-size: 11.5px; color: {MUT};">{count}</span>' if count else ''}</button>'''

linkpop = f'''<div role="dialog" aria-label="Link Corvel Palace" style="position: absolute; right: 24px; top: 856px; width: 320px; padding: 14px; box-sizing: border-box; border-radius: 22px; z-index: 12; background: {CARD}; border: 1px solid {BORDER}; box-shadow: 0 24px 60px rgba(30,50,120,.28); display: flex; flex-direction: column; gap: 10px;">
<span style="font-size: 14px; font-weight: 800;">Link “Corvel Palace” to…</span>
<label class="k-field" style="display: flex; flex-direction: column; gap: 5px;"><span style="font-size: 12px; font-weight: 800; color: {MUT};">Book</span><select style="height: 40px; border-radius: 14px; border: 1px solid {IBORDER}; font-size: 14px; font-weight: 600; color: {INK}; padding: 0 10px;"><option>Close to the Crown</option><option>The Flat on Ardenne</option><option>No book</option></select></label>
<span style="font-size: 12px; font-weight: 800; color: {MUT};">Stories</span>
<label style="display: flex; align-items: center; gap: 8px; font-size: 13px;"><input type="checkbox" checked="checked" style="accent-color: {ACC};">The Gala List</label>
<label style="display: flex; align-items: center; gap: 8px; font-size: 13px;"><input type="checkbox" style="accent-color: {ACC};">Two Sugars, No Title</label>
<span style="font-size: 12px; font-weight: 800; color: {MUT};">Characters who know it</span>
<div style="display: flex; gap: 6px; flex-wrap: wrap;">{''.join(f'<span style="display: flex; align-items: center; gap: 6px; height: 30px; padding: 0 10px 0 3px; border-radius: 15px; background: rgba(47,99,240,.08); font-size: 12px; font-weight: 700;">{face(w_,24)}{NAME[w_]}</span>' for w_ in ('oren','aren'))}<button style="height: 30px; padding: 0 10px; border-radius: 15px; border: 1px dashed rgba(47,99,240,.4); background: none; color: {ACC}; font-size: 12px; font-weight: 700;">+ Add</button></div>
<div style="display: flex; gap: 8px; margin-top: 4px;">{pill('Cancel',h=38,extra=' flex: 1 1 0;')}{pill('Link','check',dark=True,h=38,extra=' flex: 1 1 0;')}</div></div>'''

grouphead = lambda t, sub, ic, c1, c2: f'<div style="display: flex; align-items: center; gap: 12px; margin-top: 4px;">{candy(ic,c1,c2,40)}<span style="display: flex; flex-direction: column;"><span style="font-size: 18px; font-weight: 800;">{t}</span><span style="font-size: 12.5px; color: {MUT};">{sub}</span></span><span style="flex-grow: 1; height: 1px; background: rgba(20,38,77,.1); display: block; margin-left: 8px;"></span></div>'

library = f'''<div style="position: absolute; left: 144px; top: 28px; width: 1272px; display: flex; flex-direction: column; gap: 20px;">
<header style="display: flex; align-items: flex-end; justify-content: space-between;">
<div style="display: flex; flex-direction: column; gap: 4px;"><h1 style="margin: 0; font-family: {DISPLAY}; font-weight: 400; font-size: 44px; line-height: 1;">Places and Plots</h1><span style="font-size: 14px; color: {MUT};">Where stories happen, and what they start from. Keep them with a book or a story so they stay findable.</span></div>
<div style="display: flex; align-items: center; gap: 10px;">
<label style="display: flex; align-items: center; gap: 10px; width: 280px; height: 48px; padding: 0 18px; box-sizing: border-box; border-radius: 24px; {GL}">{icon('search',18,MUT)}<span class="sr">Search places and plots</span><input type="search" placeholder="Search" style="border: 0; outline: none; background: transparent; font-size: 14px; color: {INK}; flex-grow: 1;"></label>
{pill('New place','plus',dark=True,h=48)}{pill('New plot','spark',h=48)}</div>
</header>
<div style="display: flex; gap: 24px; align-items: flex-start;">
<aside aria-label="Filter" style="width: 280px; flex-shrink: 0; padding: 14px; box-sizing: border-box; border-radius: 28px; display: flex; flex-direction: column; gap: 4px; {GL}">
{treerow('Everything', sel=True, ic='grid', count='14')}
<span style="font-size: 11px; font-weight: 800; letter-spacing: .12em; color: {MUT}; padding: 12px 12px 4px;">BOOKS</span>
{treerow('Close to the Crown', ic='book', count='9')}
{treerow('Two Sugars, No Title', level=1, ic='chat', count='5')}
{treerow('The Gala List', level=1, ic='chat', count='3')}
{treerow('The Flat on Ardenne', ic='book', count='3')}
{treerow('Three in the Morning', level=1, ic='chat', count='3')}
{treerow('Not in a book', ic='alert', count='2')}
<span style="font-size: 11px; font-weight: 800; letter-spacing: .12em; color: {MUT}; padding: 12px 12px 6px;">CHARACTERS</span>
<div style="display: flex; flex-wrap: wrap; gap: 6px; padding: 0 8px 8px;">{''.join(f'<button style="display: flex; align-items: center; gap: 6px; height: 34px; padding: 0 12px 0 4px; border-radius: 17px; border: 1px solid {"rgba(47,99,240,.5)" if w_=="mira" else "rgba(255,255,255,.95)"}; background: {"rgba(47,99,240,.08)" if w_=="mira" else "rgba(255,255,255,.55)"}; color: {INK}; font-size: 12.5px; font-weight: 700;">{face(w_,26)}{NAME[w_]}</button>' for w_ in ('mira','tobin','ilsa','oren'))}</div>
<div style="height: 1px; background: {HAIR}; margin: 4px 8px;"></div>
<button style="display: flex; align-items: center; gap: 10px; height: 40px; padding: 0 12px; border: 0; border-radius: 14px; background: none; color: {ACC}; font-size: 13px; font-weight: 700;">{icon('plus',16,ACC)}New book</button>
</aside>
<div style="flex-grow: 1; display: flex; flex-direction: column; gap: 18px;">
<div style="display: flex; align-items: center; justify-content: space-between;">
<div style="display: flex; gap: 6px;">{chip('All',True)}{chip('Places',ic='map-pin')}{chip('Plots',ic='spark')}</div>
<div style="display: flex; align-items: center; gap: 10px;"><span style="font-size: 12.5px; color: {MUT};">Showing <b style="color: {INK};">Mike’s</b> places and plots</span>{pill('Recently used','down',h=38)}</div>
</div>
{grouphead('Close to the Crown','Book · 2 stories · 2 places · 2 plots','book','#7fb0ff','#3d63f2')}
<div style="display: flex; flex-wrap: wrap; gap: 20px;">
{place_card('Halcyon Coffee','A corner café with mismatched chairs. Rain on the window most of the year.','gull-dusk',[('dawn','x','0'),('day','x','0'),('dusk','x','0'),('night','x','0')],[('story','Two Sugars, No Title'),('story','The Gala List')],['mira','tobin'])}
{place_card('The flat on Ardenne','Two students, one sofa, a television nobody watches.','market',[('dawn','x','0'),('day','x','0'),('dusk','x','0'),('night','x','0')],[('story','Three in the Morning')],['ilsa'])}
{plot_card('The Invitation','The palace sends out the gala list, and both your names are on it.','A courier bike pulls up outside Halcyon, and the envelope has a seal on it…',[('story','Two Sugars, No Title'),('book','Close to the Crown')],['mira','oren'])}
</div>
{grouphead('The Flat on Ardenne','Book · 1 story · 1 place · 1 plot','map','#8fe0b0','#22b26d')}
<div style="display: flex; flex-wrap: wrap; gap: 20px;">
{plot_card('Closing Shift','The café shuts in ten minutes and neither of you wants to leave.','The espresso machine sighs and goes quiet…',[('story','Two Sugars, No Title'),('book','Close to the Crown')],['mira'])}
{place_card('Corvel Palace','Gold stairs, orange trees, and a guest list nobody admits to reading.','lighthouse',[('dawn','x','0'),('day','x','0'),('dusk','x','0'),('night','x','0')],[('book','Not in a book')],['oren'])}
</div>
</div></div></div>{linkpop}'''
files['Sky-Library.dc.html']=shell('Places and Plots',LW,LH,library,'Places &amp;<br>Plots')

DARK_SCREENS={'Sky-Home.dc.html','Sky-Profile-Mike.dc.html','Sky-Chats.dc.html','Sky-Library.dc.html'}
def polish(v):
    for a,b in [('rgba(62,92,170,','rgba(0,0,0,'),('rgba(30,50,120,','rgba(0,0,0,'),('rgba(20,38,77,.28)','rgba(0,0,0,.5)'),
                ('rgba(47,99,240,','rgba(130,168,255,'),('rgba(35,178,109,.14)','rgba(53,201,138,.18)'),('rgba(35,178,109,.16)','rgba(53,201,138,.2)'),
                ('rgba(240,160,32,.16)','rgba(240,179,90,.2)'),('#e59a1e','#ffc86a'),('#ff5d7e','#ff7fa0'),('#8a63f0','#a98bff'),('#2f9bd6','#6fc0ff'),
                ('background: #14264d','background: linear-gradient(160deg, #5b86ff, #3a62f0)')]:
        v=v.replace(a,b)
    return v
for k,v in files.items():
    if DARK:
        if k not in DARK_SCREENS: continue
        open(f"root/project/{k.replace('.dc.html','-Dark.dc.html')}",'w').write(polish(v))
    else:
        open(f'root/project/{k}','w').write(v)
print('written', len(files))
