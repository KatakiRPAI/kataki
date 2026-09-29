import re, json, os
from lib import A, LIV, MIKE, THEO, JAE, NICO, CAS, CAFE, PALACE, FLAT, DANI
O='/mnt/user-data/outputs/kataki-design/screens/html'
blob={LIV:'characters/liv.png',MIKE:'characters/mike.png',THEO:'characters/theo.png',JAE:'characters/jae.png',
      NICO:'characters/nico.png',CAS:'characters/cas.png',DANI:'characters/dani.svg',
      CAFE:'places/halcyon-coffee.png',PALACE:'places/corvel-palace.png',FLAT:'places/flat-on-ardenne.png',
      A['clouds']:'places/clouds.svg'}
def newname(f): return 'Scene-OneToOne.html' if f=='Main.dc.html' else f.replace('.dc.html','.html')
canvas=json.load(open('root/project/canvas.json'))
for f in canvas['order']:
    h=open('root/project/'+f).read()
    h=h.replace('<script src="./support.js"></script>\n','')
    h=re.sub(r'<script type="text/x-dc".*?</script>\n','',h,flags=re.S)
    for t in ('<x-dc>\n','</x-dc>\n','<helmet>\n','</helmet>\n'): h=h.replace(t,'')
    h=h.replace('<link rel="preconnect"','<link rel="stylesheet" href="../../assets/fonts/fonts.css"><link rel="preconnect"',1)
    for b,p in blob.items(): h=h.replace(b,'../../assets/'+p)
    h=re.sub(r'href="([\w-]+)\.dc\.html"', lambda m: f'href="{newname(m.group(1)+".dc.html")}"', h)
    h=h.replace('<meta charset="utf-8">','<meta charset="utf-8">\n<!-- Kataki RPAI screen mockup. Static reference: layout, copy, states. See ../SCREENS.md, ../../design-system/ and ../../sample-world/. -->',1)
    assert '/_blob/' not in h, f
    open(f'{O}/{newname(f)}','w').write(h)
print(sorted(os.listdir(O)))
