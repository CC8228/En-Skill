#!/usr/bin/env python3
"""Turn a listening script or Listen-and-Repeat sentences into audio.

  tts.py [FILE] [-o OUT] [--backend auto|edge|gtts|say|espeak] [--slow] [--list]

Lines written as "Speaker: text" are treated as a dialogue and voiced with
alternating voices where the backend allows it (edge-tts, say, espeak; gTTS
alternates accents). Blank lines become short pauses when ffmpeg is available.

Backends are tried in order: edge-tts (pip install edge-tts, needs internet),
gTTS (pip install gTTS, needs internet), macOS `say`, espeak-ng/espeak.
The output extension follows the backend: .mp3 for edge/gTTS, .aiff for say,
.wav for espeak. The final path is printed on success.
"""

import argparse
import asyncio
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave

SPEAKER_RE = re.compile(r"^\s*([A-Z][\w .'-]{0,24}):\s*(.+)$")
VOICES = {
    "edge": ["en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural", "en-US-DavisNeural"],
    "gtts": ["com", "co.uk", "com.au", "ca"],
    "say": ["Samantha", "Alex", "Karen", "Daniel"],
    "espeak": ["en-us+f3", "en-us+m3", "en-gb+f2", "en-gb+m1"],
}
EXT = {"edge": ".mp3", "gtts": ".mp3", "say": ".aiff", "espeak": ".wav"}


def parse_segments(text):
    """Return [(speaker or None, text)], with None text meaning a pause."""
    segments = []
    for line in text.splitlines():
        if not line.strip():
            if segments and segments[-1][1] is not None:
                segments.append((None, None))
            continue
        m = SPEAKER_RE.match(line)
        if m:
            segments.append((m.group(1).strip(), m.group(2).strip()))
        else:
            segments.append((None, line.strip()))
    while segments and segments[-1][1] is None:
        segments.pop()
    return segments


def voice_for(backend, speaker, speakers):
    if speaker is None:
        return VOICES[backend][0]
    if speaker not in speakers:
        speakers.append(speaker)
    return VOICES[backend][speakers.index(speaker) % len(VOICES[backend])]


def synth_edge(text, voice, path, slow):
    import edge_tts

    rate = "-20%" if slow else "+0%"
    asyncio.run(edge_tts.Communicate(text, voice, rate=rate).save(path))


def synth_gtts(text, voice, path, slow):
    from gtts import gTTS

    gTTS(text, lang="en", tld=voice, slow=slow).save(path)


def synth_say(text, voice, path, slow):
    cmd = ["say", "-v", voice, "-o", path]
    if slow:
        cmd += ["-r", "140"]
    subprocess.run(cmd + [text], check=True)


def synth_espeak(text, voice, path, slow):
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    subprocess.run([exe, "-v", voice, "-s", "130" if slow else "160", "-w", path, text], check=True)


SYNTH = {"edge": synth_edge, "gtts": synth_gtts, "say": synth_say, "espeak": synth_espeak}


def available(backend):
    if backend == "edge":
        try:
            import edge_tts  # noqa: F401
            return True
        except ImportError:
            return False
    if backend == "gtts":
        try:
            import gtts  # noqa: F401
            return True
        except ImportError:
            return False
    if backend == "say":
        return shutil.which("say") is not None
    if backend == "espeak":
        return bool(shutil.which("espeak-ng") or shutil.which("espeak"))
    return False


def join(parts, ext, out):
    """Concatenate audio files; parts are paths or None for a pause."""
    files = [p for p in parts if p]
    if len(files) == 1:
        shutil.move(files[0], out)
        return
    if shutil.which("ffmpeg"):
        # Resample every input to one format so parts from any backend can be joined,
        # and add a short pause between consecutive lines (longer for blank lines).
        cmd, labels, n = ["ffmpeg", "-loglevel", "error", "-y"], [], 0
        for i, p in enumerate(parts):
            if p is None:
                cmd += ["-f", "lavfi", "-t", "0.8", "-i", "anullsrc=r=24000:cl=mono"]
            else:
                if i and parts[i - 1] is not None:
                    cmd += ["-f", "lavfi", "-t", "0.3", "-i", "anullsrc=r=24000:cl=mono"]
                    labels.append(n)
                    n += 1
                cmd += ["-i", p]
            labels.append(n)
            n += 1
        graph = "".join(f"[{k}:a]aresample=24000,aformat=channel_layouts=mono[a{k}];" for k in labels)
        graph += "".join(f"[a{k}]" for k in labels) + f"concat=n={len(labels)}:v=0:a=1[out]"
        subprocess.run(cmd + ["-filter_complex", graph, "-map", "[out]", out], check=True)
        return
    if ext == ".mp3":  # MP3 frames can be appended directly
        with open(out, "wb") as dst:
            for p in files:
                with open(p, "rb") as src:
                    dst.write(src.read())
        return
    if ext == ".wav":
        with wave.open(out, "wb") as dst:
            for i, p in enumerate(files):
                with wave.open(p, "rb") as src:
                    if i == 0:
                        dst.setparams(src.getparams())
                    dst.writeframes(src.readframes(src.getnframes()))
        return
    raise RuntimeError("拼接多段 .aiff 需要 ffmpeg；可安装 ffmpeg，或去掉说话人标签用单一声音朗读。")


def render(backend, segments, out, slow):
    if EXT[backend] == ".aiff" and not shutil.which("ffmpeg"):
        # Without ffmpeg, .aiff parts can't be joined: read everything in one voice instead.
        segments = [(None, " ".join(t for _, t in segments if t))]
    speakers, parts = [], []
    tmp = tempfile.mkdtemp()
    try:
        for i, (speaker, text) in enumerate(segments):
            if text is None:
                parts.append(None)
                continue
            path = os.path.join(tmp, f"{i:03d}{EXT[backend]}")
            SYNTH[backend](text, voice_for(backend, speaker, speakers), path, slow)
            parts.append(path)
        join(parts, EXT[backend], out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", nargs="?", default="-")
    parser.add_argument("-o", "--out", default="toefl_audio")
    parser.add_argument("--backend", default="auto", choices=["auto", *SYNTH])
    parser.add_argument("--slow", action="store_true", help="slower speech for dictation practice")
    parser.add_argument("--list", action="store_true", help="show which backends are installed")
    args = parser.parse_args()

    if args.list:
        for b in SYNTH:
            print(f"{b:<7} {'可用' if available(b) else '未安装'}")
        return

    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    segments = parse_segments(text)
    if not segments:
        sys.exit("没有读到要朗读的文本。")

    order = list(SYNTH) if args.backend == "auto" else [args.backend]
    errors = []
    for backend in order:
        if not available(backend):
            errors.append(f"{backend}: 未安装")
            continue
        out = os.path.splitext(args.out)[0] + EXT[backend]
        try:
            render(backend, segments, out, args.slow)
        except Exception as exc:  # network failures, missing voices, etc.
            errors.append(f"{backend}: {type(exc).__name__}: {exc}"[:200])
            continue
        print(out)
        return

    print("没有可用的语音合成后端（未安装或无法联网）：", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    print("安装任一即可：pip install edge-tts（推荐，需联网）/ pip install gTTS（需联网）/ "
          "Linux: apt install espeak-ng / macOS 自带 say。", file=sys.stderr)
    print("无法安装时，改用 references/listening.md 中的文字替代练习法。", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
