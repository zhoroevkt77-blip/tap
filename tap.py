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
from tap_catalog import (TRADE_CATEGORIES, PROPERTY_CATEGORIES,
                         SERVICE_CATEGORIES, RENTAL_CATEGORIES,
                         DELIVERY_CATEGORIES, JOB_CATEGORIES, MARKETS_TYPES,
                         MALLS_TYPES,
                         WHOLESALE_CATEGORIES, CARGO_CATEGORIES, JOBSEEK_CATEGORIES,
                         OBLASTS, get_districts, get_localities, ru_name)
from design import CSS, nav, FONTS, ICONS, NAV_ICONS, BOT
from scenes import SCENES
import secimg
import appicon
from strings import T, L, H as help_text
from strings import TOPICS as HELP_TOPICS, topic_title
import bridge


# ==================== Жаңы таксономия ====================
# Бот кайсы бөлүмдөрдү колдонсо, сайт да ошолорду көрсөтөт.

SECTIONS = [
    ("trade",     SCENES["trade"],     "Соода-сатык"),
    ("wholesale", SCENES.get("wholesale", SCENES["trade"]), "Соода-сатык (дүң)"),
    ("property",  SCENES.get("property", SCENES["trade"]),   "Мүлк сатуу"),
    ("service",   SCENES["service"],   "Кызмат көрсөтүү"),
    ("rental",    SCENES["rental"],    "Ижарага берүү"),
    ("delivery",  SCENES["delivery"],  "Жеткирүү"),
    ("cargo",     SCENES.get("cargo", SCENES["delivery"]), "Жүк ташуу"),
    ("jobseek",   SCENES.get("jobseek", SCENES["job"]),    "Жумуш издөө"),
    ("job",       SCENES["job"],       "Жумуш берүү"),
    ("markets",   SCENES["markets"],   "Базарлар"),
    ("malls",     SCENES.get("malls", SCENES["markets"]),
     "Соода борборлору"),
    ("taxi",      SCENES["taxi"],      "Такси"),
]

# Жаңы бөлүмдөрдүн аттары (strings.py'де али жок)
_NEW_SECTION_NAMES = {
    "wholesale": ("Соода-сатык (дүң)", "Оптовая торговля"),
    "property":  ("Мүлк сатуу", "Продажа имущества"),
    "cargo":     ("Жүк ташуу", "Грузоперевозки"),
    "jobseek":   ("Жумуш издөө", "Поиск работы"),
    "malls":     ("Соода борборлору", "Торговые центры"),
}

SECTION_CODES = [c for c, _, _ in SECTIONS]
SECTION_NAME = {code: name for code, _, name in SECTIONS}

_CAT_LISTS = {
    "trade":    TRADE_CATEGORIES,
    "property": PROPERTY_CATEGORIES,
    "service":  SERVICE_CATEGORIES,
    "rental":   RENTAL_CATEGORIES,
    "delivery": DELIVERY_CATEGORIES,
    "job":      JOB_CATEGORIES,
    "markets":  MARKETS_TYPES,
    "malls":    MALLS_TYPES,
    "wholesale": WHOLESALE_CATEGORIES,
    "cargo":     CARGO_CATEGORIES,
    "jobseek":   JOBSEEK_CATEGORIES,
}


def _ky(text, lang="ky"):
    """
    Эки тилдүү жазуунун керектүү бөлүгү.

    «А / Б» түрүндөгү жазуудан тилге ылайыгын алат. Базадан келген
    жалаң кыргызча маани болсо (жарыя коюлганда кыргызчасы гана
    сакталат), каталогдон курулган сөздүк аркылуу которобуз —
    антпесе орусча бетте кыргызча сөздөр аралашып калат.
    """
    out = L(text, lang)
    return bridge.ru_value(out, lang) if lang == "ru" else out


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
    if code in _NEW_SECTION_NAMES:
        ky_name, ru_name = _NEW_SECTION_NAMES[code]
        return ru_name if lang == "ru" else ky_name
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
 window.tapGo=function(e,b){
   e.preventDefault(); e.stopPropagation();
   window.open(b.dataset.u,"_blank","noopener");
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
 var ob=b.parentNode.getAttribute("data-ob")||"";
 fetch("/api/ads?at="+encodeURIComponent(sec)+"&cid="+encodeURIComponent(cid)
       +"&ob="+encodeURIComponent(ob))
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


# Сүрөтү жок жарыялар: бөлүмдүн белгиси, астында категориянын аты.
EXTRA_CSS = """
.ph i.nph,.dph i.nph{width:100%;height:100%;opacity:1}
.ph .nph{display:flex;flex-direction:column;align-items:center;justify-content:center;
gap:7px;width:100%;height:100%;padding:10px;text-align:center;font-style:normal;
background:linear-gradient(160deg,#F6F9FD 0%,#E4ECF8 100%)}
.ph .nph .nphi{display:block;width:46px;height:46px}
.ph .nph .nphi svg{width:100%;height:100%;display:block}
.ph .nph em{font-style:normal;font-size:11.5px;font-weight:700;line-height:1.3;
color:#1B3355;width:100%;max-height:2.6em;overflow:hidden;display:block}
.nphw{position:absolute;inset:0;display:block;background:#E9EFF9}
.nphw .nphp{position:absolute;inset:0;width:100%;height:100%;
object-fit:contain;object-position:center;display:block}
.dph .nphw{position:relative;width:100%;height:150px;flex:1 0 100%}
.dph .nphw .nphp{height:100%}
.cap{position:absolute;left:8px;right:8px;bottom:8px;z-index:2;
display:flex;align-items:center;justify-content:center;gap:6px;
padding:6px 10px;border-radius:12px;background:rgba(16,28,48,.72);
color:#fff;font-size:11.5px;font-weight:700;line-height:1.2;text-align:center;
backdrop-filter:blur(3px)}
.dph .cap{font-size:13px;padding:6px 12px;left:auto;right:auto;bottom:10px;
width:max-content;max-width:80%;margin:0 auto;transform:translateX(-50%);left:50%}
.dph .nph{min-height:190px}
.dph .nph .nphi{width:76px;height:76px}
.dph .nph em{font-size:14px}
"""


# ── Телефонго кошулуучу колдонмо (PWA) ────────────────────────
# Браузерден «Башкы экранга кошуу» дегенде, сайт өзүнчө тиркеме болуп
# ачылат: браузердин дарек сабы көрүнбөйт, өз белгиси болот.
MANIFEST = {
    "name": "ТАП! — Кыргызстандагы акылдуу жарыя платформасы",
    "short_name": "ТАП!",
    "description": "Соода-сатык, кызмат, ижара, жумуш, такси — бүт Кыргызстан",
    "start_url": "/?src=pwa",
    "scope": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#F1F4F9",
    "theme_color": "#17365C",
    "lang": "ky",
    "icons": [
        {"src": "/pwa/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/pwa/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "/pwa/icon-512-mask.png", "sizes": "512x512",
         "type": "image/png", "purpose": "maskable"},
    ],
}

# Кызматчы скрипт. Тиркеме катары орнотулушу үчүн керек, ошону менен
# бирге бет ачылганда бир аз тезирээк келет.
SW_JS = """
const CACHE = 'tap-v1';
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  // Сүрөттөр менен белгилер кэштен берилет — трафик үнөмдөлөт
  if (u.pathname.startsWith('/si/') || u.pathname.startsWith('/pwa/')
      || u.pathname.startsWith('/media/')) {
    e.respondWith(caches.open(CACHE).then(c =>
      c.match(e.request).then(r => r || fetch(e.request).then(res => {
        c.put(e.request, res.clone());
        return res;
      }))));
  }
});
"""

PWA_JS = """<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/sw.js').catch(function () {});
  });
}
</script>"""


def page(body, title="ТАП!", tab="home", lang="ky"):
    return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#17365C">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="apple-touch-icon" href="/pwa/apple-180.png?v={appicon.VERSION}">
<link rel="icon" href="/pwa/icon-192.png?v={appicon.VERSION}" sizes="192x192">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="ТАП!">
<title>{esc(title)}</title>{FONTS}<style>{CSS}{EXTRA_CSS}</style></head><body>{body}{nav(tab, lang)}
{SCROLL_JS}{FAV_JS}{SHELF_JS}{PWA_JS}</body></html>"""


def _lang_switch(lang):
    """Тил алмаштыруу. Тандоо cookie'ге жазылат, ошол бойдон калат."""
    out = ""
    for code, label in (("ky", "KG"), ("ru", "RU")):
        on = " on" if lang == code else ""
        out += f'<a class="lg{on}" href="/lang/{code}" rel="nofollow">{label}</a>'
    return f'<span class="lgs">{out}</span>'


# Аймактын атын кыскартуу — көрүнүшкө гана. Шилтемелерде,
# базада жана издөөдө аттар толук бойдон калат.
_ABBR = [
    ("аймактык башкармалыгы", "а/б"),
    ("айыл аймагы", "а/а"),
    ("кичи району", "к/р-н"),
    ("кичи район", "к/р-н"),
    ("облусу", "обл."),
    ("району", "р-н"),
    ("шаары", "ш."),
    ("айылы", "а."),
    ("область", "обл."),
    ("район", "р-н"),
    ("город", "г."),
]

_ABBR_CSS = """<style>
.rnote{font-size:12px;line-height:1.4;color:var(--faint);
       margin:-2px 4px 10px;padding:0 2px}
.rg em,.sb2 em{font-style:normal;font-weight:600;opacity:.6;
               margin-left:3px}
</style>"""


def _price(price, lang):
    """Баа. Келишим болсо, тандалган тилде жазылат."""
    if is_deal(price):
        # «Келишим баада» деген маани базада кыргызча турат
        return "Договорная цена" if lang == "ru" else "Келишим баада"
    return price_label(price)


def _place_name(name, lang):
    """
    Аймактын аты тандалган тилде. Орусча аты табылбаса,
    кыргызчасы калат — эч нерсе жоголбойт.
    """
    s = L(str(name or ""), lang)
    if lang == "ru":
        try:
            got = ru_name(s) or ru_name(str(name or ""))
        except Exception:
            got = ""
        if got:
            s = got
    return s


def _short_place(name):
    """«Жалал-Абад облусу» → «Жалал-Абад обл.»"""
    s = str(name or "").strip()
    for pref, short in (("город ", "г. "), ("село ", "с. "),
                        ("посёлок ", "пос. "), ("поселок ", "пос. ")):
        if s.lower().startswith(pref):
            return short + s[len(pref):]
    low = s.lower()
    for full, short in _ABBR:
        i = low.rfind(full)
        if i >= 0 and (i + len(full)) >= len(low) - 1:
            return (s[:i].strip() + " " + short).strip()
    return s


def _place_note(lang):
    """Кыскартуулардын түшүндүрмөсү."""
    if lang == "ru":
        txt = "обл. — область · р-н — район · г. — город"
    else:
        txt = ("обл. — облус · р-н — район · ш. — шаар · "
               "к/р-н — кичи район · а/а — айыл аймагы · а. — айыл")
    return f'<p class="rnote">{esc(txt)}</p>' + _ABBR_CSS


_EMPTY = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
          'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
          '<circle cx="10.5" cy="10.5" r="7"/><path d="m15.6 15.6 5.4 5.4"/></svg>')

def header(q="", at=None, reg=None, lang="ky"):
    hidden = f'<input type="hidden" name="at" value="{esc(at)}">' if at else ""
    return f"""<header class="top"><div class="wrap">
<div class="tin"><a href="/" class="logo"><span>ТАП!</span></a>
<span class="pin"><b>&#9679;</b>{esc(_short_place(_place_name(reg, lang)) if reg else T("all_kg", lang))}</span>
{_lang_switch(lang)}</div>
<form class="s" action="/">{hidden}
<span class="mg">{_EMPTY}</span>
<input type="search" name="q" value="{esc(q)}" placeholder="{T("search_ph", lang)}">
<button>{T("search_btn", lang)}</button></form></div></header>"""


_NOPHOTO = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
            '<rect x="3" y="5" width="18" height="14" rx="2.6"/>'
            '<circle cx="8.5" cy="10" r="1.8"/>'
            '<path d="m3.5 17 5-4.6 3.4 3 3.6-3.4 5 5"/></svg>')

_EYE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9">'
        '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/>'
        '<circle cx="12" cy="12" r="3.1"/></svg>')


def ph_name(r, lang="ky"):
    """Сүрөт жок болгондо анын ордуна чыгуучу категориянын аты."""
    at = r.get("ad_type")
    if at:
        nm = cat_label(at, r.get("cat_id"), lang) if r.get("cat_id") else ""
        if nm:
            return nm
        return section_name(at, lang)
    nm, _e = CATS.get(r.get("category"), ("", ""))
    return nm or ""


def ph_sub(r, lang="ky"):
    """Сүрөт жок болгондо чыгуучу субкатегориянын аты."""
    if r.get("sub_id"):
        return _ky(r["sub_id"], lang)
    if not r.get("ad_type"):
        try:
            return sub_title(r.get("category"), r.get("subcat")) or ""
        except Exception:
            return ""
    return ""


def ph_place(r, lang="ky"):
    """Сүрөт жок болгондо чыгуучу аймак: облус · район · айыл."""
    parts = []
    for key in ("oblast", "district", "locality", "village"):
        v = str(r.get(key) or "").strip()
        if not v or v in parts:
            continue
        parts.append(v)
    if not parts:
        v = str(r.get("region") or "").strip()
        if v:
            parts.append(v)
    out = [_short_place(_place_name(x, lang)) for x in parts]
    return " · ".join([x for x in out if x])


def ph_block(r, lang="ky"):
    """
    Сүрөтү жок жарыянын ордуна: бөлүмдүн белгиси, астында категориянын аты.

    Аймак бул жерде жазылбайт — ал жарыянын өз барагында турат, ал эми
    карточкада аталыш менен баа маанилүүрөөк.
    """
    at = r.get("ad_type")
    # Бөлүмдүн сүрөтү бар болсо, ошол коюлат — аты сүрөттүн өзүндө жазылган
    if at and secimg.has(at):
        nm = esc(section_name(at, lang))
        return (f'<span class="nphw"><img class="nphp" '
                f'src="/si/{at}.jpg?v={secimg.VERSION}" alt="{nm}" loading="lazy">'
                f'<span class="cap">{nm}</span></span>')
    ic = ICONS.get(at) or ICONS["all"]
    nm = section_name(at, lang) if at else ph_name(r, lang)
    lbl = f"<em>{esc(nm)}</em>" if nm else ""
    return f'<i class="nph"><span class="nphi">{ic}</span>{lbl}</i>'


def _reg_lines(r, lang="ky"):
    """
    Карточкадагы аймак: үстүндө облус · район, астында айыл аймагы · айыл.
    Аттар кыскартылат, бош тепкичтер таптакыр жазылбайт.
    """
    def sh(x):
        x = str(x or "").strip()
        return _short_place(_place_name(x, lang)) if x else ""

    top = " · ".join([x for x in (sh(r.get("oblast")), sh(r.get("district"))) if x])
    low = " · ".join([x for x in (sh(r.get("locality")), sh(r.get("village"))) if x])
    if not top and not low:
        top = sh(r.get("region"))
    out = ""
    if top:
        out += f'<div class="rg">{esc(top)}</div>'
    if low:
        out += f'<div class="rg rg2">{esc(low)}</div>'
    return out


_CWA = ('<svg viewBox="0 0 32 32">'
        '<circle cx="16" cy="16" r="16" fill="#25D366"/>'
        '<path fill="#fff" d="M16 7a9 9 0 0 0-7.8 13.4L7 25l4.8-1.2A9 9 0 1 0 16 7Z'
        'm5.2 12.6c-.2.6-1.2 1.1-1.7 1.2-.4 0-1 .2-3.2-.7-2.7-1.1-4.4-3.8-4.5-4'
        '-.1-.2-1-1.4-1-2.6 0-1.3.7-1.9 1-2.2.2-.2.5-.3.7-.3h.5c.2 0 .4 0 .6.5'
        'l.8 2c.1.2.1.4 0 .5l-.3.4-.3.3c-.1.1-.2.3-.1.5.2.4.9 1.4 1.9 2.3 1.3 1.1'
        ' 2.3 1.5 2.7 1.6.2.1.4.1.5-.1l1-1.1c.2-.2.4-.2.6-.1l2.1 1c.2.1.3.2.4.3'
        '.1.2 0 .7-.2 1.2Z"/></svg>')

_CTG = ('<svg viewBox="0 0 32 32">'
        '<circle cx="16" cy="16" r="16" fill="#229ED9"/>'
        '<path fill="#fff" d="M23.8 9.6 8.9 15.4c-.9.4-.9.9-.2 1.1l3.8 1.2 1.4 4.3'
        'c.2.4.3.6.7.6.3 0 .5-.1.7-.4l1.8-1.7 3.7 2.7c.7.4 1.2.2 1.4-.6l2.5-11.6'
        'c.2-1-.4-1.4-1-1.2Zm-3 2.7-6.5 5.8-.3 2.7-1.2-3.6 8-4.9Z"/></svg>')


def _intl(raw):
    """Байланыш номерин 996XXXXXXXXX түрүнө келтирет. Болбосо бош."""
    d = "".join(c for c in str(raw or "") if c.isdigit())
    if d.startswith("996"):
        d = d[3:]
    if len(d) == 10 and d.startswith("0"):
        d = d[1:]
    return ("996" + d) if len(d) == 9 else ""


def _src(r):
    """Жарыянын булагы: tg / wa / "" (белгисиз)."""
    u = str(r.get("tg_id") or "").strip().lower()
    if not u:
        return ""
    if "@" in u or u.startswith("wa"):
        return "wa"
    d = u.lstrip("-")
    if d.isdigit():
        if len(d) == 12 and d.startswith("996"):
            return "wa"
        return "tg"
    return ""


def _cta(r):
    """Карточкадагы баскыч: жарыя кайдан коюлса ошол. #SRC_CTA"""
    intl = _intl(r.get("contact"))
    if not intl:
        return ""
    wa = ('<button class="cta wa" onclick="tapGo(event,this)"'
          ' data-u="https://wa.me/%s" aria-label="WhatsApp">%s</button>'
          % (intl, _CWA))
    tg = ('<button class="cta tg" onclick="tapGo(event,this)"'
          ' data-u="https://t.me/+%s" aria-label="Telegram">%s</button>'
          % (intl, _CTG))
    src = _src(r)
    if src == "tg":
        return tg
    if src == "wa":
        return wa
    return wa + tg


def _sago(ts, lang="ky"):
    """Карточка үчүн кыска убакыт: «мурун/назад» жок. #SAGO"""
    t = ago(ts, lang)
    for w in (" мурун", " назад"):
        if t.endswith(w):
            return t[:-len(w)]
    return t


def card(r, lang="ky"):
    has = bool(r.get("photo"))
    img = (f'<img src="/media/{esc(r["photo"])}" alt="" loading="lazy">'
           if has else
           ph_block(r, lang))
    return f"""<a class="c{'' if has else ' nophoto'}" href="/e/{r['id']}">
<div class="ph">{img}<button class="fav" data-id="{r['id']}" aria-label="Тандалганга кошуу">{NAV_ICONS['fav']}</button></div>
<div class="cb"><div class="p{' pd' if is_deal(r['price']) else ''}">{esc(_price(r['price'], lang))}</div>
{_reg_lines(r, lang)}
<h2 class="t">{esc(L(bridge.show_title(r), lang))}</h2>
<div class="m"><span>{esc(_sago(r['created_at'], lang))}</span>{'<span class="vmark">🎬</span>' if core.video_of(r) else ''}
<span class="vw">{_EYE}{r['views']}</span>{_cta(r)}</div>
</div></a>"""


def _by_count(items, counts):
    """Жарыясы барлар алдыда, «0» болгондор артында — өз ара тартиби сакталат."""
    order = {x: i for i, x in enumerate(items)}
    return sorted(items, key=lambda x: (0 if counts.get(x, 0) else 1, order[x]))


def _chip(href, label, on, n=0, lang="ky", short=True):
    """Аймактын баскычы. Жарыясы бар болсо санын көрсөтөт."""
    text = _place_name(label, lang) if short else L(str(label), lang)
    if short:
        text = _short_place(text)
    num = f' <em>{n}</em>' if n else ""
    cls = "rg on" if on else "rg"
    return f'<a href="{href}" class="{cls}">{esc(text)}{num}</a>'


def _sel(label, opts, cur):
    """
    Тандоо тизмеси. Ар бир сабында өзүнүн шилтемеси турат —
    тандаганда бет ошол шилтемеге өтөт, «Изде» басуунун кереги жок.
    """
    o = ""
    for val, href, text, n in opts:
        num = f" ({n})" if n is not None else ""
        on = " selected" if val == cur else ""
        o += f'<option value="{esc(href)}"{on}>{esc(text)}{num}</option>'
    cls = "sel set" if cur else "sel"
    return (f'<div class="ff"><label>{esc(label)}</label>'
            f'<select class="{cls}" onchange="location=this.value">{o}</select></div>')


def _group(title, inner):
    return f'<div class="fbox"><div class="fhd">{esc(title)}</div>{inner}</div>'


_TILES_CSS = """<style>
.ctiles{display:flex;gap:10px;overflow-x:auto;padding:10px 14px 14px;
 scrollbar-width:none;max-width:1040px;margin:0 auto}
.ctiles::-webkit-scrollbar{display:none}
.ct{flex:none;width:104px;text-decoration:none;color:inherit}
.ct .cti{position:relative;width:104px;height:104px;border-radius:14px;
 overflow:hidden;background:#E9EFF9;border:1px solid var(--mist)}
.ct .cti img{width:100%;height:100%;object-fit:cover;display:block}
.ct .ctn{position:absolute;left:6px;bottom:6px;background:rgba(21,39,65,.82);
 color:#fff;font-size:11px;font-weight:700;padding:2px 7px;border-radius:9px}
.ct .ctl{margin-top:6px;font-size:12.5px;font-weight:600;line-height:1.25;
 text-align:center;display:-webkit-box;-webkit-line-clamp:2;
 -webkit-box-orient:vertical;overflow:hidden;min-height:2.5em}
.ct.on .cti{border-color:var(--moss);box-shadow:0 0 0 2px var(--moss)}
.ct .cte{display:flex;align-items:center;justify-content:center;
 width:100%;height:100%;color:#8FA3C0;
 background:linear-gradient(160deg,#F6F9FD,#E4ECF8)}
.ct .cte svg{width:34px;height:34px}
</style>"""


def cat_tiles(at, cid, ob, lang):
    """Бөлүмдүн категориялары — сүрөттүү такта.

    Сүрөт кол менен коюлбайт: ар бир категориядагы эң жаңы жарыянын
    биринчи сүрөтү алынат. Жарыясы же сүрөтү жок болсо, жалпы белги.
    """
    try:
        counts = core.catid_counts(at, oblast=ob)
    except Exception:
        return ""
    if len(counts) < 2:
        return ""

    out = ""
    for c, n in sorted(counts.items(), key=lambda x: -x[1])[:14]:
        pic = ""
        try:
            top = core.find(limit=1, ad_type=at, cat_id=c, oblast=ob)
            if top and top[0].get("photo"):
                pic = f'<img src="/media/{esc(top[0]["photo"])}" alt="" loading="lazy">'
        except Exception:
            pass
        if not pic:
            pic = f'<span class="cte">{NAV_ICONS["grid"]}</span>'
        on = " on" if cid == c else ""
        href = f"/?at={at}&cid={esc(c)}{_obq(ob)}"
        out += (f'<a class="ct{on}" href="{href}">'
                f'<div class="cti">{pic}<span class="ctn">{n}</span></div>'
                f'<div class="ctl">{esc(cat_label(at, c, lang))}</div></a>')
    return _TILES_CSS + f'<nav class="ctiles">{out}</nav>'


def _filter_bars(link, q, at, cid, sid, ob, di, vi, lang, sort="new"):
    """Бөлүм жана аймак чыпкалары — тандоо тизмелери менен."""
    ru = (lang == "ru")
    flt = {"q": q or None, "ad_type": at, "cat_id": cid, "sub_id": sid}
    out = ""

    # ── Эмне издеп жатасыз: категория → субкатегория ──────────
    if at:
        cc = core.catid_counts(at, ob, di, vi, q or None, sid)
        items = list(cat_labels(at, lang).items())
        items.sort(key=lambda x: (-cc.get(x[0], 0), x[1]))
        opts = [(None, link(cid=None, sid=None),
                 "Все" if ru else "Баары", sum(cc.values()))]
        for code, nm in items:
            opts.append((code, link(cid=code, sid=None), nm, cc.get(code, 0)))
        inner = _sel("Категория", opts, cid)

        if cid:
            sc = core.subid_counts(at, cid, ob, di, vi, q or None)
            whole = "Вся категория" if ru else "Бүт категория"
            opts = [(None, link(sid=None), whole, None)]
            for code, n in sorted(sc.items(), key=lambda x: (-x[1], x[0])):
                opts.append((code, link(sid=code), _ky(code, lang), n))
            if len(opts) > 1:
                inner += _sel("Субкатегория", opts, sid)

        out += _group("Что вы ищете" if ru else "Эмне издеп жатасыз", inner)

    # ── Кайсы жерден: облус → район → айыл ────────────────────
    oc = core.oblast_counts(**flt)
    opts = [(None, link(ob=None, di=None, vi=None), T("all_kg", lang),
             sum(oc.values()))]
    for rg in _by_count(list(OBLASTS), oc):
        opts.append((rg, link(ob=rg, di=None, vi=None),
                     _place_name(rg, lang), oc.get(rg, 0)))
    inner = _sel("Область · город" if ru else "Облус · шаар", opts, ob)

    if ob:
        dc = core.district_counts(ob, **flt)
        ds = list(get_districts(ob)) or core.used_districts(ob)
        if ds:
            # Бишкек менен Ош — республикалык маанидеги шаарлар,
            # аларда «облус» эмес, «шаар» деп жазылат.
            city = "шаар" in str(ob).lower() or "город" in str(ob).lower()
            if city:
                whole = "Весь город" if ru else "Бүт шаар"
                lbl = "Район города" if ru else "Шаардын району"
            else:
                whole = T("all_oblast", lang)
                lbl = "Район · город" if ru else "Район · шаар"
            opts = [(None, link(di=None, vi=None), whole, None)]
            for x in _by_count(list(ds), dc):
                opts.append((x, link(di=x, vi=None),
                             _place_name(x, lang), dc.get(x, 0)))
            inner += _sel(lbl, opts, di)

    if ob and di:
        vc = core.village_counts(ob, di, **flt)
        vs = list(get_localities(ob, di)) or core.used_villages(ob, di)
        if vs:
            whole = "Весь район" if ru else "Бүт район"
            opts = [(None, link(vi=None), whole, None)]
            for x in _by_count(list(vs), vc):
                opts.append((x, link(vi=x), _place_name(x, lang), vc.get(x, 0)))
            inner += _sel("Айыльный округ · село" if ru else "Айыл аймагы · айыл",
                          opts, vi)

    out += _group("Откуда" if ru else "Кайсы жерден", inner)

    # ── Тартиби: жаңысынан, арзандан, кымбаттан ───────────────
    names = ([("new", "Сначала новые"), ("cheap", "Сначала дешёвые"),
              ("rich", "Сначала дорогие"), ("views", "Популярные")] if ru else
             [("new", "Жаңысынан"), ("cheap", "Арзандан"),
              ("rich", "Кымбаттан"), ("views", "Көп көрүлгөн")])
    opts = [(code, link(sort=code), nm, None) for code, nm in names]
    inner = _sel("Сортировка" if ru else "Тартиби", opts, sort or "new")
    out += _group("Как показать" if ru else "Кантип көрсөтүү", inner)
    # Тандалган бөлүмдүн түсү фильтр полосаларына өтсүн
    return f'<div class="fsec s-{at}">{out}</div>' if at else out


def _sections_strip(link, at, lang, ob=None):
    """
    Бөлүм такталары. Сүрөтү бар бөлүмдө сүрөт бүт тактаны ээлейт (аты
    сүрөттүн өзүндө жазылган), сүрөтү жогунда мурункудай белги чыгат.

    Аймак тандалганда ар бир бөлүмдүн жанында ошол аймактагы
    жарыялардын саны чыгат.
    """
    ac = {}
    if ob:
        try:
            ac = core.adtype_counts(ob)
        except Exception:
            ac = {}

    def _n(code):
        """Бөлүмдүн жанындагы сан (аймак тандалганда гана)."""
        if not ob:
            return ""
        return f'<span class="secn">{ac.get(code, 0)}</span>'

    if secimg.has("all"):
        cats = (f'<a href="{link(at=None, cid=None)}" '
                f'class="cat pic s-all{"" if at else " on"}">'
                f'<span class="picw">'
                f'<img class="pic" src="/si/all.jpg?v={secimg.VERSION}" '
                f'alt="{T("all", lang)}"></span>'
                f'{f"<span class=\'secn\'>{sum(ac.values())}</span>" if ob else ""}'
                f'<span class="pill">{T("all", lang)}</span></a>')
    else:
        cats = (f'<a href="{link(at=None, cid=None)}" class="cat{"" if at else " on"}">'
                f'<span class="ic">{SCENES["all"]}</span>'
                f'<span class="lb">{T("all", lang)}</span></a>')
    for code, ic, _name in SECTIONS:
        on = " on" if at == code else ""
        if secimg.has(code):
            nm = esc(section_name(code, lang))
            # Сүрөт өз алкагынын ичинде акырын жылып турат, ошондуктан
            # аны кыркып туруучу кабыкка ороп коёбуз.
            inner = (f'<span class="picw">'
                     f'<img class="pic" src="/si/{code}.jpg?v={secimg.VERSION}" '
                     f'alt="{nm}" loading="lazy"></span>{_n(code)}'
                     f'<span class="pill">{nm}</span>')
            cls = f"cat pic s-{code}{on}"
        else:
            inner = (f'<span class="ic">{ic}</span>{_n(code)}'
                     f'<span class="lb">{esc(section_name(code, lang))}</span>')
            cls = f"cat{on}"
        cats += f'<a href="{link(at=code, cid=None)}" class="{cls}">{inner}</a>'
    return f'<nav class="cats">{cats}</nav>'


def _obq(ob):
    """Шилтемеге «&ob=…» кошот (аймак тандалган болсо)."""
    return ("&" + urllib.parse.urlencode({"ob": ob})) if ob else ""


def _regions_strip(link, ob, lang, at=None, q=None):
    """
    Облустар менен республикалык шаарлар — горизонталдуу тилке.
    Бирөөнү баскандан кийин бүт бет ошол аймакка өтөт.

    Сандар учурдагы бөлүмдү жана издөө сөзүн эсепке алат — ошондуктан
    тилкедеги сан менен экрандагы тизме дал келет.
    """
    try:
        oc = core.oblast_counts(ad_type=at, q=q or None)
    except Exception:
        oc = {}
    out = _chip(link(ob=None, di=None, vi=None), T("all_kg", lang),
                not ob, 0, lang, short=False)
    for rg in _by_count(list(OBLASTS), oc):
        out += _chip(link(ob=rg, di=None, vi=None), rg,
                     ob == rg, oc.get(rg, 0), lang)
    return f'<nav class="regbar">{out}</nav>'


def shelves(lang="ky", ob=None):
    """
    Башкы бет: ар бир бөлүм өзүнчө катар болуп турат, жарыялары оңго-солго
    сүрүлөт. Категория чиптерин басканда ошол катардын ичи алмашат —
    бет кайра жүктөлбөйт.
    """
    out = []
    for code, _ic, _n in SECTIONS:
        rows = core.find(limit=12, ad_type=code, oblast=ob)
        if not rows:
            continue
        cc = core.catid_counts(code, oblast=ob)
        chips = (f'<button class="sb2 on" data-sec="{code}" data-cid="">'
                 f'{T("all", lang)}</button>')
        for cid, n in sorted(cc.items(), key=lambda x: -x[1])[:12]:
            chips += (f'<button class="sb2" data-sec="{code}" data-cid="{esc(cid)}">'
                      f'{esc(cat_label(code, cid, lang))} <em>{n}</em></button>')
        out.append(
            f'<section class="shelf" id="sh-{code}">'
            f'<div class="shead"><h2>{esc(section_name(code, lang))}</h2>'
            f'<a href="/?at={code}{_obq(ob)}" class="more">'
            f'{T("show_all", lang)} ›</a></div>'
            f'<nav class="subbar shchips" data-ob="{esc(ob or "")}">{chips}</nav>'
            f'<div class="srow" id="row-{code}">'
            f'{"".join(card(r, lang) for r in rows)}</div></section>')
    return "".join(out)


def home(q, at=None, cid=None, sid=None, ob=None, di=None, vi=None,
         lang="ky", sort="new"):
    """
    Башкы бет.
      at  — бөлүм (trade/service/…)
      cid — бөлүмдүн ичиндеги категория
      ob  — облус,  di — район
    Эч кандай чыпка жок болсо — бөлүмдөр катар-катар болуп көрүнөт.
    """
    def link(**kw):
        """Учурдагы чыпкаларды сактап, бирөөнү гана өзгөрткөн шилтеме."""
        prm = {"q": q or None, "at": at, "cid": cid, "sid": sid,
               "ob": ob, "di": di, "vi": vi,
               "sort": (sort if sort and sort != "new" else None)}
        prm.update(kw)
        prm = {k: v for k, v in prm.items() if v}
        return ("/?" + urllib.parse.urlencode(prm)) if prm else "/"

    top = (header(q, at, vi or di or ob, lang)
           + _sections_strip(link, at, lang, ob)
           + _regions_strip(link, ob, lang, at, q))

    # Бөлүм/категория/издөө жок — катар-катар тизме.
    # Аймак гана тандалса, ошол аймактын ичинде катарлар көрүнөт.
    if not (q or at or cid or sid or di or vi):
        return page(top + f'<main class="wrap">{shelves(lang, ob)}</main>',
                    "ТАП!", "home", lang)

    rows = core.find(q, limit=60, ad_type=at, cat_id=cid, sub_id=sid,
                     oblast=ob, district=di, village=vi, sort=sort)
    body = ((cat_tiles(at, cid, ob, lang) if at and not q else "")
            + _filter_bars(link, q, at, cid, sid, ob, di, vi, lang, sort))

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


def contact_block(raw, lang="ky", title="", url=""):
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

    # Даяр биринчи кабар — сатып алуучу эмне жазаарын ойлонбосун
    wa_msg = tg_msg = tg_ok = ""
    if title:
        greet = ("Здравствуйте! Ваше объявление «%s» на ТАП! ещё актуально?"
                 if lang == "ru" else
                 "Салам! ТАП!теги «%s» жарыяңыз актуалдуубу?") % title
        if url:
            greet += "\n" + url
        wa_msg = "?text=" + urllib.parse.quote(greet)
        tg_msg = esc(greet)
        tg_ok = esc("Текст скопирован — вставьте в чат" if lang == "ru"
                    else "Текст көчүрүлдү — чатка коюңуз")
    else:
        tg_msg = tg_ok = ""
    return f"""<div class="cnum">{esc(shown)}</div>
<div class="cbar">
<a class="cb1 call" href="tel:+{intl}">{_PHONE}<span>{T("c_call", lang)}</span></a>
<a class="cb1 wa" href="https://wa.me/{intl}{wa_msg}" target="_blank" rel="noopener">
{_WA}<span>WhatsApp</span></a>
<a class="cb1 tg" href="https://t.me/+{intl}" target="_blank" rel="noopener"
 onclick="tapCopy(this)" data-m="{tg_msg}" data-ok="{tg_ok}">
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
_SHARE_ICON = ('<svg viewBox="0 0 24 24"><circle cx="18" cy="5.2" r="2.6"/>'
               '<circle cx="6" cy="12" r="2.6"/><circle cx="18" cy="18.8" r="2.6"/>'
               '<path d="M8.3 10.8 15.7 6.5M8.3 13.2l7.4 4.3"/></svg>')

_SHARE_BTN_CSS = """<style>
.shbtn{position:absolute;top:12px;right:12px;z-index:4;width:44px;height:44px;
 border:0;border-radius:50%;background:rgba(255,255,255,.94);padding:0;
 box-shadow:0 2px 10px rgba(10,25,50,.25);display:flex;cursor:pointer;
 align-items:center;justify-content:center}
.shbtn svg{width:22px;height:22px;stroke:#3F4E68;fill:none;stroke-width:1.9;
 stroke-linecap:round;stroke-linejoin:round}
.shbtn:active{transform:scale(.92)}
.dfav{top:12px;right:64px;width:44px;height:44px;z-index:4;
 box-shadow:0 2px 10px rgba(10,25,50,.25)}
.dfav svg{width:22px;height:22px}
.shok{position:fixed;left:50%;bottom:88px;transform:translateX(-50%);z-index:60;
 background:#17365C;color:#fff;padding:10px 18px;border-radius:20px;
 font-size:14px;box-shadow:0 6px 18px rgba(10,25,50,.3)}
</style><script>
function tapCopy(a){
  var m=a.dataset.m;
  if(!m) return;
  try{
    if(navigator.clipboard){ navigator.clipboard.writeText(m); }
    else{
      var i=document.createElement("textarea");
      i.value=m; document.body.appendChild(i); i.select();
      document.execCommand("copy"); i.remove();
    }
  }catch(e){}
  var n=document.createElement("div");
  n.className="shok";
  n.textContent=a.dataset.ok||"";
  document.body.appendChild(n);
  setTimeout(function(){ n.remove(); }, 2200);
}

function tapShare(b){
  var u=b.dataset.u, t=b.dataset.t||"";
  if(navigator.share){
    navigator.share({title:t, text:t, url:u}).catch(function(){});
    return;
  }
  function done(){
    var n=document.createElement("div");
    n.className="shok";
    n.textContent=b.dataset.ok||"OK";
    document.body.appendChild(n);
    setTimeout(function(){ n.remove(); }, 1800);
  }
  if(navigator.clipboard){ navigator.clipboard.writeText(u).then(done, done); }
  else{
    var i=document.createElement("input");
    i.value=u; document.body.appendChild(i); i.select();
    try{ document.execCommand("copy"); }catch(e){}
    i.remove(); done();
  }
}
</script>"""

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
/* __TAP_GAL_V2__ */
(function(){
  function init(){
    var g=document.getElementById("pgal"), c=document.getElementById("pgc");
    if(!g||!c) return;
    var n=g.children.length;
    if(n<2) return;
    function step(){
      var a=g.children[0], b=g.children[1];
      var s=b.offsetLeft-a.offsetLeft;
      return s>0 ? s : (g.clientWidth||1);
    }
    var t=null;
    function upd(){
      var i=Math.round(g.scrollLeft/step())+1;
      if(i<1) i=1;
      if(i>n) i=n;
      c.textContent=i+" / "+n;
    }
    g.addEventListener("scroll", function(){
      if(t) return;
      t=requestAnimationFrame(function(){ t=null; upd(); });
    }, {passive:true});
    window.addEventListener("resize", upd, {passive:true});
    upd();
  }
  if(document.readyState==="loading")
    document.addEventListener("DOMContentLoaded", init);
  else
    init();
})();
</script>"""


# ── Жарыянын барагындагы саптардын белгилери ───────────────────
_FI = {
 "pin": '<path d="M12 21s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11Z"/>'
        '<circle cx="12" cy="10" r="2.6"/>',
 "bag": '<rect x="3" y="7" width="18" height="13" rx="2.5"/>'
        '<path d="M8 7V5.5A2.5 2.5 0 0 1 10.5 3h3A2.5 2.5 0 0 1 16 5.5V7"/>',
 "van": '<path d="M3 7h11v9H3z"/><path d="M14 10h4l3 3v3h-7z"/>'
        '<circle cx="7" cy="18" r="1.8"/><circle cx="17" cy="18" r="1.8"/>',
 "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5.5l3.5 2"/>',
 "cal": '<rect x="3" y="5" width="18" height="16" rx="2.5"/>'
        '<path d="M3 10h18M8 3v4M16 3v4"/>',
 "eye": '<path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6S2 12 2 12Z"/>'
        '<circle cx="12" cy="12" r="3"/>',
 "tag": '<path d="M4 4h7l9 9-7 7-9-9V4Z"/><circle cx="8.5" cy="8.5" r="1.6"/>',
 "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.6v.1"/>',
 "user": '<circle cx="12" cy="8" r="3.6"/>'
         '<path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>',
 "sect": '<rect x="3" y="6" width="18" height="14" rx="2.5"/>'
         '<path d="M3 10h18M9 6V4h6v2"/>',
 "cat":  '<path d="M4 4h7l9 9-7 7-9-9V4Z"/><circle cx="8.5" cy="8.5" r="1.6"/>',
 "sub":  '<path d="M4 11 12 4l8 7v8a1.6 1.6 0 0 1-1.6 1.6H5.6A1.6 1.6 0 0 1 4 19v-8Z"/>',
 "city": '<path d="M4 21V8l6-4v17M14 21V11l6 3v7"/><path d="M3 21h18"/>',
}

# Сүрөттөмөдөгү «Аты: мааниси» саптарына кайсы белги туура келет
_FKEY = (
    (("жеткир", "доставк"), "van"),
    (("чалуу", "звон", "убак", "врем"), "clock"),
    (("мөөнөт", "срок"), "cal"),
    (("сатуу", "продаж", "чекене", "опт"), "bag"),
    (("баа", "цена", "акы"), "tag"),
)


def _ficon(name):
    return (f'<svg viewBox="0 0 24 24">{_FI.get(name, _FI["info"])}</svg>')


# Сүрөттөмөдө сакталган кыска аталыштар бетте толук жазылат.
# (Базадагы текст өзгөрбөйт — эски жарыялар да туура көрүнөт.)
# Күндү «25-сентябрь» / «25 сентября» деп жазуу үчүн
MONTHS_GEN = [
    ("январь", "января"), ("февраль", "февраля"), ("март", "марта"),
    ("апрель", "апреля"), ("май", "мая"), ("июнь", "июня"),
    ("июль", "июля"), ("август", "августа"), ("сентябрь", "сентября"),
    ("октябрь", "октября"), ("ноябрь", "ноября"), ("декабрь", "декабря"),
]

FACT_RENAME = {
    "Мөөнөтү": ("Жарыя канча мөөнөткө жарыяланды", "Срок публикации"),
}


def _frow(icon, label, value):
    return (f'<div class="fr">{_ficon(icon)}<div class="ft">'
            f'<i>{esc(label)}</i><b>{esc(value)}</b></div></div>')


def _split_desc(text):
    """
    Сүрөттөмөнү эки бөлөт: «Аты: мааниси» саптары жана калган эркин текст.
    Ботто ушундай саптар менен жазылат, аларды өзүнчө катарга чыгарабыз.
    """
    facts, rest = [], []
    for line in str(text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip()
            if v and 1 < len(k) <= 28:
                facts.append((k, v))
                continue
        rest.append(line)
    return facts, "\n".join(rest)


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
        dimg = ph_block(r, lang)
    elif len(shots) == 1:
        dimg = f'<img src="/media/{esc(shots[0])}" alt="">'
    else:
        strip = "".join(
            f'<img src="/media/{esc(p)}" alt="" loading="lazy">'
            for p in shots)
        dimg = (_GAL_CSS + '<div class="pgal" id="pgal">' + strip
                + '</div><span class="pgc" id="pgc">1 / '
                + str(len(shots)) + '</span>')
    # Видео (бир гана). Автоматтык ойнобойт — колдонуучунун трафигин
    # аяйбыз: басканда гана жүктөлүп, ойной баштайт.
    dvid = ""  # __TAP_VID_V2__ — .dph'тан сыртта турат
    vid = core.video_of(r)
    if vid and os.path.isfile(os.path.join(MEDIA, vid)):
        vlbl = "Видео" if lang == "ru" else "Видео"
        dvid = (f'{_VID_CSS}<div class="dvid"><span class="dvl">🎬 {vlbl}'
                f'</span><video controls preload="metadata" playsinline '
                f'src="/media/{esc(vid)}"></video></div>')

    dfacts, dtext = _split_desc(r.get("description"))
    dlbl = "Описание" if lang == "ru" else "Сүрөттөмө"
    desc = (f'<div class="dcard"><div class="ft"><i>{dlbl}</i>'
            f'<b class="dtx">{esc(dtext)}</b></div></div>' if dtext else "")
    tel = contact_block(
        r.get("contact"), lang, bridge.show_title(r),
        f"{core.SITE_URL}/e/{r['id']}" if core.SITE_URL else "")

    # Бөлүшүү: WhatsApp жана Telegram аркылуу шилтемени жиберүү
    share_url = f"{core.SITE_URL}/e/{r['id']}" if core.SITE_URL else ""
    shbtn = ""
    if share_url:
        _ok = "Ссылка скопирована" if lang == "ru" else "Шилтеме көчүрүлдү"
        _al = "Поделиться" if lang == "ru" else "Бөлүшүү"
        shbtn = (_SHARE_BTN_CSS
                 + '<button class="shbtn" type="button" onclick="tapShare(this)"'
                 + ' data-u="%s" data-t="%s" data-ok="%s" aria-label="%s">'
                 % (esc(share_url), esc(bridge.show_title(r)),
                    esc(_ok), esc(_al))
                 + _SHARE_ICON + '</button>')
        _fv = "В избранное" if lang == "ru" else "Тандалганга кошуу"
        shbtn += ('<button class="fav dfav" data-id="%s" aria-label="%s">'
                  % (r["id"], esc(_fv)) + NAV_ICONS["fav"] + '</button>')
    share = ""
    if share_url:
        txt = urllib.parse.quote(f"{bridge.show_title(r)} — {share_url}")
        lb = ("Поделиться с другом" if lang == "ru"
              else "Дос менен бөлүшүү")
        share = (f'<div class="share"><span>{lb}</span>'
                 f'<a href="https://wa.me/?text={txt}" target="_blank" '
                 f'rel="noopener">WhatsApp</a>'
                 f'<a href="https://t.me/share/url?url='
                 f'{urllib.parse.quote(share_url)}" target="_blank" '
                 f'rel="noopener">Telegram</a></div>')

    ru = (lang == "ru")

    def _lb(ky, rus):
        return rus if ru else ky

    # ── Аймак эки сапта: облус/район жана кичи район/айыл ──────
    big = ", ".join([y for y in (
        _place_name(r.get("oblast"), lang) if r.get("oblast") else "",
        _place_name(r.get("district"), lang) if r.get("district") else "",
    ) if y]) or (r.get("region") or "—")
    mid = _place_name(r.get("locality"), lang) if r.get("locality") else ""
    vil = _place_name(r.get("village"), lang) if r.get("village") else ""

    rows = ""
    if r.get("tg_name"):
        rows += _frow("user", _lb("Аты", "Имя"), r["tg_name"])
    rows += _frow("pin", _lb("Аймак", "Регион"), big)
    if mid:
        rows += _frow("city",
                      _lb("Кичи район · айыл аймагы", "Микрорайон · айыльный округ"),
                      mid)
    if vil:
        rows += _frow("city", _lb("Айыл", "Село"), vil)
    rows += _frow("sect", _lb("Бөлүмү", "Раздел"), name)
    if at and r.get("cat_id"):
        rows += _frow("cat", _lb("Категориясы", "Категория"),
                      cat_label(at, r["cat_id"], lang))
    if r.get("sub_id"):
        rows += _frow("sub", _lb("Субкатегориясы", "Подкатегория"),
                      _ky(r["sub_id"], lang))

    # Сүрөттөмөдөгү «Аты: мааниси» саптары өз катары менен чыгат.
    # Субкатегория менен бирдей болгон катар кайталанбасын.
    _sub = str(_ky(r.get("sub_id") or "", lang)).strip().lower()
    for k, v in dfacts:
        if str(v).strip().lower() == _sub and _sub:
            continue
        low = k.lower()
        ic2 = "info"
        for keys, nm in _FKEY:
            if any(w in low for w in keys):
                ic2 = nm
                break
        nm = FACT_RENAME.get(k)
        rows += _frow(ic2, _lb(nm[0], nm[1]) if nm else _ky(k, lang),
                      _ky(v, lang))

    rows += _frow("cal", _lb("Жарыя жарыяланган убактысы", "Опубликовано"),
                  ago(r["created_at"], lang))
    # Мөөнөт качан бүтөрү жана канча күн калганы
    _dl = core.days_left(r.get("expires_at"))
    if _dl is not None and _dl >= 0:
        _end = str(r.get("expires_at"))[:10]
        try:
            _y, _m, _d = _end.split("-")
            _mn = MONTHS_GEN[int(_m) - 1]
            _end = ("%d %s" % (int(_d), _mn[1]) if ru
                    else "%d-%s" % (int(_d), _mn[0]))
        except Exception:
            pass
        if _dl == 0:
            _tail = "истекает сегодня" if ru else "бүгүн бүтөт"
        elif _dl == 1:
            _tail = "остался 1 день" if ru else "1 күн калды"
        else:
            _tail = ("осталось %d дн." % _dl if ru
                     else "%d күн калды" % _dl)
        rows += _frow("cal", _lb("Мөөнөтү бүтөт", "Срок истекает"),
                      "%s · %s" % (_end, _tail))

    rows += _frow("eye", _lb("Көргөндөр саны", "Количество просмотров"),
                  str(r["views"]))

    body = f"""<main class="wrap">
<a class="back" href="{back}">{_ARROW}{esc(name)}</a>
<div class="dph">{dimg}{shbtn}</div>{dvid}
<div class="dcard">
<div class="eb">{ic}{esc(sname or name)} · №{r['id']}</div>
<div class="dp{' dpd' if is_deal(r['price']) else ''}">{esc(_price(r['price'], lang))}</div>
<h1>{esc(L(bridge.show_title(r), lang))}</h1>
</div>
<div class="dcard facts">{rows}</div>{desc}{tel}{share}</main>"""
    return page(header("", None, None, lang) + body,
                L(bridge.show_title(r), lang), tab="home", lang=lang)


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


def add_page(lang="ky", task="post"):
    """
    Эки боттун бирин тандоо экраны.

    task="post" — жарыя берүү, task="my" — өз жарыяларын көрүү.
    Экөө тең бот аркылуу болот: сайтта каттоо жок, колдонуучуну
    Telegram же WhatsApp таанытат.

    WhatsApp номери WA_NUMBER өзгөрмөсүнөн алынат. Ал коюла электе
    баскыч көрүнөт, бирок басылбайт: «жакында» деп турат.
    """
    ru = (lang == "ru")
    wa_num = "".join(c for c in os.environ.get("WA_NUMBER", "") if c.isdigit())
    mine = (task == "my")
    bal = (task == "balance")

    if bal:
        head = "Мой баланс" if ru else "Менин балансым"
        lead = ("Баланс хранится в боте — выберите, где вам удобнее."
                if ru else
                "Баланс ботто турат — кайсынысы ыңгайлуу болсо, "
                "ошону тандаңыз.")
    elif mine:
        head = "Мои объявления" if ru else "Менин жарыяларым"
        lead = ("Ваши объявления хранятся в боте — выберите, где вам "
                "удобнее." if ru else
                "Жарыяларыңыз ботто турат — кайсынысы ыңгайлуу болсо, "
                "ошону тандаңыз.")
    else:
        head = "Разместить объявление" if ru else "Жарыя берүү"
        lead = ("Объявление размещается через бота — выберите, где вам удобнее."
                if ru else
                "Жарыя бот аркылуу коюлат — кайсынысы ыңгайлуу болсо, ошону тандаңыз.")
    tg_t = "Перейти в Telegram-бот" if ru else "Telegram ботко өтүү"
    wa_t = "Перейти в WhatsApp-бот" if ru else "WhatsApp ботко өтүү"
    soon = "WhatsApp — скоро" if ru else "WhatsApp — жакында"
    if bal:
        note = ("Суточный лимит, бонусные объявления и приглашённые друзья — "
                "всё в одном месте." if ru else
                "Суткалык чек, бонус жарыялар жана чакырган досторуңуз — "
                "баары бир жерде.")
    elif mine:
        note = ("Оба бота работают с одной базой: объявления, размещённые "
                "через любой из них, будут в списке." if ru else
                "Эки бот бир базада иштейт: кайсынысы аркылуу койсоңуз да, "
                "жарыяларыңыз бир тизмеде турат.")
    else:
        note = ("Оба бота работают с одной базой: объявление появится и здесь, "
                "на сайте." if ru else
                "Эки бот бир базада иштейт: жарыя ушул сайтта да чыгат.")

    # WhatsApp'та баскыч жок — кабар талаасына даяр текст коёбуз
    wa_text = ("Менин балансым" if bal else
               "Менин жарыяларым" if mine else "Салам")
    if wa_num:
        wa = (f'<a class="btn wabtn" href="https://wa.me/{wa_num}'
              f'?text={urllib.parse.quote(wa_text)}"'
              f' target="_blank" rel="noopener">'
              f'<span>{esc(wa_t)}</span></a>')
    else:
        wa = f'<span class="btn wabtn off"><span>{esc(soon)}</span></span>'

    body = f"""<main class="wrap">
<h1 class="ftitle">{esc(head)}</h1>
<p class="flead">{esc(lead)}</p>
<a class="btn tgbtn" href="https://t.me/{BOT}?start={task}">
<span>{esc(tg_t)}</span></a>
{wa}
<p class="flead">{esc(note)}</p></main>""" + _ADD_CSS
    return page(header("", None, None, lang) + body,
                head + " — ТАП!", "me" if (mine or bal) else "add", lang)


# Жардам жана Кабинет барактарынын стили. Кадимки сап — f-string
# эмес, ошондуктан CSS'тин { } белгилери коопсуз.
_VID_CSS = """<style>
.dvid{display:block;width:100%;margin:10px 0 4px;border-radius:16px;
 overflow:hidden;background:#0E1F38;position:relative}
.dvid video{display:block;width:100%;max-height:70vh;background:#0E1F38}
.dvl{position:absolute;top:9px;left:11px;z-index:2;pointer-events:none;
 padding:3px 9px;border-radius:999px;background:rgba(14,31,56,.72);
 color:#fff;font-size:11.5px;font-weight:700}
</style>"""

_ACC_CSS = """<style>
.accs{margin:6px 0 22px}
.acc{background:var(--card);border:1px solid var(--mist);border-radius:14px;
 margin-bottom:9px;overflow:hidden}
.acc summary{list-style:none;cursor:pointer;padding:14px 44px 14px 16px;
 font-size:15px;font-weight:700;color:var(--ink);position:relative;
 transition:background .15s}
.acc summary::-webkit-details-marker{display:none}
/* Оң жактагы жебе: жабыкта ылдый, ачыкта өйдө карайт */
.acc summary::after{content:"";position:absolute;right:17px;top:50%;
 width:9px;height:9px;margin-top:-6px;border-right:2px solid var(--soft);
 border-bottom:2px solid var(--soft);transform:rotate(45deg);
 transition:transform .2s}
.acc[open] summary::after{transform:rotate(-135deg);margin-top:-2px}
.acc[open] summary{color:var(--moss)}
.acc summary:active{background:var(--mist)}
.accb{padding:0 16px 16px;font-size:15.5px;line-height:1.65;
 color:#0E1B2E;font-weight:500;white-space:pre-wrap}
</style>"""

_ME_CSS = """<style>
.mewrap{padding-top:10px}
/* Үстүңкү блок — аватардын ордуна ботко чакыруу */
.mehead{display:flex;align-items:center;gap:13px;padding:4px 4px 10px;
 color:var(--ink)}
.meav{flex:none;width:58px;height:58px;border-radius:50%;
 background:var(--mist);display:flex;align-items:center;justify-content:center;
 color:var(--soft)}
.meav svg{width:30px;height:30px}
.metx{display:flex;flex-direction:column;gap:2px;min-width:0}
.metx b{font-size:16px;font-weight:700}
.metx i{font-style:normal;font-size:13.5px;color:var(--soft)}
.mesub{margin:0 4px 14px;font-size:13px;color:var(--faint)}

/* Ботко кирүү баскычтары — эки платформа тең */
.ments{display:flex;gap:8px;margin:2px 0 16px}
.ment{flex:1;display:flex;align-items:center;justify-content:center;gap:7px;
 padding:11px 8px;border-radius:14px;color:#fff;font-weight:700;
 font-size:14px;transition:transform .15s,filter .15s}
.ment svg{width:19px;height:19px;flex:none}
.ment.tg{background:#2AA3DA}
.ment.wa{background:#22C15E}
.ment.off{background:var(--mist);color:var(--faint);font-weight:600}
.ment:active{transform:scale(.96);filter:brightness(.95)}

/* Жалпак катарлар: карточка эмес, чек сызык менен бөлүнөт */
.mesec{background:var(--card);border-radius:var(--r);overflow:hidden;
 margin-bottom:12px;border:1px solid var(--mist)}
.mrow2{display:flex;align-items:center;gap:14px;padding:14px 16px;
 color:var(--ink);font-weight:600;font-size:15px;
 border-bottom:1px solid var(--mist);transition:background .15s}
.mesec .mrow2:last-child{border-bottom:0}
.mrow2 svg{flex:none;width:22px;height:22px;color:var(--soft)}
.mrow2:active{background:var(--mist)}
.mrow2.off{opacity:.45}
.mrow2.accent{color:var(--moss);font-weight:700}
.mrow2.accent svg{color:var(--moss)}
.meabout{margin:6px 4px 0;font-size:13px;line-height:1.5;color:#2E3B52}
</style>"""

_HELP_CSS = """<style>
.htext{white-space:pre-wrap;font-size:15px;line-height:1.55;
       color:var(--ink);margin:0}
.mrow{display:flex;align-items:center;gap:10px;padding:15px 16px;
      background:var(--card);border-radius:var(--r);margin-bottom:8px;
      text-decoration:none;color:var(--ink);font-weight:600}
.mrow .ar{margin-left:auto;color:var(--faint)}
.mrow.off{opacity:.5}
.btn.tgbtn{background:#2AA3DA;margin-bottom:10px}
.btn.wabtn{background:#22C15E}
.btn.off{opacity:.55}
</style>"""


def _admin_buttons(lang):
    """«Бизге жазуу» — Telegram жана WhatsApp."""
    ru = (lang == "ru")
    tg = (os.environ.get("ADMIN_TG", "") or BOT).lstrip("@")
    wa = "".join(c for c in os.environ.get("ADMIN_WA", "") if c.isdigit())
    t_tg = "Написать в Telegram" if ru else "Telegram аркылуу жазуу"
    t_wa = "Написать в WhatsApp" if ru else "WhatsApp аркылуу жазуу"
    soon = "WhatsApp — скоро" if ru else "WhatsApp — жакында"
    out = (f'<a class="btn tgbtn" href="https://t.me/{tg}">'
           f'<span>{esc(t_tg)}</span></a>')
    if wa:
        out += (f'<a class="btn wabtn" href="https://wa.me/{wa}" '
                f'target="_blank" rel="noopener"><span>{esc(t_wa)}</span></a>')
    else:
        out += f'<span class="btn wabtn off"><span>{esc(soon)}</span></span>'
    return out


def help_page(lang="ky", open_key=None):
    """
    Жардам — ачылып-жабылуучу бөлүмдөр (аккордеон).

    Он алты бөлүм бир баракка тизилсе, эч ким аягына чейин окубайт.
    Ошондуктан ар бири басканда гана ачылат. JavaScript колдонулбайт:
    браузердин өз <details> элементи иштейт, ошондуктан тез ачылат
    жана интернет начар жерде да иштейт.

    Тексттер strings.py'ден алынат — ботто да ошолор чыгат, бир
    жерден оңдосоң эки жерде тең жаңырат.
    """
    ru = (lang == "ru")
    head = "Помощь" if ru else "Жардам"
    lead = ("Всё о платформе: как разместить, как искать, правила."
            if ru else
            "Платформа жөнүндө баары: кантип коюу, кантип издөө, эрежелер.")
    write = "Написать нам" if ru else "Бизге жазуу"

    blocks = ""
    for key, _ky, _ru in HELP_TOPICS:
        txt = help_text(key, lang)
        if not txt:
            continue
        op = " open" if key == open_key else ""
        blocks += (f'<details class="acc" id="{key}"{op}>'
                   f'<summary>{esc(topic_title(key, lang))}</summary>'
                   f'<div class="accb">{esc(txt)}</div></details>')

    body = f"""<main class="wrap">
<h1 class="ftitle">{esc(head)}</h1>
<p class="flead">{esc(lead)}</p>
<div class="accs">{blocks}</div>
<h3 class="qh">{esc(write)}</h3>
{_admin_buttons(lang)}</main>""" + _HELP_CSS + _ACC_CSS
    return page(header("", None, None, lang) + body,
                head + " — ТАП!", "msg", lang)


def me_page(lang="ky"):
    """
    Кабинет — жалпак тизме түрүндө: сол жакта белги, ортодо жазуу.

    Сайтта каттоо жок, ошондуктан эң үстүндө аватар эмес, ботко
    чакырган блок турат: тааныткыч Telegram каттоо эсеби болот.
    Ылдый жагындагы блокто расмий баракчаларыбыз — алар Railway'дин
    өзгөрмөлөрүнөн алынат, коюла электери көрүнбөйт.
    """
    ru = (lang == "ru")
    head = "Кабинет"

    # ── Үстүңкү блок: ботко чакыруу (эки платформа тең) ──
    wa_top = "".join(c for c in os.environ.get("WA_NUMBER", "") if c.isdigit())
    top_t = "Войдите через бота" if ru else "Ботко кириңиз"
    top_p = ("Объявления и избранное привязаны к боту"
             if ru else "Жарыялар менен тандалгандар ботко байланган")
    soon_t = "скоро" if ru else "жакында"

    ent = (f'<a class="ment tg" href="https://t.me/{BOT}">'
           f'{NAV_ICONS["tg"]}<span>Telegram</span></a>')
    if wa_top:
        ent += (f'<a class="ment wa" href="https://wa.me/{wa_top}" '
                f'target="_blank" rel="noopener">'
                f'{NAV_ICONS["wa"]}<span>WhatsApp</span></a>')
    else:
        ent += (f'<span class="ment wa off">{NAV_ICONS["wa"]}'
                f'<span>WhatsApp — {esc(soon_t)}</span></span>')

    top = (f'<div class="mehead">'
           f'<span class="meav">{NAV_ICONS["me"]}</span>'
           f'<span class="metx"><b>{esc(top_t)}</b>'
           f'<i>{esc(top_p)}</i></span></div>'
           f'<div class="ments">{ent}</div>')

    # ── Тил ──
    lang_row = (f'<a class="mrow2 accent" href="/lang/'
                f'{"ky" if ru else "ru"}">{NAV_ICONS["globe"]}'
                f'<span>{esc("Язык: Кыргызча" if ru else "Тил: Русский")}'
                f'</span></a>')

    # ── Негизги тизме ──
    rows = [
        ("grid",   ("Объявления" if ru else "Жарыялар"),          "/"),
        ("search", ("Поиск" if ru else "Издөө"),                  "/?q="),
        ("add",    ("Разместить объявление" if ru else "Жарыя берүү"), "/add"),
        ("list",   ("Мои объявления" if ru else "Менин жарыяларым"),   "/my"),
        ("fav",    ("Избранное" if ru else "Тандалгандар"),       "/fav"),
        ("wallet", ("Мой баланс" if ru else "Менин балансым"),  "/bal"),
        ("help",   ("Помощь" if ru else "Жардам"),                "/msg"),
    ]
    items = ""
    for ic, label, href in rows:
        items += (f'<a class="mrow2" href="{href}">{NAV_ICONS[ic]}'
                  f'<span>{esc(label)}</span></a>')

    terms = "Условия использования" if ru else "Колдонуу шарттары"
    items += (f'<a class="mrow2" href="/terms">{NAV_ICONS["doc"]}'
              f'<span>{esc(terms)}</span></a>')

    # ── Расмий баракчалар ──
    wa_num = "".join(c for c in os.environ.get("WA_NUMBER", "") if c.isdigit())
    links = [("tg", "Telegram", f"https://t.me/{BOT}")]
    chan = os.environ.get("TG_CHANNEL", "").strip()
    if chan:
        links.append(("tg", ("Наш канал" if ru else "Каналыбыз"),
                      chan if chan.startswith("http")
                      else "https://t.me/" + chan.lstrip("@")))
    if wa_num:
        links.append(("wa", "WhatsApp", f"https://wa.me/{wa_num}"))
    for key, nm in (("INSTAGRAM", "Instagram"), ("FACEBOOK", "Facebook")):
        u = os.environ.get(key, "").strip()
        if u:
            links.append((key[:2].lower().replace("in", "ig"), nm, u))

    social = ""
    for ic, nm, href in links:
        social += (f'<a class="mrow2" href="{href}" target="_blank" '
                   f'rel="noopener">{NAV_ICONS.get(ic, NAV_ICONS["tg"])}'
                   f'<span>{esc(nm)}</span></a>')

    about = ("ТАП! — умная платформа объявлений Кыргызстана. Торговля, "
             "оптовая торговля, продажа имущества, услуги, аренда, "
             "доставка, грузоперевозки, поиск работы, работа, рынки "
             "и такси. Работает в Telegram, WhatsApp и на этом "
             "сайте — база одна."
             if ru else
             "ТАП! — Кыргызстандагы акылдуу жарыя платформасы. "
             "Соода-сатык, Соода-сатык (дүң), мүлк сатуу, кызмат "
             "көрсөтүү, ижарага берүү, жеткирүү, жүк ташуу, жумуш "
             "издөө, жумуш берүү, базарлар жана такси. Telegram'да, "
             "WhatsApp'та жана ушул сайтта иштейт — база бир эле.")

    body = f"""<main class="wrap mewrap">
{top}
<div class="mesec">{lang_row}</div>
<div class="mesec">{items}</div>
<div class="mesec">{social}</div>
<p class="meabout">{esc(about)}</p></main>""" + _HELP_CSS + _ME_CSS
    return page(header("", None, None, lang) + body,
                head + " — ТАП!", "me", lang)


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

        if u.path == "/bal":
            return self._send(add_page(lang, "balance"))

        if u.path == "/my":
            self._send(add_page(lang, "my"))
            return

        if u.path == "/me":
            self._send(me_page(lang))
            return

        if u.path == "/msg":
            self._send(help_page(lang))
            return

        if u.path == "/terms":
            self._send(help_page(lang, "terms"))
            return

        if u.path == "/":
            q = (qs.get("q", [""])[0]).strip()
            at = qs.get("at", [None])[0]
            if at not in SECTION_NAME:
                at = None
            cid = (qs.get("cid", [""])[0]).strip() or None
            sid = (qs.get("sid", [""])[0]).strip() or None
            sort = (qs.get("sort", [""])[0]).strip() or "new"
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

            self._send(home(q, at, cid, sid, ob, di, vi, lang, sort))

        elif u.path == "/fav":
            self._send(fav_page(lang))

        elif u.path == "/api/ads":
            at = (qs.get("at", [""])[0]).strip() or None
            if at not in SECTION_NAME:
                at = None
            cid = (qs.get("cid", [""])[0]).strip() or None
            ob = (qs.get("ob", [""])[0]).strip() or None
            rows = core.find(limit=12, ad_type=at, cat_id=cid, oblast=ob)
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

        elif u.path == "/manifest.webmanifest":
            data = json.dumps(MANIFEST, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/manifest+json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "max-age=3600")
            self.end_headers()
            self.wfile.write(data)

        elif u.path == "/sw.js":
            data = SW_JS.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(data)

        elif u.path.startswith("/pwa/"):
            key = os.path.basename(urllib.parse.unquote(u.path[5:]))
            key = key[:-4] if key.endswith(".png") else key
            data = appicon.get(key)
            if data:
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "max-age=604800")
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()

        elif u.path.startswith("/si/"):
            # Бөлүм такталарынын сүрөттөрү — secimg.py ичинде турат
            key = os.path.basename(urllib.parse.unquote(u.path[4:]))
            key = key[:-4] if key.endswith(".jpg") else key
            data = secimg.get(key)
            if data:
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "max-age=604800")
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()

        elif u.path.startswith("/media/"):
            name = os.path.basename(urllib.parse.unquote(u.path[7:]))
            fp = os.path.join(MEDIA, name)
            if name and os.path.isfile(fp):
                # Видео менен сүрөт бир папкада жатат, ошондуктан
                # түрүн кеңейтмеси боюнча аныктайбыз
                low = name.lower()
                ctype = ("video/mp4" if low.endswith(".mp4")
                         else "video/quicktime" if low.endswith(".mov")
                         else "image/png" if low.endswith(".png")
                         else "image/jpeg")
                size = os.path.getsize(fp)

                # Браузер видеону бөлүп сурайт (Range). Ансыз 20 МБ
                # файл толук жүктөлмөйүнчө ойнобойт.
                start, end, partial = 0, size - 1, False
                rng = self.headers.get("Range") or ""
                if rng.startswith("bytes="):
                    try:
                        a, _, b = rng[6:].partition("-")
                        if a:
                            start = int(a)
                            if b:
                                end = int(b)
                        elif b:
                            start = max(0, size - int(b))
                        if 0 <= start <= end < size:
                            partial = True
                    except Exception:
                        partial = False
                if not partial:
                    start, end = 0, size - 1
                else:
                    end = min(end, start + 1024 * 1024 - 1)   # 1 МБлык бөлүк

                with open(fp, "rb") as f:
                    f.seek(start)
                    data = f.read(end - start + 1)

                self.send_response(206 if partial else 200)
                self.send_header("Content-Type", ctype)
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", str(len(data)))
                if partial:
                    self.send_header("Content-Range",
                                     "bytes %d-%d/%d" % (start, end, size))
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

