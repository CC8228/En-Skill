<!-- The scheduled task "德语精读每日五句" (daily, 04:47 Europe/Berlin) runs with exactly this text. Keep the two in sync. -->

You prepare today's five German sentences for the user's intensive-reading (精读) page. You work alone: nobody is watching, so never stop to ask. Do not commit, push, open pull requests or republish the page. The only thing you write is one document in the page's database, at the end.

- Page (artifact): https://claude.ai/artifact/82DXcbb5KBj2H2TCbtQ5Gt
- Database document: collection `days`, doc_id = today's date in Europe/Berlin (`TZ=Europe/Berlin date +%F`).

## 0. Tools
Load ArtifactData with ToolSearch (`select:ArtifactData`). Run `mkdir -p /tmp/jd`.

## 1. Scripts
`jingdu_candidates.py` and `jingdu_check.py` live in the GitHub repo CC8228/En-Skill under `lessons/tools/`.
- If that repo is checked out in your working directory: `git fetch origin main claude/youthful-knuth-cmxw7y`, then copy both files from whichever of `origin/main` and `origin/claude/youthful-knuth-cmxw7y` has them (prefer main) with `git show <ref>:lessons/tools/<file> > /tmp/jd/<file>`.
- Otherwise: `git clone --depth 1 -b main https://github.com/CC8228/En-Skill /tmp/jd/repo`; if main lacks the files, clone `-b claude/youthful-knuth-cmxw7y` instead; copy the two files to /tmp/jd/.

## 2. Skip what was already used
ArtifactData `list`, collection `days`, `query.limit` 30, `out_dir` /tmp/jd/db. Put every sentence `url` and `text` from those documents into /tmp/jd/used.json (a JSON list of strings). If today's document already exists with 5 sentences, stop and report that there was nothing to do. If it exists but is incomplete, note its `version`.

## 3. Collect candidates
Run `python3 /tmp/jd/jingdu_candidates.py --out /tmp/jd/cands.json --exclude /tmp/jd/used.json` (a few minutes). It prints how many verbatim sentences each outlet gave. If it fails or gives nothing, run it once more with `--days 5`.

## 4. Pick five
Read cands.json. Choose, in this order: 2 × 新闻 (ZDFheute or taz), 2 × 专业 (ingenieur.de; if it has fewer than 2 usable ones, take economy/technology/science sentences from ZDFheute or taz and still label them 专业), 1 × 娱乐 (FILMSTARTS). Every sentence must:
- be copied exactly as it appears in cands.json: never edit, shorten, merge or fix it;
- be one complete, self-contained sentence of 26–34 words (closest to 30 is best) that makes sense without the article;
- be real, everyday modern German at B2–C1: subordinate clauses, verb brackets, Nominalstil, Passiv or Konjunktiv, Funktionsverbgefüge, and at least two small words worth studying (prepositions; particles such as doch, eben, mal, ja, schon, zwar; separable prefixes such as an-, auf-, zu-);
- not be a headline, list, caption, poem, table of contents, cookie notice, or a fragment that starts mid-sentence;
- not be dominated by names, numbers or quoted slogans, and not describe graphic violence.
Vary topics and sentence structures across the five. When choices are otherwise equal, prefer sentences useful to someone working in project coordination and on-site after-sales service.

## 5. Write the breakdown
Write /tmp/jd/day.json in exactly this shape (the `//` notes explain fields and are not part of the file). All explanations are in simplified Chinese; German is quoted exactly. Be accurate about gender, case and verb forms; when unsure, say less rather than guess.

```
{ "date": "<YYYY-MM-DD, Berlin>", "lang": "de", "level": "B2–C1", "createdAt": "<ISO 8601 UTC>",
  "sentences": [ {
    "n": 1,                     // 1..5, in the order 新闻, 新闻, 专业, 专业, 娱乐
    "text": "<verbatim sentence>",
    "source": "新闻 | 专业 | 娱乐", "outlet": "<outlet from cands>", "title": "<article title>", "url": "<article url>",
    "published": "<YYYY-MM-DD>", "topic": "<中文话题，4–8 字>", "words": <word count as the checker counts it>, "level": "B2" | "C1",
    "translation": "<自然通顺的中文整句翻译>",
    "gloss": [ {"w": "<token>", "g": "<这个词在这句里的中文意思>", "f": "<词形：名词写 冠词+单数, 复数，如 die Regierung, -en，并注明本句里的格；动词写 原形 · 时态/人称/语态；形容词写原级和词尾的原因；介词写支配的格；常见冠词、代词可以简写>"} ],
              // exactly one entry per space-separated token of text, in order; w equals that token including attached punctuation;
              // add "s": true to exactly the tokens that the "small" list below discusses (only the occurrence meant, e.g. the relative pronoun die, not the article die)
    "chunks": [ {"text": "<词组或搭配，按出现顺序，可写成词典形式如 bei etw. ansetzen>", "meaning": "<在这句里的意思>", "note": "<用法、搭配、可分动词、近义区别，一句话；没有就写空字符串>"} ],   // 4–10, covering every content part
    "structure": [ {"text": "<原句里连续的一段>", "role": "<主句 / 从句类型 / 插入语 / 同位语 …>", "note": "<这一段的主干，以及它挂在哪>"} ],   // 2–6 segments in order, together covering the sentence
    "relations": "<2–4 句：主干是什么，动词框架怎么夹住中间成分，各从句和修饰成分挂在哪个词上，谁修饰谁>",
    "context": [ {"text": "<词或组合>", "here": "<在这句里的意思>", "elsewhere": "<换个搭配或句子时的意思，附一个短的德语例句和中文>"} ],   // 2–4 words whose meaning depends on what they combine with
    "small": [ {"word": "<介词、语气词、小品词、可分前缀、连词>", "role": "<在这句里起什么作用，为什么用它而不用别的>"} ],   // 3–6
    "meanings": "<这句话的所有含义：字面意思、言外之意、语气和作者态度，2–4 句>",
    "phrasing": "<把原句按意群断开，意群之间用 | 分隔；去掉 | 后必须和原句完全相同>",
    "stress": ["<朗读时重读的词，原文拼写>"],   // 3–6
    "pron": [ {"word": "<中国学习者容易读错的词>", "tip": "<中文发音提示，可加 IPA>"} ]   // 2–4
  } ] }
```

## 6. Check
Run `python3 /tmp/jd/jingdu_check.py /tmp/jd/day.json --cands /tmp/jd/cands.json`. Fix every reported problem in day.json (never by changing a sentence's text; pick another candidate instead if a sentence cannot pass) and run it again until it prints OK. Then reread each explanation once for German grammar mistakes (gender, case, adjective endings, verb forms, fixed expressions written in their real dictionary form) and correct any you find.

## 7. Write
ArtifactData `set`: url above, collection `days`, doc_id = the date, `file_path` /tmp/jd/day.json (add `if_version` only if the document already existed). Then ArtifactData `get` it back and confirm it holds 5 sentences.

Finish with a short report in Chinese: the date and, for each sentence, the outlet and its first few words; or what failed and why.
