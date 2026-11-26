set -e
mkdir -p "$HOME/encode" "$HOME/health"
ffmpeg -y -f lavfi -i testsrc=size=1280x720:rate=24 -t 2 -pix_fmt yuv420p \
  "$HOME/encode/sample.mp4" >/dev/null 2>&1
dur=$(ffprobe -show_entries format=duration -of csv=p=0 "$HOME/encode/sample.mp4" 2>/dev/null | tr -d '\r\n')
stat -c 'VM3_ENCODE bytes=%s' "$HOME/encode/sample.mp4"
echo "VM3_ENCODE duration=$dur"
if [ ! -d "$HOME/lan-a2a/.git" ]; then
  git clone --depth 1 https://github.com/thienhongan0794-stack/lan-a2a.git "$HOME/lan-a2a" >/dev/null 2>&1 || echo BACKUP_CLONE_FAIL
fi
printf '{"role":"encode+backup","host":"%s","duration":"%s","free":"%s","time":"%s"}\n' \
  "$(hostname)" "$dur" "$(df -h "$HOME" | tail -1 | awk '{print $4}')" "$(date -u +%FT%TZ)" > "$HOME/health/status.json"
echo VM3_OK
