#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAP! — витрина (сайт).

Ботко коюлган жарыяларды көрсөтөт. Бот менен бир эле базаны колдонот.
Иштетүү: python tap.py
Ачуу:    http://localhost:8000
"""

import base64
import html, json, os, urllib.parse
import time as _t
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

import core
from core import (CATS, SUBS, MEDIA, category_title, category_icon, sub_title,
                  price_label, is_deal, ago)
from tap_catalog import (TRADE_CATEGORIES, PROPERTY_CATEGORIES,
                         VEHICLE_SALE_CATEGORIES,
                         SERVICE_CATEGORIES, RENTAL_CATEGORIES,
                         DELIVERY_CATEGORIES, JOB_CATEGORIES, MARKETS_TYPES,
                         MALLS_TYPES,
                         WHOLESALE_CATEGORIES, CARGO_CATEGORIES, JOBSEEK_CATEGORIES,
                         TAXI_CATEGORIES, TAXI_AIRPORT_SUBS,
                         OBLASTS, get_districts, get_localities, get_villages,
                         ru_name)
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
    ("vehicle",   SCENES.get("vehicle", SCENES["taxi"]),     "Унаа сатуу"),
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
    "vehicle":   ("Унаа сатуу", "Продажа транспорта"),
    "cargo":     ("Жүк ташуу", "Грузоперевозки"),
    "jobseek":   ("Жумуш издөө", "Поиск работы"),
    "malls":     ("Соода борборлору", "Торговые центры"),
}

SECTION_CODES = [c for c, _, _ in SECTIONS]
SECTION_NAME = {code: name for code, _, name in SECTIONS}

_CAT_LISTS = {
    "trade":    TRADE_CATEGORIES,
    "property": PROPERTY_CATEGORIES,
    "vehicle":  VEHICLE_SALE_CATEGORIES,
    "service":  SERVICE_CATEGORIES,
    "rental":   RENTAL_CATEGORIES,
    "delivery": DELIVERY_CATEGORIES,
    "job":      JOB_CATEGORIES,
    "markets":  MARKETS_TYPES,
    "malls":    MALLS_TYPES,
    "wholesale": WHOLESALE_CATEGORIES,
    "cargo":     CARGO_CATEGORIES,
    "jobseek":   JOBSEEK_CATEGORIES,
    "taxi":      TAXI_CATEGORIES,   # TAXI_CATS
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


# CHIP_EMOJI: ар бир категориянын белгиси (каталогдон)
_CAT_EMOJI = {}
for _lst in _CAT_LISTS.values():
    for _c in _lst:
        if _c.get("emoji"):
            _CAT_EMOJI.setdefault(_c["id"], _c["emoji"])


def cat_emoji(cat_id):
    return _CAT_EMOJI.get(cat_id, "")


def _ce(cat_id):
    """CAT_EMOJI_SHOW: категориянын белгиси + боштук (жок болсо — бош)."""
    e = _CAT_EMOJI.get(cat_id, "")
    return (e + " ") if e else ""


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
   var u=b.dataset.u||(b.dataset.h?atob(b.dataset.h):"");
   if(u)window.open(u,"_blank","noopener");
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


def page(body, title="ТАП!", tab="home", lang="ky", meta=""):
    return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#17365C">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="apple-touch-icon" href="/pwa/apple-180.png?v={appicon.VERSION}">
<link rel="icon" href="/pwa/icon-192.png?v={appicon.VERSION}" sizes="192x192">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="ТАП!">
<title>{esc(title)}</title>{meta}{FONTS}<style>{CSS}{EXTRA_CSS}</style></head><body>{body}{nav(tab, lang)}
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


# CHIP_DARK: тандалбаган чиптердин жазуусу караңгы
EXTRA_CSS += ("\n.rg:not(.on),.sb2:not(.on){color:#0B1B30!important;"
              "font-weight:700}"
              ".rg:not(.on) em,.sb2:not(.on) em{color:#0B1B30;opacity:.8}\n")


# REG_BORDER: облус чиптеринин чеги караңгы
EXTRA_CSS += ("\n.regbar1 .rg:not(.on){border:1.5px solid #3A4E6B!important}\n")


# TOPNAV_DARK: үстүңкү аймак, RU жана ылдыйкы меню караңгы
EXTRA_CSS += chr(10)+'.pin{color:#0B1B30!important;opacity:1!important}.lgs .lg:not(.on){color:#0B1B30!important;opacity:1!important}.nav a{color:#0B1B30!important;opacity:1!important}.nav a span,.nav a small,.nav a b,.nav a em,.nav a div{color:#0B1B30!important;opacity:1!important}'


# SAFE_FIX2
# SAFE_SEC: бөлүмдөрдүн эскертүүлөрү (ТАП!, кеңеш, ТАП! ru, кеңеш ru)
_SAFE_TXT = {'trade': ('ТАП! жарыя гана жайгаштырат. Соодага, төлөмгө жана жеткирүүгө катышпайт, жооп бербейт.', 'Товарды көрмөйүн алдын ала акча которбоңуз. Бөтөн шилтемеге карта маалыматын киргизбеңиз, SMS-кодду эч кимге айтпаңыз.', 'ТАП! только размещает объявления. Не участвует в сделке, оплате и доставке и не несёт ответственности.', 'Не переводите предоплату, пока не увидели товар. Не вводите данные карты по чужим ссылкам и никому не сообщайте код из SMS.'), 'wholesale': ('ТАП! жарыя гана жайгаштырат. Келишимге, төлөмгө жана товар жеткирүүгө катышпайт, жооп бербейт.', 'Биринчи жолу чоң партия албаңыз, адегенде үлгүсүн сатып алып көрүңүз. Товар менен кошо накладной алыңыз.', 'ТАП! только размещает объявления. Не участвует в договоре, оплате и доставке товара и не несёт ответственности.', 'Не берите крупную партию с первого раза — сначала купите образец. Берите накладную вместе с товаром.'), 'property': ('ТАП! жарыя гана жайгаштырат. Документ тариздөөгө, соодага жана төлөмгө катышпайт, жооп бербейт.', 'Ээсинин документтерин текшермейин задаток бербеңиз. Келишимди нотариус аркылуу түзүңүз.', 'ТАП! только размещает объявления. Не участвует в оформлении документов, сделке и оплате и не несёт ответственности.', 'Не давайте задаток, пока не проверили документы владельца. Оформляйте договор через нотариуса.'), 'vehicle': ('ТАП! жарыя гана жайгаштырат. Соодага жана төлөмгө катышпайт, унаанын абалы үчүн жооп бербейт.', 'Унааны жана документтерин көрмөйүн акча бербеңиз. Доверенность менен сатылса, ээсинин өзү менен жолугуп, VIN номерин текшериңиз жана ЦОНдо кайра каттоодон өткөрүңүз.', 'ТАП! только размещает объявления. Не отвечает за состояние авто, не участвует в сделке и оплате.', 'Не платите, пока не увидели авто и документы. Если продают по доверенности, встретьтесь с владельцем, сверьте VIN и переоформите авто в ЦОНе.'), 'service': ('ТАП! жарыя гана жайгаштырат. Төлөмгө катышпайт, иштин сапаты үчүн жооп бербейт.', 'Акынын баарын алдын ала төлөбөңүз, иш бүткөндөн кийин төлөңүз. Баасын башында так макулдашып алыңыз.', 'ТАП! только размещает объявления. Не отвечает за качество работы и не участвует в оплате.', 'Не платите всю сумму заранее — платите после работы. Заранее точно договоритесь о цене.'), 'rental': ('ТАП! жарыя гана жайгаштырат. Ижара келишимине жана төлөмгө катышпайт, жооп бербейт.', 'Мүлктү көрмөйүн алдын ала акча которбоңуз. Ээси экенин документ менен текшерип, жазуу жүзүндө келишим түзүңүз.', 'ТАП! только размещает объявления. Не участвует в договоре аренды и оплате и не несёт ответственности.', 'Не переводите деньги, пока не увидели имущество. Проверьте документы владельца и заключите письменный договор.'), 'delivery': ('ТАП! жарыя гана жайгаштырат. Жеткирүүгө жана төлөмгө катышпайт, посылка үчүн жооп бербейт.', 'Посылканы алганда ачып текшериңиз. Бөтөн шилтеме аркылуу «жеткирүү акысын» төлөбөңүз.', 'ТАП! только размещает объявления. Не участвует в передаче посылки, доставке и оплате и не несёт ответственности.', 'Вскройте и проверьте посылку при получении. Не оплачивайте «доставку» по чужим ссылкам.'), 'cargo': ('ТАП! жарыя гана жайгаштырат. Ташууга жана төлөмгө катышпайт, жүк үчүн жооп бербейт.', 'Жүктү жүктөөдөн мурун баасын жана убактысын макулдашыңыз. Баалуу жүктүн сүрөтүн тартып алыңыз.', 'ТАП! только размещает объявления. Не отвечает за груз, перевозку и оплату.', 'До погрузки договоритесь о цене и сроках. Сфотографируйте ценный груз.'), 'jobseek': ('ТАП! жарыя гана жайгаштырат. Жумушка орношууга жана эмгек келишимине катышпайт, жооп бербейт.', 'Жумушка орношуу же «окутуу» үчүн акча төлөбөңүз. Паспортуңузду эч кимге калтырбаңыз.', 'ТАП! только размещает объявления. Не участвует в трудоустройстве и трудовом договоре и не несёт ответственности.', 'Не платите за трудоустройство или «обучение». Никому не оставляйте свой паспорт.'), 'job': ('ТАП! жарыя гана жайгаштырат. Кызматкерди тандоого жана эмгек келишимине катышпайт, жооп бербейт.', 'Кызматкерди документи менен тааныңыз. Акча же баалуу буюм тапшырганда жазуу жүзүндө келишим түзүңүз.', 'ТАП! только размещает объявления. Не участвует в подборе сотрудников и трудовом договоре и не несёт ответственности.', 'Проверьте документы сотрудника. Доверяя деньги или ценности, заключите письменный договор.'), 'markets': ('ТАП! жарыя гана жайгаштырат. Соодага жана төлөмгө катышпайт, товардын сапаты үчүн жооп бербейт.', 'Товарды сатып алардан мурун колуңузга алып текшериңиз. Баасын так макулдашып, мүмкүн болсо чек же кагаз алыңыз.', 'ТАП! только размещает объявления. Не отвечает за качество товара, не участвует в сделке и оплате.', 'Перед покупкой осмотрите товар. Точно договоритесь о цене и по возможности возьмите чек.'), 'malls': ('ТАП! жарыя гана жайгаштырат. Соодага жана төлөмгө катышпайт, дүкөндөрдүн товары үчүн жооп бербейт.', 'Кепилдик талонун жана чекти сөзсүз алыңыз. Бөтөн шилтемедеги «акцияларга» ишенбеңиз.', 'ТАП! только размещает объявления. Не отвечает за товары магазинов, не участвует в сделке и оплате.', 'Обязательно берите гарантийный талон и чек. Не доверяйте «акциям» по чужим ссылкам.'), 'taxi': ('ТАП! жарыя гана жайгаштырат. Жол жүрүүгө жана төлөмгө катышпайт, жооп бербейт.', 'Унаанын номерин жана айдоочунун атын жакындарыңызга жибериңиз. Акысын жолдо же барган жерде төлөңүз.', 'ТАП! только размещает объявления. Не участвует в поездке и оплате и не несёт ответственности.', 'Отправьте близким номер авто и имя водителя. Оплачивайте в пути или по прибытии.')}


# WEB_VERIFY: JSON жооп жана /verify тест бети
def _json_out(h, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    h.send_response(200)
    h.send_header("Content-Type", "application/json; charset=utf-8")
    h.send_header("Content-Length", str(len(data)))
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    h.wfile.write(data)


# WEB_POST: сайттан жарыя берүү ─────────────────────────────
import re as _wre
import tap_flow as _tf

WEB_SECTIONS = ("trade", "wholesale", "property", "vehicle", "service",   # WEB_ALLSEC
                "rental", "delivery", "cargo", "jobseek", "job",
                "markets", "malls", "taxi")
_WEB_HOME = ("main_menu", "home", "tap_home")


def _wlead(line):
    i = 0
    while i < len(line) and (ord(line[i]) >= 0x2000 or line[i] == " "):
        i += 1
    return line[:i]


def _wloc(text, lang):
    """«кыргызча / орусча» → бир тил, HTML."""
    out = []
    for line in str(text or "").split("\n"):
        pk = L(line, lang)
        hd = _wlead(line)
        if hd.strip() and not pk.startswith(hd.strip()[:1]):
            pk = hd + pk
        pk = html.escape(pk)
        if pk.count("*") % 2 == 0:
            parts = pk.split("*")
            pk = "".join(("<b>%s</b>" % x) if i % 2 else x for i, x in enumerate(parts))
        else:
            pk = pk.replace("*", "")
        out.append(pk)
    return "<br>".join(out)


def _wview(step, d, lang):
    v = _tf.render(step, d)
    opts = []
    for o in v.get("options") or []:
        lab = o["label"] if v.get("localized") else L(o["label"], lang)
        if o["value"] in _WEB_HOME or str(lab).lstrip().startswith("🏠"):
            continue
        opts.append({"label": lab, "value": o["value"]})
    return {"text": _wloc(v["text"], lang) if not v.get("localized") else html.escape(v["text"]).replace("\n", "<br>"),
            "options": opts, "input": bool(v.get("input")),
            "placeholder": L(v.get("placeholder") or "", lang),
            "multi": bool(v.get("multi")), "photo": bool(v.get("photo")),
            "video": bool(v.get("video")), "vmax": _WEB_VMAX,
            "photo_max": v.get("photo_max") or 10, "final": bool(v.get("final")),
            "done": step == "post_done"} if step != "post_done" else {
            "text": html.escape("Дээрлик даяр! Жарыянын аталышын жазып, «Жарыялоо» басыңыз."
                                if lang != "ru" else
                                "Почти готово! Напишите заголовок и нажмите «Опубликовать»."),
            "options": [], "input": False, "placeholder": "", "multi": False,
            "photo": False, "photo_max": 10, "final": True, "done": True}


def _wverified(tok):
    try:
        st = core.web_verify_status(tok)
    except Exception:
        st = None
    return st if (st and st["verified"] and st.get("tg_id")) else None


def _web_post(b, lang):
    op = b.get("op")
    st = _wverified(b.get("token"))
    if not st:
        return {"ok": False, "err": "verify"}
    if op == "start":
        sec = b.get("section") or "trade"
        if sec not in WEB_SECTIONS:
            return {"ok": False, "err": "section"}
        step, d = _tf.advance("type_select", sec,
                              {"uiLanguage": lang, "action": "post"})
        return {"ok": True, "step": step, "data": d, "view": _wview(step, d, lang)}
    d = b.get("data") or {}
    if not isinstance(d, dict) or d.get("adType") not in WEB_SECTIONS:
        return {"ok": False, "err": "section"}
    step = str(b.get("step") or "")
    if op == "next":
        step, d = _tf.advance(step, str(b.get("value") or ""), d)
        for _i in range(2):                  # номер ырасталган — өзү толтурулат
            if step in ("post_whatsapp", "taxi_phone"):
                step, d = _tf.advance(step, "+996" + st["phone"], d)
        if step in _WEB_HOME or step == "language_select":
            return {"ok": True, "restart": True}
        return {"ok": True, "step": step, "data": d, "view": _wview(step, d, lang)}
    if op == "view":
        return {"ok": True, "step": step, "data": d, "view": _wview(step, d, lang)}
    if op == "publish":
        if step != "post_done":
            return {"ok": False, "err": "step"}
        return _web_publish(d, st, b)
    return {"ok": False, "err": "op"}


_WPH_RE = _wre.compile(r"^web_[A-Za-z0-9]{8}_[a-z0-9]{10}\.jpg$")


def _web_photo(tok, raw):
    st = _wverified(tok)
    if not st:
        return {"ok": False, "err": "verify"}
    if not raw or len(raw) > 8 * 1024 * 1024:
        return {"ok": False, "err": "size"}
    import secrets, io
    name = "web_%s_%s.jpg" % (str(tok)[:8], secrets.token_hex(5))
    path = os.path.join(MEDIA, name)
    os.makedirs(MEDIA, exist_ok=True)
    try:
        from PIL import Image, ImageOps
        im = Image.open(io.BytesIO(raw))
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((1600, 1600))
        im.save(path, "JPEG", quality=85)
    except Exception as e:
        print("web_photo:", e, flush=True)
        if raw[:3] != b"\xff\xd8\xff":   # WEB_PHOTO_RAW: PIL жок болсо JPEG түз сакталат
            return {"ok": False, "err": "image"}
        try:
            with open(path, "wb") as fh:
                fh.write(raw)
        except Exception as e2:
            print("web_photo save:", e2, flush=True)
            return {"ok": False, "err": "image"}
    return {"ok": True, "name": name}


try:
    import rules as _wrules
    _WEB_VMAX = int(getattr(_wrules, "VIDEO_MAX_MB", 20) or 20)
except Exception:
    _WEB_VMAX = 20
_WVD_RE = _wre.compile(r"^web_[A-Za-z0-9]{8}_[a-z0-9]{10}\.mp4$")


def _web_video(tok, raw):
    st = _wverified(tok)
    if not st:
        return {"ok": False, "err": "verify"}
    if not raw or len(raw) > _WEB_VMAX * 1024 * 1024:
        return {"ok": False, "err": "vbig"}
    if raw[4:8] != b"ftyp":          # mp4 / mov гана
        return {"ok": False, "err": "vfmt"}
    import secrets
    os.makedirs(MEDIA, exist_ok=True)
    name = "web_%s_%s.mp4" % (str(tok)[:8], secrets.token_hex(5))
    try:
        with open(os.path.join(MEDIA, name), "wb") as fh:
            fh.write(raw)
    except Exception as e:
        print("web_video:", e, flush=True)
        return {"ok": False, "err": "vfmt"}
    return {"ok": True, "name": name}


def _web_publish(d, st, b):
    uid = str(st["tg_id"])
    d = dict(d)
    d["phone"] = "+996" + st["phone"]
    if d.get("adType") == "taxi":
        d["taxiPhone"] = d["phone"]
    t = str(b.get("title") or "").strip()[:120]
    if t:
        d["title"] = t
    hits = []
    try:
        import rules
        ok, _bu, _bl = rules.spend_post(uid)
        if not ok:
            return {"ok": False, "err": "limit"}
        level, hits = rules.check_text(d.get("title"), d.get("postComment"),
                                       d.get("subcategory"), d.get("description"))
        if level in ("hard", "swear"):
            return {"ok": False, "err": "bad", "words": hits[:3]}
    except ImportError:
        pass
    row = bridge.to_listing(d)
    if not row.get("title"):
        row["title"] = "Жарыя"
    lid = core.add_listing(row, uid, str(d.get("personName") or "")[:60])
    for fn in (lambda: core.remember_phone(uid, row.get("contact")),
               lambda: core.log_event("post", lid, uid, "site"),
               lambda: core.query("UPDATE listings SET verified=1 WHERE id=?", (lid,))):
        try:
            fn()
        except Exception as e:
            print("web_publish:", e, flush=True)
    saved = []
    pre = "web_%s_" % str(b.get("token") or "")[:8]
    for i, name in enumerate([x for x in (d.get("webPhotos") or [])
                              if isinstance(x, str)][:10], 1):
        src = os.path.join(MEDIA, name)
        if not (_WPH_RE.match(name) and name.startswith(pre) and os.path.isfile(src)):
            continue
        dst_name = "%d.jpg" % lid if not saved else "%d_%d.jpg" % (lid, len(saved) + 1)
        try:
            os.replace(src, os.path.join(MEDIA, dst_name))
            saved.append(dst_name)
        except Exception as e:
            print("web_publish photo:", e, flush=True)
    if saved:
        try:
            core.set_photos(lid, saved)
        except Exception as e:
            print("web_publish set_photos:", e, flush=True)
    vn = d.get("webVideo")
    if isinstance(vn, str) and _WVD_RE.match(vn) and vn.startswith(pre):
        src = os.path.join(MEDIA, vn)
        if os.path.isfile(src):
            try:
                os.replace(src, os.path.join(MEDIA, "%d.mp4" % lid))
                core.set_video(lid, "%d.mp4" % lid)
            except Exception as e:
                print("web_publish video:", e, flush=True)
    try:
        import threading
        threading.Thread(target=_web_notify_admins, args=(lid, dict(row), uid, list(hits or [])),
                         daemon=True).start()
    except Exception as e:
        print("web_notify:", e, flush=True)
    return {"ok": True, "id": lid, "url": "/e/%d" % lid}


_POST_JS = r"""
(function(){
var LANG=document.documentElement.getAttribute('data-lang')||'ky';
function T(k,r){return LANG==='ru'?r:k;}
var tok=null; try{tok=localStorage.getItem('tap_vok');}catch(e){}
var S={step:null,data:null,view:null,hist:[],picked:[]};
var box=document.getElementById('pbox');
function esc(x){return String(x==null?'':x).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function api(body){body.token=tok;return fetch('/api/post',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(r){return r.json();});}
function need(){box.innerHTML='<p style="line-height:1.45">'+T('Жарыя берүү үчүн адегенде номериңизди ырастаңыз.','Сначала подтвердите номер телефона.')+'</p><a class="pbtn" href="/verify?next=post">'+T('Номерди ырастоо','Подтвердить номер')+'</a>';}
function err(e){
  if(e==='verify'){try{localStorage.removeItem('tap_vok');}catch(x){} tok=null; need(); return;}
  var m={limit:T('Бүгүнкү жарыя чегине жеттиңиз.','Достигнут дневной лимит объявлений.'),bad:T('Жарыяда тыюу салынган сөздөр бар.','В объявлении есть запрещённые слова.'),image:T('Сүрөттү окуй албадык.','Не удалось прочитать фото.')};
  alert(m[e]||T('Ката чыкты. Кайра аракет кылыңыз.','Ошибка. Попробуйте снова.'));
}
function set(j){ if(!j.ok){err(j.err);return;} if(j.restart){start();return;}
  S.step=j.step;S.data=j.data;S.view=j.view;S.picked=[];draw();window.scrollTo(0,0);}
var SECS=[['trade','Соода-сатык','Купля-продажа'],['wholesale','Соода-сатык (дүң)','Оптовая торговля'],
  ['property','Мүлк сатуу','Недвижимость'],['vehicle','Унаа сатуу','Транспорт'],['service','Кызмат көрсөтүү','Услуги'],
  ['rental','Ижарага берүү','Аренда'],['delivery','Жеткирүү','Доставка'],['cargo','Жүк ташуу','Грузоперевозки'],
  ['jobseek','Жумуш издөө','Ищу работу'],['job','Жумуш берүү','Вакансии'],['markets','Базарлар','Рынки'],
  ['malls','Соода борборлору','Торговые центры'],['taxi','Такси','Такси']];
var SIV=(document.querySelector('.pwrap')||document.body).getAttribute('data-siv')||'1';   // POST_SECIMG
function secName(){var a=(S.data||{}).adType;for(var i=0;i<SECS.length;i++){if(SECS[i][0]===a)return T(SECS[i][1],SECS[i][2]);}return '';}
function start(){S.hist=[];S.data=null;
  var tp=document.getElementById('psecs');
  box.innerHTML='<div class="pq">'+T('Кандай жарыя бересиз?','Какое объявление подаёте?')+'</div>'+(tp?tp.innerHTML:'');
  box.querySelectorAll('[data-s]').forEach(function(b){b.onclick=function(e){if(e)e.preventDefault();
    api({op:'start',section:b.getAttribute('data-s')}).then(set).catch(function(){err();});};});}
function next(v){S.hist.push({step:S.step,data:JSON.parse(JSON.stringify(S.data))});
  api({op:'next',step:S.step,data:S.data,value:v}).then(set).catch(function(){err();});}
function draw(){
  var v=S.view,h='';
  h+='<div class="ptop"><button class="pback" id="pb" aria-label="'+T('Артка','Назад')+'"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#17304F" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg></button><div class="psec">'+((S.data&&S.data.adType)?'<img src="/si/'+S.data.adType+'.jpg?v='+SIV+'" alt="">':'')+esc(secName())+'</div></div>';
  h+='<div class="pq">'+v.text+'</div>';
  if(v.done){
    h+='<label class="plab" for="pt">'+T('Жарыянын аталышы (милдеттүү эмес)','Заголовок (необязательно)')+'</label><input id="pt" class="pfld" maxlength="120">';
    h+='<button class="pbtn" id="pgo">'+T('Жарыялоо','Опубликовать')+'</button>';
  } else if(v.photo){
    var ph=S.data.webPhotos||[];
    h+='<div class="pgrid">';
    ph.forEach(function(n){h+='<img src="/media/'+esc(n)+'" alt="">';});
    if(ph.length<v.photo_max){h+='<label class="padd" aria-label="'+T('Сүрөт кошуу','Добавить фото')+'">+<input type="file" id="pf" accept="image/*" multiple hidden></label>';}
    h+='</div><div id="pst" class="phint"></div>';
    if(v.video){h+='<div class="pvid">'+(S.data.webVideo?'<video src="/media/'+esc(S.data.webVideo)+'" controls playsinline></video><button class="pbtn pbtn2" id="pvx">'+T('Видеону алып салуу','Удалить видео')+'</button>'
      :'<label class="pbtn pbtn2" style="cursor:pointer">'+T('🎬 Видео кошуу','🎬 Добавить видео')+' ('+T('максимум ','до ')+v.vmax+' MB)<input type="file" id="pv" accept="video/*" hidden></label>')+'<div id="pvs" class="phint"></div></div>';}
    h+='<button class="pbtn" id="pdone">'+T('Даяр','Готово')+' ('+ph.length+')</button>';
  } else {
    if(v.multi){h+='<div class="phint">'+T('Бир нечесин тандасаңыз болот.','Можно выбрать несколько.')+'</div>';}
    h+='<div class="popts">';
    v.options.forEach(function(o,i){h+='<button class="popt'+(S.picked.indexOf(o.value)>=0?' on':'')+(String(o.label).length>22?' pw':'')+'" data-i="'+i+'">'+esc(o.label)+'</button>';});
    h+='</div>';
    if(v.multi){h+='<button class="pbtn" id="pmd">'+T('Даяр','Готово')+'</button>';}
    if(v.input){h+='<textarea id="pi" class="pfld" rows="5" placeholder="'+esc(v.placeholder)+'"></textarea><button class="pbtn" id="pnx">'+T('Улантуу','Далее')+'</button>';}
  }
  box.innerHTML=h;
  var pb=document.getElementById('pb'); if(pb)pb.onclick=function(){var x=S.hist.pop();if(!x){start();return;}
    S.step=x.step;S.data=x.data;api({op:'view',step:x.step,data:x.data}).then(function(j){if(j.ok){S.view=j.view;S.picked=[];draw();}else err(j.err);});};
  box.querySelectorAll('.popt').forEach(function(b){b.onclick=function(){var o=v.options[+b.getAttribute('data-i')];
    if(v.multi){var k=S.picked.indexOf(o.value);if(k>=0)S.picked.splice(k,1);else S.picked.push(o.value);draw();}
    else next(o.value);};});
  var md=document.getElementById('pmd'); if(md)md.onclick=function(){if(!S.picked.length){alert(T('Жок дегенде бирөөнү тандаңыз.','Выберите хотя бы один вариант.'));return;} next(S.picked.join(', '));};
  var nx=document.getElementById('pnx'); if(nx)nx.onclick=function(){var t=(document.getElementById('pi').value||'').trim(); if(!t){alert(T('Жооп жазыңыз.','Введите ответ.'));return;} next(t);};
  var pd=document.getElementById('pdone'); if(pd)pd.onclick=function(){next(String((S.data.webPhotos||[]).length));};
  var pv=document.getElementById('pv'); if(pv)pv.onchange=function(){vupload(pv.files[0]);};
  var pvx=document.getElementById('pvx'); if(pvx)pvx.onclick=function(){delete S.data.webVideo;draw();};
  var pf=document.getElementById('pf'); if(pf)pf.onchange=function(){upload(Array.prototype.slice.call(pf.files));};
  var go=document.getElementById('pgo'); if(go)go.onclick=function(){go.disabled=true;
    api({op:'publish',step:S.step,data:S.data,title:document.getElementById('pt').value}).then(function(j){
      if(!j.ok){go.disabled=false;err(j.err);return;}
      box.innerHTML='<div class="pok">&#10003;</div><h2 style="text-align:center">'+T('Жарыяңыз жарыяланды!','Объявление опубликовано!')+'</h2><p style="text-align:center">№'+j.id+'</p><a class="pbtn" href="'+j.url+'">'+T('Жарыяны көрүү','Смотреть объявление')+'</a><a class="pbtn pbtn2" href="/post">'+T('Дагы жарыя берүү','Ещё объявление')+'</a>';
    }).catch(function(){go.disabled=false;err();});};
}
function vupload(f){if(!f)return;var st=document.getElementById('pvs');var mx=S.view.vmax*1024*1024;
  if(f.size>mx){alert(T('Видео өтө чоң. Максимум ','Видео слишком большое. Максимум ')+S.view.vmax+' MB.');return;}
  var x=new XMLHttpRequest();x.open('POST','/api/post/video?t='+encodeURIComponent(tok));
  x.upload.onprogress=function(e){if(e.lengthComputable)st.textContent=T('Видео жүктөлүүдө… ','Загрузка видео… ')+Math.round(e.loaded/e.total*100)+'%';};
  x.onload=function(){var j={};try{j=JSON.parse(x.responseText);}catch(e){}
    if(j.ok){S.data.webVideo=j.name;draw();}else{st.textContent='';
      alert(j.err==='vfmt'?T('Бул видео форматы колдоого алынбайт (MP4 керек).','Формат не поддерживается (нужен MP4).'):j.err==='verify'?T('Номерди кайра ырастаңыз.','Подтвердите номер снова.'):T('Видеону жүктөй албадык.','Не удалось загрузить видео.'));}};
  x.onerror=function(){st.textContent='';alert(T('Байланыш катасы.','Ошибка связи.'));};
  x.send(f);}
function shrink(f){return new Promise(function(res){var r=new FileReader();r.onload=function(){var im=new Image();im.onload=function(){
  var m=1600,w=im.width,h=im.height,k=Math.min(1,m/Math.max(w,h));var c=document.createElement('canvas');c.width=Math.round(w*k);c.height=Math.round(h*k);
  c.getContext('2d').drawImage(im,0,0,c.width,c.height);c.toBlob(function(b){res(b||f);},'image/jpeg',0.85);};im.onerror=function(){res(f);};im.src=r.result;};r.readAsDataURL(f);});}
function upload(files){var ph=S.data.webPhotos=S.data.webPhotos||[];var max=S.view.photo_max;var st=document.getElementById('pst');
  var q=files.slice(0,Math.max(0,max-ph.length));var i=0;
  function one(){if(i>=q.length){draw();return;} st.textContent=T('Жүктөлүүдө… ','Загрузка… ')+(i+1)+'/'+q.length;
    shrink(q[i]).then(function(b){return fetch('/api/post/photo?t='+encodeURIComponent(tok),{method:'POST',headers:{'Content-Type':'image/jpeg'},body:b});})
    .then(function(r){return r.json();}).then(function(j){if(j.ok)ph.push(j.name);else err(j.err);i++;one();}).catch(function(){i++;one();});}
  one();}
if(!tok){need();}else{var q0=(location.search.match(/[?&]s=([a-z]+)/)||[])[1];
  if(q0){api({op:'start',section:q0}).then(set).catch(function(){err();});}else{start();}}
})();
"""

_POST_CSS = """<style>/* PBACK4 */
.pwrap{max-width:520px;margin:0 auto;padding:16px 16px 140px}
.ptop{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.pback{width:52px;height:52px;flex:none;border-radius:14px;border:2px solid #17304F;background:#E6EDF6;display:flex;align-items:center;justify-content:center;padding:0;cursor:pointer}
.psec{font-weight:800;color:#3A4E6B}
.pq{font-size:19px;font-weight:700;line-height:1.4;margin:6px 0 14px;color:#0B1B30}
.popts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 10px}/* POPT_PILL POPT_GRID2 */
.popts .popt{text-align:center;padding:12px 10px;border-radius:26px;line-height:1.25;margin-bottom:0}
.popts .popt.pw{grid-column:1/-1}
.popt{min-height:52px;padding:12px 22px;border-radius:999px;border:1.5px solid #3A4E6B;background:#fff;color:#0B1B30;font-size:16px;font-weight:700;text-align:left;box-shadow:0 5px 14px rgba(23,48,79,.24);margin-bottom:4px}
.popt.on{background:#17304F;color:#fff;box-shadow:0 4px 0 #2E9E5B,0 7px 16px rgba(23,48,79,.30)}
.pbtn{display:block;width:100%;box-sizing:border-box;margin-top:14px;padding:16px;border:0;border-radius:14px;background:#17304F;color:#fff!important;font-size:17px;font-weight:800;text-align:center;text-decoration:none}
.pbtn2{background:#fff;color:#17304F!important;border:1.5px solid #3A4E6B}
.pbtn:disabled{opacity:.6}
.pfld{display:block;width:100%!important;max-width:none!important;box-sizing:border-box;margin-top:12px;padding:14px 16px;border-radius:16px;border:1.5px solid #3A4E6B;background:#fff;color:#0B1B30;font-size:17px;font-family:inherit;line-height:1.4;min-height:56px}/* PFLD */textarea.pfld{min-height:140px;resize:vertical}.pfld:focus{outline:none;border-color:#17304F;box-shadow:0 0 0 3px rgba(46,158,91,.35)}
.plab{display:block;margin-top:8px;font-weight:800}
.phint{font-size:14px;color:#3A4E6B;margin:8px 0;font-weight:600}
.pgrid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}
.pgrid img,.padd{aspect-ratio:1;width:100%;object-fit:cover;border-radius:12px}
.padd{display:flex;align-items:center;justify-content:center;border:2px dashed #3A4E6B;font-size:30px;color:#17304F;cursor:pointer;box-sizing:border-box}
.pvid{margin-top:12px}.pvid video{width:100%;max-height:260px;border-radius:12px;background:#000}
.psecg{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}/* PSEC_COMPACT */
.psc{display:flex;flex-direction:column;padding:0;border:1.5px solid #C9D2DE;border-radius:14px;background:#fff;overflow:hidden;cursor:pointer;min-width:0}
.psc img{display:block;width:100%;aspect-ratio:4/3;object-fit:cover}
.psc span{padding:5px 2px 7px;font-size:12px;font-weight:800;line-height:1.15;color:#0B1B30;text-align:center;overflow-wrap:anywhere}
.psec{display:flex;align-items:center;gap:8px}.psec img{width:34px;height:34px;border-radius:9px;object-fit:cover}
.pok{width:84px;height:84px;margin:30px auto 10px;border-radius:42px;background:#2E9E5B;color:#fff;font-size:46px;display:flex;align-items:center;justify-content:center}
</style>"""


def _post_sec_tiles(lang):   # POST_HOMETILES: башкы беттеги бөлүм такталары
    out = ""
    for code, ic, _nm in SECTIONS:
        nm = esc(section_name(code, lang))
        if secimg.has(code):
            inner = ('<span class="picw"><img class="pic" src="/si/%s.jpg?v=%s" alt="%s" '
                     'loading="lazy"></span><span class="pill">%s</span>'
                     % (code, secimg.VERSION, nm, nm))
            cls = "cat pic s-" + code
        else:
            inner = '<span class="ic">%s</span><span class="lb">%s</span>' % (ic, nm)
            cls = "cat"
        out += '<a href="/post?s=%s" data-s="%s" class="%s">%s</a>' % (code, code, cls, inner)
    return '<nav class="cats">%s</nav>' % out


# WEB_BAL: балансты сайтта көрсөтүү
def _web_balance(tok):
    st = _wverified(tok)
    if not st:
        return {"ok": False, "err": "verify"}
    uid = str(st["tg_id"])
    try:
        import rules
        b = dict(rules.balance(uid, "+996" + st["phone"]))
    except Exception as e:
        print("web_balance:", e, flush=True)
        return {"ok": False, "err": "server"}
    out = {"ok": True, "phone": "+996 " + st["phone"],
           "ref": "https://t.me/%s?start=ref%s" % (BOT, uid)}
    for k in ("used", "limit", "left", "bonus", "friends", "active", "soon"):
        try:
            out[k] = int(b.get(k) or 0)
        except Exception:
            out[k] = 0
    try:
        out["r1"], out["r2"], out["r3"] = (core.REF_FIRST_BONUS,
                                          core.REF_NEXT_BONUS, core.REF_JOIN_BONUS)
    except Exception:
        out["r1"] = out["r2"] = out["r3"] = 0
    return out


_BAL_JS = r"""
(function(){
var LANG=document.documentElement.getAttribute('data-lang')||'ky';
function T(k,r){return LANG==='ru'?r:k;}
var box=document.getElementById('bbox');
var tok=null; try{tok=localStorage.getItem('tap_vok');}catch(e){}
function esc(x){return String(x==null?'':x).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function need(){box.innerHTML='<p style="line-height:1.45">'+T('Балансты көрүү үчүн номериңизди ырастаңыз.','Чтобы увидеть баланс, подтвердите номер.')+'</p><a class="bbtn" href="/verify?next=bal">'+T('Номерди ырастоо','Подтвердить номер')+'</a>';}
function row(ic,lb,val){return '<div class="brow"><span class="bic">'+ic+'</span><span class="blb">'+lb+'</span><b>'+val+'</b></div>';}
function show(j){
  var pc=j.limit?Math.min(100,Math.round(j.used/j.limit*100)):0;
  var h='<div class="bph">'+esc(j.phone)+' · '+T('ырасталган','подтверждён')+'</div>';
  h+='<div class="bcard"><div class="bttl">'+T('Бүгүн коюлду','Сегодня размещено')+'</div>'
    +'<div class="bbig">'+j.used+' <span>/ '+j.limit+'</span></div>'
    +'<div class="bbar"><i style="width:'+pc+'%"></i></div>'
    +'<div class="bsub">'+T('Калды: ','Осталось: ')+'<b>'+j.left+'</b> '+T('жарыя','объявл.')+' · '+T('чек ар күнү жаңырат','лимит обновляется ежедневно')+'</div></div>';
  h+='<div class="bcard">'
    +row('🎁',T('Бонус жарыя','Бонусные объявления'),j.bonus)
    +row('👥',T('Чакырган досторуңуз','Приглашено друзей'),j.friends)
    +'<a class="blink" href="/my">'+row('📋',T('Активдүү жарыяларыңыз','Активные объявления'),j.active+' ›')+'</a>'
    +'<a class="blink" href="/my?f=soon">'+row('⏳',T('3 күндө бүтөт','Истекает через 3 дня'),j.soon+' ›')+'</a></div>';
  h+='<div class="bcard"><div class="bttl">'+T('Дос чакырып, бонус алыңыз','Приглашайте друзей — получайте бонусы')+'</div>'
    +'<div class="bsub" style="margin:6px 0 10px">'+T('Досуңуз биринчи жарыясын койгондо: 1-дос үчүн +','Когда друг разместит первое объявление: за 1-го друга +')+j.r1+', '
    +T('ар кийинкиси үчүн +','за каждого следующего +')+j.r2+', '+T('досуңузга +','другу +')+j.r3+'.</div>'
    +'<div class="bref">'+esc(j.ref)+'</div>'
    +'<button class="bbtn" id="bcp">'+T('Шилтемени көчүрүү','Скопировать ссылку')+'</button>'
    +'<a class="bbtn bbtn2" target="_blank" rel="noopener" href="https://t.me/share/url?url='+encodeURIComponent(j.ref)+'">'+T('Telegram аркылуу бөлүшүү','Поделиться в Telegram')+'</a>'
    +'<a class="bbtn bbtn2" target="_blank" rel="noopener" href="https://wa.me/?text='+encodeURIComponent(j.ref)+'">'+T('WhatsApp аркылуу бөлүшүү','Поделиться в WhatsApp')+'</a></div>';
  box.innerHTML=h;
  var cp=document.getElementById('bcp'); if(cp)cp.onclick=function(){
    try{navigator.clipboard.writeText(j.ref).then(function(){cp.textContent=T('Көчүрүлдү ✓','Скопировано ✓');});}catch(e){}};
}
if(!tok){need();return;}
fetch('/api/balance?t='+encodeURIComponent(tok)).then(function(r){return r.json();}).then(function(j){
  if(j.ok){show(j);}else if(j.err==='verify'){try{localStorage.removeItem('tap_vok');}catch(e){} need();}
  else{box.innerHTML='<p>'+T('Ката чыкты. Кийинчерээк кайра аракет кылыңыз.','Ошибка. Попробуйте позже.')+'</p>';}
}).catch(function(){box.innerHTML='<p>'+T('Байланыш катасы.','Ошибка связи.')+'</p>';});
})();
"""

_BAL_CSS = """<style>
.bwrap{max-width:520px;margin:0 auto;padding:16px 16px 140px}
.blink{display:block;color:inherit!important;text-decoration:none}
.bph{font-weight:700;color:#3A4E6B;margin:0 0 12px}
.bcard{background:#fff;border:1.5px solid #C9D2DE;border-radius:18px;padding:16px;margin-bottom:14px;box-shadow:0 5px 14px rgba(23,48,79,.14)}
.bttl{font-weight:800;font-size:16px;color:#0B1B30}
.bbig{font-size:34px;font-weight:800;color:#17304F;margin:6px 0}.bbig span{font-size:20px;color:#3A4E6B}
.bbar{height:10px;border-radius:5px;background:#E3E8EF;overflow:hidden}.bbar i{display:block;height:10px;background:#2E9E5B;border-radius:5px}
.bsub{font-size:14px;color:#2A3A52;line-height:1.45;margin-top:8px}
.brow{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #E3E8EF;font-size:16px}
.brow:last-child{border-bottom:0}.bic{width:28px;text-align:center}.blb{flex:1}.brow b{font-size:18px;color:#17304F}
.bref{padding:10px 12px;border-radius:12px;background:#EEF2F7;font-size:14px;word-break:break-all;color:#0B1B30}
.bbtn{display:block;width:100%;box-sizing:border-box;margin-top:10px;padding:15px;border:0;border-radius:14px;background:#17304F;color:#fff!important;font-size:16px;font-weight:800;text-align:center;text-decoration:none;cursor:pointer;font-family:inherit}
.bbtn2{background:#fff;color:#17304F!important;border:1.5px solid #3A4E6B}
</style>"""


def balance_page(lang="ky"):
    ru = lang == "ru"
    ttl = "Мой баланс" if ru else "Менин балансым"
    body = ('<main class="bwrap"><h1 style="font-size:24px;margin:0 0 8px">' + ttl + '</h1>'
            '<div id="bbox"></div>'
            '<p style="margin-top:18px;font-size:14px"><a href="https://t.me/' + BOT
            + '?start=balance">' + ("Открыть в Telegram-боте" if ru else "Telegram ботто ачуу")
            + '</a></p></main>' + _BAL_CSS
            + '<script>document.documentElement.setAttribute("data-lang",'
            + json.dumps(lang) + ');' + _BAL_JS + '</script>')
    return page(body, title=ttl, lang=lang)


# WEB_MY: Менин жарыяларым жана админге кабар
def _web_notify_admins(lid, row, uid, hits):
    tok = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not tok:
        try:
            tf = os.path.join(core.BASE, "token.txt")
            if os.path.exists(tf):
                tok = open(tf, encoding="utf-8").read().strip()
        except Exception:
            tok = ""
    admins = [x.strip() for x in (os.environ.get("ADMIN_IDS") or "").replace(" ", "").split(",")
              if x.strip()]
    if not tok or not admins:
        print("web_notify: TELEGRAM_BOT_TOKEN же ADMIN_IDS жок", flush=True)
        return
    site = (os.environ.get("SITE_URL") or "https://tapmeni.up.railway.app").rstrip("/")
    e = html.escape
    warn = ("⚠️ <b>Текшериңиз:</b> %s\n\n" % e(", ".join(str(h) for h in hits[:5]))) if hits else ""
    txt = (warn + "🆕 <b>Жаңы жарыя (сайттан)</b> №%d\n\n📦 %s\n💰 %s\n📍 %s\n☎️ %s\n👤 id %s\n"
           '🌐 <a href="%s/e/%d">Сайттан көрүү</a>'
           % (lid, e(str(row.get("title") or "")), e(_price(row.get("price"), "ky")),
              e(str(row.get("region") or row.get("oblast") or "—")),
              e(str(row.get("contact") or "—")), e(uid), site, lid))
    kb = json.dumps({"inline_keyboard": [[{"text": "❌ Өчүрүү", "callback_data": "adel:%d" % lid}]]})
    import urllib.request
    for a in admins:
        data = urllib.parse.urlencode({"chat_id": a, "text": txt, "parse_mode": "HTML",
                                       "disable_web_page_preview": "true",
                                       "reply_markup": kb}).encode()
        try:
            urllib.request.urlopen("https://api.telegram.org/bot%s/sendMessage" % tok,
                                   data=data, timeout=15).read()
        except Exception as ex:
            print("web_notify:", ex, flush=True)


def _web_my_list(tok, f, lang):
    st = _wverified(tok)
    if not st:
        return {"ok": False, "err": "verify"}
    rows = core.my_listings(st["tg_id"], "+996" + st["phone"]) or []
    out = []
    for r in rows[:150]:
        dl = core.days_left(r.get("expires_at"))
        act = str(r.get("is_active")) == "1"
        if f == "soon" and not (act and dl is not None and dl <= 3):
            continue
        try:
            ttl = bridge.show_title(r) or r.get("title") or "Жарыя"
        except Exception:
            ttl = r.get("title") or "Жарыя"
        out.append({"id": r["id"], "title": L(ttl, lang), "price": _price(r.get("price"), lang),
                    "photo": r.get("photo") or "", "active": act, "days": dl})
    return {"ok": True, "items": out}


def _web_my_act(b):
    st = _wverified(b.get("token"))
    if not st:
        return {"ok": False, "err": "verify"}
    try:
        lid = int(b.get("id"))
    except Exception:
        return {"ok": False, "err": "id"}
    ph = "+996" + st["phone"]
    if b.get("op") == "revive":
        ok = core.revive(lid, st["tg_id"], phone=ph)
    elif b.get("op") == "close":
        ok = core.deactivate(lid, st["tg_id"], ph)
    else:
        return {"ok": False, "err": "op"}
    return {"ok": bool(ok), "err": None if ok else "owner"}


_MY_JS = r"""
(function(){
var LANG=document.documentElement.getAttribute('data-lang')||'ky';
function T(k,r){return LANG==='ru'?r:k;}
var box=document.getElementById('mbox');
var F=(location.search.match(/[?&]f=([a-z]+)/)||[])[1]||'';
var tok=null; try{tok=localStorage.getItem('tap_vok');}catch(e){}
function esc(x){return String(x==null?'':x).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function need(){box.innerHTML='<p style="line-height:1.45">'+T('Жарыяларыңызды көрүү үчүн номериңизди ырастаңыз.','Чтобы увидеть объявления, подтвердите номер.')+'</p><a class="mbtn" href="/verify?next=my">'+T('Номерди ырастоо','Подтвердить номер')+'</a>';}
function st(it){if(!it.active)return '<span class="mst off">'+T('Жабык','Закрыто')+'</span>';
  if(it.days==null)return '<span class="mst">'+T('Активдүү','Активно')+'</span>';
  var w=it.days<=3?' warn':'';return '<span class="mst'+w+'">'+T('Активдүү · ','Активно · ')+Math.max(0,it.days)+T(' күн калды',' дн. осталось')+'</span>';}
function load(){
  fetch('/api/my?t='+encodeURIComponent(tok)+'&f='+F).then(function(r){return r.json();}).then(function(j){
    if(!j.ok){if(j.err==='verify'){try{localStorage.removeItem('tap_vok');}catch(e){} need();}else{box.innerHTML='<p>'+T('Ката чыкты.','Ошибка.')+'</p>';}return;}
    var h='<div class="mtabs"><a href="/my"'+(F?'':' class="on"')+'>'+T('Баары','Все')+'</a><a href="/my?f=soon"'+(F==='soon'?' class="on"':'')+'>'+T('3 күндө бүтөт','Истекают')+'</a></div>';
    if(!j.items.length){h+='<p class="mempty">'+(F?T('Жакында мөөнөтү бүтө турган жарыя жок.','Нет объявлений, которые скоро истекают.'):T('Азырынча жарыяңыз жок.','У вас пока нет объявлений.'))+'</p><a class="mbtn" href="/post">'+T('Жарыя берүү','Подать объявление')+'</a>';}
    j.items.forEach(function(it){
      h+='<div class="mit"><a class="mimg" href="/e/'+it.id+'">'+(it.photo?'<img src="/media/'+esc(it.photo)+'" alt="" loading="lazy">':'')+'</a>'
        +'<div class="minf"><a class="mttl" href="/e/'+it.id+'">'+esc(it.title)+'</a><div class="mpr">'+esc(it.price)+'</div>'+st(it)
        +'<div class="mact"><button data-op="revive" data-id="'+it.id+'">'+(it.active?T('🔄 Узартуу','🔄 Продлить'):T('🔄 Кайра жандыруу','🔄 Возобновить'))+'</button>'
        +(it.active?'<button class="mx" data-op="close" data-id="'+it.id+'">'+T('Жабуу','Закрыть')+'</button>':'')+'</div></div></div>';});
    box.innerHTML=h;
    box.querySelectorAll('[data-op]').forEach(function(b){b.onclick=function(){
      var op=b.getAttribute('data-op');
      if(op==='close'&&!confirm(T('Жарыяны жабасызбы?','Закрыть объявление?')))return;
      b.disabled=true;
      fetch('/api/my',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:tok,op:op,id:+b.getAttribute('data-id')})})
      .then(function(r){return r.json();}).then(function(x){if(!x.ok){alert(T('Ката чыкты.','Ошибка.'));b.disabled=false;return;} load();})
      .catch(function(){b.disabled=false;alert(T('Байланыш катасы.','Ошибка связи.'));});};});
  }).catch(function(){box.innerHTML='<p>'+T('Байланыш катасы.','Ошибка связи.')+'</p>';});}
if(!tok){need();}else{load();}
})();
"""

_MY_CSS = """<style>
.mwrap{max-width:560px;margin:0 auto;padding:16px 16px 140px}
.mtabs{display:flex;gap:8px;margin:0 0 14px}
.mtabs a{padding:10px 16px;border-radius:999px;border:1.5px solid #3A4E6B;color:#0B1B30;text-decoration:none;font-weight:700;background:#fff}
.mtabs a.on{background:#17304F;color:#fff}
.mit{display:flex;gap:12px;padding:12px;margin-bottom:12px;background:#fff;border:1.5px solid #C9D2DE;border-radius:18px;box-shadow:0 5px 14px rgba(23,48,79,.12)}
.mimg{flex:none;width:92px;height:92px;border-radius:14px;overflow:hidden;background:#E3E8EF}
.mimg img{width:100%;height:100%;object-fit:cover}
.minf{flex:1;min-width:0}
.mttl{display:block;font-weight:800;color:#0B1B30;text-decoration:none;line-height:1.3;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.mpr{font-weight:800;color:#17304F;margin:4px 0}
.mst{display:inline-block;font-size:13px;font-weight:700;padding:4px 10px;border-radius:999px;background:#E3F5EA;color:#155C33}
.mst.warn{background:#FFF1D6;color:#7A4B00}.mst.off{background:#E3E8EF;color:#3A4E6B}
.mact{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
.mact button{padding:9px 14px;border-radius:12px;border:0;background:#17304F;color:#fff;font-weight:800;font-family:inherit;font-size:14px;cursor:pointer}
.mact button.mx{background:#fff;color:#8A1C1C;border:1.5px solid #8A1C1C}
.mact button:disabled{opacity:.6}
.mempty{color:#2A3A52}
.mbtn{display:block;width:100%;box-sizing:border-box;margin-top:10px;padding:15px;border-radius:14px;background:#17304F;color:#fff!important;font-weight:800;text-align:center;text-decoration:none}
</style>"""


def my_page(lang="ky"):
    ru = lang == "ru"
    ttl = "Мои объявления" if ru else "Менин жарыяларым"
    body = ('<main class="mwrap"><h1 style="font-size:24px;margin:0 0 12px">' + ttl + '</h1>'
            '<div id="mbox"></div></main>' + _MY_CSS
            + '<script>document.documentElement.setAttribute("data-lang",'
            + json.dumps(lang) + ');' + _MY_JS + '</script>')
    return page(body, title=ttl, lang=lang)


def post_page(lang="ky"):
    ru = lang == "ru"
    body = ('<main class="pwrap" data-lang="%s" data-siv="%s"><h1 style="font-size:24px;margin:0 0 12px">%s</h1>'
            '<div id="pbox"></div></main>%s<script>document.documentElement.setAttribute("data-lang",%s);%s</script>'
            % (lang, esc(str(secimg.VERSION)), "Подать объявление" if ru else "Жарыя берүү", _POST_CSS,
               json.dumps(lang), _POST_JS))
    body = body.replace('<div id="pbox"></div>', '<template id="psecs">' + _post_sec_tiles(lang) + '</template><div id="pbox"></div>', 1)
    return page(body, title=("Подать объявление" if ru else "Жарыя берүү"), lang=lang)


def verify_page(lang="ky"):
    ru = lang == "ru"
    t = (lambda k, r: r if ru else k)
    body = f"""<main style="max-width:480px;margin:0 auto;padding:20px 16px 120px">
<h1 style="font-size:24px;margin:0 0 8px">{t("Номериңизди ырастаңыз", "Подтвердите номер")}</h1>
<p style="margin:0 0 16px;line-height:1.45">{t("Сайттан жарыя берүү үчүн номериңиз Telegram аркылуу ырасталат.", "Для объявлений с сайта номер подтверждается через Telegram.")}</p>
<div id="vf1">
<label for="vph" style="display:block;font-weight:800;margin-bottom:6px">{t("Телефон номери", "Номер телефона")}</label>
<div style="display:flex;align-items:center;border:1.5px solid #9AA8BA;border-radius:12px;background:#fff;overflow:hidden">
<span style="padding:0 12px;font-weight:800;font-size:17px">+996</span>
<input id="vph" inputmode="tel" placeholder="700 123 456" style="flex:1;min-width:0;height:52px;border:0;font-size:17px;font-weight:700;background:transparent">
</div>
<button id="vgo" type="button" style="margin-top:14px;width:100%;height:56px;border:0;border-radius:14px;background:#1F7FC4;color:#fff;font-size:16px;font-weight:800">{t("Telegram аркылуу ырастоо", "Подтвердить через Telegram")}</button>
<p id="verr" style="color:#B3261E;font-weight:700;min-height:20px"></p>
</div>
<div id="vf2" style="display:none;padding:14px;border-radius:14px;background:#EAF3FB;font-weight:700;line-height:1.45">
{t("Telegram ачылды. Ботто «📱 Номеримди жөнөтүү» баскычын басып, ушул бетке кайтыңыз.", "Откройте Telegram, нажмите «📱 Номеримди жөнөтүү» и вернитесь сюда.")}
<div style="margin-top:10px"><a id="vlink" href="#" target="_blank" rel="noopener">{t("Telegram ачылбаса, бул жерди басыңыз", "Если Telegram не открылся — нажмите здесь")}</a></div>
</div>
<div id="vf3" style="display:none;padding:16px;border-radius:14px;background:#E3F5EA;color:#155C33;font-weight:800;font-size:17px">✅ {t("Номериңиз ырасталды!", "Номер подтверждён!")}<div style="margin-top:12px"><a href="/post" style="color:#155C33">{t("Жарыя берүү →", "Подать объявление →")}</a></div></div>
</main>
<script>
(function(){{
  var tok=null, timer=null, left=300;
  function $(i){{return document.getElementById(i);}}
  function poll(){{
    if(!tok||left--<=0){{return;}}
    fetch('/api/verify/status?t='+encodeURIComponent(tok)).then(function(r){{return r.json();}})
    .then(function(j){{
      if(j.verified){{clearInterval(timer);$('vf2').style.display='none';$('vf3').style.display='block';
        try{{localStorage.removeItem('tap_vtok');localStorage.setItem('tap_vok',tok);}}catch(e){{}}var nx=(location.search.match(/next=([a-z]+)/)||[])[1];if(nx==='post'||nx==='bal'||nx==='my'){{location.href='/'+nx;}}}}
    }}).catch(function(){{}});
  }}
  function wait(link){{
    $('vf1').style.display='none';$('vf2').style.display='block';$('vlink').href=link;
    clearInterval(timer);timer=setInterval(poll,3000);
  }}
  try{{var s=JSON.parse(localStorage.getItem('tap_vtok')||'null');
    if(s&&s.tok&&Date.now()-s.at<15*60*1000){{tok=s.tok;wait(s.link);}}}}catch(e){{}}
  $('vgo').onclick=function(){{
    var d=($('vph').value||'').replace(/[^0-9]/g,'');
    if(d.length<9){{$('verr').textContent='{t("Номерди толук жазыңыз (9 сан).", "Введите номер полностью (9 цифр).")}';return;}}
    $('verr').textContent='';
    fetch('/api/verify/start?phone='+d).then(function(r){{return r.json();}}).then(function(j){{
      if(!j.ok){{$('verr').textContent='{t("Ката. Кайра аракет кылыңыз.", "Ошибка. Попробуйте снова.")}';return;}}
      tok=j.token;
      try{{localStorage.setItem('tap_vtok',JSON.stringify({{tok:tok,link:j.link,at:Date.now()}}));}}catch(e){{}}
      wait(j.link);window.location.href=j.link;
    }}).catch(function(){{$('verr').textContent='{t("Байланыш катасы.", "Ошибка связи.")}';}});
  }};
}})();
</script>"""
    return page(body, title=t("Номер ырастоо", "Подтверждение номера"), lang=lang)


# CARD_GRID: жарыялар эки мамычалуу плитка (сүрөт, баа, аталыш, жер)
EXTRA_CSS += chr(10) + '.g{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:14px 12px!important}.g .c,.srow .c{display:flex!important;flex-direction:column!important;padding:0!important;background:transparent!important;box-shadow:none!important;border:0!important;min-width:0}.srow .c{flex:0 0 46%!important;max-width:46%!important}.g .c .ph,.srow .c .ph{position:relative;width:100%!important;height:auto!important;aspect-ratio:1/1;flex:none!important;border-radius:16px!important;overflow:hidden}.g .c .ph img,.srow .c .ph img{width:100%!important;height:100%!important;object-fit:cover}.g .c .cb,.srow .c .cb{padding:8px 4px 0!important;min-width:0}.g .c .p,.srow .c .p{font-size:17px!important;font-weight:800!important;margin:0 0 2px!important}.g .c .t,.srow .c .t{font-size:14.5px!important;font-weight:500!important;line-height:1.3!important;margin:0!important;display:-webkit-box!important;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.g .c .rgl,.srow .c .rgl{font-size:13.5px!important;color:#5A6B82!important;margin-top:3px!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.g .c .sbt,.g .c .m,.srow .c .sbt,.srow .c .m{display:none!important}'


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
<div class="tin"><a href="/" class="logo"><img class="lgi" src="/pwa/icon-192.png?v={appicon.VERSION}" alt=""><span>ТАП!</span></a><style>.logo .lgi{{width:30px;height:30px;border-radius:9px;margin-right:7px;display:block;object-fit:cover}}</style>
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

    parts = []
    for k in ("oblast", "district", "locality", "village"):
        x = sh(r.get(k))
        if x and (not parts or parts[-1] != x):
            parts.append(x)
    if not parts and r.get("region"):
        parts = [sh(r.get("region"))]
    out = ""
    for i, x in enumerate(parts):
        out += f'<div class="rg{" rg2" if i else ""}">{esc(x)}</div>'
    return out  #RG4


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
        if len(d) >= 11:
            return "wa"
        return "tg"
    return ""


def _cta(r):
    """Карточкадагы баскыч: жарыя кайдан коюлса ошол. #SRC_CTA"""
    intl = _intl(r.get("contact"))
    if not intl:
        return ""
    _h = lambda u: base64.b64encode(u.encode()).decode("ascii")  # NUMHIDE
    wa = ('<button class="cta wa" onclick="tapGo(event,this)"'
          ' data-h="%s" aria-label="WhatsApp">%s</button>'
          % (_h("https://wa.me/" + intl), _CWA))
    tg = ('<button class="cta tg" onclick="tapGo(event,this)"'
          ' data-h="%s" aria-label="Telegram">%s</button>'
          % (_h("https://t.me/+" + intl), _CTG))
    return wa + tg  #CTA2


def _sago(ts, lang="ky"):
    """Карточка үчүн кыска убакыт: «мурун/назад» жок. #SAGO"""
    t = ago(ts, lang)
    for w in (" мурун", " назад"):
        if t.endswith(w):
            return t[:-len(w)]
    return t


def _subline(r, lang="ky"):
    """Карточка: категория · подкатегория. #SUBL2"""
    c = bridge.cat_label(r.get("cat_id")) or ""
    if c:
        pp = c.split(" / ")
        c = pp[-1] if lang == "ru" and len(pp) > 1 else pp[0]
    s = sub_title(r.get("category"), r.get("subcat")) or ""
    s = _ky(s, lang) if s else ""
    if s.strip().lower() in ("башка", "башкалар", "другое", "другие", "прочее"):
        s = ""
    t = str(L(bridge.show_title(r), lang) or "").strip().lower()
    parts = []
    for x in (c, s):
        x = _ky(str(x or '').strip(), lang)  #SBT_KY2
        x = str(x or "").strip()
        if x and x.lower() != t and x.lower() not in [y.lower() for y in parts]:
            parts.append(x)
    if not parts:
        return ""
    return f'<div class="sbt">{esc(" · ".join(parts))}</div>'


_PIN = ('<svg viewBox="0 0 24 24" width="13" height="13" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0'
        'c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>')


def _reg_line1(r, lang="ky"):
    """Карточка: аймак бир сапта. #HC1"""
    parts = []
    for k in ("oblast", "district", "locality", "village"):
        x = str(r.get(k) or "").strip()
        x = _short_place(_place_name(x, lang)) if x else ""
        if x and x not in parts:
            parts.append(x)
    if not parts and r.get("region"):
        parts = [_short_place(_place_name(str(r.get("region")), lang))]
    if not parts:
        return ""
    return f'<div class="rgl">{_PIN}<span>{esc(" · ".join(parts))}</span></div>'


_SHI = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round"><circle cx="6" cy="12" r="2.6"/>'
        '<circle cx="18" cy="6" r="2.6"/><circle cx="18" cy="18" r="2.6"/>'
        '<path d="M8.3 10.8l7.4-3.6M8.3 13.2l7.4 3.6"/></svg>')
_CAM = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M4 8h3l2-2.5h6L17 8h3v11H4z"/><circle cx="12" cy="13" r="3.4"/></svg>')


def _shbtn(r, lang="ky"):
    """Карточка: бөлүшүү баскычы, өз алдынча JS. #SHPC2"""
    t = str(L(bridge.show_title(r), lang) or "")
    ok = "Шилтеме көчүрүлдү" if lang != "ru" else "Ссылка скопирована"
    js = ("event.preventDefault();event.stopPropagation();"
          "var u=location.origin+'/e/" + str(r["id"]) + "',"
          "t=this.dataset.t,ok=this.dataset.ok;"
          "if(navigator.share){navigator.share({title:t,text:t,url:u})"
          ".catch(function(){});return false}"
          "var a=document.createElement('textarea');a.value=u;"
          "document.body.appendChild(a);a.select();"
          "try{document.execCommand('copy')}catch(e){}"
          "a.remove();alert(ok);return false")
    return ('<button class="csh" type="button" aria-label="Share" '
            'data-t="' + esc(t) + '" data-ok="' + ok + '" '
            'onclick="' + js + '">' + _SHI + '</button>')


def _pcount(r):
    """Карточка: сүрөттөрдүн саны."""
    if not r.get("photo"):
        return ""
    try:
        n = len(core.photo_list(r) or []) or 1
    except Exception:
        n = 1
    return f'<span class="pcnt">{_CAM}{n}</span>'


def card(r, lang="ky"):
    has = bool(r.get("photo"))
    img = (f'<img src="/media/{esc(r["photo"])}" alt="" loading="lazy">'
           if has else
           ph_block(r, lang))
    return f"""<a class="c{'' if has else ' nophoto'}" href="/e/{r['id']}">
<div class="ph">{img}{_shbtn(r, lang)}<button class="fav" data-id="{r['id']}" aria-label="Тандалганга кошуу">{NAV_ICONS['fav']}</button></div>
<div class="cb"><div class="p{' pd' if is_deal(r['price']) else ''}">{esc(_price(r['price'], lang))}</div>
<h2 class="t">{esc(L(bridge.show_title(r), lang))}</h2>
{_subline(r, lang)}
{_reg_line1(r, lang)}
<div class="m"><span>{esc(_sago(r['created_at'], lang))}</span>{_pcount(r)}{'<span class="vmark">🎬</span>' if core.video_of(r) else ''}
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
            pic = f'<img src="/si/{at}.jpg?v={secimg.VERSION}" alt="" loading="lazy">'
        on = " on" if cid == c else ""
        href = f"/?at={at}&cid={esc(c)}{_obq(ob)}"
        out += (f'<a class="ct{on}" href="{href}">'
                f'<div class="cti">{pic}<span class="ctn">{n}</span></div>'
                f'<div class="ctl">{_ce(c)}{esc(cat_label(at, c, lang))}</div></a>')
    return _TILES_CSS + f'<nav class="ctiles">{out}</nav>'


# CAT_CHIPS: категорияларды чип катары кылып көрсөтүү
_CAT_CHIPS_CSS = ('<style>.regcat{display:flex;gap:8px;overflow-x:auto;'
                  'scrollbar-width:none;padding:5px 14px 6px;margin:0}'  # CHIP_TIGHT
                  '.regcat::-webkit-scrollbar{display:none}'
                  '.regcat .rg{flex:none;padding:7px 10px;font-size:13px;''letter-spacing:-.2px}'  # CHIP_NARROW
                  '.regcat{gap:6px}'
                  '.rglb{padding-top:6px}'   # CHIP_SPACE
                  '</style>')


def _chips_row(label, opts, cur, lang):
    """Тандоо тизмесинин ордуна горизонталдуу чиптер.

    Жарыясы бар категориялар гана көрсөтүлөт. Эгер андай категория
    жок болсо, баары көрсөтүлөт (тизме бош калбасын).
    """
    live = opts   # CHIP_ALL: бардык категориялар ар дайым көрүнөт
    out = ""
    for code, href, nm, n in live:
        out += _chip(href, nm, code == cur, n or 0, lang, short=False)
    return (f'<div class="rglb">{esc(label)}</div>'
            f'<nav class="regcat">{out}</nav>')


def _filter_bars(link, q, at, cid, sid, ob, di, vi, lang, sort="new",
                 vv=None):
    """Бөлүм жана аймак чыпкалары — тандоо тизмелери менен."""
    ru = (lang == "ru")
    flt = {"q": q or None, "ad_type": at, "cat_id": cid, "sub_id": sid}
    out = _CAT_CHIPS_CSS   # CHIP_FIX: стиль ар дайым жүктөлсүн

    # ── Эмне издеп жатасыз: категория → субкатегория ──────────
    if at:
        cc = core.catid_counts(at, ob, di, vv, q or None, sid,
                               locality=vi)
        items = list(cat_labels(at, lang).items())
        items.sort(key=lambda x: (-cc.get(x[0], 0), x[1]))
        opts = [(None, link(cid=None, sid=None),
                 "Все" if ru else "Баары", sum(cc.values()))]
        for code, nm in items:
            opts.append((code, link(cid=code, sid=None),
                         _ce(code) + nm, cc.get(code, 0)))
        inner = _chips_row("Категория", opts, cid, lang)

        if cid:
            sc = core.subid_counts(at, cid, ob, di, vv, q or None,
                                   locality=vi)
            whole = "Вся категория" if ru else "Бүт категория"
            opts = [(None, link(sid=None), whole, None)]
            if at == "taxi" and cid == "taxi_airport":   # TAXI_AIR
                sc = {k: sc.get(k, 0) for k in TAXI_AIRPORT_SUBS}
                _items = list(sc.items())
            else:
                _items = sorted(sc.items(), key=lambda x: (-x[1], x[0]))
            for code, n in _items:
                opts.append((code, link(sid=code), _ky(code, lang), n))
            if len(opts) > 1:
                inner += _chips_row("Субкатегория", opts, sid, lang)

        # QUICKFLT: бөлүмгө жараша тез чыпкалар
        # QUICKFLT2: категория тандалганда гана чыгат
        _QF = {("vehicle", "vehicles"): (("Марка", "Марка", _CAR_BRANDS),
                                         ("Куяр май", "Топливо", _CAR_FUEL)),
               ("property", "re_residential"): (("Бөлмө", "Комнат", _HOME_ROOMS),)}
        _key = (at or "", "vehicles" if str(cid or "").startswith("veh_")
                else (cid or ""))
        for _kt, _rt, vals in _QF.get(_key, ()):
            ttl = _rt if ru else _kt
            rows = []
            _bc = {}
            if _kt == "Марка":   # BRAND_TITLE
                try:
                    for _r in core.find(None, limit=500, ad_type=at,
                                        cat_id=cid or None, sub_id=sid or None,
                                        oblast=ob or None, district=di or None,
                                        locality=vi or None, village=vv or None):
                        _b = _brand_of(_r)
                        if _b:
                            _bc[_b] = _bc.get(_b, 0) + 1
                except Exception:
                    pass
            for v in vals:
                if _kt == "Марка":
                    n = _bc.get(v, 0)
                    if n:
                        rows.append((v, n))
                    continue
                try:
                    n = core.count(q=v, ad_type=at, cat_id=cid or None,
                                   sub_id=sid or None, oblast=ob or None,
                                   district=di or None)
                except Exception:
                    n = 0
                if n:
                    rows.append((v, n))
            if not rows:
                continue
            rows.sort(key=lambda x: (-x[1], x[0]))
            cur = q if (q or "") in vals else None
            opts = [(None, link(q=None), "Все" if ru else "Баары", None)]
            for v, n in rows[:12]:
                opts.append((v, link(q=v), v, n))
            inner += _chips_row(ttl, opts, cur, lang)

        out += _group("Что вы ищете" if ru else "Эмне издеп жатасыз", inner)

    else:
        # CHIP_FIX: бөлүм тандала элек — бөлүмдөрдүн чиптери
        try:
            ac = core.adtype_counts(ob)
        except Exception:
            ac = {}
        opts = [(None, link(at=None, cid=None, sid=None),
                 "Все" if ru else "Баары", sum(ac.values()))]
        for code, _ic, _nm in SECTIONS:
            opts.append((code, link(at=code, cid=None, sid=None),
                         section_name(code, lang), ac.get(code, 0)))
        out += _group("Что ищете" if ru else "Эмне издеп жатасыз",
                      _chips_row("Раздел" if ru else "Бөлүм", opts, at, lang))

    # VILLAGE_TOP: аймак чыпкалары жогорку тилкеге көчтү

    # ── Тартиби: жаңысынан, арзандан, кымбаттан ───────────────
    names = ([("new", "Сначала новые"), ("cheap", "Сначала дешёвые"),
              ("rich", "Сначала дорогие"), ("views", "Популярные")] if ru else
             [("new", "Жаңысынан"), ("cheap", "Арзандан"),
              ("rich", "Кымбаттан"), ("views", "Көп көрүлгөн")])
    opts = [(code, link(sort=code), nm, None) for code, nm in names]
    inner = _chips_row("Сортировка" if ru else "Тартиби", opts,
                       sort or "new", lang)
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
    nav = f'<nav class="cats">{cats}</nav>'
    if not at:   # SECFOLD: башкы бетте баары көрүнөт
        return nav
    _t = ("Все разделы" if lang == "ru" else "Бардык бөлүмдөр")
    _c = len(SECTIONS) + 1
    return ('<style>.secfold{margin:10px 12px 2px}'
            '.secfold>summary{list-style:none;cursor:pointer;'
            'display:flex;align-items:center;justify-content:center;gap:8px;'
            'padding:11px 14px;border-radius:20px;font-weight:700;font-size:14px;'
            'background:var(--card,#F7FAFF);border:1.5px solid var(--mist,#E3E8F0);'
            'box-shadow:0 4px 12px rgba(16,24,40,.18)}'
            '.secfold>summary::-webkit-details-marker{display:none}'
            '.secfold>summary i{font-style:normal;opacity:.6;font-weight:600}'
            '.secfold[open]>summary{margin-bottom:2px}'
            '.secfold .cats{padding-top:4px}</style>'
            f'<details class="secfold"><summary>🗂 {esc(_t)}'
            f'<i>{_c}</i> ▾</summary>{nav}</details>')


def _obq(ob):
    """Шилтемеге «&ob=…» кошот (аймак тандалган болсо)."""
    return ("&" + urllib.parse.urlencode({"ob": ob})) if ob else ""


_HOME_ROOMS = ("Студия", "1-бөлмө", "2-бөлмө", "3-бөлмө",
               "4-бөлмө", "5+бөлмө")

_CAR_FUEL = ("Бензин", "Дизель", "Газ", "Электр", "Гибрид", "Плагин-гибрид")

_CAR_BRANDS = ("Toyota", "Mercedes-Benz", "Honda", "Hyundai", "Kia",
               "Lexus", "BMW", "Nissan", "Daewoo", "Lada (ВАЗ)", "Audi",
               "Volkswagen", "Mitsubishi", "Chevrolet", "Opel", "Subaru",
               "Mazda", "Ford", "Chery", "Changan", "Haval", "BYD", "Geely")


# BRAND_TITLE: марка аталыштын башынан аныкталат (текст издөө эмес)
def _brand_keys(v):
    v = v.lower()
    ks = {v, v.split(" (")[0], v.split("-")[0]}
    if v.startswith("lada"):
        ks |= {"ваз", "лада"}
    if v.startswith("mercedes"):
        ks |= {"мерседес"}
    return tuple(k for k in ks if k)


def _brand_of(r):
    try:
        t = (bridge.show_title(r) or "").lower().strip()
    except Exception:
        t = (r.get("title") or "").lower().strip()
    for v in _CAR_BRANDS:
        if t.startswith(_brand_keys(v)):
            return v
    return None


def _brand_rows(v, **flt):
    try:
        rows = core.find(None, limit=500, **flt)
    except Exception:
        return []
    return [r for r in rows if _brand_of(r) == v]


def _regions_strip(link0, ob, lang, at=None, q=None, di=None, vi=None,
                   vv=None):
    # VILLAGE_TOP: жогорку тилкенин шилтемелери айылды тазалайт
    link = lambda **kw: link0(**{"vv": None, **kw})
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
    # ALL_COUNT: «Бүт Кыргызстан» чибинде да жалпы сан турсун
    try:
        _all_n = core.count(ad_type=at, q=q or None)
    except Exception:
        _all_n = sum(oc.values()) if oc else 0
    out = _chip(link(ob=None, di=None, vi=None), T("all_kg", lang),
                not ob, _all_n, lang, short=False)
    for rg in _by_count(list(OBLASTS), oc):
        out += _chip(link(ob=rg, di=None, vi=None), rg,
                     ob == rg, oc.get(rg, 0), lang)
    # REGBAR2: облус тандалса — анын райондору экинчи катар
    row2 = ""
    if ob:
        try:
            dc = core.district_counts(ob, ad_type=at, q=q or None)
        except Exception:
            try:
                dc = core.district_counts(ob)
            except Exception:
                dc = {}
        dc = dc or {}
        try:
            ds = list(get_districts(ob)) or list(core.used_districts(ob))
        except Exception:
            ds = []
        if ds:
            _o = str(ob).lower()
            if "шаар" in _o or "город" in _o or _o.endswith(" ш."):
                whole = "Весь город" if lang == "ru" else "Бүт шаар"
            else:
                whole = T("all_oblast", lang)
            r2 = _chip(link(ob=ob, di=None, vi=None), whole, not di, oc.get(ob, 0), lang, short=False)
            for x in _by_count(list(ds), dc):
                r2 += _chip(link(ob=ob, di=x, vi=None), x, di == x, dc.get(x, 0), lang)
            row2 = ('<style>.regbar2{margin-top:0;padding-top:4px;padding-bottom:8px}</style>'
                    f'<nav class="regbar regbar2">{r2}</nav>')
    # REGBAR3: район тандалса — анын айылдары/кичи райондору үчүнчү катар
    row3 = ""
    if ob and di:
        try:
            vc = core.village_counts(ob, di, ad_type=at, q=q or None)
        except Exception:
            try:
                vc = core.village_counts(ob, di)
            except Exception:
                vc = {}
        vc = vc or {}
        try:
            vs = list(get_localities(ob, di)) or list(core.used_villages(ob, di))
        except Exception:
            vs = []
        if vs:
            _d3 = str(di).lower()
            if "шаар" in _d3 or "город" in _d3 or _d3.endswith(" ш."):
                whole3 = "Весь город" if lang == "ru" else "Бүт шаар"
            else:
                whole3 = "Весь район" if lang == "ru" else "Бүт район"
            try:
                _d_n = core.count(oblast=ob, district=di, ad_type=at, q=q or None)
            except Exception:
                _d_n = 0
            r3 = _chip(link(ob=ob, di=di, vi=None), whole3, not vi, _d_n, lang,
                       short=False)
            for x in _by_count(list(vs), vc):
                r3 += _chip(link(ob=ob, di=di, vi=x), x, vi == x, vc.get(x, 0), lang)
            row3 = ('<style>.regbar3{margin-top:0;padding-top:4px;padding-bottom:10px}</style>'
                    f'<nav class="regbar regbar3">{r3}</nav>')
    # VILLAGE_TOP: айыл аймагы тандалса — анын айылдары төртүнчү катар
    row4 = ""
    if ob and di and vi:
        try:
            gc = core.villages_in(ob, di, vi, ad_type=at, q=q or None)
        except Exception:
            gc = {}
        gc = gc or {}
        try:
            gs = list(get_villages(ob, di, vi))
        except Exception:
            gs = []
        if gs:
            whole4 = "Все сёла" if lang == "ru" else "Бүт айылдар"
            r4 = _chip(link(ob=ob, di=di, vi=vi), whole4, not vv,
                       sum(gc.values()) if gc else None, lang, short=False)
            for x in _by_count(list(gs), gc):
                r4 += _chip(link(ob=ob, di=di, vi=vi, vv=x), x, vv == x,
                            gc.get(x, 0), lang)
            row4 = ('<style>.regbar4{margin-top:0;padding-top:4px;padding-bottom:10px}</style>'
                    f'<nav class="regbar regbar4">{r4}</nav>')
    # REGBAR1_WRAP: облустар сыдырылбайт, эки катарга жайылат
    css = ('<style>html,body{overflow-x:hidden;max-width:100%}'   # FIT_X
           '.fbox,.regcat,.regbar,.subbar{max-width:100%;box-sizing:border-box}'
           '.regbar1{flex-wrap:wrap;overflow-x:hidden;row-gap:7px;'
           'gap:7px;padding-bottom:6px}'
           '.regbar1 .rg{flex:1 1 auto;min-width:0;max-width:100%;text-align:center;padding:8px 12px;font-size:13.5px}</style>')  # REGBAR1_JUSTIFY
    # SECCHIP: тандалган бөлүмдүн аты — аймак чиптеринин үстүндө, узун чип
    sec = ""
    if at:
        _nm = esc(section_name(at, lang))
        _n = f' <em>{_all_n}</em>' if _all_n else ""
        sec = ('<style>.regsec{padding-bottom:2px}'
               '.regsec .rg{flex:1 1 100%;max-width:100%;text-align:center;'
               'font-weight:800;font-size:14px;padding:10px 14px}'
               '.regsec .rg em{font-style:normal;opacity:.85;margin-left:4px}'
               '.regsec .x{margin-left:8px;opacity:.7;font-weight:700}</style>'
               '<nav class="regbar regsec">'
               f'<a href="{link(at=None, cid=None, sid=None)}" class="rg on">'
               f'{_nm}{_n}<span class="x">✕</span></a></nav>')
    return (css + sec + f'<nav class="regbar regbar1">{out}</nav>'
            + row2 + row3 + row4)


# PERF_PATCH: башкы бет ондогон суроо жасайт. Даяр HTML'ди бир нече
# секунд эстеп турабыз; жаңы жарыя кошулса, core.version() өзгөрүп кэш
# өзү жаңыланат.
SHELF_TTL = int(os.environ.get("SHELF_TTL", "45"))

# GUARD3: бир IP бир мүнөттө канча бет ача алат (0 — чектөө жок)
RATE_MAX = int(os.environ.get("RATE_MAX", "150"))
_RATE = {}
_RATE_LOCK = __import__("threading").Lock()
_SHELF_CACHE = {}


def shelves(lang="ky", ob=None):
    key = (lang, ob or "")
    now = _t.time()
    hit = _SHELF_CACHE.get(key)
    if hit and hit[0] > now and hit[1] == core.version():
        return hit[2]
    out = _shelves(lang, ob)
    if len(_SHELF_CACHE) > 200:
        _SHELF_CACHE.clear()
    _SHELF_CACHE[key] = (now + SHELF_TTL, core.version(), out)
    return out


def _shelves(lang="ky", ob=None):
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
            _em = cat_emoji(cid)
            chips += (f'<button class="sb2" data-sec="{code}" data-cid="{esc(cid)}">'
                      f'{(_em + " ") if _em else ""}{esc(cat_label(code, cid, lang))}'
                      f' <em>{n}</em></button>')
        out.append(
            f'<section class="shelf" id="sh-{code}">'
            f'<div class="shead"><h2>{esc(section_name(code, lang))}</h2>'
            f'<a href="/?at={code}{_obq(ob)}" class="more">'
            f'{T("show_all", lang)} ›</a></div>'
            f'<nav class="subbar shchips" data-ob="{esc(ob or "")}">{chips}</nav>'
            '<div class="swrap">'
            '<button class="sarr" type="button" aria-label="prev" '
            'onclick="this.nextElementSibling.scrollBy({left:-this.nextElementSibling.clientWidth*0.8,behavior:\'smooth\'})">&#8249;</button>'
            f'<div class="srow" id="row-{code}">'
            f'{"".join(card(r, lang) for r in rows)}</div>'
            '<button class="sarr sr" type="button" aria-label="next" '
            'onclick="this.previousElementSibling.scrollBy({left:this.previousElementSibling.clientWidth*0.8,behavior:\'smooth\'})">&#8250;</button>'
            '</div></section>')
    return "".join(out)


def home(q, at=None, cid=None, sid=None, ob=None, di=None, vi=None,
         lang="ky", sort="new", vv=None):
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
               "ob": ob, "di": di, "vi": vi, "vv": vv,
               "sort": (sort if sort and sort != "new" else None)}
        prm.update(kw)
        prm = {k: v for k, v in prm.items() if v}
        return ("/?" + urllib.parse.urlencode(prm)) if prm else "/"

    top = (header(q, at, vi or di or ob, lang)
           + _sections_strip(link, at, lang, ob)
           + _regions_strip(link, ob, lang, at, q, di, vi, vv))

    # Бөлүм/категория/издөө жок — катар-катар тизме.
    # Аймак гана тандалса, ошол аймактын ичинде катарлар көрүнөт.
    if not (q or at or cid or sid or di or vi or vv):
        return page(top + f'<main class="wrap">{shelves(lang, ob)}</main>',
                    "ТАП!", "home", lang)

    rows = core.find(q, limit=60, ad_type=at, cat_id=cid, sub_id=sid,
                     oblast=ob, district=di, locality=vi, village=vv,
                     sort=sort)
    if at == "vehicle" and q in _CAR_BRANDS:   # BRAND_TITLE
        rows = _brand_rows(q, ad_type=at, cat_id=cid, sub_id=sid,
                           oblast=ob, district=di, locality=vi,
                           village=vv, sort=sort)[:60]
    body = ((cat_tiles(at, cid, ob, lang) if at and not q else "")
            + _filter_bars(link, q, at, cid, sid, ob, di, vi, lang, sort, vv))

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


_NUM_JS = """<script>
function tapNum(b){
  var box = b.closest('.ctc');
  try { box.innerHTML = decodeURIComponent(escape(atob(b.dataset.h))); }
  catch(e) { box.innerHTML = atob(b.dataset.h); }
}
</script>"""


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
    # GUARD3: номер басканда гана ачылат. Спам роботтор беттен номерди
    # чогултуп ала албасын үчүн HTML'де ачык жатпайт.
    real = (f'<div class="cnum">{esc(shown)}</div>'
            f'<div class="cbar">'
            f'<a class="cb1 call" href="tel:+{intl}">{_PHONE}'
            f'<span>{T("c_call", lang)}</span></a>'
            f'<a class="cb1 wa" href="https://wa.me/{intl}{wa_msg}" '
            f'target="_blank" rel="noopener">{_WA}<span>WhatsApp</span></a>'
            f'<a class="cb1 tg" href="https://t.me/+{intl}" target="_blank" '
            f'rel="noopener" onclick="tapCopy(this)" data-m="{tg_msg}" '
            f'data-ok="{tg_ok}">{_TG}<span>Telegram</span></a>'
            f'</div>')
    enc = base64.b64encode(real.encode("utf-8")).decode("ascii")
    show = "Показать номер" if lang == "ru" else "Номерди көрсөтүү"
    return (f'<div class="ctc"><div class="cbar">'
            f'<button class="cb1 call" type="button" data-h="{enc}" '
            f'onclick="tapNum(this)">{_PHONE}<span>{esc(show)}</span></button>'
            f'</div></div>{_NUM_JS}')


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

# Маанилерди да которобуз (RU барагында кыргызча калбашы үчүн)
FACT_VALUE_RU = {
    "Жеткирүү жок": "Нет доставки",
    "Жеткирүү бар": "Есть доставка",
    "1 апта": "1 неделя",
    "2 апта": "2 недели",
    "3 апта": "3 недели",
    "4 апта": "4 недели",
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


_RSNS = (("scam", "Алдамчылык", "Мошенничество"),
         ("ban", "Тыюу салынган товар", "Запрещённый товар"),
         ("other", "Башка себеп", "Другая причина"))


def _report(r, lang="ky"):
    """Жарыя барагындагы даттануу формасы. #RPT5"""
    ru = lang == "ru"
    ttl = "Пожаловаться" if ru else "Даттануу"
    ask = "Выберите причину:" if ru else "Себебин тандаңыз:"
    txt = "Опишите подробнее" if ru else "Кеңири жазыңыз"
    btn = "Отправить" if ru else "Жөнөтүү"
    opts = "".join("<option value='%s'>%s</option>" % (c, esc(rr if ru else ky))
                   for c, ky, rr in _RSNS)
    return ("<details class='rpt'><summary>⚠️ " + esc(ttl) + "</summary>"
            "<form class='rptb' method='post' action='/report'>"
            "<input type='hidden' name='id' value='%d'>" % r["id"] +
            "<p>" + esc(ask) + "</p><select name='r'>" + opts + "</select>"
            "<textarea name='t' rows='3' maxlength='250' placeholder='" +
            esc(txt) + "'></textarea>"
            "<button type='submit'>" + esc(btn) + "</button></form></details>")


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
    if str(r.get("verified") or "") == "1":  # VERIFY_PHONE
        tel = ('<div class="vbadge">✅ '
               + ("Номер подтверждён" if lang == "ru" else "Номер ырасталган")
               + '</div><style>.vbadge{display:inline-block;margin:6px 0 4px;'
               'padding:5px 11px;border-radius:999px;background:#E3F6EA;'
               'color:#17693A;font-weight:700;font-size:13px}</style>') + tel
    _ask_t = ("Актуально ли объявление?" if lang == "ru"  #ASKBTN
              else "Жарыя актуалдуубу?")
    tel += ('<div class="askw"><a class="askb" target="_blank" rel="noopener" '
            f'href="https://t.me/TapmeniBot?start=ask_{r["id"]}">'
            f'❓ {_ask_t}</a></div>'
            '<style>.askw{margin:10px 0}.askb{display:block;text-align:center;'
            'padding:11px;border-radius:12px;border:1px solid #d7dbe3;'
            'background:#fff;color:#1b3a5c;font-weight:600;text-decoration:none}'
            '</style>')

    # SAFE_SEC: ар бөлүмгө өз эскертүүсү (ТАП! сабы биринчи)
    _sk = _SAFE_TXT.get(r.get("ad_type") or "", _SAFE_TXT["trade"])
    _tap, _tip = _sk[2:] if lang == "ru" else _sk[:2]
    tel += ('<div class="safe"><div class="safet">' + esc(_tap) + '</div>'
            '<div class="safep">🛡 ' + esc(_tip) + '</div></div>'
            '<style>.safe{margin:10px 0;padding:10px 12px;border-radius:12px;'
            'background:#FFF6DC;border:1px solid #F1D98B;color:#5B4300;'
            'font-size:13.5px;line-height:1.4}'
            '.safet{font-weight:700;margin-bottom:5px}</style>')

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
        _v = _ky(v, lang)
        if lang == "ru":
            _v = FACT_VALUE_RU.get(_v, _v)
        rows += _frow(ic2, _lb(nm[0], nm[1]) if nm else _ky(k, lang), _v)

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
{_report(r, lang)}<div class="dph">{dimg}{shbtn}</div>{dvid}
<div class="dcard">
<div class="eb">{ic}{esc(sname or name)} · №{r['id']}</div>
<div class="dp{' dpd' if is_deal(r['price']) else ''}">{esc(_price(r['price'], lang))}</div>
<h1>{esc(L(bridge.show_title(r), lang))}</h1>
</div>
<div class="dcard facts">{rows}</div>{desc}{tel}{share}</main>"""
    # PERF_PATCH: издөө системасы жана шилтеме үчүн сүрөттөмө
    _ttl = L(bridge.show_title(r), lang)
    _dsc = " ".join(str(r.get("description") or "").split())[:160] or _ttl
    _img = ""
    _ph = (str(r.get("photos") or "").split(",") or [""])[0].strip() or r.get("photo")
    if _ph:
        _img = '<meta property="og:image" content="%s/media/%s">' % (
            core.SITE_URL, esc(os.path.basename(str(_ph))))
    _meta = ('<meta name="description" content="%s">'
             '<link rel="canonical" href="%s/e/%s">'
             '<meta property="og:type" content="article">'
             '<meta property="og:title" content="%s">'
             '<meta property="og:description" content="%s">'
             '<meta property="og:url" content="%s/e/%s">%s'
             % (esc(_dsc), core.SITE_URL, r["id"], esc(_ttl), esc(_dsc),
                core.SITE_URL, r["id"], _img))
    return page(header("", None, None, lang) + body,
                _ttl, tab="home", lang=lang, meta=_meta)


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
        lead = ("Разместите объявление прямо на сайте или через бота."
                if ru else
                "Жарыяны ушул сайттан же бот аркылуу бере аласыз.")
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
        note = ("Сайт и оба бота работают с одной базой: где бы вы ни разместили "
                "объявление, оно появится везде." if ru else
                "Сайт жана эки бот бир базада иштейт: кайсынысы аркылуу берсеңиз да, "
                "жарыя бардык жерде чыгат.")

    site_btn = ""   # WEB_POST_BTN: сайттан жарыя берүү баскычы
    if not mine and not bal:
        site_btn = ('<a class="btn" href="/post" style="background:#17304F;color:#fff">'
                    '<span>%s</span></a><p class="flead" style="margin:6px 0 18px">%s</p>'
                    % (("🌐 Разместить на сайте" if ru else "🌐 Сайттан жарыя берүү"),
                       ("Или через бота:" if ru else "Же бот аркылуу:")))
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
{site_btn}
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
.meabout{margin:6px 4px 0;font-size:13px;line-height:1.5;color:#152741!important;opacity:1!important}
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
           f'<span class="meav"><img src="/pwa/icon-192.png?v={appicon.VERSION}" alt="ТАП!" loading="lazy"></span>'  # MEAV_LOGO
           '<style>.meav img{width:100%;height:100%;object-fit:cover;border-radius:50%;display:block}.meav{overflow:hidden;padding:0}</style>'
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
             "доставка, грузоперевозки, поиск работы, работа, рынки, торговые центры, крупные магазины "
             "и такси. Работает в Telegram, WhatsApp и на этом "
             "сайте — база одна."
             if ru else
             "ТАП! — Кыргызстандагы акылдуу жарыя платформасы. "
             "Соода-сатык, Соода-сатык (дүң), мүлк сатуу, кызмат "
             "көрсөтүү, ижарага берүү, жеткирүү, жүк ташуу, жумуш "
             "издөө, жумуш берүү, базарлар, соода борборлору, ири соода дүкөндөрү жана такси. Telegram'да, "
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

    def _text(self, body, ctype):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "max-age=3600")
        self.end_headers()
        self.wfile.write(data)

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
        if u.path.startswith("/admin"):  #MSG2
            import admin
            admin.handle(self, u)
            return
        
        if u.path == "/report":  #RPT6
            import admin
            admin.report(self)
            return
        
        if u.path == "/api/my":   # WEB_MY
            try:
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n).decode("utf-8")) if 0 < n < 10000 else {}
                _json_out(self, _web_my_act(body))
            except Exception as e:
                print("web_my:", e, flush=True)
                _json_out(self, {"ok": False, "err": "server"})
            return

        if u.path in ("/api/post", "/api/post/photo", "/api/post/video"):   # WEB_POST WEB_VIDEO
            try:
                n = int(self.headers.get("Content-Length") or 0)
                if n > ((_WEB_VMAX + 2) if u.path.endswith("/video") else 8) * 1024 * 1024:
                    _json_out(self, {"ok": False, "err": "big"})
                    return
                raw = self.rfile.read(n) if n else b""
                if u.path == "/api/post/video":
                    qs = urllib.parse.parse_qs(u.query)
                    _json_out(self, _web_video(qs.get("t", [""])[0], raw))
                elif u.path == "/api/post/photo":
                    qs = urllib.parse.parse_qs(u.query)
                    _json_out(self, _web_photo(qs.get("t", [""])[0], raw))
                else:
                    body = json.loads(raw.decode("utf-8")) if raw else {}
                    _json_out(self, _web_post(body, _lang(self)))
            except Exception as e:
                print("web_post:", e, flush=True)
                _json_out(self, {"ok": False, "err": "server"})
            return

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

    def _too_fast(self):
        """GUARD3: бир IP мүнөтүнө канча бет ача алат."""
        if RATE_MAX <= 0:
            return False
        ip = (self.headers.get("X-Forwarded-For") or "").split(",")[0].strip() \
            or self.client_address[0]
        now = _t.time()
        with _RATE_LOCK:
            box = _RATE.get(ip)
            if not box or box[0] < now:
                _RATE[ip] = [now + 60, 1]
                if len(_RATE) > 5000:
                    for k in [k for k, v in _RATE.items() if v[0] < now]:
                        _RATE.pop(k, None)
                return False
            box[1] += 1
            return box[1] > RATE_MAX

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if not u.path.startswith(("/media/", "/pwa/", "/si/")) and self._too_fast():
            self.send_response(429)
            self.send_header("Retry-After", "60")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        qs = urllib.parse.parse_qs(u.query)

        lang = _lang(self)

        if u.path == "/api/verify/start":   # WEB_VERIFY
            tok = core.web_verify_start(qs.get("phone", [""])[0])
            _json_out(self, {"ok": bool(tok), "token": tok,
                             "link": ("https://t.me/%s?start=v_%s" % (BOT, tok)) if tok else None})
            return
        if u.path == "/api/verify/status":
            r = core.web_verify_status(qs.get("t", [""])[0])
            _json_out(self, {"verified": bool(r and r["verified"])})
            return
        if u.path == "/verify":
            self._send(verify_page(lang))
            return
        if u.path == "/api/my":   # WEB_MY
            _json_out(self, _web_my_list(qs.get("t", [""])[0],
                                         qs.get("f", [""])[0], lang))
            return
        if u.path == "/api/balance":   # WEB_BAL
            _json_out(self, _web_balance(qs.get("t", [""])[0]))
            return
        if u.path == "/post":   # WEB_POST
            self._send(post_page(lang))
            return

        if u.path == "/admin" or u.path.startswith("/admin/"):  #ADM1
            import admin
            admin.handle(self, u)
            return
        
        if u.path == "/report":  #RPT2
            import admin
            admin.report(self, u)
            return
        
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

        if u.path == "/bal":   # WEB_BAL
            return self._send(balance_page(lang))

        if u.path == "/my":   # WEB_MY
            self._send(my_page(lang))
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
            vv = (qs.get("vv", [""])[0]).strip() or None

            # Эски шилтемелер иштей берсин (/?cat=…&region=…)
            if not ob:
                ob = (qs.get("region", [""])[0]).strip() or None
            if not at and qs.get("cat"):
                old = qs["cat"][0]
                at = {"transport": "trade", "realty": "rental",
                      "personal": "trade", "service": "service",
                      "shop": "markets", "business": "job"}.get(old)

            self._send(home(q, at, cid, sid, ob, di, vi, lang, sort, vv))

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

        elif u.path == "/robots.txt":
            txt = ("User-agent: *\n"
                   "Allow: /\n"
                   "Disallow: /admin\n"
                   "Disallow: /api/\n"
                   "Disallow: /me\n"
                   "Disallow: /my\n"
                   "Disallow: /bal\n"
                   "Disallow: /fav\n"
                   "Sitemap: %s/sitemap.xml\n" % core.SITE_URL)
            self._text(txt, "text/plain; charset=utf-8")

        elif u.path == "/sitemap.xml":
            self._text(sitemap(), "application/xml; charset=utf-8")

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


# PERF_PATCH: издөө системалары үчүн карта. 10 мүнөт кэште турат.
_SITEMAP = [0, ""]


def sitemap():
    now = _t.time()
    if _SITEMAP[0] > now and _SITEMAP[1]:
        return _SITEMAP[1]
    base = core.SITE_URL
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path in ["/", "/find", "/terms"] + ["/?at=%s" % c for c, _i, _n in SECTIONS]:
        parts.append("<url><loc>%s%s</loc></url>" % (base, esc(path)))
    try:
        rows = core.query("SELECT id FROM listings WHERE is_active=1 "
                          "ORDER BY id DESC LIMIT 5000", (), fetch="all") or []
    except Exception:
        rows = []
    for r in rows:
        parts.append("<url><loc>%s/e/%s</loc></url>" % (base, r["id"]))
    parts.append("</urlset>")
    out = "".join(parts)
    _SITEMAP[0] = now + 600
    _SITEMAP[1] = out
    return out


class Server(ThreadingMixIn, HTTPServer):
    """Бир эле убакта бир нече суроону иштетет."""
    daemon_threads = True

    def handle_error(self, request, client_address):   # QUIET_PIPE
        """Колдонуучу бетти жаап койсо чыккан зыянсыз каталарды логго жазбайт."""
        import sys as _s
        if isinstance(_s.exc_info()[1], (BrokenPipeError, ConnectionResetError,
                                         ConnectionAbortedError, TimeoutError)):
            return
        super().handle_error(request, client_address)


if __name__ == "__main__":
    core.init_db()
    print(f"\n  TAP! витрина: http://localhost:{PORT}", flush=True)
    print(f"  База: {'Postgres' if core.IS_PG else 'SQLite'}\n", flush=True)
    Server(("0.0.0.0", PORT), H).serve_forever()


# LOGO_IMG
