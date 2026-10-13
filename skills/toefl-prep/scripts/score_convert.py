#!/usr/bin/env python3
"""TOEFL iBT score conversion for the 2026 1-6 band scale.

Subcommands:
  to-band SCORE         legacy 0-120 total -> band (and CEFR)
  to-legacy BAND        band -> legacy 0-120 range
  overall R L S W       four section bands -> overall band
  target BAND --current R=4.5 L=4 S=4 W=4 [--min S=4]
                        how far the current section bands are from a target overall band
  section SCORE         ROUGH estimate: old 0-30 section score -> section band
                        (score x 4 looked up in the overall table; not an official mapping)

The band <-> 0-120 table is the ETS concordance for the overall score only.
Section-level bands do not map onto the old 0-30 section scores with this table.
"""

import argparse
import math
import sys

# (band, legacy_low, legacy_high, cefr)
TABLE = [
    (6.0, 114, 120, "C2"),
    (5.5, 107, 113, "C1"),
    (5.0, 95, 106, "C1"),
    (4.5, 86, 94, "B2"),
    (4.0, 72, 85, "B2"),
    (3.5, 58, 71, "B1"),
    (3.0, 44, 57, "B1"),
    (2.5, 34, 43, "A2"),
    (2.0, 24, 33, "A2"),
    (1.5, 12, 23, "A1"),
    (1.0, 0, 11, "A1"),
]
SECTIONS = {"R": "Reading", "L": "Listening", "S": "Speaking", "W": "Writing"}


def fmt(band):
    return f"{band:.1f}".rstrip("0").rstrip(".") if band != int(band) else f"{int(band)}"


def check_band(value):
    band = float(value)
    if band < 1 or band > 6 or (band * 2) != int(band * 2):
        raise argparse.ArgumentTypeError(f"band must be 1-6 in steps of 0.5, got {value}")
    return band


def row_for_band(band):
    for row in TABLE:
        if row[0] == band:
            return row
    raise ValueError(band)


def row_for_legacy(score):
    for row in TABLE:
        if row[1] <= score <= row[2]:
            return row
    raise ValueError(score)


def round_half_band(avg):
    # Nearest 0.5, ties rounded up (e.g. 4.25 -> 4.5).
    return math.floor(avg * 2 + 0.5) / 2


def overall(bands):
    avg = sum(bands) / len(bands)
    return avg, round_half_band(avg)


def cmd_to_band(args):
    score = args.score
    if not 0 <= score <= 120:
        sys.exit("score must be between 0 and 120")
    band, low, high, cefr = row_for_legacy(score)
    print(f"旧版总分 {score} → band {fmt(band)}（对应区间 {low}–{high}，CEFR {cefr}）")
    if score > low and band < 6:
        nxt = row_for_band(band + 0.5)
        print(
            f"注意：band {fmt(band)} 覆盖 {low}–{high}，区间下沿低于 {score}。"
            f"如果学校按 0–120 设门槛，band {fmt(band)} 不一定达标；"
            f"稳妥目标是 band {fmt(nxt[0])}（{nxt[1]}–{nxt[2]}），或向招生办确认是否接受 band 分数。"
        )


def cmd_to_legacy(args):
    band, low, high, cefr = row_for_band(args.band)
    print(f"band {fmt(band)} → 旧版总分 {low}–{high}（CEFR {cefr}）")


def cmd_overall(args):
    bands = [args.reading, args.listening, args.speaking, args.writing]
    avg, result = overall(bands)
    band, low, high, cefr = row_for_band(result)
    print(
        f"R {fmt(args.reading)} / L {fmt(args.listening)} / S {fmt(args.speaking)} / W {fmt(args.writing)}"
    )
    print(f"平均 {avg:.3f} → 总分 band {fmt(result)}（约 {low}–{high}，CEFR {cefr}）")
    if (avg * 4) % 2 == 1:
        print("注：平均分正好落在两档中间，这里按向上取整处理；官方舍入规则如有不同以成绩单为准。")


def cmd_section(args):
    score = args.score
    if not 0 <= score <= 30:
        sys.exit("单项分应在 0–30 之间")
    band, low, high, _ = row_for_legacy(score * 4)
    print(f"旧版单项 {score}/30 → 粗略估计单项 band {fmt(band)}（按 {score}×4={score * 4} 查总分表）")
    print("注意：这是粗略估算，ETS 各 section 的官方对照不同。学校给出单项要求时，"
          "优先查该校是否已公布新版 band 要求，或向招生办确认。")


def parse_pairs(pairs, label):
    result = {}
    for pair in pairs or []:
        try:
            key, value = pair.split("=", 1)
            key = key.strip().upper()[:1]
            if key not in SECTIONS:
                raise ValueError
            result[key] = check_band(value)
        except (ValueError, argparse.ArgumentTypeError):
            sys.exit(f"{label} 参数格式应为 R=4.5 L=4 S=4 W=4.5，收到：{pair}")
    return result


def cmd_target(args):
    current = parse_pairs(args.current, "--current")
    if set(current) != set(SECTIONS):
        sys.exit("--current 需要四个 section：R= L= S= W=")
    minimums = parse_pairs(args.min, "--min")
    target = args.band

    avg, now = overall(list(current.values()))
    print(f"当前：" + " / ".join(f"{k} {fmt(v)}" for k, v in current.items()) + f" → 总分 {fmt(now)}")
    print(f"目标总分：{fmt(target)}（约 {row_for_band(target)[1]}–{row_for_band(target)[2]}）")

    # Plan: first satisfy section minimums, then raise the lowest sections in 0.5 steps.
    plan = dict(current)
    for key, need in minimums.items():
        if plan[key] < need:
            plan[key] = need
    steps = 0
    while overall(list(plan.values()))[1] < target:
        key = min(plan, key=lambda k: (plan[k], k))
        if plan[key] >= 6:
            break
        plan[key] += 0.5
        steps += 1

    if plan == current:
        print("当前各项已达到目标总分和单项要求。")
        return
    print("\n达到目标的一种最省力组合（优先补单项要求，再从最低项开始每次 +0.5）：")
    for key in SECTIONS:
        delta = plan[key] - current[key]
        mark = f"  (+{fmt(delta)})" if delta > 0 else ""
        req = f"  [单项要求 ≥ {fmt(minimums[key])}]" if key in minimums else ""
        print(f"  {SECTIONS[key]:<9} {fmt(current[key])} → {fmt(plan[key])}{mark}{req}")
    print(f"新总分：{fmt(overall(list(plan.values()))[1])}")
    print("提示：最低项不一定最好提。结合 references/study-plan.md 的提分优先级，"
          "把 +0.5 分配到最容易提升的 section 上，只要单项要求仍满足即可。")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("to-band", help="legacy 0-120 -> band")
    p.add_argument("score", type=int)
    p.set_defaults(func=cmd_to_band)

    p = sub.add_parser("to-legacy", help="band -> legacy 0-120 range")
    p.add_argument("band", type=check_band)
    p.set_defaults(func=cmd_to_legacy)

    p = sub.add_parser("overall", help="section bands -> overall band")
    p.add_argument("--reading", "-r", type=check_band, required=True)
    p.add_argument("--listening", "-l", type=check_band, required=True)
    p.add_argument("--speaking", "-s", type=check_band, required=True)
    p.add_argument("--writing", "-w", type=check_band, required=True)
    p.set_defaults(func=cmd_overall)

    p = sub.add_parser("target", help="gap analysis toward a target overall band")
    p.add_argument("band", type=check_band)
    p.add_argument("--current", nargs=4, metavar="X=B", required=True)
    p.add_argument("--min", nargs="+", metavar="X=B", help="section minimums, e.g. S=4.5 W=4")
    p.set_defaults(func=cmd_target)

    p = sub.add_parser("section", help="ROUGH: old 0-30 section score -> band")
    p.add_argument("score", type=int)
    p.set_defaults(func=cmd_section)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
