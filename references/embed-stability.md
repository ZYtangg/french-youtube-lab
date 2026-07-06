# YouTube Embed Stability Guide

> How to make embedded YouTube videos play reliably in generated HTML tools.
> Without these fixes, users see **Error 153 — Video player configuration error**.

## ⚠️ 最重要的结论（先读这段）

有两个**完全不同**的问题，别混淆：

| 问题 | 谁的责任 | 能否用代码解决 |
|---|---|---|
| **Error 153**（Video player configuration error） | 嵌入页面的代码 | ✅ 能，见下文标准修复 |
| **"Sign in to confirm you're not a bot" / "Connectez-vous..."**（人机验证） | **用户的网络/浏览器环境** | ❌ **不能，任何代码都无法绕过** |

**人机验证是客户端问题，不是代码问题。** 实测证据：在触发人机验证的环境下，**longcut.ai（成熟商业产品）和自己生成的工具都会弹同样的验证**，因为它们用的是同一套 YouTube 嵌入机制。触发因素全在客户端：
1. **VPN / 代理机房 IP 被 YouTube 标记**（中国大陆走代理最常见）
2. **浏览器隐私拦截**（Firefox 增强跟踪保护 / Brave Shields / Safari 跨站跟踪拦截）拦截 YouTube cookie
3. 无痕模式 / 频繁清 cookie / 指纹保护插件

用户侧解法（代码无法代劳）：关掉页面的隐私拦截（地址栏盾牌图标）／换 VPN 节点（美、日住宅 IP）／换 Chrome／在同浏览器登录 Google 账号。

**产品层面唯一正确的应对**：检测到人机验证时，提供优雅降级——一键"在 YouTube 打开"并带上 `&t=Ns` 时间戳跳转。**不要再花时间试图用代码绕过**（SDK / nocookie / origin / HTTPS / 多源 fallback 全都不解决这个问题，已一一验证）。

---

## Root Cause of Error 153

Error 153 is **not** a copyright or embedding-permission issue. It's a **referrer / origin** issue.

YouTube's IFrame Player API requires the embedding page to send valid `Referer` and `Origin` headers. When these are stripped or mismatched, YouTube refuses to initialize the player and shows:

```
Watch on YouTube
Error 153 — Video player configuration error
```

Three things trigger it:

1. **`Referrer-Policy: same-origin` or `no-referrer`** — strips the Referer header
   - Django's `SecurityMiddleware` defaults to `same-origin` (Simon Willison's discovery, 2025-12)
   - Some meta tags do the same: `<meta name="referrer" content="no-referrer">`
2. **`youtube.com` instead of `youtube-nocookie.com`** — the regular domain is more aggressive about referrer validation
3. **Browser privacy extensions** (uBlock Origin, Brave Shields, Privacy Badger) — strip referrer headers client-side

## The Standard Fix (apply to every generated HTML)

### 1. Use `youtube-nocookie.com` as the iframe src

```html
<!-- ❌ DON'T — triggers Error 153 in many environments -->
<iframe src="https://www.youtube.com/embed/VIDEO_ID?...">

<!-- ✅ DO — stable across browsers and privacy extensions -->
<iframe src="https://www.youtube-nocookie.com/embed/VIDEO_ID?...">
```

`youtube-nocookie.com` is YouTube's official privacy-enhanced domain. It:
- Doesn't set tracking cookies until the user plays
- Is more lenient about referrer validation
- Returns the exact same video player UI

Verified working: `curl https://www.youtube-nocookie.com/embed/Jdpau-iYnFQ` returns HTTP 200 with full player HTML.

### 2. Set `referrerpolicy="strict-origin-when-cross-origin"` on the iframe

```html
<iframe
  src="https://www.youtube-nocookie.com/embed/VIDEO_ID?..."
  referrerpolicy="strict-origin-when-cross-origin"
  ...>
```

This sends the origin (but not the full URL) as Referer — enough for YouTube to verify, while respecting user privacy.

### 3. Include the full `allow` permissions

```html
allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
```

Missing permissions (especially `encrypted-media`) can also trigger playback failures.

### 4. Do NOT send `Referrer-Policy: same-origin` from the server

- Python's `http.server` doesn't send this header (defaults to browser's `strict-origin-when-cross-origin`) ✅
- Django's `SecurityMiddleware` defaults to `same-origin` ❌ — must override
- Nginx/Apache: ensure no `Referrer-Policy: same-origin` or `no-referrer` directive

### 5. The `origin` parameter only matters when using `enablejsapi=1`

```html
<!-- For subtitle-sync features that use postMessage to the player: -->
src="https://www.youtube-nocookie.com/embed/VIDEO_ID?enablejsapi=1&origin=http://127.0.0.1:PORT"

<!-- For plain embed without JS API: omit origin -->
src="https://www.youtube-nocookie.com/embed/VIDEO_ID?rel=0"
```

The `origin` value **must exactly match** the page's actual origin (protocol + host + port). If the user opens via `file://`, the origins will mismatch and the JS API silently fails (video still plays, but no `currentTime` updates for subtitle sync).

## Fallback Layer (for stubborn environments)

Even with all the above, some users have ad-blockers that strip all referrers. Add a JS fallback that detects playback failure and offers an "Open on YouTube" link with timestamp:

```javascript
// Detect if iframe fails to initialize within 5 seconds
let playerReady = false;
window.addEventListener("message", (e) => {
  try {
    const data = JSON.parse(e.data);
    if (data.event === "onReady" || (data.info && typeof data.info.currentTime === "number")) {
      playerReady = true;
    }
  } catch (_) {}
});

setTimeout(() => {
  if (!playerReady) {
    const hint = document.getElementById("ytStatusHint");
    if (hint) {
      hint.innerHTML = '⚠️ 视频未能加载 — 你的浏览器可能屏蔽了 YouTube。' +
        '<a href="https://www.youtube.com/watch?v=VIDEO_ID" target="_blank" style="color:#FE7F2D;">点这里在 YouTube 打开 ↗</a>';
      hint.style.color = "#C62828";
    }
  }
}, 5000);
```

## What Does NOT Work

| Approach | Result |
|---|---|
| **Piped.video public instances** as embed fallback | ❌ Unreliable — most public instances fail TLS handshake or rate-limit aggressively. Don't depend on them. |
| **Invidious public instances** as embed fallback | ❌ Same — instances go down frequently, get blocked by YouTube. |
| **Self-hosted YouTube proxy** (Cloudflare Workers, etc.) | ⚠️ Works but adds operational complexity. Overkill for a learning tool. |
| **Pre-downloading the video** with yt-dlp | ❌ Anti-bot (PO Token, n-challenge) blocks cloud IPs. Same problem as transcript fetching. |
| **Telling users to disable ad-blocker** | ⚠️ Works but hostile UX. Better to offer the YouTube-link fallback. |
| **Cobalt.tools / youtube-dl web services** as video proxy | ⚠️ Works for direct download but their public instances get rate-limited. Embedding the resulting mp4 in `<video>` works but adds a dependency. |

## A Separate Problem: YouTube Bot Challenge

After fixing Erreur 153, users in mainland China (or on flagged IPs) may see a **different** failure:

```
Connectez-vous pour confirmer que vous n'êtes pas un robot
Se connecter
```

This is YouTube's reCAPTCHA / bot-detection, not the referrer issue. Triggers:
- Mainland China IP addresses (most common)
- Datacenter / VPN IPs flagged by Google
- Fresh browsers with no YouTube cookies + suspicious fingerprint
- Sustained bot-like traffic from the same IP

**This is the same class of problem as `youtube-transcript-api` failing on cloud IPs** — YouTube anti-bot defenses.

### What to do about it

You **cannot** solve this in the generated HTML. The iframe loads, but the player inside shows a sign-in gate that blocks playback.

**The right product response is to accept the limitation and pivot the workflow:**

1. **Primary workflow**: Open the video in YouTube (in another tab/window) and use the generated HTML as a **grammar/vocabulary reference companion**.
   - Click any subtitle in the tool → it opens YouTube with `&t=Ns` timestamp
   - The tool's value is the grammar patterns, vocabulary flashcards, and side-by-side translation — not the video itself
2. **UI affordances**:
   - Always include a prominent "↗ Open in YouTube" link near the player
   - Add a "🎯 Study Mode" button that hides the iframe and gives the subtitle panel more vertical space
   - Auto-detect the bot challenge via the IFrame API's `onError` event and surface a hint when detected
3. **Skills should document this explicitly** in their Notes section, so end users know:
   - "If you see the YouTube sign-in gate, open the video on youtube.com and use this tool as a study companion."

## Verification Checklist

Before shipping generated HTML, verify:

- [ ] iframe `src` uses `youtube-nocookie.com` (not `youtube.com`)
- [ ] iframe has `referrerpolicy="strict-origin-when-cross-origin"`
- [ ] iframe `allow` includes `encrypted-media; gyroscope; picture-in-picture; web-share`
- [ ] No `<meta name="referrer" content="no-referrer">` or `same-origin` in the HTML
- [ ] If using `enablejsapi=1`, the `origin` parameter matches the page's protocol+host+port
- [ ] A "Open on YouTube" link is visible near the player as fallback
- [ ] Tested in Chrome, Firefox, Safari (different default referrer policies)
- [ ] Tested with uBlock Origin enabled (most common cause of residual 153)

## Sources

- Simon Willison, "Fixing YouTube 153 embed errors" (updated 2025-12-01) — https://til.simonwillison.net/tils/til/youtube_fixing-153-embed~2Emd
- Pratik Pathak, "FIX YouTube Error 153" — https://pratikpathak.com/fix-youtube-error-153-video-player-configuration-error-when-embedding-youtube-videos/
- YouTube official docs on Embedded Player API client identity — https://developers.google.com/youtube/terms/required-minimum-functionality#embedded-player-api-client-identity
- Arjen's "Fixing YouTube Error 153: The GDPR-Compliant Way" — https://whoisarjen.com/blog/fixing-youtube-error-153-gdpr-compliant
