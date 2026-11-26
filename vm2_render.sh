set -e
mkdir -p "$HOME/renders"
cat > "$HOME/renders/frame.html" <<'HTML'
<!doctype html><meta charset="utf-8">
<style>body{margin:0;background:radial-gradient(circle at 30% 20%,#123b57,#050c14);color:#dff9ff;font:700 52px system-ui;display:grid;place-items:center;height:100vh}
small{display:block;font:400 22px system-ui;color:#7fd6e8;margin-top:14px}</style>
<div>AI FILM STUDIO<small>render worker frame · chromium headless</small></div>
HTML
chromium --headless --no-sandbox --disable-gpu --hide-scrollbars --window-size=1280,720 \
  --screenshot="$HOME/renders/frame.png" "file://$HOME/renders/frame.html" >/dev/null 2>&1
stat -c 'VM2_RENDER bytes=%s' "$HOME/renders/frame.png"
printf '{"role":"render","host":"%s","frames":["frame.png"],"time":"%s"}\n' "$(hostname)" "$(date -u +%FT%TZ)" > "$HOME/renders/latest.json"
