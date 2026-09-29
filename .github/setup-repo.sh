#!/usr/bin/env bash
# Creates the public GitHub repo and applies Phase 1 of docs/specs/2026-09-29-repo-infrastructure.md.
# Run once, from the repo root, as an org owner:   bash .github/setup-repo.sh <org>
# Safe to re-run: every step checks or overwrites instead of duplicating.
set -euo pipefail
org=${1:?usage: setup-repo.sh <org>}
repo="$org/kataki"

git diff --quiet && git diff --cached --quiet || { echo "commit or stash first"; exit 1; }

# the org name goes into the one file that links to the repo
if grep -q KATAKI_ORG .github/ISSUE_TEMPLATE/config.yml; then
  sed -i "s/KATAKI_ORG/$org/" .github/ISSUE_TEMPLATE/config.yml
  git commit -qm "chore: point the issue form at $repo" .github/ISSUE_TEMPLATE/config.yml
fi

gh repo view "$repo" >/dev/null 2>&1 || gh repo create "$repo" --public \
  --description "AI roleplay with characters who remember, feel and change. Desktop app + website." \
  --disable-wiki
git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$repo.git"
git push -u origin main

# merge settings: squash only, PR title as the commit (Conventional Commits), tidy branches
gh api -X PATCH "repos/$repo" --silent --input - <<'JSON'
{"allow_squash_merge": true, "allow_merge_commit": false, "allow_rebase_merge": false,
 "squash_merge_commit_title": "PR_TITLE", "squash_merge_commit_message": "PR_BODY",
 "delete_branch_on_merge": true, "allow_auto_merge": true, "allow_update_branch": true,
 "has_projects": false,
 "security_and_analysis": {"secret_scanning": {"status": "enabled"},
                           "secret_scanning_push_protection": {"status": "enabled"}}}
JSON

gh api -X PUT "repos/$repo/vulnerability-alerts" --silent               # Dependabot alerts
gh api -X PUT "repos/$repo/automated-security-fixes" --silent           # Dependabot security PRs
gh api -X PUT "repos/$repo/private-vulnerability-reporting" --silent    # SECURITY.md's route

# the main ruleset (PR required, CI green, code owners, squash only, no force-push)
id=$(gh api "repos/$repo/rulesets" --jq '.[] | select(.name=="main") | .id')
if [ -n "$id" ]; then
  gh api -X PUT "repos/$repo/rulesets/$id" --input .github/rulesets/main.json --silent
else
  gh api -X POST "repos/$repo/rulesets" --input .github/rulesets/main.json --silent
fi

for l in "bug:d73a4a" "idea:a2eeef" "beta-feedback:7057ff" "agent-ready:0e8a16" "needs-human:fbca04"; do
  gh label create "${l%%:*}" --color "${l##*:}" --repo "$repo" --force >/dev/null
done

echo "done: https://github.com/$repo"
echo "check: a direct 'git push origin main' is now rejected; open a PR to see the required checks."
