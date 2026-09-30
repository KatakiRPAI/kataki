/* @ds-bundle: {"format": 4, "namespace": "Kataki", "components": [{"name": "Icon"}, {"name": "Avatar"}, {"name": "AvatarStack"}, {"name": "Panel"}, {"name": "Divider"}, {"name": "Sky"}, {"name": "Eyebrow"}, {"name": "StoryName"}, {"name": "Text"}, {"name": "Kbd"}, {"name": "Shortcut"}, {"name": "Button"}, {"name": "IconButton"}, {"name": "ButtonGroup"}, {"name": "TextLink"}, {"name": "Spinner"}, {"name": "Field"}, {"name": "TextField"}, {"name": "TextArea"}, {"name": "Select"}, {"name": "SearchField"}, {"name": "Checkbox"}, {"name": "RadioGroup"}, {"name": "Toggle"}, {"name": "Segmented"}, {"name": "Slider"}, {"name": "Chip"}, {"name": "ChoiceChips"}, {"name": "DropZone"}, {"name": "StepHeader"}, {"name": "Rail"}, {"name": "PersonaSwitch"}, {"name": "TopBar"}, {"name": "Tabs"}, {"name": "SideNav"}, {"name": "Breadcrumbs"}, {"name": "ShowMore"}, {"name": "Menu"}, {"name": "Tooltip"}, {"name": "Popover"}, {"name": "Dialog"}, {"name": "Sheet"}, {"name": "Toast"}, {"name": "CommandPalette"}, {"name": "Callout"}, {"name": "Alert"}, {"name": "EmptyState"}, {"name": "ProgressBar"}, {"name": "Skeleton"}, {"name": "StepList"}, {"name": "StatusLine"}, {"name": "StatePill"}, {"name": "Tag"}, {"name": "Badge"}, {"name": "Meter"}, {"name": "MemoryRow"}, {"name": "Stat"}, {"name": "StatRow"}, {"name": "KeyValue"}, {"name": "ListRow"}, {"name": "TimeStrip"}, {"name": "Stamp"}, {"name": "Changelog"}, {"name": "Bubble"}, {"name": "SecretCard"}, {"name": "Still"}, {"name": "ContinueHero"}, {"name": "EventCard"}, {"name": "CharacterCard"}, {"name": "AddCard"}, {"name": "PersonaCard"}, {"name": "StoryCard"}, {"name": "StoryPreview"}, {"name": "RelationshipCard"}, {"name": "PlaceCard"}, {"name": "PlotCard"}, {"name": "DoorCard"}, {"name": "SearchResult"}, {"name": "ThemeTile"}, {"name": "LanguageTile"}, {"name": "SettingsSection"}, {"name": "SettingsRow"}, {"name": "ConnectionRow"}, {"name": "JobRow"}, {"name": "FolderRow"}, {"name": "ShortcutRow"}, {"name": "SceneStage"}, {"name": "SceneButton"}, {"name": "SceneHeader"}, {"name": "BackstageToggle"}, {"name": "ChatPanel"}, {"name": "ChatLine"}, {"name": "LineTools"}, {"name": "TitleCard"}, {"name": "StoryNote"}, {"name": "RecallBox"}, {"name": "Reaction"}, {"name": "ModeChip"}, {"name": "ModeMenu"}, {"name": "Composer"}, {"name": "EditLine"}, {"name": "Widget"}, {"name": "CharacterWidget"}, {"name": "CharacterRowWidget"}, {"name": "ClockWidget"}, {"name": "MusicWidget"}, {"name": "TimeSkipCard"}, {"name": "BackstagePanel"}, {"name": "MindNode"}, {"name": "EngineRow"}, {"name": "PromptBar"}]} */
(function () {
  var React = window.React, h = React.createElement, useState = React.useState;
  var ICONS = {"home": "<path d=\"M3 11l9-8 9 8\"/><path d=\"M5 10v10h14V10\"/><path d=\"M10 20v-6h4v6\"/>", "users": "<circle cx=\"9\" cy=\"8\" r=\"4\"/><path d=\"M2 21c0-4 3-6 7-6s7 2 7 6\"/><path d=\"M16 3.6a4 4 0 010 8\"/><path d=\"M22 21c0-3-1.8-5-4.5-5.7\"/>", "chat": "<path d=\"M4 5h16v11H9l-5 4z\"/>", "map": "<path d=\"M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3z\"/><path d=\"M9 3v15\"/><path d=\"M15 6v15\"/>", "bell": "<path d=\"M6 16v-5a6 6 0 0112 0v5l2 2H4z\"/><path d=\"M10 20a2 2 0 004 0\"/>", "user": "<circle cx=\"12\" cy=\"8\" r=\"4\"/><path d=\"M4 21c0-4 4-6 8-6s8 2 8 6\"/>", "cog": "<circle cx=\"12\" cy=\"12\" r=\"3.1\"/><path d=\"M19.5 14.3a1.5 1.5 0 00.3 1.66l.05.05a1.9 1.9 0 11-2.69 2.69l-.05-.05a1.5 1.5 0 00-1.66-.3 1.5 1.5 0 00-.91 1.38V20a1.9 1.9 0 11-3.8 0v-.1a1.5 1.5 0 00-.98-1.38 1.5 1.5 0 00-1.66.3l-.05.05a1.9 1.9 0 11-2.69-2.69l.05-.05a1.5 1.5 0 00.3-1.66 1.5 1.5 0 00-1.38-.91H4a1.9 1.9 0 110-3.8h.1a1.5 1.5 0 001.38-.98 1.5 1.5 0 00-.3-1.66l-.05-.05a1.9 1.9 0 112.69-2.69l.05.05a1.5 1.5 0 001.66.3h.07a1.5 1.5 0 00.91-1.38V4a1.9 1.9 0 113.8 0v.1a1.5 1.5 0 00.91 1.38 1.5 1.5 0 001.66-.3l.05-.05a1.9 1.9 0 112.69 2.69l-.05.05a1.5 1.5 0 00-.3 1.66v.07a1.5 1.5 0 001.38.91H20a1.9 1.9 0 110 3.8h-.1a1.5 1.5 0 00-1.38.91z\"/>", "settings": "<circle cx=\"12\" cy=\"12\" r=\"3\"/><path d=\"M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1\"/>", "search": "<circle cx=\"11\" cy=\"11\" r=\"7\"/><path d=\"M20 20l-4-4\"/>", "plus": "<path d=\"M12 5v14M5 12h14\"/>", "heart": "<path d=\"M12 20s-7-4.5-7-10a4 4 0 017-2.6A4 4 0 0119 10c0 5.5-7 10-7 10z\"/>", "lock": "<rect x=\"5\" y=\"11\" width=\"14\" height=\"10\" rx=\"2\"/><path d=\"M8 11V8a4 4 0 018 0v3\"/>", "eye": "<path d=\"M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z\"/><circle cx=\"12\" cy=\"12\" r=\"3\"/>", "eyeoff": "<path d=\"M3 3l18 18\"/><path d=\"M10.6 5.1A10 10 0 0112 5c6 0 10 7 10 7a17 17 0 01-3.2 4M6.6 6.6C3.9 8.4 2 12 2 12s4 7 10 7a9.6 9.6 0 005.4-1.6\"/>", "cloud": "<path d=\"M7 18h10a4 4 0 000-8 6 6 0 00-11.5 1.5A3.5 3.5 0 007 18z\"/>", "sun": "<circle cx=\"12\" cy=\"12\" r=\"4\"/><path d=\"M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5\"/>", "moon": "<path d=\"M20 14A8 8 0 1110 4a6 6 0 0010 10z\"/>", "volume": "<path d=\"M4 9h4l5-4v14l-5-4H4z\"/><path d=\"M16.5 9a4 4 0 010 6\"/><path d=\"M19 6.5a8 8 0 010 11\"/>", "mute": "<path d=\"M4 9h4l5-4v14l-5-4H4z\"/><path d=\"M17 9l5 6M22 9l-5 6\"/>", "layers": "<path d=\"M12 3l9 5-9 5-9-5z\"/><path d=\"M3 13l9 5 9-5\"/>", "dots": "<circle cx=\"5\" cy=\"12\" r=\"1.3\"/><circle cx=\"12\" cy=\"12\" r=\"1.3\"/><circle cx=\"19\" cy=\"12\" r=\"1.3\"/>", "send": "<path d=\"M4 12l16-8-6 16-3-7z\"/><path d=\"M11 13l9-9\"/>", "stop": "<rect x=\"7\" y=\"7\" width=\"10\" height=\"10\" rx=\"1.5\"/>", "clock": "<circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M12 7v5l3 2\"/>", "spark": "<path d=\"M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z\"/><path d=\"M19 16l.7 1.8 1.8.7-1.8.7L19 21l-.7-1.8-1.8-.7 1.8-.7z\"/>", "arrow": "<path d=\"M5 12h14M13 6l6 6-6 6\"/>", "up": "<path d=\"M12 19V5M6 11l6-6 6 6\"/>", "left": "<path d=\"M15 6l-6 6 6 6\"/>", "right": "<path d=\"M9 6l6 6-6 6\"/>", "down": "<path d=\"M6 9l6 6 6-6\"/>", "check": "<path d=\"M5 12l5 5 9-10\"/>", "x": "<path d=\"M6 6l12 12M18 6L6 18\"/>", "key": "<circle cx=\"8\" cy=\"15\" r=\"4\"/><path d=\"M11 12l9-9M17 6l3 3\"/>", "server": "<rect x=\"4\" y=\"4\" width=\"16\" height=\"7\" rx=\"2\"/><rect x=\"4\" y=\"13\" width=\"16\" height=\"7\" rx=\"2\"/><path d=\"M8 7.5h.01M8 16.5h.01\"/>", "refresh": "<path d=\"M20 11a8 8 0 10-2.3 6\"/><path d=\"M20 4v7h-7\"/>", "pin": "<path d=\"M12 21s-7-6-7-11a7 7 0 0114 0c0 5-7 11-7 11z\"/><circle cx=\"12\" cy=\"10\" r=\"2.5\"/>", "pushpin": "<path d=\"M9 3h6l-1 6 4 4H6l4-4z\"/><path d=\"M12 13v8\"/>", "edit": "<path d=\"M4 20h4L19 9l-4-4L4 16z\"/><path d=\"M13.5 6.5l4 4\"/>", "ear": "<path d=\"M7 9a5 5 0 0110 0c0 3.5-3.5 4.5-3.5 8a3 3 0 01-5.5 1.6\"/><path d=\"M10 9a2 2 0 014 0\"/>", "thought": "<path d=\"M6 14a5 5 0 014-8 5 5 0 019 2.5A3.8 3.8 0 0117 15H8.5A3 3 0 016 14z\"/><circle cx=\"7\" cy=\"19\" r=\"1.3\"/><circle cx=\"4\" cy=\"21.5\" r=\".8\"/>", "hand": "<path d=\"M8 13V5.5a1.5 1.5 0 013 0V11\"/><path d=\"M11 11V4.5a1.5 1.5 0 013 0V11\"/><path d=\"M14 11V6a1.5 1.5 0 013 0v8a7 7 0 01-7 7h-.5a6 6 0 01-5-2.8L3 14.5a1.5 1.5 0 012.5-1.6L8 15\"/>", "quote": "<path d=\"M4 5h16v11H9l-5 4z\"/><path d=\"M8.5 9.5h7M8.5 12.5h4\"/>", "book": "<path d=\"M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2z\"/><path d=\"M4 19V5\"/>", "ff": "<path d=\"M4 6l7 6-7 6z\"/><path d=\"M13 6l7 6-7 6z\"/>", "quill": "<path d=\"M20 4C12 4 6 10 6 18\"/><path d=\"M6 18c6 0 12-4 14-14\"/><path d=\"M4 20l2-2\"/><path d=\"M10 14h5\"/>", "undo": "<path d=\"M9 14L4 9l5-5\"/><path d=\"M4 9h10a6 6 0 010 12h-3\"/>", "star": "<path d=\"M12 3l2.7 5.6 6.2.9-4.5 4.3 1.1 6.2L12 17l-5.5 3 1.1-6.2L3.1 9.5l6.2-.9z\"/>", "grid": "<rect x=\"4\" y=\"4\" width=\"7\" height=\"7\" rx=\"2\"/><rect x=\"13\" y=\"4\" width=\"7\" height=\"7\" rx=\"2\"/><rect x=\"4\" y=\"13\" width=\"7\" height=\"7\" rx=\"2\"/><rect x=\"13\" y=\"13\" width=\"7\" height=\"7\" rx=\"2\"/>", "film": "<rect x=\"3\" y=\"5\" width=\"18\" height=\"14\" rx=\"2\"/><path d=\"M7 5v14M17 5v14M3 9h4M3 15h4M17 9h4M17 15h4\"/>", "help": "<circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M9.5 9.5a2.5 2.5 0 015 0c0 2-2.5 2-2.5 4\"/><path d=\"M12 17h.01\"/>", "shield": "<path d=\"M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z\"/>", "cpu": "<rect x=\"6\" y=\"6\" width=\"12\" height=\"12\" rx=\"2\"/><rect x=\"9.5\" y=\"9.5\" width=\"5\" height=\"5\"/><path d=\"M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4\"/>", "globe": "<circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M3 12h18\"/><path d=\"M12 3a14 14 0 010 18a14 14 0 010-18\"/>", "drag": "<circle cx=\"9\" cy=\"6\" r=\"1.2\"/><circle cx=\"15\" cy=\"6\" r=\"1.2\"/><circle cx=\"9\" cy=\"12\" r=\"1.2\"/><circle cx=\"15\" cy=\"12\" r=\"1.2\"/><circle cx=\"9\" cy=\"18\" r=\"1.2\"/><circle cx=\"15\" cy=\"18\" r=\"1.2\"/>", "image": "<rect x=\"3\" y=\"4\" width=\"18\" height=\"16\" rx=\"2\"/><circle cx=\"9\" cy=\"10\" r=\"2\"/><path d=\"M21 16l-5-5-9 9\"/>", "feather": "<path d=\"M20 4C12 4 6 10 6 18\"/><path d=\"M6 18c6 0 12-4 14-14\"/>", "wind": "<path d=\"M3 8h11a3 3 0 10-3-3\"/><path d=\"M3 12h16a3 3 0 11-3 3\"/><path d=\"M3 16h7\"/>", "swap": "<path d=\"M7 7h13l-4-4\"/><path d=\"M17 17H4l4 4\"/>", "merge": "<circle cx=\"6\" cy=\"6\" r=\"2.5\"/><circle cx=\"6\" cy=\"18\" r=\"2.5\"/><circle cx=\"18\" cy=\"12\" r=\"2.5\"/><path d=\"M6 8.5v7M8 7l7.5 4M8 17l7.5-4\"/>", "alert": "<path d=\"M12 3l10 18H2z\"/><path d=\"M12 10v5M12 18h.01\"/>", "link": "<path d=\"M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1\"/><path d=\"M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1\"/>", "filter": "<path d=\"M4 5h16l-6 8v6l-4-2v-4z\"/>", "flame": "<path d=\"M12 21a6 6 0 006-6c0-4-3-6-4-10-1 3-3 4-4 6-1-1-1.5-2-1.5-3C6 10 6 12.5 6 15a6 6 0 006 6z\"/>", "map-pin": "<path d=\"M12 21s-7-6-7-11a7 7 0 0114 0c0 5-7 11-7 11z\"/><circle cx=\"12\" cy=\"10\" r=\"2.5\"/>", "crown": "<path d=\"M3 8l4.5 4L12 5l4.5 7L21 8l-2 11H5z\"/>", "download": "<path d=\"M12 4v11M7 10l5 5 5-5\"/><path d=\"M4 20h16\"/>", "mic": "<rect x=\"9\" y=\"3\" width=\"6\" height=\"11\" rx=\"3\"/><path d=\"M5 11a7 7 0 0014 0M12 18v3\"/>", "trash": "<path d=\"M4 7h16\"/><path d=\"M9 7V4.5h6V7\"/><path d=\"M6 7l1 13h10l1-13\"/><path d=\"M10 11v6M14 11v6\"/>", "play": "<path d=\"M8 5.5v13l10.5-6.5z\"/>", "pause": "<path d=\"M8.5 5.5v13M15.5 5.5v13\"/>"};
  var ART = {"liv": {"src": "/_blob/96a2aaee30862093be829e50a2c990f1", "focus": "52% 24%"}, "mike": {"src": "/_blob/6f5aebbb97b41f54aa01a3f3012914bd", "focus": "50% 26%"}, "theo": {"src": "/_blob/8e862a53371c28f445ba434a83dc8bcb", "focus": "50% 30%"}, "jae": {"src": "/_blob/144d4ec5739c7a0e510cce8b5678afce", "focus": "50% 32%"}, "nico": {"src": "/_blob/b8981e674d2a95f8783a001f593ed964", "focus": "52% 30%"}, "cas": {"src": "/_blob/f90f7b524561908082458b32e92b6659", "focus": "50% 20%"}, "dani": {"src": null, "focus": "50% 36%"}, "halcyon-coffee": {"src": "/_blob/9f5050bfba0340236731527f36905d6b"}, "corvel-palace": {"src": "/_blob/540fb2a248b8c2a6b2d6eed9e4342db6"}, "flat-on-ardenne": {"src": "/_blob/234321ae72ebe82dba5691941ebd0bba"}, "clouds": {"src": "/_blob/5d9f66a893448e0b9688ab76efe5a9ea"}};
  function cx() { return Array.prototype.filter.call(arguments, Boolean).join(' '); }
  function omit(p, keys) { var o = {}; for (var k in p) if (keys.indexOf(k) < 0 && k !== 'children') o[k] = p[k]; return o; }
  /* controlled when the value prop is given, otherwise it keeps its own state from the default */
  function useCtl(p, key, defKey, def, onKey) {
    var s = useState(p[defKey] !== undefined ? p[defKey] : def);
    var ctl = p[key] !== undefined;
    var val = ctl ? p[key] : s[0];
    function set(v) { if (!ctl) s[1](v); if (p[onKey || 'onChange']) p[onKey || 'onChange'](v); }
    return [val, set];
  }
  /* A portrait in any frame: object-fit cover, centred on `focus` ("x% y%"), zoomed `zoom` times about it.
     The clip keeps the zoomed picture inside its own box; `round` is the box's corner radius. */
  function framed(focus, zoom, round) {
    var z = zoom > 1 ? zoom : 1, at = focus || '50% 50%';
    if (z === 1) return { objectPosition: focus };
    var xy = at.split(' ').map(parseFloat), k = 1 - 1 / z;
    var r = round === undefined ? '' : ' round ' + (typeof round === 'number' ? round / z + 'px' : round);
    return { objectPosition: at, transform: 'scale(' + z + ')', transformOrigin: at,
      clipPath: 'inset(' + xy[1] * k + '% ' + (100 - xy[0]) * k + '% ' + (100 - xy[1]) * k + '% ' + xy[0] * k + '%' + r + ')' };
  }
  function artSrc(p, who) { var a = ART[who || p.who] || {}; return p.src || a.src; }

  /* ---------- foundations ---------- */
  function Icon(p) {
    var s = p.size || 18;
    var a = { className: cx('k-icon', p.className), width: s, height: s, viewBox: '0 0 24 24', fill: 'none',
      stroke: p.color || 'currentColor', strokeWidth: p.stroke || 1.8, strokeLinecap: 'round', strokeLinejoin: 'round',
      dangerouslySetInnerHTML: { __html: ICONS[p.name] || '' } };
    if (p.label) { a.role = 'img'; a['aria-label'] = p.label; } else { a['aria-hidden'] = 'true'; }
    if (p.flip) a.style = { transform: 'scaleX(-1)' };
    return h('svg', a);
  }
  function Avatar(p) {
    var a = ART[p.who] || {};
    var s = p.size || 36, src = p.src || a.src;
    return h('span', { className: cx('k-avatar', p.ring && 'k-avatar--ring-' + p.ring, p.away && 'k-avatar--away', p.className), style: { width: s, height: s } },
      src ? h('img', { src: src, alt: p.alt || '', style: framed(p.focus || a.focus, p.zoom, '50%') })
          : h('span', { className: 'k-avatar__initial', style: { fontSize: Math.round(s * 0.42) }, 'aria-hidden': 'true' }, (p.name || p.who || '?')[0].toUpperCase()),
      p.status ? h('span', { className: 'k-avatar__status k-avatar__status--' + p.status, 'aria-label': p.status }) : null);
  }
  function AvatarStack(p) {
    var people = p.people || [], max = p.max || 4, s = p.size || 30;
    var shown = people.slice(0, max), extra = people.length - shown.length;
    return h('span', { className: 'k-stack', 'aria-label': p.label },
      shown.map(function (x, i) { return h(Avatar, { key: i, who: x.who, src: x.src, name: x.name, focus: x.focus, zoom: x.zoom, alt: x.alt || x.name || '', size: s, className: 'k-stack__item' }); }),
      extra > 0 ? h('span', { className: 'k-stack__more', style: { width: s, height: s } }, '+' + extra) : null);
  }
  function Eyebrow(p) { return h('div', { className: cx('k-eyebrow', p.tone && 'k-eyebrow--' + p.tone, p.className) }, p.children); }
  function StoryName(p) {
    var T = p.as || 'span';
    return h(T, { className: cx('k-name', 'k-name--' + (p.size || 'card'), p.className) }, p.children);
  }
  function Text(p) {
    var T = p.as || (p.variant === 'prose' || p.variant === 'body' ? 'p' : 'span');
    return h(T, { className: cx('k-text', 'k-text--' + (p.variant || 'body'), p.tone && 'k-tone--' + p.tone, p.className) }, p.children);
  }
  function Kbd(p) { return h('kbd', { className: 'k-kbd' }, p.children); }
  function Shortcut(p) {
    var keys = p.keys || [];
    return h('span', { className: 'k-shortcut' }, keys.map(function (k, i) {
      return k === 'then' ? h('span', { key: i, className: 'k-shortcut__then' }, 'then') : h(Kbd, { key: i }, k);
    }));
  }
  function Divider(p) {
    if (p.label) return h('div', { className: 'k-divider k-divider--label', role: 'separator' }, h('span', null), h('b', null, p.label), h('span', null));
    return h('hr', { className: cx('k-divider', p.strong && 'k-divider--strong') });
  }
  function Panel(p) {
    var T = p.as || 'div';
    return h(T, { className: cx('k-panel', p.level && 'k-panel--' + p.level, p.flush && 'k-panel--flush', p.className), style: p.style, 'aria-label': p.label }, p.children);
  }
  function Sky(p) {
    var stars = [], seed = 11;
    function rnd() { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; }
    for (var i = 0; i < (p.stars == null ? 140 : p.stars); i++) stars.push(h('circle', { key: i, cx: (rnd() * 100).toFixed(2) + '%', cy: (rnd() * 100).toFixed(2) + '%', r: [0.7, 0.9, 1.1, 1.5][Math.floor(rnd() * 4)], opacity: (0.2 + rnd() * 0.6).toFixed(2) }));
    return h('div', { className: 'k-sky', 'aria-hidden': 'true' },
      h('svg', { className: 'k-sky__stars' }, stars),
      h('span', { className: 'k-sky__moon' }),
      p.clouds === false ? null : h('div', { className: 'k-sky__clouds' }, h('img', { src: p.cloudsSrc || (ART.clouds || {}).src, alt: '' })));
  }

  /* ---------- actions ---------- */
  function Spinner(p) {
    var s = p.size || 16;
    return h('span', { className: 'k-spinner', role: p.label ? 'status' : undefined, 'aria-label': p.label, style: { width: s, height: s } });
  }
  function Button(p) {
    var v = p.variant || 'secondary';
    var cls = cx('k-btn', 'k-btn--' + v, p.size === 'sm' && 'k-btn--sm', p.size === 'lg' && 'k-btn--lg', p.full && 'k-btn--full', p.loading && 'is-loading', p.className);
    var rest = omit(p, ['variant', 'icon', 'iconEnd', 'size', 'className', 'loading', 'full', 'href']);
    var inner = [p.loading ? h(Spinner, { key: 's', size: 15 }) : (p.icon ? h(Icon, { key: 'i', name: p.icon, size: 17, stroke: 1.9 }) : null),
      h('span', { key: 'l' }, p.children), p.iconEnd ? h(Icon, { key: 'e', name: p.iconEnd, size: 16, stroke: 1.9 }) : null];
    if (p.href) return h('a', Object.assign({ className: cls, href: p.href, 'aria-disabled': p.disabled ? 'true' : undefined }, rest), inner);
    return h('button', Object.assign({ type: 'button', className: cls, 'aria-busy': p.loading ? 'true' : undefined }, rest), inner);
  }
  function IconButton(p) {
    var cls = cx('k-iconbtn', 'k-iconbtn--' + (p.variant || 'plain'), p.size && 'k-iconbtn--' + p.size, p.className);
    var a = { className: cls, 'aria-label': p.label, title: p.label, onClick: p.onClick, disabled: p.disabled, 'aria-pressed': p.pressed === undefined ? undefined : String(!!p.pressed) };
    var ic = h(Icon, { name: p.icon, size: p.iconSize || (p.size === 'sm' ? 15 : p.size === 'lg' ? 20 : 18), stroke: 2 });
    return p.href ? h('a', Object.assign({ href: p.href }, a), ic) : h('button', Object.assign({ type: 'button' }, a), ic);
  }
  function ButtonGroup(p) { return h('div', { className: cx('k-btngroup', p.align && 'k-btngroup--' + p.align) }, p.children); }
  function TextLink(p) {
    return h('a', { className: cx('k-link', p.quiet && 'k-link--quiet'), href: p.href || '#' }, p.icon ? h(Icon, { name: p.icon, size: 15, stroke: 1.9 }) : null, p.children);
  }

  /* ---------- forms ---------- */
  var fid = 0;
  function useId(p) { var s = useState(function () { fid += 1; return 'k-f' + fid; }); return p.id || s[0]; }
  function Field(p) {
    return h('div', { className: cx('k-field', p.error && 'is-error', p.disabled && 'is-disabled') },
      p.label ? h('label', { className: 'k-field__label', htmlFor: p.htmlFor }, p.label,
        p.required ? h('span', { className: 'k-field__req' }, 'Required') : null,
        p.optional ? h('span', { className: 'k-field__opt' }, 'optional') : null) : null,
      p.children,
      p.error ? h('div', { className: 'k-field__error', role: 'alert' }, h(Icon, { name: 'alert', size: 14 }), p.error)
              : p.hint ? h('div', { className: 'k-field__hint' }, p.hint) : null);
  }
  function TextField(p) {
    var id = useId(p);
    var v = useCtl(p, 'value', 'defaultValue', '');
    var ctrl = h('div', { className: cx('k-input', p.story && 'k-input--story', p.icon && 'has-icon') },
      p.icon ? h(Icon, { name: p.icon, size: 16, stroke: 1.9 }) : null,
      h('input', { id: id, type: p.type || 'text', value: v[0], placeholder: p.placeholder, disabled: p.disabled, maxLength: p.max,
        'aria-invalid': p.error ? 'true' : undefined, onChange: function (e) { v[1](e.target.value); } }),
      p.max ? h('span', { className: 'k-input__count' }, String(v[0]).length + ' / ' + p.max) : null,
      p.suffix ? h('span', { className: 'k-input__suffix' }, p.suffix) : null);
    return h(Field, { label: p.label, hint: p.hint, error: p.error, required: p.required, optional: p.optional, disabled: p.disabled, htmlFor: id }, ctrl);
  }
  function TextArea(p) {
    var id = useId(p);
    var v = useCtl(p, 'value', 'defaultValue', '');
    return h(Field, { label: p.label, hint: p.hint, error: p.error, required: p.required, optional: p.optional, disabled: p.disabled, htmlFor: id },
      h('textarea', { id: id, className: cx('k-textarea', p.story !== false && 'k-input--story'), rows: p.rows || 4, value: v[0], placeholder: p.placeholder,
        disabled: p.disabled, 'aria-invalid': p.error ? 'true' : undefined, onChange: function (e) { v[1](e.target.value); } }));
  }
  function Select(p) {
    var id = useId(p);
    var v = useCtl(p, 'value', 'defaultValue', (p.options || [''])[0]);
    return h(Field, { label: p.label, hint: p.hint, error: p.error, optional: p.optional, disabled: p.disabled, htmlFor: id },
      h('div', { className: 'k-select' },
        p.icon ? h(Icon, { name: p.icon, size: 16, stroke: 1.9 }) : null,
        h('select', { id: id, value: v[0], disabled: p.disabled, onChange: function (e) { v[1](e.target.value); } },
          (p.options || []).map(function (o) { return h('option', { key: o, value: o }, o); })),
        h(Icon, { name: 'down', size: 15, stroke: 2, className: 'k-select__chev' })));
  }
  function SearchField(p) {
    return h('label', { className: cx('k-search', p.size === 'lg' && 'k-search--lg') }, h(Icon, { name: 'search', size: 16, stroke: 1.9 }),
      h('input', Object.assign({ className: 'k-search__input', placeholder: p.placeholder || 'Search everything', 'aria-label': p.label || 'Search' }, p.onChange ? { value: p.value || '', onChange: function (e) { p.onChange(e.target.value); } } : { defaultValue: p.value })),
      p.shortcut === false ? null : h('kbd', { className: 'k-kbd' }, p.shortcut || 'Ctrl K'));
  }
  function Checkbox(p) {
    var v = useCtl(p, 'checked', 'defaultChecked', false);
    return h('label', { className: cx('k-check', p.disabled && 'is-disabled') },
      h('input', { type: 'checkbox', checked: !!v[0], disabled: p.disabled, onChange: function (e) { v[1](e.target.checked); } }),
      h('span', { className: 'k-check__box', 'aria-hidden': 'true' }, h(Icon, { name: 'check', size: 13, stroke: 2.6 })),
      h('span', { className: 'k-check__text' }, h('span', { className: 'k-check__label' }, p.label), p.description ? h('span', { className: 'k-check__desc' }, p.description) : null));
  }
  function RadioGroup(p) {
    var name = useId(p);
    var v = useCtl(p, 'value', 'defaultValue', ((p.options || [])[0] || {}).value);
    return h('fieldset', { className: 'k-radios' },
      p.label ? h('legend', { className: 'k-field__label' }, p.label) : null,
      (p.options || []).map(function (o) {
        return h('label', { key: o.value, className: cx('k-radio', o.disabled && 'is-disabled') },
          h('input', { type: 'radio', name: name, value: o.value, checked: v[0] === o.value, disabled: o.disabled, onChange: function () { v[1](o.value); } }),
          h('span', { className: 'k-radio__dot', 'aria-hidden': 'true' }),
          h('span', { className: 'k-check__text' }, h('span', { className: 'k-check__label' }, o.label), o.description ? h('span', { className: 'k-check__desc' }, o.description) : null));
      }));
  }
  function Toggle(p) {
    var v = useCtl(p, 'on', 'defaultOn', false, 'onToggle');
    return h('button', { type: 'button', role: 'switch', className: 'k-toggle', 'aria-checked': v[0] ? 'true' : 'false', 'aria-label': p.label, disabled: p.disabled,
      onClick: function () { v[1](!v[0]); if (p.onClick) p.onClick(); } }, h('span', { className: 'k-toggle__knob' }));
  }
  function Segmented(p) {
    var v = useCtl(p, 'value', 'defaultValue', (p.options || [])[0]);
    return h('div', { className: cx('k-seg', p.size === 'sm' && 'k-seg--sm', p.tone === 'scene' && 'k-seg--scene'), role: 'group', 'aria-label': p.label },
      (p.options || []).map(function (o) {
        return h('button', { key: o, type: 'button', className: 'k-seg__opt', 'aria-pressed': o === v[0] ? 'true' : 'false', onClick: function () { v[1](o); } }, o);
      }));
  }
  function Slider(p) {
    var id = useId(p);
    var v = useCtl(p, 'value', 'defaultValue', 50);
    var min = p.min || 0, max = p.max === undefined ? 100 : p.max;
    var pct = ((v[0] - min) / (max - min)) * 100;
    return h('div', { className: 'k-slider' },
      p.label ? h('div', { className: 'k-slider__row' }, h('label', { htmlFor: id, className: 'k-field__label' }, p.label), h('span', { className: 'k-slider__value' }, p.valueText || v[0])) : null,
      h('input', { id: id, type: 'range', min: min, max: max, step: p.step || 1, value: v[0], disabled: p.disabled, style: { '--pct': pct + '%' },
        onChange: function (e) { v[1](Number(e.target.value)); } }),
      p.ends ? h('div', { className: 'k-slider__ends' }, h('span', null, p.ends[0]), h('span', null, p.ends[1])) : null);
  }
  function Chip(p) {
    var v = useCtl(p, 'pressed', 'defaultPressed', false, 'onPress');
    return h('span', { className: 'k-chipwrap' },
      h('button', { type: 'button', className: cx('k-chip', p.size === 'sm' && 'k-chip--sm'), 'aria-pressed': v[0] ? 'true' : 'false', disabled: p.disabled,
        onClick: function () { if (p.toggle !== false) v[1](!v[0]); if (p.onClick) p.onClick(); } },
        p.who ? h(Avatar, { who: p.who, src: p.src, size: 20 }) : null,
        p.icon ? h(Icon, { name: p.icon, size: 14, stroke: 2 }) : null,
        p.children,
        p.count != null ? h('span', { className: 'k-chip__count' }, p.count) : null,
        p.removable ? h('span', { className: 'k-chip__x', 'aria-hidden': 'true' }, h(Icon, { name: 'x', size: 12, stroke: 2.2 })) : null));
  }
  function ChoiceChips(p) {
    return h('div', { className: 'k-choices', role: 'group', 'aria-label': p.label },
      p.label ? h('span', { className: 'k-choices__label' }, p.label) : null,
      (p.options || []).map(function (o) { return h('button', { key: o, type: 'button', className: 'k-choice', onClick: function () { if (p.onPick) p.onPick(o); } }, o); }));
  }
  function DropZone(p) {
    return h('div', { className: cx('k-drop', p.active && 'is-active') },
      h('div', { className: 'k-drop__art', 'aria-hidden': 'true' }, h(Icon, { name: p.icon || 'image', size: 26, stroke: 1.6 }), h('span', null, p.empty || 'No portrait')),
      h('div', { className: 'k-drop__text' },
        h('div', { className: 'k-drop__title' }, p.title || 'Drop a file here'),
        p.description ? h('div', { className: 'k-drop__desc' }, p.description) : null,
        p.children ? h('div', { className: 'k-btngroup' }, p.children) : null));
  }
  function StepHeader(p) {
    return h('div', { className: 'k-stephead' }, h('span', { className: 'k-stephead__n' }, p.n), h('span', { className: 'k-stephead__t' }, p.title), p.optional ? h('span', { className: 'k-stephead__opt' }, 'optional') : null);
  }

  /* ---------- navigation ---------- */
  var NAV = [['home', 'Home'], ['chat', 'Stories'], ['users', 'Characters'], ['map', 'World'], ['user', 'You']];
  function Rail(p) {
    var active = p.active || 'Home', compact = !!p.compact, hrefs = p.hrefs || {};
    function go(label) { return function (e) { if (!hrefs[label]) e.preventDefault(); if (p.onNavigate) p.onNavigate(label); }; }
    function item(icon, label, quiet, dot) {
      return h('a', { key: label, href: hrefs[label] || '#', className: cx('k-rail__item', quiet && 'k-rail__item--quiet'), 'aria-current': label === active ? 'page' : undefined, title: compact ? label : undefined, onClick: go(label) },
        h(Icon, { name: icon, size: quiet ? 16 : (compact ? 20 : 19), stroke: quiet ? 1.8 : 1.9 }), h('span', { className: 'k-rail__label' }, label),
        dot ? h('span', { className: 'k-rail__dot', 'aria-label': dot }) : null);
    }
    return h('nav', { className: cx('k-rail', compact && 'k-rail--compact'), 'aria-label': 'Main', style: p.height ? { height: p.height } : undefined },
      h('div', { className: 'k-rail__mark' }, compact ? 'K' : 'Kataki'),
      h('div', { className: 'k-rail__list' }, NAV.map(function (n) { return item(n[0], n[1]); })),
      h('a', { href: hrefs['New character'] || '#', className: 'k-rail__new', onClick: go('New character') }, h(Icon, { name: 'plus', size: 17, stroke: 1.9 }), h('span', { className: 'k-rail__label' }, 'New character')),
      h('div', { className: 'k-rail__foot' },
        item('cog', 'Settings', true, p.settingsDot ? 'What’s new' : null), item('help', 'Feedback', true),
        item(p.theme === 'day' ? 'moon' : 'sun', p.theme === 'day' ? 'Night' : 'Day', true)));
  }
  function PersonaSwitch(p) {
    return h('button', { type: 'button', className: 'k-persona', 'aria-haspopup': 'menu', 'aria-expanded': p.open ? 'true' : 'false' },
      h(Avatar, { who: p.who || 'liv', src: p.src, size: 30, alt: '' }),
      h('span', { className: 'k-persona__text' }, h('b', null, p.name || 'Liv'), h('span', null, 'playing as')),
      h(Icon, { name: 'down', size: 14, stroke: 2 }));
  }
  function TopBar(p) {
    return h('header', { className: 'k-topbar' },
      p.back ? h(TextLink, { href: p.backHref, icon: 'left' }, p.back) : h(PersonaSwitch, { who: p.who, src: p.src, name: p.name }),
      p.children || h(SearchField, null));
  }
  function Tabs(p) {
    var tabs = p.tabs || [];
    var v = useCtl(p, 'value', 'defaultValue', tabs[0]);
    return h('div', { className: cx('k-tabs', p.size === 'sm' && 'k-tabs--sm'), role: 'tablist', 'aria-label': p.label },
      tabs.map(function (t) {
        var on = t === v[0];
        return h('button', { key: t, type: 'button', role: 'tab', className: 'k-tab', 'aria-selected': on ? 'true' : 'false', tabIndex: on ? 0 : -1, onClick: function () { v[1](t); } }, t,
          p.counts && p.counts[t] != null ? h('span', { className: 'k-tab__count' }, p.counts[t]) : null);
      }));
  }
  function SideNav(p) {
    var items = p.items || [];
    return h('nav', { className: 'k-sidenav', 'aria-label': p.label || 'Section' },
      items.map(function (it) {
        return h('a', { key: it.label, href: it.href || '#', className: 'k-sidenav__item', 'aria-current': it.label === p.active ? 'page' : undefined, onClick: it.href ? undefined : function (e) { e.preventDefault(); } },
          it.icon ? h(Icon, { name: it.icon, size: 16 }) : null, h('span', null, it.label), it.count != null ? h('span', { className: 'k-sidenav__count' }, it.count) : null);
      }),
      p.footer ? h('div', { className: 'k-sidenav__foot' }, p.footer) : null);
  }
  function Breadcrumbs(p) {
    var items = p.items || [];
    return h('nav', { className: 'k-crumbs', 'aria-label': 'Breadcrumb' }, items.map(function (it, i) {
      var last = i === items.length - 1;
      return h('span', { key: i, className: 'k-crumbs__item' }, last ? h('span', { 'aria-current': 'page' }, it) : h('a', { href: '#' }, it), last ? null : h(Icon, { name: 'right', size: 13, flip: false }));
    }));
  }
  function ShowMore(p) { return h('button', { type: 'button', className: 'k-showmore' }, p.children, h(Icon, { name: 'down', size: 14, stroke: 2 })); }

  /* ---------- menus and overlays ---------- */
  function Menu(p) {
    var items = p.items || [];
    return h('div', { className: cx('k-menu', p.scene && 'k-menu--scene'), role: 'menu', 'aria-label': p.title || p.label, style: p.width ? { width: p.width } : undefined },
      p.title ? h('div', { className: 'k-menu__title' }, p.title) : null,
      items.map(function (it, i) {
        if (it.divider) return h('div', { key: i, className: 'k-menu__divider', role: 'separator' });
        if (it.section) return h('div', { key: i, className: 'k-menu__section' }, it.section);
        return h('button', { key: i, type: 'button', role: it.checked !== undefined ? 'menuitemradio' : 'menuitem', 'aria-checked': it.checked === undefined ? undefined : String(!!it.checked),
          className: cx('k-menu__item', it.danger && 'is-danger', it.active && 'is-active'), disabled: it.disabled, onClick: it.onSelect },
          it.who ? h(Avatar, { who: it.who, src: it.src, size: 22 }) : (it.icon ? h(Icon, { name: it.icon, size: 16 }) : h('span', { className: 'k-menu__noicon' })),
          h('span', { className: 'k-menu__label' }, it.label, it.detail ? h('span', { className: 'k-menu__detail' }, it.detail) : null),
          it.meta ? h('span', { className: 'k-menu__meta' }, it.meta) : null,
          it.count != null ? h('span', { className: 'k-menu__meta' }, it.count) : null,
          it.shortcut ? h(Shortcut, { keys: it.shortcut }) : null,
          it.checked ? h(Icon, { name: 'check', size: 15, stroke: 2.2, className: 'k-menu__check' }) : null);
      }),
      p.footer ? h('div', { className: 'k-menu__foot' }, p.footer) : null);
  }
  function Tooltip(p) {
    return h('span', { className: cx('k-tipwrap', p.open && 'is-open') }, p.children,
      h('span', { role: 'tooltip', className: cx('k-tip', 'k-tip--' + (p.placement || 'top')) }, p.title ? h('b', null, p.title) : null, p.text));
  }
  function Popover(p) {
    return h('div', { className: 'k-popover', role: 'dialog', 'aria-label': p.title, style: p.width ? { width: p.width } : undefined },
      p.title ? h('div', { className: 'k-popover__head' }, h(StoryName, { size: 'row' }, p.title), p.onClose !== false ? h(IconButton, { icon: 'x', label: 'Close', size: 'sm', onClick: p.onClose || undefined }) : null) : null,
      p.description ? h('div', { className: 'k-popover__desc' }, p.description) : null,
      h('div', { className: 'k-popover__body' }, p.children),
      p.actions ? h('div', { className: 'k-popover__actions' }, p.actions) : null);
  }
  function Dialog(p) {
    var card = h('div', { className: cx('k-dialog', p.size && 'k-dialog--' + p.size), role: 'dialog', 'aria-modal': 'true', 'aria-label': p.title },
      h('div', { className: 'k-dialog__head' },
        p.icon ? h('span', { className: cx('k-dialog__icon', p.tone && 'k-dialog__icon--' + p.tone) }, h(Icon, { name: p.icon, size: 20 })) : null,
        h('div', { className: 'k-dialog__titles' }, h('h2', { className: 'k-dialog__title' }, p.title), p.description ? h('p', { className: 'k-dialog__desc' }, p.description) : null),
        h(IconButton, { icon: 'x', label: 'Close', size: 'sm', onClick: p.onClose })),
      p.children ? h('div', { className: 'k-dialog__body' }, p.children) : null,
      p.actions ? h('div', { className: 'k-dialog__actions' }, p.note ? h('span', { className: 'k-dialog__note' }, p.note) : null, h('div', { className: 'k-btngroup' }, p.actions)) : null);
    return p.backdrop ? h('div', { className: 'k-backdrop' }, card) : card;
  }
  function Sheet(p) {
    return h('aside', { className: cx('k-sheet', p.tone === 'scene' && 'k-sheet--scene'), role: 'dialog', 'aria-label': p.title },
      h('div', { className: 'k-sheet__head' }, h(StoryName, { size: 'title' }, p.title), h('div', { className: 'k-btngroup' }, p.headerAction, h(IconButton, { icon: 'x', label: 'Close', size: 'sm', onClick: p.onClose }))),
      h('div', { className: 'k-sheet__body' }, p.children));
  }
  function Toast(p) {
    return h('div', { className: cx('k-toast', p.tone && 'k-toast--' + p.tone), role: 'status' },
      h(Icon, { name: p.icon || 'check', size: 17 }), h('span', { className: 'k-toast__text' }, p.children),
      p.action ? h('button', { type: 'button', className: 'k-toast__action', onClick: p.onAction }, p.action) : null,
      h(IconButton, { icon: 'x', label: 'Dismiss', size: 'sm', onClick: p.onDismiss }));
  }
  function CommandPalette(p) {
    var groups = p.groups || [];
    return h('div', { className: 'k-palette', role: 'dialog', 'aria-label': 'Search and commands' },
      h('div', { className: 'k-palette__input' }, h(Icon, { name: 'search', size: 18 }), h('input', Object.assign({ placeholder: p.placeholder || 'Search, or type a command', 'aria-label': p.label || 'Search', autoFocus: !!p.onQuery, onKeyDown: p.onKeyDown, role: 'combobox', 'aria-expanded': 'true' }, p.onQuery ? { value: p.query || '', onChange: function (e) { p.onQuery(e.target.value); } } : { defaultValue: p.query })), h(Kbd, null, 'Esc')),
      h('div', { className: 'k-palette__list', role: 'listbox' }, groups.map(function (g) {
        return h('div', { key: g.title, className: 'k-palette__group' }, h('div', { className: 'k-palette__title' }, g.title),
          g.items.map(function (it, i) {
            return h('div', { key: i, role: 'option', id: it.id, 'aria-selected': it.active ? 'true' : 'false', className: cx('k-palette__item', it.active && 'is-active'), onClick: it.onSelect, onMouseEnter: it.onHover },
              it.who || it.src || it.name ? h(Avatar, { who: it.who, src: it.src, name: it.name, size: 22 }) : h(Icon, { name: it.icon || 'right', size: 16 }),
              h('span', { className: cx('k-palette__label', it.story && 'k-palette__label--story') }, it.label),
              it.meta ? h('span', { className: 'k-palette__meta' }, it.meta) : null,
              it.shortcut ? h(Shortcut, { keys: it.shortcut }) : null);
          }));
      })),
      h('div', { className: 'k-palette__foot' }, h(Shortcut, { keys: ['↑', '↓'] }), p.moveLabel || 'move', h(Kbd, null, 'Enter'), p.openLabel || 'open', h(Kbd, null, 'Tab'), p.filterLabel || 'filter'));
  }

  /* ---------- feedback ---------- */
  var TONE_ICON = { info: 'help', warm: 'spark', ok: 'check', bad: 'alert', privacy: 'shield' };
  function Callout(p) {
    var t = p.tone || 'info';
    return h('div', { className: cx('k-callout', 'k-callout--' + t), role: t === 'bad' ? 'alert' : undefined },
      h('span', { className: 'k-callout__icon' }, h(Icon, { name: p.icon || TONE_ICON[t] || 'help', size: 17 })),
      h('div', { className: 'k-callout__text' }, p.title ? h('b', { className: 'k-callout__title' }, p.title) : null, p.children ? h('span', null, p.children) : null),
      p.action ? h('div', { className: 'k-callout__action' }, p.action) : null);
  }
  function Alert(p) {
    return h('section', { className: 'k-alert', role: 'alert' },
      h('span', { className: 'k-alert__icon' }, h(Icon, { name: p.icon || 'alert', size: 22 })),
      h('div', { className: 'k-alert__body' },
        h('div', { className: 'k-alert__head' }, h('h2', { className: 'k-alert__title' }, p.title), p.code ? h('code', { className: 'k-alert__code' }, p.code) : null),
        h('div', { className: 'k-alert__text' }, p.children),
        p.actions ? h('div', { className: 'k-btngroup' }, p.actions) : null));
  }
  function EmptyState(p) {
    return h('div', { className: cx('k-empty', p.compact && 'k-empty--compact') },
      p.icon ? h('span', { className: 'k-empty__icon' }, h(Icon, { name: p.icon, size: 26, stroke: 1.6 })) : null,
      p.eyebrow ? h(Eyebrow, { tone: 'warm' }, p.eyebrow) : null,
      h('h2', { className: 'k-empty__title' }, p.title),
      p.children ? h('p', { className: 'k-empty__text' }, p.children) : null,
      p.actions ? h('div', { className: 'k-btngroup' }, p.actions) : null);
  }
  function ProgressBar(p) {
    var v = Math.max(0, Math.min(100, p.value || 0));
    return h('div', { className: 'k-progress' },
      p.label ? h('div', { className: 'k-progress__row' }, h('span', null, p.label), p.valueText ? h('span', { className: 'k-progress__val' }, p.valueText) : null) : null,
      h('div', { className: cx('k-progress__track', p.indeterminate && 'is-indeterminate'), role: 'progressbar', 'aria-valuenow': p.indeterminate ? undefined : v, 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-label': p.label },
        h('i', { style: { width: p.indeterminate ? '30%' : v + '%' } })));
  }
  function Skeleton(p) {
    if (p.lines) {
      var ls = []; for (var i = 0; i < p.lines; i++) ls.push(h('span', { key: i, className: 'k-skel', style: { width: i === p.lines - 1 ? '62%' : '100%', height: 12 } }));
      return h('div', { className: 'k-skel-lines', 'aria-hidden': 'true' }, ls);
    }
    return h('span', { className: 'k-skel', 'aria-hidden': 'true', style: { width: p.width || '100%', height: p.height || 16, borderRadius: p.round ? '50%' : (p.radius || 6) } });
  }
  function StepList(p) {
    var ic = { done: 'check', doing: 'refresh', wait: 'clock', failed: 'alert' };
    return h('ol', { className: 'k-steps' }, (p.steps || []).map(function (s, i) {
      return h('li', { key: i, className: 'k-steps__item is-' + (s.state || 'wait') }, h(Icon, { name: ic[s.state || 'wait'], size: 16, stroke: 2 }),
        h('span', { className: 'k-steps__label' }, s.label), s.detail ? h('span', { className: 'k-steps__detail' }, s.detail) : null);
    }));
  }
  function StatusLine(p) {
    return h('div', { className: cx('k-statusline', 'k-statusline--' + (p.tone || 'ok')), role: 'status' },
      h('span', { className: 'k-statusline__dot' }), h('div', { className: 'k-statusline__text' }, h('b', null, p.title), p.children ? h('span', null, p.children) : null),
      p.action ? h('div', null, p.action) : null);
  }

  /* ---------- data display ---------- */
  function StatePill(p) {
    return h('span', { className: cx('k-pill', 'k-pill--' + (p.tone || 'muted')) }, p.icon ? h(Icon, { name: p.icon, size: 13, stroke: 2 }) : null, p.children);
  }
  function Tag(p) { return h('span', { className: cx('k-tag', p.tone && 'k-tag--' + p.tone) }, p.children); }
  function Badge(p) {
    if (p.dot) return h('span', { className: cx('k-badge-dot', 'k-badge-dot--' + (p.tone || 'warm')), 'aria-label': p.label || 'New' });
    return h('span', { className: cx('k-badge', 'k-badge--' + (p.tone || 'accent')) }, p.children != null ? p.children : p.count);
  }
  function Meter(p) {
    var v = Math.max(0, Math.min(100, p.value || 0));
    return h('div', { className: 'k-meter' },
      h('div', { className: 'k-meter__row' }, h('span', { className: 'k-meter__label' }, p.label), h('span', { className: cx('k-meter__value', p.word && 'k-meter__value--word', p.word && 'k-tone--' + (p.tone || 'muted')) }, p.word || v)),
      h('div', { className: 'k-meter__track', role: 'meter', 'aria-valuenow': v, 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-label': p.label || p.word },
        h('i', { className: 'k-meter__fill k-meter__fill--' + (p.tone || 'accent'), style: { width: v + '%' } })));
  }
  function MemoryRow(p) {
    var v = Math.max(0, Math.min(100, p.value || 0));
    return h('div', { className: 'k-memrow' },
      h('div', { className: 'k-memrow__top' }, h('span', { className: 'k-memrow__text' }, p.children), h('span', { className: 'k-memrow__word k-tone--' + (p.tone || 'muted') }, p.word)),
      h('div', { className: 'k-meter__track', role: 'meter', 'aria-valuenow': v, 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-label': p.word },
        h('i', { className: 'k-meter__fill k-meter__fill--' + (p.tone || 'muted'), style: { width: v + '%' } })),
      p.meta ? h('div', { className: 'k-memrow__meta' }, p.meta) : null);
  }
  function Stat(p) { return h('span', { className: 'k-stat' }, h('b', null, p.value), h('span', null, p.label)); }
  function StatRow(p) { return h('div', { className: 'k-statrow' }, (p.stats || []).map(function (s, i) { return h(Stat, { key: i, value: s[0], label: s[1] }); }), p.children); }
  function KeyValue(p) {
    return h('div', { className: 'k-kv' }, p.icon ? h(Icon, { name: p.icon, size: 15 }) : h('span'), h('span', { className: 'k-kv__k' }, p.label), h('span', { className: 'k-kv__v' }, p.children));
  }
  function ListRow(p) {
    var T = p.href ? 'a' : 'div';
    return h(T, { className: cx('k-listrow', p.href && 'is-link'), href: p.href },
      p.who || p.src || p.name ? h(Avatar, { who: p.who, src: p.src, name: p.name, size: p.avatarSize || 36 }) : (p.icon ? h('span', { className: 'k-listrow__icon' }, h(Icon, { name: p.icon, size: 17 })) : null),
      h('div', { className: 'k-listrow__main' }, p.story ? h(StoryName, { size: 'row' }, p.title) : h('div', { className: 'k-listrow__title' }, p.title), p.subtitle ? h('div', { className: 'k-listrow__sub' }, p.subtitle) : null),
      p.meta ? h('span', { className: 'k-listrow__meta' }, p.meta) : null, p.children);
  }
  var TIMES = [['dawn', '#c9a6c6'], ['day', '#9fc4e8'], ['dusk', '#e0a06a'], ['night', '#5b6ba8']];
  function TimeStrip(p) {
    return h('div', { className: 'k-timestrip', role: 'group', 'aria-label': 'Time of day' }, TIMES.map(function (t) {
      var on = t[0] === p.value;
      return h('span', { key: t[0], className: cx('k-timestrip__seg', on && 'is-on', 'k-timestrip__seg--' + t[0]), 'aria-current': on ? 'true' : undefined }, t[0]);
    }));
  }
  function Stamp(p) {
    return h(Tooltip, { title: p.exact, text: p.detail, open: p.open, placement: p.placement }, h('span', { className: cx('k-stamp', p.tone === 'scene' && 'k-stamp--scene'), tabIndex: 0 }, p.children));
  }
  function Changelog(p) {
    return h('ol', { className: 'k-changelog' }, (p.items || []).map(function (it, i) {
      return h('li', { key: i }, h('div', { className: 'k-changelog__ver' }, h('code', null, it.version), h('span', null, it.when)), h('p', null, it.text));
    }));
  }
  function Bubble(p) { return h('div', { className: cx('k-bubble', p.indent && 'k-bubble--indent') }, renderProse(p.children)); }
  function SecretCard(p) {
    return h('section', { className: 'k-secret', 'aria-label': 'Secret' },
      h('div', { className: 'k-secret__head' }, h(Icon, { name: 'lock', size: 17, color: 'var(--warm)' }), h(Eyebrow, { tone: 'warm' }, p.title || ('Only ' + (p.name || 'they') + ' knows this'))),
      h('p', { className: 'k-secret__text' }, p.children));
  }

  /* ---------- the story world: cards ---------- */
  function Still(p) {
    var a = ART[p.place] || {};
    return h('figure', { className: 'k-still', style: { height: p.height || 240 } },
      p.src || a.src ? h('img', { src: p.src || a.src, alt: p.alt || '', style: { objectPosition: p.position || '50% 45%' } }) : null,
      p.caption ? h('figcaption', { className: 'k-still__caption' }, p.caption) : null);
  }
  function EventCard(p) {
    return h('article', { className: 'k-event' },
      h('div', { className: 'k-event__head' }, h(Avatar, { who: p.who, size: 24, src: p.avatarSrc }), h('b', null, p.name), h('span', { className: 'k-event__type k-event__type--' + (p.tone || 'warm') }, p.event)),
      h('p', { className: 'k-event__memory' }, p.memory),
      h('div', { className: 'k-event__meta' }, p.meta));
  }
  function CharacterCard(p) {
    var a = ART[p.who] || {}, src = p.src || a.src;
    return h('article', { className: cx('k-char', p.featured && 'k-char--featured', p.hover && 'is-hover', p.variant === 'list' && 'k-char--list') },
      h('div', { className: 'k-char__art' },
        src ? h('img', { src: src, alt: p.alt || (p.name + ', portrait'), style: framed(p.focus || a.focus, p.zoom) })
            : h('div', { className: 'k-char__noface' }, h('span', { 'aria-hidden': 'true' }, (p.name || '?')[0]), h('small', null, 'no portrait yet')),
        p.badge ? h('span', { className: cx('k-char__badge', p.badgeTone === 'warm' && 'k-char__badge--warm') }, p.badge) : null,
        p.hover || p.continueHref || p.onMore ? h('div', { className: 'k-char__quick' }, p.continueHref || p.hover ? h(Button, { variant: 'primary', size: 'sm', href: p.continueHref }, p.continueLabel || 'Continue') : h('span'), h(IconButton, { icon: 'dots', label: 'More for ' + p.name, size: 'sm', variant: 'glass', onClick: p.onMore })) : null),
      h('div', { className: 'k-char__body' },
        h(StoryName, { size: p.featured ? 'lg' : 'card' }, p.name),
        p.line ? h('div', { className: 'k-char__line' }, p.line) : null,
        h('div', { className: 'k-char__foot' }, h('span', { className: 'k-meta' }, p.when), p.stories != null ? h('span', { className: 'k-meta' }, p.stories + (p.stories === 1 ? ' story' : ' stories')) : null)));
  }
  function AddCard(p) {
    return h(p.onClick ? 'button' : 'a', { href: p.onClick ? undefined : p.href || '#', type: p.onClick ? 'button' : undefined, onClick: p.onClick, className: cx('k-addcard', p.wide && 'k-addcard--wide') }, h(Icon, { name: p.icon || 'plus', size: 24, stroke: 1.8 }), h('span', null, p.children || 'Add'), p.sub ? h('small', null, p.sub) : null);
  }
  function PersonaCard(p) {
    return h('article', { className: cx('k-persona-card', p.selected && 'is-selected') },
      p.who || p.src ? h(Avatar, { who: p.who, src: p.src, focus: p.focus, zoom: p.zoom, size: 40 }) : h('span', { className: 'k-persona-card__icon' }, h(Icon, { name: p.icon || 'feather', size: 18 })),
      h('div', { className: 'k-persona-card__text' }, h('div', { className: 'k-persona-card__name' }, p.name, p.isDefault ? h(Tag, { tone: 'accent' }, 'Default') : null), h('div', { className: 'k-persona-card__line' }, p.line)));
  }
  function StoryCard(p) {
    var faces = p.people && p.people.length ? h(AvatarStack, { people: p.people, size: 32 }) : h(Avatar, { who: p.who, size: 38, src: p.avatarSrc });
    return h('article', { className: cx('k-story', p.selected && 'k-story--selected', p.compact && 'k-story--compact') },
      h('div', { className: 'k-story__head' }, faces,
        h('div', { className: 'k-story__titles' }, h(StoryName, { size: 'row' }, p.title), h('div', { className: 'k-story__book' }, p.book)),
        p.pinned ? h('span', { className: 'k-story__pin', 'aria-label': 'Pinned' }, h(Icon, { name: 'pushpin', size: 15, color: 'var(--warm)' })) : null),
      h('p', { className: 'k-story__quote' }, p.quote),
      h('div', { className: 'k-story__foot' }, h('span', { className: 'k-story__when' }, p.when), p.storyTime ? h('span', { className: 'k-story__time' }, p.storyTime) : null));
  }
  function ContinueHero(p) {
    function act(label, variant, href, fn) { return h(Button, { variant: variant, size: 'lg', href: href, onClick: fn }, label); }
    return h('section', { className: 'k-hero', 'aria-label': 'Continue' },
      h('div', { className: 'k-hero__text' },
        h(Eyebrow, { tone: 'mid' }, 'Continue · ' + p.book),
        h(StoryName, { size: 'hero', as: 'h1' }, p.title),
        h('blockquote', { className: 'k-hero__quote' }, p.lastLine),
        h('div', { className: 'k-hero__state' }, h(Avatar, { who: p.who, size: 26, src: p.avatarSrc, name: p.avatarName }), p.mood ? h(StatePill, { tone: 'warm' }, p.mood) : null, h('span', { className: 'k-hero__stats' }, p.stats)),
        h('div', { className: 'k-hero__actions' }, act('Continue', 'primary', p.continueHref, p.onContinue), act('New story', 'secondary', p.newHref)),
        h('div', { className: 'k-meta' }, p.where)),
      h(Still, { place: p.place, src: p.placeSrc, caption: p.caption, height: 332, alt: p.placeAlt }));
  }
  function StoryPreview(p) {
    return h('section', { className: 'k-preview', 'aria-label': p.title },
      h('div', { className: 'k-preview__art' }, p.placeSrc || (ART[p.place] || {}).src ? h('img', { src: p.placeSrc || (ART[p.place] || {}).src, alt: p.placeAlt || '' }) : null),
      h('div', { className: 'k-preview__body' },
        h(StoryName, { size: 'title', as: 'h2' }, p.title),
        h('div', { className: 'k-meta' }, p.meta),
        h('div', { className: 'k-btngroup' }, h(Button, { variant: 'primary', href: p.continueHref }, 'Continue'), h('span', { className: 'k-meta' }, p.lastPlayed)),
        h(Divider, null), h(Eyebrow, null, 'Who is here'),
        (p.cast || []).map(function (c, i) {
          return h('div', { key: i, className: 'k-preview__cast' }, h(Avatar, { who: c.who, src: c.src, name: c.name, size: 36 }),
            h('div', { className: 'k-preview__who' }, h('b', null, c.name), h('span', null, c.memories)), c.pill ? h(StatePill, { tone: c.tone || 'muted' }, c.pill) : null);
        }),
        p.children));
  }
  function RelationshipCard(p) {
    return h('div', { className: 'k-relcard' }, h(Avatar, { who: p.who, src: p.src, size: 38 }), h('div', null, h(StoryName, { size: 'row' }, p.name), h('div', { className: 'k-meta' }, p.how)));
  }
  function PlaceCard(p) {
    return h('article', { className: cx('k-place', p.selected && 'is-selected') },
      h('div', { className: 'k-place__art' }, p.src || (ART[p.place] || {}).src ? h('img', { src: p.src || (ART[p.place] || {}).src, alt: p.alt || '' }) : null, h('div', { className: 'k-place__name' }, h(StoryName, { size: 'card' }, p.name))),
      h('div', { className: 'k-place__body' },
        p.blurb ? h('p', { className: 'k-place__blurb' }, p.blurb) : null,
        p.time ? h(TimeStrip, { value: p.time }) : null,
        h('div', { className: 'k-place__foot' }, p.people ? h(AvatarStack, { people: p.people, size: 22 }) : null, h('span', { className: 'k-meta' }, p.links))));
  }
  function PlotCard(p) {
    return h('article', { className: 'k-plot' },
      h(Icon, { name: 'quote', size: 18, color: 'var(--warm)' }),
      h('p', { className: 'k-plot__quote' }, p.quote),
      h('p', { className: 'k-plot__opening' }, p.opening),
      h('div', { className: 'k-place__foot' }, p.people ? h(AvatarStack, { people: p.people, size: 22 }) : null, h('span', { className: 'k-meta' }, p.book)));
  }
  function DoorCard(p) {
    return h('article', { className: cx('k-door', p.recommended && 'is-recommended') },
      h('span', { className: 'k-door__icon' }, h(Icon, { name: p.icon || 'flame', size: 19 })),
      h(Eyebrow, { tone: p.recommended ? 'accent' : undefined }, p.eyebrow),
      h('h3', { className: 'k-door__title' }, p.title),
      h('p', { className: 'k-door__body' }, p.children),
      p.actions ? h('div', { className: 'k-btngroup' }, p.actions) : null);
  }
  function SearchResult(p) {
    return h('article', { className: 'k-result' },
      h('span', { className: 'k-result__icon' }, h(Icon, { name: p.icon || 'chat', size: 17 })),
      h('div', { className: 'k-result__main' },
        h('div', { className: cx('k-result__title', p.story && 'k-result__title--story') }, p.title),
        p.meta ? h('div', { className: 'k-result__meta' }, p.meta) : null,
        p.excerpt ? h('div', { className: 'k-result__excerpt' }, p.excerpt) : null),
      p.who ? h(Avatar, { who: p.who, src: p.src, size: 28 }) : null,
      h(Button, { size: 'sm' }, p.action || 'Open'));
  }
  function ThemeTile(p) {
    return h('button', { type: 'button', className: cx('k-themetile', p.selected && 'is-selected'), 'aria-pressed': p.selected ? 'true' : 'false', onClick: p.onClick },
      h('span', { className: 'k-themetile__swatch k-themetile__swatch--' + (p.variant || 'night') }),
      h('span', { className: 'k-themetile__name' }, p.name), p.note ? h('span', { className: 'k-themetile__note' }, p.note) : null);
  }
  function LanguageTile(p) {
    return h('button', { type: 'button', onClick: p.onClick, disabled: p.disabled, className: cx('k-langtile', p.selected && 'is-selected'), 'aria-pressed': p.selected ? 'true' : 'false', lang: p.lang, dir: p.rtl ? 'rtl' : undefined },
      h('span', { className: 'k-langtile__name' }, p.name), h('span', { className: 'k-langtile__status' }, p.status),
      p.rtl ? h('span', { className: 'k-langtile__rtl', dir: 'ltr' }, 'RTL') : null, p.selected ? h(Icon, { name: 'check', size: 15, color: 'var(--accent-text)' }) : null);
  }

  /* ---------- settings ---------- */
  function SettingsSection(p) {
    return h('section', { className: 'k-setsec', 'aria-label': p.title },
      h('div', { className: 'k-setsec__head' }, h('h2', { className: 'k-setsec__title' }, p.title), p.note ? h('p', { className: 'k-setsec__note' }, p.note) : null),
      h('div', { className: 'k-setsec__rows' }, p.children));
  }
  function SettingsRow(p) {
    return h('div', { className: 'k-setrow' },
      h('div', { className: 'k-setrow__text' }, h('div', { className: 'k-setrow__title' }, p.title), p.description ? h('div', { className: 'k-setrow__desc' }, p.description) : null),
      h('div', { className: 'k-setrow__control' }, p.children));
  }
  var CONN = { connected: ['ok', 'Connected'], ready: ['accent', 'Ready'], fallback: ['muted', 'Fallback'], offline: ['bad', 'Not answering'] };
  function ConnectionRow(p) {
    var st = CONN[p.status] || CONN.ready;
    return h('div', { className: 'k-conn' },
      h('span', { className: 'k-conn__icon' }, h(Icon, { name: p.icon || 'server', size: 18 })),
      h('div', { className: 'k-conn__main' }, h('div', { className: 'k-conn__name' }, p.name, h('span', { className: 'k-conn__status k-tone--' + st[0] }, st[1])), h('div', { className: 'k-conn__detail' }, p.detail)),
      h('div', { className: 'k-btngroup' }, p.onTest ? h(Button, { variant: 'ghost', size: 'sm', onClick: p.onTest, loading: p.testing }, p.testLabel || 'Test') : null, p.onRemove ? h(Button, { variant: 'ghost', size: 'sm', onClick: p.onRemove }, p.removeLabel || 'Remove') : null, p.onMore ? h(IconButton, { icon: 'dots', label: p.moreLabel || 'More', size: 'sm', onClick: p.onMore }) : null));
  }
  function JobRow(p) {
    return h(p.onClick ? 'button' : 'div', { type: p.onClick ? 'button' : undefined, onClick: p.onClick, 'aria-expanded': p.onClick ? String(!!p.open) : undefined, className: cx('k-job', p.open && 'is-open') },
      h(Icon, { name: p.icon || 'cpu', size: 16 }), h('span', { className: 'k-job__name' }, p.name), h('span', { className: 'k-job__desc' }, p.description),
      h('code', { className: 'k-job__model' }, p.model), h(Icon, { name: p.open ? 'up' : 'down', size: 14 }));
  }
  function FolderRow(p) {
    return h('div', { className: 'k-folder' }, h(Icon, { name: p.icon || 'book', size: 17 }), h('span', { className: 'k-folder__label' }, p.label),
      h('code', { className: 'k-folder__path', dir: 'ltr' }, p.path), h('span', { className: 'k-folder__size' }, p.size), p.onOpen ? h(Button, { variant: 'ghost', size: 'sm', onClick: p.onOpen }, p.openLabel || 'Open folder') : null);
  }
  function ShortcutRow(p) { return h(p.onClick ? 'button' : 'div', { type: p.onClick ? 'button' : undefined, onClick: p.onClick, className: cx('k-shortrow', p.recording && 'is-recording') }, h('span', null, p.label), p.recording ? h('span', { className: 'k-shortrow__rec' }, p.recording) : p.keys && p.keys.length ? h(Shortcut, { keys: p.keys }) : h('span', { className: 'k-shortrow__rec' }, p.unset || 'Not set')); }

  /* ---------- the scene ---------- */
  function renderProse(t) {
    if (typeof t !== 'string') return t;
    // *an action* in the action colour; _a thought_ (at word edges, so snake_case stays a word) dim, with no markers shown
    return t.split(/(\*[^*\n]+\*|(?<![\w*])_[^_\n]+?_(?!\w))/).map(function (s, i) {
      return /^\*[^*\n]+\*$/.test(s) ? h('em', { key: i, className: 'k-act' }, s.slice(1, -1))
        : /^_[^_\n]+_$/.test(s) ? h('em', { key: i, className: 'k-think' }, s.slice(1, -1)) : s;
    });
  }
  var SPEAKER = { liv: 'var(--speaker-liv)', mike: 'var(--speaker-mike)', theo: 'var(--speaker-theo)' };
  function SceneStage(p) {
    return h('div', { className: 'k-scene-stage', style: p.height ? { height: p.height } : undefined },
      h('img', { src: p.src || (ART[p.place] || {}).src, alt: p.alt || '' }), p.children);
  }
  function SceneButton(p) {
    var a = { className: cx('k-scenebtn', p.pressed && 'is-pressed'), 'aria-label': p.label, title: p.label, onClick: p.onClick };
    var ic = h(Icon, { name: p.icon, size: p.iconSize || 18 });
    return p.href ? h('a', Object.assign({ href: p.href }, a), ic) : h('button', Object.assign({ type: 'button' }, a), ic);
  }
  function SceneHeader(p) {
    return h('div', { className: 'k-scenehead' }, h(SceneButton, { icon: 'cloud', label: 'Back to the Sky', href: p.backHref }),
      h('div', { className: 'k-scenehead__text' }, h('span', { className: 'k-scenehead__title' }, p.title), h('span', { className: 'k-scenehead__sub' }, p.subtitle)));
  }
  function BackstageToggle(p) {
    var v = useCtl(p, 'on', 'defaultOn', false, 'onToggle');
    return h('button', { type: 'button', role: 'switch', 'aria-checked': v[0] ? 'true' : 'false', className: 'k-bstoggle', onClick: function () { v[1](!v[0]); } },
      h(Icon, { name: 'layers', size: 16 }), 'Backstage', h('span', { className: 'k-bstoggle__track' }, h('span', { className: 'k-bstoggle__knob' })));
  }
  function ChatPanel(p) {
    return h('section', { className: 'k-chat', 'aria-label': p.label || 'The story', style: p.height ? { height: p.height } : undefined },
      h('div', { className: 'k-chat__lines', 'aria-live': 'polite' }, p.children), p.composer ? h('div', { className: 'k-chat__composer' }, p.composer) : null);
  }
  function LineTools(p) {
    return h('div', { className: 'k-linetools', role: 'toolbar', 'aria-label': 'Line tools' },
      p.take ? [h('button', { key: 'p', type: 'button', 'aria-label': 'Previous take', disabled: p.disabled || !p.onPrev, onClick: p.onPrev }, h(Icon, { name: 'left', size: 15 })), h('span', { key: 't' }, p.take),
      h('button', { key: 'n', type: 'button', 'aria-label': p.nextLabel || 'New take', disabled: p.disabled || !p.onNext, onClick: p.onNext }, h(Icon, { name: 'right', size: 15 })), h('span', { key: 's', className: 'k-linetools__sep' })] : null,
      h('button', { type: 'button', disabled: p.disabled, onClick: p.onEdit }, h(Icon, { name: 'edit', size: 14 }), p.editLabel || 'Edit'), h('button', { type: 'button', disabled: p.disabled, onClick: p.onHide }, h(Icon, { name: 'eyeoff', size: 14 }), p.hideLabel || 'Hide'),
      p.onMore ? h('button', { type: 'button', 'aria-label': 'Line menu', onClick: p.onMore }, h(Icon, { name: 'dots', size: 15 })) : null);
  }
  var LINE_ICON = { think: 'thought', whisper: 'ear' };
  var LINE_NOTE = { think: 'thinks', whisper: 'whispers' };
  function ChatLine(p) {
    var time = p.exact ? h(Stamp, { exact: p.exact, detail: p.timeDetail, open: p.timeOpen, tone: 'scene' }, p.time) : h('span', { className: 'k-line__time' }, p.time);
    // mode: 'think' | 'whisper' | 'narrate' (unset = said aloud). Narration has no speaker; the others name how it was meant.
    var how = p.mode && p.mode !== 'narrate' ? h('span', { className: 'k-line__how' }, h(Icon, { name: LINE_ICON[p.mode], size: 13 }), p.modeNote || LINE_NOTE[p.mode]) : null;
    return h('article', { id: p.id, tabIndex: p.tools ? 0 : undefined, onContextMenu: p.onContextMenu, onKeyDown: p.onKeyDown, className: cx('k-line', p.mode && 'k-line--' + p.mode, p.dim && 'k-line--dim', p.hover && 'is-hover', p.tools && 'has-tools') },
      p.tools ? p.tools : p.hover ? h(LineTools, { take: p.take }) : null,
      h('div', { className: 'k-line__head' }, p.mode === 'narrate' || !p.name ? null : h('span', { className: 'k-line__who', style: { color: p.color || SPEAKER[p.speaker] || 'var(--scene-ink)' } }, p.name), how, time,
        p.recalled ? h('span', { className: 'k-line__spark', 'aria-label': 'Drew on memory' }, h(Icon, { name: 'spark', size: 14, color: 'var(--event-memory)' })) : null,
        p.writing ? h('span', { className: 'k-line__time' }, 'writing…') : null),
      h('p', { className: 'k-line__text' }, renderProse(p.text), p.writing ? h('span', { className: 'k-caret' }) : null),
      p.children ? h('div', { className: 'k-line__reacts' }, p.children) : null,
      p.thought ? h('div', { className: 'k-line__reacts' }, h('span', { className: 'k-thought' }, h(Icon, { name: 'thought', size: 13 }), p.thought)) : null);
  }
  function TitleCard(p) {
    return h('div', { className: 'k-titlecard', role: 'separator' }, h('span', { className: 'k-titlecard__rule' }), h('span', { className: 'k-titlecard__text' }, p.children),
      p.undo ? h('button', { type: 'button', className: 'k-titlecard__undo', onClick: p.onUndo }, h(Icon, { name: 'undo', size: 11 }), 'Undo') : null, h('span', { className: 'k-titlecard__rule' }));
  }
  function StoryNote(p) {
    return h('div', { className: 'k-note' }, p.who || p.src || p.name ? h(Avatar, { who: p.who, src: p.src, name: p.name, size: 22, away: p.away }) : null, h('span', null, p.children), p.onUndo ? h('button', { type: 'button', className: 'k-titlecard__undo', onClick: p.onUndo }, h(Icon, { name: 'undo', size: 11 }), 'Undo') : null);
  }
  function RecallBox(p) {
    return h('div', { className: 'k-recall' }, h('div', { className: 'k-recall__head' }, h(Icon, { name: 'spark', size: 14 }), p.title || 'Remembered'),
      h('span', { className: 'k-recall__memory' }, p.memory), p.meta ? h('span', { className: 'k-recall__meta' }, p.meta) : null);
  }
  var REACT_ICON = { memory: 'spark', feeling: 'heart', warm: 'heart', belief: 'help', mood: 'thought' };
  function Reaction(p) {
    return h('span', { className: cx('k-react', 'k-react--' + (p.kind || 'feeling'), p.soft && 'is-soft') }, p.who || p.avatarSrc || p.name ? h(Avatar, { who: p.who, size: 20, src: p.avatarSrc, name: p.name }) : null, h(Icon, { name: REACT_ICON[p.kind] || 'heart', size: 13, stroke: 2 }), p.children);
  }
  function ModeChip(p) {
    return h('button', { type: 'button', className: cx('k-mode', p.open && 'is-open'), 'aria-haspopup': 'menu', 'aria-expanded': p.open ? 'true' : 'false', onClick: p.onClick },
      h(Icon, { name: 'spark', size: 14, color: 'var(--event-memory)' }), p.value || 'Auto', p.detected ? h('span', { className: 'k-mode__detected' }, '· ' + p.detected) : null, h(Icon, { name: 'down', size: 14 }));
  }
  var MODES = [['Auto', 'Works it out from how you write', 'spark'], ['Say', 'Plain text', 'chat'], ['Do', '*between asterisks*', 'hand'], ['Whisper', '(in brackets)', 'ear'], ['Think', '_underscores_', 'thought'], ['Narrate', '> a line starting with >', 'quill']];
  function ModeMenu(p) {
    var v = p.value || 'Auto';
    return h('div', { className: 'k-menu k-menu--scene', role: 'menu', 'aria-label': 'How your line is read' },
      MODES.map(function (m) {
        return h('button', { key: m[0], type: 'button', role: 'menuitemradio', 'aria-checked': String(m[0] === v), className: cx('k-menu__item', m[0] === v && 'is-active'), onClick: function () { if (p.onPick) p.onPick(m[0]); } },
          h(Icon, { name: m[2], size: 16 }), h('span', { className: 'k-menu__label' }, m[0], h('span', { className: 'k-menu__detail' }, m[1])), m[0] === v ? h(Icon, { name: 'check', size: 15, className: 'k-menu__check' }) : null);
      }),
      h('div', { className: 'k-menu__foot' }, 'Auto works it out from how you write. Pick a mode to override it for this line.'));
  }
  function Composer(p) {
    var v = useCtl(p, 'value', 'defaultValue', '');
    var adv = useCtl(p, 'advanced', 'defaultAdvanced', false, 'onAdvanced');
    function send() { if (p.onSend) p.onSend(v[0]); }
    return h('div', { className: cx('k-composer', adv[0] && 'is-advanced') },
      adv[0] && p.meter != null ? h('div', { className: 'k-composer__meter' }, h('i', { style: { width: p.meter + '%' } })) : null,
      adv[0] ? h('div', { className: 'k-composer__adv' },
        h('span', { className: 'k-composer__hear' }, h(AvatarStack, { people: p.hearing || [], size: 22 }), h('b', null, p.hearingText || 'Only Mike will hear this'), p.away ? h('span', { className: 'k-composer__away' }, p.away) : null),
        h('span', { className: 'k-composer__answers' }, h('span', { className: 'k-composer__label' }, 'Answers'),
          (p.answers || []).map(function (a) { return h(Chip, { key: a.id, size: 'sm', icon: a.icon, who: a.who, src: a.src, pressed: a.id === p.answer, onPress: function () { if (p.onAnswer) p.onAnswer(a.id); } }, a.label); }))) : null,
      h('label', { className: 'k-composer__field' }, h('span', { className: 'k-sr' }, 'Your line'),
        h('textarea', { rows: 2, value: v[0], placeholder: p.placeholder || 'Speak or act as Liv…', onChange: function (e) { v[1](e.target.value); },
          onKeyDown: function (e) { if (p.onKey && p.onKey(e)) return; if (e.key === 'Escape' && p.streaming && p.onStop) { e.preventDefault(); p.onStop(); } else if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } } })),
      h('div', { className: 'k-composer__bar' },
        h('div', { className: 'k-composer__left' },
          h(Segmented, { label: 'Composer detail', options: ['Simple', 'Advanced'], value: adv[0] ? 'Advanced' : 'Simple', onChange: function (o) { adv[1](o === 'Advanced'); }, tone: 'scene', size: 'sm' }),
          h(SceneButton, { icon: 'ff', label: 'Continue the story', iconSize: 14, onClick: p.onContinue }),
          adv[0] ? h('button', { type: 'button', className: 'k-scenechip', onClick: p.onPassTime }, h(Icon, { name: 'clock', size: 14 }), 'Pass time') : null,
          adv[0] && p.tokens ? h('span', { className: 'k-composer__tokens' }, p.tokens) : null),
        h('div', { className: 'k-composer__right' }, p.queued ? h('span', { className: 'k-composer__tokens' }, p.queued) : null, h(ModeChip, { value: p.mode, detected: p.detected, open: p.modeOpen, onClick: p.onMode }),
          p.streaming ? h('button', { type: 'button', className: 'k-btn k-btn--scene-stop', onClick: p.onStop }, h(Icon, { name: 'stop', size: 15 }), 'Stop')
                      : h('button', { type: 'button', className: 'k-btn k-btn--scene-send', onClick: send }, 'Send', h(Icon, { name: 'send', size: 15 })))));
  }
  function EditLine(p) {
    return h('article', { className: 'k-editline' },
      h('div', { className: 'k-line__head' }, h('span', { className: 'k-line__who', style: { color: p.color || SPEAKER[p.speaker] || 'var(--scene-ink)' } }, p.name), h('span', { className: 'k-line__time' }, p.time), h('span', { className: 'k-line__time' }, 'Editing')),
      h('textarea', { className: 'k-editline__field', rows: 3, value: p.value, defaultValue: p.value === undefined ? p.text : undefined, onChange: p.onChange ? function (e) { p.onChange(e.target.value); } : undefined, 'aria-label': 'Edit line', autoFocus: !!p.onChange,
        onKeyDown: function (e) { if (e.key === 'Escape' && p.onCancel) { e.preventDefault(); e.stopPropagation(); p.onCancel(); } if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && p.onSave) { e.preventDefault(); p.onSave(); } } }),
      p.after ? h('div', { className: 'k-editline__warn' }, h(Icon, { name: 'alert', size: 16 }), h('span', null, h('b', null, p.warn || 'Regenerating from here rewrites the ' + p.after + ' messages after this one.'), ' ', p.warnMore || 'They’ll be kept as the previous take, so you can flip back.')) : null,
      h('div', { className: 'k-btngroup k-btngroup--end' }, h('button', { type: 'button', className: 'k-btn k-btn--scene-ghost', onClick: p.onCancel }, 'Cancel'), h('button', { type: 'button', className: 'k-btn k-btn--scene-stop', onClick: p.onSave }, 'Save edit'), p.onRegenerate ? h('button', { type: 'button', className: 'k-btn k-btn--scene-send', onClick: p.onRegenerate }, 'Save and regenerate from here') : null));
  }
  function Widget(p) {
    return h('section', { className: cx('k-widget', p.edit && 'is-edit', p.dragging && 'is-dragging'), 'aria-label': p.label, style: p.width ? { width: p.width } : undefined },
      p.edit ? h('span', { className: 'k-widget__drag', 'aria-label': 'Drag to move' }, h(Icon, { name: 'drag', size: 15 })) : null,
      p.edit ? h('span', { className: 'k-widget__ctl' }, h('button', { type: 'button', className: cx('k-widget__pin', p.pinned && 'is-on'), 'aria-label': p.pinned ? 'Unpin' : 'Pin', 'aria-pressed': String(!!p.pinned), onClick: p.onPin }, h(Icon, { name: 'pushpin', size: 14 })),
        h('button', { type: 'button', className: 'k-widget__remove', 'aria-label': 'Remove widget', onClick: p.onRemove }, h(Icon, { name: 'x', size: 14 }))) : null,
      p.children);
  }
  function CharacterWidget(p) {
    var a = ART[p.who] || {};
    return h(Widget, { label: p.name, edit: p.edit, pinned: p.pinned !== false, dragging: p.dragging, width: p.width || 272, onPin: p.onPin, onRemove: p.onRemove },
      h('div', { className: cx('k-cw__art', p.away && 'is-away'), onClick: p.edit ? undefined : p.onOpen, style: p.onOpen && !p.edit ? { cursor: 'pointer' } : undefined }, p.src || a.src ? h('img', { src: p.src || a.src, alt: p.alt || (p.name + ', portrait'), style: framed(p.focus || a.focus, p.zoom) }) : h('div', { className: 'k-char__noface' }, h('span', { 'aria-hidden': 'true' }, (p.name || '?')[0])),
        p.thinking ? h('span', { className: 'k-cw__flag k-cw__flag--thinking' }, h(Icon, { name: 'thought', size: 13 }), 'thinking…') : null,
        p.badge ? h('span', { className: 'k-cw__flag k-cw__flag--badge' }, p.badge) : null,
        !p.edit ? h('button', { type: 'button', className: cx('k-cw__pin', p.pinned !== false && 'is-on'), 'aria-label': (p.pinned !== false ? 'Unpin ' : 'Pin ') + p.name, 'aria-pressed': String(p.pinned !== false), onClick: function (e) { e.stopPropagation(); if (p.onPin) p.onPin(); } }, h(Icon, { name: 'pushpin', size: 14 })) : null),
      h('div', { className: 'k-cw__body', onClick: p.edit ? undefined : p.onOpen, style: p.onOpen && !p.edit ? { cursor: 'pointer' } : undefined }, h('div', { className: 'k-cw__name' }, h(StoryName, { size: 'card' }, p.name), p.mood ? h(StatePill, { tone: 'warm' }, p.mood) : null), p.status ? h('span', { className: 'k-cw__status' }, p.status) : null));
  }
  function CharacterRowWidget(p) {
    return h(Widget, { label: p.name, edit: p.edit, width: p.width || 272, pinned: p.pinned, onPin: p.onPin, onRemove: p.onRemove },
      h('div', { className: 'k-cwrow', onClick: p.edit ? undefined : p.onOpen, style: p.onOpen && !p.edit ? { cursor: 'pointer' } : undefined }, h(Avatar, { who: p.who, src: p.src, focus: p.focus, zoom: p.zoom, name: p.name, size: 40, away: p.away }), h('div', null, h('b', null, p.name), h('span', null, p.status))));
  }
  function ClockWidget(p) {
    var night = p.kind === 'night';
    return h(Widget, { label: 'Story clock', edit: p.edit, width: p.width || 272, pinned: p.pinned, onPin: p.onPin, onRemove: p.onRemove },
      h('div', { className: 'k-clock' },
        h('div', { className: 'k-clock__top' }, h(Stamp, { exact: p.exact, detail: p.detail, open: p.open, tone: 'scene' }, h('span', { className: 'k-clock__time' }, p.time)),
          h('svg', { width: 96, height: 32, viewBox: '0 0 120 40', 'aria-hidden': 'true', className: 'k-clock__arc' },
            h('path', { d: 'M6 38 A56 56 0 0 1 114 38', fill: 'none', stroke: 'var(--scene-border)', strokeWidth: 1.5, strokeDasharray: '3 4' }),
            h('path', { d: 'M0 38h120', stroke: 'var(--scene-border)' }),
            night ? h('circle', { cx: 60, cy: 8, r: 6, fill: 'var(--scene-ink)' }) : h('circle', { cx: 106, cy: 30, r: 6, fill: 'var(--scene-primary)' }))),
        h('span', { className: 'k-clock__rel' }, p.rel),
        h('div', { className: 'k-clock__foot' }, h('span', null, p.place), h('button', { type: 'button', className: 'k-scenechip', onClick: p.onPassTime, disabled: p.disabled }, h(Icon, { name: 'clock', size: 13 }), 'Pass time'))));
  }
  function MusicWidget(p) {
    return h(Widget, { label: 'Music', edit: p.edit, width: p.width || 272 },
      h('div', { className: 'k-music' }, h('button', { type: 'button', className: 'k-music__play', 'aria-label': p.playing === false ? 'Play' : 'Pause' }, h(Icon, { name: p.playing === false ? 'play' : 'pause', size: 15, stroke: 2 })),
        h('div', { className: 'k-music__text' }, h('b', null, p.track), h('span', null, p.source || 'Matched to the scene')),
        p.playing === false ? null : h('span', { className: 'k-music__bars', 'aria-hidden': 'true' }, h('i'), h('i'), h('i'), h('i'), h('i')),
        h('button', { type: 'button', className: 'k-music__vol', 'aria-label': 'Volume' }, h(Icon, { name: 'volume', size: 16 }))));
  }
  function TimeSkipCard(p) {
    return h('div', { className: 'k-skipcard', role: 'status' },
      h('span', { className: 'k-skipcard__story' }, p.story),
      h('span', { className: 'k-skipcard__big' }, p.children || 'Three weeks later'),
      h('div', { className: 'k-skipcard__move' }, h('span', null, p.from), h(Icon, { name: 'arrow', size: 18 }), h('b', null, p.to)),
      p.note ? h('span', { className: 'k-skipcard__note' }, p.note) : null,
      h('div', { className: 'k-btngroup' }, p.onUndo ? h('button', { type: 'button', className: 'k-btn k-btn--scene-stop', onClick: p.onUndo }, h(Icon, { name: 'undo', size: 15 }), 'Undo') : null, p.confirm ? h('button', { type: 'button', className: 'k-btn k-btn--scene-send', onClick: p.onConfirm }, p.confirm) : null));
  }

  /* ---------- backstage ---------- */
  function BackstagePanel(p) {
    return h('section', { className: 'k-bs', 'aria-label': p.title, style: p.width ? { width: p.width } : undefined },
      h('div', { className: 'k-bs__head' }, h('span', { className: 'k-bs__title' }, p.title), p.action ? h('button', { type: 'button', className: 'k-bs__btn', onClick: p.onAction }, p.actionIcon ? h(Icon, { name: p.actionIcon, size: 12 }) : null, p.action) : (p.status ? h('span', { className: 'k-bs__ok' }, p.status) : null)),
      h('div', { className: 'k-bs__body' }, p.children));
  }
  function MindNode(p) {
    return h('div', { className: cx('k-node', p.hot && 'is-hot') },
      h('div', { className: 'k-node__head' }, h('span', null, p.kind), h('span', null, (p.value || 0).toFixed(2))),
      h('div', { className: 'k-node__text' }, p.children),
      h('div', { className: 'k-node__bar' }, h('i', { style: { width: Math.round((p.value || 0) * 100) + '%' } })));
  }
  function EngineRow(p) {
    return h('div', { className: 'k-engrow' }, h('span', { className: 'k-engrow__job' }, h('i', { className: 'k-engrow__dot k-engrow__dot--' + (p.state || 'ok') }), p.job), h('span', { className: 'k-engrow__model' }, p.model), h('span', null, p.stat, ' ', h('span', { className: 'k-engrow__detail' }, p.detail)));
  }
  var SEGCOL = ['#6aa8ff', '#8cc3ff', '#ffd08a', '#a9e0c8', '#c7b8ff', '#f4a595'];
  function PromptBar(p) {
    var segs = p.segments || [], total = p.total || 16384;
    return h('div', { className: 'k-promptbar' },
      h('div', { className: 'k-promptbar__row' }, h('span', null, p.label), p.meta ? h('span', { className: 'k-engrow__detail' }, p.meta) : null),
      h('div', { className: 'k-promptbar__bar', role: 'img', 'aria-label': p.label }, segs.map(function (s, i) { return h('i', { key: i, style: { width: (s.value / total * 100) + '%', background: SEGCOL[i % SEGCOL.length] } }); })),
      h('div', { className: 'k-promptbar__legend' }, segs.map(function (s, i) { return h('span', { key: i }, h('i', { style: { background: SEGCOL[i % SEGCOL.length] } }), s.name, ' ', s.value.toLocaleString('en'), h('span', { className: 'k-engrow__detail' }, ' / ' + s.limit.toLocaleString('en'))); })));
  }

  window.Kataki = { Icon: Icon, Avatar: Avatar, AvatarStack: AvatarStack, Eyebrow: Eyebrow, StoryName: StoryName, Text: Text, Kbd: Kbd, Shortcut: Shortcut, Divider: Divider, Panel: Panel, Sky: Sky, Spinner: Spinner, Button: Button, IconButton: IconButton, ButtonGroup: ButtonGroup, TextLink: TextLink, Field: Field, TextField: TextField, TextArea: TextArea, Select: Select, SearchField: SearchField, Checkbox: Checkbox, RadioGroup: RadioGroup, Toggle: Toggle, Segmented: Segmented, Slider: Slider, Chip: Chip, ChoiceChips: ChoiceChips, DropZone: DropZone, StepHeader: StepHeader, Rail: Rail, PersonaSwitch: PersonaSwitch, TopBar: TopBar, Tabs: Tabs, SideNav: SideNav, Breadcrumbs: Breadcrumbs, ShowMore: ShowMore, Menu: Menu, Tooltip: Tooltip, Popover: Popover, Dialog: Dialog, Sheet: Sheet, Toast: Toast, CommandPalette: CommandPalette, Callout: Callout, Alert: Alert, EmptyState: EmptyState, ProgressBar: ProgressBar, Skeleton: Skeleton, StepList: StepList, StatusLine: StatusLine, StatePill: StatePill, Tag: Tag, Badge: Badge, Meter: Meter, MemoryRow: MemoryRow, Stat: Stat, StatRow: StatRow, KeyValue: KeyValue, ListRow: ListRow, TimeStrip: TimeStrip, Stamp: Stamp, Changelog: Changelog, Bubble: Bubble, SecretCard: SecretCard, Still: Still, EventCard: EventCard, CharacterCard: CharacterCard, AddCard: AddCard, PersonaCard: PersonaCard, StoryCard: StoryCard, ContinueHero: ContinueHero, StoryPreview: StoryPreview, RelationshipCard: RelationshipCard, PlaceCard: PlaceCard, PlotCard: PlotCard, DoorCard: DoorCard, SearchResult: SearchResult, ThemeTile: ThemeTile, LanguageTile: LanguageTile, SettingsSection: SettingsSection, SettingsRow: SettingsRow, ConnectionRow: ConnectionRow, JobRow: JobRow, FolderRow: FolderRow, ShortcutRow: ShortcutRow, SceneStage: SceneStage, SceneButton: SceneButton, SceneHeader: SceneHeader, BackstageToggle: BackstageToggle, ChatPanel: ChatPanel, LineTools: LineTools, ChatLine: ChatLine, TitleCard: TitleCard, StoryNote: StoryNote, RecallBox: RecallBox, Reaction: Reaction, ModeChip: ModeChip, ModeMenu: ModeMenu, Composer: Composer, EditLine: EditLine, Widget: Widget, CharacterWidget: CharacterWidget, CharacterRowWidget: CharacterRowWidget, ClockWidget: ClockWidget, MusicWidget: MusicWidget, TimeSkipCard: TimeSkipCard, BackstagePanel: BackstagePanel, MindNode: MindNode, EngineRow: EngineRow, PromptBar: PromptBar, ICONS: ICONS, ART: ART, framed: framed };
})();
