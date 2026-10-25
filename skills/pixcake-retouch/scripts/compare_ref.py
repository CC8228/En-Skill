#!/usr/bin/env python3
"""Compare the user's photo with one or more reference images and turn the
differences into starting values for PixCake (像素蛋糕) sliders.

  compare_ref.py MINE REF [REF ...] [--source auto|render|embedded] [--json]

MINE may be RAW. REF are reference screenshots/exports; flat borders are trimmed
automatically, but Instagram UI (avatar row, buttons, caption) must be cropped
first, e.g. with analyze_raw.py REF --crop 0,0.12,1,0.78 and then using its
*_preview.jpg here. Several references are averaged and checked for consistency.

The numbers are statistics, not the blogger's actual settings: they say which
way and roughly how far to move each slider. Differences in scene content (more
sky, more skin, a darker background) also move the statistics, so read the
suggestions next to the images themselves.
"""

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import photo_stats as ps  # noqa: E402

BANDS = [b[0] for b in ps.HSL_BANDS]


def clamp_round(v, lo, hi, step=5):
    return int(max(lo, min(hi, step * round(v / step))))


def mag_word(d):
    d = abs(d)
    return "小幅" if d < 4 else ("中幅" if d < 8 else "大幅")


def metrics(st):
    L = st["L"]
    m = {
        "p1": L["p1"], "p5": L["p5"], "p50": L["p50"], "p95": L["p95"], "p99": L["p99"],
        "upper": L["p95"] - L["p50"], "lower": L["p50"] - L["p5"],
        "range": L["p95"] - L["p5"],
        "bright_share": st["zones"]["亮部"] + st["zones"]["高光"],
        "dark_share": st["zones"]["死黑"] + st["zones"]["暗部"],
        "clip_high": st["clip_high_pct"],
        "colorfulness": st["colorfulness"], "chroma": st["chroma_mean"],
        "vignette": st["corner_minus_center"],
        "wb": st["wb"], "toning": st["toning"], "hsl": st["hsl"], "skin": st["skin"],
        "tone_type": st["tone_type"],
    }
    return m


def average(ms):
    """Average several reference metric dicts (circular mean for hues)."""
    if len(ms) == 1:
        return ms[0]
    out = {}
    for k in ("p1", "p5", "p50", "p95", "p99", "upper", "lower", "range", "bright_share",
              "dark_share", "clip_high", "colorfulness", "chroma", "vignette"):
        out[k] = sum(m[k] for m in ms) / len(ms)
    out["tone_type"] = "/".join(dict.fromkeys(m["tone_type"] for m in ms))

    def avg_cast(cs):
        cs = [c for c in cs if c]
        if not cs:
            return None
        a = sum(c["a"] for c in cs) / len(cs)
        b = sum(c["b"] for c in cs) / len(cs)
        basis = cs[0]["basis"] if all(c["basis"] == cs[0]["basis"] for c in cs) else "混合"
        return {"a": a, "b": b, "chroma": math.hypot(a, b), "wheel_hue": ps.wheel_hue(a, b), "basis": basis,
                "zone_pct": sum(c["zone_pct"] for c in cs) / len(cs)}

    out["wb"] = avg_cast([m["wb"] for m in ms])
    out["toning"] = {z: avg_cast([m["toning"][z] for m in ms]) for z in ps.TONE_ZONES}

    def avg_colour(items):
        items = [i for i in items if "hue" in i]
        res = {"share": sum(i["share"] for i in items) / len(items) if items else 0.0}
        if items:
            res["hue"] = ps.circ_mean([i["hue"] for i in items])
            res["sat"] = sum(i["sat"] for i in items) / len(items)
            res["L"] = sum(i["L"] for i in items) / len(items)
        return res

    out["hsl"] = {b: avg_colour([m["hsl"][b] for m in ms]) for b in BANDS}
    out["skin"] = avg_colour([m["skin"] for m in ms])
    return out


def spread_warnings(ms):
    if len(ms) < 2:
        return []
    checks = [("p50", 8, "整体亮度"), ("range", 10, "对比/亮度跨度"), ("colorfulness", 12, "鲜艳度")]
    warns = []
    for k, lim, name in checks:
        vals = [m[k] for m in ms]
        if max(vals) - min(vals) > 2 * lim:
            warns.append(f"{name}：各参考图差别大（{min(vals):.0f}–{max(vals):.0f}），这一项以肉眼挑最像的那张为准")
    bs = [m["wb"]["b"] for m in ms if m["wb"]]
    if len(bs) >= 2 and max(bs) - min(bs) > 8:
        warns.append("冷暖：参考图之间冷暖不一致，可能混了不同风格的图")
    return warns


def neighbour(band, step):
    i = BANDS.index(band)
    return BANDS[(i + step) % len(BANDS)]


def suggest(me, ref, mine_meta):
    s = {"白平衡": [], "影调": [], "曲线": [], "HSL": [], "颜色分级": [], "效果": []}
    is_raw = mine_meta.get("raw") is not None

    # white balance (neutral-pixel cast)
    if me["wb"] and ref["wb"]:
        db, da = ref["wb"]["b"] - me["wb"]["b"], ref["wb"]["a"] - me["wb"]["a"]
        weak = ("（依据是整片区域而非中性像素，参考性低）" if "整个区域" in me["wb"]["basis"] + ref["wb"]["basis"]
                else "（先看参考图里本该是白/灰的东西——白衣、白墙、云——确认确实偏这个方向）")
        if abs(db) >= 2:
            verb = "加" if db > 0 else "减"
            amount = ({"小幅": "200–500K", "中幅": "500–1000K", "大幅": "1000K 以上"} if is_raw
                      else {"小幅": "5–10", "中幅": "10–20", "大幅": "20 以上"})[mag_word(db)]
            s["白平衡"].append(f"色温 → {'往暖（右）' if db > 0 else '往冷（左）'}{mag_word(db)}，{verb}约 {amount}"
                            f"（参考图中性色 b* 比你{'高' if db > 0 else '低'} {abs(db):.1f}）{weak}")
        if abs(da) >= 2:
            amount = {"小幅": "3–6", "中幅": "6–12", "大幅": "12 以上"}[mag_word(da)]
            s["白平衡"].append(f"色调 → {'往洋红（右）' if da > 0 else '往绿（左）'}{mag_word(da)}，"
                            f"{'加' if da > 0 else '减'}约 {amount}"
                            f"（a* 差 {da:+.1f}）{weak}")

    # exposure
    d50 = ref["p50"] - me["p50"]
    if abs(d50) >= 3:
        ev = round(d50 / 15, 1)
        line = f"曝光 {ev:+.1f} 左右（参考中位亮度 L* {ref['p50']:.0f}，你的 {me['p50']:.0f}）"
        if "中性 RAW 渲染" in mine_meta.get("rendered_from", ""):
            line += "；你的照片是按中性渲染统计的，像素蛋糕里打开会更亮，先加一半再看"
        s["影调"].append(line)

    # contrast / highlights / shadows from the spread above and below the median
    du, dl = ref["upper"] - me["upper"], ref["lower"] - me["lower"]
    common = math.copysign(min(abs(du), abs(dl)), du) if du * dl > 0 else 0.0
    if abs(common) >= 3:
        s["影调"].append(f"对比度 {clamp_round(common * 1.5, -60, 60):+d}（参考亮度跨度 {ref['range']:.0f}，你的 {me['range']:.0f}）")
    ru, rl = du - common, dl - common
    if me["clip_high"] > 0.5 and ref["clip_high"] < me["clip_high"] / 2:
        s["影调"].append(f"高光 {min(-20, clamp_round(ru * 3, -70, -20)):+d} 起（你有 {me['clip_high']:.1f}% 高光溢出，参考 {ref['clip_high']:.1f}%）")
    elif abs(ru) >= 3:
        s["影调"].append(f"高光 {clamp_round(ru * 3, -60, 60):+d}（参考图亮部{'拉得更开' if ru > 0 else '更收、更柔'}）")
    if abs(rl) >= 3:
        s["影调"].append(f"阴影 {clamp_round(-rl * 3, -60, 60):+d}（参考图暗部{'更深' if rl > 0 else '更亮、更通透'}）")

    # black / white points
    if ref["p1"] >= 6 and ref["p1"] - me["p1"] >= 4:
        lo_me, lo_ref = ps.lstar_to_level(me["p1"]), ps.lstar_to_level(ref["p1"])
        lift = clamp_round((lo_ref - lo_me) / (1 - lo_me / 255), 5, 80)
        s["曲线"].append(f"RGB 曲线左下端点上抬到输出约 {lift}（参考图黑位发灰/哑光：最暗处约 {lo_ref}/255，你的约 {lo_me}/255）")
    elif me["p1"] - ref["p1"] >= 4:
        s["影调"].append(f"黑色 {clamp_round((ref['p1'] - me['p1']) * 3, -60, -5):+d}（参考图黑位更实）")
    if ref["p99"] <= 94 and me["p99"] - ref["p99"] >= 4:
        hi_me, hi_ref = ps.lstar_to_level(me["p99"]), ps.lstar_to_level(ref["p99"])
        top = clamp_round(255 * hi_ref / max(hi_me, 1), 175, 250)
        s["曲线"].append(f"RGB 曲线右上端点下压到输出约 {top}（参考图最亮处不到纯白：约 {hi_ref}/255，你的约 {hi_me}/255）")
    elif ref["p99"] - me["p99"] >= 4:
        s["影调"].append(f"白色 {clamp_round((ref['p99'] - me['p99']) * 3, 5, 60):+d}（参考图亮部更通透）")

    # global saturation
    g = ref["colorfulness"] / me["colorfulness"] if me["colorfulness"] > 1 else 1.0
    if g < 0.85:
        s["影调"].append(f"饱和度 {clamp_round((g - 1) * 100, -60, -5):+d}（参考鲜艳度 {ref['colorfulness']:.0f}，你的 "
                        f"{me['colorfulness']:.0f}；也可以先只降 HSL 里抢眼的颜色）")
    elif g > 1.15:
        s["影调"].append(f"自然饱和度 {clamp_round((g - 1) * 100, 5, 40):+d}（参考鲜艳度 {ref['colorfulness']:.0f}，你的 "
                        f"{me['colorfulness']:.0f}）")
    g = min(max(g, 0.4), 2.0)

    # HSL bands; skin-tone pixels override the generic orange band
    def band_lines(name, a, b, label):
        out = []
        dh = ps.circ_diff(b["hue"], a["hue"])
        if abs(dh) >= 4:
            v = clamp_round(dh * 3, -60, 60)
            out.append(f"色相 {v:+d}（往{neighbour(name, 1 if dh > 0 else -1)}偏，参考 {b['hue']:.0f}° vs 你 {a['hue']:.0f}°）")
        r = (b["sat"] / a["sat"]) / g if a["sat"] > 1 else 1
        if r < 0.85 or r > 1.15:
            out.append(f"饱和度 {clamp_round((r - 1) * 100, -70, 70):+d}")
        dL = (b["L"] - a["L"]) - d50
        if abs(dL) >= 4:
            out.append(f"明亮度 {clamp_round(dL * 3, -60, 60):+d}")
        if out:
            s["HSL"].append(f"{label}：" + "，".join(out))

    skin_done = False
    if me["skin"].get("hue") is not None and ref["skin"].get("hue") is not None \
            and me["skin"]["share"] >= 2 and ref["skin"]["share"] >= 2:
        band_lines("橙", me["skin"], ref["skin"], "橙（按肤色像素算）")
        skin_done = True
    for name in BANDS:
        if name == "橙" and skin_done:
            continue
        a, b = me["hsl"][name], ref["hsl"][name]
        if "hue" in a and "hue" in b and a["share"] >= 3 and b["share"] >= 3:
            band_lines(name, a, b, name)

    # colour grading: zone casts beyond the global shift
    base = None
    if me["toning"]["midtones"] and ref["toning"]["midtones"]:
        base = (ref["toning"]["midtones"]["a"] - me["toning"]["midtones"]["a"],
                ref["toning"]["midtones"]["b"] - me["toning"]["midtones"]["b"])
    for z, label in (("shadows", "阴影"), ("highlights", "高光")):
        a, b = me["toning"][z], ref["toning"][z]
        if not (a and b and base) or min(a["zone_pct"], b["zone_pct"]) < 3:
            continue
        ra, rb = (b["a"] - a["a"]) - base[0], (b["b"] - a["b"]) - base[1]
        mag = math.hypot(ra, rb)
        if mag >= 2.5:
            h = ps.wheel_hue(ra, rb)
            s["颜色分级"].append(f"{label}：色相约 {h:.0f}°（{ps.hue_name(h)}），饱和度约 {clamp_round(mag * 4, 5, 50)}"
                              f"（参考图{label}比你的多一层{ps.hue_name(h)}色）")
    sh, hi = ref["toning"]["shadows"], ref["toning"]["highlights"]
    if sh and hi and sh["chroma"] >= 4 and hi["chroma"] >= 4 and \
            abs(ps.circ_diff(sh["wheel_hue"], hi["wheel_hue"])) >= 90:
        s["颜色分级"].append(f"参考图本身是分离色调：阴影偏{ps.hue_name(sh['wheel_hue'])}、高光偏{ps.hue_name(hi['wheel_hue'])}")

    dv = ref["vignette"] - me["vignette"]
    if dv <= -6:
        s["效果"].append(f"暗角 {clamp_round(dv * 2.5, -50, -5):+d}（参考图四周比中心更暗；如果是构图/背景本来就暗则忽略）")
    elif dv >= 6:
        s["效果"].append("你的四角比参考暗：镜头调整里开暗角校正，或暗角往正方向少量加")
    return s


def table(me, ref):
    rows = [
        ("影调类型", me["tone_type"], ref["tone_type"], ""),
        ("中位亮度 L*", f"{me['p50']:.0f}", f"{ref['p50']:.0f}", f"{ref['p50'] - me['p50']:+.0f}"),
        ("亮度跨度 p5–p95", f"{me['range']:.0f}", f"{ref['range']:.0f}", f"{ref['range'] - me['range']:+.0f}"),
        ("黑位 p1 / 白位 p99", f"{me['p1']:.0f} / {me['p99']:.0f}", f"{ref['p1']:.0f} / {ref['p99']:.0f}", ""),
        ("暗部 / 亮部占比 %", f"{me['dark_share']:.0f} / {me['bright_share']:.0f}",
         f"{ref['dark_share']:.0f} / {ref['bright_share']:.0f}", ""),
        ("鲜艳度", f"{me['colorfulness']:.0f}", f"{ref['colorfulness']:.0f}",
         f"{ref['colorfulness'] - me['colorfulness']:+.0f}"),
        ("整体白平衡", ps.describe_cast(me["wb"]), ps.describe_cast(ref["wb"]), ""),
        ("阴影色", ps.describe_cast(me["toning"]["shadows"]), ps.describe_cast(ref["toning"]["shadows"]), ""),
        ("高光色", ps.describe_cast(me["toning"]["highlights"]), ps.describe_cast(ref["toning"]["highlights"]), ""),
        ("四角-中心 L*", f"{me['vignette']:+.0f}", f"{ref['vignette']:+.0f}", ""),
    ]
    for name in BANDS:
        a, b = me["hsl"][name], ref["hsl"][name]
        if "hue" in a and "hue" in b and a["share"] >= 3 and b["share"] >= 3:
            rows.append((f"{name}（色相/饱和/明度）", f"{a['hue']:.0f}°/{a['sat']:.0f}/{a['L']:.0f}",
                         f"{b['hue']:.0f}°/{b['sat']:.0f}/{b['L']:.0f}", ""))
    if me["skin"].get("hue") is not None and ref["skin"].get("hue") is not None:
        a, b = me["skin"], ref["skin"]
        rows.append(("肤色像素（色相/饱和/明度）", f"{a['hue']:.0f}°/{a['sat']:.0f}/{a['L']:.0f}",
                     f"{b['hue']:.0f}°/{b['sat']:.0f}/{b['L']:.0f}", ""))
    lines = ["| 指标 | 你的照片 | 参考 | 差 |", "|---|---|---|---|"]
    lines += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |" for r in rows]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mine")
    ap.add_argument("refs", nargs="+")
    ap.add_argument("--source", choices=["auto", "render", "embedded"], default="auto",
                    help="你的照片是 RAW 时用哪种方式统计（同 analyze_raw.py）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    for p in [args.mine] + args.refs:
        if not os.path.isfile(p):
            raise SystemExit(f"找不到文件：{p}")
    rgb, mine_meta = ps.load_image(args.mine, source=args.source)
    me = metrics(ps.measure(rgb))
    ref_ms = [metrics(ps.measure(ps.load_image(p)[0])) for p in args.refs]
    ref = average(ref_ms)
    sugg = suggest(me, ref, mine_meta)
    warns = spread_warnings(ref_ms)

    if args.json:
        print(json.dumps({"mine": me, "reference": ref, "suggestions": sugg, "warnings": warns},
                         ensure_ascii=False, indent=2))
        return

    print(f"== 你的照片 vs 参考（{len(args.refs)} 张{'，取平均' if len(args.refs) > 1 else ''}）==")
    print(f"你的照片统计基于：{mine_meta['rendered_from']}\n")
    print(table(me, ref))
    print("\n== 建议起步值（像素蛋糕，按面板顺序；数值是方向和量级，不是博主原参数）==")
    any_s = False
    for panel, items in sugg.items():
        if items:
            any_s = True
            print(f"{panel}：")
            for it in items:
                print(f"  - {it}")
    if not any_s:
        print("统计上已经很接近，差别在局部（光比、肤色质感、局部亮度），靠肉眼对比调。")
    print("\n== 注意 ==")
    for w in warns:
        print(f"- {w}")
    print("- 画面内容不同（天空/肤色/背景多少）会影响统计；建议和预览图对照着看，内容差异大的项以肉眼为准。")
    print("- 颗粒、清晰度、锐化、磨皮这类质感，截图压缩后测不准，靠看图判断。")


if __name__ == "__main__":
    main()
