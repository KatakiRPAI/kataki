// Settings › Profiles (desktop): each profile is a name and the folder that holds its library
// (docs/specs/2026-10-02-profiles-and-accounts.md P1). The shell keeps the list and asks for folders.
import { useState } from 'react'
import { K } from '../../ds'
import { useLoad } from '../../hooks'
import { Overlay, toast } from '../../overlay'
import { t } from '../../strings'

export default function Profiles() {
  const shell = window.kataki!
  const [state, reload] = useLoad(() => shell.profiles!(), [])
  const [naming, setNaming] = useState<DesktopProfile | 'new'>()
  const [forgetting, setForgetting] = useState<DesktopProfile>()
  const add = async (name: string) => {
    const made = await shell.profileAdd!(name)
    reload()
    if (made) toast(t('pf.added', { name: made.name }), { icon: 'user', action: t('pf.switch'), onAction: () => shell.profileSwitch!(made.id) }, 8000)
  }
  return (
    <>
      <K.Callout tone="privacy" title={t('pf.what')}>{t('pf.whatBody')}</K.Callout>
      <K.SettingsSection title={t('set.n.profiles')} note={t('pf.note')}>
        {state?.list.map((p) => (
          <K.SettingsRow key={p.id} title={p.name} description={p.folder}>
            <div className="row" style={{ gap: 8 }}>
              {p.id === state.current ? <K.StatePill tone="ok" icon="check">{t('pf.open')}</K.StatePill>
                : <K.Button size="sm" icon="swap" onClick={() => shell.profileSwitch!(p.id)}>{t('pf.switch')}</K.Button>}
              <K.Button size="sm" variant="ghost" onClick={() => setNaming(p)}>{t('pf.rename')}</K.Button>
              {p.id !== state.current && <K.Button size="sm" variant="ghost" onClick={() => setForgetting(p)}>{t('pf.forget')}</K.Button>}
            </div>
          </K.SettingsRow>
        ))}
        <K.SettingsRow title={t('pf.add')} description={t('pf.addSub')}><K.Button size="sm" icon="plus" onClick={() => setNaming('new')}>{t('pf.addBtn')}</K.Button></K.SettingsRow>
      </K.SettingsSection>
      {naming && <Name p={naming === 'new' ? undefined : naming} onClose={() => setNaming(undefined)}
        onSave={(name) => (naming === 'new' ? add(name) : shell.profileRename!(naming.id, name).then(reload))} />}
      {forgetting && (
        <Overlay onClose={() => setForgetting(undefined)}>
          <K.Dialog size="sm" title={t('pf.forgetTitle', { name: forgetting.name })} description={t('pf.forgetBody', { folder: forgetting.folder })} onClose={() => setForgetting(undefined)}
            actions={[<K.Button key="k" variant="ghost" onClick={() => setForgetting(undefined)}>{t('pf.keep')}</K.Button>,
              <K.Button key="f" variant="primary" onClick={() => shell.profileForget!(forgetting.id).then(() => { setForgetting(undefined); reload() })}>{t('pf.forget')}</K.Button>]} />
        </Overlay>
      )}
    </>
  )
}

/** A profile's name: a new one goes on to the shell's folder dialog. */
function Name({ p, onClose, onSave }: { p?: DesktopProfile; onClose: () => void; onSave: (name: string) => void }) {
  const [name, setName] = useState(p?.name ?? '')
  return (
    <Overlay onClose={onClose}>
      <K.Dialog size="sm" icon="user" title={p ? t('pf.renameTitle', { name: p.name }) : t('pf.newTitle')} description={p ? undefined : t('pf.newBody')} onClose={onClose}
        actions={[<K.Button key="c" variant="ghost" onClick={onClose}>{t('ep.cancel')}</K.Button>,
          <K.Button key="s" variant="primary" disabled={!name.trim()} onClick={() => { onSave(name.trim()); onClose() }}>{t(p ? 'ep.save' : 'pf.choose')}</K.Button>]}>
        <K.TextField label={t('pf.name')} required value={name} onChange={setName} max={40} />
      </K.Dialog>
    </Overlay>
  )
}
