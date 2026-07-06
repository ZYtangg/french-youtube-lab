#!/usr/bin/env python3
"""
fetch_transcript.py — Fetch a YouTube video's metadata + transcript via Supadata.

Handles the key gotcha: a video's metadata may report `transcriptLanguages: []`
yet still have an (auto-generated) transcript retrievable with `lang=fr`.
So we ALWAYS try the direct lang request, never trust the metadata list.

Usage:
  python3 fetch_transcript.py VIDEO_ID [--lang fr] [--key SUPADATA_KEY] [--out DIR]

Env:
  SUPADATA_API_KEY  (used if --key not given)

Outputs (into --out, default current dir):
  <VIDEO_ID>.meta.json        raw video metadata
  <VIDEO_ID>.transcript.json  raw transcript segments (offset in ms)

Exit codes:
  0 ok | 2 no transcript | 3 live stream | 4 network/api error
"""
import sys, os, json, argparse, urllib.parse, urllib.request

API = "https://api.supadata.ai/v1/youtube"

def _get(url, key, timeout=60):
    req = urllib.request.Request(url, headers={"x-api-key": key})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--lang", default="fr")
    ap.add_argument("--key", default=os.environ.get("SUPADATA_API_KEY", ""))
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    if not a.key:
        print("ERROR: no API key. Pass --key or set SUPADATA_API_KEY.", file=sys.stderr)
        sys.exit(4)
    vid = a.video_id
    os.makedirs(a.out, exist_ok=True)

    # 1) metadata (best-effort, non-fatal)
    meta = {}
    try:
        st, body = _get(f"{API}/video?id={urllib.parse.quote(vid)}", a.key, 30)
        if st == 200:
            meta = json.loads(body)
            with open(os.path.join(a.out, f"{vid}.meta.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"WARN: metadata fetch failed: {e}", file=sys.stderr)

    # 2) transcript — ALWAYS try direct lang request (do NOT trust transcriptLanguages)
    watch = f"https://www.youtube.com/watch?v={vid}"
    url = f"{API}/transcript?url={urllib.parse.quote(watch, safe='')}&lang={a.lang}"
    try:
        st, body = _get(url, a.key, 90)
    except Exception as e:
        print(f"ERROR: transcript request failed: {e}", file=sys.stderr)
        sys.exit(4)

    try:
        data = json.loads(body)
    except Exception:
        print(f"ERROR: non-JSON response: {body[:200]}", file=sys.stderr)
        sys.exit(4)

    if isinstance(data, dict) and data.get("error"):
        det = (data.get("details") or "") + " " + (data.get("message") or "")
        if "live" in det.lower():
            print("LIVE_STREAM: transcript only available after the stream ends.", file=sys.stderr)
            sys.exit(3)
        print(f"NO_TRANSCRIPT: {det.strip()}", file=sys.stderr)
        sys.exit(2)

    segs = data.get("content") if isinstance(data, dict) else data
    if not segs:
        print("NO_TRANSCRIPT: empty content.", file=sys.stderr)
        sys.exit(2)

    with open(os.path.join(a.out, f"{vid}.transcript.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    title = meta.get("title", "(unknown)")
    dur = meta.get("duration", "?")
    print(f"OK: {vid} | {len(segs)} segments | {dur}s | {title}")
    # Heuristic auto-caption warning: no punctuation across many segments
    joined = " ".join(s.get("text", "") for s in segs[:30])
    if joined and joined.count(".") + joined.count("?") + joined.count("!") <= 1:
        print("NOTE: transcript looks auto-generated (no punctuation) — likely ASR, quality may be low.")

if __name__ == "__main__":
    main()
