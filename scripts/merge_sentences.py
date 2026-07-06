#!/usr/bin/env python3
"""
merge_sentences.py — Merge raw transcript segments into readable sentences.

Supadata segments are short fragments with `offset` (ms) + `duration` (ms).
We merge them into sentence-level units using punctuation + gap heuristics,
so the subtitle corpus and example lookups work on natural sentences.

Usage:
  python3 merge_sentences.py <VIDEO_ID>.transcript.json [--out sentences.json]

Output: JSON array of {"fr": "...", "time": <int seconds>}
"""
import sys, json, re, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("--out", default="sentences.json")
    ap.add_argument("--max-len", type=int, default=180)
    ap.add_argument("--gap", type=float, default=1.2, help="hard-break gap in seconds")
    a = ap.parse_args()

    with open(a.transcript, encoding="utf-8") as f:
        data = json.load(f)
    segs = data.get("content") if isinstance(data, dict) else data

    items = []
    for s in segs:
        txt = (s.get("text") or "").strip()
        if not txt:
            continue
        off = s.get("offset", 0) / 1000.0
        dur = s.get("duration", 0) / 1000.0
        items.append({"text": txt, "start": off, "dur": dur})

    sentences = []
    buf, buf_start = "", None
    for i, it in enumerate(items):
        if buf_start is None:
            buf_start = it["start"]
        buf = (buf + " " + it["text"]).strip() if buf else it["text"]
        ends = bool(re.search(r"[.!?…]$", buf.rstrip("\"'» ")))
        nxt_gap = (items[i + 1]["start"] - (it["start"] + it["dur"])) if i + 1 < len(items) else 99
        if ends or nxt_gap > a.gap or len(buf) > a.max_len:
            sentences.append({"fr": buf, "time": int(buf_start)})
            buf, buf_start = "", None
    if buf:
        sentences.append({"fr": buf, "time": int(buf_start)})

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(sentences, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(items)} segments -> {len(sentences)} sentences -> {a.out}")
    for i, s in enumerate(sentences):
        print(f"{i+1}|{s['time']}|{s['fr']}")

if __name__ == "__main__":
    main()
