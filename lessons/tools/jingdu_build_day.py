#!/usr/bin/env python3
"""Assemble one day's set from the chosen audio candidates and their breakdowns.

The breakdown file is a JSON list of five objects, in page order. Each names
the candidate it explains ("cid") and carries the teaching fields (topic,
level, translation, gloss, chunks, structure, relations, context, small,
meanings, phrasing, stress, pron). Everything that must match the recording
exactly (text, word timings, source, link, the audio itself) is copied from the
candidate here, never retyped.

The five clips are joined into one audio file for the day (AAC in an .mp4
container: the page's file store takes .mp4 but not .mp3) (a short pause between
sentences); each sentence records where it sits in that file ("clip": [start,
end] in seconds) and its word timings relative to that start ("t").

Usage:
    1. python3 jingdu_build_day.py --cands cands.json --breakdown breakdown.json --date YYYY-MM-DD --out outdir
       -> outdir/day-YYYY-MM-DD.mp4 and outdir/day.json (no audio id yet)
    2. upload outdir/day-YYYY-MM-DD.mp4 to the page's asset store; note the asset id
    3. run the same command again with --audio-id <id> -> day.json now points at the audio
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys

TEACH = ["topic", "level", "translation", "gloss", "chunks", "structure", "relations", "context", "small",
         "meanings", "phrasing", "stress", "pron"]
FROM_CAND = ["text", "source", "outlet", "title", "url", "published", "at", "words", "t"]
GAP = 0.6  # seconds of silence between sentences in the day's file


def duration(path):
    # Count the decoded samples: the container's own duration estimate drifts by tens of milliseconds
    # per clip, which would add up across the day's file.
    pcm = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", "24000", "-"],
                         capture_output=True, check=True).stdout
    return len(pcm) / 2 / 24000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", required=True)
    ap.add_argument("--breakdown", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--audio-id", default="", help="asset id of the uploaded day audio file")
    args = ap.parse_args()

    cands = {c["cid"]: c for c in json.load(open(args.cands, encoding="utf-8"))}
    picks = json.load(open(args.breakdown, encoding="utf-8"))
    os.makedirs(args.out, exist_ok=True)
    errs, sentences, clips = [], [], []
    pos = 0.0
    for n, b in enumerate(picks, 1):
        c = cands.get(b.get("cid"))
        if not c:
            errs.append(f"sentence {n}: unknown cid {b.get('cid')!r}")
            continue
        d = duration(c["clip"])
        s = {"n": n, "cid": c["cid"]}
        s.update({k: c[k] for k in FROM_CAND})
        s.update({k: b.get(k) for k in TEACH})
        s["clip"] = [round(pos, 2), round(pos + d, 2)]
        sentences.append(s)
        clips.append(c["clip"])
        pos += d + GAP
    if errs:
        print("\n".join(errs))
        return 1

    mp4 = os.path.join(args.out, f"day-{args.date}.mp4")
    inputs, chain = [], []
    for i, path in enumerate(clips):
        inputs += ["-i", path]
        chain.append(f"[{i}:a]aresample=24000,aformat=channel_layouts=mono,apad=pad_dur={GAP}[a{i}]")
    chain.append("".join(f"[a{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=0:a=1[out]")
    if args.audio_id and os.path.exists(mp4):
        pass  # second run: the file was already uploaded; keep it exactly as it is
    else:
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(chain),
                        "-map", "[out]", "-ac", "1", "-ar", "24000", "-c:a", "aac", "-b:a", "48k", "-movflags", "+faststart", mp4],
                       check=True)

    day = {"date": args.date, "lang": "de", "level": "B2–C1", "audio": True, "audioId": args.audio_id,
           "createdAt": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "sentences": sentences}
    json.dump(day, open(os.path.join(args.out, "day.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"wrote {mp4} ({os.path.getsize(mp4) // 1024} KB, {pos:.1f}s) and {args.out}/day.json"
          + ("" if args.audio_id else " — upload the .mp4, then rerun with --audio-id"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
