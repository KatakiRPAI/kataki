// Renders canvas boards with the REAL fonts (local TTFs), and can audit text contrast.
const { chromium } = require('playwright');
const fs=require('fs'), path=require('path');
const lib=fs.readFileSync('lib.py','utf8'); const map={};
for (const m of lib.matchAll(/^([A-Z]+)='\/_blob\/(\w+)'/gm)) map[m[2]]=m[1];
map['249dcec7fe41970ab9704b8b690e72c3']='CLOUDS';
const U='/root/.claude/uploads/b8ee7179-a8bc-5225-a4b8-425032ace8b8/';
const F={LIV:U+'999ea114-image.png',MIKE:U+'30607efd-image.png',THEO:U+'7bb37e5d-image.png',JAE:U+'ec30ce9d-image.png',NICO:U+'e1910862-image.png',CAS:U+'27b0df1e-image.png',CAFE:U+'830d22bb-image.png',PALACE:U+'5f0f2c36-image.png',FLAT:U+'29d59bfe-image.png',DANI:path.resolve('assets/dani-placeholder.svg'),CLOUDS:path.resolve('assets/clouds.svg')};
const FD='/tmp/claude-0/f2/';
const FACES=`<style>
@font-face{font-family:'Baloo 2';src:url('file://${FD}Baloo2.ttf');font-weight:400 800}
@font-face{font-family:'Baloo Bhaijaan 2';src:url('file://${FD}BalooBhaijaan2.ttf');font-weight:400 800}
@font-face{font-family:Figtree;src:url('file://${FD}Figtree.ttf');font-weight:300 900}
@font-face{font-family:Figtree;src:url('file://${FD}Figtree-Italic.ttf');font-weight:300 900;font-style:italic}
@font-face{font-family:Newsreader;src:url('file://${FD}Newsreader.ttf');font-weight:200 800}
@font-face{font-family:Newsreader;src:url('file://${FD}Newsreader-Italic.ttf');font-weight:200 800;font-style:italic}
@font-face{font-family:'JetBrains Mono';src:url('file://${FD}JetBrainsMono.ttf');font-weight:100 800}
@font-face{font-family:'Noto Naskh Arabic';src:url('file://${FD}NotoNaskhArabic.ttf');font-weight:400 700}
@font-face{font-family:'IBM Plex Sans Arabic';src:url('file://${FD}IBMPlexSansArabic-Regular.ttf');font-weight:400}
@font-face{font-family:'IBM Plex Sans Arabic';src:url('file://${FD}IBMPlexSansArabic-Medium.ttf');font-weight:500}
@font-face{font-family:'IBM Plex Sans Arabic';src:url('file://${FD}IBMPlexSansArabic-SemiBold.ttf');font-weight:600}
@font-face{font-family:'IBM Plex Sans Arabic';src:url('file://${FD}IBMPlexSansArabic-Bold.ttf');font-weight:700 800}
</style>`;
const mode=process.argv[2]; const files=process.argv.slice(3);
(async()=>{const b=await chromium.launch({args:['--allow-file-access-from-files']});
for (const f of files){
 let h=fs.readFileSync('root/project/'+f,'utf8');
 h=h.replace(/\/_blob\/(\w+)/g,(_,id)=>'file://'+F[map[id]]);
 h=h.replace('<script src="./support.js"></script>','').replace(/<helmet>/,'').replace(/<\/helmet>/,'');
 h=h.replace(/<link[^>]+fonts\.googleapis[^>]+>/g,'').replace('</head>',FACES+'</head>');
 const m=h.match(/"width":(\d+),"height":(\d+)/);
 const tmp='/tmp/claude-0/pv2.html'; fs.writeFileSync(tmp,h);
 const p=await b.newPage({viewport:{width:+m[1],height:+m[2]}});
 await p.goto('file://'+tmp); await p.evaluate(()=>document.fonts.ready); await p.waitForTimeout(700);
 const base=f.replace('.dc.html','');
 if(mode==='shot'){ await p.screenshot({path:'pv2-'+base+'.png'}); }
 else {
  const items=await p.evaluate(()=>{const out=[];const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
   while((n=w.nextNode())){const tx=n.textContent.trim(); if(!tx) continue; const el=n.parentElement; const cs=getComputedStyle(el);
    if(cs.visibility==='hidden'||cs.display==='none') continue; let op=1,e=el,hid=false,dis=false;
    while(e){const s=getComputedStyle(e); op*=parseFloat(s.opacity); if(e.getAttribute&&e.getAttribute('aria-hidden')==='true') hid=true; if(e.dataset&&(e.dataset.disabled!==undefined||e.dataset.inactive!==undefined)) dis=true; if(e.hasAttribute&&e.hasAttribute('inert')) dis=true; e=e.parentElement}
    if(op<.05) continue; const r=document.createRange(); r.selectNodeContents(n); const rs=[...r.getClientRects()].filter(q=>q.width>1&&q.height>1).map(q=>[q.left,q.top,q.width,q.height]);
    if(!rs.length) continue;
    // occluded? sample the centre of each run: is the topmost element this text's element (or inside it)?
    let occ=0; for(const q of rs){const cx=q[0]+q[2]/2, cy=q[1]+q[3]/2; const top=document.elementFromPoint(cx,cy); if(top && !(top===el||el.contains(top)||top.contains(el))) occ++;}
    out.push({t:tx.slice(0,60),c:cs.color,op,sz:parseFloat(cs.fontSize),wt:parseInt(cs.fontWeight),rs,hid,dis,occ:occ===rs.length})}
   return out});
  await p.addStyleTag({content:'*{color:transparent!important;-webkit-text-fill-color:transparent!important;text-shadow:none!important;caret-color:transparent!important}'});
  await p.waitForTimeout(150); await p.screenshot({path:'/tmp/claude-0/audit_bg_'+base+'.png'});
  fs.writeFileSync('/tmp/claude-0/audit_'+base+'.json',JSON.stringify(items));
 }
 await p.close();}
await b.close();})();
