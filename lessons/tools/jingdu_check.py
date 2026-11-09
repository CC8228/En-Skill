#!/usr/bin/env python3
"""Check one day's intensive-reading set before it is written to the page.

Usage:
    python3 jingdu_check.py day.json [--cands cands.json]

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


def norm(w):
    return re.sub(r"[^\wÄÖÜäöüß]", "", w).lower()


def check(day, cands=None):
    errs = []
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(day.get("date", ""))):
        errs.append("date must be YYYY-MM-DD")
    if day.get("lang") != "de":
        errs.append('lang must be "de"')
    sents = day.get("sentences")
    if not isinstance(sents, list) or len(sents) != 5:
        return errs + ["sentences must be a list of exactly 5"]
    texts = set()
    for i, s in enumerate(sents, 1):
        p = f"sentence {i}: "
        if s.get("n") != i:
            errs.append(p + f"n must be {i}")
        for f in STR_FIELDS:
            if not isinstance(s.get(f), str) or not s.get(f).strip():
                errs.append(p + f"missing text field '{f}'")
        for f, k in LIST_MIN.items():
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
        if not 25 <= len(words) <= 35:
            errs.append(p + f"{len(words)} words; needs 25-35")
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
        if not str(s.get("url", "")).startswith("https://"):
            errs.append(p + "url must start with https://")
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
