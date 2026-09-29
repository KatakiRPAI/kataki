import json, sys, re, numpy as np
from PIL import Image
def lum(c):
    c=np.asarray(c,float)/255; c=np.where(c<=.03928,c/12.92,((c+.055)/1.055)**2.4); return c@np.array([.2126,.7152,.0722])
def parse(s):
    v=[float(x) for x in re.findall(r'[\d.]+',s)]; return v[:3],(v[3] if len(v)>3 else 1.0)
fails=0; total=0; occluded=0; inactive=0; report=[]
for base in sys.argv[1:]:
    items=json.load(open(f'/tmp/claude-0/audit_{base}.json')); im=np.asarray(Image.open(f'/tmp/claude-0/audit_bg_{base}.png').convert('RGB')).astype(float)
    H,W,_=im.shape
    for it in items:
        if it['hid'] or it['dis']: inactive+=1; continue
        if it.get('occ'): occluded+=1; continue
        rgb,a=parse(it['c']); a*=it['op']
        px=[]
        for x,y,w,h in it['rs']:
            x0,y0,x1,y1=int(max(0,x)),int(max(0,y)),int(min(W,x+w)),int(min(H,y+h))
            if x1>x0 and y1>y0: px.append(im[y0:y1,x0:x1].reshape(-1,3))
        if not px: continue
        px=np.concatenate(px)
        if len(px)>4000: px=px[np.random.default_rng(0).choice(len(px),4000,replace=False)]
        fg=a*np.array(rgb)+(1-a)*px
        lf=lum(fg); lb=lum(px); cr=(np.maximum(lf,lb)+.05)/(np.minimum(lf,lb)+.05)
        worst=np.percentile(cr,10)
        large = it['sz']>=24 or (it['sz']>=18.66 and it['wt']>=700)
        need=3.0 if large else 4.5
        total+=1
        if worst<need:
            fails+=1; report.append((base,round(float(worst),2),need,it['sz'],it['c'],round(it['op'],2),it['t']))
import json as _j
_j.dump({'runs':total,'fails':fails,'boards':len(sys.argv)-1,'occluded':occluded,'inactive':inactive},open('/tmp/claude-0/audit_summary.json','w'))
for r in sorted(report,key=lambda r:r[1]): print(*r,sep=' | ')
print(f'\n{total} text runs checked, {fails} below WCAG AA ({occluded} covered by a modal or overlay, {inactive} in inert/disabled regions: skipped as WCAG 1.4.3 allows)')
