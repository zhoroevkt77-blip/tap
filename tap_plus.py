# -*- coding: utf-8 -*-
"""
ТАП+ — сатуучулар үчүн акылуу аккаунт жана «✅ Ишеним» белгиси.

  • ТАП+ тарифтери: 🐴 Кулун, 🐎 Тай, 🏇 Тулпар (мөөнөтү менен)
  • «✅ Ишеним» — акысыз: номери жана дареги текшерилген сатуучу (админ берет)
  • Дүкөндүн барагы: /d/<slug>
  • Админ: /admin/plus — сатуучуну кошуу, тариф, мөөнөт, Ишеним

Төлөм азырынча кол менен: сатуучу MBank'тан которот, админ ушул жерден жандырат.
"""
import datetime as _dt
import hmac
import html
import os
import re
import threading
import time
from urllib.parse import parse_qs, quote

import core

E = html.escape

TIERS = [
    # ачкыч, аты, баасы (сом/ай), издөөдөгү орду (кичине — алдыда)
    ("kulun", "🐴 Кулун", int(os.environ.get("PLUS_PRICE_KULUN", "490") or 490), 2),
    ("tai", "🐎 Тай", int(os.environ.get("PLUS_PRICE_TAI", "990") or 990), 1),
    ("tulpar", "🏇 Тулпар", int(os.environ.get("PLUS_PRICE_TULPAR", "1990") or 1990), 0),
]
TIER = {t[0]: t for t in TIERS}
PAY_PHONE = os.environ.get("PLUS_PAY_PHONE", "").strip()

_LOCK = threading.Lock()
_C = {"t": 0.0, "tg": {}, "slug": {}, "ready": False}


def _ensure():
    if _C["ready"]:
        return
    core.query("CREATE TABLE IF NOT EXISTS sellers ("
               "tg_id TEXT PRIMARY KEY, slug TEXT, name TEXT, about TEXT, address TEXT, "
               "hours TEXT, phone TEXT, tier TEXT, until TEXT, ishenim INTEGER DEFAULT 0, "
               "created_at TEXT)")
    _C["ready"] = True


def _today():
    return _dt.date.today().isoformat()


def _load(force=False):
    now = time.time()
    if not force and now - _C["t"] < 60:
        return
    try:
        _ensure()
        rows = core.query("SELECT * FROM sellers", fetch="all") or []
    except Exception:
        rows = []
    tg, sl = {}, {}
    for r in rows:
        r = dict(r)
        tg[str(r.get("tg_id") or "")] = r
        if r.get("slug"):
            sl[str(r["slug"])] = r
    with _LOCK:
        _C.update(t=now, tg=tg, slug=sl)


def get(tg_id):
    if not tg_id:
        return None
    _load()
    return _C["tg"].get(str(tg_id))


def by_slug(slug):
    _load()
    return _C["slug"].get(str(slug or ""))


def tier(tg_id):
    """Учурда жарактуу ТАП+ тарифи (kulun/tai/tulpar) же None."""
    r = get(tg_id)
    if not r or r.get("tier") not in TIER:
        return None
    if str(r.get("until") or "") < _today():
        return None
    return r["tier"]


def ishenim(tg_id):
    r = get(tg_id)
    try:
        return bool(r and int(r.get("ishenim") or 0))
    except Exception:
        return False


def rank(tg_id):
    t = tier(tg_id)
    return TIER[t][3] if t else 9


_TR = dict(zip("абвгдеёжзийклмнңоөпрстуүфхцчшщъыьэюя",
               ["a", "b", "v", "g", "d", "e", "yo", "zh", "z", "i", "y", "k", "l", "m", "n", "ng", "o", "o",
                "p", "r", "s", "t", "u", "u", "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya"]))


def slugify(s):
    s = "".join(_TR.get(c, c) for c in str(s or "").lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:40] or "dukon"


def _uniq_slug(s, tg_id):
    base, i = slugify(s), 1
    out = base
    while True:
        r = core.query("SELECT tg_id FROM sellers WHERE slug=?", (out,), fetch="one")
        if not r or str(r["tg_id"]) == str(tg_id):
            return out
        i += 1
        out = "%s-%d" % (base, i)


def _tg_by_phone(phone):
    d = "".join(c for c in str(phone or "") if c.isdigit())[-9:]
    if len(d) < 9:
        return None
    r = core.query("SELECT tg_id FROM listings WHERE contact LIKE ? AND tg_id IS NOT NULL "
                   "AND tg_id<>'' ORDER BY id DESC LIMIT 1", ("%" + d,), fetch="one")
    return str(r["tg_id"]) if r else None


# ═══════════════════════ АДМИН ═══════════════════════
_ACSS = ("<style>.pt{width:100%;border-collapse:collapse;font-size:14px;margin:8px 0 18px}"
         ".pt td,.pt th{padding:8px 6px;border-bottom:1px solid #E3E9F2;text-align:left;vertical-align:top}"
         ".pf label{display:block;font-size:13px;color:#33425A;margin:10px 0 4px;font-weight:600}"
         ".pf input,.pf select,.pf textarea{width:100%;box-sizing:border-box;font-size:15px;font-family:inherit;"
         "border:1.5px solid #9AA8BF;border-radius:10px;padding:9px 10px;background:#fff}"
         ".pf .ck{display:flex;gap:8px;align-items:center;margin-top:12px;font-weight:600}.pf .ck input{width:auto}"
         ".pf button{width:100%;margin-top:14px;border:0;border-radius:10px;padding:12px;background:#17365C;color:#fff;"
         "font-size:15px;font-weight:700}.tg{display:inline-block;font-size:12px;font-weight:800;padding:2px 7px;"
         "border-radius:7px;background:#FFF1D0;color:#8A5A00}.ish{background:#E3F6EE;color:#0E7A54}"
         ".off{background:#F1F4F9;color:#5A6982}</style>")


def admin(h, uid, q, p, msg, page, k):
    _ensure()
    if p == "/admin/plus/save" and getattr(h, "command", "GET") == "POST":
        return _save(h, k)
    ed = (q.get("edit") or [""])[0]
    _load(force=True)
    cur = _C["tg"].get(ed) if ed else None
    rows = sorted(_C["tg"].values(), key=lambda r: str(r.get("created_at") or ""), reverse=True)
    t = "<table class='pt'><tr><th>Сатуучу</th><th>Тариф</th><th></th></tr>"
    for r in rows:
        tr = r.get("tier")
        ok = tr in TIER and str(r.get("until") or "") >= _today()
        tb = ("<span class='tg'>%s · %s чейин</span>" % (E(TIER[tr][1]), E(str(r.get("until") or "")))
              if tr in TIER else "<span class='tg off'>—</span>")
        if tr in TIER and not ok:
            tb = "<span class='tg off'>%s · бүттү %s</span>" % (E(TIER[tr][1]), E(str(r.get("until") or "")))
        ish = " <span class='tg ish'>✅ Ишеним</span>" if int(r.get("ishenim") or 0) else ""
        t += ("<tr><td><b>%s</b>%s<br><small>%s · <a href='/d/%s' target='_blank'>/d/%s</a></small></td>"
              "<td>%s</td><td><a href='/admin/plus?edit=%s'>✏️</a></td></tr>"
              % (E(str(r.get("name") or "")), ish, E(str(r.get("phone") or r.get("tg_id") or "")),
                 E(str(r.get("slug") or "")), E(str(r.get("slug") or "")), tb, quote(str(r.get("tg_id") or ""))))
    t += "</table>" if rows else "<p>Азырынча сатуучу жок.</p></table>"
    c = cur or {}
    sel = "".join("<option value='%s'%s>%s — %d сом/ай</option>" % (
        key, " selected" if c.get("tier") == key else "", E(nm), pr) for key, nm, pr, _ in TIERS)
    form = ("<h2 style='font-size:18px'>%s</h2><form class='pf' method='post' action='/admin/plus/save'>"
            "<input type='hidden' name='k' value='%s'><input type='hidden' name='old' value='%s'>"
            "<label>Телефон номери (жарыяларындагы номер) же Telegram ID</label>"
            "<input name='who' value='%s' placeholder='0700 123 456' required>"
            "<label>Дүкөндүн / сатуучунун аты</label><input name='name' value='%s' placeholder='Айбек Эмерек' required>"
            "<label>Барактын дареги: /d/… (бош калса, атынан өзү түзүлөт)</label><input name='slug' value='%s' placeholder='aybek-emerek'>"
            "<label>Тариф</label><select name='tier'><option value=''>— ТАП+ жок —</option>%s</select>"
            "<label>Мөөнөтүн узартуу</label><select name='days'><option value='0'>Өзгөртпөө%s</option>"
            "<option value='30'>+30 күн</option><option value='90'>+90 күн</option><option value='365'>+1 жыл</option></select>"
            "<label class='ck'><input type='checkbox' name='ishenim' value='1'%s> ✅ Ишеним (номери жана дареги текшерилди)</label>"
            "<label>Дареги</label><input name='address' value='%s' placeholder='Бишкек, Жибек Жолу 120'>"
            "<label>Иш убактысы</label><input name='hours' value='%s' placeholder='09:00–20:00, дем алышсыз'>"
            "<label>Дүкөн жөнүндө</label><textarea name='about' rows='4'>%s</textarea>"
            "<button>💾 Сактоо</button></form>"
            % ("✏️ " + E(str(c.get("name") or "")) if cur else "➕ Жаңы сатуучу", E(k), E(str(c.get("tg_id") or "")),
               E(str(c.get("phone") or c.get("tg_id") or "")), E(str(c.get("name") or "")), E(str(c.get("slug") or "")),
               sel, (" (азыр: %s чейин)" % E(str(c.get("until")))) if c.get("until") else "",
               " checked" if int(c.get("ishenim") or 0) else "",
               E(str(c.get("address") or "")), E(str(c.get("hours") or "")), E(str(c.get("about") or ""))))
    info = ("<p style='font-size:13px;color:#5A6982'>Сатуучу MBank'тан которгондон кийин ушул жерден тарифин жана "
            "мөөнөтүн коёсуз. «✅ Ишеним» — акысыз, номерин жана дарегин текшергенден кийин белгилейсиз.</p>")
    h._send(page("ТАП+", _ACSS + info + form + "<h2 style='font-size:18px;margin-top:24px'>Сатуучулар</h2>" + t,
                 "pl", msg))


def _save(h, k):
    try:
        n = int(h.headers.get("Content-Length") or 0)
        d = parse_qs(h.rfile.read(n).decode("utf-8")) if 0 < n < 20000 else {}
    except Exception:
        d = {}
    g = lambda x: (d.get(x) or [""])[0].strip()
    if not hmac.compare_digest(g("k"), k):
        return h._go("/admin/plus?m=" + quote("Сессия бүттү, кайра кириңиз"))
    who = g("who")
    tg = g("old") or _tg_by_phone(who)
    if not tg and who.isdigit():
        r = core.query("SELECT tg_id FROM listings WHERE tg_id=? LIMIT 1", (who,), fetch="one")
        tg = who if r else None
    phone = who if any(c.isdigit() for c in who) else ""
    if not tg:
        return h._go("/admin/plus?m=" + quote("Бул номер менен жарыя табылган жок. Сатуучу адегенде жарыя бериши керек."))
    name = g("name")[:80] or "Дүкөн"
    _ensure()
    cur = core.query("SELECT * FROM sellers WHERE tg_id=?", (tg,), fetch="one")
    cur = dict(cur) if cur else {}
    slug = _uniq_slug(g("slug") or cur.get("slug") or name, tg)
    tr = g("tier") if g("tier") in TIER else ""
    until = str(cur.get("until") or "")
    try:
        days = int(g("days") or 0)
    except Exception:
        days = 0
    if days > 0:
        base = max(_dt.date.today(), _dt.date.fromisoformat(until)) if until[:10] >= _today() else _dt.date.today()
        until = (base + _dt.timedelta(days=days)).isoformat()
    vals = (slug, name, g("about")[:1500], g("address")[:200], g("hours")[:120],
            phone or cur.get("phone") or who, tr, until, 1 if g("ishenim") else 0)
    if cur:
        core.query("UPDATE sellers SET slug=?, name=?, about=?, address=?, hours=?, phone=?, tier=?, until=?, "
                   "ishenim=? WHERE tg_id=?", vals + (tg,))
    else:
        core.query("INSERT INTO sellers (slug, name, about, address, hours, phone, tier, until, ishenim, tg_id, "
                   "created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)", vals + (tg, core.now_str()))
    _load(force=True)
    try:
        core.cache_clear()
    except Exception:
        pass
    return h._go("/admin/plus?m=" + quote("✅ Сакталды: %s → /d/%s" % (name, slug)))



# ══ TAPPLUS2: барактын түрлөрү, бригада/агенттик/автосалон маалыматы, логотип, баннер, портфолио, акция ══
import base64 as _b64
import json as _json

KINDS = [
    # ачкыч, белги, аты, «эмне кылабыз» аталышы, «команда» аталышы, «өтүнүч» баскычы
    ("store", "🏪", "Дүкөн", "Эмне сатабыз", "Кызматкерлер", "📝 Буйрутма берүү"),
    ("brigade", "🧱", "Уста бригада", "Эмне кылабыз", "Бригада", "📐 Өлчөөгө чакыруу"),
    ("realtor", "🏢", "Риелтор / агенттик", "Багыттар", "Агенттер", "🏠 Көрүүгө жазылуу"),
    ("auto", "🚗", "Автосалон", "Кызматтар", "Менеджерлер", "🚗 Көрүүгө жазылуу"),
    ("builder", "🏗", "Курулуш компаниясы", "Долбоорлор", "Команда", "📝 Өтүнүч калтыруу"),
    ("transport", "🚚", "Жүк ташуу / такси парк", "Багыттар жана кызматтар", "Айдоочулар", "🚚 Буйрутма берүү"),
    ("salon", "💇", "Салон, клиника", "Кызматтар", "Адистер", "📅 Жазылуу"),
    ("edu", "🎓", "Курстар, окуу борбору", "Курстар", "Мугалимдер", "📅 Курска жазылуу"),
    ("farm", "🐄", "Ферма", "Продукция", "Команда", "📝 Буйрутма берүү"),
    ("factory", "🧵", "Цех, өндүрүш", "Продукция", "Команда", "📝 Буйрутма берүү"),
]
KIND = {k[0]: k for k in KINDS}
KIND_RU = {"store": "Магазин", "brigade": "Бригада мастеров", "realtor": "Риелтор / агентство",
           "auto": "Автосалон", "builder": "Строительная компания", "transport": "Грузоперевозки / таксопарк",
           "salon": "Салон, клиника", "edu": "Курсы, учебный центр", "farm": "Ферма", "factory": "Цех, производство"}
_C["ready2"] = False


def _ensure2():
    _ensure()
    if _C.get("ready2"):
        return
    for col in ("kind", "extra", "promo", "promo_until", "logo", "banner"):
        try:
            if getattr(core, "IS_PG", False):
                core.query("ALTER TABLE sellers ADD COLUMN IF NOT EXISTS %s TEXT" % col)
            else:
                core.query("ALTER TABLE sellers ADD COLUMN %s TEXT" % col)
        except Exception:
            pass
    if getattr(core, "IS_PG", False):
        core.query("CREATE TABLE IF NOT EXISTS seller_imgs (id SERIAL PRIMARY KEY, tg_id TEXT, kind TEXT, "
                   "cap TEXT, data TEXT, created_at TEXT)")
    else:
        core.query("CREATE TABLE IF NOT EXISTS seller_imgs (id INTEGER PRIMARY KEY AUTOINCREMENT, tg_id TEXT, "
                   "kind TEXT, cap TEXT, data TEXT, created_at TEXT)")
    _C["ready2"] = True


_load_base1 = _load


def _load(force=False):
    try:
        _ensure2()
    except Exception:
        pass
    return _load_base1(force)


def extra(r):
    try:
        d = _json.loads((r or {}).get("extra") or "{}")
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def kind(r):
    k = (r or {}).get("kind") or "store"
    return k if k in KIND else "store"


def promo(r):
    """Жарактуу акция тексти же ''."""
    if not r or not (r.get("promo") or "").strip():
        return ""
    if str(r.get("promo_until") or "9999") < _today():
        return ""
    return str(r["promo"]).strip()


def img_put(tg_id, kind_, data_url, cap=""):
    s = str(data_url or "")
    if not s.startswith("data:image/jpeg;base64,"):
        return None
    b = s.split(",", 1)[1]
    try:
        raw = _b64.b64decode(b)
    except Exception:
        return None
    if raw[:2] != b"\xff\xd8" or len(raw) > 1_500_000:
        return None
    _ensure2()
    core.query("INSERT INTO seller_imgs (tg_id, kind, cap, data, created_at) VALUES (?,?,?,?,?)",
               (str(tg_id), kind_, str(cap or "")[:80], b, core.now_str()))
    r = core.query("SELECT MAX(id) AS i FROM seller_imgs WHERE tg_id=? AND kind=?", (str(tg_id), kind_), fetch="one")
    return int(r["i"]) if r and r.get("i") is not None else None


def img_get(iid):
    try:
        _ensure2()
        r = core.query("SELECT data FROM seller_imgs WHERE id=?", (int(iid),), fetch="one")
        return _b64.b64decode(r["data"]) if r else None
    except Exception:
        return None


def imgs(tg_id, kind_):
    try:
        _ensure2()
        return [dict(x) for x in (core.query("SELECT id, cap FROM seller_imgs WHERE tg_id=? AND kind=? ORDER BY id",
                                             (str(tg_id), kind_), fetch="all") or [])]
    except Exception:
        return []


def lines(txt):
    return [x.strip() for x in str(txt or "").splitlines() if x.strip()]


def pairs(txt):
    out = []
    for ln in lines(txt):
        for sep in (" — ", " - ", ": ", "—"):
            if sep in ln:
                a, b = ln.split(sep, 1)
                out.append((a.strip(), b.strip()))
                break
        else:
            out.append((ln, ""))
    return out


_IMG_JS = """<script>
function tpImg(inp,out,w,h,crop){var f=inp.files&&inp.files[0];if(!f)return;var rd=new FileReader();
rd.onload=function(){var im=new Image();im.onload=function(){var c=document.createElement('canvas');
var sw=im.width,sh=im.height,sx=0,sy=0;if(crop){var r=w/h;if(sw/sh>r){sx=(sw-sh*r)/2;sw=sh*r;}else{sy=(sh-sw/r)/2;sh=sw/r;}c.width=w;c.height=h;}
else{var k=Math.min(1,w/sw,h/sh);c.width=Math.round(sw*k);c.height=Math.round(sh*k);}
c.getContext('2d').drawImage(im,sx,sy,sw,sh,0,0,c.width,c.height);var d=c.toDataURL('image/jpeg',0.82);
var o=document.getElementById(out);o.value=d;var p=document.getElementById(out+'_p');if(p){p.src=d;p.style.display='block';}};im.src=rd.result;};rd.readAsDataURL(f);}
function tpPf(inp){var box=document.getElementById('pfnew');Array.prototype.slice.call(inp.files,0,8).forEach(function(f,i){
var rd=new FileReader();rd.onload=function(){var im=new Image();im.onload=function(){var c=document.createElement('canvas');
var k=Math.min(1,1000/im.width,1000/im.height);c.width=Math.round(im.width*k);c.height=Math.round(im.height*k);
c.getContext('2d').drawImage(im,0,0,c.width,c.height);var d=c.toDataURL('image/jpeg',0.8);
var w=document.createElement('div');w.className='pfi';w.innerHTML='<img src="'+d+'"><input name="pf_cap" placeholder="Аталышы (мис: Батир ремонту, 2025)"><input type="hidden" name="pf_data">';
w.querySelector('[name=pf_data]').value=d;box.appendChild(w);};im.src=rd.result;};rd.readAsDataURL(f);});inp.value='';}
</script>"""

_ACSS2 = ("<style>.pf .row2{display:grid;grid-template-columns:1fr 1fr;gap:8px}.pf small{display:block;color:#5A6982;"
          "font-size:12px;margin-top:3px}.pf .im{max-width:160px;border-radius:10px;margin-top:6px;display:none}"
          ".pfg{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:6px}.pfg label{font-size:11px;margin:0}"
          ".pfg img,.pfi img{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:8px;display:block}"
          "#pfnew{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px}.pfi input{margin-top:4px;font-size:13px}"
          ".pf fieldset{border:1.5px solid #E3E9F2;border-radius:12px;padding:6px 12px 12px;margin:14px 0 0}"
          ".pf legend{font-weight:800;font-size:14px;padding:0 6px}</style>")


def admin(h, uid, q, p, msg, page, k):
    _ensure2()
    if p == "/admin/plus/save" and getattr(h, "command", "GET") == "POST":
        return _save(h, k)
    ed = (q.get("edit") or [""])[0]
    _load(force=True)
    cur = _C["tg"].get(ed) if ed else None
    rows = sorted(_C["tg"].values(), key=lambda r: str(r.get("created_at") or ""), reverse=True)
    t = "<table class='pt'><tr><th>Сатуучу</th><th>Тариф</th><th></th></tr>"
    for r in rows:
        tr = r.get("tier")
        ok = tr in TIER and str(r.get("until") or "") >= _today()
        tb = ("<span class='tg'>%s · %s чейин</span>" % (E(TIER[tr][1]), E(str(r.get("until") or "")))
              if tr in TIER else "<span class='tg off'>—</span>")
        if tr in TIER and not ok:
            tb = "<span class='tg off'>%s · бүттү %s</span>" % (E(TIER[tr][1]), E(str(r.get("until") or "")))
        ish = " <span class='tg ish'>✅ Ишеним</span>" if int(r.get("ishenim") or 0) else ""
        kd = KIND[kind(r)]
        t += ("<tr><td><b>%s %s</b>%s<br><small>%s · %s · <a href='/d/%s' target='_blank'>/d/%s</a></small></td>"
              "<td>%s</td><td><a href='/admin/plus?edit=%s'>✏️</a></td></tr>"
              % (kd[1], E(str(r.get("name") or "")), ish, E(kd[2]), E(str(r.get("phone") or r.get("tg_id") or "")),
                 E(str(r.get("slug") or "")), E(str(r.get("slug") or "")), tb, quote(str(r.get("tg_id") or ""))))
    t += "</table>" if rows else "<p>Азырынча сатуучу жок.</p></table>"
    c = cur or {}
    x = extra(c)
    tsel = "".join("<option value='%s'%s>%s — %d сом/ай</option>" % (
        key, " selected" if c.get("tier") == key else "", E(nm), pr) for key, nm, pr, _ in TIERS)
    ksel = "".join("<option value='%s'%s>%s %s</option>" % (
        kk[0], " selected" if kind(c) == kk[0] else "", kk[1], E(kk[2])) for kk in KINDS)
    lg = ("<img class='im' style='display:block' src='/pi/%s.jpg'>" % E(str(c["logo"]))) if c.get("logo") else ""
    bn = ("<img class='im' style='display:block;max-width:100%%' src='/pi/%s.jpg'>" % E(str(c["banner"]))) if c.get("banner") else ""
    pfs = imgs(c.get("tg_id"), "pf") if cur else []
    pfh = "".join("<label><img src='/pi/%d.jpg'><input type='checkbox' name='pf_del' value='%d'> өчүрүү<br>%s</label>"
                  % (i["id"], i["id"], E(str(i.get("cap") or ""))) for i in pfs)
    v = lambda key: E(str(x.get(key) or ""))
    form = ("<h2 style='font-size:18px'>%s</h2><form class='pf' method='post' action='/admin/plus/save'>"
            "<input type='hidden' name='k' value='%s'><input type='hidden' name='old' value='%s'>"
            "<label>Телефон номери (жарыяларындагы номер) же Telegram ID</label>"
            "<input name='who' value='%s' placeholder='0700 123 456' required>"
            "<div class='row2'><div><label>Барактын түрү</label><select name='kind'>%s</select></div>"
            "<div><label>Тариф</label><select name='tier'><option value=''>— ТАП+ жок —</option>%s</select></div></div>"
            "<label>Аты</label><input name='name' value='%s' placeholder='«Ак-Үй» бригадасы' required>"
            "<label>Барактын дареги: /d/… (бош калса, атынан өзү түзүлөт)</label><input name='slug' value='%s'>"
            "<label>Мөөнөтүн узартуу</label><select name='days'><option value='0'>Өзгөртпөө%s</option>"
            "<option value='7'>+7 күн (акысыз сыноо)</option><option value='30'>+30 күн</option>"
            "<option value='90'>+90 күн</option><option value='365'>+1 жыл</option></select>"
            "<label class='ck'><input type='checkbox' name='ishenim' value='1'%s> ✅ Ишеним (номери жана дареги текшерилди)</label>"
            "<fieldset><legend>Негизги маалымат</legend>"
            "<label>Дареги</label><input name='address' value='%s' placeholder='Бишкек, Жибек Жолу 120'>"
            "<label>Иш убактысы</label><input name='hours' value='%s' placeholder='09:00–20:00, дем алышсыз'>"
            "<label>Жөнүндө</label><textarea name='about' rows='3'>%s</textarea>"
            "<label>Кыска фактылар (ар бири өз сабында)</label><textarea name='facts' rows='3' placeholder='👷 6 уста&#10;🧰 12 жыл тажрыйба&#10;🏠 140+ объект'>%s</textarea></fieldset>"
            "<fieldset><legend>Түрүнө жараша</legend>"
            "<label>Эмне кылат / сатат (үтүр менен)</label><input name='services' value='%s' placeholder='Батир ремонту, Кирпич, Плитка, Электрика'>"
            "<label>Шарттар (ар бири өз сабында: «Аталыш: маани»)</label><textarea name='conds' rows='5' placeholder='Өлчөө жана смета: Акысыз&#10;Кепилдик: 1 жыл&#10;Иштөө аймагы: Бишкек + 50 км'>%s</textarea>"
            "<label>Команда (ар бири өз сабында: «Аты — адистиги»)</label><textarea name='team' rows='4' placeholder='Азамат — бригадир&#10;Нурлан — кирпич'>%s</textarea>"
            "<label>Баалар (ар бири өз сабында: «Иш — баа»)</label><textarea name='prices' rows='5' placeholder='Шыбак — 350 сом/м²&#10;Плитка коюу — 800 сом/м²'>%s</textarea></fieldset>"
            "<fieldset><legend>Сүрөттөр</legend>"
            "<label>Логотип (чарчы)</label><input type='file' accept='image/*' onchange=\"tpImg(this,'logo_data',300,300,1)\">"
            "<input type='hidden' name='logo_data' id='logo_data'><img id='logo_data_p' class='im'>%s"
            "<label>Баннер (кенен сүрөт)</label><input type='file' accept='image/*' onchange=\"tpImg(this,'banner_data',1200,400,1)\">"
            "<input type='hidden' name='banner_data' id='banner_data'><img id='banner_data_p' class='im' style='max-width:100%%'>%s"
            "<label>Портфолио — бүткөн иштер (бир нечесин тандаса болот)</label>"
            "<input type='file' accept='image/*' multiple onchange='tpPf(this)'><div id='pfnew'></div><div class='pfg'>%s</div></fieldset>"
            "<fieldset><legend>🏷 Акция</legend>"
            "<label>Акциянын тексти (кыска)</label><input name='promo' maxlength='40' value='%s' placeholder='−20%% жума аягына чейин'>"
            "<label>Акция бүтөт</label><input type='date' name='promo_until' value='%s'></fieldset>"
            "<button>💾 Сактоо</button></form>"
            % ("✏️ " + E(str(c.get("name") or "")) if cur else "➕ Жаңы сатуучу", E(k), E(str(c.get("tg_id") or "")),
               E(str(c.get("phone") or c.get("tg_id") or "")), ksel, tsel, E(str(c.get("name") or "")),
               E(str(c.get("slug") or "")), (" (азыр: %s чейин)" % E(str(c.get("until")))) if c.get("until") else "",
               " checked" if int(c.get("ishenim") or 0) else "",
               E(str(c.get("address") or "")), E(str(c.get("hours") or "")), E(str(c.get("about") or "")),
               v("facts"), v("services"), v("conds"), v("team"), v("prices"), lg, bn, pfh,
               E(str(c.get("promo") or "")), E(str(c.get("promo_until") or ""))))
    info = ("<p style='font-size:13px;color:#5A6982'>Сатуучу MBank'тан которгондон кийин тарифин жана мөөнөтүн коёсуз. "
            "Жаңы сатуучуга «+7 күн (акысыз сыноо)» тандасаңыз болот. «✅ Ишеним» — акысыз.</p>")
    h._send(page("ТАП+", _ACSS + _ACSS2 + _IMG_JS + info + form +
                 "<h2 style='font-size:18px;margin-top:24px'>Сатуучулар</h2>" + t, "pl", msg))


def _save(h, k):
    try:
        n = int(h.headers.get("Content-Length") or 0)
        d = parse_qs(h.rfile.read(n).decode("utf-8")) if 0 < n < 16_000_000 else {}
    except Exception:
        d = {}
    g = lambda x: (d.get(x) or [""])[0].strip()
    if not hmac.compare_digest(g("k"), k):
        return h._go("/admin/plus?m=" + quote("Сессия бүттү, кайра кириңиз"))
    who = g("who")
    tg = g("old") or _tg_by_phone(who)
    if not tg and who.isdigit():
        r = core.query("SELECT tg_id FROM listings WHERE tg_id=? LIMIT 1", (who,), fetch="one")
        tg = who if r else None
    if not tg:
        return h._go("/admin/plus?m=" + quote("Бул номер менен жарыя табылган жок. Сатуучу адегенде жарыя бериши керек."))
    phone = who if any(c.isdigit() for c in who) else ""
    name = g("name")[:80] or "Дүкөн"
    _ensure2()
    cur = core.query("SELECT * FROM sellers WHERE tg_id=?", (tg,), fetch="one")
    cur = dict(cur) if cur else {}
    slug = _uniq_slug(g("slug") or cur.get("slug") or name, tg)
    tr = g("tier") if g("tier") in TIER else ""
    kd = g("kind") if g("kind") in KIND else "store"
    until = str(cur.get("until") or "")
    try:
        days = int(g("days") or 0)
    except Exception:
        days = 0
    if days > 0:
        base = max(_dt.date.today(), _dt.date.fromisoformat(until[:10])) if until[:10] >= _today() else _dt.date.today()
        until = (base + _dt.timedelta(days=days)).isoformat()
    ex = {key: g(key)[:3000] for key in ("facts", "services", "conds", "team", "prices")}
    pu = g("promo_until")[:10]
    vals = (slug, name, g("about")[:1500], g("address")[:200], g("hours")[:120],
            phone or cur.get("phone") or who, tr, until, 1 if g("ishenim") else 0,
            kd, _json.dumps(ex, ensure_ascii=False), g("promo")[:40], pu)
    if cur:
        core.query("UPDATE sellers SET slug=?, name=?, about=?, address=?, hours=?, phone=?, tier=?, until=?, "
                   "ishenim=?, kind=?, extra=?, promo=?, promo_until=? WHERE tg_id=?", vals + (tg,))
    else:
        core.query("INSERT INTO sellers (slug, name, about, address, hours, phone, tier, until, ishenim, kind, extra, "
                   "promo, promo_until, tg_id, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   vals + (tg, core.now_str()))
    for fld, kn in (("logo_data", "logo"), ("banner_data", "banner")):
        if g(fld):
            iid = img_put(tg, kn, g(fld))
            if iid:
                core.query("UPDATE sellers SET %s=? WHERE tg_id=?" % kn, (str(iid), tg))
    caps = d.get("pf_cap") or []
    for i, du in enumerate(d.get("pf_data") or []):
        img_put(tg, "pf", du, caps[i] if i < len(caps) else "")
    for dd in d.get("pf_del") or []:
        if str(dd).isdigit():
            core.query("DELETE FROM seller_imgs WHERE id=? AND tg_id=? AND kind='pf'", (int(dd), tg))
    _load(force=True)
    try:
        core.cache_clear()
    except Exception:
        pass
    return h._go("/admin/plus?edit=%s&m=%s" % (quote(tg), quote("✅ Сакталды: %s → /d/%s" % (name, slug))))
# ══ TAPPLUS2_END

