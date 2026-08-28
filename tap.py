#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAP! — витрина (сайт).

Ботко коюлган жарыяларды көрсөтөт. Бот менен бир эле базаны колдонот.
Иштетүү: python tap.py
Ачуу:    http://localhost:8000
"""

import html, json, os, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

import core
from core import (CATS, SUBS, MEDIA, category_title, category_icon, sub_title,
                  price_label, is_deal, ago)
from tap_catalog import (TRADE_CATEGORIES, SERVICE_CATEGORIES, RENTAL_CATEGORIES,
                         DELIVERY_CATEGORIES, JOB_CATEGORIES, MARKETS_TYPES,
                         OBLASTS, get_districts, get_localities)
from design import CSS, nav, FONTS, ICONS, NAV_ICONS, BOT
from scenes import SCENES
from strings import T, L


# ==================== Жаңы таксономия ====================
# Бот кайсы бөлүмдөрдү колдонсо, сайт да ошолорду көрсөтөт.

SECTIONS = [
    ("trade",    SCENES["trade"],    "Соода-сатык"),
    ("service",  SCENES["service"],  "Кызмат көрсөтүү"),
    ("rental",   SCENES["rental"],   "Ижарага берүү"),
    ("delivery", SCENES["delivery"], "Жеткирүү"),
    ("job",      SCENES["job"],      "Жумуш берүү"),
    ("markets",  SCENES["markets"],  "Базарлар"),
    ("taxi",     SCENES["taxi"],     "Такси"),
]

SECTION_CODES = [c for c, _, _ in SECTIONS]
SECTION_NAME = {code: name for code, _, name in SECTIONS}

_CAT_LISTS = {
    "trade":    TRADE_CATEGORIES,
    "service":  SERVICE_CATEGORIES,
    "rental":   RENTAL_CATEGORIES,
    "delivery": DELIVERY_CATEGORIES,
    "job":      JOB_CATEGORIES,
    "markets":  MARKETS_TYPES,
}


def _ky(text, lang="ky"):
    """Эки тилдүү жазуунун керектүү бөлүгү."""
    return L(text, lang)


def cat_labels(ad_type, lang="ky"):
    """Бөлүмдүн ичиндеги категориялардын аттары: {id: аты}"""
    out = {}
    for c in _CAT_LISTS.get(ad_type) or []:
        out[c["id"]] = _ky(c.get("label") or c["id"], lang)
    return out


# Бардык категориялардын аты — кайсы бөлүмдө болбосун табылсын.
# (Базар жарыяларынын категориясы соода тизмесинен алынат, ошондуктан
#  бир гана өз бөлүмүнөн издөө жетишсиз.)
_ALL_RAW = {}
for _lst in _CAT_LISTS.values():
    for _c in _lst:
        _ALL_RAW.setdefault(_c["id"], _c.get("label") or _c["id"])


def cat_label(ad_type, cat_id, lang="ky"):
    if not cat_id:
        return ""
    return (cat_labels(ad_type, lang).get(cat_id)
            or _ky(_ALL_RAW.get(cat_id, ""), lang)
            or str(cat_id).replace("_", " ").capitalize())


def section_name(code, lang="ky"):
    return T(code, lang) if code in ("trade", "service", "rental", "delivery",
                                     "job", "markets", "taxi") else code

PORT = int(os.environ.get("PORT", 8000))


def esc(s):
    return html.escape(str(s or ""))


# Тандалган чыпка тилкенин ичинде жашырылып калбасын — көрүнөр жерге жылдырат.
# Тандалгандар браузердин өз эсинде сакталат: катталуунун кереги жок,
# телефондон чыкпайт. Сервер аларды билбейт.
FAV_JS = ("""<script>
(function(){
 var K="tap_fav";
 function get(){try{return JSON.parse(localStorage.getItem(K))||[]}catch(e){return []}}
 function set(v){try{localStorage.setItem(K,JSON.stringify(v))}catch(e){}}
 window.tapFavs=get;
 // Жаңы карточкалар кошулганда кайра чакырылат (мис. «Тандалган» бетинде)
 window.tapBindFavs=function(root){
   (root||document).querySelectorAll(".fav").forEach(function(b){
     var id=b.getAttribute("data-id"); if(!id||b.dataset.bound)return;
     b.dataset.bound="1";
     if(get().indexOf(id)>=0)b.classList.add("on");
     b.addEventListener("click",function(e){
       e.preventDefault(); e.stopPropagation();
       var f=get(), i=f.indexOf(id);
       if(i>=0){f.splice(i,1);b.classList.remove("on")}else{f.push(id);b.classList.add("on")}
       set(f);
     });
   });
 };
 window.tapBindFavs();
})();
</script>""")

# Категория чиби басылганда ошол катардын ичи гана жаңыланат.
SHELF_JS = ("""<script>
document.addEventListener("click",function(e){
 var b=e.target.closest(".shchips .sb2"); if(!b)return;
 var sec=b.getAttribute("data-sec"), cid=b.getAttribute("data-cid")||"";
 var row=document.getElementById("row-"+sec); if(!row)return;
 b.parentNode.querySelectorAll(".sb2").forEach(function(x){x.classList.remove("on")});
 b.classList.add("on");
 row.classList.add("load");
 fetch("/api/ads?at="+encodeURIComponent(sec)+"&cid="+encodeURIComponent(cid))
  .then(function(r){return r.text()})
  .then(function(h){
    row.innerHTML=h||"";
    row.scrollLeft=0;
    row.classList.remove("load");
    if(window.tapBindFavs)window.tapBindFavs(row);
  })
  .catch(function(){row.classList.remove("load")});
});
</script>""")

SCROLL_JS = ('<script>document.querySelectorAll(".cats,.regbar,.subbar")'
             '.forEach(function(n){var a=n.querySelector(".on");'
             'if(a)n.scrollLeft=Math.max(0,a.offsetLeft-16)})</script>')


def page(body, title="ТАП!", tab="home", lang="ky"):
    return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0B6E3F">
<title>{esc(title)}</title>{FONTS}<style>{CSS}</style></head><body>{body}{nav(tab, lang)}
{SCROLL_JS}{FAV_JS}{SHELF_JS}</body></html>"""


def _lang_switch(lang):
    """Тил алмаштыруу. Тандоо cookie'ге жазылат, ошол бойдон калат."""
    out = ""
    for code, label in (("ky", "KG"), ("ru", "RU")):
        on = " on" if lang == code else ""
        out += f'<a class="lg{on}" href="/lang/{code}" rel="nofollow">{label}</a>'
    return f'<span class="lgs">{out}</span>'


def header(q="", at=None, reg=None, lang="ky"):
    hidden = f'<input type="hidden" name="at" value="{esc(at)}">' if at else ""
    return f"""<header class="top"><div class="wrap">
<div class="tin"><a href="/" class="logo"><span>ТАП!</span></a>
<span class="pin"><b>&#9679;</b>{esc(reg or T("all_kg", lang))}</span>
{_lang_switch(lang)}</div>
<form class="s" action="/">{hidden}
<input type="search" name="q" value="{esc(q)}" placeholder="{T("search_ph", lang)}">
<button>{T("search_btn", lang)}</button></form></div></header>"""


_EMPTY = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
          'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
          '<circle cx="10.5" cy="10.5" r="7"/><path d="m15.6 15.6 5.4 5.4"/></svg>')

_NOPHOTO = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
            '<rect x="3" y="5" width="18" height="14" rx="2.6"/>'
            '<circle cx="8.5" cy="10" r="1.8"/>'
            '<path d="m3.5 17 5-4.6 3.4 3 3.6-3.4 5 5"/></svg>')

_EYE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9">'
        '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/>'
        '<circle cx="12" cy="12" r="3.1"/></svg>')


def card(r, lang="ky"):
    has = bool(r.get("photo"))
    img = (f'<img src="/media/{esc(r["photo"])}" alt="" loading="lazy">'
           if has else f'<i>{_NOPHOTO}</i>')
    return f"""<a class="c{'' if has else ' nophoto'}" href="/e/{r['id']}">
<div class="ph">{img}<button class="fav" data-id="{r['id']}" aria-label="Тандалганга кошуу">{NAV_ICONS['fav']}</button></div>
<div class="cb"><div class="p{' pd' if is_deal(r['price']) else ''}">{esc(price_label(r['price']))}</div>
<h2 class="t">{esc(L(r['title'], lang))}</h2>
<div class="m"><span>{esc(ago(r['created_at']))}</span>
<span class="vw">{_EYE}{r['views']}</span></div>
</div></a>"""


def _chip(href, label, on, n=0):
    """Аймактын баскычы. Жарыясы бар болсо санын көрсөтөт."""
    num = f' <em>{n}</em>' if n else ""
    cls = "rg on" if on else "rg"
    return f'<a href="{href}" class="{cls}">{esc(label)}{num}</a>'


def _filter_bars(link, at, cid, ob, di, vi, lang):
    """Аймак жана категория чыпкаларынын тилкелери."""
    # 1-тепкич: облустар — боттогудай толук тизме
    oc = core.oblast_counts()
    rb = _chip(link(ob=None, di=None, vi=None), T("all_kg", lang), not ob)
    for rg in OBLASTS:
        rb += _chip(link(ob=rg, di=None, vi=None), rg, ob == rg, oc.get(rg, 0))
    out = f'<nav class="regbar">{rb}</nav>'

    # 2-тепкич: райондор жана шаарлар
    if ob:
        dc = core.district_counts(ob)
        ds = list(get_districts(ob)) or core.used_districts(ob)
        if ds:
            chips = _chip(link(di=None, vi=None), T("all_oblast", lang), not di)
            for x in ds:
                chips += _chip(link(di=x, vi=None), x, di == x, dc.get(x, 0))
            out += f'<nav class="regbar">{chips}</nav>'

    # 3-тепкич: айыл аймактары жана кичи райондор
    if ob and di:
        vc = core.village_counts(ob, di)
        vs = list(get_localities(ob, di)) or core.used_villages(ob, di)
        if vs:
            whole = "Весь район" if lang == "ru" else "Бүт район"
            chips = _chip(link(vi=None), whole, not vi)
            for x in vs:
                chips += _chip(link(vi=x), x, vi == x, vc.get(x, 0))
            out += f'<nav class="regbar">{chips}</nav>'

    if at:
        cc = core.catid_counts(at, ob)
        chips = (f'<a href="{link(cid=None)}" class="sb2{"" if cid else " on"}">'
                 f'{T("all", lang)}</a>')
        for code, n in sorted(cc.items(), key=lambda x: -x[1]):
            chips += (f'<a href="{link(cid=code)}" '
                      f'class="sb2{" on" if cid == code else ""}">'
                      f'{esc(cat_label(at, code, lang))} <em>{n}</em></a>')
        if chips.count("<a") > 1:
            out += f'<nav class="subbar">{chips}</nav>'
    return out


def _sections_strip(link, at, lang):
    cats = (f'<a href="{link(at=None, cid=None)}" class="cat{"" if at else " on"}">'
            f'<span class="ic">{SCENES["all"]}</span>'
            f'<span class="lb">{T("all", lang)}</span></a>')
    for code, ic, _name in SECTIONS:
        cats += (f'<a href="{link(at=code, cid=None)}" '
                 f'class="cat{" on" if at == code else ""}">'
                 f'<span class="ic">{ic}</span>'
                 f'<span class="lb">{esc(section_name(code, lang))}</span></a>')
    return f'<nav class="cats">{cats}</nav>'


def shelves(lang="ky"):
    """
    Башкы бет: ар бир бөлүм өзүнчө катар болуп турат, жарыялары оңго-солго
    сүрүлөт. Категория чиптерин басканда ошол катардын ичи алмашат —
    бет кайра жүктөлбөйт.
    """
    out = []
    for code, _ic, _n in SECTIONS:
        rows = core.find(limit=12, ad_type=code)
        if not rows:
            continue
        cc = core.catid_counts(code)
        chips = (f'<button class="sb2 on" data-sec="{code}" data-cid="">'
                 f'{T("all", lang)}</button>')
        for cid, n in sorted(cc.items(), key=lambda x: -x[1])[:12]:
            chips += (f'<button class="sb2" data-sec="{code}" data-cid="{esc(cid)}">'
                      f'{esc(cat_label(code, cid, lang))} <em>{n}</em></button>')
        out.append(
            f'<section class="shelf" id="sh-{code}">'
            f'<div class="shead"><h2>{esc(section_name(code, lang))}</h2>'
            f'<a href="/?at={code}" class="more">{T("show_all", lang)} ›</a></div>'
            f'<nav class="subbar shchips">{chips}</nav>'
            f'<div class="srow" id="row-{code}">'
            f'{"".join(card(r, lang) for r in rows)}</div></section>')
    return "".join(out)


def home(q, at=None, cid=None, ob=None, di=None, vi=None, lang="ky"):
    """
    Башкы бет.
      at  — бөлүм (trade/service/…)
      cid — бөлүмдүн ичиндеги категория
      ob  — облус,  di — район
    Эч кандай чыпка жок болсо — бөлүмдөр катар-катар болуп көрүнөт.
    """
    def link(**kw):
        """Учурдагы чыпкаларды сактап, бирөөнү гана өзгөрткөн шилтеме."""
        prm = {"q": q or None, "at": at, "cid": cid,
               "ob": ob, "di": di, "vi": vi}
        prm.update(kw)
        prm = {k: v for k, v in prm.items() if v}
        return ("/?" + urllib.parse.urlencode(prm)) if prm else "/"

    top = header(q, at, vi or di or ob, lang) + _sections_strip(link, at, lang)

    # Чыпкасыз башкы бет — катар-катар тизме
    if not (q or at or cid or ob or di or vi):
        return page(top + f'<main class="wrap">{shelves(lang)}</main>',
                    "ТАП!", "home", lang)

    rows = core.find(q, limit=60, ad_type=at, cat_id=cid,
                     oblast=ob, district=di, village=vi)
    body = _filter_bars(link, at, cid, ob, di, vi, lang)

    if rows:
        if q:
            lbl = f"«{esc(q)}» {T('by_word', lang)}"
        elif cid and at:
            lbl = esc(cat_label(at, cid, lang))
        elif at:
            lbl = esc(section_name(at, lang))
        else:
            lbl = T("ads", lang)
        main = (f'<div class="rl"><span class="rn">{len(rows)}</span>'
                f'<span class="rlb">{lbl}</span>'
                f'<a href="/" class="cl">{T("clear", lang)}</a></div>'
                f'<div class="g">{"".join(card(r, lang) for r in rows)}</div>')
    elif at and not q and not cid:
        nm = section_name(at, lang)
        main = (f'<div class="em"><i>{_EMPTY}</i>'
                f'<h2>«{esc(nm)}» {T("empty_sec", lang)}</h2>'
                f'<p>{T("be_first", lang)}</p>'
                f'<a class="dk" href="/">{T("all_ads", lang)}</a></div>')
    else:
        main = (f'<div class="em"><i>{_EMPTY}</i><h2>{T("nothing", lang)}</h2>'
                f'<p>{T("try_other", lang)}</p>'
                f'<a class="dk" href="/">{T("all_ads", lang)}</a></div>')

    return page(top + body + f'<main class="wrap">{main}</main>',
                "ТАП!", "home", lang)


_PHONE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
          'stroke-linecap="round" stroke-linejoin="round">'
          '<path d="M21 16.4v2.6a1.8 1.8 0 0 1-2 1.8 17.6 17.6 0 0 1-7.7-2.7 17.3 17.3 0 0 1-5.3-5.3'
          'A17.6 17.6 0 0 1 3.2 5a1.8 1.8 0 0 1 1.8-2h2.6a1.8 1.8 0 0 1 1.8 1.6c.1 1 .3 1.9.6 2.7'
          'a1.8 1.8 0 0 1-.4 1.9l-1.1 1.1a14.4 14.4 0 0 0 5.3 5.3l1.1-1.1a1.8 1.8 0 0 1 1.9-.4'
          'c.9.3 1.8.5 2.7.6A1.8 1.8 0 0 1 21 16.4Z"/></svg>')

_WA = ('<svg viewBox="0 0 24 24" fill="currentColor">'
       '<path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5.1-1.3A10 10 0 1 0 12 2Zm0 18.2'
       'a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Z"/>'
       '<path d="M16.6 14.3c-.3-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2'
       '-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.1-.2 0-.4.1-.5l.4-.5c.1-.2.2-.3.3-.5 0-.2 0-.3'
       '-.1-.4l-.8-1.9c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3c-.3.3-.9.9-.9 2.1s.9 2.5'
       '1 2.6c.1.2 1.8 2.8 4.4 3.9 1.6.7 2.2.7 3 .6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.1'
       '-1.2l-.5-.4Z"/></svg>')

_TG = ('<svg viewBox="0 0 24 24" fill="currentColor">'
       '<path d="M21.9 4.3 18.7 19c-.2 1-.9 1.3-1.7.8l-4.7-3.5-2.3 2.2c-.3.3-.5.5-1 .5'
       'l.3-4.8 8.8-8c.4-.3-.1-.5-.6-.2L6.7 13.1l-4.7-1.5c-1-.3-1-1 .2-1.5L20.6 3'
       'c.8-.3 1.6.2 1.3 1.3Z"/></svg>')

_ARROW = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" '
          'stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px">'
          '<path d="M14.5 5.5 8 12l6.5 6.5"/></svg>')


def contact_block(raw, lang="ky"):
    """
    Байланыш баскычтары: чалуу, WhatsApp, Telegram.

    Кыргызстанда көпчүлүк WhatsApp менен жазышат, ошондуктан үчөө тең
    керек. Telegram номер боюнча ачылат — ал номерде Telegram бар болсо.
    """
    if not raw:
        return ""
    digits = "".join(ch for ch in str(raw) if ch.isdigit())
    if digits.startswith("996"):
        digits = digits[3:]
    elif digits.startswith("0"):
        digits = digits[1:]
    if len(digits) != 9:
        # Кадимкидей эмес номер — чалуу баскычы гана
        num = "".join(ch for ch in str(raw) if ch.isdigit() or ch == "+")
        return (f'<a class="btn" href="tel:{esc(num)}">{_PHONE}'
                f'<span>{esc(raw)}</span></a>')

    intl = "996" + digits
    shown = "+996 %s %s %s" % (digits[:3], digits[3:6], digits[6:])
    return f"""<div class="cnum">{esc(shown)}</div>
<div class="cbar">
<a class="cb1 call" href="tel:+{intl}">{_PHONE}<span>{T("c_call", lang)}</span></a>
<a class="cb1 wa" href="https://wa.me/{intl}" target="_blank" rel="noopener">
{_WA}<span>WhatsApp</span></a>
<a class="cb1 tg" href="https://t.me/+{intl}" target="_blank" rel="noopener">
{_TG}<span>Telegram</span></a>
</div>"""


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


# Галереянын стили. Кадимки сап — f-string эмес, ошондуктан
# CSS'тин { } белгилери коопсуз.
_GAL_CSS = """<style>
.dph{position:relative}
.pgal{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;
      gap:4px;-webkit-overflow-scrolling:touch;scrollbar-width:none}
.pgal::-webkit-scrollbar{display:none}
.pgal img{flex:0 0 100%;scroll-snap-align:center;width:100%;
          object-fit:contain;border-radius:14px}
.pgc{position:absolute;right:12px;bottom:12px;padding:3px 10px;
     border-radius:999px;background:rgba(0,0,0,.6);color:#fff;
     font-size:13px;font-weight:600;pointer-events:none}
</style>
<script>
(function(){
  var g=document.getElementById("pgal"), c=document.getElementById("pgc");
  if(!g||!c) return;
  var n=g.children.length;
  g.addEventListener("scroll", function(){
    var i=Math.round(g.scrollLeft/g.clientWidth)+1;
    if(i<1) i=1;
    if(i>n) i=n;
    c.textContent=i+" / "+n;
  }, {passive:true});
})();
</script>"""


def detail(r, lang="ky"):
    at = r.get("ad_type")
    if at:
        ic = next((i for c, i, _ in SECTIONS if c == at), "")
        name = section_name(at, lang)
        sname = cat_label(at, r.get("cat_id"), lang) if r.get("cat_id") else ""
        if r.get("sub_id"):
            sub = _ky(r["sub_id"], lang)
            sname = (sname + " · " + sub) if sname else sub
        back = f"/?at={at}"
    else:
        # Эски жарыялар — мурунку категориялар боюнча
        name, _emoji = CATS.get(r["category"], ("—", ""))
        ic = ICONS["all"]
        sname = sub_title(r["category"], r.get("subcat"))
        back = f"/?cat={r['category']}"
    # Галерея: бир нече сүрөт болсо сол-оңго сүрүп кароого болот.
    shots = core.photo_list(r)
    if not shots:
        dimg = f'<i>{_NOPHOTO}</i>'
    elif len(shots) == 1:
        dimg = f'<img src="/media/{esc(shots[0])}" alt="">'
    else:
        strip = "".join(
            f'<img src="/media/{esc(p)}" alt="" loading="lazy">'
            for p in shots)
        dimg = (_GAL_CSS + '<div class="pgal" id="pgal">' + strip
                + '</div><span class="pgc" id="pgc">1 / '
                + str(len(shots)) + '</span>')
    desc = (f'<div class="dcard"><p class="d">{esc(r["description"])}</p></div>'
            if r.get("description") else "")
    tel = contact_block(r.get("contact"), lang)
    body = f"""<main class="wrap">
<a class="back" href="{back}">{_ARROW}{esc(name)}</a>
<div class="dph">{dimg}</div>
<div class="dcard">
<div class="eb">{ic}{esc(sname or name)} · №{r['id']}</div>
<div class="dp{' dpd' if is_deal(r['price']) else ''}">{esc(price_label(r['price']))}</div>
<h1>{esc(L(r['title'], lang))}</h1>
<div class="f"><div><b>{T("region", lang)}</b><span>{esc(r['region'] or '—')}</span></div>
<div><b>{T("posted", lang)}</b><span>{esc(ago(r['created_at']))}</span></div>
<div><b>{T("views", lang)}</b><span>{r['views']}</span></div></div>
</div>{desc}{tel}</main>"""
    return page(header("", None, None, lang) + body,
                L(r["title"], lang), tab="home", lang=lang)


def find_page(ob=None, di=None, lang="ky"):
    """
    Аймак боюнча издөө: облус → район → айыл, анан аталыш боюнча.
    Ар бир кадамда жарыясы бар аймактар гана көрсөтүлөт.
    """
    def link(**kw):
        prm = {"ob": ob, "di": di}
        prm.update(kw)
        prm = {k: v for k, v in prm.items() if v}
        return ("/find?" + urllib.parse.urlencode(prm)) if prm else "/find"

    # Кайсы кадамда турабыз
    if not ob:
        title, items = T("find_oblast", lang), [
            (x, link(ob=x, di=None)) for x in core.used_oblasts()]
    elif not di:
        title, items = T("find_district", lang), [
            (x, link(di=x)) for x in core.used_districts(ob)]
    else:
        title, items = T("find_village", lang), [
            (x, "/?" + urllib.parse.urlencode({"ob": ob, "di": di, "q": ""}))
            for x in core.used_villages(ob, di)]

    crumbs = ""
    if ob:
        crumbs += (f'<a href="{link(ob=None, di=None)}" class="rg">✕ {esc(ob)}</a>')
    if di:
        crumbs += f'<a href="{link(di=None)}" class="rg">✕ {esc(di)}</a>'
    if crumbs:
        crumbs = f'<nav class="regbar">{crumbs}</nav>'

    lst = "".join(f'<a class="frow" href="{href}">{esc(nm)}'
                  f'<span class="fchev">›</span></a>' for nm, href in items)
    if not lst:
        lst = f'<p class="fnote">{T("nothing", lang)}</p>'

    # Аталыш боюнча издөө — тандалган аймактын ичинде
    hidden = ""
    if ob:
        hidden += f'<input type="hidden" name="ob" value="{esc(ob)}">'
    if di:
        hidden += f'<input type="hidden" name="di" value="{esc(di)}">'
    skip = (f'<a class="dk fskip" href="/?{urllib.parse.urlencode({k: v for k, v in {"ob": ob, "di": di}.items() if v})}">'
            f'{T("find_skip", lang)}</a>') if ob else ""

    body = f"""<main class="wrap">
<h1 class="ftitle">{T("find_title", lang)}</h1>
<p class="flead">{T("find_lead", lang)}</p>
{crumbs}
<form class="fsearch" action="/">{hidden}
<input type="search" name="q" placeholder="{T("find_word_ph", lang)}">
<button>{T("find_go", lang)}</button></form>
<div class="fstep">{T("find_word", lang) if False else esc(title)}</div>
<div class="flist">{lst}</div>
{skip}</main>"""
    return page(header("", None, di or ob, lang) + body,
                T("find_title", lang) + " — ТАП!", "home", lang)


# Эки боттун баскычтары. Кадимки сап — f-string эмес,
# ошондуктан CSS'тин { } белгилери коопсуз.
_ADD_CSS = """<style>
.btn.tgbtn{background:#2AA3DA;margin-bottom:10px}
.btn.wabtn{background:#22C15E}
.btn.off{opacity:.55}
</style>"""


def add_page(lang="ky"):
    """
    «Жарыя берүү» — эки боттун бирин тандоо.

    WhatsApp номери WA_NUMBER өзгөрмөсүнөн алынат. Ал коюла электе
    баскыч көрүнөт, бирок басылбайт: «жакында» деп турат.
    """
    ru = (lang == "ru")
    wa_num = "".join(c for c in os.environ.get("WA_NUMBER", "") if c.isdigit())

    head = "Разместить объявление" if ru else "Жарыя берүү"
    lead = ("Объявление размещается через бота — выберите, где вам удобнее."
            if ru else
            "Жарыя бот аркылуу коюлат — кайсынысы ыңгайлуу болсо, ошону тандаңыз.")
    tg_t = "Перейти в Telegram-бот" if ru else "Telegram ботко өтүү"
    wa_t = "Перейти в WhatsApp-бот" if ru else "WhatsApp ботко өтүү"
    soon = "WhatsApp — скоро" if ru else "WhatsApp — жакында"
    note = ("Оба бота работают с одной базой: объявление появится и здесь, "
            "на сайте." if ru else
            "Эки бот бир базада иштейт: жарыя ушул сайтта да чыгат.")

    if wa_num:
        wa = (f'<a class="btn wabtn" href="https://wa.me/{wa_num}?text=%D0%A1%D0%B0%D0%BB%D0%B0%D0%BC"'
              f' target="_blank" rel="noopener">'
              f'<span>{esc(wa_t)}</span></a>')
    else:
        wa = f'<span class="btn wabtn off"><span>{esc(soon)}</span></span>'

    body = f"""<main class="wrap">
<h1 class="ftitle">{esc(head)}</h1>
<p class="flead">{esc(lead)}</p>
<a class="btn tgbtn" href="https://t.me/{BOT}?start=post">
<span>{esc(tg_t)}</span></a>
{wa}
<p class="flead">{esc(note)}</p></main>""" + _ADD_CSS
    return page(header("", None, None, lang) + body,
                head + " — ТАП!", "add", lang)


def msg_page(lang="ky"):
    """Байланыш: сайтта кат жазышуу жок, кантип байланышуу керектиги."""
    blocks = ""
    for h, p in [("msg_h1", "msg_p1"), ("msg_h2", "msg_p2"),
                 ("msg_h3", "msg_p3"), ("msg_h4", "msg_p4")]:
        blocks += (f'<div class="dcard"><h3 class="qh">{T(h, lang)}</h3>'
                   f'<p class="qp">{T(p, lang)}</p></div>')
    body = f"""<main class="wrap">
<h1 class="ftitle">{T("msg_title", lang)}</h1>
<p class="flead">{T("msg_lead", lang)}</p>
{blocks}
<a class="btn" href="https://t.me/{BOT}">{NAV_ICONS['msg']}
<span>{T("msg_btn", lang)}</span></a></main>"""
    return page(header("", None, None, lang) + body,
                T("msg_title", lang) + " — ТАП!", "msg", lang)


def fav_page(lang="ky"):
    """
    Тандалгандар. Тизме браузердин эсинде турат, ошондуктан бет бош
    жүктөлүп, номерлерин JS сурап алат.
    """
    body = f"""<main class="wrap">
<div class="rl"><span class="rn" id="fn">·</span>
<span class="rlb">{T("fav_title", lang)}</span></div>
<div class="g" id="fg"></div>
<div class="em" id="fe" style="display:none"><i>{_EMPTY}</i>
<h2>{T("fav_empty", lang)}</h2>
<p>{T("fav_hint", lang)}</p>
<a class="dk" href="/">{T("fav_look", lang)}</a></div></main>
<script>
window.addEventListener("DOMContentLoaded",function(){{
 var ids=[]; try{{ids=JSON.parse(localStorage.getItem("tap_fav"))||[]}}catch(err){{}}
 var g=document.getElementById("fg"),e=document.getElementById("fe"),n=document.getElementById("fn");
 if(!ids.length){{n.textContent="0";e.style.display="";return}}
 fetch("/api/favs?ids="+encodeURIComponent(ids.join(",")))
  .then(function(r){{return r.text()}})
  .then(function(h){{
    g.innerHTML=h;
    if(window.tapBindFavs)window.tapBindFavs(g);
    var c=g.querySelectorAll(".c").length;
    n.textContent=c;
    if(!c)e.style.display="";
  }})
  .catch(function(){{n.textContent="0";e.style.display=""}});
}});
</script>"""
    return page(header("", None, None, lang) + body,
                T("nav_fav", lang) + " — ТАП!", tab="fav", lang=lang)


def empty_page(title, note, lang="ky"):
    return page(header("", None, None, lang) + f'<main class="wrap"><div class="em"><i>{_EMPTY}</i>'
                f'<h2>{esc(title)}</h2><p>{esc(note)}</p>'
                f'<a class="dk" href="/">{T("nav_home", lang)}</a></div></main>',
                title, "home", lang)


# ==================== Сервер ====================

def _lang(handler):
    """Тил cookie'де сакталат — ар бир шилтемеге тиркөөнүн кереги жок."""
    raw = handler.headers.get("Cookie") or ""
    for part in raw.split(";"):
        k, _, v = part.strip().partition("=")
        if k == "lang" and v in ("ky", "ru"):
            return v
    return "ky"


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, body, code=200, cookie=None):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(data)

    def _go(self, url, cookie=None):
        self.send_response(303)
        self.send_header("Location", url)
        self.send_header("Content-Length", "0")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def do_POST(self):
        """Green API'ден келген WhatsApp билдирүүсү."""
        u = urllib.parse.urlparse(self.path)
        if u.path != "/wa":
            self._send("not found", 404)
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except Exception:
            body = {}
        # Green API жоопту тез күтөт: адегенде «ok» деп жооп берип,
        # анан иштетебиз — антпесе ал билдирүүнү кайра-кайра жиберет.
        self._send("ok")
        try:
            import whatsapp
            whatsapp.handle(body)
        except Exception as e:
            print("  WhatsApp катасы:", e, flush=True)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)

        lang = _lang(self)

        if u.path.startswith("/lang/"):
            new = u.path[6:]
            if new not in ("ky", "ru"):
                new = "ky"
            ref = self.headers.get("Referer") or "/"
            if "://" in ref:
                ref = "/" + ref.split("/", 3)[-1] if ref.count("/") > 2 else "/"
            self._go(ref or "/",
                     "lang=%s; Path=/; Max-Age=31536000; SameSite=Lax" % new)
            return

        if u.path == "/find":
            ob = (qs.get("ob", [""])[0]).strip() or None
            di = (qs.get("di", [""])[0]).strip() or None
            self._send(find_page(ob, di, lang))
            return

        if u.path == "/add":
            self._send(add_page(lang))
            return

        if u.path == "/msg":
            self._send(msg_page(lang))
            return

        if u.path == "/":
            q = (qs.get("q", [""])[0]).strip()
            at = qs.get("at", [None])[0]
            if at not in SECTION_NAME:
                at = None
            cid = (qs.get("cid", [""])[0]).strip() or None
            ob = (qs.get("ob", [""])[0]).strip() or None
            di = (qs.get("di", [""])[0]).strip() or None
            vi = (qs.get("vi", [""])[0]).strip() or None

            # Эски шилтемелер иштей берсин (/?cat=…&region=…)
            if not ob:
                ob = (qs.get("region", [""])[0]).strip() or None
            if not at and qs.get("cat"):
                old = qs["cat"][0]
                at = {"transport": "trade", "realty": "rental",
                      "personal": "trade", "service": "service",
                      "shop": "markets", "business": "job"}.get(old)

            self._send(home(q, at, cid, ob, di, vi, lang))

        elif u.path == "/fav":
            self._send(fav_page(lang))

        elif u.path == "/api/ads":
            at = (qs.get("at", [""])[0]).strip() or None
            if at not in SECTION_NAME:
                at = None
            cid = (qs.get("cid", [""])[0]).strip() or None
            rows = core.find(limit=12, ad_type=at, cat_id=cid)
            self._send("".join(card(r, _lang(self)) for r in rows))

        elif u.path == "/api/favs":
            raw = (qs.get("ids", [""])[0])
            ids = []
            for part in raw.split(",")[:60]:
                part = part.strip()
                if part.isdigit():
                    ids.append(int(part))
            rows = [core.one(i, count_view=False) for i in ids]
            html = "".join(card(r) for r in rows if r)
            self._send(html)

        elif u.path == "/wa":
            import whatsapp
            self._send("ok" if whatsapp.ENABLED else "whatsapp off")

        elif u.path == "/health":
            self._send("ok")

        elif u.path.startswith("/e/"):
            try:
                r = core.one(int(u.path[3:]))
            except ValueError:
                r = None
            if r:
                self._send(detail(r, lang))
            else:
                self._send(empty_page(T("no_page", lang), T("bad_link", lang), lang), 404)

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
            self._send(empty_page(T("no_url", lang), T("no_such", lang), lang), 404)

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

