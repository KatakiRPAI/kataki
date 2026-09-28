# Errors

62 codes. This file is generated from `errors.json`; edit the JSON, not this file. Board M4 shows every one, and the boards named in each entry show it in place.

## Rules

- **One code, one surface, one wording.** The surface decides where it shows; the title and body are the exact strings (templates with `{data}`); actions are the exact button labels in order, primary first.
- **Order of a message**: what happened · what is safe · what to do. Never blame the user. Never “oops”, never an exclamation mark.
- **The code** ends the message in small mono (`.code` / Alert `code`), so a bug report can quote it, on every surface except `inline` field errors (there it is only logged). OS or HTTP details (`ECONNREFUSED`, `401`) go next to it verbatim. The crash dialog shows its reference `KT-CRASH-{nnnn}` instead.
- **Variants**: a few codes have different wording where the context differs (first run vs Settings vs the Home banner). `variants` in the JSON gives the exact copy per board; everywhere else use the main copy.
- **Errors never delete.** Recovery copies, moves aside, or queues. Nothing the user made is removed by an error path.
- **Unknown errors** fall to `UNKNOWN` through a React error boundary per route and per overlay, with a reference `KT-ERR-{nnnn}` written to the log.
- **Logging**: every raised code is logged with its data (never keys, never story text unless the user attaches it). Backstage › logs shows the session’s lines.

## Surfaces

| Surface | Component | Where | Blocks? |
|---|---|---|---|
| page | `Alert` in a full page | replaces the route content (A2, N1, N2, N3) | yes, until an action or the condition clears |
| dialog | `Dialog` tone bad | over the route | yes |
| statusline | `StatusLine` tone bad/warm | inside the setting or panel it concerns | no |
| callout | `Callout` tone bad/warm | inside a flow (first run, import) | no |
| inline | field `error` / `hint` | under the field; on blur after first edit, and on submit | blocks submit only |
| line | `.lineerr` in the chat | where the reply would have been | no; the composer stays usable |
| toast | `Toast` tone bad | bottom centre / above the composer | no |
| banner | `StatusLine` under the top bar | Home | no |

## Catalogue

### Opening and the library

#### `LIBRARY_UNREADABLE`

- **Surface**: page · **Drawn in context on**: OpeningFailed · **Appears on**: OpeningFailed
- **Title**: Kataki can’t read your library.
- **Body**: The file {file} in {folder} didn’t open. It may be damaged, or another program may be holding it. Nothing has been changed or deleted.
- **Actions**: **Restore {backupWhen}’s backup** · Open the folder · Try again · Start with an empty library
- **Recovery**: Never overwrite the unreadable file. Restoring copies the backup beside it as library.restored-{date} and opens that; the damaged file moves to library/damaged/. “Restore…” shows only when a backup exists.

#### `LIBRARY_LOCKED`

- **Surface**: page · **Drawn in context on**: AlreadyOpen · **Appears on**: AlreadyOpen
- **Title**: Kataki is already open
- **Body**: Another Kataki window has your library open. Two at once could overwrite each other, so this one waits.
- **Actions**: **Switch to it** · Quit this one
- **Recovery**: Single-instance lock. Second launch focuses the first window and exits; this page shows only if the first window doesn’t answer within 3 s.

#### `LIBRARY_NEWER`

- **Surface**: page · **Drawn in context on**: M4 only · **Appears on**: OpeningFailed
- **Title**: This library is from a newer Kataki
- **Body**: It was last saved by Kataki {libraryVersion}. This is {appVersion}. Update to open it. Nothing was changed.
- **Actions**: **Check for updates** · Open the last backup
- **Recovery**: Read-only refusal. Never migrate downwards.

#### `LIBRARY_MIGRATION_FAILED`

- **Surface**: page · **Drawn in context on**: M4 only · **Appears on**: OpeningFailed
- **Title**: Kataki couldn’t bring your library up to date
- **Body**: Your library is exactly as it was. A copy was made before trying: {copyPath}.
- **Actions**: **Report a bug** · Show the copy · Quit
- **Recovery**: Migrations run in one transaction on a copy; the original is only replaced after success.

#### `STORY_UNREADABLE`

- **Surface**: page · **Drawn in context on**: M4 only · **Appears on**: /story/:id, in place of the Scene
- **Title**: Part of {story} didn’t read back
- **Body**: {goodLines} lines are fine; {badLines} couldn’t be read. The rest of your library isn’t affected.
- **Actions**: **Open what’s readable** · Restore it from a backup · Report a bug
- **Recovery**: Shown in place of the Scene. Open what’s readable marks the damaged rows and never deletes them.

#### `APP_CRASHED`

- **Surface**: dialog · **Drawn in context on**: CrashRecovered · **Appears on**: CrashRecovered
- **Title**: Kataki closed unexpectedly
- **Body**: Last time, Kataki stopped at {time} while {name} was answering. Everything up to {his} last finished line is safe. The line {he} was writing is gone.
- **Actions**: **Continue the story** · Report it · Stay here
- **Recovery**: The dialog shows the crash reference (“Crash log saved · KT-CRASH-{nnnn}”) instead of this code. The crash log stays local until attached to a bug report.

#### `DISK_FULL`

- **Surface**: page · **Drawn in context on**: DiskFull · **Appears on**: DiskFull
- **Title**: There’s no room left on {drive}
- **Body**: Kataki needs about {neededMb} MB to keep saving. Your stories are safe up to {lastSavedAt}. Lines you write now wait here until there’s room. Don’t close Kataki until this goes away.
- **Actions**: **Try again** · Show what uses space · Move the library…
- **Recovery**: Queue writes in memory, retry every 30 s, never drop a line.

#### `DISK_READONLY`

- **Surface**: page · **Drawn in context on**: DiskFull · **Appears on**: DiskFull
- **Title**: Kataki can’t write to its folder
- **Body**: {libraryFolder} is read-only. Your stories are safe; nothing new can be saved until Kataki can write there.
- **Actions**: **Try again** · Move the library… · Show the folder
- **Recovery**: Same queue as DISK_FULL.

### Getting a model

#### `DOWNLOAD_NETWORK`

- **Surface**: callout · **Drawn in context on**: FirstRunDownload · **Appears on**: FirstRunDownload
- **Title**: The download stopped
- **Body**: This computer lost its internet connection at {doneGb} GB. It picks up from there.
- **Actions**: **Resume**
- **Recovery**: HTTP range resume. Auto-retry 3 times at 5 s, 20 s, 60 s before showing.

#### `DOWNLOAD_DISK`

- **Surface**: callout · **Drawn in context on**: FirstRunDownload · **Appears on**: FirstRunDownload
- **Title**: Not enough room on {drive}
- **Body**: The model needs {needGb} GB and {freeGb} GB is free. Free some space, or keep models on another drive.
- **Actions**: **Choose a folder**
- **Recovery**: Checked before starting and again every 100 MB.

#### `DOWNLOAD_CHECKSUM`

- **Surface**: callout · **Drawn in context on**: FirstRunDownload · **Appears on**: FirstRunDownload
- **Title**: The file didn’t check out
- **Body**: What arrived doesn’t match what was sent, so Kataki threw it away. Downloading again usually fixes it.
- **Actions**: **Download again**
- **Recovery**: SHA-256 against the published manifest. Partial file deleted (it is Kataki’s own temp file, not the user’s).

#### `HARDWARE_TOO_SMALL`

- **Surface**: callout · **Drawn in context on**: M4 only · **Appears on**: FirstRun
- **Title**: This computer may be slow with Kataki’s model
- **Body**: kataki-small-3b wants {needGb} GB of free memory and {freeGb} GB is free. It will run, slowly. A server on another computer or an online model will be faster.
- **Actions**: **Download anyway** · Use an online model
- **Recovery**: Warning only; never blocks.

### Model servers

#### `SERVER_NO_MODEL`

- **Surface**: statusline · **Drawn in context on**: FirstRunServer · **Appears on**: FirstRunServer, SetModelsFailed
- **Title**: Connected, but no model loaded
- **Body**: Load a model in {server}, then test again.
- **Actions**: **Test again**
- **Recovery**: Poll every 10 s while the page is open.

#### `SERVER_UNREACHABLE`

- **Surface**: statusline · **Drawn in context on**: FirstRunServer, HomeOffline, SetModels · **Appears on**: FirstRunServer, SetModelsFailed
- **Title**: Nothing answered
- **Body**: Nothing answered at {address} after {seconds} s. Is the server running, and is that its port?
- **Actions**: **Test again** · Look again
- **Variant on SetModelsFailed**: title “Nothing answered at {address}” · body “Tested {ago}: connection refused. Is {server} still running?” · actions Test again
- **Variant on HomeOffline** (banner): title “Nobody is answering” · body “{server} at {address} stopped answering {ago}. You can read, edit and export everything; new replies wait until it is back.” · actions What happened
- **Recovery**: detail is the OS error, e.g. ECONNREFUSED, verbatim.

#### `SERVER_NOT_COMPATIBLE`

- **Surface**: statusline · **Drawn in context on**: FirstRunServer · **Appears on**: SetModelsFailed
- **Title**: It answered, but not like a model server
- **Body**: The address is right but it isn’t an OpenAI-style API.
- **Actions**: **Edit address**
- **Recovery**: Probe GET /v1/models then POST /v1/chat/completions with max_tokens 1.

#### `SERVER_UNAUTHORIZED`

- **Surface**: statusline · **Drawn in context on**: FirstRunServer · **Appears on**: SetModelsFailed
- **Title**: It wants a key
- **Body**: The server said 401. Add its key above.
- **Recovery**: Key stored with the OS keychain (safeStorage).

#### `SERVER_TIMEOUT`

- **Surface**: statusline · **Drawn in context on**: M4 only · **Appears on**: SetModelsFailed
- **Title**: {server} took too long
- **Body**: No answer in {seconds} s. Big models on small computers can be slow. You can raise the limit in Advanced.
- **Actions**: **Test again** · Open Advanced
- **Recovery**: Default timeout 60 s to first token.

#### `MODEL_GONE`

- **Surface**: page · **Drawn in context on**: ModelGone · **Appears on**: ModelGone
- **Title**: Nobody is home to answer.
- **Body**: Kataki was talking to {server} {where} at {address}, and it stopped answering {ago}. Your story is safe: every line was written to disk as it arrived.
- **Actions**: **Try again** · Use Kataki’s own model instead · Open Settings
- **Recovery**: Shown over a story only after 3 failed retries. Replies catch up in order when it returns.

#### `CONTEXT_TOO_SMALL`

- **Surface**: statusline · **Drawn in context on**: M4 only · **Appears on**: SetModelsAdvanced
- **Title**: This model holds {modelCtx} tokens
- **Body**: A scene needs about {needCtx}. Kataki drops the oldest lines first. A model with 16k or more fits better.
- **Actions**: **Choose another model**
- **Recovery**: Warning only. History is the only segment trimmed.

### Online models

#### `API_KEY_INVALID`

- **Surface**: statusline · **Drawn in context on**: FirstRunOnline, SetModels · **Appears on**: FirstRunOnline, SetModelsFailed, AddApi
- **Title**: Key not valid
- **Body**: {provider} said this key isn’t valid. Copy it again from {keysPage}; it starts with {prefix}.
- **Actions**: **Test again**
- **Variant on SetModelsFailed**: title “{provider} turned the key down” · body “It answered 401. The key may have been revoked or mistyped.” · actions Replace the key
- **Recovery**: Never log the key; show only its last 4.

#### `API_NO_CREDIT`

- **Surface**: statusline · **Drawn in context on**: FirstRunOnline · **Appears on**: SetModelsFailed
- **Title**: No credit left on this key
- **Body**: Top up at the service, then test again.
- **Actions**: **Test again** · Use Kataki’s own model
- **Recovery**: Stops retrying until the user acts.

#### `API_RATE_LIMITED`

- **Surface**: line · **Drawn in context on**: FirstRunOnline · **Appears on**: SetModelsFailed, SceneFailed
- **Title**: Too many requests
- **Body**: The service asked Kataki to slow down. It tries again in {seconds} s.
- **Actions**: **Try now**
- **Recovery**: Honour Retry-After; else 5, 15, 45 s.

#### `API_UNREACHABLE`

- **Surface**: line · **Drawn in context on**: FirstRunOnline · **Appears on**: SetModelsFailed, SceneFailed
- **Title**: Couldn’t reach the service
- **Body**: No internet, or the address is wrong. Local models still work.
- **Actions**: **Try again** · Use Kataki’s own model
- **Recovery**: Retry every 10 s while a reply is waiting.

#### `API_MODEL_NOT_FOUND`

- **Surface**: statusline · **Drawn in context on**: M4 only · **Appears on**: SetModelsFailed
- **Title**: {provider} doesn’t offer {model} any more
- **Body**: Pick another from the list.
- **Actions**: **Choose a model**
- **Recovery**: Refresh the model list from the provider.

#### `API_REFUSED`

- **Surface**: line · **Drawn in context on**: M4 only · **Appears on**: SceneFailed
- **Title**: {provider} refused this reply
- **Body**: It returned a refusal instead of a line. Nothing in the story changed. Try again, change your line, or use a local model.
- **Actions**: **Try again** · Edit my line · Use Kataki’s own model
- **Recovery**: Detected by provider finish_reason / error type only; never by reading the text.

### In a story

#### `REPLY_UNREACHABLE`

- **Surface**: line · **Drawn in context on**: Backstage, Scene · **Appears on**: SceneFailed
- **Title**: {name}’s reply didn’t arrive
- **Body**: {server} stopped answering at {time}. Your line is saved; nothing was lost. Kataki will try again by itself when the server is back.
- **Actions**: **Try again** · Use Kataki’s own model · Edit my line
- **Recovery**: Composer stays usable; new lines queue.

#### `REPLY_TIMEOUT`

- **Surface**: line · **Drawn in context on**: M4 only · **Appears on**: SceneFailed
- **Title**: {name} took too long
- **Body**: No words after {seconds} s. Your line is saved.
- **Actions**: **Try again** · Edit my line
- **Recovery**: Stop the stream, keep partial text as a hidden take.

#### `REPLY_EMPTY`

- **Surface**: line · **Drawn in context on**: M4 only · **Appears on**: SceneFailed
- **Title**: {name}’s reply came back empty
- **Body**: The model returned nothing. Some models do this now and then.
- **Actions**: **New take**
- **Recovery**: Auto-retry once silently before showing.

#### `REPLY_CUT_OFF`

- **Surface**: line · **Drawn in context on**: M4 only · **Appears on**: SceneFailed
- **Title**: {name}’s reply was cut short
- **Body**: It reached the {limit}-token reply limit.
- **Actions**: **Continue it** · Keep it
- **Recovery**: finish_reason = length. Continue uses Ctrl J.

#### `MEMORY_READER_FAILED`

- **Surface**: statusline · **Drawn in context on**: M4 only · **Appears on**: BackstageLogs
- **Title**: {name} didn’t take in the last {count} lines
- **Body**: The memory reader timed out. The story is fine; {name} just won’t remember those lines until it runs again.
- **Actions**: **Run it again**
- **Recovery**: Shown in Backstage and as a dot on the widget. Retries on the next turn.

#### `NARRATOR_FAILED`

- **Surface**: toast · **Drawn in context on**: Toasts · **Appears on**: Toasts
- **Title**: The narrator couldn’t add a line
- **Actions**: **Try again**
- **Recovery**: Story continues without it.

#### `TIMESKIP_FAILED`

- **Surface**: dialog · **Drawn in context on**: M4 only · **Appears on**: SceneTimeSkip
- **Title**: Time didn’t pass
- **Body**: Fading memories didn’t finish, so Kataki put everything back to {fromTime}. Nothing changed.
- **Actions**: **Try again** · Cancel
- **Recovery**: Time skip is one transaction: clock, presence, memory fade.

#### `LINE_SAVE_FAILED`

- **Surface**: line · **Drawn in context on**: M4 only · **Appears on**: SceneFailed
- **Title**: Your last line isn’t saved yet
- **Body**: Kataki couldn’t write it to the library. It stays here and saves as soon as it can.
- **Actions**: **Try again** · Copy the line
- **Recovery**: Leads to DISK_FULL / DISK_READONLY if the cause is the disk.

#### `MUSIC_UNSUPPORTED`

- **Surface**: toast · **Drawn in context on**: Toasts · **Appears on**: Toasts, SceneMusic
- **Title**: That file won’t play
- **Body**: Kataki plays mp3, ogg and wav. This is .{ext}.
- **Actions**: **Choose another**
- **Recovery**: File not copied into the library.

#### `MUSIC_MISSING`

- **Surface**: statusline · **Drawn in context on**: M4 only · **Appears on**: SceneMusic
- **Title**: {file} isn’t where it was
- **Body**: It was moved or deleted. Pick it again, or choose another track.
- **Actions**: **Find it** · Choose another
- **Recovery**: Uploaded tracks are copied into the library, so this only happens to linked files.

### Characters and portraits

#### `IMPORT_NO_CARD`

- **Surface**: inline · **Drawn in context on**: ImportCards · **Appears on**: ImportCards
- **Title**: No character card inside this picture.
- **Recovery**: The row shows the Skipped pill. Other files in the batch continue.

#### `IMPORT_UNSUPPORTED_VERSION`

- **Surface**: inline · **Drawn in context on**: M4 only · **Appears on**: ImportCards
- **Title**: {file} uses a card format Kataki can’t read yet
- **Body**: It says {spec}. Kataki reads chara_card_v1, v2 and v3.
- **Actions**: **Skip it**
- **Recovery**: Log the spec string.

#### `IMPORT_DUPLICATE`

- **Surface**: inline · **Drawn in context on**: M4 only · **Appears on**: ImportCards
- **Title**: {file} · someone called {name} is already here
- **Actions**: **Keep both** · Replace the one here · Skip this card
- **Recovery**: The three choices are a Select on the row. Replace keeps the existing character’s memories and stories.

#### `PORTRAIT_UNSUPPORTED`

- **Surface**: callout · **Drawn in context on**: NewCharacter · **Appears on**: PortraitPicker
- **Title**: That file isn’t a picture Kataki can use
- **Body**: PNG, JPG or WEBP, up to 20 MB.
- **Actions**: **Choose a file**
- **Recovery**: Sniff bytes, not the extension. Shown in Crop and focus (F5) after a file is chosen.

#### `PORTRAIT_TOO_LARGE`

- **Surface**: callout · **Drawn in context on**: M4 only · **Appears on**: PortraitPicker
- **Title**: That picture is too big
- **Body**: PNG, JPG or WEBP, up to 20 MB. This one is {sizeMb} MB.
- **Actions**: **Choose a file**
- **Recovery**: Accepted images are re-encoded to 1024 px WebP.

### Forms

#### `NAME_REQUIRED`

- **Surface**: inline · **Drawn in context on**: NewCharacter · **Appears on**: NewCharacterErrors
- **Title**: Give them a name. It’s the one thing Kataki can’t guess.
- **Recovery**: Validated on Create and on blur after the first edit. Other forms use the same code with their own line: “Give it a name.” (place, plot, book, group), “Give yourself a name.” (persona).

#### `NAME_TAKEN`

- **Surface**: inline · **Drawn in context on**: M4 only · **Appears on**: NewCharacterErrors
- **Title**: There’s already a {name}
- **Body**: Two is fine. Add something to tell them apart.
- **Recovery**: Warning, not blocking.

#### `FIELD_TOO_LONG`

- **Surface**: inline · **Drawn in context on**: M4 only · **Appears on**: NewCharacterErrors
- **Title**: Keep it under {max} characters
- **Body**: This is {count}.
- **Recovery**: Blocks Save for that field only.

#### `GREETING_REQUIRED`

- **Surface**: inline · **Drawn in context on**: NewCharacter · **Appears on**: NewCharacterErrors
- **Title**: Write how they say hi. It’s their first line in every new story.
- **Recovery**: Validated on Create and on blur after the first edit.

#### `CONFIRM_MISMATCH`

- **Surface**: inline · **Drawn in context on**: SetData · **Appears on**: DeleteSomething
- **Title**: That doesn’t match yet.
- **Recovery**: Case-sensitive, trimmed. The confirm button stays disabled until it matches.

### World

#### `DELETE_IN_USE`

- **Surface**: dialog · **Drawn in context on**: M4 only · **Appears on**: World delete confirms (PlaceMenu, PlotMenu)
- **Title**: {name} is in {count} stories
- **Body**: Those stories keep their own copy. Deleting only removes it from World.
- **Actions**: **Delete** · Cancel
- **Recovery**: Not an error state; a guard shown inside the delete confirm.

### Data

#### `EXPORT_WRITE_FAILED`

- **Surface**: toast · **Drawn in context on**: Toasts · **Appears on**: Toasts, ExportStory, ExportAll
- **Title**: Couldn’t save to that folder
- **Body**: {folder} is read-only or full.
- **Actions**: **Choose a folder**
- **Recovery**: No partial file left behind (write to temp, then rename).

#### `BACKUP_FAILED`

- **Surface**: statusline · **Drawn in context on**: M4 only · **Appears on**: Backups
- **Title**: The {time} backup didn’t happen
- **Body**: Couldn’t write to {folder}. The last good one is from {lastBackupAt}.
- **Actions**: **Back up now** · Choose a folder
- **Recovery**: Also sets the Settings dot on the Rail.

#### `BACKUP_RESTORE_FAILED`

- **Surface**: dialog · **Drawn in context on**: M4 only · **Appears on**: Backups
- **Title**: That backup couldn’t be opened
- **Body**: It may be damaged. Your current library wasn’t touched.
- **Actions**: **Choose another**
- **Recovery**: Restore opens a copy; never overwrites the live library until it opens.

### Settings

#### `SHORTCUT_TAKEN`

- **Surface**: callout · **Drawn in context on**: SetShortcuts · **Appears on**: RemapShortcut
- **Title**: {keys} already {does}
- **Body**: Use it for {action} instead, and leave {other} without a shortcut?
- **Actions**: **Use it here** · Pick other keys
- **Recovery**: Use it here unassigns the other action.

#### `SHORTCUT_RESERVED`

- **Surface**: inline · **Drawn in context on**: M4 only · **Appears on**: RemapShortcut
- **Title**: Windows keeps {keys} for itself
- **Body**: Pick other keys.
- **Recovery**: Reserved list: Alt F4, Ctrl Alt Del, Win + anything, Alt Tab, F11 handled by Kataki itself.

#### `LANGUAGE_MODEL_WEAK`

- **Surface**: callout · **Drawn in context on**: M4 only · **Appears on**: SetLanguage
- **Title**: {model} writes {language} less well
- **Body**: Characters may slip into English. Kataki’s interface is fully in {language} either way.
- **Actions**: **Choose another model**
- **Recovery**: Driven by a static per-model language list shipped with Kataki.

### Updates

#### `UPDATE_UNREACHABLE`

- **Surface**: statusline · **Drawn in context on**: M4 only · **Appears on**: UpdateStates
- **Title**: Couldn’t reach [UPDATE HOST]
- **Body**: You’re offline or it’s down. Kataki works fine without it.
- **Actions**: **Try again**
- **Recovery**: Silent when automatic; shown only on a manual check.

#### `UPDATE_VERIFY_FAILED`

- **Surface**: statusline · **Drawn in context on**: SetAbout · **Appears on**: UpdateStates
- **Title**: The update didn’t install
- **Body**: The file didn’t match what was published, so nothing was changed. You’re still on {appVersion}.
- **Actions**: **Try again**
- **Recovery**: Signature and hash checked before install.

#### `UPDATE_INSTALL_FAILED`

- **Surface**: statusline · **Drawn in context on**: M4 only · **Appears on**: UpdateStates
- **Title**: {version} didn’t install
- **Body**: Windows stopped the installer. You’re still on {appVersion}.
- **Actions**: **Try again** · Report a bug
- **Recovery**: Installer exit code goes into the log.

### Feedback

#### `FEEDBACK_OFFLINE`

- **Surface**: inline · **Drawn in context on**: Feedback, Toasts · **Appears on**: Feedback, Toasts
- **Title**: Couldn’t send it
- **Body**: This computer isn’t reaching the internet. The report is saved and goes the next time Kataki is online, unless you cancel it.
- **Actions**: **Try again** · Copy instead · Cancel it
- **Recovery**: Saved to the Outbox; sent once when online; toast.feedback.queued confirms after the dialog closes.

#### `FEEDBACK_TOO_LARGE`

- **Surface**: inline · **Drawn in context on**: M4 only · **Appears on**: BugReport
- **Title**: The attachments are too big
- **Body**: Reports can carry {maxMb} MB. The log is {logMb} MB; Kataki can keep just the last hour.
- **Actions**: **Keep the last hour** · Remove the log
- **Recovery**: Trim happens on a copy.

#### `FEEDBACK_FAILED`

- **Surface**: inline · **Drawn in context on**: M4 only · **Appears on**: Feedback
- **Title**: It didn’t send
- **Body**: [FEEDBACK HOST] answered {status}. Your text is kept here.
- **Actions**: **Try again** · Copy it
- **Recovery**: Never lose the text.

### Search

#### `SEARCH_INDEXING`

- **Surface**: statusline · **Drawn in context on**: M4 only · **Appears on**: Search
- **Title**: Search is still reading your library
- **Body**: {done} of {total} lines. Some results may be missing until it’s done.
- **Recovery**: Index built in a worker, resumable.

### System

#### `OFFLINE`

- **Surface**: banner · **Drawn in context on**: M4 only · **Appears on**: Home (when the computer has no network and an online model is chosen)
- **Title**: You’re offline
- **Body**: Local models work as always. Online models, updates and feedback wait.
- **Recovery**: From navigator.onLine plus a probe; banner clears itself.

#### `RENDERER_FALLBACK`

- **Surface**: toast · **Drawn in context on**: Toasts · **Appears on**: any route
- **Title**: The graphics driver restarted
- **Body**: Kataki is drawing without the GPU for now. Restart to go back.
- **Actions**: **Restart**
- **Recovery**: Electron gpu-process-crashed.

#### `UNKNOWN`

- **Surface**: dialog · **Drawn in context on**: M4 only · **Appears on**: any route or overlay
- **Title**: Something went wrong
- **Body**: Kataki doesn’t know what happened here. Your work is saved. Reference {errorRef}.
- **Actions**: **Report a bug** · Close
- **Recovery**: React error boundary per route and per overlay. errorRef format KT-ERR-{4 digits}.
