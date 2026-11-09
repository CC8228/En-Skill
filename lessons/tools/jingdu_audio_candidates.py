#!/usr/bin/env python3
"""Collect spoken German sentences, with their real audio, for the daily reading set.

For each podcast below the script takes the newest episode from its public RSS
feed, downloads only the part it needs, transcribes a window of a few minutes
with Whisper (word timestamps), rebuilds whole sentences and keeps those of
about 30 words. Each kept sentence gets a short MP3 clip of the real audio and
the start/end time of every word inside that clip, so the page can play the
whole sentence, one sense group or one word in the speaker's own voice.

Usage:
    python3 jingdu_audio_candidates.py --out cands.json --clips clips/ [--feeds news,pro,fun]
                                       [--window 300] [--exclude used.json] [--date YYYY-MM-DD]

Needs: ffmpeg, `pip install faster-whisper`, and the environment variable
HF_HUB_DISABLE_XET=1 where the Xet download host is not reachable. The model
(large-v3-turbo, int8 on CPU) transcribes about 4x faster than real time on 4 cores.
"""
import argparse
import datetime as dt
import email.utils
import json
import os
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET

# (category shown on the page, podcast name, feed URL). All are hosted on Podigee.
FEEDS = {
    "news": [
        ("新闻", "Handelsblatt Today", "https://handelsblatt-today.podigee.io/feed/mp3"),
        ("新闻", "Bundestalk (taz)", "https://taz-bundestalk.podigee.io/feed/mp3"),
    ],
    "pro": [
        ("专业", "OMR Podcast", "https://omr.podigee.io/feed/mp3"),
        ("专业", "Methodisch inkorrekt", "https://minkorrekt.podigee.io/feed/mp3"),
        ("专业", "Geschichten aus der Geschichte", "https://geschichten-aus-der-geschichte.podigee.io/feed/mp3"),
    ],
    "fun": [
        ("娱乐", "Hotel Matze", "https://hotelmatze.podigee.io/feed/mp3"),
    ],
}
UA = "Mozilla/5.0 (personal language-learning podcast reader)"
MIN_WORDS, MAX_WORDS = 25, 35
AD_WORDS = re.compile(r"(Werbung|Anzeige|Sponsor|gesponsert|Rabatt|Gutschein|Code\b|präsentiert von|unterstützt von|"
                      r"Partner dieser Folge|Link in den Shownotes|Shownotes|abonnier|Abo\b|Steady|Patreon)", re.I)


def fetch(url, timeout=30, rng=None):
    headers = {"User-Agent": UA}
    if rng:
        headers["Range"] = rng
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
        return r.read()


def seconds(text):
    text = (text or "").strip()
    if not text:
        return 0
    if text.isdigit():
        return int(text)
    parts = [int(p) for p in text.split(":") if p.isdigit()]
    total = 0
    for p in parts:
        total = total * 60 + p
    return total


def newest_episode(feed_url):
    root = ET.fromstring(fetch(feed_url))
    best = None
    for item in root.iter("item"):
        enc = item.find("enclosure")
        if enc is None or not enc.get("url"):
            continue
        get = lambda tag: (item.findtext(tag) or "").strip()
        date = email.utils.parsedate_to_datetime(get("pubDate")) if get("pubDate") else None
        dur = 0
        for child in item:
            if child.tag.endswith("}duration"):
                dur = seconds(child.text)
        ep = {"title": get("title"), "link": get("link") or enc.get("url"), "audio": enc.get("url"),
              "date": date, "duration": dur, "guid": get("guid") or enc.get("url")}
        if date and (best is None or date > best["date"]):
            best = ep
    return best


def run(cmd):
    return subprocess.run(cmd, capture_output=True, check=True)


def load_model():
    from faster_whisper import WhisperModel
    return WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)


def transcribe(model, wav_path):
    import numpy as np
    pcm = run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", wav_path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"]).stdout
    audio = np.frombuffer(pcm, dtype=np.float32)
    segs, _ = model.transcribe(audio, language="de", word_timestamps=True, vad_filter=True, beam_size=5)
    words = []
    for s in segs:
        for w in s.words:
            tok = w.word.strip()
            if not tok:
                continue
            # Whisper marks a new word with a leading space; a piece without one (e.g. "-Präsidentschaft")
            # belongs to the word before it.
            if words and not w.word.startswith(" ") and (tok[0] in "-–'’" or tok[0].islower()):
                prev = words[-1]
                words[-1] = [prev[0] + tok, prev[1], float(w.end), min(prev[3], float(w.probability))]
                continue
            words.append([tok, float(w.start), float(w.end), float(w.probability)])
    return words


def sentences(words):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1][0] if i + 1 < len(words) else ""
        if re.search(r"[.!?][\"“”»«’)]*$", w[0]) and (not nxt or re.match(r"[\"„»(]?[A-ZÄÖÜ0-9]", nxt)):
            out.append(cur)
            cur = []
    return out


def good(sent):
    toks = [w[0] for w in sent]
    text = " ".join(toks)
    real = [t for t in toks if re.search(r"[\wÄÖÜäöüß]", t)]
    if not (MIN_WORDS <= len(real) <= MAX_WORDS):
        return False
    if not re.match(r"[\"„»(]?[A-ZÄÖÜ]", text) or text.endswith("?"):
        return False
    if AD_WORDS.search(text):
        return False
    probs = [w[3] for w in sent]
    if sum(probs) / len(probs) < 0.8 or min(probs) < 0.3:
        return False
    if sum(1 for t in real if re.search(r"\d", t)) > 2:
        return False
    if sent[-1][2] - sent[0][1] > 25:  # long pauses inside: probably not one fluent sentence
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--clips", required=True)
    ap.add_argument("--feeds", default="news,pro,fun")
    ap.add_argument("--window", type=int, default=300, help="seconds of audio to transcribe per podcast")
    ap.add_argument("--exclude")
    ap.add_argument("--date", default=dt.date.today().isoformat(), help="varies the window position from day to day")
    args = ap.parse_args()

    os.makedirs(args.clips, exist_ok=True)
    work = os.path.join(args.clips, "_work")
    os.makedirs(work, exist_ok=True)
    used = set()
    if args.exclude:
        try:
            used = set(json.load(open(args.exclude, encoding="utf-8")))
        except (OSError, ValueError):
            pass
    day_no = dt.date.fromisoformat(args.date).toordinal()

    model = load_model()
    cands, report = [], []
    feeds = [f for key in args.feeds.split(",") for f in FEEDS.get(key.strip(), [])]
    for fi, (source, show, feed) in enumerate(feeds):
        try:
            ep = newest_episode(feed)
        except Exception as e:
            report.append(f"{show}: feed failed ({e})")
            continue
        if not ep:
            report.append(f"{show}: no episode")
            continue
        dur = ep["duration"] or 1800
        span = max(1, dur - args.window - 240)
        offset = 120 + (day_no * 337 + fi * 911) % span  # skip the intro; move through the episode day by day
        mp3 = os.path.join(work, f"ep{fi}.mp3")
        try:
            # 24 kB/s covers bitrates up to 192 kbit/s; only the bytes up to the window are fetched.
            data = fetch(ep["audio"], timeout=180, rng=f"bytes=0-{int((offset + args.window + 30) * 24000)}")
        except Exception as e:
            report.append(f"{show}: audio failed ({e})")
            continue
        open(mp3, "wb").write(data)
        wav = os.path.join(work, f"win{fi}.wav")
        run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", str(offset), "-t", str(args.window),
             "-i", mp3, "-ac", "1", "-ar", "16000", wav])
        words = transcribe(model, wav)
        n = 0
        for sent in sentences(words):
            text = " ".join(w[0] for w in sent)
            if text in used or not good(sent):
                continue
            t0 = max(0.0, sent[0][1] - 0.25)
            t1 = sent[-1][2] + 0.35
            cid = f"{fi}-{int((offset + t0) * 10)}"
            clip = os.path.join(args.clips, cid + ".mp3")
            run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", f"{offset + t0:.2f}", "-t", f"{t1 - t0:.2f}",
                 "-i", mp3, "-ac", "1", "-ar", "24000", "-b:a", "48k", clip])
            cands.append({
                "cid": cid, "source": source, "outlet": show, "title": ep["title"], "url": ep["link"],
                "published": ep["date"].astimezone(dt.timezone.utc).strftime("%Y-%m-%d") if ep["date"] else "",
                "at": round(offset + t0),  # position in the downloaded episode, in seconds (ads may shift it)
                "text": text,
                "words": len([w for w in sent if re.search(r"[\wÄÖÜäöüß]", w[0])]),
                "t": [[round(w[1] - t0, 2), round(w[2] - t0, 2)] for w in sent],
                "minProb": round(min(w[3] for w in sent), 2),
                "clip": clip,
            })
            n += 1
        report.append(f"{show}: \"{ep['title'][:60]}\" from {offset // 60}:{offset % 60:02d}, {len(words)} words, {n} candidates")
        for f in (mp3, wav):
            os.remove(f)

    json.dump(cands, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(report))
    print(f"total {len(cands)} candidates -> {args.out}")
    return 0 if cands else 1


if __name__ == "__main__":
    sys.exit(main())
