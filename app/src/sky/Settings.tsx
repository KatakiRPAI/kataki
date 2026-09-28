// Settings (K1–K18): docs/handoff/kataki-handoff/SCREENS.md › K. Every change saves itself.
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { api, type StorySummary } from '../api'
import { isPersona } from '../characters'
import { K } from '../ds'
import { useLibrary, useLoad } from '../hooks'
import { setPref, usePrefs } from '../prefs'
import { complete, lang, LANGUAGES, RTL, switchLanguage, t, type Key } from '../strings'
import Data from './settings/Data'
import Models from './settings/Models'
import Shortcuts from './settings/Shortcuts'

const PANELS = ['general', 'appearance', 'language', 'models', 'memory', 'data', 'shortcuts', 'about'] as const
type Panel = (typeof PANELS)[number]
export const last = { panel: 'general' as Panel } // the rail's Settings comes back here this session

/** A Select over [value, label key] pairs, saved to one setting. */
function Choice({ k, options, fallback }: { k: string; options: [string, Key][]; fallback: string }) {
  const [prefs] = usePrefs()
  const value = String(prefs[k] ?? fallback)
  return (
    <div style={{ width: 240 }}>
      <K.Select label="" options={options.map(([, l]) => t(l))} value={t(options.find(([v]) => v === value)?.[1] ?? options[0][1])}
        onChange={(v) => setPref(k, options.find(([, l]) => t(l) === v)?.[0] ?? fallback)} />
    </div>
  )
}
function Switch({ k, fallback, label }: { k: string; fallback: boolean; label: string }) {
  const [prefs] = usePrefs()
  return <K.Toggle label={label} on={(prefs[k] as boolean | undefined) ?? fallback} onToggle={(v) => setPref(k, v)} />
}
function Seg({ k, options, fallback, label }: { k: string; options: [string, Key][]; fallback: string; label: string }) {
  const [prefs] = usePrefs()
  const value = String(prefs[k] ?? fallback)
  return <K.Segmented label={label} size="sm" options={options.map(([, l]) => t(l))} value={t(options.find(([v]) => v === value)?.[1] ?? options[0][1])}
    onChange={(v) => setPref(k, options.find(([, l]) => t(l) === v)?.[0] ?? fallback)} />
}

export default function Settings() {
  const asked = useParams().panel as Panel
  const panel: Panel = PANELS.includes(asked) ? asked : 'general'
  last.panel = panel
  return (
    <main className="app__main" aria-label={t('set.nav')} style={{ gap: 24 }}>
      <h1 className="pg-title">{t('set.nav')}</h1>
      <div className="set">
        <K.SideNav label={t('set.nav')} active={t(`set.n.${panel}` as Key)}
          items={PANELS.map((p) => ({ label: t(`set.n.${p}` as Key), href: `/settings/${p}` }))}
          footer={<K.TextLink href="/settings/about">{t('set.n.new')}</K.TextLink>} />
        <div className="set__panel">
          {panel === 'general' && <General />}
          {panel === 'appearance' && <Appearance />}
          {panel === 'language' && <Language />}
          {panel === 'models' && <Models />}
          {panel === 'memory' && <Memory />}
          {panel === 'data' && <Data />}
          {panel === 'shortcuts' && <Shortcuts />}
          {panel === 'about' && <About />}
        </div>
      </div>
    </main>
  )
}

function General() {
  const { items } = useLibrary()
  const [prefs] = usePrefs()
  const personas = items.filter(isPersona)
  const persona = prefs.persona as number | undefined
  const options: [number | null, string][] = [...personas.map((p) => [p.id, p.name] as [number, string]), [null, t('g.director')]]
  const [advanced, setAdvanced] = useState(() => { try { return localStorage.getItem('kataki.composer.advanced') === '1' } catch { return false } })
  return (
    <>
      <K.SettingsSection title={t('g.start')}>
        <K.SettingsRow title={t('g.openTo')}><Choice k="general.openTo" fallback="home" options={[['home', 'g.openTo.home'], ['last', 'g.openTo.last']]} /></K.SettingsRow>
        <K.SettingsRow title={t('g.autosave')} description={t('g.autosaveSub')}><K.StatePill tone="ok">{t('g.always')}</K.StatePill></K.SettingsRow>
        <K.SettingsRow title={t('g.history')}><Choice k="general.editHistoryDays" fallback="30" options={[['30', 'g.history.30'], ['90', 'g.history.90'], ['forever', 'g.history.forever']]} /></K.SettingsRow>
        <K.SettingsRow title={t('g.updates')}><Choice k="general.updates" fallback="weekly" options={[['weekly', 'g.updates.weekly'], ['daily', 'g.updates.daily'], ['never', 'g.updates.never']]} /></K.SettingsRow>
      </K.SettingsSection>
      <K.SettingsSection title={t('g.window')}>
        <K.SettingsRow title={t('g.startup')}>
          <K.Toggle label={t('g.startup')} on={!!prefs['general.startup']} disabled={!window.kataki?.startup}
            onToggle={(v) => { setPref('general.startup', v); window.kataki?.startup?.(v) }} />
        </K.SettingsRow>
        <K.SettingsRow title={t('g.close')}><Choice k="general.closeAction" fallback="quit" options={[['quit', 'g.close.quit'], ['tray', 'g.close.tray']]} /></K.SettingsRow>
        <K.SettingsRow title={t('g.usage')} description={t('g.usageSub')}><K.StatePill tone="muted">{t('g.notCollected')}</K.StatePill></K.SettingsRow>
      </K.SettingsSection>
      <K.SettingsSection title={t('g.stories')}>
        <K.SettingsRow title={t('g.persona')} description={t('g.personaSub')}>
          <div style={{ width: 240 }}>
            <K.Select label="" options={options.map(([, l]) => l)} value={options.find(([id]) => id === (persona ?? null))?.[1] ?? options[0]?.[1]}
              onChange={(v) => setPref('persona', options.find(([, l]) => l === v)?.[0] ?? null)} />
          </div>
        </K.SettingsRow>
        <K.SettingsRow title={t('g.mode')}>
          <Choice k="story.composerMode" fallback="Auto" options={[['Auto', 'mode.auto'], ['Say', 'mode.say'], ['Do', 'mode.do'], ['Whisper', 'mode.whisper'], ['Think', 'mode.think'], ['Narrate', 'mode.narrate']]} />
        </K.SettingsRow>
        <K.SettingsRow title={t('g.hears')} description={t('g.hearsSub')}>
          <K.Toggle label={t('g.hears')} on={advanced} onToggle={(v) => { setAdvanced(v); try { localStorage.setItem('kataki.composer.advanced', v ? '1' : '0') } catch { /* for this session */ } }} />
        </K.SettingsRow>
        <K.SettingsRow title={t('g.speed')}>
          <Choice k="reply_speed" fallback="normal" options={[['slow', 'g.speed.slow'], ['normal', 'g.speed.normal'], ['fast', 'g.speed.fast'], ['instant', 'g.speed.instant']]} />
        </K.SettingsRow>
      </K.SettingsSection>
    </>
  )
}

function Appearance() {
  const [prefs] = usePrefs()
  const theme = String(prefs['appearance.theme'] ?? 'night')
  return (
    <>
      <K.SettingsSection title={t('ap.theme')}>
        <div className="row" style={{ gap: 14 }}>
          {([['night', 'ap.night', 'ap.nightNote'], ['day', 'ap.day', 'ap.dayNote'], ['system', 'ap.system', 'ap.systemNote']] as const).map(([v, n, note]) => (
            <K.ThemeTile key={v} variant={v} name={t(n)} note={t(note)} selected={theme === v} onClick={() => setPref('appearance.theme', v)} />
          ))}
        </div>
      </K.SettingsSection>
      <K.SettingsSection title={t('ap.text')}>
        <K.SettingsRow title={t('ap.text')} description={t('ap.textSub')}>
          <Seg k="appearance.textSize" fallback="100" label={t('ap.text')} options={[['100', 'ap.t100'], ['125', 'ap.t125'], ['150', 'ap.t150']]} />
        </K.SettingsRow>
        <K.SettingsRow title={t('ap.motion')}>
          <Choice k="appearance.motion" fallback="system" options={[['system', 'ap.motion.system'], ['reduce', 'ap.motion.reduce'], ['full', 'ap.motion.full']]} />
        </K.SettingsRow>
        <K.SettingsRow title={t('ap.stars')}><Switch k="appearance.stars" fallback label={t('ap.stars')} /></K.SettingsRow>
        <K.SettingsRow title={t('ap.font')}>
          <Choice k="appearance.storyFont" fallback="newsreader" options={[['newsreader', 'ap.font.newsreader'], ['figtree', 'ap.font.figtree'], ['atkinson', 'ap.font.atkinson']]} />
        </K.SettingsRow>
        <K.SettingsRow title={t('ap.contrast')} description={t('ap.contrastSub')}><Switch k="appearance.contrast" fallback={false} label={t('ap.contrast')} /></K.SettingsRow>
      </K.SettingsSection>
      <K.Callout title={t('ap.fixed')}>{t('ap.fixedBody')}</K.Callout>
    </>
  )
}

function Language() {
  return (
    <>
      <K.SettingsSection title={t('la.title')}>
        <div className="row row--wrap" style={{ gap: 12 }}>
          {[...new Set(['en', 'ar', ...Object.keys(LANGUAGES)])].map((code) => {
            const done = code === 'en' ? 1 : complete(code)
            const pct = Math.floor(done * 100)
            const status = done >= 1 ? t('la.complete') : pct === 0 ? t('la.notStarted') : t('la.partly', { n: pct })
            return (
              <K.LanguageTile key={code} name={new Intl.DisplayNames([code], { type: 'language' }).of(code) ?? code} lang={code} rtl={RTL.has(code)}
                status={RTL.has(code) ? t('la.rtlStatus', { status }) : status} selected={code === lang} disabled={done < 0.95}
                onClick={() => code !== lang && switchLanguage(code)} />
            )
          })}
        </div>
        <K.SettingsRow title={t('la.mirror')}><K.StatePill tone="muted">{t('la.auto')}</K.StatePill></K.SettingsRow>
        <K.SettingsRow title={t('la.clock')}><Choice k="language.clock" fallback="12" options={[['12', 'la.12'], ['24', 'la.24']]} /></K.SettingsRow>
        <K.SettingsRow title={t('la.help')} description={t('la.helpSub')}><span /></K.SettingsRow>
      </K.SettingsSection>
      <K.Callout title={t('la.restart')}>{t('la.restartBody')}</K.Callout>
    </>
  )
}

function Memory() {
  const navigate = useNavigate()
  const [stories] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const lastStory = stories?.[0]
  return (
    <>
      <K.SettingsSection title={t('set.n.memory')}>
        <K.SettingsRow title={t('me.fade')}><Seg k="memory.fade" fallback="lifelike" label={t('me.fade')} options={[['fast', 'me.fast'], ['lifelike', 'me.lifelike'], ['slow', 'me.slow'], ['never', 'me.never']]} /></K.SettingsRow>
        <K.SettingsRow title={t('me.wrong')}><Switch k="memory.canBeWrong" fallback label={t('me.wrong')} /></K.SettingsRow>
        <K.SettingsRow title={t('me.doubt')}><Switch k="memory.canDoubt" fallback label={t('me.doubt')} /></K.SettingsRow>
        <K.SettingsRow title={t('me.thinking')}><Seg k="memory.thinking" fallback="some" label={t('me.thinking')} options={[['none', 'me.think.none'], ['some', 'me.think.some'], ['lot', 'me.think.lot']]} /></K.SettingsRow>
        <K.SettingsRow title={t('me.hearing')}><Seg k="memory.hearing" fallback="real" label={t('me.hearing')} options={[['real', 'me.hearing.real'], ['all', 'me.hearing.all']]} /></K.SettingsRow>
        <K.SettingsRow title={t('me.meaning')} description={t('me.meaningSub')}><Switch k="memory.byMeaning" fallback label={t('me.meaning')} /></K.SettingsRow>
        <K.SettingsRow title={t('me.replyLength')}><Seg k="reply_length" fallback="medium" label={t('me.replyLength')} options={[['short', 'me.short'], ['medium', 'me.medium'], ['long', 'me.long']]} /></K.SettingsRow>
      </K.SettingsSection>
      <K.Callout tone="warm" title={t('me.engineNote')}>{t('me.engineNoteBody')}</K.Callout>
      <K.Callout icon="layers" title={t('me.callout')}
        action={lastStory ? <K.Button size="sm" onClick={() => navigate(`/story/${lastStory.id}?backstage=0`)}>{t('me.open')}</K.Button> : undefined} />
    </>
  )
}

function About() {
  const [health] = useLoad(() => api<{ version: string }>('/health'), [])
  const os = navigator.userAgent.includes('Windows') ? 'Windows' : navigator.userAgent.includes('Mac') ? 'macOS' : 'Linux'
  return (
    <>
      <K.Panel>
        <div className="col" style={{ gap: 10 }}>
          <span className="pg-title" style={{ fontSize: 26 }}>{t('ab.identity')}</span>
          <span className="t-meta">{t('ab.version', { v: health?.version ?? '…', os })}</span>
          <div className="row" style={{ gap: 8 }}>
            <K.Button size="sm" disabled>{t('ab.check')}</K.Button>
          </div>
          <span className="t-faint">{t('ab.upToDate')}</span>
        </div>
      </K.Panel>
      <K.SettingsSection title={t('ab.tell')}>
        <div className="row" style={{ gap: 8 }}>
          <K.Button size="sm" href="/settings/about#feedback">{t('ab.feedback')}</K.Button>
          <K.Button size="sm" variant="ghost" href="/settings/about#bug">{t('ab.bug')}</K.Button>
          <K.Button size="sm" variant="ghost" href="/settings/about#suggest">{t('ab.suggest')}</K.Button>
        </div>
      </K.SettingsSection>
      <K.SettingsSection title={t('ab.licences')}>
        <K.SettingsRow title={t('ab.fonts')} description={t('ab.fontsBody')}><span /></K.SettingsRow>
      </K.SettingsSection>
    </>
  )
}
