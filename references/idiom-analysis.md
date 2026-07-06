# 地道表达挖掘方法（Idiom / Native-Expression Analysis）

本 skill 的核心不是罗列语法点，而是挖掘**法国人真正会说的、地道、精妙、高频**的表达。
下面是挑选标准、写讲解的方法，以及分类清单。

## 什么算「地道表达」（优先挑这些）

1. **口语惯用法 / 固定搭配**
   - avoir du mal à + inf.（做…很费劲）、faire comme si + 从句（假装）、prendre A pour B（把A当成B）、arriver à + inf.（成功做到）
2. **比喻 / 习语（idiome）**
   - raide comme un balai（僵得像棍子）、péter les plombs（抓狂）、avoir qqch dans le sang（骨子里就有）、jeter un regard（瞟一眼）
3. **语气词 / 填充词 / 话语标记（discourse markers）**——最能体现「native 感」
   - enfin（呃…我是说，纠正语气）、bref（总之）、du coup（于是）、genre（就那种）、quand même（还是/不过）、au final（到头来）、en fait（其实）、voilà（就这样）
4. **假朋友（faux amis）**——中国学习者最易错，价值高
   - supporter（受得了，≠英语 support 支持）、assumer（坦然承担，≠assume 假设）、鼓励用户特别标注
5. **构词法产出的词**——能举一反三
   - in- + 动词 + -able（inarrêtable 势不可挡 / incontournable 绕不开）
6. **一词多义的口语义**
   - monde=人（peu de monde 没几个人 / du monde 人多）、truc=东西（万能词）、tour=一圈（faire le tour de）

## 什么不要挑

- 教科书语法点罗列（"passé composé 的构成"、"il y a 的用法"这种）——除非它在这个视频里有特别地道/高频的用法
- 太基础的 A1/A2 词汇当"表达"（那些放词汇本即可）
- 视频里没真实出现的表达（例句必须来自字幕原文）

## expressions.json 每条的字段

```json
{
  "name": "péter les plombs",          // 表达本身（原形）
  "level": "B2",                        // CEFR: A2/B1/B2/C1
  "meaning": "抓狂 · 情绪爆炸",          // 一句话点破（≤12字，用 · 分隔近义）
  "freq": 1,                            // 在视频里出现次数
  "explanation": "100-200字：为什么地道 + 场景 + 近义 + 易错点",
  "examples": [
    { "fr": "字幕里真实出现的原句", "zh": "自然中文", "time": 183 }
  ]
}
```

## explanation 怎么写（关键）

讲「为什么地道 + 怎么用」，不是讲语法规则。好的 explanation 包含：
- **点破含义**：这个表达到底什么意思、什么语气/色彩（正式/口语/俚语/自嘲…）
- **使用场景**：法国人什么时候会说它、放句首/句中/句尾
- **近义对比**：比某个"教科书说法"地道在哪（如 péter les plombs 比 s'énerver 强烈）
- **易错/注意点**：阴阳性配合、假朋友、口语省略（je sais pas 省 ne）、发音联诵等

**范例**（good）：
> 「péter les plombs」= 抓狂 / 情绪爆炸。这是法国人形容「气到失控」最地道的俚语，字面是「烧断了保险丝」。比 s'énerver（生气）强烈得多，接近「气疯了」。同义地道说法：péter un câble。日常对话、影视高频出现，正式场合避免。

**反例**（bad，太像教科书）：
> 「péter」是第一组动词，变位为 je pète, tu pètes... 后接直接宾语 les plombs。

## 数量与排序

- 一个视频挑 **10–22 条**（短视频 10–12，长视频 15–22）。
- 最终由 `snap_timestamps.py` 按视频出现时间排序，不用手动排。

## 分类标签（可选，用于 meaning 或分组参考）

常见表达源自这些类别（供扫描时参考，不必强制分组）：
表达/搭配 · 习语比喻 · 话语标记/语气词 · 假朋友 · 构词法 · 一词多义 · 时态/语式的地道用法（如 conditionnel 表假设、imparfait vs passé composé 叙事切换）。
