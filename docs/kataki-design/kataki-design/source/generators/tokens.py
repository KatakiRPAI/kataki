import json, sys
sys.path.insert(0,'.')
from lib import I
O='/mnt/user-data/outputs/kataki-design/design-system'
T = {
 "font": {
  "display": {"value": "Chewy, 'Segoe UI', system-ui, sans-serif", "use": "Sky big moments only: greeting name, page titles, First run headline, character names on portrait cards"},
  "ui": {"value": "Figtree, 'Segoe UI', system-ui, sans-serif", "use": "All interface text in both worlds"},
  "story": {"value": "Newsreader, Georgia, 'Times New Roman', serif", "use": "Story prose, story titles, title cards, time-skip lettering"},
  "mono": {"value": "'JetBrains Mono', Consolas, monospace", "use": "Backstage lens, model ids, hosts, JSON"}
 },
 "type": {
  "hero": {"size": 104, "line": 1, "font": "display", "use": "First run headline"},
  "title-xl": {"size": 76, "line": 1, "font": "story", "style": "italic", "use": "Time skip card"},
  "profile-name": {"size": 46, "line": 1, "font": "display"},
  "page-title": {"size": 44, "line": 1, "font": "display", "use": "Greeting name, Activity, Models"},
  "page-title-sm": {"size": 40, "line": 1, "font": "display", "use": "Chats"},
  "story-title": {"size": 34, "line": 1.05, "font": "story"},
  "h2": {"size": 22, "weight": 800, "font": "ui", "tracking": "-0.01em"},
  "h3": {"size": 16, "weight": 800, "font": "ui"},
  "story-body": {"size": 19, "line": 1.5, "font": "story", "use": "Every line in the conversation"},
  "body": {"size": 15, "line": 1.5, "font": "ui"},
  "body-sm": {"size": 14, "line": 1.4, "font": "ui"},
  "label": {"size": 13, "weight": 700, "font": "ui"},
  "caption": {"size": 12, "font": "ui"},
  "eyebrow": {"size": 11, "weight": 700, "tracking": "0.12em", "transform": "uppercase", "font": "ui"}
 },
 "sky": {
  "bg": {"value": "linear-gradient(165deg, #e4f0ff 0%, #c3dafc 38%, #aec4f7 70%, #b9b3f2 100%)"},
  "bg-solid": {"value": "#c3dafc"},
  "ink": {"value": "#14264d", "use": "Primary text, dark buttons"},
  "muted": {"value": "#4b5d82", "use": "Secondary text; 6:1 on white glass"},
  "accent": {"value": "#2f63f0", "use": "Links, active nav, focus, progress"},
  "accent-hover": {"value": "#1d44b8"},
  "glass": {"value": "rgba(255,255,255,.60)"},
  "glass-strong": {"value": "rgba(255,255,255,.82)", "use": "Overlays on art: name plates"},
  "glass-border": {"value": "rgba(255,255,255,.92)"},
  "glass-shadow": {"value": "0 14px 34px rgba(62,92,170,.14)"},
  "glass-blur": {"value": "16px"},
  "hairline": {"value": "rgba(20,38,77,.08)"},
  "success": {"value": "#23b26d"}, "success-ink": {"value": "#11804b"},
  "warning": {"value": "#f0a020"}, "warning-ink": {"value": "#9a6206"},
  "danger": {"value": "#c43c5c"}, "notify": {"value": "#ff4f7b"},
  "event-memory": {"value": "#e59a1e"}, "event-feeling": {"value": "#ff5d7e"},
  "event-belief": {"value": "#8a63f0"}, "event-time": {"value": "#2f9bd6"}
 },
 "candy": {
  "blue": ["#7fb0ff", "#3d63f2"], "pink": ["#ff9fb8", "#f0487a"], "purple": ["#c4a4ff", "#7c4ff0"],
  "green": ["#8fe0b0", "#22b26d"], "orange": ["#ffc98a", "#f08a2a"], "gold": ["#ffd58a", "#f0a020"]
 },
 "character-bg": {
  "mira": "linear-gradient(160deg,#c4ece4,#6fb7c9)", "tobin": "linear-gradient(160deg,#ffe3bf,#f2a468)",
  "ilsa": "linear-gradient(160deg,#f8d8ec,#c3a0ea)", "oren": "linear-gradient(160deg,#dbf2d4,#8cc79a)",
  "wren": "linear-gradient(160deg,#fff3bf,#f4c35a)", "aren": "linear-gradient(160deg,#d3e3ff,#7ea4f0)",
  "sable": "linear-gradient(160deg,#f6ccd2,#c77886)"
 },
 "scene": {
  "bg": {"value": "#0e0a08"},
  "ink": {"value": "#f4e9da", "use": "Story text"},
  "muted": {"value": "#cdbba4", "use": "Stamps, receipts text, secondary"},
  "action": {"value": "#dcc8ad", "use": "*actions* in italics"},
  "amber": {"value": "#f0b35a", "use": "Primary action, memory glow, 'will remember'"},
  "amber-ink": {"value": "#2a1606", "use": "Text on amber"},
  "lilac": {"value": "#cbb8ff", "use": "Belief callouts (doubts, believed, knows it's untrue)"},
  "rose": {"value": "#f4a595", "use": "Feeling callouts, distrust"},
  "glass": {"value": "rgba(26,19,15,.62)"},
  "glass-strong": {"value": "rgba(24,17,13,.84)", "use": "Composer"},
  "glass-border": {"value": "rgba(255,236,210,.16)"},
  "panel-scrim": {"value": "linear-gradient(90deg, rgba(14,10,8,0) 0%, rgba(14,10,8,.74) 11%, rgba(14,10,8,.9) 100%)"},
  "topbar-scrim": {"value": "linear-gradient(180deg, rgba(8,5,3,.72) 0%, rgba(8,5,3,0) 100%)"},
  "vignette": {"value": "radial-gradient(ellipse 70% 80% at 35% 45%, rgba(0,0,0,0) 50%, rgba(0,0,0,.55) 100%)"},
  "speaker": {"aren": "#a9c8ff", "mira": "#f2b870", "tobin": "#e8cc6a", "note": "Assign each character a speaker colour from a warm-light set; personas get cool blue"},
  "character-filter": {"value": "drop-shadow(0 30px 50px rgba(0,0,0,.55)) sepia(.14) saturate(1.05)", "use": "Warms character art into the lamplit place"},
  "softened-filter": {"value": "brightness(.62) blur(1.5px) sepia(.2)", "use": "Characters on stage who are not speaking"}
 },
 "backstage": {
  "bg": {"value": "#06203f"},
  "grid": {"value": "linear-gradient(rgba(140,195,255,.08) 1px, transparent 1px) 0 0/120px 120px, linear-gradient(90deg, rgba(140,195,255,.08) 1px, transparent 1px) 0 0/120px 120px, linear-gradient(rgba(140,195,255,.04) 1px, transparent 1px) 0 0/24px 24px, linear-gradient(90deg, rgba(140,195,255,.04) 1px, transparent 1px) 0 0/24px 24px"},
  "panel": {"value": "rgba(8,28,54,.86)"}, "line": {"value": "#8cc3ff"}, "border": {"value": "rgba(140,195,255,.28)"},
  "ink": {"value": "#e4f0ff"}, "muted": {"value": "#9db8d8"}, "tier": {"value": "#ffd08a"},
  "ok": {"value": "#a9e0c8"}, "error": {"value": "#f4a595"},
  "prompt-parts": {"rules": "#6aa8ff", "cards": "#8cc3ff", "memory": "#ffd08a", "examples": "#a9e0c8", "history": "#c7b8ff", "tail": "#f4a595"}
 },
 "memory": {
  "sharp": {"ring": "0 0 0 1.5px #f0b35a, 0 0 10px rgba(240,179,90,.75)", "opacity": 1, "use": "Filed and remembered clearly (lit receipt)"},
  "heard": {"ring": "0 0 0 1.5px rgba(255,255,255,.4)", "opacity": 0.85, "use": "Present when said; memory reader has not filed it yet (add pending dots)"},
  "hazy": {"ring": "0 0 0 1.5px rgba(240,179,90,.3)", "opacity": 0.42, "filter": "blur(.5px)", "use": "Only the gist remains"},
  "forgotten": {"use": "Avatar removed from the receipt row; backstage shows a dotted grey tier badge"},
  "absent": {"ring": "1.5px dashed rgba(255,236,210,.45)", "use": "Wasn't there: empty dashed circle with the initial"}
 },
 "radius": {"xs": 8, "sm": 12, "md": 14, "lg": 16, "xl": 20, "2xl": 22, "3xl": 24, "card": 28, "card-lg": 32, "hero": 34, "pill": 999},
 "space": {"1": 4, "2": 6, "3": 8, "4": 10, "5": 12, "6": 14, "7": 16, "8": 18, "9": 20, "10": 24, "11": 28, "12": 32, "13": 40},
 "size": {"hit-min": 44, "avatar-xs": 16, "avatar-sm": 20, "avatar-md": 24, "avatar-lg": 44, "avatar-xl": 62, "orb-rail": 54, "orb-card": 74, "rail-width": 92, "friend-card": [196, 268]},
 "layout": {
  "artboard": [1440, 900], "supported-width": [1280, 1920],
  "sky": {"rail": {"left": 20, "top": 20, "width": 92}, "content-left": 144, "content-right": 24},
  "scene": {"panel-left": 740, "text-column": {"left": 836, "width": 560}, "composer": {"left": 822, "right": 24, "bottom": 24}, "tray": {"left": 24, "top": 300, "width": 206}, "topbar-height": 88, "stage-character": {"one": {"x": 90, "y": 190, "w": 640}, "two": "speaker ~600w lit in front, other ~560w softened behind, offset left"}}
 },
 "motion": {
  "duration": {"quick": "120ms", "base": "200ms", "slow": "320ms", "scene": "600ms", "dive": "900ms", "time-skip": "1800ms"},
  "ease": {"standard": "cubic-bezier(.2,.8,.2,1)", "bounce": "cubic-bezier(.34,1.56,.64,1)", "drift": "cubic-bezier(.45,0,.2,1)"},
  "rules": ["Sky: things float, bounce and settle (bounce ease on hover/appear)", "Scene: crossfades and slow parallax only; controls fade out while reading", "No heavy 3D or large blurs animated per frame: the model often shares the GPU", "prefers-reduced-motion: stage becomes still images with crossfades; no bounce"]
 }
}

# ---- v3 Scene: full-height chat + widgets
T['scene'].pop('softened-filter',None); T['scene'].pop('panel-scrim',None)
T['scene']['character-filter']={"value":"drop-shadow(0 16px 22px rgba(0,0,0,.5)) sepia(.12) saturate(1.05)","use":"Portrait art in character widgets and cards"}
T['scene']['sage']={"value":"#a9dcb8","use":"Warmth and trust reactions"}
T['scene']['sky']={"value":"#9cc8ff","use":"Mood and thinking reactions"}
T['scene']['chat']={"value":"rgba(16,12,9,.80)","use":"The chat column's glass"}
T['scene']['widget']={"value":"rgba(26,19,15,.66)","use":"Widget glass"}
T['scene']['place-filter']={"value":"blur(3px) brightness(.55) saturate(.95)","use":"The place behind the chat"}
T['layout']['scene']={"chat":{"width":800,"top":16,"bottom":16,"radius":30,"measure":680},
 "corners":{"inset":24,"top":20},
 "widgets":{"width":272,"left":24,"right":24,"radius":24,"default":{"characters":"right column from y 84","clock":"bottom left, y 654","music":"bottom left, y 806"},"unpinned-dismiss-after":"6s"},
 "timeskip-card":{"width":560,"background":"#ffffff","ink":"#1f1a2b"}}
T['story-time']={"format":"12-hour in the UI, 24-hour on hover","date-order":["the story's own calendar","relative to a defining event","Day N / Year N, Day N"]}
T['backstage']['prompt-parts']={"rules":"#6aa8ff","cards":"#8cc3ff","mind":"#ffd08a","examples":"#a9e0c8","history":"#c7b8ff","tail":"#f4a595"}
T['backstage']['win']={"value":"#ffd08a","use":"The winning path in the Mind graph"}

json.dump(T, open(f'{O}/tokens.json','w'), indent=1, ensure_ascii=False)

# CSS variables
L=[":root {","  /* fonts */"]
for k,v in T['font'].items(): L.append(f"  --k-font-{k}: {v['value']};")
L.append("  /* sky */")
for k,v in T['sky'].items(): L.append(f"  --k-sky-{k}: {v['value']};")
for k,(a,b) in T['candy'].items(): L.append(f"  --k-candy-{k}-1: {a}; --k-candy-{k}-2: {b};")
for k,v in T['character-bg'].items(): L.append(f"  --k-char-{k}: {v};")
L.append("  /* scene */")
for k,v in T['scene'].items():
    if isinstance(v,dict) and 'value' in v: L.append(f"  --k-scene-{k}: {v['value']};")
for k,v in T['scene']['speaker'].items():
    if k!='note': L.append(f"  --k-speaker-{k}: {v};")
L.append("  /* backstage */")
for k,v in T['backstage'].items():
    if 'value' in v: L.append(f"  --k-bs-{k}: {v['value']};")
for k,v in T['backstage']['prompt-parts'].items(): L.append(f"  --k-bs-part-{k}: {v};")
L.append("  /* shape, space, motion */")
for k,v in T['radius'].items(): L.append(f"  --k-radius-{k}: {v}px;")
for k,v in T['space'].items(): L.append(f"  --k-space-{k}: {v}px;")
for k,v in T['motion']['duration'].items(): L.append(f"  --k-dur-{k}: {v};")
for k,v in T['motion']['ease'].items(): L.append(f"  --k-ease-{k}: {v};")
L.append("  --k-hit-min: 44px;")
L.append("}")
L.append("@media (prefers-reduced-motion: reduce) { :root { --k-dur-quick: 0ms; --k-dur-base: 0ms; --k-dur-slow: 0ms; --k-ease-bounce: linear; } }")
open(f'{O}/tokens.css','w').write("/* Kataki RPAI design tokens. Generated from tokens.json. */\n"+"\n".join(L)+"\n")

# icons
json.dump({k: f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{v}</svg>' for k,v in I.items()}, open(f'{O}/icons/icons.json','w'), indent=1)
sprite='<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n'+''.join(f'<symbol id="i-{k}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{v}</symbol>\n' for k,v in I.items())+'</svg>\n'
open(f'{O}/icons/sprite.svg','w').write(sprite)
print(len(I),'icons')
