#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
usage:
  yt-dlp-probe.sh metadata <url>
  yt-dlp-probe.sh flat-playlist <playlist-url>
  yt-dlp-probe.sh subs <outdir> <url>
  yt-dlp-probe.sh media <outdir> <url>
EOF
}

if [[ $# -lt 2 ]]; then
  usage
  exit 2
fi

mode="$1"
shift
YTDLP=/home/linuxuser/.local/bin/yt-dlp

run_probe() {
  "$@"
}

run_with_fallback() {
  if run_probe "$@"; then
    return 0
  fi
  if command -v ss >/dev/null 2>&1 && ss -ltn 2>/dev/null | grep -q '127.0.0.1:1080'; then
    ALL_PROXY='socks5h://127.0.0.1:1080' run_probe "$@"
    return 0
  fi
  return 1
}

case "$mode" in
  metadata)
    url="$1"
    run_with_fallback "$YTDLP" --skip-download --dump-single-json "$url"
    exit $?
    ;;
  flat-playlist)
    url="$1"
    run_with_fallback "$YTDLP" --skip-download --flat-playlist --dump-single-json "$url"
    exit $?
    ;;
  subs)
    if [[ $# -lt 2 ]]; then usage; exit 2; fi
    outdir="$1"
    url="$2"
    mkdir -p "$outdir"
    run_with_fallback       "$YTDLP"       --skip-download       --write-auto-sub       --write-sub       --sub-langs 'en.*,en-orig,zh-Hant.*,zh-Hans.*,ja.*,-live_chat'       --convert-subs srt       --no-write-thumbnail       --no-write-comments       --no-write-info-json       --no-write-playlist-metafiles       -o "$outdir/%(id)s.%(ext)s"       "$url"
    find "$outdir" -maxdepth 1 \( -iname '*.srt' -o -iname '*.vtt' -o -iname '*.ttml' -o -iname '*.srv3' -o -iname '*.json3' \) -print | sort
    ;;
  media)
    if [[ $# -lt 2 ]]; then usage; exit 2; fi
    outdir="$1"
    url="$2"
    mkdir -p "$outdir"
    run_with_fallback       "$YTDLP"       --write-auto-sub       --write-sub       --sub-langs 'en.*,en-orig,zh-Hant.*,zh-Hans.*,ja.*,-live_chat'       --convert-subs srt       --no-write-thumbnail       --no-write-comments       --no-write-info-json       --no-write-playlist-metafiles       -o "$outdir/%(id)s.%(ext)s"       "$url"
    find "$outdir" -maxdepth 1 \( -iname '*.mp4' -o -iname '*.webm' -o -iname '*.mkv' -o -iname '*.mov' -o -iname '*.m4a' -o -iname '*.opus' -o -iname '*.srt' -o -iname '*.vtt' -o -iname '*.ttml' -o -iname '*.srv3' -o -iname '*.json3' \) -print | sort
    ;;
  *)
    usage
    exit 2
    ;;
esac
