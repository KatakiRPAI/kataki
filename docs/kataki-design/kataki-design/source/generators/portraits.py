import os
OUT='assets'

def eyes(expr, iris):
    out=[]
    for i,x in enumerate((172,228)):
        y=212
        if expr in ('smile','grin'):
            out.append(f'<path d="M{x-15},{y+3} Q{x},{y-10} {x+15},{y+3}" fill="none" stroke="#2a1812" stroke-width="4" stroke-linecap="round"/>')
            continue
        lid = 0
        if expr=='wary': lid=5
        if expr=='doubtful' and i==0: lid=4
        top = y-11+lid
        out.append(f'<path d="M{x-16},{y} Q{x},{top} {x+16},{y} Q{x},{y+9} {x-16},{y}Z" fill="#fbf4ea"/>')
        dx,dy=0,1
        if expr=='thinking': dx,dy=-5,-3
        if expr=='doubtful': dx=3
        out.append(f'<circle cx="{x+dx}" cy="{y+dy}" r="7.5" fill="{iris}"/>')
        out.append(f'<circle cx="{x+dx}" cy="{y+dy}" r="3.6" fill="#140c08"/>')
        out.append(f'<circle cx="{x+dx+2.5}" cy="{y+dy-2.5}" r="2" fill="#fff"/>')
        out.append(f'<path d="M{x-17},{y+1} Q{x},{top-1} {x+17},{y+1}" fill="none" stroke="#2a1812" stroke-width="3.6" stroke-linecap="round"/>')
    return ''.join(out)

def brows(expr,col,thick=5):
    L={'neutral':'M154,190 Q170,182 188,188','smile':'M154,186 Q170,178 188,184','grin':'M154,184 Q170,176 188,182',
       'wary':'M154,188 Q172,190 188,196','doubtful':'M154,192 Q170,190 188,192','thinking':'M154,184 Q170,176 188,184','sour':'M154,186 Q172,190 188,196'}
    R={'neutral':'M212,188 Q230,182 246,190','smile':'M212,184 Q230,178 246,186','grin':'M212,182 Q230,176 246,184',
       'wary':'M212,196 Q228,190 246,188','doubtful':'M212,182 Q230,170 246,180','thinking':'M212,186 Q230,180 246,188','sour':'M212,196 Q228,190 246,186'}
    return f'<path d="{L[expr]}" fill="none" stroke="{col}" stroke-width="{thick}" stroke-linecap="round"/><path d="{R[expr]}" fill="none" stroke="{col}" stroke-width="{thick}" stroke-linecap="round"/>'

def mouth(expr, lip):
    m={'neutral':f'<path d="M186,266 Q200,271 214,266" fill="none" stroke="{lip}" stroke-width="3.4" stroke-linecap="round"/>',
       'smile':f'<path d="M181,261 Q200,284 219,261 Q200,270 181,261Z" fill="#6e2a22"/><path d="M186,264 Q200,270 214,264 L212,267 Q200,272 188,267Z" fill="#fff" opacity=".9"/>',
       'grin':f'<path d="M174,257 Q200,294 228,255 Q200,268 174,257Z" fill="#5e241c"/><path d="M180,260 Q200,270 222,258 L220,264 Q200,274 182,265Z" fill="#fff"/>',
       'wary':f'<path d="M190,268 L212,267" fill="none" stroke="{lip}" stroke-width="3.4" stroke-linecap="round"/>',
       'doubtful':f'<path d="M185,270 Q199,265 216,262" fill="none" stroke="{lip}" stroke-width="3.4" stroke-linecap="round"/>',
       'thinking':f'<path d="M192,269 Q200,265 207,268" fill="none" stroke="{lip}" stroke-width="3.4" stroke-linecap="round"/>',
       'sour':f'<path d="M186,272 Q200,264 214,272" fill="none" stroke="{lip}" stroke-width="3.4" stroke-linecap="round"/>'}
    return m[expr]

C = {
 'mira': dict(skin='#f1c7a4',shade='#d69a78',hair='#b4502c',hair2='#7a301a',iris='#3f7a5a',lip='#9a4a3e',cloth='#1f5c5a',cloth2='#143f3e',style='bob'),
 'tobin': dict(skin='#d9a57c',shade='#b27a55',hair='#5a3a24',hair2='#3a2414',iris='#6b4a2a',lip='#8a4a3a',cloth='#c9962e',cloth2='#8f6a1c',style='curls'),
 'ilsa': dict(skin='#f6d6c0',shade='#dfae92',hair='#e8cc8c',hair2='#b99654',iris='#4d7fa8',lip='#b0586a',cloth='#8e2f2f',cloth2='#5e1d1f',style='braid'),
 'oren': dict(skin='#e2b491',shade='#b98763',hair='#c9c4bd',hair2='#8f8a83',iris='#4f5b52',lip='#8a4f44',cloth='#2c3a33',cloth2='#1a241f',style='bald'),
 'wren': dict(skin='#8a5a3c',shade='#6a4028',hair='#1e1b22',hair2='#0e0c10',iris='#3a2414',lip='#5a2c22',cloth='#e3b53c',cloth2='#b38a22',style='pixie'),
 'aren': dict(skin='#e8bb97',shade='#c4906c',hair='#3a2a22',hair2='#22160f',iris='#56708a',lip='#9a5448',cloth='#2b3d63',cloth2='#1b2944',style='short'),
 'sable': dict(skin='#c99a74',shade='#a3734f',hair='#1c1a1e',hair2='#0c0b0d',iris='#6a5a2a',lip='#8a3e3a',cloth='#5b1f2e',cloth2='#3a121c',style='long'),
}

def back_hair(s,c):
    h,h2=c['hair'],c['hair2']
    if s=='bob': return f'<path d="M112,215 C104,120 156,88 202,88 C252,88 302,122 290,218 C294,262 288,300 270,312 L132,312 C114,300 108,262 112,215Z" fill="{h2}"/>'
    if s=='curls':
        cs=''.join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{h2}"/>' for x,y,r in [(140,160,40),(170,120,42),(215,110,44),(258,130,40),(275,175,34),(125,205,30),(280,215,28)])
        return cs
    if s=='braid':
        b=''.join(f'<ellipse cx="{262+i*6}" cy="{300+i*38}" rx="22" ry="24" fill="{h}" stroke="{h2}" stroke-width="3"/>' for i in range(5))
        return f'<path d="M116,215 C108,125 158,92 202,92 C250,92 298,125 288,215 L280,280 L124,280Z" fill="{h2}"/>'+b
    if s=='bald': return f'<path d="M122,190 C116,230 124,262 138,270 L142,200Z M278,190 C284,230 276,262 262,270 L258,200Z" fill="{h}"/>'
    if s=='pixie': return f'<path d="M118,210 C110,125 158,94 202,94 C250,94 296,125 286,210 L282,250 L122,250Z" fill="{h2}"/>'
    if s=='short': return f'<path d="M120,205 C112,125 158,96 202,96 C250,96 294,125 284,205 L280,240 L124,240Z" fill="{h2}"/>'
    if s=='long': return f'<path d="M108,215 C98,115 156,86 202,86 C252,86 306,118 294,220 C300,300 312,380 318,440 L86,440 C92,380 104,300 108,215Z" fill="{h2}"/><path d="M270,160 C300,240 304,330 300,430 L286,430 C290,330 284,240 262,170Z" fill="#8d8a90"/>'
    return ''

def front_hair(s,c):
    h,h2=c['hair'],c['hair2']
    if s=='bob':
        return (f'<path d="M122,222 C110,138 152,98 206,98 C262,98 294,140 282,222 C276,186 262,158 238,146 C214,172 176,178 146,162 C136,180 128,200 122,222Z" fill="{h}"/>'
                f'<path d="M124,196 C116,250 122,292 142,310 C148,282 140,238 144,196Z" fill="{h}"/><path d="M280,196 C288,250 282,292 262,310 C256,282 264,238 260,196Z" fill="{h}"/>'
                f'<path d="M150,130 C180,112 230,110 260,132" fill="none" stroke="#e08a5a" stroke-width="5" opacity=".6" stroke-linecap="round"/>'
                f'<rect x="246" y="150" width="22" height="8" rx="3" fill="#d9b25a" transform="rotate(-24 257 154)"/>')
    if s=='curls':
        return ''.join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{h}"/>' for x,y,r in [(150,150,26),(178,128,28),(210,124,28),(242,134,26),(266,160,22),(136,178,18),(196,146,16),(226,150,16)])
    if s=='braid':
        return f'<path d="M124,214 C114,138 156,102 204,102 C256,102 292,140 282,214 C270,170 240,142 204,140 C170,142 136,166 124,214Z" fill="{h}"/><path d="M204,102 L200,140" stroke="{h2}" stroke-width="3"/>'
    if s=='bald': return f'<path d="M150,140 C170,122 230,122 250,140" fill="none" stroke="#fff" stroke-width="6" opacity=".25" stroke-linecap="round"/>'
    if s=='pixie':
        return f'<path d="M122,212 C112,136 154,100 204,100 C258,100 292,138 282,206 C270,176 250,160 226,158 L214,176 L200,158 L176,178 L168,158 C150,166 132,186 122,212Z" fill="{h}"/>'
    if s=='short':
        return f'<path d="M124,206 C114,134 156,100 204,100 C256,100 292,136 282,204 C274,172 256,152 232,146 C226,164 196,170 178,160 C164,170 140,176 124,206Z" fill="{h}"/>'
    if s=='long':
        return f'<path d="M116,230 C104,136 152,94 204,94 C258,94 300,136 290,230 C282,180 262,150 226,138 C196,158 160,160 140,150 C128,172 120,200 116,230Z" fill="{h}"/><path d="M252,120 C276,140 290,170 292,220" fill="none" stroke="#9c99a0" stroke-width="10" stroke-linecap="round"/>'
    return ''

def clothes(name,c):
    cl,cl2=c['cloth'],c['cloth2']
    torso=f'<path d="M36,520 C40,420 90,366 162,350 Q200,372 238,350 C310,366 360,420 364,520Z" fill="url(#cl)"/>'
    if name=='mira':
        return torso+(f'<path d="M150,352 Q200,410 250,352 L240,346 Q200,386 160,346Z" fill="#efe2c8"/>'
            f'<path d="M120,362 C160,390 240,392 286,360 C292,380 262,410 200,412 C140,410 112,384 120,362Z" fill="{cl2}"/>'
            f'<path d="M96,420 L300,520 L278,520 L90,436Z" fill="#6b4228"/><rect x="176" y="452" width="22" height="18" rx="3" fill="none" stroke="#d9b25a" stroke-width="4" transform="rotate(26 187 461)"/>'
            f'<circle cx="252" cy="398" r="9" fill="#d9b25a"/><circle cx="252" cy="398" r="4" fill="{cl2}"/>')
    if name=='tobin':
        return (f'<path d="M36,520 C40,420 90,366 162,350 Q200,372 238,350 C310,366 360,420 364,520Z" fill="#efe6d4"/>'
            f'<path d="M36,520 C40,420 90,366 150,352 L186,520Z M364,520 C360,420 310,366 250,352 L214,520Z" fill="url(#cl)"/>'
            f'<path d="M160,350 L200,392 L240,350 L230,370 L200,410 L170,370Z" fill="#b8352c"/><circle cx="276" cy="238" r="6" fill="none" stroke="#e0b64a" stroke-width="3"/>')
    if name=='ilsa':
        fur=''.join(f'<circle cx="{x}" cy="{360+((x//10)%3)*6}" r="20" fill="#ece4d6"/>' for x in range(110,300,22))
        return torso+fur
    if name=='oren':
        return torso+(f'<path d="M150,346 L200,380 L250,346 L256,400 L200,420 L144,400Z" fill="{cl2}"/><path d="M186,380 L214,380 L212,470 L188,470Z" fill="#e8e0cf"/>'
            f'<path d="M230,430 Q260,450 290,436" fill="none" stroke="#d9b25a" stroke-width="3"/><circle cx="292" cy="436" r="6" fill="#d9b25a"/>')
    if name=='wren':
        return torso+f'<path d="M160,350 L200,396 L240,350 L236,346 Q200,380 164,346Z" fill="#f5ecd6"/><path d="M200,396 L200,520" stroke="{cl2}" stroke-width="4"/><circle cx="214" cy="440" r="5" fill="{cl2}"/><circle cx="214" cy="480" r="5" fill="{cl2}"/>'
    if name=='aren':
        return torso+(f'<path d="M130,358 C160,384 240,384 272,358 C278,378 250,398 200,398 C150,398 124,380 130,358Z" fill="#9aa3ad"/>'
            f'<circle cx="170" cy="440" r="6" fill="#c9a24a"/><circle cx="170" cy="480" r="6" fill="#c9a24a"/><circle cx="232" cy="440" r="6" fill="#c9a24a"/><circle cx="232" cy="480" r="6" fill="#c9a24a"/>')
    if name=='sable':
        return torso+f'<path d="M150,352 L200,420 L250,352" fill="none" stroke="#d9b25a" stroke-width="5"/><path d="M160,350 Q200,400 240,350" fill="#2a2126"/><circle cx="126" cy="238" r="5" fill="#d9b25a"/>'
    return torso

def extras(name,c,expr):
    if name=='tobin':
        return f'<path d="M150,246 C156,284 180,302 200,304 C222,302 246,284 252,246 C244,276 224,292 200,292 C176,292 158,276 150,246Z" fill="{c["hair2"]}" opacity=".35"/>'
    if name=='oren':
        return (f'<path d="M144,248 C150,300 176,330 200,332 C226,330 252,300 258,248 C246,270 228,282 214,280 Q200,272 186,280 C172,282 154,270 144,248Z" fill="{c["hair"]}"/>'
            f'<circle cx="172" cy="212" r="20" fill="none" stroke="#c9a24a" stroke-width="3.5"/><circle cx="228" cy="212" r="20" fill="none" stroke="#c9a24a" stroke-width="3.5"/><path d="M192,210 Q200,204 208,210" fill="none" stroke="#c9a24a" stroke-width="3.5"/>')
    if name=='sable':
        return '<path d="M152,176 L166,206" stroke="#8a4a3e" stroke-width="3" stroke-linecap="round" opacity=".8"/>'
    return ''

def portrait(name,expr):
    c=C[name]
    s=c['style']
    face='M128,200 C128,128 162,110 200,110 C240,110 272,128 272,200 C272,254 244,298 200,302 C156,298 128,254 128,200Z'
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 70 400 450" width="400" height="450">
<defs>
<linearGradient id="sk" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c['skin']}"/><stop offset="1" stop-color="{c['shade']}"/></linearGradient>
<linearGradient id="cl" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c['cloth']}"/><stop offset="1" stop-color="{c['cloth2']}"/></linearGradient>
<filter id="bl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
</defs>
{back_hair(s,c)}
<path d="M168,262 L168,336 Q200,356 232,336 L232,262Z" fill="{c['shade']}"/>
{clothes(name,c)}
<ellipse cx="129" cy="214" rx="11" ry="19" fill="{c['shade']}"/><ellipse cx="271" cy="214" rx="11" ry="19" fill="{c['shade']}"/>
<path d="{face}" fill="url(#sk)"/>
<path d="M246,140 C272,170 274,240 246,286 C258,240 258,180 246,140Z" fill="{c['shade']}" opacity=".45"/>
<ellipse cx="164" cy="248" rx="16" ry="9" fill="#e27a6a" opacity=".28" filter="url(#bl)"/><ellipse cx="236" cy="248" rx="16" ry="9" fill="#e27a6a" opacity=".28" filter="url(#bl)"/>
{eyes(expr,c['iris'])}
{brows(expr,c['hair2'] if s!='bald' else '#9a958e', 7 if name=='oren' else 5)}
<path d="M198,222 Q193,240 199,245 Q205,247 209,243" fill="none" stroke="{c['shade']}" stroke-width="2.6" stroke-linecap="round"/>
{mouth(expr,c['lip'])}
{extras(name,c,expr)}
{front_hair(s,c)}
<path d="M134,170 C130,200 132,240 150,272" fill="none" stroke="#fff4e0" stroke-width="3" opacity=".35" stroke-linecap="round"/>
</svg>'''
    open(f'{OUT}/{name}-{expr}.svg','w').write(svg)

for n,e in [('mira','neutral'),('mira','smile'),('mira','thinking'),('mira','doubtful'),('mira','wary'),('tobin','grin'),('tobin','sour'),
            ('ilsa','smile'),('oren','neutral'),('wren','smile'),('aren','neutral'),('sable','wary')]:
    portrait(n,e)
print('ok')
