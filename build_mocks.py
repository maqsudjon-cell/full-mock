#!/usr/bin/env python3
"""Generate full-mock pages for Mocks 2-5 from existing engines + user's writing materials."""
import json, re, os, sys

FM = '/Users/macbook/Downloads/full-mock'
DL = '/Users/macbook/Downloads'

MOCKS = [
    # n, listening source test, reading source cdi
    (2, 19, 6),
    (3, 20, 7),
    (4, 21, 1),
    (5, 22, 2),
]

# ───────────────────────── listening ─────────────────────────
def build_listening(n, test):
    tpl = open(f'{FM}/listening.html').read()
    src = open(f'{DL}/Diyorbek_Test{test}/diyorbek-test{test}-listening.html').read()

    sec_re = re.compile(r'<section class="part-section active" id="part-1">[\s\S]*?(?=\n?\s*<div class="submit-wrap">)')
    m_src, m_tpl = sec_re.search(src), sec_re.search(tpl)
    assert m_src and m_tpl, f'sections not found for test {test}'
    tpl = tpl[:m_tpl.start()] + m_src.group(0) + tpl[m_tpl.end():]

    for name in ('correctAnswers', 'multiCorrect'):
        line_re = re.compile(r'const %s = \{.*?\};' % name)
        m_src2, m_tpl2 = line_re.search(src), line_re.search(tpl)
        assert m_src2 and m_tpl2, f'{name} not found for test {test}'
        tpl = tpl[:m_tpl2.start()] + m_src2.group(0) + tpl[m_tpl2.end():]

    m_tracks = re.search(r'const audioTracks = (\{.*?\});', src)
    assert m_tracks, f'audioTracks not found for test {test}'
    tracks = json.loads(m_tracks.group(1))
    tracks = {k: v.replace('.m4a', '.mp3') for k, v in tracks.items()}
    new_tracks = 'const audioTracks = {' + ', '.join(
        f'"{k}": AUDIO_BASE+"{v}"' for k, v in sorted(tracks.items())) + '};'
    tpl = re.sub(r'const audioTracks = \{.*?\};', new_tracks, tpl, count=1)
    tpl = tpl.replace("const AUDIO_BASE = 'https://pangea8.com/test14/';",
                      f"const AUDIO_BASE = 'https://pangea8.com/test{test}/';")
    tpl = re.sub(r'<source id="audio-src" src="[^"]*"',
                 f'<source id="audio-src" src="https://pangea8.com/test{test}/{tracks["1"]}"', tpl, count=1)
    tpl = tpl.replace("P8M.requireStage('listening', 1)", f"P8M.requireStage('listening', {n})")
    tpl = tpl.replace("location.replace('reading.html')", f"location.replace('reading{n}.html')")

    # sanity: answers cover 1..40
    ca = json.loads(re.search(r'const correctAnswers = (\{.*?\});', tpl).group(1))
    missing = [q for q in range(1, 41) if str(q) not in ca]
    assert not missing, f'test {test}: missing answers {missing}'
    open(f'{FM}/listening{n}.html', 'w').write(tpl)
    print(f'listening{n}.html  <- Test {test}  (answers 1-40 ok)')

# ───────────────────────── reading ─────────────────────────
def build_reading(n, cdi):
    tpl = open(f'{FM}/reading.html').read()
    src = open(f'{DL}/cdi-build/cdi-reading-{cdi}/index.html').read()

    blk_re = re.compile(r'/\* ---------- 1\) PASSAGES ---------- \*/[\s\S]*?(?=/\* =+\n\s*END OF AUTHORING AREA)')
    m_src, m_tpl = blk_re.search(src), blk_re.search(tpl)
    assert m_src and m_tpl, f'authoring block not found for cdi-{cdi}'
    tpl = tpl[:m_tpl.start()] + m_src.group(0) + tpl[m_tpl.end():]

    tpl = tpl.replace("P8M.requireStage('reading', 1)", f"P8M.requireStage('reading', {n})")
    tpl = tpl.replace("location.replace('writing.html')", f"location.replace('writing{n}.html')")

    # sanity: ANSWERS has 40 entries
    m_ans = re.search(r'const ANSWERS = \{([\s\S]*?)\};', tpl)
    keys = set(int(k) for k in re.findall(r'(\d+)\s*:', m_ans.group(1)))
    missing = [q for q in range(1, 41) if q not in keys]
    assert not missing, f'cdi-{cdi}: missing ANSWERS {missing}'
    open(f'{FM}/reading{n}.html', 'w').write(tpl)
    print(f'reading{n}.html    <- cdi-reading-{cdi}  (ANSWERS 1-40 ok)')

# ───────────────────────── writing charts ─────────────────────────
F = 'font-family="Arial,Helvetica,sans-serif"'

def wrap_label(s, width=11):
    words, lines, cur = s.split(), [], ''
    for w in words:
        if cur and len(cur) + 1 + len(w) > width: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    if cur: lines.append(cur)
    return lines[:3]

def vbar(title, cats, vals, ymax, ystep):
    W, H, ml, mr, mt, mb = 640, 330, 46, 12, 36, 66
    pw, ph = W - ml - mr, H - mt - mb
    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" style="max-width:100%;height:auto;background:#fff">']
    out.append(f'<text x="{W/2}" y="20" text-anchor="middle" font-size="15" font-weight="bold" {F} fill="#111">{title}</text>')
    y = 0
    while y <= ymax:
        py = mt + ph - ph * y / ymax
        out.append(f'<line x1="{ml}" y1="{py:.1f}" x2="{ml+pw}" y2="{py:.1f}" stroke="{"#999" if y==0 else "#e5e7eb"}" stroke-width="1"/>')
        out.append(f'<text x="{ml-8}" y="{py+4:.1f}" text-anchor="end" font-size="11" {F} fill="#444">{y}</text>')
        y += ystep
    slot = pw / len(cats); bw = slot * 0.5
    for i, (c, v) in enumerate(zip(cats, vals)):
        x = ml + slot * i + (slot - bw) / 2
        bh = ph * v / ymax
        out.append(f'<rect x="{x:.1f}" y="{mt+ph-bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="#2f5fa8"/>')
        for j, ln in enumerate(wrap_label(c)):
            out.append(f'<text x="{ml+slot*i+slot/2:.1f}" y="{mt+ph+16+j*13}" text-anchor="middle" font-size="11" {F} fill="#333">{ln}</text>')
    out.append('</svg>')
    return ''.join(out)

def hbar_grouped(title, cats, men, women, xmax, xstep):
    W, ml, mr, mt, rowh, gap = 640, 200, 20, 40, 44, 10
    H = mt + len(cats) * rowh + 34
    pw = W - ml - mr
    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" style="max-width:100%;height:auto;background:#fff">']
    out.append(f'<text x="{W/2}" y="22" text-anchor="middle" font-size="15" font-weight="bold" {F} fill="#111">{title}</text>')
    x = 0
    while x <= xmax:
        px = ml + pw * x / xmax
        out.append(f'<line x1="{px:.1f}" y1="{mt}" x2="{px:.1f}" y2="{mt+len(cats)*rowh}" stroke="{"#999" if x==0 else "#e5e7eb"}" stroke-dasharray="{"none" if x==0 else "3 3"}"/>')
        out.append(f'<text x="{px:.1f}" y="{mt+len(cats)*rowh+18}" text-anchor="middle" font-size="11" {F} fill="#444">{x}</text>')
        x += xstep
    for i, c in enumerate(cats):
        y0 = mt + i * rowh + 6
        out.append(f'<rect x="{ml}" y="{y0}" width="{pw*men[i]/xmax:.1f}" height="13" fill="#4b5563"/>')
        out.append(f'<rect x="{ml}" y="{y0+16}" width="{pw*women[i]/xmax:.1f}" height="13" fill="#f59e0b"/>')
        out.append(f'<text x="{ml-8}" y="{y0+19}" text-anchor="end" font-size="12" {F} fill="#333">{c}</text>')
    lx = ml + pw - 96
    out.append(f'<rect x="{lx-8}" y="{mt-4}" width="104" height="44" fill="#fff" stroke="#e5e7eb"/>')
    out.append(f'<rect x="{lx}" y="{mt+2}" width="12" height="12" fill="#4b5563"/><text x="{lx+18}" y="{mt+12}" font-size="12" {F} fill="#333">Men</text>')
    out.append(f'<rect x="{lx}" y="{mt+20}" width="12" height="12" fill="#f59e0b"/><text x="{lx+18}" y="{mt+30}" font-size="12" {F} fill="#333">Women</text>')
    out.append('</svg>')
    return ''.join(out)

def pie(title, labels, vals, colors):
    import math
    W, H, cx, cy, r = 640, 320, 170, 175, 115
    total = sum(vals)
    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" style="max-width:100%;height:auto;background:#fff">']
    out.append(f'<text x="{W/2}" y="24" text-anchor="middle" font-size="15" font-weight="bold" {F} fill="#111">{title}</text>')
    a0 = -90.0
    for lab, v, col in zip(labels, vals, colors):
        a1 = a0 + 360.0 * v / total
        x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
        x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
        large = 1 if (a1 - a0) > 180 else 0
        out.append(f'<path d="M{cx},{cy} L{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f} Z" fill="{col}" stroke="#fff" stroke-width="1.5"/>')
        amid = math.radians((a0 + a1) / 2)
        lx, ly = cx + r * 0.62 * math.cos(amid), cy + r * 0.62 * math.sin(amid)
        out.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" font-size="13" font-weight="bold" {F} fill="#fff">{v}%</text>')
        a0 = a1
    ly0 = 70
    for i, (lab, col) in enumerate(zip(labels, colors)):
        out.append(f'<rect x="340" y="{ly0+i*30}" width="14" height="14" fill="{col}"/>')
        out.append(f'<text x="362" y="{ly0+i*30+12}" font-size="13" {F} fill="#333">{lab} — {vals[i]}%</text>')
    out.append('</svg>')
    return ''.join(out)

def table_html(caption, head, rows):
    h = f'<table class="data"><caption>{caption}</caption><thead><tr>' + \
        ''.join(f'<th>{c}</th>' for c in head) + '</tr></thead><tbody>'
    for row in rows:
        h += '<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>'
    return h + '</tbody></table>'

def t1_html(box, visual):
    return ('<h2>Writing Task 1</h2>'
            '<p class="tasknote">You should spend about <b>20 minutes</b> on this task.</p>'
            f'<div class="taskbox">{box}<br><br>Summarise the information by selecting and reporting the main features, and make comparisons where relevant.</div>'
            '<p class="minwords">Write at least <b>150 words</b>.</p>' + visual)

def t2_html(box):
    return ('<h2>Writing Task 2</h2>'
            '<p class="tasknote">You should spend about <b>40 minutes</b> on this task.</p>'
            f'<div class="taskbox">{box}</div>'
            '<p class="minwords">Write at least <b>250 words</b>. Give reasons for your answer and include any relevant examples from your own knowledge or experience.</p>')

WRITING = {
2: dict(
    t1_box="The bar charts below display the results from a 2009 survey regarding people&#39;s cars in a European country.",
    t1_visual=(vbar('How often do you change your car?',
                    ['Every year', 'Every 2 years', 'Every 3-4 years', 'Every 5 years or more', 'Never change', 'No car'],
                    [1, 5, 37, 52, 3, 2], 60, 10) +
               vbar('What car do you buy?',
                    ['New', 'Second-hand', 'Sometimes new / sometimes second-hand', 'No car'],
                    [25, 68, 10, 2], 80, 10)),
    t1_prompt=("The two bar charts show the results of a 2009 survey about people's cars in a European country. "
               "Chart 1, 'How often do you change your car?' (% of respondents): every year 1, every 2 years 5, every 3-4 years 37, every 5 years or more 52, never change 3, no car 2. "
               "Chart 2, 'What car do you buy?': new 25, second-hand 68, sometimes new/sometimes second-hand 10, no car 2. "
               "Summarise the information by selecting and reporting the main features, and make comparisons where relevant."),
    t2_box="Rich countries often give money to poorer countries, but it does not solve poverty. Therefore, developed countries should give other types of help to the poor countries rather than financial aid.<br><br>To what extent do you agree or disagree?",
    t2_prompt="Rich countries often give money to poorer countries, but it does not solve poverty. Therefore, developed countries should give other types of help to the poor countries rather than financial aid. To what extent do you agree or disagree?"),
3: dict(
    t1_box="The charts below show the comparison of time spent, in minutes per day, by males and females in the UK on household and leisure activities in 2008.",
    t1_visual=(table_html('Leisure activities (average minutes per day)',
                          ['Activity', 'Men', 'Women'],
                          [['TV, video, radio', 137, 118], ['Reading', 18, 19], ['Sport', 15, 11]]) +
               hbar_grouped('Household activities (average minutes per day)',
                            ['Cooking and washing', 'Shopping', 'Repair', 'Clothes washing and ironing'],
                            [27, 24, 20, 12], [75, 33, 7, 30], 80, 20)),
    t1_prompt=("The table and bar chart compare time spent, in minutes per day, by UK men and women on leisure and household activities in 2008. "
               "Leisure (men/women): TV, video and radio 137/118; reading 18/19; sport 15/11. "
               "Household (men/women): cooking and washing 27/75; shopping 24/33; repair 20/7; clothes washing and ironing 12/30. "
               "Summarise the information by selecting and reporting the main features, and make comparisons where relevant."),
    t2_box="Some people think that it is important to use leisure time for activities that improve the mind, such as reading and doing word puzzles. Other people feel that it is important to rest the mind during leisure time.<br><br>Discuss both views and give your own opinion.",
    t2_prompt="Some people think that it is important to use leisure time for activities that improve the mind, such as reading and doing word puzzles. Other people feel that it is important to rest the mind during leisure time. Discuss both views and give your own opinion."),
4: dict(
    t1_box="The chart and table below show the results of a survey of library users at a university.",
    t1_visual=(pie('Categories of library users',
                   ['Full-time undergraduate', 'Full-time postgraduate', 'Part-time postgraduate', 'Distance learning (all courses)', 'Academic staff'],
                   [44, 25, 16, 8, 7],
                   ['#2f5fa8', '#a5a5a5', '#f59e0b', '#264478', '#70ad47']) +
               table_html('Library user satisfaction (%)',
                          ['', 'Very satisfied', 'Fairly satisfied', 'Not satisfied'],
                          [['Library opening hours', 65, 35, 0], ['Helpfulness of staff', 95, 5, 0],
                           ['Availability of books', 50, 40, 10], ['Availability of journals', 45, 35, 20],
                           ['Reliability of wi-fi', 48, 33, 19]])),
    t1_prompt=("The pie chart and table show the results of a survey of library users at a university. "
               "Categories of users: full-time undergraduate 44%, full-time postgraduate 25%, part-time postgraduate 16%, distance learning 8%, academic staff 7%. "
               "Satisfaction (% very satisfied / fairly satisfied / not satisfied): library opening hours 65/35/0; helpfulness of staff 95/5/0; availability of books 50/40/10; availability of journals 45/35/20; reliability of wi-fi 48/33/19. "
               "Summarise the information by selecting and reporting the main features, and make comparisons where relevant."),
    t2_box="Some people say that children should spend their free time on clubs and extra classes. Others, however, believe they should spend their leisure time doing activities with their families.<br><br>Discuss both of these views and give your own opinion.",
    t2_prompt="Some people say that children should spend their free time on clubs and extra classes. Others, however, believe they should spend their leisure time doing activities with their families. Discuss both of these views and give your own opinion."),
5: dict(
    t1_box="The table below shows the percentage of households with internet access in five European countries in three years and compares them with the European average.",
    t1_visual=table_html('Households with internet access (%)',
                         ['Country', '2010', '2015', '2020'],
                         [['Country 1', 45, 62, 70], ['Country 2', 60, 75, 85], ['Country 3', 55, 68, 66],
                          ['Country 4', 70, 70, 72], ['Country 5', 82, 90, 96], ['Average of 5', 62, 73, 78]]),
    t1_prompt=("The table shows the percentage of households with internet access in five European countries in 2010, 2015 and 2020, compared with the average of the five. "
               "Data (2010/2015/2020): Country 1: 45/62/70; Country 2: 60/75/85; Country 3: 55/68/66; Country 4: 70/70/72; Country 5: 82/90/96; Average of 5: 62/73/78. "
               "Summarise the information by selecting and reporting the main features, and make comparisons where relevant."),
    t2_box="Children&#39;s leisure activities should always be educational because they may have too much to learn before they become adults.<br><br>Do you agree or disagree?",
    t2_prompt="Children's leisure activities should always be educational because they may have too much to learn before they become adults. Do you agree or disagree?"),
}

def build_writing(n):
    tpl = open(f'{FM}/writing.html').read()
    w = WRITING[n]
    block = ('var TASKS = {\n'
             '  1: { min: 150,\n'
             '       html: ' + json.dumps(t1_html(w['t1_box'], w['t1_visual'])) + ',\n'
             '       prompt: ' + json.dumps(w['t1_prompt']) + ' },\n'
             '  2: { min: 250,\n'
             '       html: ' + json.dumps(t2_html(w['t2_box'])) + ',\n'
             '       prompt: ' + json.dumps(w['t2_prompt']) + ' }\n'
             '};')
    new = re.sub(r'var TASKS = \{[\s\S]*?\n\};', lambda m: block, tpl, count=1)
    assert new != tpl, 'TASKS block not replaced'
    new = new.replace("P8M.requireStage('writing', 1)", f"P8M.requireStage('writing', {n})")
    open(f'{FM}/writing{n}.html', 'w').write(new)
    print(f'writing{n}.html    (tasks embedded)')

for n, test, cdi in MOCKS:
    build_listening(n, test)
    build_reading(n, cdi)
    build_writing(n)
print('ALL GENERATED OK')
