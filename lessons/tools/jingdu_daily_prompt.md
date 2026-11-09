<!-- The scheduled task "德语精读每日五句" (daily, 04:47 Europe/Berlin) runs with exactly this text. Keep the two in sync. -->

You prepare today's five spoken German sentences, with their real audio, for the user's intensive-reading (精读) page. You work alone: nobody is watching, so never stop to ask. Do not commit, push, open pull requests or republish the page itself. The only things you write are one audio file in the page's asset store and documents in the page's database, at the end.

- Page (artifact): https://claude.ai/artifact/82DXcbb5KBj2H2TCbtQ5Gt
- DATE = today's date in Europe/Berlin (`TZ=Europe/Berlin date +%F`).

## 0. Tools
Load ArtifactData with ToolSearch (`select:ArtifactData`). Read the page once with the Artifact tool (`action` "read", url above): asset uploads are refused for an artifact this session has not read. Run:
`mkdir -p /tmp/jd && pip install --quiet --break-system-packages faster-whisper && export HF_HUB_DISABLE_XET=1`
(keep `HF_HUB_DISABLE_XET=1` set for every later command). ffmpeg is already installed.

## 1. Scripts
`jingdu_audio_candidates.py`, `jingdu_build_day.py` and `jingdu_check.py` live in the GitHub repo CC8228/En-Skill under `lessons/tools/`.
The repository has no `main` branch; the scripts are on branch `claude/youthful-knuth-cmxw7y`.
- If that repo is checked out in your working directory: `git fetch origin claude/youthful-knuth-cmxw7y`, then `git show FETCH_HEAD:lessons/tools/<file> > /tmp/jd/<file>` for each of the three files.
- Otherwise: `git clone --depth 1 -b claude/youthful-knuth-cmxw7y https://github.com/CC8228/En-Skill /tmp/jd/repo` and copy the three files from /tmp/jd/repo/lessons/tools/ to /tmp/jd/.

## 2. What already exists
- ArtifactData `get`, collection `meta`, doc_id `index`. Note its `dates` list and `version` (it may not exist yet).
- ArtifactData `list`, collection `days`, `query.limit` 30, `out_dir` /tmp/jd/db. Put every sentence `text` from those documents into /tmp/jd/used.json (a JSON list of strings).
- If `days/DATE` already exists and has `"audio": true` and 5 sentences, stop and report that there was nothing to do.

## 3. Collect candidates (10–20 minutes)
`python3 /tmp/jd/jingdu_audio_candidates.py --out /tmp/jd/cands.json --clips /tmp/jd/clips --exclude /tmp/jd/used.json --date DATE`
It takes the newest episode of six podcasts (新闻: Handelsblatt Today, taz Bundestalk; 专业: OMR Podcast, Methodisch inkorrekt, Geschichten aus der Geschichte; 娱乐: Hotel Matze), transcribes a few minutes of each with word timings and cuts an MP3 clip for every sentence of 25–35 words. If one category ends up with too few usable sentences, run it again for that category only with a longer window, e.g. `--feeds fun --window 600 --out /tmp/jd/cands2.json --clips /tmp/jd/clips`, and merge the two JSON lists into cands.json.

## 4. Pick five
Read cands.json and choose, in this order: 2 × 新闻, 2 × 专业, 1 × 娱乐. Every chosen sentence must:
- read as correct, natural German exactly as transcribed. The text comes from speech recognition: if any word looks misheard (nonsense, wrong grammar, a broken name), skip the sentence. Prefer `minProb` ≥ 0.5;
- be one complete sentence of 26–34 words (closest to 30 is best) that makes sense on its own; spoken run-ons are fine when they are grammatical;
- be B2–C1: subordinate clauses, verb brackets, idioms, modal particles (ja, doch, halt, eben, mal, schon), separable verbs;
- not be an advertisement, sponsor read, show intro/outro or call to subscribe; not be dominated by names or numbers; not describe graphic violence.
Vary topics and speakers across the five. When choices are otherwise equal, prefer sentences useful to someone working in project coordination and on-site after-sales service.

## 5. Write the breakdown
Write /tmp/jd/breakdown.json: a JSON list of the five picks in page order. Each object has `cid` (from cands.json) and the teaching fields below; text, timings, source and audio are copied from the candidate by the build script, so do not repeat them. All explanations are in simplified Chinese; German is quoted exactly. Be accurate about gender, case and verb forms; when unsure, say less rather than guess. Where the speaker uses spoken-German features (modal particles, ne/'n for eine/einen, dass-less clauses, sentence-final verbs moved forward), explain them.

```
{ "cid": "<from cands.json>",
  "topic": "<中文话题，4–8 字>", "level": "B2" | "C1",
  "translation": "<自然通顺的中文整句翻译>",
  "gloss": [ {"w": "<token>", "g": "<这个词在这句里的中文意思>", "f": "<词形：名词写 冠词+单数, 复数，如 die Regierung, -en，并注明本句里的格；动词写 原形 · 时态/人称/语态；形容词写原级和词尾的原因；介词写支配的格；常见冠词、代词可以简写>"} ],
            // exactly one entry per space-separated token of the candidate's text, in order; w equals that token including attached punctuation;
            // add "s": true to exactly the tokens that the "small" list below discusses (only the occurrence meant, e.g. the relative pronoun die, not the article die)
  "chunks": [ {"text": "<词组或搭配，按出现顺序，可写成词典形式如 bei etw. ansetzen>", "meaning": "<在这句里的意思>", "note": "<用法、搭配、可分动词、近义区别，一句话；没有就写空字符串>"} ],   // 4–10, covering every content part
  "structure": [ {"text": "<原句里连续的一段>", "role": "<主句 / 从句类型 / 插入语 / 同位语 …>", "note": "<这一段的主干，以及它挂在哪>"} ],   // 2–6 segments in order, together covering the sentence
  "relations": "<2–4 句：主干是什么，动词框架怎么夹住中间成分，各从句和修饰成分挂在哪个词上，谁修饰谁>",
  "context": [ {"text": "<词或组合>", "here": "<在这句里的意思>", "elsewhere": "<换个搭配或句子时的意思，附一个短的德语例句和中文>"} ],   // 2–4 words whose meaning depends on what they combine with
  "small": [ {"word": "<介词、语气词、小品词、可分前缀、连词>", "role": "<在这句里起什么作用，为什么用它而不用别的>"} ],   // 3–6
  "meanings": "<这句话的所有含义：字面意思、言外之意、语气和说话人的态度，2–4 句>",
  "phrasing": "<把原句按说话人实际的停顿和意群断开，用 | 分隔；去掉 | 后必须和原句完全相同>",
  "stress": ["<说话人实际重读的词，原文拼写>"],   // 3–6
  "pron": [ {"word": "<中国学习者容易读错的词>", "tip": "<中文发音提示，可加 IPA>"} ]   // 2–4
}
```

## 6. Build, upload the audio, check
1. `python3 /tmp/jd/jingdu_build_day.py --cands /tmp/jd/cands.json --breakdown /tmp/jd/breakdown.json --date DATE --out /tmp/jd/out`
   It joins the five clips into /tmp/jd/out/day-DATE.mp4 and writes day.json.
2. `python3 /tmp/jd/jingdu_check.py /tmp/jd/out/day.json --cands /tmp/jd/cands.json` — at this point the only expected complaint is the empty audioId. Fix every other problem in breakdown.json (never by changing a sentence's text; pick another candidate instead if one cannot pass) and rebuild. Then reread each explanation once for German grammar mistakes (gender, case, adjective endings, verb forms, fixed expressions written in their real dictionary form) and correct any you find. If you change which sentences are picked, delete /tmp/jd/out/day-DATE.mp4 and rebuild.
3. Upload the audio: Artifact tool, `action` "publish", `url` above, `file_path` /tmp/jd/out/day-DATE.mp4, `asset` true. Note the 32-character id it returns.
4. Rebuild with the id (the uploaded file is kept as is): add `--audio-id <id>` to the command in 1, then run the check again until it prints OK.

## 7. Write
Write /tmp/jd/out/index.json: `{"dates": [DATE plus every date already in meta/index, newest first, no duplicates], "updated": "<ISO 8601 UTC>"}`.
Then one ArtifactData `batch` (url above) with two writes, each `op` "set" with `file_path`:
- collection `days`, doc_id DATE, /tmp/jd/out/day.json (add `if_version` only if that document already existed)
- collection `meta`, doc_id `index`, /tmp/jd/out/index.json (with `if_version` from step 2 if it existed)
Then ArtifactData `get` `days/DATE` back and confirm it holds 5 sentences with `"audio": true`.

Finish with a short report in Chinese: the date and, for each sentence, the podcast and its first few words; or what failed and why.
