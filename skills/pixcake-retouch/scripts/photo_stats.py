#!/usr/bin/env python3
"""Shared loading and measurement code for analyze_raw.py and compare_ref.py.

Not meant to be run directly. Needs numpy + Pillow; RAW files also need rawpy,
EXIF reading uses exifread when installed (pip install rawpy exifread).
"""

import logging
import math
import os

import numpy as np
from PIL import Image, ImageOps

RAW_EXTS = {
    ".3fr", ".arw", ".cr2", ".cr3", ".crw", ".dcr", ".dng", ".erf", ".iiq", ".k25",
    ".kdc", ".mef", ".mos", ".mrw", ".nef", ".nrw", ".orf", ".pef", ".raf", ".raw",
    ".rw2", ".rwl", ".sr2", ".srf", ".srw", ".x3f",
}

STATS_SIDE = 800  # measurements run on a downscaled copy; enough for tone/colour statistics

# HSL bands as PixCake / Lightroom name them, by HSV hue in degrees (red wraps around 0).
HSL_BANDS = [
    ("红", 345, 15), ("橙", 15, 45), ("黄", 45, 70), ("绿", 70, 165),
    ("青", 165, 200), ("蓝", 200, 255), ("紫", 255, 290), ("洋红", 290, 345),
]

ZONES = [("死黑", 0, 10), ("暗部", 10, 30), ("中间调", 30, 70), ("亮部", 70, 90), ("高光", 90, 101)]

TONE_ZONES = {"shadows": (5, 35), "midtones": (35, 70), "highlights": (70, 97)}


# ---------------------------------------------------------------- colour maths

def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


_M = np.array([[0.4124564, 0.3575761, 0.1804375],
               [0.2126729, 0.7151522, 0.0721750],
               [0.0193339, 0.1191920, 0.9503041]])
_WHITE = np.array([0.95047, 1.0, 1.08883])


def rgb8_to_lab(rgb):
    """uint8 sRGB (..., 3) -> L*, a*, b* arrays (D65)."""
    xyz = srgb_to_linear(rgb.astype(np.float64) / 255.0) @ _M.T / _WHITE
    d = 6 / 29
    f = np.where(xyz > d ** 3, np.cbrt(xyz), xyz / (3 * d * d) + 4 / 29)
    return 116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])


def lab_to_rgb8(L, a, b):
    fy = (np.asarray(L, dtype=np.float64) + 16) / 116
    f = np.stack([fy + np.asarray(a) / 500, fy, fy - np.asarray(b) / 200], axis=-1)
    d = 6 / 29
    xyz = np.where(f > d, f ** 3, 3 * d * d * (f - 4 / 29)) * _WHITE
    rgb = linear_to_srgb(xyz @ np.linalg.inv(_M).T)
    return np.round(rgb * 255).astype(np.uint8)


def lstar_to_level(L):
    """Neutral grey with lightness L* -> 0-255 level, i.e. what a curve point would read."""
    return int(lab_to_rgb8(L, 0, 0)[0])


def rgb_to_hsv(rgb):
    """uint8 sRGB -> hue degrees [0, 360), saturation 0-1, value 0-1."""
    x = rgb.astype(np.float64) / 255.0
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    mx, mn = x.max(axis=-1), x.min(axis=-1)
    d = mx - mn
    safe = np.where(d == 0, 1, d)
    h = np.select(
        [d == 0, mx == r, mx == g],
        [0.0, ((g - b) / safe) % 6, (b - r) / safe + 2],
        (r - g) / safe + 4,
    ) * 60.0
    s = np.where(mx == 0, 0, d / np.where(mx == 0, 1, mx))
    return h % 360, s, mx


def wheel_hue(a, b):
    """Direction of a Lab a*/b* offset -> hue on a 0-360 colour wheel (as in 颜色分级)."""
    ang = math.atan2(b, a)
    rgb = lab_to_rgb8(60, 30 * math.cos(ang), 30 * math.sin(ang))
    h, _, _ = rgb_to_hsv(rgb.reshape(1, 3))
    return float(h[0])


def hue_name(h):
    for name, lo, hi in HSL_BANDS:
        if (lo <= h < hi) if lo < hi else (h >= lo or h < hi):
            return name
    return "红"


def circ_mean(deg):
    r = np.radians(deg)
    return float(np.degrees(math.atan2(np.sin(r).mean(), np.cos(r).mean())) % 360)


def circ_diff(a, b):
    """Signed a - b on the hue circle, in (-180, 180]."""
    return (a - b + 180) % 360 - 180


# ---------------------------------------------------------------- loading

def _flip_thumb(img, flip, raw_w, raw_h):
    """Rotate an embedded preview to match LibRaw's flip code, unless it is already upright."""
    want_portrait = (raw_h > raw_w) != (flip in (5, 6))
    is_portrait = img.height > img.width
    if flip == 3:
        return img.rotate(180, expand=True)
    if flip in (5, 6) and want_portrait != is_portrait:
        return img.rotate(90 if flip == 5 else -90, expand=True)
    return img


def _read_exif(path):
    try:
        import exifread
    except ImportError:
        return {}
    logging.getLogger("exifread").setLevel(logging.ERROR)
    try:
        with open(path, "rb") as fh:
            tags = exifread.process_file(fh, details=False)
    except Exception:
        return {}
    want = {
        "相机": ("Image Make", "Image Model"),
        "镜头": ("EXIF LensModel",),
        "焦距": ("EXIF FocalLength",),
        "光圈": ("EXIF FNumber",),
        "快门": ("EXIF ExposureTime",),
        "ISO": ("EXIF ISOSpeedRatings", "EXIF PhotographicSensitivity"),
        "曝光补偿": ("EXIF ExposureBiasValue",),
        "测光": ("EXIF MeteringMode",),
        "闪光灯": ("EXIF Flash",),
        "拍摄时间": ("EXIF DateTimeOriginal",),
    }
    out = {}
    for key, names in want.items():
        vals = [str(tags[n]).strip() for n in names if n in tags]
        if not vals:
            continue
        if key == "相机":
            out[key] = " ".join(dict.fromkeys(vals))
        else:
            out[key] = vals[0]
    for key in ("光圈", "焦距"):
        if key in out and "/" in out[key]:
            num, den = out[key].split("/", 1)
            try:
                out[key] = f"{float(num) / float(den):.1f}"
            except ValueError:
                pass
    if "光圈" in out:
        out["光圈"] = "f/" + out["光圈"]
    if "焦距" in out:
        out["焦距"] += "mm"
    return out


def _raw_info(raw):
    vis = raw.raw_image_visible
    black = float(np.mean(raw.black_level_per_channel))
    white = float(raw.white_level)
    span = max(white - black, 1.0)
    step = max(1, int(math.sqrt(vis.size / 4e6)))  # sample about 4 MP
    v = vis[::step, ::step].astype(np.float64)
    rel = (v - black) / span
    info = {
        "raw_clipped_pct": float((v >= white - span * 0.02).mean() * 100),
        "raw_deep_shadow_pct": float((rel < 2 ** -9).mean() * 100),
    }
    shot = list(raw.camera_whitebalance)[:3]
    day = list(raw.daylight_whitebalance)[:3]
    if shot[0] > 0 and shot[2] > 0 and day[0] > 0 and day[2] > 0:
        # >1: the camera had to add red relative to daylight -> scene light was cooler than daylight
        info["wb_vs_daylight"] = float((shot[0] / shot[2]) / (day[0] / day[2]))
    return info


def load_image(path, source="auto", max_side=1600, crop=None):
    """Return (rgb uint8 array, meta dict).

    source: auto   RAW -> embedded camera preview when it is large enough, else neutral render
            render RAW -> neutral LibRaw render (camera WB, sRGB, no auto-brightening)
            embedded RAW -> embedded preview only
    crop: optional (left, top, right, bottom) as fractions 0-1, applied after orientation.
    """
    ext = os.path.splitext(path)[1].lower()
    meta = {"file": os.path.basename(path), "exif": _read_exif(path), "raw": None}

    if ext in RAW_EXTS:
        try:
            import rawpy
        except ImportError:
            raise SystemExit("读取 RAW 需要 rawpy：pip install rawpy exifread")
        with rawpy.imread(path) as raw:
            meta["raw"] = _raw_info(raw)
            img = None
            if source in ("auto", "embedded"):
                try:
                    thumb = raw.extract_thumb()
                    if thumb.format == rawpy.ThumbFormat.JPEG:
                        from io import BytesIO
                        t = Image.open(BytesIO(thumb.data))
                        t = ImageOps.exif_transpose(t).convert("RGB")
                    else:
                        t = Image.fromarray(thumb.data).convert("RGB")
                    s = raw.sizes
                    t = _flip_thumb(t, s.flip, s.width, s.height)
                    if source == "embedded" or max(t.size) >= 1000:
                        img, meta["rendered_from"] = t, "相机内嵌预览（含机内风格/照片风格）"
                except Exception:
                    if source == "embedded":
                        raise SystemExit("这个 RAW 没有可用的内嵌预览，改用 --source render")
            if img is None:
                arr = raw.postprocess(use_camera_wb=True, no_auto_bright=True, output_bps=8,
                                      gamma=(2.4, 12.92), half_size=True,
                                      output_color=rawpy.ColorSpace.sRGB)
                img = Image.fromarray(arr)
                meta["rendered_from"] = "中性 RAW 渲染（相机白平衡、无风格曲线，比软件默认显示偏平偏暗）"
    else:
        img = Image.open(path)
        icc = img.info.get("icc_profile")
        img = ImageOps.exif_transpose(img)
        if icc and img.mode == "RGB":
            # iPhone screenshots are Display P3; read as sRGB they would look duller than on screen
            try:
                from io import BytesIO
                from PIL import ImageCms
                src = ImageCms.ImageCmsProfile(BytesIO(icc))
                meta["icc"] = ImageCms.getProfileDescription(src).strip()
                img = ImageCms.profileToProfile(img, src, ImageCms.createProfile("sRGB"), outputMode="RGB")
            except Exception:
                pass
        img = img.convert("RGB")
        if not crop:  # an explicit crop is measured on the original frame, so skip trimming then
            img = autotrim(img)
        meta["rendered_from"] = "图片文件"

    if crop:
        l, t, r, b = crop
        w, h = img.size
        img = img.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    if max(img.size) > max_side:
        img.thumbnail((max_side, max_side), Image.LANCZOS)
    meta["size"] = img.size
    return np.asarray(img), meta


def autotrim(img, tol=6):
    """Strip flat borders (white/black frames, letterboxing) around a screenshot or export."""
    a = np.asarray(img.convert("L"), dtype=np.int16)
    h, w = a.shape
    if h < 50 or w < 50:
        return img

    def flat(line):
        return line.max() - line.min() <= tol

    top = 0
    while top < h // 3 and flat(a[top]):
        top += 1
    bottom = h
    while bottom > h * 2 // 3 and flat(a[bottom - 1]):
        bottom -= 1
    left = 0
    while left < w // 3 and flat(a[top:bottom, left]):
        left += 1
    right = w
    while right > w * 2 // 3 and flat(a[top:bottom, right - 1]):
        right -= 1
    if (top, bottom, left, right) == (0, h, 0, w):
        return img
    return img.crop((left, top, right, bottom))


def parse_crop(text):
    if not text:
        return None
    parts = [float(p) for p in text.split(",")]
    if len(parts) != 4 or not (0 <= parts[0] < parts[2] <= 1 and 0 <= parts[1] < parts[3] <= 1):
        raise SystemExit("--crop 格式：左,上,右,下（0–1 的比例），例如 0,0.12,1,0.8")
    return parts


# ---------------------------------------------------------------- measurement

def _palette(L, a, b, k=6, seed=7):
    pts = np.stack([L, a, b], axis=1)
    rng = np.random.default_rng(seed)
    if len(pts) > 20000:
        pts = pts[rng.choice(len(pts), 20000, replace=False)]
    order = np.argsort(pts[:, 0])
    centers = pts[order[np.linspace(0, len(pts) - 1, k).astype(int)]].copy()
    for _ in range(15):
        lab = np.argmin(((pts[:, None, :] - centers[None]) ** 2).sum(-1), axis=1)
        for i in range(k):
            sel = pts[lab == i]
            if len(sel):
                centers[i] = sel.mean(axis=0)
    share = np.bincount(lab, minlength=k) / len(pts)
    out = []
    for i in np.argsort(-share):
        if share[i] < 0.02:
            continue
        rgb = lab_to_rgb8(*centers[i])
        out.append({"hex": "#%02x%02x%02x" % tuple(int(x) for x in rgb), "share": float(share[i] * 100),
                    "L": float(centers[i][0])})
    return out


def _cast(a, b, mask_neutral, mask_zone, min_share=0.05):
    """Median a*/b* of the near-neutral pixels in a zone (falls back to the whole zone)."""
    zone = mask_zone.sum()
    if zone == 0:
        return None
    m = mask_zone & mask_neutral
    basis = "近中性像素"
    if m.sum() < max(50, zone * min_share):
        m, basis = mask_zone, "整个区域（中性像素太少，受画面内容影响大）"
    am, bm = float(np.median(a[m])), float(np.median(b[m]))
    return {"a": am, "b": bm, "chroma": math.hypot(am, bm), "wheel_hue": wheel_hue(am, bm),
            "basis": basis, "zone_pct": float(zone / mask_zone.size * 100)}


def measure(rgb):
    img = Image.fromarray(rgb)
    if max(img.size) > STATS_SIDE:
        img.thumbnail((STATS_SIDE, STATS_SIDE), Image.BOX)
    x = np.asarray(img)
    flat = x.reshape(-1, 3)
    L, a, b = rgb8_to_lab(flat)
    C = np.hypot(a, b)
    H, S, V = rgb_to_hsv(flat)

    st = {}
    pct = np.percentile(L, [1, 2, 5, 25, 50, 75, 95, 98, 99])
    st["L"] = dict(zip(["p1", "p2", "p5", "p25", "p50", "p75", "p95", "p98", "p99"], map(float, pct)))
    st["L"]["mean"], st["L"]["std"] = float(L.mean()), float(L.std())
    st["zones"] = {n: float(((L >= lo) & (L < hi)).mean() * 100) for n, lo, hi in ZONES}
    st["clip_high_pct"] = float((flat.max(axis=1) >= 254).mean() * 100)
    st["clip_low_pct"] = float((flat.max(axis=1) <= 3).mean() * 100)

    key = st["L"]["p50"]
    rng = st["L"]["p98"] - st["L"]["p2"]
    k = "低" if key < 38 else ("高" if key > 62 else "中")
    r = "长" if rng > 80 else ("短" if rng < 55 else "中")
    st["tone_type"] = f"{k}{r}调"
    st["tone_range"] = float(rng)

    neutral = C < 12
    mid = (L >= 25) & (L <= 85)
    st["wb"] = _cast(a, b, neutral, mid, min_share=0.02)
    tn = C < 25
    st["toning"] = {z: _cast(a, b, tn, (L >= lo) & (L < hi)) for z, (lo, hi) in TONE_ZONES.items()}

    rg = flat[:, 0].astype(float) - flat[:, 1]
    yb = 0.5 * (flat[:, 0].astype(float) + flat[:, 1]) - flat[:, 2]
    st["colorfulness"] = float(math.hypot(rg.std(), yb.std()) + 0.3 * math.hypot(rg.mean(), yb.mean()))
    st["chroma_mean"], st["chroma_p90"] = float(C.mean()), float(np.percentile(C, 90))

    colored = (S >= 0.12) & (V >= 0.08)
    bands = {}
    for name, lo, hi in HSL_BANDS:
        m = colored & (((H >= lo) & (H < hi)) if lo < hi else ((H >= lo) | (H < hi)))
        share = float(m.mean() * 100)
        if m.sum() >= 30:
            bands[name] = {"share": share, "hue": circ_mean(H[m]), "sat": float(S[m].mean() * 100),
                           "L": float(L[m].mean())}
        else:
            bands[name] = {"share": share}
    st["hsl"] = bands

    skin = (H >= 5) & (H <= 40) & (S >= 0.18) & (S <= 0.65) & (V >= 0.35) & (a > 5) & (b > 5)
    st["skin"] = {"share": float(skin.mean() * 100)}
    if skin.sum() >= 100:
        st["skin"].update(hue=circ_mean(H[skin]), sat=float(S[skin].mean() * 100), L=float(L[skin].mean()))

    h, w = x.shape[:2]
    Lmap = L.reshape(h, w)
    ch, cw = max(1, h // 8), max(1, w // 8)
    corners = np.concatenate([Lmap[:ch, :cw].ravel(), Lmap[:ch, -cw:].ravel(),
                              Lmap[-ch:, :cw].ravel(), Lmap[-ch:, -cw:].ravel()])
    center = Lmap[h * 3 // 10: h * 7 // 10, w * 3 // 10: w * 7 // 10]
    st["corner_minus_center"] = float(corners.mean() - center.mean())

    st["palette"] = _palette(L, a, b)
    st["_hist"] = {
        "L": np.histogram(L, bins=100, range=(0, 100))[0].tolist(),
        "rgb": [np.bincount(flat[:, i], minlength=256).tolist() for i in range(3)],
    }
    return st


# ---------------------------------------------------------------- wording helpers

def describe_cast(c, strong=6.0):
    """a*/b* offset -> Chinese description, e.g. '偏暖黄（b*+4.2）'."""
    if c is None:
        return "无法判断"
    parts = []
    if abs(c["b"]) >= 2:
        parts.append(("偏暖黄" if c["b"] > 0 else "偏冷蓝") + f"（b*{c['b']:+.1f}）")
    if abs(c["a"]) >= 2:
        parts.append(("偏洋红" if c["a"] > 0 else "偏绿") + f"（a*{c['a']:+.1f}）")
    if not parts:
        return "基本中性"
    if c["chroma"] >= strong:
        parts[0] = "明显" + parts[0]
    return "、".join(parts)


def colorfulness_word(m):
    for limit, word in [(15, "很灰、几乎无彩"), (33, "低饱和"), (45, "中等偏低"), (59, "中等"),
                        (82, "较鲜艳"), (109, "很鲜艳")]:
        if m < limit:
            return word
    return "极其鲜艳"
