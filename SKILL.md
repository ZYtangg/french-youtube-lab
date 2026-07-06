---
name: french-youtube-lab
description: "把任意法语 YouTube 视频（含 Shorts）转成一个自包含的「地道法语表达」学习网页：抓取字幕 → 挖掘高频·精妙·native 的地道表达 → 自动填充 B1+ 词汇本 → 生成可播放视频、例句时间戳精准跳转的 HTML。触发词：French YouTube learning, 法语YouTube学习, 地道法语表达, French idiom lab."
license: MIT
compatible_with: "Codebuddy / Claude Code style agents with Bash + file tools"
---

# French YouTube Lab

把一个法语 YouTube 视频变成一个交互式「地道法语表达」学习网页。核心价值 = **教你法国人真正怎么地道地说**（不是教科书语法罗列）+ **B1+ 词汇闪卡** + **视频同步、例句一键跳到对应时间戳**。

## ⚠️ 开始前：两个需要用户配合的前置条件（务必先确认）

1. **Supadata API key（抓字幕用，付费服务）**
   - 本 skill 用 [Supadata](https://supadata.ai) 抓 YouTube 字幕（绕过 YouTube 对云 IP 的反爬，这是 longcut.ai 同款方案）。
   - 需要用户提供 key，通过环境变量 `SUPADATA_API_KEY` 或脚本 `--key` 传入。
   - 若用户没有：引导去 supadata.ai 注册（有免费额度），或改用其它字幕源。

2. **观看视频需要 Chrome + 登录 Google 账号**
   - 生成的 HTML 用 YouTube IFrame Player SDK 嵌入视频。**能否播放取决于用户的浏览器/网络，不是代码问题**。
   - 在受限网络（如中国大陆走代理）下，YouTube 会弹「确认你不是机器人」的人机验证——**任何第三方嵌入都躲不掉，longcut.ai 同环境也一样**。
   - **可靠方案**：用 **Chrome** 打开并**登录 Google 账号**（实测有效）。详见 `references/embed-stability.md`。
   - 部署时**必须用 HTTPS 公开域名**（CloudStudio / Vercel / Cloudflare Pages），**不要用 localhost / file://**。

## 🔑 三条铁律（本 skill 的灵魂，任何时候都要遵守）

1. **例句时间戳必须对准** —— 这是最重要的功能。Agent 手写的例句时间是猜的，一定会跳错。**必须**用 `scripts/snap_timestamps.py` 把每条例句吸附到字幕里真实出现的时间。绝不手填时间戳后直接发布。
2. **没字幕的视频也常常能爬** —— 视频元信息里 `transcriptLanguages: []` **不代表没字幕**！很多视频有自动生成字幕（ASR），元信息不列但 `lang=fr` 能抓到。`scripts/fetch_transcript.py` 已内置：永远直接试 `lang=fr`，不看元信息。ASR 字幕质量差（无标点、有识别错误）时脚本会警告，此时只提炼识别正确的句子，并向用户标注「自动字幕」。
3. **挖地道表达，不做教科书语法** —— 目标是「法国人如何地道表达」：高频、精妙、native 的用法。每条讲清「为什么地道 + 怎么用」。词汇本默认 **B1 及以上自动填充，不要问用户选级别**。

## 工作流（脚本化，快）

> 设计原则：**确定性的机械步骤全部交给脚本**（抓取/合并/吸附时间戳/装配 HTML），Agent 只做**创造性工作**（挖地道表达 + 翻译）。这样最快、最稳、最省往返。

```
VIDEO_ID
  │  scripts/fetch_transcript.py      → <id>.meta.json + <id>.transcript.json
  ▼
raw segments
  │  scripts/merge_sentences.py       → sentences.json  (fr + time秒)
  ▼
sentences   ── Agent 翻译每句 zh ──▶  corpus.json   (fr + zh + time)
            └─ Agent 挖地道表达 ───▶  expressions.json + vocab.json
  │  scripts/snap_timestamps.py       → expressions.snapped.json (时间戳吸附✔ + 按视频顺序排)
  ▼
scripts/build_html.py                 → french-lab-<id>.html
  ▼
部署到 HTTPS 公开域名（不要 localhost）
```

### Step 1 — 抓字幕

```bash
python3 scripts/fetch_transcript.py VIDEO_ID --lang fr --key "$SUPADATA_API_KEY" --out ./work
```
- 输出 `work/VIDEO_ID.meta.json`（含 title/duration）和 `work/VIDEO_ID.transcript.json`。
- 退出码：`0` 成功 / `2` 确实无字幕 / `3` 是直播（直播结束才有字幕）/ `4` 网络或 key 错误。
- 若打印 `NOTE: ...ASR...`，说明是自动字幕，质量可能差 → 后续只用识别正确的句子，并告知用户。

### Step 2 — 合并成句子

```bash
python3 scripts/merge_sentences.py work/VIDEO_ID.transcript.json --out work/sentences.json
```
- 把碎片段按标点 + 停顿合并成自然句（`{fr, time秒}`）。会打印全文供你通读。

### Step 3 — Agent 创造性工作（翻译 + 挖地道表达）

通读 `sentences.json` 全文后：

1. **翻译**：为**每一句**写自然的中文，产出 `work/corpus.json`：
   ```json
   [{ "fr": "原句", "zh": "中文翻译", "time": 8 }, ...]
   ```
   （time 沿用 sentences.json 里的值。）

2. **挖地道表达**（核心）：从真实出现的句子里挑 **10–22 条**高频/精妙/native 的表达，产出 `work/expressions.json`：
   ```json
   [{
     "name": "péter les plombs",
     "level": "B2",
     "meaning": "抓狂 · 情绪爆炸",
     "freq": 1,
     "explanation": "为什么地道 + 怎么用（100-200字，讲清楚场景、近义、易错点）",
     "examples": [{ "fr": "视频里真实出现的句子", "zh": "中文", "time": 183 }]
   }, ...]
   ```
   - 优先：口语惯用法、固定搭配、比喻习语、语气词/填充词（enfin/bref/du coup/genre/quand même…）、假朋友（如 supporter≠support）、构词法。
   - `examples.fr` **必须是字幕里真实出现的原句**（供下一步吸附时间戳）。
   - `explanation` 讲「为什么地道」而非语法规则。

3. **词汇本**（B1+ 自动填充）：产出 `work/vocab.json`：
   ```json
   [{ "word": "assumer", "zh": "坦然接受、承担", "example": "j'ai du mal à assumer mon prénom." }, ...]
   ```
   - 只收 B1 及以上（排除 A1/A2 太基础的、排除人名地名）。参考 `references/cefr-guidelines.md`。
   - **不要问用户选级别**，直接按 B1+ 填。

### Step 4 — 吸附时间戳（最重要，勿跳过）

```bash
python3 scripts/snap_timestamps.py work/expressions.json work/corpus.json --out work/expressions.snapped.json
```
- 把每条例句的 `time` 对齐到字幕真实时间，并按视频顺序排、重编 id。
- 看输出报告；若有 `LOW-CONFIDENCE` 警告，手动核对那几条例句（可能字幕里没这句原文、或你改写过头了 → 把 example.fr 改回贴近原文）。

### Step 5 — 装配 HTML

```bash
# 普通横屏视频：--aspect 16/9
# Shorts 竖屏视频：--aspect 9/16（会自动约束尺寸，不铺满全屏）
python3 scripts/build_html.py \
  --template assets/template.html \
  --video-id VIDEO_ID \
  --title "地道法语表达实验室 — <视频标题>" \
  --header "<视频标题> | <频道>（如是自动字幕注明）" \
  --expressions work/expressions.snapped.json \
  --vocab work/vocab.json \
  --corpus work/corpus.json \
  --aspect 16/9 \
  --out french-lab-VIDEO_ID.html
```
- 脚本会校验无残留占位符、无 `[[` 语法错误。

### Step 6 — 部署（HTTPS，非 localhost）

用 CloudStudio / Vercel / Cloudflare Pages 等把 `french-lab-VIDEO_ID.html` 部署到 HTTPS 公开域名，把链接给用户。
提醒用户：用 Chrome + 登录 Google 账号观看，若仍要人机验证见 `references/embed-stability.md`。

## HTML 功能（模板已内置）

- 左侧：单个从上到下可滚动的「地道表达」列表，按视频时间顺序排，每条标 CEFR 级别。
- 中间：点表达 → 显示讲解 + 例句；点例句 → 视频跳到该时间戳并播放。
- 右侧：YouTube 播放器（IFrame SDK）+ 字幕面板（中法对照，随播放高亮滚动，点字幕也能跳转）+「背 B1+ 单词」闪卡。
- 数据存 localStorage（按 video id 区分），支持手动补充单词（重音不敏感搜索全字幕）。

## 参考

- `references/embed-stability.md` — YouTube 嵌入的所有坑（Error 153、人机验证）与真正的解法。**遇到视频播放问题先读它。**
- `references/idiom-analysis.md` — 怎么挑「地道表达」、怎么写 explanation 的方法与范例。
- `references/cefr-guidelines.md` — B1+ 词汇筛选标准。
