// Settings (K1–K18): docs/handoff/kataki-handoff/SCREENS.md › K. Every change saves itself.
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { api, type StorySummary } from '../api'
import { fullName, isPersona } from '../characters'
import { K } from '../ds'
import type { IconName } from '../ds/kataki'
import { openFeedback } from './Feedback'
import Top from './Top'
import { useLibrary, useLoad } from '../hooks'
import { setPref, usePrefs } from '../prefs'
import { complete, lang, LANGUAGES, RTL, switchLanguage, t, type Key } from '../strings'
import { account } from '../online/session'
import Account from './settings/Account'
import Data from './settings/Data'
import { Overlay } from '../overlay'
import Models from './settings/Models'
import Profiles from './settings/Profiles'
import Shortcuts from './settings/Shortcuts'

const ALL = ['general', 'appearance', 'language', 'models', 'memory', 'profiles', 'account', 'data', 'shortcuts', 'about'] as const
type Panel = (typeof ALL)[number]
// Profiles are the desktop shell's (electron/profiles.ts): no list on the web or on one fixed library
// and the account is Kataki online's (the gateway): the desktop has none
const PANELS = ALL.filter((p) => (p !== 'profiles' || !!window.kataki?.profiles) && (p !== 'account' || !!account()))
export const last = { panel: 'general' as Panel } // the rail's Settings comes back here this session

/** A Select over [value, label key] pairs, saved to one setting. */
function Choice({ k, options, fallback, width = 200 }: { k: string; options: [string, Key][]; fallback: string; width?: number }) {
  const [prefs] = usePrefs()
  const value = String(prefs[k] ?? fallback)
  return (
    <div style={{ width }}>
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

const ICONS: Record<Panel, IconName> = { general: 'settings', appearance: 'sun', language: 'globe', models: 'cpu', memory: 'thought', profiles: 'users', account: 'user', data: 'shield', shortcuts: 'key', about: 'help' }

export default function Settings() {
  const asked = useParams().panel as Panel
  const panel: Panel = PANELS.includes(asked) ? asked : 'general'
  last.panel = panel
  return (
    <main className="app__main" aria-label={t('set.nav')} style={{ gap: 24 }}>
      <Top />
      <h1 className="pg-title">{t('set.nav')}</h1>
      {asked && <span className="set__back"><K.TextLink icon="left" href="/settings">{t('set.all')}</K.TextLink></span>}
      <div className={`set${asked ? ' set--open' : ' set--list'}`}>
        <K.SideNav label={t('set.nav')} active={t(`set.n.${panel}` as Key)}
          items={PANELS.map((p) => ({ icon: ICONS[p], label: t(`set.n.${p}` as Key), href: `/settings/${p}` }))}
          footer={<K.TextLink icon="spark" href="/settings/about">{t('set.n.new')}</K.TextLink>} />
        <div className="set__panel">
          {panel === 'general' && <General />}
          {panel === 'appearance' && <Appearance />}
          {panel === 'language' && <Language />}
          {panel === 'models' && <Models />}
          {panel === 'memory' && <Memory />}
          {panel === 'profiles' && <Profiles />}
          {panel === 'account' && <Account />}
          {panel === 'data' && <Data />}
          {panel === 'shortcuts' && <Shortcuts />}
          {panel === 'about' && <About />}
        </div>
      </div>
    </main>
  )
}

const OS = navigator.userAgent.includes('Windows') ? 'win' : navigator.userAgent.includes('Mac') ? 'mac' : 'other'

function General() {
  const { items } = useLibrary()
  const [prefs] = usePrefs()
  const personas = items.filter(isPersona)
  const persona = prefs.persona as number | undefined
  const options: [number | null, string][] = [...personas.map((p) => [p.id, fullName(p)] as [number, string]), [null, t('g.director')]]
  const [advanced, setAdvanced] = useState(() => { try { return localStorage.getItem('kataki.composer.advanced') === '1' } catch { return false } })
  return (
    <>
      <K.SettingsSection title={t('set.n.general')} note={t('g.note')}>
        <K.SettingsRow title={t('g.openTo')} description={t('g.openToSub')}><Choice k="general.openTo" fallback="home" options={[['home', 'g.openTo.home'], ['last', 'g.openTo.last']]} /></K.SettingsRow>
        <K.SettingsRow title={t('g.autosave')} description={t('g.autosaveSub')}><K.StatePill tone="ok" icon="check">{t('g.always')}</K.StatePill></K.SettingsRow>
        <K.SettingsRow title={t('g.history')} description={t('g.historySub')}>
          <div className="row" style={{ gap: 12 }}>
            <Choice k="general.editHistoryDays" fallback="30" width={150} options={[['30', 'g.history.30'], ['90', 'g.history.90'], ['forever', 'g.history.forever']]} />
            <Switch k="general.editHistory" fallback label={t('g.history')} />
          </div>
        </K.SettingsRow>
        {window.kataki && ( // the desktop app's own: online and in a browser there is no app to update, start or close
          <>
            <K.SettingsRow title={t('g.updates')} description={t('g.updatesSub')}><Choice k="general.updates" fallback="weekly" options={[['weekly', 'g.updates.weekly'], ['daily', 'g.updates.daily'], ['never', 'g.updates.never']]} /></K.SettingsRow>
            <K.SettingsRow title={t('g.startup', { os: OS })} description={t('g.startupSub')}>
              <K.Toggle label={t('g.startup', { os: OS })} on={!!prefs['general.startup']} disabled={!window.kataki?.startup}
                onToggle={(v) => { setPref('general.startup', v); window.kataki?.startup?.(v) }} />
            </K.SettingsRow>
            <K.SettingsRow title={t('g.close')} description={t('g.closeSub')}><Choice k="general.closeAction" fallback="quit" options={[['quit', 'g.close.quit'], ['tray', 'g.close.tray']]} /></K.SettingsRow>
          </>
        )}
        <K.SettingsRow title={t('g.usage')} description={t('g.usageSub')}><K.StatePill tone="muted" icon="shield">{t('g.notCollected')}</K.StatePill></K.SettingsRow>
      </K.SettingsSection>
      <K.SettingsSection title={t('g.stories')} note={t('g.storiesNote')}>
        <K.SettingsRow title={t('g.persona')} description={t('g.personaSub')}>
          <div style={{ width: 200 }}>
            <K.Select label="" options={options.map(([, l]) => l)} value={options.find(([id]) => id === (persona ?? null))?.[1] ?? options[0]?.[1]}
              onChange={(v) => setPref('persona', options.find(([, l]) => l === v)?.[0] ?? null)} />
          </div>
        </K.SettingsRow>
        <K.SettingsRow title={t('g.mode')} description={t('g.modeSub')}>
          <Choice k="story.composerMode" fallback="Auto" options={[['Auto', 'mode.auto'], ['Say', 'mode.say'], ['Do', 'mode.do'], ['Whisper', 'mode.whisper'], ['Think', 'mode.think'], ['Narrate', 'mode.narrate']]} />
        </K.SettingsRow>
        <K.SettingsRow title={t('g.hears')} description={t('g.hearsSub')}>
          <K.Toggle label={t('g.hears')} on={advanced} onToggle={(v) => { setAdvanced(v); try { localStorage.setItem('kataki.composer.advanced', v ? '1' : '0') } catch { /* for this session */ } }} />
        </K.SettingsRow>
        <K.SettingsRow title={t('g.speed')} description={t('g.speedSub')}>
          <Choice k="reply_speed" fallback="normal" options={[['slow', 'g.speed.slow'], ['normal', 'g.speed.normal'], ['fast', 'g.speed.fast'], ['instant', 'g.speed.instant']]} />
        </K.SettingsRow>
        <Content />
      </K.SettingsSection>
    </>
  )
}

/** How far stories may go, and what to keep out of them (the engine's [Content] rule, context.py). */
function Content() {
  const [prefs] = usePrefs()
  const level = String(prefs['content.level'] ?? 'mature')
  const [asking, setAsking] = useState(false) // explicit, on a computer with no account that said 18 or older
  const [avoid, setAvoid] = useState(() => ((prefs['content.avoid'] as string[] | undefined) ?? []).join(', '))
  const levels: [string, Key][] = [['gentle', 'g.content.gentle'], ['mature', 'g.content.mature'], ['explicit', 'g.content.explicit']]
  const pick = (v: string) => {
    const to = levels.find(([, l]) => t(l) === v)?.[0] ?? 'mature'
    if (to === 'explicit' && !account() && !prefs['content.adult']) return setAsking(true)
    setPref('content.level', to)
  }
  return (
    <>
      <K.SettingsRow title={t('g.content')} description={t(`g.content.${level}Sub` as Key)}>
        <K.Segmented label={t('g.content')} size="sm" options={levels.map(([, l]) => t(l))} value={t(levels.find(([v]) => v === level)?.[1] ?? 'g.content.mature')} onChange={pick} />
      </K.SettingsRow>
      <K.SettingsRow title={t('g.avoid')} description={t('g.avoidSub')}>
        <div style={{ width: 260 }}>
          <K.TextField label="" value={avoid} placeholder={t('g.avoidHint')}
            onChange={(v) => { setAvoid(v); setPref('content.avoid', v.split(',').map((x) => x.trim()).filter(Boolean).slice(0, 20)) }} />
        </div>
      </K.SettingsRow>
      {asking && (
        <Overlay onClose={() => setAsking(false)}>
          <K.Dialog size="sm" icon="alert" tone="warm" title={t('g.adultTitle')} description={t('g.adultBody')} onClose={() => setAsking(false)}
            actions={[<K.Button key="n" variant="ghost" onClick={() => setAsking(false)}>{t('ep.cancel')}</K.Button>,
              <K.Button key="y" variant="primary" onClick={() => { setPref('content.adult', new Date().toISOString()); setPref('content.level', 'explicit'); setAsking(false) }}>{t('g.adultYes')}</K.Button>]} />
        </Overlay>
      )}
    </>
  )
}

function Appearance() {
  const [prefs] = usePrefs()
  const theme = String(prefs['appearance.theme'] ?? 'night')
  return (
    <>
      <K.SettingsSection title={t('set.n.appearance')} note={t('ap.note')}>
        <div className="set__tiles">
          {([['night', 'ap.night', 'ap.nightNote'], ['day', 'ap.day', 'ap.dayNote'], ['system', 'ap.system', 'ap.systemNote']] as const).map(([v, n, note]) => (
            <K.ThemeTile key={v} variant={v} name={t(n)} note={t(note, { os: OS })} selected={theme === v} onClick={() => setPref('appearance.theme', v)} />
          ))}
        </div>
        <K.SettingsRow title={t('ap.text')} description={t('ap.textSub')}>
          <Seg k="appearance.textSize" fallback="100" label={t('ap.text')} options={[['100', 'ap.t100'], ['125', 'ap.t125'], ['150', 'ap.t150']]} />
        </K.SettingsRow>
        <K.SettingsRow title={t('ap.motion')} description={t('ap.motionSub')}>
          <Choice k="appearance.motion" fallback="system" options={[['system', 'ap.motion.system'], ['reduce', 'ap.motion.reduce'], ['full', 'ap.motion.full']]} />
        </K.SettingsRow>
        <K.SettingsRow title={t('ap.stars')} description={t('ap.starsSub')}><Switch k="appearance.stars" fallback label={t('ap.stars')} /></K.SettingsRow>
        <K.SettingsRow title={t('ap.font')} description={t('ap.fontSub')}>
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
      <K.SettingsSection title={t('set.n.language')} note={t('la.note')}>
        <div className="set__tiles">
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
        <K.SettingsRow title={t('la.mirror')} description={t('la.mirrorSub')}><K.StatePill tone="ok" icon="check">{t('la.auto')}</K.StatePill></K.SettingsRow>
        <K.SettingsRow title={t('la.clock')} description={t('la.clockSub')}><Choice k="language.clock" fallback="12" options={[['12', 'la.12'], ['24', 'la.24']]} /></K.SettingsRow>
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
      <K.SettingsSection title={t('set.n.memory')} note={t('me.note')}>
        <K.SettingsRow title={t('me.fade')} description={t('me.fadeSub')}><Seg k="memory.fade" fallback="lifelike" label={t('me.fade')} options={[['fast', 'me.fast'], ['lifelike', 'me.lifelike'], ['slow', 'me.slow'], ['never', 'me.never']]} /></K.SettingsRow>
        <K.SettingsRow title={t('me.wrong')} description={t('me.wrongSub')}><Switch k="memory.canBeWrong" fallback label={t('me.wrong')} /></K.SettingsRow>
        <K.SettingsRow title={t('me.doubt')} description={t('me.doubtSub')}><Switch k="memory.canDoubt" fallback label={t('me.doubt')} /></K.SettingsRow>
        <K.SettingsRow title={t('me.thinking')} description={t('me.thinkingSub')}><Seg k="memory.thinking" fallback="some" label={t('me.thinking')} options={[['none', 'me.think.none'], ['some', 'me.think.some'], ['lot', 'me.think.lot']]} /></K.SettingsRow>
      </K.SettingsSection>
      <K.Callout tone="warm" title={t('me.engineNote')}>{t('me.engineNoteBody')}</K.Callout>
      <K.SettingsSection title={t('me.notice')}>
        <K.SettingsRow title={t('me.hearing')} description={t('me.hearingSub')}><Choice k="memory.hearing" fallback="real" options={[['real', 'me.hearing.real'], ['all', 'me.hearing.all']]} /></K.SettingsRow>
        <K.SettingsRow title={t('me.meaning')} description={t('me.meaningSub')}><Switch k="memory.byMeaning" fallback label={t('me.meaning')} /></K.SettingsRow>
        <K.SettingsRow title={t('me.replyLength')} description={t('me.replyLengthSub')}><Seg k="reply_length" fallback="medium" label={t('me.replyLength')} options={[['short', 'me.short'], ['medium', 'me.medium'], ['long', 'me.long']]} /></K.SettingsRow>
      </K.SettingsSection>
      <K.Callout title={t('me.callout')} action={lastStory ? <K.Button size="sm" onClick={() => navigate(`/story/${lastStory.id}?backstage=0`)}>{t('me.open')}</K.Button> : undefined}>{t('me.calloutBody')}</K.Callout>
    </>
  )
}

function About() {
  const [health] = useLoad(() => api<{ version: string }>('/health'), [])
  const os = navigator.userAgent.includes('Windows') ? 'Windows' : navigator.userAgent.includes('Mac') ? 'macOS' : 'Linux'
  return (
    <>
      <div className="card ab-id">
        <span className="ab-mark">K</span>
        <div style={{ flex: 1 }}>
          <div className="ab-name">{t('ab.identity')}</div>
          <div className="t-meta">{t('ab.version', { v: health?.version ?? '…', os })}</div>
        </div>
        <K.ButtonGroup>
          <K.Button size="sm" icon="refresh" disabled>{t('ab.check')}</K.Button>
        </K.ButtonGroup>
      </div>
      {account() && ( // design brief 3: a small, friendly way to the free desktop app
        <K.SettingsSection title={t('ab.desktop')}>
          <K.SettingsRow title={t('ab.desktop')} description={t('ab.desktopSub')}><K.Button size="sm" icon="download" href="https://github.com/KatakiRPAI/kataki/releases">{t('ab.desktopGet')}</K.Button></K.SettingsRow>
        </K.SettingsSection>
      )}
      <K.SettingsSection title={t('ab.tell')} note={t('ab.tellNote')}>
        <K.SettingsRow title={t('ab.feedback')} description={t('ab.feedbackSub')}><K.Button size="sm" onClick={() => openFeedback('feedback')}>{t('ab.feedback')}</K.Button></K.SettingsRow>
        <K.SettingsRow title={t('ab.bug')} description={t('ab.bugSub')}><K.Button size="sm" onClick={() => openFeedback('bug')}>{t('ab.bug')}</K.Button></K.SettingsRow>
        <K.SettingsRow title={t('ab.suggest')} description={t('ab.suggestSub')}><K.Button size="sm" onClick={() => openFeedback('suggestion')}>{t('ab.suggest')}</K.Button></K.SettingsRow>
      </K.SettingsSection>
      <K.SettingsSection title={t('ab.licences')}>
        <K.SettingsRow title={t('ab.fonts')} description={t('ab.fontsBody')}><span /></K.SettingsRow>
      </K.SettingsSection>
    </>
  )
}
