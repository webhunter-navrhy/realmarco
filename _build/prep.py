#!/usr/bin/env python3
"""Příprava dat: z uložených stránek realmarco.cz (scratchpad) vyrobí _build/data.json
a zmenšené fotky v assets/img/n/<id>/. Spouští se jednou; build.py pak čte data.json."""
import json, os, re, html, sys, unicodedata
from PIL import Image, ImageOps

SRC = sys.argv[1] if len(sys.argv) > 1 else '.'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_IMG = os.path.join(ROOT, 'assets', 'img', 'n')

lst = json.load(open(os.path.join(SRC, 'listings.json')))
active = [x for x in lst if not x['sold']]
sold = [x for x in lst if x['sold']]


def slugify(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()
    return re.sub(r'-+', '-', s)


def page_lines(pid):
    s = open(os.path.join(SRC, 'det', f'{pid}.html')).read().split('Novinky v nabídce')[0]
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', s, flags=re.S)
    t = re.sub(r'<[^>]+>', '\n', t)
    t = html.unescape(t)
    return [l.strip() for l in t.split('\n') if l.strip()]


def block(L, start, stops):
    if start not in L:
        return []
    i = L.index(start) + 1
    out = []
    while i < len(L) and L[i] not in stops:
        out.append(L[i]); i += 1
    return out


def clean_addr(meta):
    a = re.split(r'\s+\d+\s+(?:týdn|týdny|měsíc|měsíce|měsíců|rok|roky|let|dn|den|dny)\S*\s+ago', meta)[0]
    a = re.sub(r'\s+,', ',', a)
    for k, v in [(', South Moravian Region Czechia', ''), (', Southeast Czechia', ''), (', Central Moravia Czechia', ''),
                 (', Czechia', ''), (' Czechia', ''), (', Region of Bratislava Slovakia', ', Slovensko'),
                 ('Prague', 'Praha'), (', South Moravian Region', '')]:
        a = a.replace(k, v)
    a = re.sub(r'^,\s*', '', a).strip(' ,')
    return a


def num(s):
    d = re.sub(r'[^\d]', '', s)
    return int(d) if d else None


def fmt_num(v):
    v = v.strip()
    if re.fullmatch(r'\d+\.\d+', v):
        return v.replace('.', ',')
    if re.fullmatch(r'\d{4,}', v):
        return f'{int(v):,}'.replace(',', ' ')
    return v


def kind(title):
    t = title.lower()
    if 'pronájem' in t:
        return 'Pronájem'
    return 'Prodej'


BAD_NOTE = {21465}  # poznámka k ceně je u inzerátu zjevně zkopírovaná z jiné nabídky
OVERRIDE_TITLE = {}

data = []
for x in active:
    pid = x['id']
    L = page_lines(pid)
    stops = {'Občanská vybavenost', 'Informace o nemovitosti', 'Poznámka k ceně', 'Štítky', 'Lokalita', 'Půdorysy', 'Kontaktovat makléře'}
    amen = block(L, 'Občanská vybavenost', stops)
    feats = block(L, 'Informace o nemovitosti', stops)
    note = block(L, 'Poznámka k ceně', stops)
    note = ' '.join(note) if pid not in BAD_NOTE else ''
    pr = x['price_raw']
    price = None if 'On Call' in pr or not re.search(r'\d', pr) else num(pr.split('Kč')[0])
    monthly = 'měsíc' in pr
    params = []
    area = None
    land = None
    for k, v in x['overview']:
        if k.startswith('ID No'):
            continue
        k2 = k.replace('ID zakázky Sreality.cz', 'Číslo zakázky')
        if k2.startswith('Užitná plocha'):
            area = float(v.replace(',', '.'))
        if k2.startswith('Plocha pozemku'):
            land = float(v.replace(',', '.'))
        if k2.startswith('Cena za m'):
            k2, v = 'Cena za m²', f'{int(v):,} Kč'.replace(',', ' ')
        params.append([k2, fmt_num(v) if not k2.startswith('Číslo') else v])
    desc = x['desc']
    desc = re.sub(r'^O nemovitosti\n', '', desc)
    disp = re.search(r'\b(\d\+(?:kk|\d))\b', x['title'] + ' ' + desc[:400])
    # obrázky
    imgs = [u for u in x['imgs'] if u][:14]
    os.makedirs(os.path.join(OUT_IMG, str(pid)), exist_ok=True)
    out_imgs = []
    for k, u in enumerate(imgs):
        ext = u.rsplit('.', 1)[1].lower()
        src = os.path.join(SRC, 'raw', f'{pid}_{k:02d}.{ext}')
        if not os.path.exists(src):
            continue
        try:
            im = Image.open(src)
            im = ImageOps.exif_transpose(im).convert('RGB')
        except Exception as e:
            print('skip', src, e); continue
        w, h = im.size
        base = os.path.join(OUT_IMG, str(pid), f'{k:02d}')
        for W, q, suf in [(1800, 80, 'l'), (760, 76, 's')]:
            if not os.path.exists(f'{base}-{suf}.webp'):
                im2 = im.copy()
                if w > W:
                    im2 = im2.resize((W, round(h * W / w)), Image.LANCZOS)
                im2.save(f'{base}-{suf}.webp', 'WEBP', quality=q, method=5)
        out_imgs.append({'s': f'assets/img/n/{pid}/{k:02d}-s.webp', 'l': f'assets/img/n/{pid}/{k:02d}-l.webp',
                         'w': w, 'h': h, 'plan': bool(re.search(r'pudorys|layout|půdorys', u, re.I))})
    cat = x['cat'][1] if len(x['cat']) > 1 else 'Ostatní'
    data.append({
        'id': pid, 'slug': slugify(x['title']), 'title': OVERRIDE_TITLE.get(pid, x['title']).replace('  ', ' '),
        'orig': x['url'], 'date': x['date'], 'kind': kind(x['title']), 'cat': cat,
        'price': price, 'monthly': monthly, 'note': note, 'addr': clean_addr(x['meta']),
        'area': area, 'land': land, 'disp': disp.group(1) if disp else '', 'params': params,
        'desc': desc, 'amen': amen, 'feats': feats, 'broker': x['broker'],
        'badges': [b for b in x['badges'] if b in ('Novinka', 'TOP nabídka', 'Doporučujeme')], 'imgs': out_imgs,
    })

# realizované – jen fotka + titul (bez počtů)
real = []
for x in sold[:24]:
    pid = x['id']
    fs = [f for f in os.listdir(os.path.join(SRC, 'raw')) if f.startswith(f's{pid}_')]
    if not fs:
        continue
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, 'raw', fs[0]))).convert('RGB')
    if 'ChatGPT' in ''.join(x['imgs'][:1]):
        continue
    os.makedirs(os.path.join(OUT_IMG, 'r'), exist_ok=True)
    p = os.path.join(OUT_IMG, 'r', f'{pid}.webp')
    if not os.path.exists(p):
        w, h = im.size
        im.resize((720, round(h * 720 / w)), Image.LANCZOS).save(p, 'WEBP', quality=74, method=5)
    real.append({'id': pid, 'title': x['title'], 'kind': kind(x['title']), 'img': f'assets/img/n/r/{pid}.webp'})

json.dump({'listings': data, 'realized': real}, open(os.path.join(ROOT, '_build', 'data.json'), 'w'), ensure_ascii=False, indent=1)
print(len(data), 'aktivních,', len(real), 'realizovaných')
