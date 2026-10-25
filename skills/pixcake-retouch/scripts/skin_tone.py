#!/usr/bin/env python3
"""Compare face skin tone between the user's photo and reference images.

  skin_tone.py --mine PHOTO L,T,R,B --ref REF L,T,R,B [--ref REF2 L,T,R,B ...]

Each box is the lit part of a face (cheeks/forehead, avoiding glasses, hair and
specular highlights) as fractions of the image after orientation, e.g.
0.36,0.26,0.44,0.30. Whole-image "skin-coloured pixel" statistics are easily
fooled by autumn leaves, wood or golden-lit fabric; a face box is not.

Prints median L*, a*, b*, hue and chroma per face, then which way to move
PixCake's orange (and red) HSL sliders, white balance and subject exposure.

  skin_tone.py --region --label 米色外套 --mine PHOTO BOX --ref REF BOX ...

--region compares any like-for-like object instead of skin (a beige jacket with a
beige jacket, denim with denim, tree foliage with foliage), using the brighter half
of the box so a half-shadowed object is compared by its lit side. For near-neutral
objects it gives white balance; for coloured ones the HSL band to move. Matching
objects is the most reliable white-balance check when whole-image neutral pixels
are polluted by sky, jeans or leaves.
"""

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402

import photo_stats as ps  # noqa: E402


def clamp_round(v, lo, hi, step=5):
    return int(max(lo, min(hi, step * round(v / step))))


def face_stats(path, box, skin=True):
    rgb, _ = ps.load_image(path)
    h, w = rgb.shape[:2]
    l, t, r, b = box
    crop = rgb[int(t * h):int(b * h), int(l * w):int(r * w)].reshape(-1, 3)
    L, a, bb = ps.rgb8_to_lab(crop)
    H, S, _ = ps.rgb_to_hsv(crop)
    if skin:
        m = (L > 25) & (L < 92) & (a > 3) & (bb > 3)  # drop hair, glasses, eyes and blown specular spots
    else:
        # objects are often half in shadow under side light: compare the lit half only
        m = (L > 2) & (L < 99)
        m &= L >= np.median(L[m]) if m.any() else m
    if m.sum() < 50:
        raise SystemExit(f"{os.path.basename(path)}：框里几乎没有可用像素，检查框的位置（左,上,右,下 比例）")
    st = {"L": float(np.median(L[m])), "a": float(np.median(a[m])), "b": float(np.median(bb[m])),
          "hsv_hue": ps.circ_mean(H[m]), "hsv_sat": float(np.median(S[m]) * 100), "n": int(m.sum()),
          "p90": float(np.percentile(L[m], 90))}
    st["lab_hue"] = math.degrees(math.atan2(st["b"], st["a"]))
    st["chroma"] = math.hypot(st["a"], st["b"])
    return st


def describe(st):
    return (f"L* {st['L']:4.1f}  a* {st['a']:5.1f}  b* {st['b']:5.1f}  色相 {st['lab_hue']:4.1f}°"
            f"（HSV {st['hsv_hue']:4.1f}°）  彩度 C* {st['chroma']:4.1f}  亮部 p90 L* {st['p90']:4.1f}  像素 {st['n']}")


def mag(d):
    d = abs(d)
    return "小幅" if d < 4 else ("中幅" if d < 8 else "大幅")


def region_advice(label, me, ref, dh, ratio, dL):
    print(f"\n== {label}：同类物体对比（像素蛋糕；起步值）==")
    db, da = ref["b"] - me["b"], ref["a"] - me["a"]
    neutral = me["chroma"] < 18 and ref["chroma"] < 18
    if neutral:
        # near-neutral object: its colour difference is the white balance difference
        if abs(db) >= 2:
            print(f"- 色温 → {'往暖' if db > 0 else '往冷'}{mag(db)}（b* {me['b']:+.1f} → {ref['b']:+.1f}）："
                  f"RAW 约 {'+' if db > 0 else '-'}{ {'小幅': '200–500', '中幅': '500–1000', '大幅': '1000 以上'}[mag(db)] }K")
        if abs(da) >= 2:
            print(f"- 色调 → {'往洋红' if da > 0 else '往绿'}{mag(da)}（a* {me['a']:+.1f} → {ref['a']:+.1f}）")
        if abs(db) < 2 and abs(da) < 2:
            print(f"- 颜色已经一致（a* {me['a']:+.1f}/{ref['a']:+.1f}，b* {me['b']:+.1f}/{ref['b']:+.1f}），白平衡不用动")
    else:
        band = ps.hue_name(me["hsv_hue"])
        parts = []
        if abs(dh) >= 3:
            parts.append(f"色相 {clamp_round(dh * 3, -40, 40):+d}")
        if ratio < 0.85 or ratio > 1.15:
            parts.append(f"饱和度 {clamp_round((ratio - 1) * 100, -60, 60):+d}")
        if abs(dL) >= 4:
            parts.append(f"明亮度 {clamp_round(dL * 2, -40, 40):+d}")
        if parts:
            print(f"- HSL {band}：" + "，".join(parts) + f"（HSV 色相 {me['hsv_hue']:.0f}° → {ref['hsv_hue']:.0f}°，"
                  f"彩度 {me['chroma']:.0f} → {ref['chroma']:.0f}，L* {me['L']:.0f} → {ref['L']:.0f}）")
        else:
            print("- 颜色已经接近，不用动")
    if abs(dL) >= 4 and neutral:
        print(f"- 亮度：参考{'更亮' if dL > 0 else '更暗'}（L* {me['L']:.0f} → {ref['L']:.0f}），"
              f"亮部物体用高光/白色，暗部物体用阴影/黑色或局部调色")
    print("- 两边光线条件（直射/阴影）要一致才有意义；截图压缩误差约 ±2 L* / ±3 彩度。")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mine", nargs=2, metavar=("PHOTO", "BOX"), required=True)
    ap.add_argument("--ref", nargs=2, metavar=("REF", "BOX"), action="append", required=True)
    ap.add_argument("--region", action="store_true", help="比较任意同类物体（不过滤肤色）")
    ap.add_argument("--label", default="物体", help="--region 时物体的名字，例如 米色外套、牛仔裤、树叶")
    args = ap.parse_args()

    me = face_stats(args.mine[0], ps.parse_crop(args.mine[1]), skin=not args.region)
    refs = [face_stats(p, ps.parse_crop(b), skin=not args.region) for p, b in args.ref]
    print(f"你的照片  {describe(me)}")
    for (p, _), st in zip(args.ref, refs):
        print(f"{os.path.basename(p)[:8]:8s}  {describe(st)}")

    ref = {k: sum(r[k] for r in refs) / len(refs) for k in ("L", "a", "b", "chroma", "lab_hue", "p90")}
    ref["hsv_hue"] = ps.circ_mean([r["hsv_hue"] for r in refs])
    dh = ps.circ_diff(ref["hsv_hue"], me["hsv_hue"])
    ratio = ref["chroma"] / me["chroma"] if me["chroma"] > 1 else 1.0
    dL = ref["L"] - me["L"]

    if args.region:
        region_advice(args.label, me, ref, dh, ratio, dL)
        return

    print("\n== 肤色建议（像素蛋糕；起步值，调完看脸）==")
    if abs(dh) >= 2:
        print(f"- HSL 橙 色相 {clamp_round(dh * 3, -40, 40):+d}：参考肤色更{'偏黄/金' if dh > 0 else '偏红/粉'}"
              f"（HSV {ref['hsv_hue']:.0f}° vs 你 {me['hsv_hue']:.0f}°）；整体光线也偏这个方向时，先用色温"
              f"{'加暖' if dh > 0 else '减暖'}，剩下的再交给橙色色相")
    if ratio < 0.85 or ratio > 1.15:
        print(f"- HSL 橙 饱和度 {clamp_round((ratio - 1) * 100, -60, 60):+d}：参考肤色{'更浓' if ratio > 1 else '更淡'}"
              f"（C* {ref['chroma']:.0f} vs 你 {me['chroma']:.0f}）；加暖白平衡和高光的颜色分级也会提高肤色饱和，"
              "这一项最后再补")
    dhi = ref["p90"] - me["p90"]
    if dhi <= -6:
        print(f"- 脸上的亮部比参考亮（亮部 p90 L* {me['p90']:.0f} vs {ref['p90']:.0f}）：先压高光、白色"
              "（或局部调色在脸上降高光），让亮部收住、留一层光泽，再看整体肤色要不要压暗")
        dL -= dhi / 4  # compressing the hot highlights also lowers the median a little
    if abs(dL) >= 3:
        print(f"- 肤色明暗：参考{'更亮' if dL > 0 else '更暗、更“实”'}（L* {ref['L']:.0f} vs 你 {me['L']:.0f}）。"
              f"HSL 橙 明亮度 {clamp_round(dL * 2, -30, 30):+d}，或局部调色里主体曝光 {dL / 15:+.1f}")
    da = ref["a"] - me["a"]
    if abs(da) >= 3 and abs(dh) < 2:
        print(f"- 红润度：参考 a* {'高' if da > 0 else '低'} {abs(da):.0f}，HSL 红 饱和度 {clamp_round(da * 2, -30, 30):+d}")
    print("- 截图经过压缩和平台调色，误差约 ±2 L* / ±3 彩度；差距小于这个范围的不用追。")


if __name__ == "__main__":
    main()
