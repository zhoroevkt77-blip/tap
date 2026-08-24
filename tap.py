#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAP! — жарыя сайты. БИР ФАЙЛ, кошумча китепкана КЕРЕК ЭМЕС.
Termux'та иштетүү:  python tap.py
Браузерден ачуу:    http://localhost:8000
"""

import sqlite3, html, os, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "tap.db")
MEDIA = os.path.join(BASE, "media")
PORT = 8000

CATS = {
    "transport": ("Транспорт", "🚗"),
    "realty":    ("Кыймылсыз мүлк", "🏠"),
    "personal":  ("Жеке буюмдар", "👕"),
    "service":   ("Кызматтар", "🔧"),
    "shop":      ("Магазиндер", "🛍"),
    "business":  ("Бизнес", "🤝"),
}

# ---- Латын / кириллица издөө ----
# Кыргызстанда "батир" деп да, "batir" деп да жазышат.
# Ошондуктан ар бир жарыянын латынча жазылышын да сактайбыз,
# издөөдө болсо суроону эки формада тең текшеребиз.

_TR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "ң": "ng", "о": "o", "ө": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "у": "u", "ү": "u", "ф": "f", "х": "h", "ц": "c", "ч": "ch",
    "ш": "sh", "щ": "sh", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
    "я": "ya",
}

# Латынча жазуунун ар кандай варианттарын бир формага келтирүү:
# jantyk / zhantyk, han / khan, cai / tsai — баары бир болуп калсын.

def translit(s):
    """Кириллицаны латынга которот. Латын тамгалар тийбейт."""
    return "".join(_TR.get(ch, ch) for ch in (s or "").lower())


def fold(s):
    """Латынча жазуунун варианттарын бир формага келтирет."""
    s = (s or "").lower()
    # ch/sh убактылуу белгиге — алардын ичиндеги тамгалар өзгөрбөш үчүн
    s = s.replace("ch", "\x01").replace("sh", "\x02")
    for a, b in (("zh", "j"), ("kh", "h"), ("ts", "k"), ("c", "k"),
                 ("yo", "o"), ("yu", "u"), ("ya", "a"), ("ye", "e"),
                 ("q", "k"), ("w", "v"), ("x", "ks"), ("y", "i")):
        s = s.replace(a, b)
    s = s.replace("\x01", "ch").replace("\x02", "sh")
    # Кайталанган тамгаларды бирге түшүрөбүз: donggolok -> dongolok
    out = []
    for ch in s:
        if not out or out[-1] != ch:
            out.append(ch)
    return "".join(out)


def norm(s):
    """Издөө үчүн бир формага келтирилген текст."""
    return fold(translit(s))

# Кыргызча-орусча синонимдер. Киши "квартира" деп издейт,
# жарыяда "батир" деп жазылган болушу мүмкүн — экөө тең табылсын.
SYNS = [
    ["батир", "квартира"],
    ["там", "үй", "дом"],
    ["унаа", "машина", "авто", "автомобиль"],
    ["телефон", "смартфон"],
    ["дөңгөлөк", "резина", "шина", "колесо"],
    ["эмерек", "мебель"],
    ["кийим", "одежда"],
    ["жер", "участок"],
    ["иш", "жумуш", "работа", "вакансия"],
    ["ижара", "аренда", "арендага"],
    ["сатылат", "продается", "продам"],
    ["компьютер", "ноутбук", "комп"],
    ["курулуш", "стройка", "ремонт", "оңдоо"],
]


def expand(text):
    """Тексттеги сөздөрдүн синонимдерин кошуп берет."""
    low = (text or "").lower()
    extra = []
    for group in SYNS:
        if any(w in low for w in group):
            extra += group
    return " ".join(extra)


# Категориянын ичиндеги түрлөр.
# Бул издөө үчүн эң маанилүү: эч ким жарыясына "телефон" деп жазбайт,
# "Redmi Note 13" деп жазат. Түр тандалганда ошол сөз жарыяга байланат.
SUBS = {
    "transport": [("car", "Унаа"), ("parts", "Унаа тетиктери"), ("tire", "Дөңгөлөк"),
                  ("moto", "Мотоцикл, велосипед"), ("truck", "Жүк техникасы")],
    "realty":    [("flat", "Батир"), ("house", "Там, үй"), ("land", "Жер участок"),
                  ("commerce", "Коммерциялык жай"), ("rent", "Ижарага")],
    "personal":  [("phone", "Телефон"), ("comp", "Компьютер, ноутбук"),
                  ("cloth", "Кийим-кече"), ("furn", "Эмерек"),
                  ("tech", "Тиричилик техникасы"), ("kids", "Балдар буюмдары"),
                  ("other", "Башка")],
    "service":   [("build", "Оңдоо, курулуш"), ("transport", "Ташуу кызматы"),
                  ("repair", "Техника оңдоо"), ("beauty", "Сулуулук, саламаттык"),
                  ("teach", "Окутуу"), ("other", "Башка")],
    "shop":      [("food", "Азык-түлүк"), ("cloth", "Кийим дүкөнү"),
                  ("tech", "Техника дүкөнү"), ("build", "Курулуш материалдары"),
                  ("other", "Башка")],
    "business":  [("ready", "Даяр бизнес"), ("equip", "Жабдуу"),
                  ("partner", "Өнөктөштүк"), ("other", "Башка")],
}


def sub_title(cat, code):
    for c, n in SUBS.get(cat, []):
        if c == code:
            return n
    return ""

REGIONS = ["Жалал-Абад облусу", "Ош облусу", "Баткен облусу", "Чүй облусу",
           "Ысык-Көл облусу", "Нарын облусу", "Талас облусу", "Бишкек", "Ош шаары"]

DEMO = [
    ("transport", "Фара Chevrolet Cruze 2012", "5 000 сом", "Жалал-Абад облусу",
     "Оригинал фара, сынган жери жок. Оң жагы.", "+996772445566"),
    ("service", "Шаарлар аралык жана жергиликтүү такси", "$6 000", "Жалал-Абад облусу",
     "Даяр такси программасы. 4 тиркеме комплектте, 24/7 техподдержка.", "+996555778899"),
    ("personal", "Чехол Redmi Note 15 Pro", "", "Жалал-Абад облусу",
     "Nillkin, ачылган эмес, кутусунда.", "+996700112233"),
    ("personal", "Redmi 15C, дээрлик жаңы", "", "Жалал-Абад облусу",
     "8GB RAM, 256GB ROM, 6000mAh, 33W заряд, 6.9 дюйм, 120Hz.", "+996555778899"),
    ("realty", "2 бөлмөлүү батир, борбордо", "45 000 сом/ай", "Жалал-Абад облусу",
     "Ремонту жаңы, эмеректери менен. Мектеп, базар жакын.", "+996772445566"),
    ("transport", "Toyota Camry 2015", "$14 500", "Ош облусу",
     "Пробег 180 000 км, автомат, газ-бензин.", "+996700112233"),
    ("service", "Кир жуучу машина оңдоо", "Келишимдүү", "Жалал-Абад облусу",
     "Үйгө барып оңдойм. Бардык маркалар. Кепилдик берилет.", "+996772445566"),
    ("shop", "Балдар кийимдери дүң баада", "", "Ош шаары",
     "Түркиядан. Дүң алгандарга арзандатуу.", "+996555778899"),
    ("business", "Даяр кафе сатылат", "$25 000", "Жалал-Абад облусу",
     "Борбордо, 40 орундуу. Бардык жабдуулары менен, иштеп турат.", "+996700112233"),
    ("realty", "Там сатылат, 8 сотых", "$32 000", "Жалал-Абад облусу",
     "4 бөлмө, гараж, бак-дарак. Документтери таза.", "+996772445566"),
]


# ---------------- База ----------------

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL, region TEXT, title TEXT NOT NULL,
            description TEXT, price TEXT, contact TEXT,
            views INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1,
            photo TEXT, tg_id TEXT, tg_name TEXT, stext TEXT, subcat TEXT,
            created_at TEXT DEFAULT (datetime('now')))""")
        have = {r[1] for r in c.execute("PRAGMA table_info(listings)")}
        for col in ("photo", "tg_id", "tg_name", "stext", "subcat"):
            if col not in have:
                c.execute(f"ALTER TABLE listings ADD COLUMN {col} TEXT")
        for r in c.execute("SELECT id,title,description FROM listings "
                           "WHERE stext IS NULL").fetchall():
            raw = f"{r['title'] or ''} {r['description'] or ''}".lower()
            raw = raw + " " + expand(raw)
            c.execute("UPDATE listings SET stext=? WHERE id=?", (raw + " " + norm(raw), r["id"]))
        os.makedirs(MEDIA, exist_ok=True)
        if c.execute("SELECT COUNT(*) n FROM listings").fetchone()["n"] == 0:
            c.executemany(
                """INSERT INTO listings (category,title,price,region,description,contact)
                   VALUES (?,?,?,?,?,?)""", DEMO)


def search(q=None, cat=None, reg=None, sub=None):
    sql = "SELECT * FROM listings WHERE is_active=1"
    p = []
    if cat:
        sql += " AND category=?"; p.append(cat)
    if sub:
        sql += " AND subcat=?"; p.append(sub)
    if reg:
        sql += " AND region=?"; p.append(reg)
    if q:
        sql += " AND (stext LIKE ? OR stext LIKE ?)"
        p += [f"%{q.lower()}%", f"%{norm(q)}%"]
    sql += " ORDER BY id DESC"
    with conn() as c:
        return [dict(r) for r in c.execute(sql, p).fetchall()]


def one(i):
    with conn() as c:
        r = c.execute("SELECT * FROM listings WHERE id=? AND is_active=1", (i,)).fetchone()
        if r:
            c.execute("UPDATE listings SET views=views+1 WHERE id=?", (i,))
        return dict(r) if r else None


def counts(reg=None):
    sql = "SELECT category, COUNT(*) n FROM listings WHERE is_active=1"
    p = []
    if reg:
        sql += " AND region=?"; p.append(reg)
    sql += " GROUP BY category"
    with conn() as c:
        return {r["category"]: r["n"] for r in c.execute(sql, p)}


def sub_counts(cat, reg=None):
    """Тандалган категориядагы ар бир түрдө канча жарыя бар."""
    sql = ("SELECT subcat, COUNT(*) n FROM listings WHERE is_active=1 AND category=?")
    p = [cat]
    if reg:
        sql += " AND region=?"; p.append(reg)
    sql += " GROUP BY subcat"
    with conn() as c:
        return {r["subcat"]: r["n"] for r in c.execute(sql, p) if r["subcat"]}


def used_regions():
    """Базада чындап колдонулган аймактар гана."""
    with conn() as c:
        return [r["region"] for r in c.execute(
            "SELECT region, COUNT(*) n FROM listings WHERE is_active=1 "
            "AND region IS NOT NULL AND region<>'' GROUP BY region ORDER BY n DESC")]


def ago(ts):
    """'2026-08-23 03:53' -> '2 саат мурун'"""
    from datetime import datetime, timezone
    try:
        t = datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return ts[:16]
    sec = (datetime.now(timezone.utc) - t).total_seconds()
    if sec < 60:
        return "азыр эле"
    if sec < 3600:
        return f"{int(sec // 60)} мүнөт мурун"
    if sec < 86400:
        return f"{int(sec // 3600)} саат мурун"
    d = int(sec // 86400)
    if d == 1:
        return "кечээ"
    if d < 30:
        return f"{d} күн мурун"
    if d < 365:
        return f"{d // 30} ай мурун"
    return f"{d // 365} жыл мурун"


# ---------------- Дизайн ----------------

CSS = """
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:#F2F3F5;color:#0F1419;
 font:15px/1.45 -apple-system,"Segoe UI",Roboto,system-ui,sans-serif;padding-bottom:66px}
a{color:inherit;text-decoration:none}
.wrap{max-width:1000px;margin:0 auto;padding:0 12px}

/* ---- Башкы тилке ---- */
.top{background:linear-gradient(180deg,#12A05C 0%,#0E8C50 100%);color:#fff;
 padding:8px 0 14px;position:sticky;top:0;z-index:20}
.tin{display:flex;align-items:center;gap:10px;padding:4px 0 12px}
.logo{font-weight:800;font-size:19px;letter-spacing:-.5px}
.pin{opacity:.95;font-size:13.5px;background:rgba(255,255,255,.16);
 padding:5px 11px;border-radius:14px}
.regbar{display:flex;gap:7px;overflow-x:auto;padding:10px 12px 2px;
 scrollbar-width:none;max-width:1000px;margin:0 auto}
.regbar::-webkit-scrollbar{display:none}
.rg{flex:none;background:#fff;border:1px solid #E3E7EB;border-radius:16px;
 padding:6px 13px;font-size:12.5px;color:#3C4650;white-space:nowrap}
.rg.on{background:#0F1419;color:#fff;border-color:#0F1419;font-weight:600}
.subbar{display:flex;gap:7px;overflow-x:auto;padding:8px 12px 2px;
 scrollbar-width:none;max-width:1000px;margin:0 auto}
.subbar::-webkit-scrollbar{display:none}
.sb2{flex:none;background:#E7F5EE;border:1px solid #C9E7D8;border-radius:15px;
 padding:6px 13px;font-size:12.5px;color:#0E7A45;white-space:nowrap}
.sb2.on{background:#12A05C;color:#fff;border-color:#12A05C;font-weight:600}
.sb2 em{font-style:normal;opacity:.7;font-size:11px}
.s{display:flex;align-items:center;background:#fff;border-radius:24px;
 padding:0 6px 0 16px;height:46px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.s input{flex:1;min-width:0;border:0;font-size:16px;background:transparent;padding:0}
.s input:focus{outline:none}
.s input::placeholder{color:#8B95A1}
.s button{border:0;background:#0F1419;color:#fff;height:34px;padding:0 16px;
 border-radius:18px;font-size:14px;font-weight:600}

/* ---- Категориялар ---- */
.cats{display:flex;gap:12px;overflow-x:auto;padding:14px 12px 6px;
 scrollbar-width:none;max-width:1000px;margin:0 auto}
.cats::-webkit-scrollbar{display:none}
.cat{flex:none;width:68px;text-align:center;font-size:11.5px;line-height:1.25;color:#3C4650}
.cat span.lb{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
 overflow:hidden;height:29px}
.cat .ic{width:54px;height:54px;border-radius:18px;background:#fff;display:flex;
 align-items:center;justify-content:center;font-size:24px;margin:0 auto 6px;
 box-shadow:0 1px 3px rgba(0,0,0,.06)}
.cat.on .ic{background:#0F1419;color:#fff}
.cat.on{color:#0F1419;font-weight:600}

/* ---- Жыйынтык ---- */
.rl{display:flex;align-items:center;gap:8px;padding:12px 0 10px}
.rn{font-size:17px;font-weight:700}
.rlb{font-size:14px;color:#6B7580}
.cl{margin-left:auto;font-size:13px;color:#12A05C;font-weight:600}

/* ---- Карточкалар ---- */
.g{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;padding-bottom:24px}
@media(min-width:620px){.g{grid-template-columns:repeat(3,1fr);gap:12px}}
@media(min-width:900px){.g{grid-template-columns:repeat(4,1fr)}}
.c{background:#fff;border-radius:16px;overflow:hidden;display:flex;flex-direction:column}
.ph{position:relative;aspect-ratio:1/1;background:#EDEFF2;
 display:flex;align-items:center;justify-content:center}
.ph i{width:36px;height:36px;border:2px solid #D3D8DE;border-radius:8px;
 transform:rotate(45deg);display:block}
.ph img{width:100%;height:100%;object-fit:cover;display:block}
.dph img{width:100%;height:100%;object-fit:contain;display:block;border-radius:16px}
.fav{position:absolute;top:8px;right:8px;width:32px;height:32px;border-radius:50%;
 background:rgba(255,255,255,.92);display:flex;align-items:center;justify-content:center;
 font-size:16px;color:#8B95A1}
.cb{padding:10px 11px 12px;display:flex;flex-direction:column;flex:1}
.p{font-size:18px;font-weight:800;letter-spacing:-.3px;margin-bottom:5px;color:#0F1419}
.pd{font-size:15px;font-weight:700;color:#12A05C}
.t{font-size:13.5px;line-height:1.35;margin:0 0 9px;font-weight:400;color:#3C4650;
 display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.m{margin-top:auto;display:flex;gap:8px;font-size:11.5px;color:#8B95A1;white-space:nowrap}
.m span:first-child{overflow:hidden;text-overflow:ellipsis}
.m span:last-child{margin-left:auto}

/* ---- Толук барак ---- */
.back{display:inline-block;padding:14px 0 8px;font-size:14px;color:#12A05C;font-weight:600}
.dph{background:#fff;border-radius:16px;aspect-ratio:4/3;max-height:230px;
 display:flex;align-items:center;justify-content:center;margin-bottom:12px}
.dph i{width:44px;height:44px;border:2px solid #D3D8DE;border-radius:10px;
 transform:rotate(45deg);display:block}
.dcard{background:#fff;border-radius:16px;padding:16px;margin-bottom:12px}
.eb{font-size:12px;color:#8B95A1;margin-bottom:8px}
h1{font-size:19px;line-height:1.3;margin:0 0 12px;font-weight:600}
.dp{font-size:30px;font-weight:800;letter-spacing:-.8px;margin-bottom:6px}
.dpd{font-size:22px;color:#12A05C}
.f{margin-top:14px;border-top:1px solid #EDEFF2}
.f div{display:flex;justify-content:space-between;gap:16px;padding:11px 0;
 border-bottom:1px solid #EDEFF2;font-size:14px}
.f b{color:#8B95A1;font-weight:400}
.d{font-size:14.5px;line-height:1.6;margin:0;white-space:pre-wrap;color:#3C4650}
.btn{display:block;text-align:center;background:#12A05C;color:#fff;padding:15px;
 border-radius:14px;font-weight:700;font-size:16px;margin-bottom:20px}

/* ---- Бош абал ---- */
.em{text-align:center;padding:56px 20px 70px;background:#fff;border-radius:16px;margin-top:8px}
.em i{width:44px;height:44px;border:2px solid #E3E7EB;border-radius:10px;
 transform:rotate(45deg);margin:0 auto 24px;display:block}
.em h2{font-size:17px;margin:0 0 8px;font-weight:600}
.em p{color:#8B95A1;font-size:14px;margin:0 0 20px}
.dk{display:inline-block;background:#0F1419;color:#fff;padding:12px 20px;
 border-radius:12px;font-size:14px;font-weight:600}

/* ---- Ылдыйкы навигация ---- */
.nav{position:fixed;left:0;right:0;bottom:0;background:#fff;display:flex;
 border-top:1px solid #E8EBEE;z-index:30}
.nav a{flex:1;text-align:center;padding:8px 0 9px;font-size:10.5px;color:#8B95A1}
.nav a b{display:block;font-size:20px;font-weight:400;line-height:1.25;margin-bottom:1px}
.nav a.on{color:#12A05C;font-weight:600}
"""

DEAL = {"келишимдүү", "келишим", "договорная", ""}


def esc(s):
    return html.escape(str(s or ""))


def price_bits(p):
    """(текст, келишимдүүбү) кайтарат."""
    p = (p or "").strip()
    return (p or "Келишимдүү", p.lower() in DEAL)


NAV = """<nav class="nav">
<a href="/" class="on"><b>&#8962;</b>Башкы бет</a>
<a href="/"><b>&#9825;</b>Тандалган</a>
<a href="/"><b>&#8853;</b>Жарыя берүү</a>
<a href="/"><b>&#9993;</b>Билдирүү</a>
<a href="/"><b>&#9786;</b>Кабинет</a>
</nav>"""


def page(body, title="TAP!"):
    return f"""<!DOCTYPE html><html lang="ky"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#12A05C">
<title>{esc(title)}</title><style>{CSS}</style></head><body>{body}{NAV}
</body></html>"""


def header(q="", cat=None, reg=None):
    return f"""<header class="top"><div class="wrap">
<div class="tin"><span class="logo">TAP!</span>
<span class="pin">&#128205; {esc(reg or 'Бүт Кыргызстан')}</span></div>
<form class="s" action="/">
{f'<input type="hidden" name="cat" value="{esc(cat)}">' if cat else ''}
{f'<input type="hidden" name="region" value="{esc(reg)}">' if reg else ''}
<input type="search" name="q" value="{esc(q)}" placeholder="Жарыя издөө">
<button>Изде</button></form></div></header>"""


def card(r):
    txt, deal = price_bits(r["price"])
    img = (f'<img src="/media/{esc(r["photo"])}" alt="" loading="lazy">'
           if r.get("photo") else '<i></i>')
    return f"""<a class="c" href="/e/{r['id']}">
<div class="ph">{img}<span class="fav">&#9825;</span></div>
<div class="cb"><div class="p{' pd' if deal else ''}">{esc(txt)}</div>
<h2 class="t">{esc(r['title'])}</h2>
<div class="m"><span>{esc(ago(r['created_at']))}</span><span>&#128065; {r['views']}</span></div>
</div></a>"""


def home(q, cat, reg=None, sub=None):
    rows = search(q, cat, reg, sub)
    cn = counts(reg)

    def link(**kw):
        """Учурдагы чыпкаларды сактап, бирөөнү гана өзгөрткөн шилтеме."""
        prm = {"q": q or None, "cat": cat, "region": reg, "sub": sub}
        prm.update(kw)
        prm = {k: v for k, v in prm.items() if v}
        return ("/?" + urllib.parse.urlencode(prm)) if prm else "/"

    cats = (f'<a href="{link(cat=None, sub=None)}" class="cat{"" if cat else " on"}">'
            f'<span class="ic">&#9635;</span><span class="lb">Баары</span></a>')
    for code, (name, ic) in CATS.items():
        cats += (f'<a href="{link(cat=code, sub=None)}" '
                 f'class="cat{" on" if cat == code else ""}">'
                 f'<span class="ic">{ic}</span><span class="lb">{esc(name)}</span></a>')

    # Түр тилкеси — категория тандалганда гана көрүнөт
    sbar = ""
    if cat and SUBS.get(cat):
        sc = sub_counts(cat, reg)
        chips = (f'<a href="{link(sub=None)}" class="sb2{"" if sub else " on"}">Баары</a>')
        for code, nm in SUBS[cat]:
            if not sc.get(code):
                continue
            chips += (f'<a href="{link(sub=code)}" class="sb2{" on" if sub == code else ""}">'
                      f'{esc(nm)} <em>{sc[code]}</em></a>')
        if chips.count("<a") > 1:
            sbar = f'<nav class="subbar">{chips}</nav>'


    regs = used_regions()
    rb = f'<a href="{link(region=None)}" class="rg{"" if reg else " on"}">Бүт Кыргызстан</a>'
    for rg in regs:
        rb += (f'<a href="{link(region=rg)}" '
               f'class="rg{" on" if reg == rg else ""}">{esc(rg)}</a>')
    rb = f'<nav class="regbar">{rb}</nav>'

    if rows:
        if q:
            lbl = f"«{esc(q)}» боюнча"
        elif sub and cat:
            lbl = esc(sub_title(cat, sub))
        elif cat:
            lbl = esc(CATS[cat][0])
        else:
            lbl = "жарыя"
        clear = f'<a href="/" class="cl">Тазалоо</a>' if (q or cat or reg or sub) else ""
        body = (f'<div class="rl"><span class="rn">{len(rows)}</span>'
                f'<span class="rlb">{lbl}</span>{clear}</div>'
                f'<div class="g">{"".join(card(r) for r in rows)}</div>')
    else:
        body = ('<div class="em"><i></i><h2>Эч нерсе табылган жок</h2>'
                '<p>Башка сөз менен аракет кылып көрүңүз.</p>'
                '<a class="dk" href="/">Бардык жарыялар</a></div>')

    return page(header(q, cat, reg) + f'<nav class="cats">{cats}</nav>' + rb + sbar +
                f'<main class="wrap">{body}</main>')


def detail(r):
    txt, deal = price_bits(r["price"])
    name, ic = CATS.get(r["category"], ("—", ""))
    sname = sub_title(r["category"], r.get("subcat"))
    desc = (f'<div class="dcard"><p class="d">{esc(r["description"])}</p></div>'
            if r["description"] else "")
    dimg = (f'<img src="/media/{esc(r["photo"])}" alt="">'
            if r.get("photo") else '<i></i>')
    tel = ""
    if r["contact"]:
        num = "".join(ch for ch in r["contact"] if ch.isdigit() or ch == "+")
        tel = f'<a class="btn" href="tel:{esc(num)}">&#9742; {esc(r["contact"])}</a>'
    body = f"""<main class="wrap">
<a class="back" href="/?cat={r['category']}">← {esc(name)}</a>
<div class="dph">{dimg}</div>
<div class="dcard">
<div class="eb">{ic} {esc(sname or name)} · №{r['id']}</div>
<div class="dp{' dpd' if deal else ''}">{esc(txt)}</div>
<h1>{esc(r['title'])}</h1>
<div class="f"><div><b>Аймак</b><span>{esc(r['region'] or '—')}</span></div>
<div><b>Коюлган</b><span>{esc(ago(r['created_at']))}</span></div>
<div><b>Көрүү</b><span>{r['views']}</span></div></div>
</div>{desc}{tel}</main>"""
    return page(header() + body, r["title"])


# ---------------- Сервер ----------------

class H(BaseHTTPRequestHandler):
    def _send(self, body, code=200):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)

        if u.path == "/":
            q = (qs.get("q", [""])[0]).strip()
            cat = qs.get("cat", [None])[0]
            if cat not in CATS:
                cat = None
            reg = (qs.get("region", [""])[0]).strip() or None
            sub = (qs.get("sub", [""])[0]).strip() or None
            self._send(home(q, cat, reg, sub))

        elif u.path.startswith("/e/"):
            try:
                r = one(int(u.path[3:]))
            except ValueError:
                r = None
            if r:
                self._send(detail(r))
            else:
                self._send(page(header() + '<main class="wrap"><div class="em"><i></i>'
                                '<h2>Бул жарыя жок</h2><p>Шилтеме туура эмес болушу мүмкүн.</p>'
                                '<a class="dk" href="/">Башкы бетке</a></div></main>'), 404)
        elif u.path.startswith("/media/"):
            name = os.path.basename(urllib.parse.unquote(u.path[7:]))
            fp = os.path.join(MEDIA, name)
            if name and os.path.isfile(fp):
                data = open(fp, "rb").read()
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "max-age=86400")
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.end_headers()

        else:
            self._send(page(header() + '<main class="wrap"><div class="em"><i></i>'
                            '<h2>Барак жок</h2><p>Мындай дарек жок.</p>'
                            '<a class="dk" href="/">Башкы бетке</a></div></main>'), 404)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    init()
    print("\n  TAP! иштеп жатат")
    print(f"  Браузерден ач:  http://localhost:{PORT}")
    print("  Токтотуу:       CTRL+C\n")
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()
