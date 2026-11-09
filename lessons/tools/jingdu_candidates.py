#!/usr/bin/env python3
"""Collect candidate sentences for the daily German intensive-reading set.

Reads the RSS/Atom feeds of a few German outlets whose robots.txt does not
turn away Claude, downloads recent articles, pulls the body paragraphs and
keeps complete sentences of roughly 30 words. The output is a JSON list of
verbatim sentences with their source, so the person picking the day's five
sentences never has to retype or paraphrase anything.

Usage:
    python3 jingdu_candidates.py --out cands.json [--days 3] [--per-feed 12]
                                 [--exclude used.json]

`--exclude` takes a JSON list of URLs or sentence texts already used.
Only the Python 3 standard library is needed.
"""
import argparse
import email.utils
import html
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

# (category shown on the page, outlet name, feed URL). Golem.de was tried and dropped:
# without a cookie consent its article pages carry no body text.
FEEDS = [
    ("新闻", "ZDFheute", "https://www.zdfheute.de/rss/zdf/nachrichten"),
    ("新闻", "taz", "https://taz.de/!p4608;rss/"),
    ("专业", "ingenieur.de", "https://www.ingenieur.de/feed/"),
    ("娱乐", "FILMSTARTS", "https://www.filmstarts.de/rss/nachrichten.xml"),
]
UA = "Mozilla/5.0 (personal language-learning reader; one request per article)"
MIN_WORDS, MAX_WORDS = 25, 35

# Abbreviations after which a full stop does not end a sentence.
ABBR = {
    "z", "b", "d", "h", "u", "a", "bzw", "ca", "dr", "prof", "nr", "st", "str", "vgl", "ggf", "inkl",
    "evtl", "usw", "etc", "mio", "mrd", "jh", "jhd", "bspw", "sog", "geb", "max", "min", "abs", "art",
    "tel", "hrsg", "co", "mr", "mrs", "vs", "rd", "ff", "s", "v", "chr", "okt", "nov", "dez", "jan",
    "feb", "aug", "sept", "sep", "kap", "bd", "gmbh", "ag", "e", "v", "o", "i", "a", "us",
}
SKIP = re.compile(
    r"(Foto:|Bild:|Quelle:|Lesen Sie|Newsletter|Anzeige|Cookie|Abonn|Datenschutz|"
    r"Alle Rechte|Mehr zum Thema|Mehr dazu|Hier klicken|Video:|Audio:|Podcast|Live-Ticker|"
    r"Inhaltsverzeichnis|personenbezogene|Drittanbieter|Tracking|Zustimmung|https?://|www\.|@|\|)", re.I)
MONTHS = {"Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
          "November", "Dezember", "Jahrhundert", "Jahrhunderts"}
MID_OK = {"z", "B", "u", "a", "Dr", "Prof", "St", "Nr", "Mr", "Mrs", "bzw", "ca", "vgl", "sog", "inkl", "d", "h"}


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "de-DE,de;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        charset = r.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def parse_date(text):
    if not text:
        return None
    text = text.strip()
    try:
        d = email.utils.parsedate_to_datetime(text)
    except (TypeError, ValueError):
        d = None
    if d is None:
        try:
            d = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def feed_items(xml_text):
    root = ET.fromstring(xml_text.encode("utf-8"))
    items = []
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        title = link = date = None
        for child in node:
            ct = child.tag.split("}")[-1]
            if ct == "title":
                title = (child.text or "").strip()
            elif ct == "link":
                href = child.get("href")
                if href and child.get("rel", "alternate") == "alternate":
                    link = href.strip()
                elif child.text and child.text.strip():
                    link = child.text.strip()
            elif ct in ("pubDate", "published", "updated", "date") and not date:
                date = parse_date(child.text)
        if link:
            items.append({"title": html.unescape(title or ""), "url": link, "date": date})
    return items


class Paragraphs(HTMLParser):
    """Collects the text of <p> elements, skipping navigation and asides."""

    SKIP_TAGS = {"nav", "footer", "aside", "figure", "figcaption", "script", "style", "noscript", "form", "button"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth_skip = 0
        self.in_p = 0
        self.buf = []
        self.out = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self.depth_skip += 1
        elif tag == "p" and not self.depth_skip:
            self.in_p += 1
            if self.in_p == 1:
                self.buf = []
        elif tag == "br" and self.in_p:
            self.buf.append(" ")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self.depth_skip:
            self.depth_skip -= 1
        elif tag == "p" and self.in_p:
            self.in_p -= 1
            if not self.in_p:
                text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
                if text:
                    self.out.append(text)

    def handle_data(self, data):
        if self.in_p and not self.depth_skip:
            self.buf.append(data)


def words(sentence):
    return [w for w in sentence.split() if re.search(r"[\wÄÖÜäöüß]", w)]


def split_sentences(par):
    out, start = [], 0
    for m in re.finditer(r"[.!?…][\"'“”„»«’)]*\s+(?=[\"'„»«(]?[A-ZÄÖÜ0-9])", par):
        end = m.end()
        before = par[start:m.start() + 1]
        last = re.findall(r"([\wÄÖÜäöüß]+)\.$", before)
        if last and (last[0].lower() in ABBR or last[0].isdigit() or len(last[0]) == 1):
            continue
        out.append(par[start:end].strip())
        start = end
    tail = par[start:].strip()
    if tail:
        out.append(tail)
    return out


def good(sentence):
    w = words(sentence)
    if not (MIN_WORDS <= len(w) <= MAX_WORDS):
        return False
    if not re.search(r"[.!?][\"'“”„»«’)]*$", sentence):
        return False
    if not re.match(r"[\"'„»«(]?[A-ZÄÖÜ]", sentence):
        return False
    if SKIP.search(sentence):
        return False
    if sum(1 for x in w if re.search(r"\d", x)) > 3:
        return False
    if sentence.count("„") + sentence.count("\"") + sentence.count("“") > 4:
        return False
    if re.search(r"\?\s+\S", sentence.rstrip("\"'“”„»«’) ")[:-1]):
        return False  # a question mark mid-text: usually a run of headings
    for m in re.finditer(r"([\wÄÖÜäöüß°]+)\.\s+([A-ZÄÖÜ][\wäöüß]*)", sentence):
        prev, nxt = m.group(1), m.group(2)
        if prev.isdigit() and nxt in MONTHS:
            continue
        if prev in MID_OK:
            continue
        return False  # two sentences glued together at an abbreviation or number
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--per-feed", type=int, default=12)
    ap.add_argument("--exclude")
    args = ap.parse_args()

    used = set()
    if args.exclude:
        try:
            used = set(json.load(open(args.exclude, encoding="utf-8")))
        except (OSError, ValueError):
            pass

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    cands, report = [], []
    for source, outlet, feed in FEEDS:
        try:
            items = feed_items(fetch(feed))
        except Exception as e:  # keep going when one outlet is down
            report.append(f"{outlet}: feed failed ({e})")
            continue
        items = [i for i in items if i["url"] not in used and (i["date"] is None or i["date"] >= cutoff)]
        n_found = 0
        for it in items[: args.per_feed]:
            try:
                page = fetch(it["url"])
            except Exception as e:
                report.append(f"{outlet}: article failed {it['url']} ({e})")
                continue
            p = Paragraphs()
            try:
                p.feed(page)
            except Exception:
                continue
            seen = set()
            for par in p.out:
                if len(words(par)) < 12:
                    continue
                for s in split_sentences(par):
                    if s in seen or s in used or not good(s):
                        continue
                    seen.add(s)
                    cands.append({
                        "source": source, "outlet": outlet, "title": it["title"], "url": it["url"],
                        "published": it["date"].astimezone(timezone.utc).strftime("%Y-%m-%d") if it["date"] else "",
                        "text": s, "words": len(words(s)),
                    })
                    n_found += 1
            time.sleep(0.5)
        report.append(f"{outlet}: {len(items[: args.per_feed])} articles, {n_found} candidate sentences")

    json.dump(cands, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(report))
    print(f"total {len(cands)} candidates -> {args.out}")
    return 0 if cands else 1


if __name__ == "__main__":
    sys.exit(main())
