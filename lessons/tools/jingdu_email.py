#!/usr/bin/env python3
"""Turn one day's intensive-reading set into an email, and optionally send it.

Usage:
    # just render (writes the HTML and plain-text bodies, prints the subject)
    python3 jingdu_email.py day.json --html mail.html --text mail.txt [--lean]

    # render and send through the Resend API, with the day's audio attached as MP3
    python3 jingdu_email.py day.json --send --to someone@example.com [--audio day-2026-11-10.mp4]

`--lean` writes plain HTML with almost no styling, short enough to paste into a
mail tool by hand. Without it the HTML carries inline styles for mail clients.

Sending needs no key in this file or in the environment: the request goes to
api.resend.com with a placeholder token, and the cloud environment's network
secret for that host replaces it. Outside such an environment set RESEND_API_KEY.
"""
import argparse
import base64
import html
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

PAGE = "https://claude.ai/artifact/82DXcbb5KBj2H2TCbtQ5Gt"
SENDER = "精读训练 <onboarding@resend.dev>"
ACCENT, MUTED, LINE, MARK = "#5b3fa6", "#5e5d70", "#e1dfea", "#fcebc0"
SANS = "-apple-system,'PingFang SC','Microsoft YaHei','Noto Sans SC',Arial,sans-serif"
SERIF = "Georgia,'Times New Roman',serif"

e = html.escape


def norm(w):
    return re.sub(r"[^\wÄÖÜäöüß]", "", str(w)).lower()


def day_label(date):
    import datetime as dt
    d = dt.date.fromisoformat(date)
    return f"{d.month}月{d.day}日 周{'一二三四五六日'[d.weekday()]}"


def subject(day):
    topics = "、".join(str(s.get("topic", "")) for s in day["sentences"][:2] if s.get("topic"))
    return f"精读训练 · {day_label(day['date'])} · 5 句德语原声" + (f"（{topics}…）" if topics else "")


def mmss(sec):
    sec = int(float(sec))
    return f"{sec // 60}:{sec % 60:02d}"


def stressed_sentence(s, lean):
    stress = {norm(x) for w in s.get("stress", []) for x in str(w).split()}
    out = []
    for tok in s["text"].split():
        m = re.match(r"^([^\wÄÖÜäöüß]*)(.*?)([^\wÄÖÜäöüß]*)$", tok)
        pre, core, post = m.groups() if m else ("", tok, "")
        out.append(e(pre) + (f"<u>{e(core)}</u>" if core and norm(core) in stress else e(core)) + e(post))
    return " ".join(out)


def small_flags(s):
    gloss = s.get("gloss", [])
    if any("s" in g for g in gloss):
        return [bool(g.get("s")) for g in gloss]
    small = {norm(x) for it in s.get("small", []) for x in str(it.get("word", "")).split()}
    return [norm(g.get("w", "")) in small for g in gloss]


def render_html(day, lean=False, attached=False):
    """lean: bare tags with one wrapper style. Otherwise inline styles that Gmail and Apple Mail keep.
    attached: the day's recording travels with the mail, so say where each sentence starts in it."""
    has_audio = bool(day.get("audio"))
    S = (lambda css: "") if lean else (lambda css: f' style="{css}"')
    h = []
    if lean:
        h.append(f'<div style="font-family:{SANS};font-size:15px;line-height:1.6;color:#1b1b26;max-width:680px;">')
    else:
        h.append(f'<div style="margin:0;padding:12px 8px;background:#f4f3f8;">'
                 f'<div style="max-width:660px;margin:0 auto;background:#ffffff;border-radius:12px;padding:22px 24px;'
                 f'font-family:{SANS};color:#1b1b26;font-size:15px;line-height:1.65;">')
    h.append(f'<h2{S("margin:0 0 4px;font-size:21px;")}>精读训练 · {e(day_label(day["date"]))}</h2>')
    listen = "打开页面听原声、点词跟读" if has_audio else "打开页面"
    h.append(f'<p{S(f"margin:0 0 6px;color:{MUTED};font-size:13.5px;")}>德语 · B2–C1 · 今天 5 句'
             + ("真人原声" if has_audio else "原句")
             + f' · <a href="{PAGE}"{S(f"color:{ACCENT};font-weight:600;")}>{listen} →</a></p>')
    if has_audio and attached:
        marks = " · ".join(f"第 {s['n']} 句 {mmss(s['clip'][0])}" for s in day["sentences"] if s.get("clip"))
        h.append(f'<p{S(f"margin:0 0 4px;color:{MUTED};font-size:12.5px;")}>附件里的录音是 5 句连播：{marks}</p>')

    for s in day["sentences"]:
        flags = small_flags(s)
        h.append(f'<hr{S(f"border:0;border-top:1px solid {LINE};margin:20px 0 14px;")}>')
        head = f"{s['n']} · {e(str(s.get('source', '')))} · {e(str(s.get('outlet', '')))}"
        if s.get("topic"):
            head += f" · {e(str(s['topic']))}"
        h.append(f'<h3{S(f"margin:0 0 2px;font-size:14px;color:{ACCENT};")}>{head}</h3>')
        meta = []
        if str(s.get("url", "")).startswith("https://"):
            where = f"（约 {mmss(s['at'])} 处）" if s.get("at") else ""
            meta.append(f'<a href="{e(s["url"])}"{S(f"color:{MUTED};")}>{e(str(s.get("title", "原文")))}</a>{where}')
        meta.append(f"{s.get('words', len(s['text'].split()))} 词")
        if s.get("level"):
            meta.append(e(str(s["level"])))
        h.append(f'<p{S(f"margin:0 0 10px;color:{MUTED};font-size:12.5px;")}>{" · ".join(meta)}</p>')

        sent = stressed_sentence(s, lean)
        if lean:
            h.append(f'<p><font face="Georgia" size="4">{sent}</font></p>')
        else:
            h.append(f'<p style="margin:0 0 8px;font-family:{SERIF};font-size:20px;line-height:1.6;">{sent}</p>')
        h.append(f'<p{S("margin:0 0 6px;")}><b>整句</b>　{e(str(s.get("translation", "")))}</p>')
        if s.get("phrasing"):
            sep = " | " if lean else f' <span style="color:{ACCENT};">|</span> '
            parts = [e(p.strip()) for p in str(s["phrasing"]).split("|") if p.strip()]
            fam = "" if lean else f"font-family:{SERIF};"
            h.append(f'<p{S(f"margin:0 0 6px;{fam}")}><b{S(f"font-family:{SANS};")}>意群</b>　{sep.join(parts)}</p>')

        def title(t):
            h.append(f'<p{S(f"margin:14px 0 4px;font-size:13px;font-weight:700;color:{ACCENT};")}><b>{t}</b></p>')

        title("每个词")
        rows = []
        for g, small in zip(s.get("gloss", []), flags):
            w = e(str(g.get("w", "")))
            w = f'<span style="background-color:{MARK};">{w}</span>' if small else w
            form = f' <small{S(f"color:{MUTED};")}>{e(str(g["f"]))}</small>' if g.get("f") else ""
            wcss = "" if lean else f' style="font-family:{SERIF};font-size:16px;"'
            rows.append(f'<b{wcss}>{w}</b>　{e(str(g.get("g", "")))}{form}')
        h.append(f'<p{S("margin:0;line-height:1.75;")}>' + "<br>\n".join(rows) + "</p>")

        def listing(name, items, fmt):
            items = [fmt(x) for x in items if x]
            if items:
                title(name)
                h.append(f'<ul{S("margin:0;padding-left:20px;")}>' + "".join(f'<li{S("margin:0 0 4px;")}>{x}</li>' for x in items) + "</ul>")

        de = (lambda t: f"<b>{e(str(t))}</b>") if lean else (lambda t: f'<b style="font-family:{SERIF};color:{ACCENT};">{e(str(t))}</b>')
        note = lambda t: f' <small{S(f"color:{MUTED};")}>{e(str(t))}</small>' if t else ""
        listing("每个词组", s.get("chunks", []), lambda x: f'{de(x.get("text", ""))}　{e(str(x.get("meaning", "")))}{note(x.get("note"))}')
        listing("不起眼的小介词、小词", s.get("small", []), lambda x: f'{de(x.get("word", ""))}　{e(str(x.get("role", "")))}')
        listing("词和词之间是什么关系", s.get("structure", []),
                lambda x: f'<i>{e(str(x.get("role", "")))}</i>　{de(x.get("text", ""))}{note(x.get("note"))}')
        if s.get("relations"):
            h.append(f'<p{S("margin:6px 0 0;")}>{e(str(s["relations"]))}</p>')
        listing("词组合后在这个语境里的意思", s.get("context", []),
                lambda x: f'{de(x.get("text", ""))}　这里：{e(str(x.get("here", "")))}；换个搭配：{e(str(x.get("elsewhere", "")))}')
        if s.get("meanings"):
            title("这句话的所有含义")
            h.append(f'<p{S("margin:0;")}>{e(str(s["meanings"]))}</p>')
        listing("发音难点", s.get("pron", []), lambda x: f'{de(x.get("word", ""))}　{e(str(x.get("tip", "")))}')

    h.append(f'<hr{S(f"border:0;border-top:1px solid {LINE};margin:20px 0 12px;")}>')
    h.append(f'<p{S(f"margin:0;color:{MUTED};font-size:12.5px;")}><b>精读五步</b>　1 读好 → 2 彻底弄懂（上面逐项列好）→ 3 说出来（约 2 天：发音、语调、语流）'
             f'→ 4 脱稿（没练好之前不要背）→ 5 找人说。黄底是讲到的小词，下划线是通常重读的词，以原声为准。'
             f'文字由语音识别转写，个别词可能有出入。</p>')
    h.append("</div>" if lean else "</div></div>")
    return "\n".join(h)


def render_text(day):
    t = [f"精读训练 · {day_label(day['date'])}", f"打开页面听原声：{PAGE}", ""]
    for s in day["sentences"]:
        t += [f"【{s['n']}】{s.get('source', '')} · {s.get('outlet', '')} · {s.get('topic', '')}", s["text"],
              "整句：" + str(s.get("translation", "")), ""]
        t += [f"  {g.get('w', '')}  {g.get('g', '')}  ({g.get('f', '')})" for g in s.get("gloss", [])]
        t += ["", "词组：" + "；".join(f"{c.get('text')} = {c.get('meaning')}" for c in s.get("chunks", [])),
              "小词：" + "；".join(f"{c.get('word')}：{c.get('role')}" for c in s.get("small", [])),
              "关系：" + str(s.get("relations", "")), "含义：" + str(s.get("meanings", "")), ""]
    return "\n".join(t)


def as_mp3(path, workdir):
    if path.lower().endswith(".mp3"):
        return path
    out = os.path.join(workdir, os.path.splitext(os.path.basename(path))[0] + ".mp3")
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", path, "-ac", "1", "-ar", "24000", "-b:a", "56k", out],
                   check=True)
    return out


def send_resend(day, to, audio=None, sender=SENDER):
    body = {"from": sender, "to": [to], "subject": subject(day), "html": render_html(day, attached=bool(audio)),
            "text": render_text(day)}
    if audio:
        mp3 = as_mp3(audio, os.path.dirname(os.path.abspath(audio)))
        body["attachments"] = [{"filename": f"精读-{day['date']}.mp3",
                                "content": base64.b64encode(open(mp3, "rb").read()).decode("ascii")}]
    req = urllib.request.Request(
        "https://api.resend.com/emails", data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Authorization": "Bearer " + os.environ.get("RESEND_API_KEY", "re_placeholder_filled_in_by_the_proxy"),
                 "Content-Type": "application/json", "User-Agent": "jingdu-daily/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("day")
    ap.add_argument("--html")
    ap.add_argument("--text")
    ap.add_argument("--lean", action="store_true")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--to")
    ap.add_argument("--audio")
    args = ap.parse_args()

    day = json.load(open(args.day, encoding="utf-8"))
    day = day.get("data", day)
    if args.html:
        open(args.html, "w", encoding="utf-8").write(render_html(day, lean=args.lean))
    if args.text:
        open(args.text, "w", encoding="utf-8").write(render_text(day))
    print("Subject:", subject(day))
    if args.send:
        if not args.to:
            print("--send needs --to")
            return 2
        status, reply = send_resend(day, args.to, args.audio)
        print("resend:", status, reply[:300])
        return 0 if 200 <= status < 300 else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
