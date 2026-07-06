#!/usr/bin/env python3
"""
snap_timestamps.py — Snap each example sentence's `time` to the REAL timestamp
where that phrase actually appears in the transcript.

THIS IS THE MOST IMPORTANT FEATURE. Hand-written example times are guesses and
will jump to the wrong place. This aligns every example to the true subtitle time
by finding the corpus segment sharing the longest contiguous phrase.

Usage:
  python3 snap_timestamps.py expressions.json corpus.json [--out expressions.snapped.json]

Where:
  expressions.json = [{ "name","level","meaning","freq","explanation",
                        "examples":[{"fr","zh","time"}...] }, ...]
  corpus.json      = [{ "fr","zh","time" }, ...]  (the merged/translated subtitle corpus)

Behavior:
  - For each example, find corpus line with the longest contiguous shared word-run.
  - Require >=2-word contiguous match; else keep the original time (fallback).
  - Then sorts expressions by first example time (video order) and re-ids 1..N.
  - Prints a report so you can eyeball any low-confidence matches.
"""
import sys, json, re, argparse, unicodedata

def norm(s):
    s = s.lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def snap(example_fr, ncorpus, fallback):
    ewords = norm(example_fr).split()
    best_t, best_len = fallback, 0
    for t, ct in ncorpus:
        maxrun = 0
        for start in range(len(ewords)):
            for L in range(len(ewords) - start, 0, -1):
                phrase = " ".join(ewords[start:start + L])
                if len(phrase) < 8:
                    continue
                if phrase in ct:
                    maxrun = max(maxrun, L)
                    break
        if maxrun > best_len:
            best_len, best_t = maxrun, t
    return (best_t, best_len)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("expressions")
    ap.add_argument("corpus")
    ap.add_argument("--out", default="expressions.snapped.json")
    a = ap.parse_args()

    with open(a.expressions, encoding="utf-8") as f:
        exprs = json.load(f)
    with open(a.corpus, encoding="utf-8") as f:
        corpus = json.load(f)
    ncorpus = [(c["time"], norm(c["fr"])) for c in corpus]

    low_conf = []
    for it in exprs:
        for ex in it.get("examples", []):
            t, conf = snap(ex["fr"], ncorpus, ex.get("time", 0))
            if conf >= 2:
                ex["time"] = t
            else:
                low_conf.append((it.get("name", "?"), ex["fr"][:50]))

    def first_time(it):
        return min((ex["time"] for ex in it.get("examples", [])), default=99999)
    exprs.sort(key=first_time)
    for i, it in enumerate(exprs):
        it["id"] = i + 1

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(exprs, f, ensure_ascii=False, indent=2)

    print(f"OK: snapped {len(exprs)} expressions -> {a.out}")
    for it in exprs:
        ts = ",".join(str(ex["time"]) for ex in it["examples"])
        print(f"  [{first_time(it):>4}s] {it.get('level','?'):3} {it.get('name','?')}  -> {ts}")
    if low_conf:
        print("\nLOW-CONFIDENCE (kept original time, verify manually):", file=sys.stderr)
        for name, snippet in low_conf:
            print(f"  - {name}: {snippet}", file=sys.stderr)

if __name__ == "__main__":
    main()
