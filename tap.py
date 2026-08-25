#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAP! — витрина (сайт).

Ботко коюлган жарыяларды көрсөтөт. Бот менен бир эле базаны колдонот.
Иштетүү: python tap.py
Ачуу:    http://localhost:8000
"""

import html, os, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

import core
from core import (CATS, SUBS, MEDIA, category_title, category_icon, sub_title,
                  price_label, is_deal, ago)
from tap_catalog import (TRADE_CATEGORIES, SERVICE_CATEGORIES, RENTAL_CATEGORIES,
                         DELIVERY_CATEGORIES, JOB_CATEGORIES, MARKETS_TYPES)


# ==================== Жаңы таксономия ====================
# Бот кайсы бөлүмдөрдү колдонсо, сайт да ошолорду көрсөтөт.

SECTIONS = [
    ("trade",    "&#128717;", "Соода-сатык"),
    ("service",  "&#128736;", "Кызмат көрсөтүү"),
    ("rental",   "&#128273;", "Ижарага берүү"),
    ("delivery", "&#128230;", "Жеткирүү"),
    ("job",      "&#128188;", "Жумуш берүү"),
    ("markets",  "&#127978;", "Базарлар"),
    ("taxi",     "&#128661;", "Такси"),
]

SECTION_NAME = {code: name for code, _, name in SECTIONS}

_CAT_LISTS = {
    "trade":    TRADE_CATEGORIES,
    "service":  SERVICE_CATEGORIES,
    "rental":   RENTAL_CATEGORIES,
    "delivery": DELIVERY_CATEGORIES,
    "job":      JOB_CATEGORIES,
    "markets":  MARKETS_TYPES,
}


def _ky(text):
    """Эки тилдүү жазуунун кыргызча бөлүгү."""
    return str(text or "").split(" / ")[0].strip()


def cat_labels(ad_type):
    """Бөлүмдүн ичиндеги категориялардын аттары: {id: аты}"""
    out = {}
    for c in _CAT_LISTS.get(ad_type) or []:
        out[c["id"]] = _ky(c.get("label") or c["id"])
    return out


# Бардык категориялардын аты — кайсы бөлүмдө болбосун табылсын.
# (Базар жарыяларынын категориясы соода тизмесинен алынат, ошондуктан
#  бир гана өз бөлүмүнөн издөө жетишсиз.)
_ALL_LABELS = {}
for _lst in _CAT_LISTS.values():
    for _c in _lst:
        _ALL_LABELS.setdefault(_c["id"], _ky(_c.get("label") or _c["id"]))


def cat_label(ad_type, cat_id):
    if not cat_id:
        return ""
    return (cat_labels(ad_type).get(cat_id)
            or _ALL_LABELS.get(cat_id)
            or _ky(cat_id).replace("_", " ").capitalize())

PORT = int(os.environ.get("PORT", 8000))


def esc(s):
    return html.escape(str(s or ""))


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
    hidden = ""
    if cat:
        hidden += f'<input type="hidden" name="cat" value="{esc(cat)}">'
    if reg:
        hidden += f'<input type="hidden" name="region" value="{esc(reg)}">'
    return f"""<header class="top"><div class="wrap">
<div class="tin"><span class="logo">TAP!</span>
<span class="pin">&#128205; {esc(reg or 'Бүт Кыргызстан')}</span></div>
<form class="s" action="/">{hidden}
<input type="search" name="q" value="{esc(q)}" placeholder="Жарыя издөө">
<button>Изде</button></form></div></header>"""


def card(r):
    img = (f'<img src="/media/{esc(r["photo"])}" alt="" loading="lazy">'
           if r.get("photo") else '<i></i>')
    return f"""<a class="c" href="/e/{r['id']}">
<div class="ph">{img}<span class="fav">&#9825;</span></div>
<div class="cb"><div class="p{' pd' if is_deal(r['price']) else ''}">{esc(price_label(r['price']))}</div>
<h2 class="t">{esc(r['title'])}</h2>
<div class="m"><span>{esc(ago(r['created_at']))}</span><span>&#128065; {r['views']}</span></div>
</div></a>"""


def home(q, at=None, cid=None, ob=None, di=None):
    """
    Башкы бет.
      at  — бөлүм (trade/service/…)
      cid — бөлүмдүн ичиндеги категория
      ob  — облус,  di — район
    """
    rows = core.find(q, limit=60, ad_type=at, cat_id=cid, oblast=ob, district=di)
    sec_counts = core.adtype_counts(ob)

    def link(**kw):
        """Учурдагы чыпкаларды сактап, бирөөнү гана өзгөрткөн шилтеме."""
        prm = {"q": q or None, "at": at, "cid": cid, "ob": ob, "di": di}
        prm.update(kw)
        prm = {k: v for k, v in prm.items() if v}
        return ("/?" + urllib.parse.urlencode(prm)) if prm else "/"

    # ── Бөлүмдөр ────────────────────────────────────────────
    cats = (f'<a href="{link(at=None, cid=None)}" class="cat{"" if at else " on"}">'
            f'<span class="ic">&#9635;</span><span class="lb">Баары</span></a>')
    for code, ic, name in SECTIONS:
        # Жети бөлүм тең дайыма турат — бош болсо да. Колдонуучу
        # платформада эмне бар экенин бир көз менен көрүшү керек.
        cats += (f'<a href="{link(at=code, cid=None)}" '
                 f'class="cat{" on" if at == code else ""}">'
                 f'<span class="ic">{ic}</span><span class="lb">{esc(name)}</span></a>')

    # ── Облустар ────────────────────────────────────────────
    rb = f'<a href="{link(ob=None, di=None)}" class="rg{"" if ob else " on"}">Бүт Кыргызстан</a>'
    for rg in core.used_oblasts():
        rb += (f'<a href="{link(ob=rg, di=None)}" '
               f'class="rg{" on" if ob == rg else ""}">{esc(rg)}</a>')
    rb = f'<nav class="regbar">{rb}</nav>'

    # ── Райондор — облус тандалганда ────────────────────────
    dbar = ""
    if ob:
        ds = core.used_districts(ob)
        if ds:
            chips = f'<a href="{link(di=None)}" class="rg{"" if di else " on"}">Бүт облус</a>'
            for d in ds:
                chips += (f'<a href="{link(di=d)}" '
                          f'class="rg{" on" if di == d else ""}">{esc(d)}</a>')
            dbar = f'<nav class="regbar">{chips}</nav>'

    # ── Категориялар — бөлүм тандалганда ────────────────────
    sbar = ""
    if at:
        cc = core.catid_counts(at, ob)
        chips = f'<a href="{link(cid=None)}" class="sb2{"" if cid else " on"}">Баары</a>'
        for code, n in sorted(cc.items(), key=lambda x: -x[1]):
            nm = cat_label(at, code)
            chips += (f'<a href="{link(cid=code)}" class="sb2{" on" if cid == code else ""}">'
                      f'{esc(nm)} <em>{n}</em></a>')
        if chips.count("<a") > 1:
            sbar = f'<nav class="subbar">{chips}</nav>'

    # ── Тизме ───────────────────────────────────────────────
    if rows:
        if q:
            lbl = f"«{esc(q)}» боюнча"
        elif cid and at:
            lbl = esc(cat_label(at, cid))
        elif at:
            lbl = esc(SECTION_NAME.get(at, at))
        else:
            lbl = "жарыя"
        clear = ('<a href="/" class="cl">Тазалоо</a>'
                 if (q or at or cid or ob or di) else "")
        main = (f'<div class="rl"><span class="rn">{len(rows)}</span>'
                f'<span class="rlb">{lbl}</span>{clear}</div>'
                f'<div class="g">{"".join(card(r) for r in rows)}</div>')
    elif at and not q and not cid:
        nm = SECTION_NAME.get(at, at)
        main = (f'<div class="em"><i></i><h2>«{esc(nm)}» боюнча жарыя жок</h2>'
                f'<p>Бул бөлүмгө биринчи болуп жарыя коюңуз — ботко жазсаңыз болот.</p>'
                f'<a class="dk" href="/">Бардык жарыялар</a></div>')
    else:
        main = ('<div class="em"><i></i><h2>Эч нерсе табылган жок</h2>'
                '<p>Башка сөз менен аракет кылып көрүңүз.</p>'
                '<a class="dk" href="/">Бардык жарыялар</a></div>')

    return page(header(q, at, di or ob) + f'<nav class="cats">{cats}</nav>' +
                rb + dbar + sbar + f'<main class="wrap">{main}</main>')


def detail(r):
    at = r.get("ad_type")
    if at:
        ic = next((i for c, i, _ in SECTIONS if c == at), "")
        name = SECTION_NAME.get(at, at)
        sname = cat_label(at, r.get("cat_id")) if r.get("cat_id") else ""
        if r.get("sub_id"):
            sname = (sname + " · " + _ky(r["sub_id"])) if sname else _ky(r["sub_id"])
        back = f"/?at={at}"
    else:
        # Эски жарыялар — мурунку категориялар боюнча
        name, ic = CATS.get(r["category"], ("—", ""))
        sname = sub_title(r["category"], r.get("subcat"))
        back = f"/?cat={r['category']}"
    dimg = (f'<img src="/media/{esc(r["photo"])}" alt="">'
            if r.get("photo") else '<i></i>')
    desc = (f'<div class="dcard"><p class="d">{esc(r["description"])}</p></div>'
            if r.get("description") else "")
    tel = ""
    if r.get("contact"):
        num = "".join(ch for ch in r["contact"] if ch.isdigit() or ch == "+")
        tel = f'<a class="btn" href="tel:{esc(num)}">&#9742; {esc(r["contact"])}</a>'
    body = f"""<main class="wrap">
<a class="back" href="{back}">← {esc(name)}</a>
<div class="dph">{dimg}</div>
<div class="dcard">
<div class="eb">{ic} {esc(sname or name)} · №{r['id']}</div>
<div class="dp{' dpd' if is_deal(r['price']) else ''}">{esc(price_label(r['price']))}</div>
<h1>{esc(r['title'])}</h1>
<div class="f"><div><b>Аймак</b><span>{esc(r['region'] or '—')}</span></div>
<div><b>Коюлган</b><span>{esc(ago(r['created_at']))}</span></div>
<div><b>Көрүү</b><span>{r['views']}</span></div></div>
</div>{desc}{tel}</main>"""
    return page(header() + body, r["title"])


def empty_page(title, note):
    return page(header() + f'<main class="wrap"><div class="em"><i></i>'
                f'<h2>{esc(title)}</h2><p>{esc(note)}</p>'
                f'<a class="dk" href="/">Башкы бетке</a></div></main>')


# ==================== Сервер ====================

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

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
            at = qs.get("at", [None])[0]
            if at not in SECTION_NAME:
                at = None
            cid = (qs.get("cid", [""])[0]).strip() or None
            ob = (qs.get("ob", [""])[0]).strip() or None
            di = (qs.get("di", [""])[0]).strip() or None

            # Эски шилтемелер иштей берсин (/?cat=…&region=…)
            if not ob:
                ob = (qs.get("region", [""])[0]).strip() or None
            if not at and qs.get("cat"):
                old = qs["cat"][0]
                at = {"transport": "trade", "realty": "rental",
                      "personal": "trade", "service": "service",
                      "shop": "markets", "business": "job"}.get(old)

            self._send(home(q, at, cid, ob, di))

        elif u.path == "/health":
            self._send("ok")

        elif u.path.startswith("/e/"):
            try:
                r = core.one(int(u.path[3:]))
            except ValueError:
                r = None
            if r:
                self._send(detail(r))
            else:
                self._send(empty_page("Бул жарыя жок",
                                      "Шилтеме туура эмес болушу мүмкүн."), 404)

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
                self.send_header("Content-Length", "0")
                self.end_headers()

        else:
            self._send(empty_page("Барак жок", "Мындай дарек жок."), 404)

    def log_message(self, *a):
        pass


class Server(ThreadingMixIn, HTTPServer):
    """Бир эле убакта бир нече суроону иштетет."""
    daemon_threads = True


if __name__ == "__main__":
    core.init_db()
    print(f"\n  TAP! витрина: http://localhost:{PORT}", flush=True)
    print(f"  База: {'Postgres' if core.IS_PG else 'SQLite'}\n", flush=True)
    Server(("0.0.0.0", PORT), H).serve_forever()

