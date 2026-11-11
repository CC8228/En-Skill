#!/usr/bin/env python3
"""Check one day's intensive-reading set before it is written to the page.

Usage:
    python3 jingdu_check.py day.json [--cands cands.json]

Works for text sentences and for spoken items with audio (then the day needs "audioId",
and every item word timings "t" and its "clip" span). A day is five sentences of 25-35
words, or, when it says "unit": "passage", two passages of 100-170 words, each explained
in full depth (build, grammar, why, rewrite, pitfalls, and one structure entry per sentence).
Exits 0 and prints "OK" when the file is fit to publish; otherwise lists every
problem and exits 1. With --cands, each sentence must match a collected
candidate exactly, so a sentence can never drift from its source.
"""
import json
import re
import sys

SOURCES = {"新闻", "专业", "娱乐"}
STR_FIELDS = ["text", "source", "outlet", "title", "url", "published", "topic", "level",
              "translation", "relations", "meanings", "phrasing"]
LIST_MIN = {"gloss": 1, "chunks": 4, "structure": 2, "context": 2, "small": 3, "stress": 3, "pron": 1}
UNITS = {
    "sentence": {"count": 5, "words": (25, 35), "min": LIST_MIN, "deep": {}},
    "passage": {"count": 2, "words": (100, 170),
                "min": {"gloss": 1, "chunks": 8, "structure": 2, "context": 3, "small": 4, "stress": 6, "pron": 3},
                "deep": {"build": (3, ("text", "note")), "grammar": (4, ("point", "rule", "here", "example")),
                         "why": (5, ("q", "a")), "rewrite": (2, ("text", "note")), "pitfalls": (4, ("wrong", "right", "why"))}},
}
SENT_END = re.compile(r"[.!?][\"“”»«’)]*$")


def norm(w):
    return re.sub(r"[^\wÄÖÜäöüß]", "", w).lower()


def check(day, cands=None):
    errs = []
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(day.get("date", ""))):
        errs.append("date must be YYYY-MM-DD")
    if day.get("lang") != "de":
        errs.append('lang must be "de"')
    if day.get("audio") and not str(day.get("audioId", "")).strip():
        errs.append("audioId is empty: upload the day's .mp4 and rebuild with --audio-id")
    unit = day.get("unit", "sentence")
    if unit not in UNITS:
        return errs + ['unit must be "sentence" or "passage"']
    U = UNITS[unit]
    sents = day.get("sentences")
    if not isinstance(sents, list) or len(sents) != U["count"]:
        return errs + [f"sentences must be a list of exactly {U['count']} ({unit})"]
    texts = set()
    for i, s in enumerate(sents, 1):
        p = f"sentence {i}: "
        if s.get("n") != i:
            errs.append(p + f"n must be {i}")
        for f in STR_FIELDS:
            if not isinstance(s.get(f), str) or not s.get(f).strip():
                errs.append(p + f"missing text field '{f}'")
        for f, k in U["min"].items():
            if not isinstance(s.get(f), list) or len(s.get(f)) < k:
                errs.append(p + f"'{f}' needs at least {k} entries")
        text = s.get("text", "")
        if text in texts:
            errs.append(p + "duplicate sentence")
        texts.add(text)
        if s.get("source") not in SOURCES:
            errs.append(p + "source must be 新闻, 专业 or 娱乐")
        if s.get("level") not in ("B2", "C1"):
            errs.append(p + 'level must be "B2" or "C1"')
        tokens = text.split()
        words = [t for t in tokens if re.search(r"[\wÄÖÜäöüß]", t)]
        lo, hi = U["words"]
        if not lo <= len(words) <= hi:
            errs.append(p + f"{len(words)} words; needs {lo}-{hi}")
        if s.get("words") != len(words):
            errs.append(p + f"words must be {len(words)}")
        if cands is not None and text not in cands:
            errs.append(p + "text is not verbatim from the collected candidates")
        gloss = s.get("gloss") or []
        ws = [g.get("w") if isinstance(g, dict) else None for g in gloss]
        if ws != tokens:
            for j, (a, b) in enumerate(zip(ws + [None] * len(tokens), tokens)):
                if a != b:
                    errs.append(p + f"gloss[{j}].w is {a!r}, the sentence has {b!r} there "
                                "(one gloss entry per space-separated token, punctuation attached)")
                    break
            if len(ws) != len(tokens):
                errs.append(p + f"gloss has {len(ws)} entries, the sentence has {len(tokens)} tokens")
        for j, g in enumerate(gloss):
            if isinstance(g, dict) and not str(g.get("g", "")).strip():
                errs.append(p + f"gloss[{j}] ({g.get('w')}) has no meaning 'g'")
        for key, need in (("chunks", ("text", "meaning")), ("structure", ("text", "role")),
                          ("context", ("text", "here", "elsewhere")), ("small", ("word", "role")),
                          ("pron", ("word", "tip"))):
            for j, item in enumerate(s.get(key) or []):
                if not isinstance(item, dict) or any(not str(item.get(n, "")).strip() for n in need):
                    errs.append(p + f"{key}[{j}] needs {', '.join(need)}")
        flat = re.sub(r"\s+", " ", (s.get("phrasing") or "").replace("|", " ")).strip()
        if flat != re.sub(r"\s+", " ", text).strip():
            errs.append(p + "phrasing without the | marks must equal the sentence")
        have = {norm(t) for t in tokens}
        for w in s.get("stress") or []:
            if not all(norm(x) in have for x in str(w).split()):
                errs.append(p + f"stress word {w!r} is not in the sentence")
        # the deeper layer: required for passages, checked whenever it is there
        deep = dict(U["deep"])
        for k, need in UNITS["passage"]["deep"].items():
            if k not in deep and s.get(k):
                deep[k] = (1, need[1])
        for k, (n, keys) in deep.items():
            v = s.get(k)
            if not isinstance(v, list) or len(v) < n or any(not isinstance(x, dict) or any(not str(x.get(f, "")).strip() for f in keys) for x in v):
                errs.append(p + f"'{k}' needs at least {n} entries, each with {', '.join(keys)}")
        build = s.get("build") or []
        if build and isinstance(build[-1], dict):
            last = str(build[-1].get("text", ""))
            if unit == "passage":
                at = text.find(last)
                if not last or at < 0 or (at > 0 and not SENT_END.search(text[:at].rstrip())) or not SENT_END.search(last):
                    errs.append(p + "the last build step must be one whole sentence of the passage, character for character")
            elif last != text:
                errs.append(p + "the last build step must be the sentence itself, character for character")
        if unit == "passage":
            at = 0
            for j, seg in enumerate(s.get("structure") or []):
                seg_text = str(seg.get("text", "")) if isinstance(seg, dict) else ""
                k = text.find(seg_text, at) if seg_text else -1
                if k < 0:
                    errs.append(p + f"structure[{j}] is not the next stretch of the passage word for word")
                    break
                at = k + len(seg_text)
                if not str(seg.get("zh", "")).strip():
                    errs.append(p + f"structure[{j}] needs its Chinese translation 'zh'")
            if at and text[at:].strip():
                errs.append(p + "structure must cover the passage to its end")
            if len(s.get("rewrite") or []) != 2:
                errs.append(p + "rewrite needs exactly 2 entries (书面版, 简单版)")
        if not str(s.get("url", "")).startswith("https://"):
            errs.append(p + "url must start with https://")
        if "t" in s or day.get("audio"):
            t = s.get("t")
            if not isinstance(t, list) or len(t) != len(tokens):
                errs.append(p + f"t needs one [start, end] per token ({len(tokens)})")
            elif any(not (isinstance(x, list) and len(x) == 2 and 0 <= x[0] <= x[1]) for x in t):
                errs.append(p + "every t entry must be [start, end] with start <= end")
            clip = s.get("clip")
            if not (isinstance(clip, list) and len(clip) == 2 and 0 <= clip[0] < clip[1]):
                errs.append(p + "clip must be [start, end] of this sentence inside the day's audio file")
            elif isinstance(t, list) and t and t[-1][1] > clip[1] - clip[0] + 0.5:
                errs.append(p + "word timings run past the end of the clip")
    return errs


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    day = json.load(open(args[0], encoding="utf-8"))
    cands = None
    if "--cands" in args:
        cands = {c["text"] for c in json.load(open(args[args.index("--cands") + 1], encoding="utf-8"))}
    errs = check(day, cands)
    if errs:
        print("\n".join(errs))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
