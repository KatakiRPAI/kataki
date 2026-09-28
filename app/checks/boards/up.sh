#!/usr/bin/env bash
# Everything the side-by-side check needs, from nothing (Git Bash on Windows, or any bash):
#   bash app/checks/boards/up.sh <scratch dir>
# The dev app on :5174, the fake model on :8099, and four engines with token "dev":
#   :8768 the sample world + fixture.py   :8769 an empty library
#   :8770 a copy of 8768 whose model doesn't answer   :8771 the sample world, no stories yet
# Then: cd app && node checks/boards/jobs.mjs both > jobs.json &&
#       SHOOT_PORT=8768 node node_modules/electron/cli.js checks/boards/shoot.cjs jobs.json out/
set -e
S=${1:?scratch dir}; mkdir -p "$S"
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
PY="$ROOT/engine/.venv/Scripts/python.exe"; [ -x "$PY" ] || PY="$ROOT/engine/.venv/bin/python"
up() { for _ in $(seq 40); do curl -s -o /dev/null "$1" && return; sleep 0.5; done; echo "no answer at $1"; exit 1; }
api() { curl -s -H "Authorization: Bearer dev" -H "content-type: application/json" "$@" >/dev/null; }
engine() { (cd "$ROOT/engine" && KATAKI_TOKEN=dev nohup "$PY" -m kataki serve --db "$S/$1.db" --port "$2" > "$S/engine-$1.log" 2>&1 &); up "http://127.0.0.1:$2/health"; }
connect() { api -X POST -d '{"name":"llama.cpp","base_url":"http://127.0.0.1:8099/v1"}' "http://127.0.0.1:$1/providers"; api -X PUT -d '{"provider_id":1,"model":"fake"}' "http://127.0.0.1:$1/roles/rp"; }
seed() {  # the app's own first run writes the sample world
  echo '[{"id":"seed","board":"FirstRunWho","props":{"theme":"night"},"app":"/welcome/who","js":"await wait(15000)"}]' > "$S/seed.json"
  (cd "$ROOT/app" && SHOOT_PORT=$1 node node_modules/electron/cli.js checks/boards/shoot.cjs "$S/seed.json" "$S/seed-$1" >/dev/null 2>&1)
}

curl -s -o /dev/null http://localhost:5174/ || (cd "$ROOT/app" && nohup corepack pnpm exec vite --port 5174 --strictPort > "$S/vite.log" 2>&1 &)
curl -s -o /dev/null http://127.0.0.1:8099/v1/models || (cd "$ROOT/engine" && nohup "$PY" evals/demo.py serve-model > "$S/model.log" 2>&1 &)
up http://localhost:5174/; up http://127.0.0.1:8099/v1/models

rm -f "$S"/{sample,empty,dead,day1}.db*
engine sample 8768; connect 8768; seed 8768; "$PY" "$ROOT/app/checks/boards/fixture.py" "$S/sample.db"
engine day1 8771; connect 8771; seed 8771
engine empty 8769
"$PY" -c "
import sqlite3, sys
s, d = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2]); s.backup(d)
d.execute(\"UPDATE providers SET base_url='http://127.0.0.1:8081/v1'\"); d.commit()" "$S/sample.db" "$S/dead.db"
engine dead 8770
echo up
