# Security

## Reporting a problem

Report it privately through GitHub: the repo's **Security** tab › **Report a vulnerability**.
Please don't open a public issue. You'll get a reply within a week, and credit in the release
notes if you want it.

## What we support

The latest stable desktop release, the current beta, and the Kataki website. Older desktop
versions get fixes by updating.

## What matters most

- **API keys.** The desktop app keeps them in the OS keychain, never in the library file. Any
  path that writes a key to disk, a log or a network request it wasn't meant for is a bug.
- **The local engine.** It binds 127.0.0.1 and wants a per-launch bearer token on every API
  call. A way for a web page or another user on the machine to reach it is a bug.
- **Imports.** Character cards, chats, lorebooks and `.kataki` libraries come from strangers.
  Anything in one that runs code, reads files outside the library or escapes the preview is a
  bug.
- **The website.** One user reading or spending another's library or credit is the worst bug
  there is.
