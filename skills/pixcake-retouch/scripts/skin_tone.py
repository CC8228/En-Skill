#!/usr/bin/env python3
"""Compare face skin tone between the user's photo and reference images.

  skin_tone.py --mine PHOTO L,T,R,B --ref REF L,T,R,B [--ref REF2 L,T,R,B ...]

Each box is the lit part of a face (cheeks/forehead, avoiding glasses, hair and
specular highlights) as fractions of the image after orientation, e.g.
0.36,0.26,0.44,0.30. Whole-image "skin-coloured pixel" statistics are easily
fooled by autumn leaves, wood or golden-lit fabric; a face box is not.

Prints median L*, a*, b*, hue and chroma per face, then which way to move
PixCake's orange (and red) HSL sliders, white balance and subject exposure.
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


def face_stats(path, box):
    rgb, _ = ps.load_image(path)
    h, w = rgb.shape[:2]
    l, t, r, b = box
    crop = rgb[int(t * h):int(b * h), int(l * w):int(r * w)].reshape(-1, 3)
    L, a, bb = ps.rgb8_to_lab(crop)
    H, S, _ = ps.rgb_to_hsv(crop)
    m = (L > 25) & (L < 92) & (a > 3) & (bb > 3)  # drop hair, glasses, eyes and blown specular spots
    if m.sum() < 50:
        raise SystemExit(f"{os.path.basename(path)}：框里几乎没有肤色像素，检查框的位置（左,上,右,下 比例）")
    st = {"L": float(np.median(L[m])), "a": float(np.median(a[m])), "b": float(np.median(bb[m])),
          "hsv_hue": ps.circ_mean(H[m]), "hsv_sat": float(np.median(S[m]) * 100), "n": int(m.sum()),
          "p90": float(np.percentile(L[m], 90))}
    st["lab_hue"] = math.degrees(math.atan2(st["b"], st["a"]))
    st["chroma"] = math.hypot(st["a"], st["b"])
    return st


def describe(st):
    return (f"L* {st['L']:4.1f}  a* {st['a']:5.1f}  b* {st['b']:5.1f}  色相 {st['lab_hue']:4.1f}°"
            f"（HSV {st['hsv_hue']:4.1f}°）  彩度 C* {st['chroma']:4.1f}  亮部 p90 L* {st['p90']:4.1f}  像素 {st['n']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mine", nargs=2, metavar=("PHOTO", "BOX"), required=True)
    ap.add_argument("--ref", nargs=2, metavar=("REF", "BOX"), action="append", required=True)
    args = ap.parse_args()

    me = face_stats(args.mine[0], ps.parse_crop(args.mine[1]))
    refs = [face_stats(p, ps.parse_crop(b)) for p, b in args.ref]
    print(f"你的照片  {describe(me)}")
    for (p, _), st in zip(args.ref, refs):
        print(f"{os.path.basename(p)[:8]:8s}  {describe(st)}")

    ref = {k: sum(r[k] for r in refs) / len(refs) for k in ("L", "a", "b", "chroma", "lab_hue", "p90")}
    ref["hsv_hue"] = ps.circ_mean([r["hsv_hue"] for r in refs])
    dh = ps.circ_diff(ref["hsv_hue"], me["hsv_hue"])
    ratio = ref["chroma"] / me["chroma"] if me["chroma"] > 1 else 1.0
    dL = ref["L"] - me["L"]

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
