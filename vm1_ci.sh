set -u
mkdir -p "$HOME/ci-runs"
if [ ! -d "$HOME/game-survival" ]; then
  git clone --depth 1 https://github.com/thienhongan0794-stack/game-survival.git "$HOME/game-survival" >/dev/null 2>&1 || true
fi
if [ -d "$HOME/game-survival/.git" ]; then
  cd "$HOME/game-survival" || exit 1
  git pull --ff-only origin master >/dev/null 2>&1 || true
  commit=$(git rev-parse --short HEAD)
else
  mkdir -p "$HOME/game-survival"
  commit=$(cat "$HOME/game-survival/.commit" 2>/dev/null || echo snapshot)
fi
cd "$HOME/game-survival" || exit 1
node --test web/tests > "$HOME/ci-runs/web.log" 2>&1
rc=$?
grep -E '# (tests|pass|fail)' "$HOME/ci-runs/web.log" > "$HOME/ci-runs/web.summary" || true
printf '{"role":"ci","host":"%s","commit":"%s","web_rc":%d,"time":"%s"}\n' "$(hostname)" "$commit" "$rc" "$(date -u +%FT%TZ)" > "$HOME/ci-runs/ci-latest.json"
echo "VM1_CI commit=$commit rc=$rc"
cat "$HOME/ci-runs/web.summary"
