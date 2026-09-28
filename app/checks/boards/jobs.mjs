// Every board the side-by-side check compares, and how the app gets into the same state.
//   node checks/boards/jobs.mjs [night|day|both] [filter] > jobs.json
// Engines (see fixture.py): SHOOT_PORT the sample library + fixture, DAY1 the sample world with
// no stories yet, EMPTY a library with nothing in it, DEAD a copy of the sample whose model doesn't answer.
// A job's js runs in the app page with click(text), key(k, mods), type(text), wait(ms).
const EMPTY = process.env.SHOOT_EMPTY ?? '8769'
const DEAD = process.env.SHOOT_DEAD ?? '8770'
const DAY1 = process.env.SHOOT_DAY1 ?? '8771'
const menu = "await click('Story menu');"
const say = (text) => `document.querySelector('.scene textarea').focus(); await type(${JSON.stringify(text)});`
const right = (sel) => `document.querySelector(${JSON.stringify(sel)}).dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, clientX: 700, clientY: 300 })); await wait(400);`

// [code, board, app route, height, js?, engine port?]
const ROUTES = [
  ['B1', 'FirstRun', '/welcome', 900], ['B2', 'FirstRunDownload', '/welcome/download', 900], ['B3', 'FirstRunServer', '/welcome/server', 900],
  ['B4', 'FirstRunOnline', '/welcome/online', 900], ['B5', 'FirstRunWho', '/welcome/who', 900], ['C1', 'Home', '/home', 1360],
  ['C8', 'Search', '/search?q=gala', 1100], ['D1', 'Characters', '/characters', 1100], ['E1', 'Profile', '/characters/6?tab=story', 1500],
  ['E2', 'ProfileTab', '/characters/6?tab=profile', 1500], ['F1', 'NewCharacter', '/characters/new', 1200], ['F6', 'EditCharacter', '/characters/6/edit', 1900],
  ['G1', 'NewStory', '/stories/new', 1000], ['H1', 'Stories', '/stories', 900], ['H2', 'StoriesByCharacter', '/stories?by=character', 900],
  ['I1', 'World', '/world', 1300], ['J1', 'You', '/you', 1100], ['K1', 'SetGeneral', '/settings/general', 1000],
  ['K2', 'SetAppearance', '/settings/appearance', 1000], ['K3', 'SetLanguage', '/settings/language', 1000], ['K4', 'SetModels', '/settings/models', 1200],
  ['K9', 'SetMemory', '/settings/memory', 1000], ['K10', 'SetData', '/settings/data', 1000], ['K14', 'SetShortcuts', '/settings/shortcuts', 1100],
  ['K16', 'SetAbout', '/settings/about', 1000], ['N1', 'ModelGone', '/status/model', 1000], ['P1', 'Scene', '/story/1', 900],
]
const OVERLAYS = [
  ['B6', 'FirstRunPersona', '/welcome/who', 900, "await click('Change')"],
  ['C4', 'PersonaMenu', '/home', 1360, "await key('p', { ctrlKey: true })"],
  ['C5', 'Palette', '/home', 1360, "await key('k', { ctrlKey: true }); await type('gala')"],
  ['C6', 'PaletteEmpty', '/home', 1360, "await key('k', { ctrlKey: true })"],
  ['C7', 'PaletteNone', '/home', 1360, "await key('k', { ctrlKey: true }); await type('galla')"],
  ['C9', 'SearchNone', '/search?q=galla', 900],
  ['D2', 'CharactersList', '/characters', 1100, "await click('List')"],
  ['D4', 'ImportCards', '/characters?import=1', 1100],
  ['D5', 'NewGroup', '/characters', 1100, "await click('New group')"],
  ['E3', 'ProfileMemories', '/characters/6', 1500, "[...document.querySelectorAll('button')].find((b) => /^All \\d+ memories/.test(b.textContent)).click(); await wait(500)"],
  ['E4', 'ForgetMemory', '/characters/6', 1500, "[...document.querySelectorAll('button')].find((b) => /^All \\d+ memories/.test(b.textContent)).click(); await wait(500);" + "document.querySelector('.pf-memrow .k-iconbtn, .pf-memrow button').click(); await wait(400); await click('Forget this…')"],
  ['E5', 'DeleteCharacter', '/characters/6', 1500, "await click('More for Mike'); await click('Delete Mike…')"],
  ['F2', 'NewCharacterFull', '/characters/new', 1900, "for (const b of document.querySelectorAll('.opt')) { b.click(); await wait(150) }"],
  ['F3', 'NewCharacterErrors', '/characters/new', 1200, "await click('Create')"],
  ['F4', 'PortraitPicker', '/characters/new', 1200, "await click('Pick from Kataki')"],
  ['F5', 'PortraitFocus', '/characters/6/edit', 1200, "await click('Crop and focus')"],
  ['F7', 'DiscardChanges', '/characters/6/edit', 1900, "[...document.querySelectorAll('main input')].find((i) => i.value === 'Mike').focus(); await type('Michael'); await click('Characters')"],
  ['G2', 'NewStoryGroup', '/stories/new', 1000, "await click('Mike'); await click('Theo')"],
  ['G3', 'NewStoryFind', '/stories/new', 1000, "await click('Find')"],
  ['G4', 'NewStoryPlace', '/stories/new', 1000, "await click('Mike'); await click('Somewhere new')"],
  ['H4', 'RenameStory', '/stories', 900, "await click('Rename')"],
  ['H5', 'DeleteStory', '/stories', 900, "await click('Delete')"],
  ['H6', 'ExportStory', '/stories', 900, "await click('Export')"],
  ['I3', 'PlaceDetail', '/world', 1300, "await click('Halcyon Coffee')"],
  ['I4', 'PlotDetail', '/world', 1300, "document.querySelectorAll('.w-card__open')[2].click(); await wait(500)"],
  ['I5', 'NewPlace', '/world', 1300, "await click('New place')"],
  ['I6', 'NewPlot', '/world', 1300, "await click('New plot')"],
  ['I7', 'NewBook', '/world', 1300, "await click('New book')"],
  ['J2', 'EditPersona', '/you', 1100, "await click('Edit persona')"],
  ['J3', 'DeletePersona', '/you', 1100, "await click('Cas Brennan'); await click('Delete this persona')"],
  ['K5', 'SetModelsAdvanced', '/settings/models', 1500, "await click('Characters')"],
  ['K7', 'AddApi', '/settings/models', 1200, "await click('Add an online model')"],
  ['K8', 'FindServers', '/settings/models', 1200, "await click('Look for servers on this computer')"],
  ['K12', 'Backups', '/settings/data', 1000, "await click('Change')"],
  ['K13', 'DeleteSomething', '/settings/data', 1000, "await click('Delete something')"],
  ['K15', 'RemapShortcut', '/settings/shortcuts', 1100, "await click('Search everything')"],
  ['L1', 'Feedback', '/home', 1360, "await click('Feedback')"],
  ['L2', 'BugReport', '/home', 1360, "await click('Feedback'); await click('Bug')"],
  ['L3', 'Suggestion', '/home', 1360, "await click('Feedback'); await click('Suggestion')"],
  // the empty library and the silent model
  ['C2', 'HomeEmpty', '/home', 1100, '', DAY1], ['D3', 'CharactersNone', '/characters', 900, "await click('Favourites')"],
  ['H3', 'StoriesEmpty', '/stories', 900, '', DAY1], ['I2', 'WorldEmpty', '/world', 900, '', EMPTY],
  ['C3', 'HomeOffline', '/home', 1360, 'await wait(3000)', DEAD], ['K6', 'SetModelsFailed', '/settings/models', 1300, "await click('Test again'); await wait(6000)", DEAD],
  ['N2', 'DiskFull', '/home', 900, "dispatchEvent(new CustomEvent('kataki:disk', { detail: 'DISK_FULL' })); await wait(300)"],
  // the Scene
  ['P2', 'SceneMenu', '/story/1', 900, menu],
  ['P3', 'SceneWidgets', '/story/1', 900, menu + "await click('Edit widgets')"],
  ['P6', 'SceneAdvanced', '/story/1', 900, "await click('Advanced')"],
  ['P7', 'SceneModes', '/story/1', 900, say('*leans over the counter* Then don’t tell anyone you saw me here.') + "await click('Auto')"],
  ['P8', 'SceneEditLine', '/story/1', 900, "document.querySelector('.scene textarea').focus(); await key('ArrowUp')"],
  ['P10', 'SceneTakes', '/story/1', 900, "await key('r', { ctrlKey: true }); await wait(5000)"],
  ['P11', 'ScenePassTime', '/story/1', 900, menu + "[...document.querySelectorAll('.k-menu__item')].find((b) => b.textContent.startsWith('Pass time')).click(); await wait(400)"],
  ['P15', 'ScenePeek', '/story/1', 900, "document.querySelector('.k-charw, .k-widget').click(); await wait(400)"],
  ['P16', 'SceneReading', '/story/1', 900, menu + "await click('Reading mode')"],
  ['P17', 'ScenePlace', '/story/1', 900, menu + "await click('Scene and place')"],
  ['P18', 'SceneSettings', '/story/1', 900, menu + "await click('Story settings')"],
  ['P19', 'SceneFailed', '/story/1', 900, say('Say that again?') + "await key('Enter'); await wait(8000)", DEAD],
  ['P20', 'SceneFirst', '/story/5', 900],
  ['P21', 'SceneNarrator', '/story/6', 900],
  ['Q1', 'Backstage', '/story/1', 900, "await click('Backstage')"],
  ['Q2', 'BackstageNode', '/story/1', 900, "await click('Backstage'); document.querySelector('.k-mindnode, .k-node, [class*=mindnode]').click(); await wait(400)"],
  ['Q3', 'BackstagePrompt', '/story/1', 900, "await click('Backstage'); await click('prompt')"],
  ['Q4', 'BackstageMemory', '/story/1', 900, "await click('Backstage'); await click('memories')"],
  ['Q5', 'BackstageLogs', '/story/1', 900, "await click('Backstage'); await click('logs')"],
]

// R1–R4 are collages of several screens: the app is shot alone at the proof's size, to look at
// next to the board, and the page must never scroll sideways.
const WIDE = "const m = document.querySelector('.app__main'); if (m && m.scrollWidth > m.clientWidth + 1) throw new Error('scrolls sideways: ' + m.scrollWidth + ' > ' + m.clientWidth)"
const PROOFS = [
  ['R1-home', '/home', 1024, 1, 700], ['R1-scene', '/story/1', 1024, 1, 700],
  ['R2-home', '/home?dir=rtl', 1440, 1, 900], ['R3-scene', '/story/1?dir=rtl', 1440, 1, 900],
  ...['home', 'stories', 'characters', 'characters/6', 'characters/new', 'stories/new', 'world', 'you', 'settings/general', 'search?q=gala'].map((r) => [`R4-${r.replace(/[/?=]/g, '-')}`, `/${r}`, 1440, 2, 900, WIDE]),
  ['R4-scene', '/story/1', 1440, 2, 900],
]

// M1, M2 are catalogues: each menu is shot open in the app, to read against the sheet
const ctx = (sel) => `const el = document.querySelector(${JSON.stringify(sel)}); const r = el.getBoundingClientRect(); el.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: r.left + 40, clientY: r.top + 30 })); await wait(500)`
PROOFS.push(
  ['M1-story', '/stories', 1440, 1, 900, ctx('.st-list [role=listitem]')], ['M1-home', '/home', 1440, 1, 900, ctx('.home-row a')],
  ['M1-character', '/characters', 1440, 1, 900, ctx('.ch-card')], ['M1-place', '/world', 1440, 1, 900, ctx('.w-card')],
  ['M1-book', '/world', 1440, 1, 900, ctx('.tree__book')], ['M1-persona', '/you', 1440, 1, 900, ctx('.ns-pick')],
  ['M1-connection', '/settings/models', 1440, 1, 900, ctx('.k-conn, [class*=conn]')], ['M1-filter', '/characters', 1100, 1, 900, "document.querySelector('.k-chip').click(); await wait(400)"],
  ['M2-line', '/story/1', 1440, 1, 900, ctx('.k-line')], ['M2-widget', '/story/1', 1440, 1, 900, ctx('.wcell')], ['M2-clock', '/story/1', 1440, 1, 900, ctx('.scene__left .wcell')],
)

const [, , which = 'both', filter = ''] = process.argv
const themes = which === 'both' ? ['night', 'day'] : [which]
const jobs = []
for (const theme of themes) {
  for (const [code, board, app, h, js, port] of [...ROUTES, ...OVERLAYS]) {
    if (filter && !new RegExp(`^(${filter})$`).test(code)) continue
    jobs.push({ id: `${code}-${theme}`, board, props: { theme }, app, theme, h, js: js || undefined, port })
  }
}
for (const theme of themes) {
  for (const [code, app, w, zoom, h, js] of PROOFS) {
    if (filter && !new RegExp(`^(${filter})$`).test(code.split('-')[0])) continue
    jobs.push({ id: `${code}-${theme}`, app, w, zoom, h, js, theme, appOnly: true })
  }
}
process.stdout.write(JSON.stringify(jobs, null, 1))
