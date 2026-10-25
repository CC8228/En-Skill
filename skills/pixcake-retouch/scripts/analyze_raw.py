#!/usr/bin/env python3
"""Diagnose one photo (RAW or JPEG/PNG/TIFF/HEIC-converted) before planning an edit.

  analyze_raw.py PHOTO [--out DIR] [--source auto|render|embedded] [--crop L,T,R,B] [--json]

Writes DIR/<name>_preview.jpg (look at it) and DIR/<name>_analysis.png (histogram,
tone zones, palette, HSL bands), then prints a Chinese report: EXIF, RAW clipping and
deep-shadow share, tone type (高/中/低 × 长/中/短调), black/white points as curve levels,
white-balance cast, shadow/midtone/highlight toning, saturation, HSL band breakdown,
skin-tone pixels and vignetting. --crop takes fractions, e.g. to cut Instagram UI out
of a screenshot: --crop 0,0.12,1,0.78 (the cropped preview can then go to compare_ref.py).
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw  # noqa: E402

import photo_stats as ps  # noqa: E402

BAND_RGB = {"红": (220, 40, 40), "橙": (240, 140, 30), "黄": (235, 210, 40), "绿": (60, 170, 60),
            "青": (40, 190, 190), "蓝": (40, 90, 220), "紫": (130, 60, 200), "洋红": (210, 50, 170)}
BAND_EN = {"红": "Red", "橙": "Orange", "黄": "Yellow", "绿": "Green", "青": "Aqua", "蓝": "Blue",
           "紫": "Purple", "洋红": "Magenta"}


def draw_chart(st, path):
    W, H = 900, 560
    im = Image.new("RGB", (W, H), (250, 250, 250))
    d = ImageDraw.Draw(im, "RGBA")
    # histogram
    x0, y0, w, h = 40, 30, 820, 220
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=(235, 235, 235))
    for zl in (10, 30, 70, 90):
        X = x0 + w * ps.lstar_to_level(zl) / 255
        d.line([X, y0, X, y0 + h], fill=(200, 200, 200))
    rgb = st["_hist"]["rgb"]
    peak = max(max(c[2:-2]) for c in rgb) or 1
    for ch, col in zip(rgb, [(220, 0, 0, 110), (0, 160, 0, 110), (0, 60, 230, 110)]):
        pts = [(x0 + w * i / 255, y0 + h - h * min(v / peak, 1)) for i, v in enumerate(ch)]
        d.polygon([(x0, y0 + h)] + pts + [(x0 + w, y0 + h)], fill=col)
    d.text((x0, 8), "RGB histogram 0-255 (grey lines: zone borders at L* 10/30/70/90)", fill=(60, 60, 60))
    d.text((x0, y0 + h + 4), f"clip high {st['clip_high_pct']:.1f}%   clip low {st['clip_low_pct']:.1f}%   "
                             f"tone range L* p2-p98 = {st['tone_range']:.0f}", fill=(60, 60, 60))
    # zones
    zy = 300
    d.text((x0, zy - 18), "tone zones: black / shadows / midtones / lights / highlights", fill=(60, 60, 60))
    X = x0
    for (name, lo, hi), shade in zip(ps.ZONES, [20, 70, 128, 190, 240]):
        seg = w * st["zones"][name] / 100
        d.rectangle([X, zy, X + seg, zy + 30], fill=(shade, shade, shade))
        if seg > 40:
            d.text((X + 4, zy + 9), f"{st['zones'][name]:.0f}%", fill=(255, 0, 0) if shade > 150 else (255, 255, 0))
        X += seg
    # palette
    py = 370
    d.text((x0, py - 18), "palette (k-means)", fill=(60, 60, 60))
    X = x0
    for p in st["palette"]:
        seg = w * p["share"] / sum(q["share"] for q in st["palette"])
        d.rectangle([X, py, X + seg, py + 40], fill=p["hex"])
        if seg > 60:
            d.text((X + 4, py + 44), f"{p['hex']} {p['share']:.0f}%", fill=(60, 60, 60))
        X += seg
    # hsl bands
    by = 470
    d.text((x0, by - 18), "colour share per HSL band (% of all pixels)", fill=(60, 60, 60))
    bw = w / 8
    top = max(max(v["share"] for v in st["hsl"].values()), 1)
    for i, (name, _, _) in enumerate(ps.HSL_BANDS):
        v = st["hsl"][name]["share"]
        bh = 60 * v / top
        bx = x0 + i * bw
        d.rectangle([bx + 8, by + 60 - bh, bx + bw - 8, by + 60], fill=BAND_RGB[name])
        d.text((bx + 8, by + 64), f"{BAND_EN[name]} {v:.0f}%", fill=(60, 60, 60))
    im.save(path)


def fmt_cast(c):
    if c is None:
        return "—"
    s = ps.describe_cast(c)
    if c["chroma"] >= 2:
        s += f"，色轮方向约 {c['wheel_hue']:.0f}°（{ps.hue_name(c['wheel_hue'])}）"
    return s


def report(st, meta):
    L = st["L"]
    out = []
    add = out.append
    add(f"== 文件 ==\n{meta['file']}  分析基于：{meta['rendered_from']}  分析尺寸 {meta['size'][0]}×{meta['size'][1]}")
    if meta.get("icc"):
        add(f"色彩配置文件：{meta['icc']}（已转换到 sRGB 再统计）")
    if meta["exif"]:
        add("  ".join(f"{k} {v}" for k, v in meta["exif"].items()))

    raw = meta["raw"]
    if raw:
        add("\n== RAW 数据 ==")
        add(f"传感器溢出：{raw['raw_clipped_pct']:.2f}%（这部分高光在 RAW 里也没有细节，降高光拉不回）")
        add(f"深暗部（比溢出点低 9 档以上）：{raw['raw_deep_shadow_pct']:.1f}%（这些区域大幅提亮会出噪点）")
        r = raw.get("wb_vs_daylight")
        if r:
            light = ("相机按冷光校正（往暖拉）：阴天、阴影、蓝调时刻，或画面里大片蓝色带偏了自动白平衡" if r > 1.15 else (
                "相机按暖光校正（往冷拉）：暖光室内、夕阳，或画面里大片暖色（落叶、木头、暖墙）带偏了自动白平衡"
                if r < 0.85 else "接近日光白平衡"))
            add(f"相机白平衡：{light}（红蓝倍率比 / 日光估计 = {r:.2f}，只看方向，数值是粗估）")

    add("\n== 影调 ==")
    add(f"影调类型：{st['tone_type']}（中位亮度 L* {L['p50']:.0f}，亮度跨度 p2–p98 = {st['tone_range']:.0f}）")
    add("亮度分布：" + " | ".join(f"{k} {v:.0f}%" for k, v in st["zones"].items()))
    add(f"黑位 p1 = L* {L['p1']:.0f}（≈ 曲线 {ps.lstar_to_level(L['p1'])}/255）  "
        f"白位 p99 = L* {L['p99']:.0f}（≈ 曲线 {ps.lstar_to_level(L['p99'])}/255）  亮度标准差 {L['std']:.1f}")
    add(f"溢出像素：高光 {st['clip_high_pct']:.2f}%  暗部 {st['clip_low_pct']:.2f}%")
    v = st["corner_minus_center"]
    add(f"四角相对中心：{'暗' if v < 0 else '亮'} {abs(v):.0f} L*（< -10 通常已有明显暗角或四周本来就暗）")

    add("\n== 色彩 ==")
    wb = st["wb"]
    add(f"整体白平衡：{fmt_cast(wb)}" + (f"  [依据：{wb['basis']}]" if wb else ""))
    names = {"shadows": "阴影", "midtones": "中间调", "highlights": "高光"}
    for z, c in st["toning"].items():
        if c:
            add(f"  {names[z]}（占画面 {c['zone_pct']:.0f}%）：{fmt_cast(c)}")
    add(f"鲜艳度：{st['colorfulness']:.0f}（{ps.colorfulness_word(st['colorfulness'])}），"
        f"平均彩度 C* {st['chroma_mean']:.1f}，p90 {st['chroma_p90']:.1f}")
    add("主色：" + "  ".join(f"{p['hex']} {p['share']:.0f}%" for p in st["palette"]))
    add("HSL 分布（占全图%｜平均色相°｜HSV 饱和度｜L*）：")
    for name, _, _ in ps.HSL_BANDS:
        b = st["hsl"][name]
        if b["share"] >= 1 and "hue" in b:
            add(f"  {name:<2} {b['share']:5.1f}% ｜ {b['hue']:5.0f}° ｜ 饱和 {b['sat']:4.0f} ｜ 明度 {b['L']:4.0f}")
    sk = st["skin"]
    if "hue" in sk:
        add(f"疑似肤色像素：{sk['share']:.1f}%（色相 {sk['hue']:.0f}°，饱和 {sk['sat']:.0f}，明度 L* {sk['L']:.0f}）"
            "——只是颜色范围判断，木头、沙地、暖色墙也会算进来")

    tips = []
    if raw and raw["raw_clipped_pct"] > 0.5:
        tips.append(f"有 {raw['raw_clipped_pct']:.1f}% 高光在传感器层面已溢出：别指望高光滑块救回，"
                    "考虑局部压暗、让它保持纯白，天空大面积溢出可考虑换天空")
    elif st["clip_high_pct"] > 1 and raw:
        tips.append("预览里有高光溢出，但 RAW 层面基本没溢出：降高光/白色可以拉回细节")
    elif st["clip_high_pct"] > 1:
        tips.append("高光有溢出（非 RAW 文件，溢出部分无法恢复）")
    if L["p50"] < 30:
        tips.append("整体偏暗，先提曝光/阴影再判断颜色")
    elif L["p50"] > 70:
        tips.append("整体偏亮，先确认是否有意做高调")
    iso = meta["exif"].get("ISO", "")
    if iso.isdigit() and int(iso) >= 3200:
        tips.append(f"ISO {iso}，提亮暗部前先开降噪（细节面板），提亮幅度越大噪点越明显")
    if raw and raw["raw_deep_shadow_pct"] > 25 and L["p50"] < 40:
        tips.append("大量深暗部：阴影提太多会脏，暗调风格反而顺势而为")
    if wb and wb["chroma"] >= 6:
        tips.append("整体偏色明显，先用白平衡或 AI 校准拉回中性，再决定要不要做风格偏色")
    if tips:
        add("\n== 先处理 ==")
        out.extend(f"- {t}" for t in tips)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photo")
    ap.add_argument("--out", default=None, help="输出目录（默认与照片同目录下的 retouch-analysis/）")
    ap.add_argument("--source", choices=["auto", "render", "embedded"], default="auto",
                    help="RAW 用内嵌预览还是中性渲染来统计（默认 auto：预览够大就用预览）")
    ap.add_argument("--crop", default=None, help="裁剪比例 左,上,右,下，例如 0,0.12,1,0.78")
    ap.add_argument("--json", action="store_true", help="输出 JSON 而不是中文报告")
    args = ap.parse_args()

    if not os.path.isfile(args.photo):
        raise SystemExit(f"找不到文件：{args.photo}")
    rgb, meta = ps.load_image(args.photo, source=args.source, crop=ps.parse_crop(args.crop))
    st = ps.measure(rgb)

    out_dir = args.out or os.path.join(os.path.dirname(os.path.abspath(args.photo)), "retouch-analysis")
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.photo))[0]
    preview = os.path.join(out_dir, f"{stem}_preview.jpg")
    chart = os.path.join(out_dir, f"{stem}_analysis.png")
    Image.fromarray(rgb).save(preview, quality=90)
    draw_chart(st, chart)

    if args.json:
        st.pop("_hist")
        print(json.dumps({"meta": meta, "stats": st, "preview": preview, "chart": chart},
                         ensure_ascii=False, indent=2))
    else:
        print(report(st, meta))
        print(f"\n预览图：{preview}\n分析图：{chart}")


if __name__ == "__main__":
    main()
