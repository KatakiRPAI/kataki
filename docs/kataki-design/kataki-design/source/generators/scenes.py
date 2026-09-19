import random
OUT='assets'
def grain(op=.09):
    return f'<filter id="gr"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="1440" height="900" filter="url(#gr)" opacity="{op}"/>'

def gull(night=False):
    random.seed(4)
    if night:
        wall=('#1e1a24','#0e0b10'); sky=('#070b1c','#1a2548','#34406a'); lamp='#ffb866'; lampop=.55; harbourlight='#ffd58a'
    else:
        wall=('#4a2c1c','#1f120b'); sky=('#2b3a6e','#8a5a7e','#e39a5c'); lamp='#ffcf85'; lampop=.85; harbourlight='#ffe0a0'
    rain=''.join(f'<line x1="{x}" y1="{y}" x2="{x-6}" y2="{y+26}" stroke="#dfe8ff" stroke-width="1.4" opacity="{random.uniform(.15,.45):.2f}"/>' for x,y in [(random.uniform(0,1440),random.uniform(0,900)) for _ in range(420 if night else 260)])
    drops=''.join(f'<circle cx="{random.uniform(0,1440):.0f}" cy="{random.uniform(0,900):.0f}" r="{random.uniform(1.5,3.5):.1f}" fill="#eaf0ff" opacity=".35"/>' for _ in range(90))
    masts=''.join(f'<path d="M{x},{470} L{x},{470-h} M{x-30},{470-h*0.6} L{x+26},{470-h*0.6}" stroke="#0c0a14" stroke-width="3"/>' for x,h in [(170,150),(240,110),(330,170),(700,120),(760,160)])
    lights=''.join(f'<circle cx="{x}" cy="{y}" r="3" fill="{harbourlight}"/><circle cx="{x}" cy="{y}" r="12" fill="{harbourlight}" opacity=".18"/>' for x,y in [(150,455),(205,462),(290,450),(372,458),(690,452),(745,460),(800,448)])
    planks=''.join(f'<line x1="{x}" y1="0" x2="{x}" y2="600" stroke="#000" stroke-opacity=".22" stroke-width="2"/>' for x in range(0,1440,64))
    bottles=''
    cols=['#2f5a3a','#6a2a1e','#b88a3a','#3a4a6a','#7a5a2a','#2a3a2a']
    for row,y in enumerate((250,390)):
        x=930
        while x<1400:
            h=random.randint(60,95); w=random.randint(20,30); c=random.choice(cols)
            bottles+=f'<rect x="{x}" y="{y-h}" width="{w}" height="{h}" rx="6" fill="{c}" opacity=".9"/><rect x="{x+w/2-4}" y="{y-h-18}" width="8" height="20" fill="{c}"/><rect x="{x+4}" y="{y-h+8}" width="3" height="{h-20}" fill="#fff" opacity=".18"/>'
            x+=w+random.randint(10,24)
    def window(x,y,w,h,cid,cel=True):
        return (f'<clipPath id="{cid}"><path d="M{x},{y+h} L{x},{y+w/2} A{w/2},{w/2} 0 0 1 {x+w},{y+w/2} L{x+w},{y+h}Z"/></clipPath>'
            f'<g clip-path="url(#{cid})"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#sky)"/>'
            + ('' if not cel else f'<circle cx="{x+w*0.7}" cy="{y+90}" r="26" fill="#e8ecff" opacity=".85"/><circle cx="{x+w*0.7}" cy="{y+90}" r="60" fill="#e8ecff" opacity=".08"/>' if night else f'<circle cx="{x+w*0.3}" cy="{y+h-110}" r="44" fill="#ffd79a" opacity=".7"/>')
            + f'<rect x="{x}" y="{y+h-110}" width="{w}" height="110" fill="{"#0b1024" if night else "#3a3050"}"/>{masts}{lights}'
            f'<rect x="{x}" y="{y+h-60}" width="{w}" height="60" fill="{"#070a18" if night else "#2a2440"}" opacity=".7"/>{rain}{drops}</g>'
            f'<path d="M{x},{y+h} L{x},{y+w/2} A{w/2},{w/2} 0 0 1 {x+w},{y+w/2} L{x+w},{y+h}Z" fill="none" stroke="#150c07" stroke-width="16"/>'
            f'<line x1="{x+w/2}" y1="{y}" x2="{x+w/2}" y2="{y+h}" stroke="#150c07" stroke-width="10"/><line x1="{x}" y1="{y+h*0.55}" x2="{x+w}" y2="{y+h*0.55}" stroke="#150c07" stroke-width="10"/>'
            f'<rect x="{x-24}" y="{y+h}" width="{w+48}" height="18" fill="#2a170d"/>')
    lampg=lambda x,y,r: f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#lg)" opacity="{lampop}"/>'
    lampbody=lambda x,y: f'<line x1="{x}" y1="0" x2="{x}" y2="{y-26}" stroke="#120a06" stroke-width="3"/><path d="M{x-22},{y-26} L{x+22},{y-26} L{x+16},{y+18} L{x-16},{y+18}Z" fill="#2a1a10"/><rect x="{x-12}" y="{y-20}" width="24" height="32" rx="4" fill="{lamp}"/>'
    smoke=''.join(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="#f4e6d0" opacity=".07" filter="url(#sb)"/>' for x,y,rx,ry in [(520,330,260,60),(820,260,300,50),(380,210,200,40),(1100,340,240,50)])
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" width="1440" height="900" preserveAspectRatio="xMidYMid slice">
<defs>
<linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{wall[0]}"/><stop offset="1" stop-color="{wall[1]}"/></linearGradient>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{sky[0]}"/><stop offset=".55" stop-color="{sky[1]}"/><stop offset="1" stop-color="{sky[2]}"/></linearGradient>
<radialGradient id="lg"><stop offset="0" stop-color="{lamp}" stop-opacity=".9"/><stop offset=".35" stop-color="{lamp}" stop-opacity=".35"/><stop offset="1" stop-color="{lamp}" stop-opacity="0"/></radialGradient>
<radialGradient id="vig" cx=".42" cy=".45" r=".75"><stop offset=".45" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".78"/></radialGradient>
<filter id="sb" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="30"/></filter>
</defs>
<rect width="1440" height="900" fill="url(#wall)"/>
{planks}
{window(90,110,330,440,"w1")}
{window(560,170,220,360,"w2",False)}
<rect x="900" y="120" width="520" height="440" fill="#1a0f09" opacity=".75"/>
<rect x="900" y="250" width="520" height="12" fill="#3a2414"/><rect x="900" y="390" width="520" height="12" fill="#3a2414"/>
{bottles}
<rect x="0" y="600" width="1440" height="300" fill="#180d07"/>
<rect x="0" y="592" width="1440" height="14" fill="#3a2414"/>
<rect x="880" y="560" width="560" height="340" fill="#2a170d"/><rect x="870" y="548" width="580" height="22" fill="#4a2c18"/>
{lampbody(500,190)}{lampbody(1120,150)}
{lampg(500,200,420)}{lampg(1120,160,360)}
<rect width="1440" height="900" fill="{"#1a2a6a" if night else "#ff9a3a"}" opacity="{.18 if night else .08}"/>
{smoke}
<rect width="1440" height="900" fill="url(#vig)"/>
{grain()}
</svg>'''
    open(f'{OUT}/scene-gull-{"night" if night else "dusk"}.svg','w').write(svg)

def table(night=False):
    lamp='#ffb866' if night else '#ffcf85'
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 300" width="1440" height="300">
<defs><linearGradient id="t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{"#3a2a26" if night else "#6a3e22"}"/><stop offset="1" stop-color="#1a0e08"/></linearGradient>
<radialGradient id="c"><stop offset="0" stop-color="{lamp}" stop-opacity=".8"/><stop offset="1" stop-color="{lamp}" stop-opacity="0"/></radialGradient></defs>
<path d="M-40,300 L-40,150 Q720,90 1480,150 L1480,300Z" fill="url(#t)"/>
<path d="M-40,150 Q720,90 1480,150" fill="none" stroke="#c98a4a" stroke-opacity=".35" stroke-width="3"/>
<circle cx="640" cy="110" r="150" fill="url(#c)"/>
<rect x="628" y="90" width="24" height="60" rx="4" fill="#efe2c8"/><path d="M640,64 Q650,80 640,92 Q630,80 640,64Z" fill="{lamp}"/>
<g transform="rotate(-8 400 170)"><rect x="330" y="140" width="150" height="96" rx="4" fill="#ecdcb8"/><path d="M330,140 L405,196 L480,140" fill="none" stroke="#b9a37a" stroke-width="2"/><circle cx="405" cy="194" r="14" fill="#9e2a22"/><circle cx="405" cy="194" r="7" fill="#7a1c16"/></g>
<rect x="820" y="100" width="70" height="90" rx="10" fill="#6a4a2a"/><path d="M890,120 Q920,125 918,150 Q915,172 890,170" fill="none" stroke="#6a4a2a" stroke-width="10"/><ellipse cx="855" cy="102" rx="35" ry="8" fill="#e8d6a8"/>
</svg>'''
    open(f'{OUT}/scene-table-{"night" if night else "dusk"}.svg','w').write(svg)

def lighthouse():
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" width="1440" height="900" preserveAspectRatio="xMidYMid slice">
<defs><linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7f9fd6"/><stop offset=".5" stop-color="#f3b3a8"/><stop offset="1" stop-color="#ffd9a0"/></linearGradient>
<linearGradient id="sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e7a98f"/><stop offset="1" stop-color="#3a5b8a"/></linearGradient>
<radialGradient id="g"><stop offset="0" stop-color="#fff2c0"/><stop offset="1" stop-color="#fff2c0" stop-opacity="0"/></radialGradient></defs>
<rect width="1440" height="900" fill="url(#s)"/>
<circle cx="360" cy="560" r="90" fill="#ffe6b0"/><circle cx="360" cy="560" r="260" fill="url(#g)" opacity=".6"/>
<rect y="560" width="1440" height="340" fill="url(#sea)"/>
<path d="M0,560 L1440,560" stroke="#fff" stroke-opacity=".5"/>
<path d="M200,600 L520,600 M260,640 L460,640 M300,690 L420,690" stroke="#fff3d0" stroke-width="4" opacity=".6"/>
<path d="M700,900 L760,640 Q840,560 980,540 L1100,520 Q1300,540 1440,600 L1440,900Z" fill="#3f4a3a"/>
<path d="M760,640 Q840,570 980,552 L1100,532 Q1300,550 1440,610 L1440,640 Q1200,600 980,590 Q860,610 760,660Z" fill="#6f8a4a"/>
<rect x="1040" y="250" width="70" height="290" fill="#f4efe6"/><rect x="1040" y="310" width="70" height="36" fill="#c0463a"/><rect x="1040" y="410" width="70" height="36" fill="#c0463a"/>
<path d="M1030,250 L1120,250 L1110,236 L1040,236Z" fill="#2a2a30"/><rect x="1048" y="200" width="54" height="36" fill="#ffe6a0"/><path d="M1040,200 L1075,168 L1110,200Z" fill="#2a2a30"/>
<circle cx="1075" cy="218" r="140" fill="url(#g)" opacity=".7"/>
<path d="M1075,218 L1440,150 L1440,290Z" fill="#fff2c0" opacity=".25"/>
<path d="M60,180 Q140,150 220,178 Q300,150 380,182" fill="none" stroke="#fff" stroke-width="14" stroke-linecap="round" opacity=".5"/>
</svg>'''
    open(f'{OUT}/scene-lighthouse.svg','w').write(svg)

def market():
    random.seed(7)
    stalls=''
    cols=[('#e0533a','#fff3e0'),('#2f7ac0','#fff'),('#e8b23a','#fff6dc'),('#3a9a6a','#effff5')]
    for i,x in enumerate(range(40,1440,280)):
        a,b=cols[i%4]
        stripes=''.join(f'<path d="M{x+j*40},330 L{x+j*40+40},330 L{x+j*40+44},400 L{x+j*40-4},400Z" fill="{a if j%2==0 else b}"/>' for j in range(6))
        goods=''.join(f'<circle cx="{x+30+k*34}" cy="{505}" r="16" fill="{random.choice(["#e8543a","#f0a030","#8ac04a","#c0302a"])}"/>' for k in range(6))
        stalls+=f'<rect x="{x}" y="400" width="12" height="220" fill="#6a4a2a"/><rect x="{x+228}" y="400" width="12" height="220" fill="#6a4a2a"/>{stripes}<path d="M{x-4},400 {"".join(f"Q{x+j*40+20},{425} {x+j*40+40},400 " for j in range(6))}" fill="{a}"/><rect x="{x}" y="520" width="240" height="100" fill="#8a5a32"/>{goods}'
    bunting=''.join(f'<path d="M{x},120 L{x+30},120 L{x+15},160Z" fill="{["#e0533a","#2f7ac0","#e8b23a","#3a9a6a"][i%4]}"/>' for i,x in enumerate(range(0,1440,44)))
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" width="1440" height="900" preserveAspectRatio="xMidYMid slice">
<defs><linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6fb4ff"/><stop offset="1" stop-color="#d8ecff"/></linearGradient></defs>
<rect width="1440" height="900" fill="url(#s)"/>
<path d="M0,110 Q720,160 1440,110" fill="none" stroke="#5a4a3a" stroke-width="2"/>{bunting}
<rect y="300" width="1440" height="340" fill="#e8d8c0"/>
<g fill="#c9b49a">{''.join(f'<rect x="{x}" y="200" width="120" height="120"/>' for x in range(0,1440,180))}</g>
{stalls}
<rect y="620" width="1440" height="280" fill="#b8a48a"/>
{''.join(f'<ellipse cx="{x}" cy="{y}" rx="26" ry="10" fill="#a8947a"/>' for x in range(20,1440,60) for y in range(650,900,34))}
</svg>'''
    open(f'{OUT}/scene-market.svg','w').write(svg)

def clouds():
    random.seed(11)
    def cloud(cx,cy,s,op):
        parts=[(-1.2,.3,.55),(-.6,-.1,.75),(0,-.35,.9),(.7,-.05,.7),(1.25,.3,.5),(0,.35,.8)]
        g=''.join(f'<circle cx="{cx+dx*s*100:.0f}" cy="{cy+dy*s*100:.0f}" r="{r*s*100:.0f}" fill="url(#cg)"/>' for dx,dy,r in parts)
        return f'<g opacity="{op}" filter="url(#cb)">{g}</g>'
    cl=''.join(cloud(*a) for a in [(160,780,1.6,.95),(620,860,2.0,.95),(1180,800,1.8,.95),(1350,180,1.0,.7),(90,160,.9,.6),(760,120,.7,.5),(1000,420,.8,.45),(360,420,.6,.4)])
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" width="1440" height="900" preserveAspectRatio="xMidYMid slice">
<defs><radialGradient id="cg" cx=".45" cy=".35"><stop offset="0" stop-color="#ffffff"/><stop offset=".7" stop-color="#f3f7ff"/><stop offset="1" stop-color="#d6e2fb"/></radialGradient>
<filter id="cb" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="6"/></filter></defs>
{cl}</svg>'''
    open(f'{OUT}/clouds.svg','w').write(svg)

gull(False); gull(True); table(False); table(True); lighthouse(); market(); clouds()
print('ok')
