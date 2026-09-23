import re, glob, json, os
from lib import A
O='/mnt/user-data/outputs/kataki-design/screens/html'
key2file={'mira':'characters/mira-neutral','tobin':'characters/tobin-grin','tobin-sour':'characters/tobin-sour','ilsa':'characters/ilsa-smile','oren':'characters/oren-neutral','wren':'characters/wren-smile','aren':'characters/aren-neutral','sable':'characters/sable-wary','gull-dusk':'places/gull-dusk','gull-night':'places/gull-night','lighthouse':'places/lighthouse','market':'places/market','table-dusk':'places/table-dusk','table-night':'places/table-night','clouds':'places/clouds'}
for k in list(A):
    if k.startswith('mira-'): key2file[k]='characters/'+k
blob={v:'../../assets/'+key2file[k]+'.svg' for k,v in A.items()}
def newname(f): return 'Scene-OneToOne.html' if f=='Main.dc.html' else f.replace('.dc.html','.html')
canvas=json.load(open('root/project/canvas.json'))
for f in canvas['order']:
    h=open('root/project/'+f).read()
    h=h.replace('<script src="./support.js"></script>\n','')
    h=re.sub(r'<script type="text/x-dc".*?</script>\n','',h,flags=re.S)
    for t in ('<x-dc>\n','</x-dc>\n','<helmet>\n','</helmet>\n'): h=h.replace(t,'')
    h=h.replace('<link rel="preconnect"','<link rel="stylesheet" href="../../assets/fonts/fonts.css"><link rel="preconnect"',1)
    for b,p in blob.items(): h=h.replace(b,p)
    h=re.sub(r'href="([\w-]+)\.dc\.html"', lambda m: f'href="{newname(m.group(1)+".dc.html")}"', h)
    h=h.replace('<meta charset="utf-8">','<meta charset="utf-8">\n<!-- Kataki RPAI screen mockup. Static reference: layout, copy, states. See ../SCREENS.md and ../../design-system/. -->',1)
    assert '/_blob/' not in h, f
    open(f'{O}/{newname(f)}','w').write(h)
print(sorted(os.listdir(O)))
