#!/usr/bin/env bash
# Đồng bộ toàn bộ dữ liệu dự án .13 <-> .14. Không in nội dung secret ra stdout.
set -u
REMOTE=thienhongan0908@192.168.1.14
RBASE=/home/thienhongan0908/lan-a2a/SYNC
BASE="$HOME/lan-a2a/SYNC"
LOCAL_MIRROR="$BASE/from-13"
REMOTE_MIRROR="$BASE/from-14"
SECRETS="$BASE/SECRETS"

mkdir -p "$LOCAL_MIRROR" "$REMOTE_MIRROR" "$SECRETS/from-13" "$SECRETS/from-14"
printf '*\n!.gitignore\n' > "$BASE/.gitignore"
ssh -o BatchMode=yes "$REMOTE" "mkdir -p '$RBASE/from-13' '$RBASE/from-14' '$RBASE/SECRETS/from-14'"

EX=(--exclude '.git' --exclude '.venv' --exclude 'node_modules' --exclude '__pycache__' --exclude '*.pyc' --exclude '*.zip' --exclude '*.tar.gz' --exclude 'Godot_v*' --exclude 'o3de/source' --exclude '.hermes/cache')

echo '=== PUSH local .13 -> .14 ==='
for src in game-survival ai-film-studio lan-a2a engines projects-registry.json auto-social-content-2026.md; do
  [ -e "$HOME/$src" ] || continue
  rsync -a "${EX[@]}" "$HOME/$src" "$REMOTE:$RBASE/from-13/" && echo "push $src OK" || echo "push $src FAIL"
done

echo '=== PULL remote .14 -> .13 ==='
for src in game-survival AI-FILM-STUDIO lan-a2a; do
  mkdir -p "$REMOTE_MIRROR/$src"
  rsync -a "${EX[@]}" "$REMOTE:/home/thienhongan0908/$src/" "$REMOTE_MIRROR/$src/" && echo "pull $src OK" || echo "pull $src FAIL"
done

echo '=== SECRETS local -> bundle ==='
for f in .lan_token .hermes/.env .hermes/config.yaml .hermes/scripts/a2a_hosts.json; do
  [ -f "$HOME/$f" ] || continue
  out="$SECRETS/from-13/$(printf '%s' "$f" | tr '/' '_')"
  cp -p "$HOME/$f" "$out" && chmod 600 "$out" && echo "secret ${f##*/} bundled"
done
find "$HOME/.hermes" -maxdepth 2 -type f \( -iname '*token*' -o -name '.env*' \) -print0 2>/dev/null |
while IFS= read -r -d '' f; do
  out="$SECRETS/from-13/extra_$(basename "$f")"
  cp -p "$f" "$out" && chmod 600 "$out"
done

echo '=== SECRETS remote -> bundle ==='
ssh "$REMOTE" 'find "$HOME/.hermes" -maxdepth 2 -type f \( -iname "*token*" -o -name ".env*" \) -printf "%P\n" 2>/dev/null' |
while IFS= read -r f; do
  [ -n "$f" ] || continue
  out="$SECRETS/from-14/$(printf '%s' "$f" | tr '/' '_')"
  rsync -a "$REMOTE:/home/thienhongan0908/.hermes/$f" "$out" && chmod 600 "$out" && echo "remote secret ${f##*/} bundled"
done

echo '=== VERIFY ==='
echo -n 'local-mirror files: '; find "$LOCAL_MIRROR" -type f | wc -l
echo -n 'remote-mirror files: '; find "$REMOTE_MIRROR" -type f | wc -l
echo -n 'local secrets: '; find "$SECRETS/from-13" -type f | wc -l
echo -n 'remote secrets: '; find "$SECRETS/from-14" -type f | wc -l
du -sh "$BASE" 2>/dev/null
echo '=== DISCOVER AFTER SCRUB ==='
(cd "$HOME/lan-a2a" && .venv/bin/python -m lan_a2a.cli discover 2>&1 | grep -E 'OK|UNREACH|FAIL' || true)
