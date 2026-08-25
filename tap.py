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
from design import CSS, NAV, FONTS, ICONS, NAV_ICONS, TUNDUK


# ==================== Жаңы таксономия ====================
# Бот кайсы бөлүмдөрдү колдонсо, сайт да ошолорду көрсөтөт.

SECTIONS = [
    ("trade",    ICONS["trade"],    "Соода-сатык"),
    ("service",  ICONS["service"],  "Кызмат көрсөтүү"),
    ("rental",   ICONS["rental"],   "Ижарага берүү"),
    ("delivery", ICONS["delivery"], "Жеткирүү"),
    ("job",      ICONS["job"],      "Жумуш берүү"),
    ("markets",  ICONS["markets"],  "Базарлар"),
    ("taxi",     ICONS["taxi"],     "Такси"),
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


# Тандалган чыпка тилкенин ичинде жашырылып калбасын — көрүнөр жерге жылдырат.
SCROLL_JS = ('<script>document.querySelectorAll(".cats,.regbar,.subbar")'
             '.forEach(function(n){var a=n.querySelector(".on");'
             'if(a)n.scrollLeft=Math.max(0,a.offsetLeft-16)})</script>')


def page(body, title="ТАП!"):
    return f"""<!DOCTYPE html><html lang="ky"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0B6E3F">
<title>{esc(title)}</title>{FONTS}<style>{CSS}</style></head><body>{body}{NAV}
{SCROLL_JS}</body></html>"""


def header(q="", cat=None, reg=None):
    hidden = ""
    if cat:
        hidden += f'<input type="hidden" name="cat" value="{esc(cat)}">'
    if reg:
        hidden += f'<input type="hidden" name="region" value="{esc(reg)}">'
    return f"""<header class="top"><div class="wrap">
<div class="tin"><a href="/" class="logo">{TUNDUK}<span>ТАП!</span></a>
<span class="pin"><b>&#9679;</b>{esc(reg or 'Бүт Кыргызстан')}</span></div>
<form class="s" action="/">{hidden}
<input type="search" name="q" value="{esc(q)}" placeholder="Жарыя издөө">
<button>Изде</button></form></div></header>"""


_EYE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9">'
        '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/>'
        '<circle cx="12" cy="12" r="3.1"/></svg>')


def card(r):
    has = bool(r.get("photo"))
    img = (f'<img src="/media/{esc(r["photo"])}" alt="" loading="lazy">'
           if has else f'<i>{TUNDUK}</i>')
    return f"""<a class="c{'' if has else ' nophoto'}" href="/e/{r['id']}">
<div class="ph">{img}<span class="fav">{NAV_ICONS['fav']}</span></div>
<div class="cb"><div class="p{' pd' if is_deal(r['price']) else ''}">{esc(price_label(r['price']))}</div>
<h2 class="t">{esc(r['title'])}</h2>
<div class="m"><span>{esc(ago(r['created_at']))}</span>
<span class="vw">{_EYE}{r['views']}</span></div>
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
            f'<span class="ic">{ICONS["all"]}</span><span class="lb">Баары</span></a>')
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
        main = (f'<div class="em"><i>{TUNDUK}</i><h2>«{esc(nm)}» боюнча жарыя жок</h2>'
                f'<p>Бул бөлүмгө биринчи болуп жарыя коюңуз — ботко жазсаңыз болот.</p>'
                f'<a class="dk" href="/">Бардык жарыялар</a></div>')
    else:
        main = (f'<div class="em"><i>{TUNDUK}</i><h2>Эч нерсе табылган жок</h2>'
                '<p>Башка сөз менен аракет кылып көрүңүз.</p>'
                '<a class="dk" href="/">Бардык жарыялар</a></div>')

    return page(header(q, at, di or ob) + f'<nav class="cats">{cats}</nav>' +
                rb + dbar + sbar + f'<main class="wrap">{main}</main>')


_PHONE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
          'stroke-linecap="round" stroke-linejoin="round">'
          '<path d="M21 16.4v2.6a1.8 1.8 0 0 1-2 1.8 17.6 17.6 0 0 1-7.7-2.7 17.3 17.3 0 0 1-5.3-5.3'
          'A17.6 17.6 0 0 1 3.2 5a1.8 1.8 0 0 1 1.8-2h2.6a1.8 1.8 0 0 1 1.8 1.6c.1 1 .3 1.9.6 2.7'
          'a1.8 1.8 0 0 1-.4 1.9l-1.1 1.1a14.4 14.4 0 0 0 5.3 5.3l1.1-1.1a1.8 1.8 0 0 1 1.9-.4'
          'c.9.3 1.8.5 2.7.6A1.8 1.8 0 0 1 21 16.4Z"/></svg>')

_ARROW = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" '
          'stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px">'
          '<path d="M14.5 5.5 8 12l6.5 6.5"/></svg>')


def pretty_phone(num):
    """700333333 -> +996 700 333 333"""
    d = "".join(ch for ch in num if ch.isdigit())
    if d.startswith("996"):
        d = d[3:]
    elif d.startswith("0"):
        d = d[1:]
    if len(d) == 9:
        return "+996 %s %s %s" % (d[:3], d[3:6], d[6:])
    return num


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
        name, _emoji = CATS.get(r["category"], ("—", ""))
        ic = ICONS["all"]
        sname = sub_title(r["category"], r.get("subcat"))
        back = f"/?cat={r['category']}"
    dimg = (f'<img src="/media/{esc(r["photo"])}" alt="">'
            if r.get("photo") else f'<i>{TUNDUK}</i>')
    desc = (f'<div class="dcard"><p class="d">{esc(r["description"])}</p></div>'
            if r.get("description") else "")
    tel = ""
    if r.get("contact"):
        num = "".join(ch for ch in r["contact"] if ch.isdigit() or ch == "+")
        shown = pretty_phone(num)
        tel = (f'<a class="btn" href="tel:{esc(num)}">{_PHONE}'
               f'<span>{esc(shown)}</span></a>')
    body = f"""<main class="wrap">
<a class="back" href="{back}">{_ARROW}{esc(name)}</a>
<div class="dph">{dimg}</div>
<div class="dcard">
<div class="eb">{ic}{esc(sname or name)} · №{r['id']}</div>
<div class="dp{' dpd' if is_deal(r['price']) else ''}">{esc(price_label(r['price']))}</div>
<h1>{esc(r['title'])}</h1>
<div class="f"><div><b>Аймак</b><span>{esc(r['region'] or '—')}</span></div>
<div><b>Коюлган</b><span>{esc(ago(r['created_at']))}</span></div>
<div><b>Көрүү</b><span>{r['views']}</span></div></div>
</div>{desc}{tel}</main>"""
    return page(header() + body, r["title"])


def empty_page(title, note):
    return page(header() + f'<main class="wrap"><div class="em"><i>{TUNDUK}</i>'
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

