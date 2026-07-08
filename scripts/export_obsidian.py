#!/usr/bin/env python3
"""
export_obsidian.py — Export mined expressions + vocab into an Obsidian vault as Markdown notes.

Each expression / word gets its OWN note file. Running this again for a different video
does NOT create duplicates: if the same expression/word already has a note, the new
video's examples are merged into it (grouped by source video), instead of overwriting
or duplicating the file.

Merging is index-driven, not text-parsing-driven: a small JSON index file is kept inside
the vault (`<vault>/.french-lab-index.json`). On every run we load it, merge in the new
data, write it back, then FULLY REGENERATE the .md file for every touched entry from the
index. This means the Markdown is always a clean, deterministic render of the index —
never a fragile "append to existing text" operation that could corrupt a note.

Usage:
  python3 export_obsidian.py \
      --vault /path/to/ObsidianVault \
      --video-id VIDEO_ID \
      --video-title "视频标题" \
      --channel "频道名" \
      --expressions work/expressions.snapped.json \
      --vocab work/vocab.json \
      [--expr-folder "法语表达"] [--vocab-folder "法语单词"]

Notes:
  - Re-running with the same --video-id updates that video's entry in place (idempotent),
    it does not append a second copy.
  - Matching across videos is accent/case-insensitive (so "Ça veut dire quoi" and
    "ça veut dire quoi" are treated as the same expression), but the FIRST spelling seen
    becomes the canonical filename/heading — later runs never rename an existing note.
"""
import sys, os, json, re, argparse, unicodedata

INDEX_NAME = ".french-lab-index.json"


def norm_key(s):
    s = s.lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def safe_filename(s):
    s = s.strip()
    s = re.sub(r'[\\/:*?"<>|]', "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return (s or "untitled")[:120]


def get_text(ex):
    """Source-language text field. Supports fr/es/text so this script travels with forks."""
    return ex.get("fr") or ex.get("es") or ex.get("text") or ""


def format_time(seconds):
    seconds = int(seconds or 0)
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


def yt_link(video_id, time=None):
    url = f"https://www.youtube.com/watch?v={video_id}"
    if time is not None:
        url += f"&t={int(time)}s"
    return url


def load_index(vault):
    p = os.path.join(vault, INDEX_NAME)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"expressions": {}, "vocab": {}}


def save_index(vault, index):
    p = os.path.join(vault, INDEX_NAME)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def merge_expressions(index, exprs, video):
    touched = set()
    for it in exprs:
        key = norm_key(it["name"])
        entry = index["expressions"].setdefault(key, {
            "name": it["name"],
            "level": it.get("level", "?"),
            "meaning": it.get("meaning", ""),
            "explanation": it.get("explanation", ""),
            "sources": {},
        })
        entry["sources"][video["video_id"]] = {
            "video_id": video["video_id"],
            "video_title": video["video_title"],
            "channel": video.get("channel", ""),
            "examples": [
                {"text": get_text(ex), "zh": ex.get("zh", ""), "time": ex.get("time", 0)}
                for ex in it.get("examples", [])
            ],
        }
        touched.add(key)
    return touched


def merge_vocab(index, vocab, video):
    touched = set()
    for it in vocab:
        key = norm_key(it["word"])
        entry = index["vocab"].setdefault(key, {
            "word": it["word"],
            "zh": it.get("zh", ""),
            "sources": {},
        })
        entry["sources"][video["video_id"]] = {
            "video_id": video["video_id"],
            "video_title": video["video_title"],
            "channel": video.get("channel", ""),
            "example": it.get("example", ""),
        }
        touched.add(key)
    return touched


def render_expression_md(entry):
    tags = ["expression", str(entry.get("level", "?")).lower()]
    fm = [
        "---",
        "type: expression",
        f"level: {entry.get('level', '?')}",
        f"meaning: \"{entry.get('meaning', '').replace(chr(34), chr(39))}\"",
        f"aliases: [\"{entry['name'].replace(chr(34), chr(39))}\"]",
        f"tags: [{', '.join(tags)}]",
        "---",
        "",
    ]
    body = [f"# {entry['name']}", "", f"> {entry.get('meaning', '')}", "", entry.get("explanation", ""), "", "## 例句（按视频来源）", ""]
    for src in sorted(entry["sources"].values(), key=lambda s: s.get("video_title", "")):
        link = yt_link(src["video_id"])
        title = src.get("video_title") or src["video_id"]
        channel = f" · {src['channel']}" if src.get("channel") else ""
        body.append(f"### 来自：[{title}]({link}){channel}")
        body.append("")
        for ex in src.get("examples", []):
            t = ex.get("time", 0)
            body.append(f"- 🇫🇷 {ex.get('text', '')}")
            body.append(f"  🇨🇳 {ex.get('zh', '')}")
            body.append(f"  ⏱ [{format_time(t)}]({yt_link(src['video_id'], t)})")
        body.append("")
    return "\n".join(fm + body).rstrip() + "\n"


def render_vocab_md(entry):
    fm = [
        "---",
        "type: vocab",
        f"meaning: \"{entry.get('zh', '').replace(chr(34), chr(39))}\"",
        "tags: [vocab]",
        "---",
        "",
    ]
    body = [f"# {entry['word']}", "", f"> {entry.get('zh', '')}", "", "## 例句（按视频来源）", ""]
    for src in sorted(entry["sources"].values(), key=lambda s: s.get("video_title", "")):
        link = yt_link(src["video_id"])
        title = src.get("video_title") or src["video_id"]
        channel = f" · {src['channel']}" if src.get("channel") else ""
        body.append(f"- **[{title}]({link}){channel}**：{src.get('example', '')}")
    body.append("")
    return "\n".join(fm + body).rstrip() + "\n"


def write_notes(vault, folder, keys, store, render):
    dirpath = os.path.join(vault, folder)
    os.makedirs(dirpath, exist_ok=True)
    written = []
    for key in keys:
        entry = store[key]
        name_field = entry.get("name") or entry.get("word")
        fname = safe_filename(name_field) + ".md"
        path = os.path.join(dirpath, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(render(entry))
        written.append(fname)
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, help="Path to your Obsidian vault (or any folder)")
    ap.add_argument("--video-id", required=True)
    ap.add_argument("--video-title", required=True)
    ap.add_argument("--channel", default="")
    ap.add_argument("--expressions", required=True, help="expressions.snapped.json")
    ap.add_argument("--vocab", required=True, help="vocab.json")
    ap.add_argument("--expr-folder", default="法语表达")
    ap.add_argument("--vocab-folder", default="法语单词")
    a = ap.parse_args()

    os.makedirs(a.vault, exist_ok=True)
    with open(a.expressions, encoding="utf-8") as f:
        exprs = json.load(f)
    with open(a.vocab, encoding="utf-8") as f:
        vocab = json.load(f)

    video = {"video_id": a.video_id, "video_title": a.video_title, "channel": a.channel}

    index = load_index(a.vault)
    expr_keys = merge_expressions(index, exprs, video)
    vocab_keys = merge_vocab(index, vocab, video)
    save_index(a.vault, index)

    written_exprs = write_notes(a.vault, a.expr_folder, expr_keys, index["expressions"], render_expression_md)
    written_vocab = write_notes(a.vault, a.vocab_folder, vocab_keys, index["vocab"], render_vocab_md)

    print(f"OK: {len(written_exprs)} expression note(s) -> {a.vault}/{a.expr_folder}/")
    print(f"OK: {len(written_vocab)} vocab note(s) -> {a.vault}/{a.vocab_folder}/")
    print(f"Index updated: {os.path.join(a.vault, INDEX_NAME)}")


if __name__ == "__main__":
    main()
