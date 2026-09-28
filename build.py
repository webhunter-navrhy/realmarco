#!/usr/bin/env python3
"""Real Marco – návrh nového webu.
Spuštění: python3 build.py → vygeneruje index.html, nabidka/, nemovitost/<slug>/ a 404.html
Data inzerátů jsou v _build/data.json (vyrobeno z realmarco.cz skriptem _build/prep.py).
"""
import hashlib, html, json, os, re, shutil
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(ROOT, '_build', 'data.json')))
LIST = sorted(D['listings'], key=lambda x: x['date'], reverse=True)
REAL = D['realized']
E = html.escape


def ver(p):
    with open(os.path.join(ROOT, p), 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()[:8]


V_CSS, V_JS = ver('assets/style.css'), ver('assets/main.js')


def nb(s):
    """nezlomitelné mezery po jednopísmenných předložkách a spojkách"""
    return re.sub(r'(?<=[\s(„])([vVsSkKzZoOuUaAiI])\s', r'\1&nbsp;', ' ' + s)[1:]


def money(v):
    return f'{v:,}'.replace(',', '&nbsp;')


def price_html(x):
    if not x['price']:
        return 'Cena na dotaz'
    s = money(x['price']) + '&nbsp;Kč'
    if x['monthly']:
        s += '<small>&nbsp;/&nbsp;měsíc</small>'
    return s


def m2(v):
    if v is None:
        return ''
    s = f'{v:.1f}'.rstrip('0').rstrip('.').replace('.', ',')
    if v >= 1000:
        s = f'{int(v):,}'.replace(',', '&nbsp;')
    return s + '&nbsp;m²'


# ---------------------------------------------------------------- doplňková data (z realmarco.cz)
LOC = {21804: 'Záříčí', 21755: 'Brno – Horní Heršpice', 21744: 'Zlín – Klečůvka', 21319: 'Kuřim', 21465: 'Brno – Černá Pole',
       21569: 'Závist, okres Blansko', 21687: 'Praha – Karlín', 21711: 'Zdravá Voda – Žarošice', 21305: 'Velké Hostěrádky',
       21335: 'Heroltice u Tišnova', 20995: 'Bratislava', 21012: 'Sedlec u Mikulova', 20953: 'Ochoz u Brna', 20779: 'Boskovice',
       20577: 'Napajedla', 18644: 'Luhačovice', 19720: 'Diváky', 18801: 'Brno – Tuřany', 18567: 'Brno – Tuřany',
       18592: 'Brno – Tuřany', 18454: 'Syrovice', 18614: 'Brno – Tuřany'}
REG = {'brno': [21755, 21465, 18801, 18567, 18592, 18614],
       'jm': [21319, 21569, 21711, 21305, 21335, 21012, 20953, 20779, 19720, 18454],
       'zlin': [21804, 21744, 20577, 18644], 'praha': [21687], 'sk': [20995]}
REG_LABEL = {'brno': 'Brno', 'jm': 'Jižní Morava', 'zlin': 'Zlínsko', 'praha': 'Praha', 'sk': 'Bratislava'}
REG_OF = {i: r for r, ids in REG.items() for i in ids}
CAT = {'Byty': ('byty', 'Byt'), 'Rodinné domy': ('domy', 'Dům'), 'Pozemky': ('pozemky', 'Pozemek'),
       'Komerční prostory': ('komercni', 'Komerční'), 'Ostatní': ('ostatni', 'Ostatní')}
CAT_ORDER = [('byty', 'Byty'), ('domy', 'Domy'), ('pozemky', 'Pozemky'), ('komercni', 'Komerční'), ('ostatni', 'Chaty a jiné')]
TYPE_LABEL = {21711: 'Areál', 21305: 'Dům', 21335: 'Chata', 21012: 'Vinařství', 20953: 'Chata'}

BROKERS = [
    {'key': 'Marek Karvaj', 'first': 'Marek', 'last': 'Karvaj', 'role': 'Realitní makléř, zakladatel', 'tel': '+420 777 699 754',
     'mail': 'karvaj@realmarco.cz', 'img': 'marek',
     'bio': 'Charizmatický zakladatel společnosti s největšími zkušenostmi v oboru, ve kterém úspěšně působí již 15 let. Obchodní a hypoteční král a náš zásadní stratég. Za Markem si můžete kdykoliv přijít pro radu, nikdy vás neodmítne. Nejčastěji ho můžete spatřit u jídla, na golfu nebo na rodinném vinohradě.'},
    {'key': 'Tamara Hanáková', 'first': 'Tamara', 'last': 'Hanáková', 'role': 'Realitní makléřka', 'tel': '+420 603 954 846',
     'mail': 'hanakova@realmarco.cz', 'img': 'tamara',
     'bio': 'Spojovací článek nás všech. Ve svojí práci často využívá emoce, nejvíc rozumí marketingu a ráda píše texty. Opravdovou satisfakcí jsou pro ni výsledky, kdy jsou všichni klienti spokojení. Vášnivá fanynka Komety Brno, sportovec a knihomol.'},
    {'key': 'Dušan Valach', 'first': 'Dušan', 'last': 'Valach', 'role': 'Realitní makléř', 'tel': '+420 608 712 571',
     'mail': 'valach@realmarco.cz', 'img': 'dusan',
     'bio': 'Solitérní a zásadní pilíř, vzbuzující respekt nejen svojí postavou. U Dušana vždy najdete prostor k sebevyjádření a přátelské debatě. Pracovně má za sebou desítky úspěšných obchodů a složitých jednání. Největšími koníčky jsou rybaření, kolo a cestování s rodinou.'},
    {'key': 'Alexandra Rumíšková', 'first': 'Alexandra', 'last': 'Rumíšková', 'role': 'Realitní makléřka', 'tel': '+420 604 685 528',
     'mail': 'rumiskova@realmarco.cz', 'img': 'alexandra',
     'bio': 'Ohnivá hříva a nevyčerpatelná pozitivní energie. K Alex si chodíme pro klid a nadhled, pro mléko do kávy a pro úsměv. O své klienty se stará pečlivě a stoprocentně. Mezi velké záliby patří architektura, chalupa a sport.'},
]
BRK = {b['key']: b for b in BROKERS}

REVIEWS = [
    ('Chtěla bych poděkovat Tamaře Hanákové za velice profesionální přístup při dlouhodobém pronajímání mého bytu. Její rady jsou velice užitečné.', 'Jana Pokorná', 'pronájem bytu'),
    ('Děkuji Marku Karvajovi za profesionální přístup při prodeji mé nemovitosti. Realitní kancelář Real Marco doporučuji ve všech ohledech.', 'Mgr. Martin Koťa', 'prodej nemovitosti'),
    ('Hledali jsme pozemek nedaleko Brna, který by splňoval všechny naše podmínky pro spokojený rodinný život. Díky panu Karvajovi jsme ho našli.', 'Luděk Pokorný', 'koupě pozemku'),
    ('S realitnou spoločnosťou REAL MARCO som veľmi spokojná. Zástupcovia realitnej spoločnosti sú vysoko profesionálni a celý obchod – kúpa bytu – bol bezproblémový, rýchly, koordinovaný tak, aby obchod prebehol v krátkom časovom horizonte.', 'Bc. Andrea Dudziková, MBA.', 'koupě bytu'),
]

OFFICE = {'addr': 'Hlinky 118, 603 00 Brno', 'area': 'Staré Brno', 'tel': '+420 603 954 846', 'tel2': '+420 777 699 754',
          'mail': 'info@realmarco.cz', 'fb': 'https://www.facebook.com/realmarcocz', 'ig': 'https://www.instagram.com/realmarcocz/'}


def tel(t):
    return 'tel:' + t.replace(' ', '')


# ---------------------------------------------------------------- komponenty
ICON = {
    'arrow': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    'phone': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/></svg>',
    'mail': '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="1"/><path d="m3 7 9 6 9-6"/></svg>',
    'pin': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>',
    'grid': '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
    'close': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>',
    'left': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>',
    'right': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>',
    'filter': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M7 12h10M10 18h4"/></svg>',
    'fb': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 8h3V4h-3a4 4 0 0 0-4 4v2H7v4h3v7h4v-7h3l1-4h-4V8z"/></svg>',
    'ig': '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r=".6"/></svg>',
}


def head(r, title, desc, extra_class=''):
    return f'''<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{E(desc)}">
<meta name="theme-color" content="#F6F4EE">
<script>document.documentElement.classList.add('js')</script>
<meta property="og:title" content="{title}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:type" content="website">
<meta name="robots" content="noindex">
<link rel="icon" href="{r}assets/img/site/favicon-64.png" type="image/png">
<link rel="apple-touch-icon" href="{r}assets/img/site/apple-touch.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Onest:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}assets/style.css?v={V_CSS}">
<script src="{r}assets/main.js?v={V_JS}" defer></script>
</head>
<body class="{extra_class}">
<div class="progress" aria-hidden="true"></div>
<a class="skip" href="#obsah">Přeskočit na obsah</a>
'''


def nav(r, active=''):
    def a(href, label, key):
        cur = ' aria-current="page"' if key == active else ''
        return f'<a href="{href}" class="ul"{cur}>{label}</a>'
    home = r or './'
    return f'''<header class="nav" id="nav">
  <div class="nav-in">
    <a class="brand" href="{home}" aria-label="Real Marco – úvod"><img src="{r}assets/img/site/logo.png" alt="Real Marco" width="720" height="185"></a>
    <nav class="menu" id="menu" aria-label="Hlavní navigace">
      {a(r + 'nabidka/', 'Nabídka', 'nabidka')}
      {a(home + '#sluzby', 'Služby', 'sluzby')}
      {a(home + '#development', 'Development', 'dev')}
      {a(home + '#makleri', 'Makléři', 'makleri')}
      {a(home + '#o-nas', 'O nás', 'onas')}
      {a(home + '#kontakt', 'Kontakt', 'kontakt')}
      <div class="menu-foot">
        <a href="{tel(OFFICE['tel'])}">{OFFICE['tel']}</a>
        <a href="mailto:{OFFICE['mail']}">{OFFICE['mail']}</a>
      </div>
    </nav>
    <div class="nav-cta">
      <a class="nav-tel" href="{tel(OFFICE['tel'])}">{ICON['phone']}<span>{OFFICE['tel']}</span></a>
      <a class="btn btn-y btn-sm" href="{home}#kontakt">Napište nám</a>
    </div>
    <button class="burger" id="burger" aria-label="Otevřít menu" aria-expanded="false" aria-controls="menu"><span></span><span></span></button>
  </div>
</header>
'''


def footer(r):
    home = r or './'
    return f'''<footer class="foot">
  <div class="wrap">
    <div class="foot-top">
      <img class="foot-logo" src="{r}assets/img/site/logo-light.png" alt="Real Marco" width="720" height="185" loading="lazy">
      <p class="foot-claim">Realitní kancelář <em>na&nbsp;úrovni.</em><br>Prodej, pronájem a&nbsp;správa nemovitostí v&nbsp;Brně a&nbsp;okolí.</p>
    </div>
    <div class="foot-cols">
      <div><h4>Kancelář</h4><p>{OFFICE['addr']}<br>{OFFICE['area']}</p></div>
      <div><h4>Kontakt</h4><p><a class="ul" href="{tel(OFFICE['tel'])}">{OFFICE['tel']}</a><br><a class="ul" href="mailto:{OFFICE['mail']}">{OFFICE['mail']}</a></p></div>
      <div><h4>Web</h4><p><a class="ul" href="{r}nabidka/">Nabídka nemovitostí</a><br><a class="ul" href="{home}#makleri">Naši makléři</a><br><a class="ul" href="{home}#development">Development Syrovice</a></p></div>
      <div><h4>Sledujte nás</h4><p class="foot-soc"><a href="{OFFICE['fb']}" target="_blank" rel="noopener" aria-label="Facebook">{ICON['fb']}</a><a href="{OFFICE['ig']}" target="_blank" rel="noopener" aria-label="Instagram">{ICON['ig']}</a></p></div>
    </div>
    <div class="foot-bot">
      <span>© 2026 Real Marco · Chateau Marco, s.r.o., IČ 29237394</span>
      <span>Návrh webu: <a class="ul" href="https://webhunter.cz" target="_blank" rel="noopener">WebHunter</a></span>
    </div>
  </div>
</footer>
'''


def card(x, r, big=False, lazy=True):
    slug, k = CAT[x['cat']]
    typ = TYPE_LABEL.get(x['id'], k)
    imgs = [i for i in x['imgs'] if not i['plan']] or x['imgs']
    im1 = imgs[0]
    im2 = imgs[1] if len(imgs) > 1 else None
    src = im1['l'] if big else im1['s']
    ld = ' loading="lazy"' if lazy else ' fetchpriority="high"'
    facts = []
    if x['disp']:
        facts.append(x['disp'])
    if x['area']:
        facts.append(m2(x['area']))
    if x['land'] and x['cat'] in ('Pozemky', 'Rodinné domy', 'Ostatní'):
        facts.append(('pozemek ' if x['area'] else '') + m2(x['land']))
    badges = ''.join(f'<span class="badge{" badge-y" if b != "Doporučujeme" else ""}">{b}</span>' for b in x['badges'] if b != 'Doporučujeme')
    href = f'{r}nemovitost/{x["slug"]}/'
    alt2 = f'<img class="alt" src="{r}{im2["l" if big else "s"]}" alt="" loading="lazy" decoding="async">' if im2 else ''
    return f'''<article class="card{" card-big" if big else ""} rv" data-kind="{"pronajem" if x["kind"] == "Pronájem" else "prodej"}" data-cat="{slug}" data-reg="{REG_OF.get(x["id"], "jm")}" data-price="{x["price"] or 0}" data-area="{int(x["area"] or x["land"] or 0)}" data-date="{x["date"]}">
  <a class="card-media" href="{href}" tabindex="-1" aria-hidden="true">
    <img src="{r}{src}" alt="{E(x["title"])}"{ld} decoding="async" width="{1800 if big else 760}" height="{round((1800 if big else 760) * im1["h"] / im1["w"])}">{alt2}
    <span class="card-badges"><span class="badge badge-k">{x["kind"]}</span>{badges}</span>
    <span class="card-count">{ICON['grid']}{len(x["imgs"])}</span>
  </a>
  <div class="card-body">
    <p class="card-meta"><span>{typ}</span><span>{E(LOC[x["id"]])}</span></p>
    <h3 class="card-title"><a href="{href}">{nb(E(x["title"]))}</a></h3>
    <p class="card-facts">{"<span>" + "</span><span>".join(facts) + "</span>" if facts else ""}</p>
    <p class="card-price">{price_html(x)}</p>
  </div>
</article>'''


# ---------------------------------------------------------------- úvodní stránka
def build_home():
    r = ''
    hero_x = next(x for x in LIST if x['id'] == 18644)
    newest = LIST[:6]
    n = len(LIST)
    words1 = 'Realitní kancelář'.split()
    h1 = ' '.join(f'<span class="w"><span style="--i:{i}">{w}</span></span>' for i, w in enumerate(words1))
    cat_opts = ''.join(f'<option value="{s}">{l}</option>' for s, l in CAT_ORDER)

    services = [
        ('Prodáme', 'Rychlý prodej a profesionální prezentace vaší nemovitosti se všemi potřebnými podklady a dokumenty.', 'assets/img/n/21465/00-s.webp', '#kontakt'),
        ('Pronajmeme', 'Bezstarostný pronájem včetně nájemních a podnájemních smluv. Vlastní automatizovaný systém: od prověření nájemce přes smlouvy až po předání klíčů.', 'assets/img/n/21687/01-s.webp', '#kontakt'),
        ('Najdeme', 'Pomůžeme vám najít vysněnou nemovitost, ať už jde o dům, byt, pozemek nebo komerční prostory.', 'assets/img/n/21804/01-s.webp', 'nabidka/'),
        ('Odhad ceny zdarma', 'Potřebujete znát odhadní cenu své nemovitosti? Napište nám a my se ozveme nejpozději druhý den.', 'assets/img/n/20577/00-s.webp', '#kontakt'),
        ('Development', 'Projektový management a prodej developerských projektů – od pozemků po hotové domy.', 'assets/img/n/18454/03-s.webp', '#development'),
        ('Správa, hypotéky, investice', 'Správa bytových domů, hypoteční poradenství a návrhy menších interiérů. Sdružujeme investory a hledáme nové možnosti investování.', 'assets/img/site/kancelar-zasedacka.webp', '#kontakt'),
    ]
    srv = '\n'.join(f'''<a class="srv rv" href="{h}" data-img="{img}">
        <span class="srv-n">{i + 1:02d}</span>
        <h3 class="srv-t">{t}</h3>
        <p class="srv-p">{nb(p)}</p>
        <span class="srv-a">{ICON['arrow']}</span>
      </a>''' for i, (t, p, img, h) in enumerate(services))

    team = '\n'.join(f'''<article class="agent rv" style="--d:{i * 90}ms">
        <div class="agent-ph"><img src="assets/img/site/{b['img']}.webp" alt="{b['first']} {b['last']}" loading="lazy" width="700" height="700"></div>
        <h3 class="agent-n"><span>{b['first']}</span> {b['last']}</h3>
        <p class="agent-r">{b['role']}</p>
        <p class="agent-bio">{nb(b['bio'])}</p>
        <p class="agent-c"><a class="ul" href="{tel(b['tel'])}">{b['tel']}</a><a class="ul" href="mailto:{b['mail']}">{b['mail']}</a></p>
      </article>''' for i, b in enumerate(BROKERS))

    rev_main = REVIEWS[0]
    revs = '\n'.join(f'''<figure class="rev rv" style="--d:{i * 90}ms"><blockquote>„{nb(q)}“</blockquote><figcaption><strong>{a}</strong><span>{c}</span></figcaption></figure>''' for i, (q, a, c) in enumerate(REVIEWS[1:]))
    real = ''.join(f'<figure class="real-i"><img src="{x["img"]}" alt="{E(x["title"])}" loading="lazy" width="720" height="480"><figcaption><span>Realizováno</span>{E(x["title"])}</figcaption></figure>' for x in REAL[:14])

    body = head(r, 'Real Marco – realitní kancelář na úrovni | Brno', 'Prodej, pronájem a správa nemovitostí v Brně a okolí. Aktuální nabídka bytů, domů a pozemků, makléři s přímým kontaktem a odhad ceny zdarma.', 'home')
    body += nav(r)
    body += f'''<main id="obsah">
<section class="hero">
  <div class="wrap hero-grid">
    <div class="hero-txt">
      <p class="eyebrow">Realitní kancelář · {OFFICE['addr'].split(',')[0]}, Brno</p>
      <h1 class="h1">{h1}<br><span class="lvl"><span class="w"><span style="--i:2"><em>na&nbsp;úrovni</em></span></span><i class="lvl-bar" aria-hidden="true"></i></span></h1>
      <p class="hero-sub">{nb("Prodáme, pronajmeme i najdeme. Byty, domy a pozemky v Brně a okolí – s čistou, precizní prací a fair play od prvního telefonátu po předání klíčů.")}</p>
      <form class="qs" action="nabidka/" method="get" role="search" aria-label="Rychlé hledání">
        <div class="qs-seg" role="radiogroup" aria-label="Typ nabídky">
          <label><input type="radio" name="typ" value="prodej" checked><span>Koupit</span></label>
          <label><input type="radio" name="typ" value="pronajem"><span>Pronajmout</span></label>
        </div>
        <label class="qs-sel"><span class="sr">Kategorie</span><select name="kat"><option value="">Všechny nemovitosti</option>{cat_opts}</select></label>
        <button class="btn btn-k" type="submit">Hledat {ICON['arrow']}</button>
      </form>
      <a class="hero-all ul" href="nabidka/">{n} nemovitostí právě v nabídce</a>
    </div>
    <div class="hero-vis">
      <figure class="hero-main"><img src="assets/img/site/hero-sava.webp" alt="Oválné okno ve vile Sáva v Luhačovicích" fetchpriority="high" width="842" height="1080"></figure>
      <a class="hero-card" href="nemovitost/{hero_x['slug']}/">
        <img src="{hero_x['imgs'][0]['s']}" alt="" width="760" height="507">
        <span class="hero-card-t"><small>TOP nabídka · Luhačovice</small>Vila Sáva od Bohuslava Fuchse<b>{price_html(hero_x)}</b></span>
        <span class="hero-card-a">{ICON['arrow']}</span>
      </a>
    </div>
  </div>
  <a class="scroll-hint" href="#nabidka" aria-label="Posunout na nabídku"><span>Nabídka</span><i></i></a>
</section>

<div class="marquee" aria-hidden="true"><div class="mq">
  {"".join(f'<span>{w}</span><b></b>' for w in ["Prodej", "Pronájem", "Výkup", "Odhad ceny zdarma", "Správa bytových domů", "Hypoteční poradenství", "Development", "Brno a okolí"] * 2)}
</div></div>

<section class="sec sec-alt" id="nabidka">
  <div class="wrap">
    <div class="sec-head">
      <div>
        <p class="eyebrow rv">Nejnovější v nabídce</p>
        <h2 class="h2 rv">Domy, byty a pozemky, <em>které právě hledají nového majitele</em></h2>
      </div>
      <a class="btn btn-o rv" href="nabidka/">Celá nabídka ({n}) {ICON['arrow']}</a>
    </div>
    <div class="feat">
      {card(newest[0], r, big=True)}
      {"".join(card(x, r) for x in newest[1:])}
    </div>
  </div>
</section>

<section class="stats" aria-label="Real Marco v číslech">
  <div class="wrap">
    <p class="eyebrow eyebrow-d rv">Real Marco v číslech, které jsou pravda</p>
    <div class="stats-g">
      <div class="st rv"><b class="st-n" data-count="{n}">{n}</b><span>nemovitostí právě v&nbsp;nabídce</span></div>
      <div class="st rv" style="--d:90ms"><b class="st-n" data-count="4">4</b><span>makléři, jeden tým a&nbsp;jedna kancelář na Hlinkách</span></div>
      <div class="st rv" style="--d:180ms"><b class="st-n" data-count="15">15</b><span>let v&nbsp;oboru – tolik zkušeností má zakladatel Marek Karvaj</span></div>
      <div class="st rv" style="--d:270ms"><b class="st-n">0&nbsp;Kč</b><span>stojí odhad ceny vaší nemovitosti</span></div>
    </div>
  </div>
</section>

<section class="sec" id="sluzby">
  <div class="wrap">
    <div class="sec-head sec-head-split">
      <div>
        <p class="eyebrow rv">Co pro vás uděláme</p>
        <h2 class="h2 rv">Specialisté na <em>prodej a&nbsp;pronájem</em></h2>
      </div>
      <p class="lead rv">{nb("Od odhadu ceny přes fotografie, smlouvy a právní servis až po předání klíčů. Jedna kancelář, jeden makléř, který vás zná jménem.")}</p>
    </div>
    <div class="srv-list">
      {srv}
    </div>
    <div class="srv-prev" aria-hidden="true"><img alt=""></div>
  </div>
</section>

<section class="dev" id="development">
  <div class="dev-bg"><img src="assets/img/n/18454/03-l.webp" alt="Letecký pohled na lokalitu Vlčí máky v Syrovicích" loading="lazy" width="1800" height="1200"></div>
  <div class="wrap dev-in">
    <p class="eyebrow eyebrow-d rv">Development · Syrovice, lokalita Vlčí máky</p>
    <h2 class="h2 dev-h rv">Domy i&nbsp;pozemky <em>na&nbsp;jihu od&nbsp;Brna</em></h2>
    <p class="dev-p rv">{nb("Developerský projekt společnosti STAREX v obci Syrovice. Stavební pozemky se sítěmi na hranici a tři typové rodinné domy – vždy včetně parcely od 200 m².")}</p>
    <div class="dev-types">
      <div class="dt rv"><b>RD ECO 29</b><span>3+kk+1G až 5+kk+1G</span><span>106,6 / 134,1 až 159,7 m²</span></div>
      <div class="dt rv" style="--d:90ms"><b>RD ECO 30</b><span>3+kk+1G až 6+kk</span><span>100 m² nebo 126 až 154 m²</span></div>
      <div class="dt rv" style="--d:180ms"><b>RD ECO 32</b><span>4+kk až 5+kk</span><span>110 m² + garáž 37 m²</span></div>
    </div>
    <div class="dev-cta rv">
      <a class="btn btn-y" href="https://domysyrovice.realmarco.cz" target="_blank" rel="noopener">Nabídka domů {ICON['arrow']}</a>
      <a class="btn btn-ol" href="https://pozemkysyrovice.realmarco.cz" target="_blank" rel="noopener">Nabídka pozemků</a>
    </div>
  </div>
</section>

<section class="sec about" id="o-nas">
  <div class="wrap about-g">
    <figure class="about-ph clip"><img src="assets/img/site/kancelar-tym.webp" alt="Makléři Real Marco při schůzce v kanceláři na Hlinkách" loading="lazy" width="2000" height="1333"></figure>
    <div class="about-t">
      <p class="eyebrow rv">Kdo jsme</p>
      <h2 class="h2 rv">Naší vizí je čistá, precizní práce <em>a&nbsp;fair play</em></h2>
      <p class="rv">{nb("Jsme sdružení realitních makléřů, manažerů, ekonomů, správců nemovitostí a milovníků architektury, kteří se během společné profesní cesty stali přáteli. Silnou stránku má každý z nás jinou – a každý ji přidává do společného.")}</p>
      <ul class="pill rv">
        <li><b>Založeno na důvěře</b>{nb("Klientům přinášíme trvalou, důvěrnou a celoživotní péči. Dlouhodobá spolupráce je pro nás zásadní.")}</li>
        <li><b>Vzájemně se doplňujeme</b>{nb("Široký záběr a nahraditelnost – když jeden z nás nemůže, převezme to druhý.")}</li>
        <li><b>Poradenství a investice</b>{nb("Sdružujeme investory do nemovitostí a nové příležitosti sdílíme s klienty napřímo.")}</li>
      </ul>
    </div>
  </div>
  <div class="wrap" id="makleri">
    <div class="sec-head team-head">
      <div>
        <p class="eyebrow rv">Naši makléři</p>
        <h2 class="h2 rv">Voláte přímo <em>svému makléři</em></h2>
      </div>
      <p class="lead rv">{nb("Žádná ústředna, žádná skrytá čísla. U každé nemovitosti najdete telefon i e-mail makléře, který ji zná nejlépe.")}</p>
    </div>
    <div class="team">
      {team}
    </div>
    <p class="join rv">Chcete se stát makléřem? <a class="ul" href="#kontakt">Přidejte se k&nbsp;našemu týmu</a></p>
  </div>
</section>

<section class="refs" aria-label="Reference">
  <div class="wrap">
    <p class="eyebrow eyebrow-d rv">Co o nás říkají klienti</p>
    <figure class="rev-big rv"><blockquote>„{nb(rev_main[0])}“</blockquote><figcaption><strong>{rev_main[1]}</strong><span>{rev_main[2]}</span></figcaption></figure>
    <div class="rev-g">{revs}</div>
  </div>
  <div class="real" aria-label="Nedávno realizované zakázky">
    <p class="wrap real-h rv">Nedávno prodáno a pronajato</p>
    <div class="real-mq"><div class="real-tr">{real}{real.replace('<figure class="real-i">', '<figure class="real-i" aria-hidden="true">')}</div></div>
  </div>
</section>

<section class="contact" id="kontakt">
  <div class="wrap contact-g">
    <div class="contact-t">
      <p class="eyebrow eyebrow-k rv">Zastavte se</p>
      <h2 class="h-cafe rv">Stavte se <em>na&nbsp;kávu.</em></h2>
      <p class="rv">{nb("Rádi vám pomůžeme s prodejem, koupí nebo pronájmem. Navštivte nás na Hlinkách, zavolejte, nebo nám napište – ozveme se nejpozději druhý den.")}</p>
      <dl class="contact-dl rv">
        <div><dt>Kancelář</dt><dd>{OFFICE['addr']}</dd></div>
        <div><dt>Telefon</dt><dd><a class="ul" href="{tel(OFFICE['tel'])}">{OFFICE['tel']}</a></dd></div>
        <div><dt>E-mail</dt><dd><a class="ul" href="mailto:{OFFICE['mail']}">{OFFICE['mail']}</a></dd></div>
      </dl>
    </div>
    <form class="form rv" data-form>
      <p class="form-h">Napište nám</p>
      <div class="form-seg" role="radiogroup" aria-label="Téma">
        <label><input type="radio" name="tema" value="prodej" checked><span>Chci prodat</span></label>
        <label><input type="radio" name="tema" value="pronajem"><span>Chci pronajmout</span></label>
        <label><input type="radio" name="tema" value="odhad"><span>Odhad zdarma</span></label>
        <label><input type="radio" name="tema" value="jine"><span>Něco jiného</span></label>
      </div>
      <label class="fld"><span>Jméno a příjmení</span><input name="jmeno" required autocomplete="name"></label>
      <div class="fld-2">
        <label class="fld"><span>Telefon</span><input name="tel" type="tel" autocomplete="tel"></label>
        <label class="fld"><span>E-mail</span><input name="email" type="email" required autocomplete="email"></label>
      </div>
      <label class="fld"><span>Zpráva</span><textarea name="zprava" rows="3" placeholder="Např. byt 2+kk v Brně, chtěl bych znát jeho cenu"></textarea></label>
      <button class="btn btn-k btn-wide" type="submit">Odeslat zprávu {ICON['arrow']}</button>
      <p class="form-ok" hidden>Děkujeme! Ozveme se vám nejpozději druhý den.</p>
      <p class="form-note">Návrh webu – formulář zatím nic neodesílá.</p>
    </form>
  </div>
</section>
</main>
'''
    body += footer(r) + '</body>\n</html>\n'
    open(os.path.join(ROOT, 'index.html'), 'w').write(body)


# ---------------------------------------------------------------- nabídka
def build_offer():
    r = '../'
    n = len(LIST)
    counts = {s: sum(1 for x in LIST if CAT[x['cat']][0] == s) for s, _ in CAT_ORDER}
    kinds = {'prodej': sum(1 for x in LIST if x['kind'] == 'Prodej'), 'pronajem': sum(1 for x in LIST if x['kind'] == 'Pronájem')}
    chips = ''.join(f'<button type="button" class="chip" data-f="kat" data-v="{s}" aria-pressed="false">{l}<sup>{counts[s]}</sup></button>' for s, l in CAT_ORDER if counts[s])
    regs = ''.join(f'<option value="{k}">{v}</option>' for k, v in REG_LABEL.items())
    body = head(r, 'Nabídka nemovitostí | Real Marco', f'{n} aktuálních nabídek realitní kanceláře Real Marco – byty, domy, pozemky a komerční prostory v Brně a okolí.', 'offer')
    body += nav(r, 'nabidka')
    body += f'''<main id="obsah">
<section class="offer-head">
  <div class="wrap">
    <p class="crumbs"><a class="ul" href="../">Úvod</a><span>/</span>Nabídka</p>
    <h1 class="h1 h1-page">Nabídka <em>nemovitostí</em></h1>
    <p class="lead">{nb(f"{n} aktuálních nabídek. Filtrujte podle typu, lokality, ceny i plochy – výsledky se mění okamžitě a odkaz si můžete poslat dál.")}</p>
  </div>
</section>
<section class="filters" id="filters" aria-label="Filtry nabídky">
  <div class="wrap">
    <button class="f-toggle" type="button" aria-expanded="false" aria-controls="fpanel">{ICON['filter']} Filtrovat <span class="f-badge" hidden></span></button>
    <div class="fpanel" id="fpanel">
      <div class="f-row">
        <div class="seg" role="group" aria-label="Typ">
          <button type="button" data-f="typ" data-v="" aria-pressed="true">Vše<sup>{n}</sup></button>
          <button type="button" data-f="typ" data-v="prodej" aria-pressed="false">Koupě<sup>{kinds['prodej']}</sup></button>
          <button type="button" data-f="typ" data-v="pronajem" aria-pressed="false">Pronájem<sup>{kinds['pronajem']}</sup></button>
        </div>
        <div class="chips" role="group" aria-label="Kategorie">{chips}</div>
      </div>
      <div class="f-row f-row-2">
        <label class="sel"><span>Lokalita</span><select data-f="lok"><option value="">Kdekoliv</option>{regs}</select></label>
        <label class="sel"><span>Cena do</span><select data-f="cena"><option value="">Neomezeně</option></select></label>
        <label class="sel"><span>Plocha od</span><select data-f="plocha"><option value="">Jakákoliv</option><option value="40">40 m²</option><option value="80">80 m²</option><option value="120">120 m²</option><option value="200">200 m²</option><option value="500">500 m²</option></select></label>
        <label class="sel"><span>Řazení</span><select data-f="razeni"><option value="">Nejnovější</option><option value="cena-asc">Od nejlevnější</option><option value="cena-desc">Od nejdražší</option><option value="plocha-desc">Největší plocha</option></select></label>
        <button type="button" class="reset ul" data-reset hidden>Zrušit filtry</button>
      </div>
    </div>
  </div>
</section>
<section class="results">
  <div class="wrap">
    <p class="res-count" aria-live="polite"><b data-count-out>{n}</b> z {n} nemovitostí</p>
    <div class="grid" id="grid">
      {"".join(card(x, r) for x in LIST)}
    </div>
    <div class="empty" hidden>
      <p class="h3">Tomu teď nic neodpovídá.</p>
      <p>{nb("Napište nám, co hledáte – často máme nemovitosti dřív, než se dostanou na portály.")}</p>
      <a class="btn btn-k" href="../#kontakt">Popsat, co hledám {ICON['arrow']}</a>
    </div>
    <aside class="watch rv">
      <div><p class="h3">Nenašli jste to pravé?</p><p>{nb("Řekněte nám, co hledáte, a ozveme se, jakmile se objeví. Ať vám neuteče žádná nabídka.")}</p></div>
      <a class="btn btn-y" href="../#kontakt">Hlídat nabídku {ICON['arrow']}</a>
    </aside>
  </div>
</section>
</main>
'''
    body += footer(r) + '</body>\n</html>\n'
    os.makedirs(os.path.join(ROOT, 'nabidka'), exist_ok=True)
    open(os.path.join(ROOT, 'nabidka', 'index.html'), 'w').write(body)


# ---------------------------------------------------------------- detail
def render_desc(txt):
    txt = re.sub(r'\bm\n2\n', 'm² ', txt)
    lines = [l.strip() for l in txt.split('\n')]
    out, ul, small = [], [], []

    def flush():
        if ul:
            out.append('<ul>' + ''.join(f'<li>{nb(E(i))}</li>' for i in ul) + '</ul>')
            ul.clear()
    for i, l in enumerate(lines):
        if not l or re.fullmatch(r'[_\-–=]{4,}', l):
            flush(); continue
        if re.match(r'^[•·▪\-–]\s*', l) and len(l) > 2:
            ul.append(re.sub(r'^[•·▪\-–]\s*', '', l)); continue
        flush()
        if '§1731' in l or l.startswith('Uvedené výměry jsou orientační') or l.startswith('Veškeré zveřejněné údaje'):
            small.append(l); continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ''
        if len(l) < 64 and not re.search(r'[.!…,;]$', l) and nxt and i > 0:
            out.append(f'<h3>{nb(E(l.rstrip(":")))}</h3>'); continue
        if i == 0 and len(l) < 120 and not l.endswith('.'):
            out.append(f'<p class="d-lead">{nb(E(l))}</p>'); continue
        out.append(f'<p>{nb(E(l))}</p>')
    flush()
    if small:
        out.append('<p class="d-small">' + nb(E(' '.join(small))) + '</p>')
    return '\n'.join(out)


def build_detail(x, i):
    r = '../../'
    b = BRK.get(x['broker'], BROKERS[0])
    imgs = x['imgs']
    photos = [im for im in imgs if not im['plan']] + [im for im in imgs if im['plan']]
    gal = ''
    for k, im in enumerate(photos[:5]):
        more = f'<span class="gal-more">{ICON["grid"]} Všech {len(photos)} fotek</span>' if k == min(4, len(photos) - 1) and len(photos) > 1 else ''
        src = im['l'] if k == 0 else im['s']
        ld = 'fetchpriority="high"' if k == 0 else 'loading="lazy"'
        gal += f'<button class="gal-i gal-{k}" type="button" data-lb="{k}" aria-label="Zobrazit fotku {k + 1} z {len(photos)}"><img src="{r}{src}" alt="{E(x["title"])} – fotka {k + 1}" {ld} decoding="async" width="{im["w"]}" height="{im["h"]}">{more}</button>'
    lb_data = json.dumps([r + im['l'] for im in photos])
    slug, k1 = CAT[x['cat']]
    typ = TYPE_LABEL.get(x['id'], k1)
    facts = []
    for k, v in x['params']:
        if k.startswith('Číslo'):
            continue
        facts.append((k.replace(' m²', ''), v + (' m²' if 'm²' in k and 'Cena' not in k else '')))
    if x['disp']:
        facts.insert(0, ('Dispozice', x['disp']))
    facts_html = ''.join(f'<div><dt>{E(k)}</dt><dd>{v}</dd></div>' for k, v in facts[:6])
    zak = next((v for k, v in x['params'] if k.startswith('Číslo')), '')
    feats = ''.join(f'<li>{E(f)}</li>' for f in x['feats'])
    amen = ''.join(f'<li>{E(f)}</li>' for f in x['amen'])
    info = ''
    if feats:
        info += f'<div class="d-block"><h2 class="d-h">Informace o nemovitosti</h2><ul class="tags">{feats}</ul></div>'
    if amen:
        info += f'<div class="d-block"><h2 class="d-h">Občanská vybavenost</h2><ul class="tags tags-l">{amen}</ul></div>'
    q = quote(x['addr'])
    similar = [y for y in LIST if y['id'] != x['id'] and (y['cat'] == x['cat'] or REG_OF.get(y['id']) == REG_OF.get(x['id']))][:3]
    if len(similar) < 3:
        similar += [y for y in LIST if y['id'] != x['id'] and y not in similar][:3 - len(similar)]
    calc = ''
    if x['price'] and not x['monthly']:
        calc = f'''<div class="calc" data-calc data-price="{x['price']}">
      <p class="calc-h">Orientační hypotéka</p>
      <label class="rng"><span>Vlastní zdroje <b data-o="own">20 %</b></span><input type="range" min="10" max="60" step="5" value="20" data-i="own"></label>
      <label class="rng"><span>Doba splácení <b data-o="yrs">30 let</b></span><input type="range" min="5" max="30" step="1" value="30" data-i="yrs"></label>
      <label class="rng"><span>Úroková sazba <b data-o="rate">5,0 %</b></span><input type="range" min="2" max="8" step="0.1" value="5" data-i="rate"></label>
      <p class="calc-r">Měsíční splátka <b data-o="pay">–</b></p>
      <p class="calc-n">Jen orientační výpočet. S hypotékou vám rádi poradíme přímo v kanceláři.</p>
    </div>'''
    title = f'{x["title"]} | Real Marco'
    desc0 = re.sub(r'\s+', ' ', x['desc'])[:150]
    body = head(r, E(title), desc0, 'detail')
    body += nav(r, 'nabidka')
    body += f'''<main id="obsah">
<div class="wrap">
  <p class="crumbs"><a class="ul" href="{r}">Úvod</a><span>/</span><a class="ul" href="{r}nabidka/">Nabídka</a><span>/</span><a class="ul" href="{r}nabidka/?kat={slug}">{dict(CAT_ORDER)[slug]}</a></p>
  <div class="d-top">
    <div>
      <p class="d-kicker"><span class="badge badge-k">{x['kind']}</span>{"".join(f'<span class="badge badge-y">{bb}</span>' for bb in x['badges'] if bb != 'Doporučujeme')}<span>{typ}</span></p>
      <h1 class="d-title">{nb(E(x['title']))}</h1>
      <p class="d-addr">{ICON['pin']}{E(x['addr'])}</p>
    </div>
    <div class="d-price"><span>{"Nájem" if x['monthly'] else "Cena"}</span><b>{price_html(x)}</b>{f'<small>{E(x["note"])}</small>' if x['note'] else ''}</div>
  </div>
  <div class="gal gal-n{min(5, len(photos))}" data-lbsrc='{lb_data}'>{gal}</div>
</div>
<div class="wrap d-grid">
  <article class="d-main">
    <dl class="d-facts">{facts_html}</dl>
    <div class="d-desc">{render_desc(x['desc'])}</div>
    {info}
    <div class="d-block">
      <h2 class="d-h">Lokalita</h2>
      <div class="map" data-map="https://maps.google.com/maps?q={q}&amp;z=13&amp;output=embed">
        <p>{ICON['pin']} {E(x['addr'])}</p>
        <button class="btn btn-o btn-sm" type="button">Zobrazit mapu</button>
      </div>
    </div>
    {f'<p class="d-id">Číslo zakázky {E(zak)} · ID {x["id"]}</p>' if zak else ''}
  </article>
  <aside class="d-side">
    <div class="agent-card">
      <div class="ac-top">
        <img src="{r}assets/img/site/{b['img']}.webp" alt="{b['first']} {b['last']}" width="700" height="700" loading="lazy">
        <div><p class="ac-l">Váš makléř</p><p class="ac-n">{b['first']} {b['last']}</p><p class="ac-r">{b['role']}</p></div>
      </div>
      <a class="btn btn-y btn-wide" href="{tel(b['tel'])}">{ICON['phone']} {b['tel']}</a>
      <a class="btn btn-o btn-wide" href="mailto:{b['mail']}?subject={quote('Dotaz: ' + x['title'])}">{ICON['mail']} {b['mail']}</a>
      <form class="mini-form" data-form>
        <p class="mf-h">Domluvit prohlídku</p>
        <label class="fld"><span>Jméno</span><input name="jmeno" required autocomplete="name"></label>
        <label class="fld"><span>Telefon nebo e-mail</span><input name="kontakt" required></label>
        <button class="btn btn-k btn-wide" type="submit">Chci na prohlídku {ICON['arrow']}</button>
        <p class="form-ok" hidden>Děkujeme, {b['first']} se vám ozve.</p>
      </form>
    </div>
    {calc}
  </aside>
</div>
<section class="sec sec-alt sim">
  <div class="wrap">
    <div class="sec-head"><h2 class="h2">Mohlo by vás <em>zajímat</em></h2><a class="btn btn-o" href="{r}nabidka/">Celá nabídka {ICON['arrow']}</a></div>
    <div class="grid grid-3">{"".join(card(y, r) for y in similar)}</div>
  </div>
</section>
</main>
<div class="d-bar">
  <div><small>{"Nájem" if x['monthly'] else "Cena"}</small><b>{price_html(x)}</b></div>
  <a class="btn btn-y btn-sm" href="{tel(b['tel'])}">{ICON['phone']} Zavolat</a>
</div>
<div class="lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="Fotogalerie">
  <button class="lb-x" type="button" aria-label="Zavřít">{ICON['close']}</button>
  <button class="lb-p" type="button" aria-label="Předchozí">{ICON['left']}</button>
  <figure class="lb-f"><img alt=""></figure>
  <button class="lb-n" type="button" aria-label="Další">{ICON['right']}</button>
  <p class="lb-c"></p>
</div>
'''
    body += footer(r) + '</body>\n</html>\n'
    d = os.path.join(ROOT, 'nemovitost', x['slug'])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w').write(body)


def build_404():
    r = '/realmarco/'
    body = head(r, 'Stránka nenalezena | Real Marco', 'Stránka nenalezena', 'nf')
    body += nav(r)
    body += f'''<main id="obsah" class="nf-main"><div class="wrap"><p class="eyebrow">Chyba 404</p><h1 class="h1 h1-page">Tady <em>nic není.</em></h1><p class="lead">Nemovitost už možná našla nového majitele.</p><p><a class="btn btn-k" href="{r}nabidka/">Prohlédnout nabídku {ICON['arrow']}</a></p></div></main>'''
    body += footer(r) + '</body>\n</html>\n'
    open(os.path.join(ROOT, '404.html'), 'w').write(body)


if __name__ == '__main__':
    shutil.rmtree(os.path.join(ROOT, 'nemovitost'), ignore_errors=True)
    build_home()
    build_offer()
    for i, x in enumerate(LIST):
        build_detail(x, i)
    build_404()
    print('hotovo:', len(LIST), 'detailů, css', V_CSS, 'js', V_JS)
