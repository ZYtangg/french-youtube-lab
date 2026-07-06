#!/usr/bin/env python3
"""
build_html.py — Assemble the final self-contained learning HTML from data files.

Fills assets/template.html placeholders with real data. Handles the classic
"double-bracket" pitfall safely by injecting valid JSON directly.

Usage:
  python3 build_html.py \
      --template assets/template.html \
      --video-id VIDEO_ID \
      --title "地道法语表达实验室 — <video title>" \
      --header "<header line>" \
      --expressions expressions.snapped.json \
      --vocab vocab.json \
      --corpus corpus.json \
      --aspect 16/9 \
      --out french-lab-VIDEO_ID.html

Notes:
  --aspect: use "16/9" for normal videos, "9/16" for Shorts (vertical).
            When 9/16, the wrapper is auto-constrained so it isn't full-screen.
  All JSON files must be UTF-8. French accents are embedded directly (not escaped).
"""
import sys, json, argparse, re

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--video-id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--header", required=True)
    ap.add_argument("--expressions", required=True)
    ap.add_argument("--vocab", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--list-label", default="地道表达 · 按视频顺序")
    ap.add_argument("--aspect", default="16/9", help="16/9 normal, 9/16 Shorts")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    html = open(a.template, encoding="utf-8").read()
    exprs = load(a.expressions)
    vocab = load(a.vocab)
    corpus = load(a.corpus)

    # ensure sequential ids on expressions (defensive)
    for i, it in enumerate(exprs):
        it["id"] = i + 1

    def esc(s):  # for HTML attribute/text placeholders (not JSON)
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    html = html.replace("{{VIDEO_ID}}", a.video_id)
    html = html.replace("{{PAGE_TITLE}}", esc(a.title))
    html = html.replace("{{HEADER}}", esc(a.header))
    html = html.replace("{{LIST_LABEL}}", esc(a.list_label))
    html = html.replace("{{VIDEO_ASPECT}}", a.aspect)
    html = html.replace("{{GRAMMARS_JSON}}", json.dumps(exprs, ensure_ascii=False, indent=2))
    html = html.replace("{{VOCAB_JSON}}", json.dumps(vocab, ensure_ascii=False, indent=2))
    html = html.replace("{{CORPUS_JSON}}", json.dumps(corpus, ensure_ascii=False, indent=2))

    # Shorts: constrain the wrapper so a 9/16 video isn't full-screen tall.
    if a.aspect.strip() == "9/16":
        html = html.replace(
            ".video-wrapper {\n    width: 100%;\n    align-self: stretch;",
            ".video-wrapper {\n    align-self: center;\n    height: 46vh;\n    max-height: 420px;"
        )

    # Safety: no leftover placeholders, no double-bracket
    leftovers = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if leftovers:
        print(f"ERROR: unfilled placeholders: {set(leftovers)}", file=sys.stderr)
        sys.exit(1)
    for nm in ["const grammars =", "const DEFAULT_VOCAB =", "const subtitleCorpus ="]:
        i = html.find(nm) + len(nm)
        while i < len(html) and html[i] == " ":
            i += 1
        if not (html[i] == "[" and html[i + 1] != "["):
            print(f"ERROR: malformed array after {nm}", file=sys.stderr)
            sys.exit(1)

    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK: wrote {a.out} ({len(html)} chars) | {len(exprs)} expressions, {len(vocab)} vocab, {len(corpus)} corpus lines")
    print("NEXT: deploy to an HTTPS host (not localhost) so YouTube embed is trusted.")

if __name__ == "__main__":
    main()
