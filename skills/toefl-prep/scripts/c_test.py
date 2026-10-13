#!/usr/bin/env python3
"""Build and grade TOEFL "Complete the Words" items (C-test style).

  make [FILE]                 read a paragraph (file or stdin) and print the gapped version + key
       --blanks N             number of gaps (default 10)
       --plain                plain-text underscores instead of Markdown-escaped ones
       --key-out KEY.json     also save the answer key for `check`
  check KEY.json ANSWER...    grade answers; each answer may be the full word or only the missing letters

Rules (same as the classic C-test the TOEFL task is based on):
- The first sentence stays intact; with 3+ sentences the last one stays intact too.
- Starting with the 2nd word of the 2nd sentence, every second word loses its second half.
  A word of n letters keeps its first n // 2 letters (might -> mi___, that -> th__).
- One-letter words, numbers, hyphenated or apostrophe words and capitalised words
  inside a sentence (likely proper nouns) are skipped; the next usable word takes the gap.
"""

import argparse
import json
import re
import sys

WORD_RE = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")
SENTENCE_RE = re.compile(r"(?<=[.!?])[\"”']?\s+(?=[\"“']?[A-Z])")


def split_sentences(text):
    """Return (start, end) spans of sentences in text."""
    spans, start = [], 0
    for m in SENTENCE_RE.finditer(text):
        spans.append((start, m.start()))
        start = m.end()
    spans.append((start, len(text)))
    return [(s, e) for s, e in spans if text[s:e].strip()]


def eligible(word, first_in_sentence):
    if len(word) < 2 or not word.isalpha():
        return False
    if word.isupper():  # acronyms such as DNA
        return False
    if word[0].isupper() and not first_in_sentence:  # probable proper noun
        return False
    return True


def pick_gaps(text, sentences, zone, blanks):
    gaps, want = [], False
    for idx in zone:
        s, e = sentences[idx]
        for n, m in enumerate(WORD_RE.finditer(text, s, e)):
            if len(gaps) == blanks:
                return gaps
            if not want:
                want = True
                continue
            if eligible(m.group(), n == 0):
                gaps.append(m)
                want = False
    return gaps


def make(text, blanks, plain):
    text = " ".join(text.split())
    sentences = split_sentences(text)
    if len(sentences) < 2:
        sys.exit("需要至少两句话：第一句保持完整，从第二句开始挖空。")

    zone = list(range(1, len(sentences) - 1)) if len(sentences) >= 3 else [1]
    gaps = pick_gaps(text, sentences, zone, blanks)
    if len(gaps) < blanks and len(sentences) >= 3:
        gaps = pick_gaps(text, sentences, range(1, len(sentences)), blanks)
        if len(gaps) == blanks:
            print("提示：中间句子不够长，最后一句也被挖空了。", file=sys.stderr)
    if len(gaps) < blanks:
        print(f"提示：文本太短，只生成了 {len(gaps)} 个空（要求 {blanks} 个）。", file=sys.stderr)

    blank = "_" if plain else "\\_"
    out, key, pos = [], [], 0
    for i, m in enumerate(gaps, 1):
        word = m.group()
        keep = len(word) // 2
        missing = word[keep:]
        out.append(text[pos:m.start()])
        out.append(f"{word[:keep]}{blank * len(missing)}[{i}]")
        key.append({"n": i, "word": word, "shown": word[:keep], "missing": missing})
        pos = m.end()
    out.append(text[pos:])
    return "".join(out), key


def normalise(s):
    return s.strip().lower().replace("’", "'")


def check(key, answers):
    if len(answers) == 1 and len(key) > 1:
        answers = re.split(r"[\s,;]+", answers[0].strip())
    correct = 0
    for item in key:
        i = item["n"] - 1
        given = normalise(answers[i]) if i < len(answers) else ""
        ok = given in (normalise(item["missing"]), normalise(item["word"]))
        correct += ok
        mark = "✓" if ok else "✗"
        shown = given or "（未作答）"
        print(f"{item['n']:>2}. {mark} {item['shown']}+{item['missing']} = {item['word']}    你的答案：{shown}")
    print(f"\n得分：{correct}/{len(key)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("make")
    p.add_argument("file", nargs="?", default="-")
    p.add_argument("--blanks", type=int, default=10)
    p.add_argument("--plain", action="store_true")
    p.add_argument("--key-out")

    p = sub.add_parser("check")
    p.add_argument("key")
    p.add_argument("answers", nargs="+")

    args = parser.parse_args()
    if args.cmd == "make":
        text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
        gapped, key = make(text, args.blanks, args.plain)
        print("## 题目（每条下划线代表一个缺失字母，[n] 是空的编号）\n")
        print(gapped)
        print("\n## 答案（批改前不要展示给考生）\n")
        for item in key:
            print(f"{item['n']}. {item['shown']}+{item['missing']} = {item['word']}")
        if args.key_out:
            with open(args.key_out, "w", encoding="utf-8") as f:
                json.dump(key, f, ensure_ascii=False, indent=2)
    else:
        with open(args.key, encoding="utf-8") as f:
            key = json.load(f)
        check(key, args.answers)


if __name__ == "__main__":
    main()
