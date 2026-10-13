#!/usr/bin/env python3
"""Objective statistics for a TOEFL writing response or speaking transcript.

  text_stats.py [FILE] [--task email|discussion|interview] [--seconds N] [--json]

Reads FILE (or stdin). Reports word/sentence counts, sentence length, repeated
content words and linking expressions, plus task-specific length benchmarks.
--seconds gives speaking rate (words per minute) for a transcript.
"""

import argparse
import json
import re
import sys
from collections import Counter

WORD_RE = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*|\d+(?:[.,]\d+)*")
SENT_RE = re.compile(r"[^.!?]+(?:[.!?]+|$)")

STOPWORDS = set("""
a an the and or but if so as of to in on at by for with from into about over after before than then
is am are was were be been being have has had do does did will would can could should may might must
i me my mine we us our you your he him his she her it its they them their this that these those there here
not no yes very too also just only more most much many some any all each every other such own same
what which who whom whose when where why how because while although though since until unless
one two first second also really think thing things lot get got make made go going say said
""".split())

LINKERS = [
    "however", "therefore", "moreover", "furthermore", "in addition", "additionally", "for example",
    "for instance", "on the other hand", "in contrast", "as a result", "consequently", "although",
    "even though", "whereas", "while", "because", "since", "first", "second", "finally", "overall",
    "in conclusion", "to be honest", "personally", "i believe", "in my opinion", "i think",
    "that said", "admittedly", "specifically", "in particular", "for one thing",
]

BENCHMARKS = {
    "email": "Write an Email：建议约 100–150 词，3 个要点都要展开；7 分钟内写完并留 1 分钟检查。",
    "discussion": "Academic Discussion：有效回答通常至少 100 词，高分常见 120–180 词；字数够了更要看展开质量。",
    "interview": "Take an Interview：45 秒内自然语速约 90–130 词；明显低于 80 词通常说明展开不足或停顿太多。",
}


def analyse(text, seconds=None):
    words = WORD_RE.findall(text)
    lower = [w.lower().replace("’", "'") for w in words]
    sentences = [s.strip() for s in SENT_RE.findall(" ".join(text.split())) if WORD_RE.search(s)]
    sent_lengths = [len(WORD_RE.findall(s)) for s in sentences]
    paragraphs = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]

    content = [w for w in lower if w not in STOPWORDS and w.isalpha() and len(w) > 2]
    repeated = [(w, c) for w, c in Counter(content).most_common() if c >= 3][:8]

    joined = " " + " ".join(lower) + " "
    linkers = {}
    for phrase in LINKERS:
        count = len(re.findall(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", joined))
        if count:
            linkers[phrase] = count

    stats = {
        "words": len(words),
        "sentences": len(sentences),
        "paragraphs": len(paragraphs),
        "avg_sentence_length": round(sum(sent_lengths) / len(sent_lengths), 1) if sent_lengths else 0,
        "longest_sentence": max(sent_lengths, default=0),
        "long_sentences_over_35": [s for s, n in zip(sentences, sent_lengths) if n > 35],
        "short_sentences_under_6": [s for s, n in zip(sentences, sent_lengths) if n < 6],
        "unique_word_ratio": round(len(set(lower)) / len(lower), 2) if lower else 0,
        "repeated_content_words": repeated,
        "linkers": linkers,
    }
    if seconds:
        stats["seconds"] = seconds
        stats["words_per_minute"] = round(len(words) / seconds * 60)
    return stats


def report(stats, task):
    print(f"字数：{stats['words']}    句数：{stats['sentences']}    段落：{stats['paragraphs']}")
    print(f"平均句长：{stats['avg_sentence_length']} 词    最长句：{stats['longest_sentence']} 词")
    print(f"词汇多样性（不重复词占比）：{stats['unique_word_ratio']}")
    if "words_per_minute" in stats:
        wpm = stats["words_per_minute"]
        note = "偏慢" if wpm < 110 else "偏快，注意清晰度" if wpm > 170 else "正常"
        print(f"语速：{wpm} 词/分钟（{stats['seconds']} 秒）— {note}")
    if stats["long_sentences_over_35"]:
        print("\n超过 35 词的长句（检查是否逗号连句 / 结构失控）：")
        for s in stats["long_sentences_over_35"]:
            print(f"  - {s}")
    if stats["short_sentences_under_6"]:
        print("\n少于 6 词的短句（偶尔用来强调可以，多了显得零碎）：")
        for s in stats["short_sentences_under_6"]:
            print(f"  - {s}")
    if stats["repeated_content_words"]:
        print("\n重复 3 次以上的实词（考虑同义替换）：")
        print("  " + ", ".join(f"{w}×{c}" for w, c in stats["repeated_content_words"]))
    if stats["linkers"]:
        print("\n使用的衔接表达：")
        print("  " + ", ".join(f"{w}×{c}" for w, c in stats["linkers"].items()))
    else:
        print("\n没有检测到常见衔接表达（however / for example / as a result 等）。")
    if task:
        print(f"\n参考：{BENCHMARKS[task]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", nargs="?", default="-")
    parser.add_argument("--task", choices=sorted(BENCHMARKS))
    parser.add_argument("--seconds", type=float, help="recording length, for words per minute")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    if not text.strip():
        sys.exit("没有读到文本。")
    stats = analyse(text, args.seconds)
    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        report(stats, args.task)


if __name__ == "__main__":
    main()
