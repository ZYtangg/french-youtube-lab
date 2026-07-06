# French YouTube Lab 🇫🇷

> Turn any French YouTube video (including Shorts) into a self-contained
> **"native French expressions"** learning webpage — with a synced video player,
> click-to-jump example timestamps, and an auto-filled B1+ vocabulary flashcard deck.

This is an **agent skill** (for Codebuddy / Claude Code style coding agents). Point it at a
French YouTube URL and it produces a single `french-lab-<id>.html` you can open in a browser.

![status](https://img.shields.io/badge/status-stable-brightgreen) ![license](https://img.shields.io/badge/license-MIT-blue)

## What it does

- **Fetches the transcript** via Supadata (works even when a video "has no subtitles" — many
  videos have auto-generated captions that the metadata doesn't list).
- **Mines idiomatic, native expressions** — not textbook grammar drills. Each entry explains
  *why it's idiomatic and how to use it* (colloquialisms, discourse markers, idioms, false
  friends like `supporter` ≠ *support*, word-formation patterns…).
- **Auto-fills a B1+ vocabulary deck** (no level prompts).
- **Snaps every example to its real subtitle timestamp** so click-to-jump lands exactly right.
- **Builds a polished HTML**: scrollable expression list (CEFR-tagged), YouTube IFrame player,
  bilingual subtitle panel with live highlight, and a flashcard wordbook. Handles Shorts (9:16).

## Prerequisites

1. **Supadata API key** — sign up at [supadata.ai](https://supadata.ai) (free tier available).
   Export it: `export SUPADATA_API_KEY=sd_xxx`
2. **Chrome + a signed-in Google account** to *watch* the embedded video. YouTube may show a
   "confirm you're not a bot" gate on restricted networks/VPNs — this affects **any** third-party
   embed (including commercial products), not this tool's code. See
   [`references/embed-stability.md`](references/embed-stability.md).
3. **Deploy to an HTTPS public host** (CloudStudio / Vercel / Cloudflare Pages). Do **not** open via
   `file://` or serve on `localhost` — YouTube trusts HTTPS origins.

## Quick start (manual pipeline)

```bash
# 1. Fetch transcript + metadata
python3 scripts/fetch_transcript.py VIDEO_ID --lang fr --out ./work

# 2. Merge fragments into sentences
python3 scripts/merge_sentences.py work/VIDEO_ID.transcript.json --out work/sentences.json

# 3. (Agent step) Read sentences.json, then write:
#    - work/corpus.json       [{fr, zh, time}]        translate every line
#    - work/expressions.json  [{name,level,meaning,freq,explanation,examples}]
#    - work/vocab.json         [{word, zh, example}]  B1+ only

# 4. Snap example timestamps to real subtitle times (MOST IMPORTANT)
python3 scripts/snap_timestamps.py work/expressions.json work/corpus.json \
    --out work/expressions.snapped.json

# 5. Build the HTML
python3 scripts/build_html.py \
    --template assets/template.html \
    --video-id VIDEO_ID \
    --title "地道法语表达实验室 — <title>" \
    --header "<title> | <channel>" \
    --expressions work/expressions.snapped.json \
    --vocab work/vocab.json \
    --corpus work/corpus.json \
    --aspect 16/9 \
    --out french-lab-VIDEO_ID.html
    # use --aspect 9/16 for Shorts
```

Then deploy `french-lab-VIDEO_ID.html` to an HTTPS host and open it in Chrome.

## Design principle: fast by scripting

Deterministic, mechanical steps (fetch / merge / **timestamp snapping** / HTML assembly) are
**scripts**. The agent only does the creative part (translation + expression mining). This keeps
runs fast and reliable — no multi-round manual fiddling for the boring parts.

## Repo layout

```
french-youtube-lab/
├── SKILL.md                     # agent instructions (the entry point)
├── README.md                    # this file
├── LICENSE                      # MIT
├── assets/
│   └── template.html            # HTML template with {{placeholders}}
├── scripts/
│   ├── fetch_transcript.py      # Supadata fetch (handles "no subtitles" gotcha)
│   ├── merge_sentences.py       # segments → sentences
│   ├── snap_timestamps.py       # ★ align examples to real subtitle times
│   └── build_html.py            # fill template → final HTML
└── references/
    ├── embed-stability.md       # YouTube 153 / bot-challenge: causes & fixes
    ├── idiom-analysis.md        # how to pick & explain native expressions
    └── cefr-guidelines.md       # B1+ vocabulary selection
```

## The three iron rules

1. **Example timestamps must be exact** — always run `snap_timestamps.py`. Hand-written times are
   guesses and will jump to the wrong place.
2. **"No subtitles" videos are often scrapable** — never trust `transcriptLanguages: []`; always try
   `lang=fr`. Auto-captions (ASR) are lower quality (no punctuation, recognition errors) — only mine
   the correctly-transcribed lines and label the output as auto-caption.
3. **Mine idioms, not textbook grammar** — teach how French people actually speak; vocab defaults to
   B1+ with no prompts.

## License

MIT — see [LICENSE](LICENSE).

## Credits

Subtitle fetching powered by [Supadata](https://supadata.ai). Video playback via the YouTube
IFrame Player API.
