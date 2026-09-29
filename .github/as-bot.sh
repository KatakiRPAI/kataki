#!/usr/bin/env bash
# Run one git or gh command as the agents' bot account, so its PRs are the bot's and the owner
# can approve them:  bash .github/as-bot.sh git push -u origin HEAD
#                    bash .github/as-bot.sh gh pr create --fill
# The bot's token comes from gh's keyring; the owner's own git and gh logins stay untouched.
set -euo pipefail
bot=${KATAKI_BOT:-QaisBOT}
GH_TOKEN=$(gh auth token --user "$bot" 2>/dev/null) || {
  echo "the bot isn't logged in: the owner runs 'gh auth login' as $bot once, then 'gh auth switch --user QaisZAK'" >&2
  exit 1
}
export GH_TOKEN
if [ "${1:-}" = git ]; then
  shift
  exec git -c credential.helper= -c 'credential.helper=!gh auth git-credential' "$@"
fi
exec "$@"
