"""Build a printable self-test paper (questions + separate answer key) from a lesson page's DATA."""
import html, json, random, re, sys

lang, src, out = sys.argv[1], sys.argv[2], sys.argv[3]   # lang: en | de
s = open(src).read()
i = s.index('const DATA = ') + len('const DATA = ')
j = s.index(';\n', i)
D = json.loads(s[i:j].replace('<\\/', '</'))
R = random.Random(20261102)
E = html.escape
L = {"en": "英语", "de": "德语"}[lang]
X = {"en": "英", "de": "德"}[lang]


def plain(m): return m.replace('[[', '').replace(']]', '')
def bold(m): return ''.join(('<b>' + E(p[2:-2]) + '</b>') if p.startswith('[[') else E(p) for p in re.split(r'(\[\[.+?\]\])', m))


# ---------- unify the two data shapes ----------
phr = []   # (group, target, zh, [(sentence, zh, tag)])
for g in D['phrases']:
    for it in g['items']:
        if lang == 'en':
            phr.append((g['name'], it[0], it[1], [(e[0], e[1], e[2]) for e in it[2]]))
        else:
            phr.append((g['name'], it[0], it[1], [(e[0], e[1], e[2]) for e in it[4]]))
ind = []   # (group, term, zh, plural or None)
for g in D['industry']:
    for it in g['items']:
        if lang == 'en': ind.append((g['name'], it[0], it[1], None))
        else: ind.append((g['name'], it[0], it[2], it[1]))
story = next(st for st in D['stories'] if st['title'] == '现场与故障')
sents = [(z, e) for z, e in D['sentences']] if lang == 'en' else [(x[0], x[1]) for x in D['sentences']]

# ---------- sampling: spread across groups ----------
def spread(items, n, key=lambda x: x[0]):
    groups = {}
    for it in items: groups.setdefault(key(it), []).append(it)
    for v in groups.values(): R.shuffle(v)
    picked, names = [], list(groups)
    while len(picked) < n:
        for g in names:
            if groups[g] and len(picked) < n: picked.append(groups[g].pop())
    return picked

sec3 = spread(phr, 5)                       # whole-sentence writing, both registers
rest = [p for p in phr if p not in sec3]
sec1 = spread(rest, 20)                     # phrase recall
sec2 = spread(ind, 14)                      # industry terms
sec4 = story['sentences'][:6]               # passage, sentence by sentence
sec5 = R.sample(sents, 4)                   # Chinese -> target language
for lst in (sec1, sec2): lst.sort(key=lambda x: [p[0] for p in (phr if lst is sec1 else ind)].index(x[0]))

# ---------- question paper ----------
def lines(n): return '<div class="wl"></div>' * n
q = []
q.append(f'''<header class="top"><div><h1>职场{L} · 第 1 课 · 自测卷 A</h1>
<p>项目协调与现场售后　建议用时 50 分钟　不看资料，做完再翻答案页</p></div>
<div class="boxes"><span>日期 ________</span><span>用时 ______ 分钟</span><span class="score">得分 ______ / 100</span></div></header>''')

q.append(f'<h2><span>一、看中文写出{L}词组</span><small>20 题 × 1 分</small></h2><div class="grid2">')
for k, (g, t, zh, _) in enumerate(sec1, 1):
    q.append(f'<div class="qi"><div class="p"><i>{k}</i>{E(zh)}</div>{lines(1)}</div>')
q.append('</div>')

if lang == 'en':
    q.append('<h2><span>二、看中文写出行业词汇</span><small>14 题 × 1 分</small></h2><div class="grid2">')
    for k, (g, t, zh, _) in enumerate(sec2, 1):
        q.append(f'<div class="qi"><div class="p"><i>{k}</i>{E(zh)}<em>（{E(g)}）</em></div>{lines(1)}</div>')
    q.append('</div>')
else:
    q.append('<h2><span>二、看中文写出行业名词</span><small>14 题 × 1 分 · 带冠词，写出复数（没有复数的写“—”）</small></h2><div class="grid2">')
    for k, (g, t, zh, pl) in enumerate(sec2, 1):
        q.append(f'<div class="qi"><div class="p"><i>{k}</i>{E(zh)}<em>（{E(g)}）</em></div><div class="pair"><span>单数</span><div class="wl"></div><span>复数</span><div class="wl"></div></div></div>')
    q.append('</div>')

q.append(f'<h2 class="brk"><span>三、例句默写：看中文写出整句{L}</span><small>10 句 × 3 分 · 词组用对 2 分，整句通顺 1 分</small></h2>')
for k, (g, t, zh, exs) in enumerate(sec3, 1):
    q.append(f'<div class="blk"><div class="bh"><i>{k}</i>要用的词组：<b>{E(zh)}</b></div>')
    for m, z, tag in exs:
        q.append(f'<div class="si"><div class="p"><span class="tag {"w" if tag == "书面" else "s"}">{tag}</span>{E(z)}</div>{lines(2)}</div>')
    q.append('</div>')

q.append(f'<h2><span>四、情景短文：逐句写出{L}</span><small>6 句 × 4 分 · 词组用对 2 分，整句正确 2 分</small></h2>')
q.append(f'<p class="scene">场景：{E(story["scene"])}。写完后连起来大声读一遍，就是一段完整的故障处理经历。</p>')
for k, (m, z) in enumerate(sec4, 1):
    q.append(f'<div class="si"><div class="p"><i>{k}</i>{E(z)}</div>{lines(2)}</div>')

q.append(f'<h2><span>五、中译{X}</span><small>4 句 × 3 分 · 意思对、关键词组用对即可，不必和参考答案一字不差</small></h2>')
for k, (z, e) in enumerate(sec5, 1):
    q.append(f'<div class="si"><div class="p"><i>{k}</i>{E(z)}</div>{lines(2)}</div>')
q.append('<div class="tally">一 ____ /20　　二 ____ /14　　三 ____ /30　　四 ____ /24　　五 ____ /12　　总分 ____ /100</div>')

# ---------- answer key ----------
a = ['<section class="key">']
a.append(f'<header class="top"><div><h1>答案页 · 职场{L}第 1 课自测卷 A</h1><p>先做完试卷再看。错题写进错题本，或者在网页练习里标成“不会”。</p></div></header>')
a.append('<div class="rules"><b>评分：</b>一、二题拼写全对才给分（大小写不扣分）' + ('，德语名词冠词或复数错一处得 0.5 分' if lang == 'de' else '') +
         '；三、五题每句 3 分：加粗的词组用对得 2 分，整句意思和语法基本正确再得 1 分；四题每句 4 分：词组 2 分，整句 2 分。说法和参考答案不同但同样地道也算对。</div>')
a.append('<div class="cols">')
a.append('<h3>一、词组</h3><ol class="sm">' + ''.join(f'<li>{E(t)}</li>' for g, t, zh, _ in sec1) + '</ol>')
if lang == 'en':
    a.append('<h3>二、行业词汇</h3><ol class="sm">' + ''.join(f'<li>{E(t)}</li>' for g, t, zh, _ in sec2) + '</ol>')
else:
    a.append('<h3>二、行业名词</h3><ol class="sm">' + ''.join(f'<li>{E(t)}{" · " + E(pl) if pl else " · —"}</li>' for g, t, zh, pl in sec2) + '</ol>')
a.append('<h3>三、例句</h3><ol class="sm">')
for g, t, zh, exs in sec3:
    a.append(f'<li><b>{E(t)}</b>' + ''.join(f'<div class="ar"><span class="tag {"w" if tag == "书面" else "s"}">{tag}</span>{bold(m)}</div>' for m, z, tag in exs) + '</li>')
a.append('</ol><h3>四、情景短文</h3><ol class="sm">' + ''.join(f'<li>{bold(m)}</li>' for m, z in sec4) + '</ol>')
a.append('<h3>五、中译' + X + '</h3><ol class="sm">' + ''.join(f'<li>{E(e)}</li>' for z, e in sec5) + '</ol>')
a.append('</div></section>')

css = '''
@page { size: A4; margin: 12mm 13mm 11mm; }
* { box-sizing: border-box; }
body { margin: 0; font-family: "Liberation Sans", "WenQuanYi Zen Hei", sans-serif; font-size: 9.6pt; line-height: 1.35; color: #111; }
header.top { display: flex; justify-content: space-between; align-items: flex-end; gap: 6mm; border-bottom: 2px solid #111; padding-bottom: 2mm; margin-bottom: 3mm; }
h1 { font-size: 14pt; margin: 0 0 1mm; }
header.top p { margin: 0; color: #444; font-size: 8.8pt; }
.boxes { display: grid; gap: 1.2mm; font-size: 9pt; text-align: right; white-space: nowrap; }
.boxes .score { font-weight: 700; font-size: 10.5pt; border: 1.5px solid #111; padding: 1mm 2mm; }
h2 { display: flex; justify-content: space-between; align-items: baseline; gap: 4mm; font-size: 10.5pt; margin: 3.5mm 0 1.2mm; padding: 1mm 2mm; background: #ececec; border-left: 3px solid #111; break-after: avoid; }
h2 small { font-weight: normal; font-size: 8.4pt; color: #444; }
h2.brk { break-before: page; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 0 8mm; }
.qi { break-inside: avoid; padding-top: 0.6mm; }
.grid2 .wl { height: 7.4mm; }
.p { font-size: 9.6pt; }
.p i, .bh i { font-style: normal; font-weight: 700; display: inline-block; min-width: 6mm; }
.p em { font-style: normal; color: #777; font-size: 8.2pt; margin-left: 1mm; }
.wl { height: 7.6mm; border-bottom: 1px solid #9a9a9a; }
.pair { display: grid; grid-template-columns: auto 1fr auto 1fr; gap: 0 2mm; align-items: end; }
.pair span { font-size: 8pt; color: #666; padding-bottom: 1mm; }
.blk { border-left: 2px solid #9a9a9a; padding: 0.5mm 0 1mm 3mm; margin-bottom: 2.5mm; }
.blk .bh { break-after: avoid; }
.bh { font-size: 9.6pt; margin-bottom: 0.5mm; }
.si { break-inside: avoid; margin-top: 1mm; }
.tag { display: inline-block; font-size: 7.6pt; font-weight: 700; padding: 0.3mm 1.3mm; margin-right: 1.8mm; border-radius: 1mm; border: 1px solid #111; }
.tag.w { background: #111; color: #fff; }
.scene { margin: 0 0 1mm; color: #444; font-size: 9pt; }
.tally { margin-top: 5mm; border: 1.5px solid #111; padding: 2mm 3mm; font-size: 10pt; font-weight: 700; break-inside: avoid; }
.key { break-before: page; font-size: 8.4pt; }
.key header.top { margin-bottom: 2mm; }
.rules { font-size: 8.4pt; background: #f2f2f2; padding: 1.5mm 2.5mm; margin-bottom: 2mm; }
.cols { column-count: 2; column-gap: 7mm; }
.cols h3 { font-size: 9.4pt; margin: 2mm 0 1mm; break-after: avoid; }
ol.sm { margin: 0; padding-left: 5.5mm; }
ol.sm li { margin: 0.4mm 0; break-inside: avoid; }
.ar { margin-top: 0.4mm; }
'''
title = f'职场{L}第1课自测卷A'
doc = f'<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>{title}</title><style>{css}</style></head><body>' + ''.join(q) + ''.join(a) + '</body></html>'
open(out, 'w').write(doc)
print('written', out)
