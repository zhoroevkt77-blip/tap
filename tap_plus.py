# -*- coding: utf-8 -*-
"""
ТАП+ — сатуучулар үчүн акылуу аккаунт жана «✅ Ишеним» белгиси.

  • ТАП+ тарифтери: 🥈 Күмүш, 🥇 Алтын, 💎 Алмаз (мөөнөтү менен)
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
    ("kulun", "🥈 Күмүш", int(os.environ.get("PLUS_PRICE_KULUN", "490") or 490), 2),
    ("tai", "🥇 Алтын", int(os.environ.get("PLUS_PRICE_TAI", "990") or 990), 1),
    ("tulpar", "💎 Алмаз", int(os.environ.get("PLUS_PRICE_TULPAR", "1990") or 1990), 0),
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
            "<label>Акциянын тексти (кыска)</label><input name='promo' maxlength='40' value='%s' placeholder='−20%% апта аягына чейин'>"
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



# ══ REVIEWS_ADMIN: пикирлерди көзөмөлдөө (/admin/plus) ══
_admin_rv_base = admin


def admin(h, uid, q, p, msg, page, k):
    if p == "/admin/plus/rev":
        g = lambda x: (q.get(x) or [""])[0]
        if hmac.compare_digest(g("k"), k) and g("id").isdigit():
            core.query("UPDATE reviews SET hidden=? WHERE id=?", (1 if g("h") == "1" else 0, int(g("id"))))
            return h._go("/admin/plus?m=" + quote("✅ Пикир жаңыланды"))
        return h._go("/admin/plus?m=" + quote("Сессия бүттү"))

    def page2(title, body, tab="", m=""):
        try:
            rows = core.query("SELECT r.id, r.seller, r.name, r.stars, r.body, r.at, r.hidden, s.name AS sn "
                              "FROM reviews r LEFT JOIN sellers s ON s.tg_id=r.seller ORDER BY r.id DESC LIMIT 40",
                              fetch="all") or []
        except Exception:
            rows = []
        if rows:
            body += "<h2 style='font-size:18px;margin-top:24px'>⭐ Акыркы пикирлер</h2><table class='pt'>"
            for r in rows:
                hid = int(r.get("hidden") or 0)
                body += ("<tr%s><td><b>%s</b> → %s<br>%s<br><small>%s · %s</small></td><td><a href='/admin/plus/rev?id=%d&h=%d&k=%s'>%s</a></td></tr>"
                         % (" style='opacity:.45'" if hid else "", "★" * int(r.get("stars") or 0),
                            E(str(r.get("sn") or r.get("seller") or "")), E(str(r.get("body") or "")),
                            E(str(r.get("name") or "")), E(str(r.get("at") or "")[:16]), int(r["id"]),
                            0 if hid else 1, quote(k), "↩️ Кайтаруу" if hid else "🙈 Жашыруу"))
            body += "</table>"
        return page(title, body, tab, m)
    return _admin_rv_base(h, uid, q, p, msg, page2, k)
# ══ REVIEWS_ADMIN_END



# ══ ADMEX: админ формасында барактын түрүнө жараша үлгү жазуулар ══
ADM_EX = {
    "store": {"name": "Айбек Эмерек", "address": "Бишкек, Жибек Жолу 120, «Дордой Плаза» 2-кабат",
              "hours": "09:00–20:00, дем алышсыз",
              "about": "Диван, шкаф, ашкана гарнитуру. Буйрутма менен 7 күндө жасайбыз.",
              "facts": "📦 300+ товар\n🚚 Бишкек ичинде жеткирүү бекер\n🛡 Кепилдик 1 жыл",
              "services": "Диван, Шкаф, Ашкана гарнитуру, Керебет, Үстөл-отургуч",
              "conds": "Жеткирүү: Бишкек ичинде бекер\nТөлөм: Накталай, MBank, бөлүп төлөө\nКепилдик: 1 жыл\nКайтаруу: 14 күн ичинде",
              "team": "Айбек — ээси\nАйгерим — сатуучу-консультант",
              "prices": "Бурчтук диван — 38 000 сомдон\nШкаф-купе — 25 000 сомдон",
              "promo": "−20% бардык диваңдарга"},
    "brigade": {"name": "«Ак-Үй» бригадасы", "address": "Бишкек, Аламедин-1",
                "hours": "08:00–19:00, жекшембиден башка",
                "about": "Батир жана үй ремонту ачкычы менен. Келишим менен иштейбиз.",
                "facts": "👷 6 уста\n🧰 12 жыл тажрыйба\n🏠 140+ объект",
                "services": "Батир ремонту, Кирпич, Плитка, Шыбак, Электрика, Сантехника",
                "conds": "Өлчөө жана смета: Акысыз\nМатериал: Биз алып келебиз же сиздики\nКепилдик: 1 жыл\nИштөө аймагы: Бишкек + 50 км",
                "team": "Азамат — бригадир\nНурлан — кирпич\nЭрлан — электрик",
                "prices": "Шыбак — 350 сом/м²\nПлитка коюу — 800 сом/м²\nБатир ремонту «ачкычы менен» — 6 000 сом/м²дан",
                "promo": "−15% октябрь бою"},
    "realtor": {"name": "«Ордо Недвижимость»", "address": "Ош, Ленин көч. 205, 3-кабат",
                "hours": "09:00–19:00, ишемби 10:00–15:00",
                "about": "Батир, үй, жер сатуу жана ижара. Документтерди текшерип, бүтүмгө чейин коштоп жүрөбүз.",
                "facts": "🏠 64 объект\n👥 5 агент\n🤝 210+ бүтүм",
                "services": "Батир сатуу, Үй сатуу, Жер, Ижара, Коммерциялык мүлк, Ипотекага жардам",
                "conds": "Комиссия: 2% же келишим\nДокумент текшерүү: Акысыз\nКөрсөтүү: Күн сайын\nИпотека: Банк менен жардам беребиз",
                "team": "Жылдыз — батир\nУлан — үй, жер\nМээрим — ижара",
                "prices": "Сатуу боюнча кызмат — 2%\nИжарага табуу — 1 айлык акынын 50%",
                "promo": "Комиссия 1% — ноябрь бою"},
    "auto": {"name": "«Asia Motors»", "address": "Бишкек, Кулиев көч. 12",
             "hours": "09:00–20:00, күн сайын",
             "about": "Корея, Япония жана АКШдан унаалар. Кредит, бөлүп төлөө, trade-in.",
             "facts": "🚘 38 унаа\n💳 Кредит 1 күндө\n🔄 Trade-in",
             "services": "Кредит, Бөлүп төлөө, Trade-in, Растаможка, Каттоо, Диагностика",
             "conds": "Алгачкы төлөм: 30%дан\nТекшерүү: СТОдо акысыз\nКепилдик: 3 ай же 5 000 км\nДокументтер: Тазалыгы текшерилген",
             "team": "Нурбек — менеджер\nАзиз — кредит адиси",
             "prices": "Растаможка кызматы — 15 000 сом\nДиагностика — 2 000 сом",
             "promo": "Ноябрда каттоо бекер"},
    "builder": {"name": "«Ала-Тоо Курулуш»", "address": "Бишкек, Ахунбаев көч. 98",
                "hours": "09:00–18:00, ишемби-жекшемби дем алыш",
                "about": "Турак жай комплекстерин курабыз. Батирлерди бөлүп төлөө менен сатабыз.",
                "facts": "🏗 12 ЖК бүттү\n📅 2010-жылдан бери\n🏠 3 000+ батир",
                "services": "Турак жай комплекстери, Коттедждер, Коммерциялык имараттар, Бөлүп төлөө",
                "conds": "Бөлүп төлөө: 3 жылга чейин, 0%\nАлгачкы төлөм: 30%дан\nУчурдагы ЖК: «Асман», «Ак-Бата»\nТапшыруу: 2027-жыл, 2-чейрек",
                "team": "Талант — директор\nАсель — сатуу бөлүмү",
                "prices": "1 м² (каркас) — 75 000 сомдон\n1 м² (ак кутуча) — 95 000 сомдон",
                "promo": "Ноябрда 1 м²ге −5%"},
    "transport": {"name": "«Тез Жүк»", "address": "Бишкек, Дордой базары",
                  "hours": "24/7",
                  "about": "Шаар ичинде жана облустарга жүк ташуу, жүкчүлөр менен.",
                  "facts": "🚚 15 унаа\n👷 Жүкчүлөр бар\n🕐 24/7",
                  "services": "Шаар ичинде, Облустарга, Көчүү, Курулуш материалдары, Жүкчүлөр",
                  "conds": "Унаалар: 1,5 т, 3 т, 5 т, фура\nТөлөм: Саатына же рейсине\nЖүкчүлөр: Өзүнчө акыга\nКамсыздандыруу: Бар",
                  "team": "Мирлан — диспетчер\nЭрмек — айдоочу",
                  "prices": "Портер 1,5 т — 800 сом/саат\nЖүкчү — 500 сом/саат\nБишкек–Ош — 25 000 сомдон",
                  "promo": "Түнкү рейске −10%"},
    "salon": {"name": "«Айзада» сулуулук салону", "address": "Бишкек, Токтогул көч. 77",
              "hours": "10:00–21:00, дем алышсыз",
              "about": "Чач кырктыруу, боёо, маникюр, косметология. Алдын ала жазылуу менен.",
              "facts": "💇 8 адис\n⭐ 500+ кардар\n📅 Онлайн жазылуу",
              "services": "Чач кырктыруу, Чач боёо, Маникюр, Педикюр, Каш-кирпик, Косметология",
              "conds": "Жазылуу: Алдын ала\nТөлөм: Накталай, MBank\nТуулган күнүңүздө: −15%",
              "team": "Айзада — стилист\nНуриза — маникюр\nДиана — косметолог",
              "prices": "Аялдар чач кырктыруу — 800 сомдон\nМаникюр — 700 сом\nЧач боёо — 2 500 сомдон",
              "promo": "Биринчи келүүгө −20%"},
    "edu": {"name": "«Bright English» курстары", "address": "Бишкек, Чүй пр. 150",
            "hours": "09:00–20:00, жекшембиден башка",
            "about": "Англис жана орус тилдери, ЖРТга даярдоо. Чакан топтор, 6–8 киши.",
            "facts": "🎓 1 200+ бүтүрүүчү\n👩‍🏫 9 мугалим\n📚 2015-жылдан",
            "services": "Англис тили, Орус тили, ЖРТга даярдоо, IELTS, Балдар үчүн курстар",
            "conds": "Топ: 6–8 киши\nСабак: Аптасына 3 жолу, 90 мүнөт\nСертификат: Берилет\nСыноо сабак: Акысыз",
            "team": "Айгүл — англис тили\nБакыт — ЖРТ",
            "prices": "Англис тили — 4 500 сом/ай\nIELTS даярдоо — 8 000 сом/ай",
            "promo": "Сентябрь тобуна −10%"},
    "farm": {"name": "«Ак-Суу» фермасы", "address": "Ысык-Көл облусу, Ак-Суу району",
             "hours": "08:00–19:00",
             "about": "Таза эт, сүт, бал. Кой, уй, жылкы — тирүүлөй жана союлган.",
             "facts": "🐑 300 баш кой\n🐄 40 уй\n🍯 Тоо балы",
             "services": "Кой эти, Уй эти, Сүт, Каймак, Бал, Тирүү мал",
             "conds": "Жеткирүү: Каракол жана Бишкекке аптасына 2 жолу\nДүң баа: 50 кгдан\nВетпаспорт: Бар",
             "team": "Мирбек — ээси\nКанат — малчы",
             "prices": "Кой эти — 650 сом/кг\nСүт — 60 сом/л\nБал — 600 сом/кг",
             "promo": "Курман айтка алдын ала буйрутма"},
    "factory": {"name": "«Ош Текстиль» цехи", "address": "Ош, Курманжан Датка көч. 210",
                "hours": "08:00–18:00, жекшемби дем алыш",
                "about": "Кийим тигүү: форма, спорт кийим, логотиптүү футболкалар. Дүң буйрутма.",
                "facts": "🧵 40 машина\n👕 Айына 15 000 буюм\n🏷 Логотип басуу",
                "services": "Мектеп формасы, Жумушчу кийим, Спорт кийим, Футболка, Логотип басуу",
                "conds": "Эң аз буйрутма: 50 даана\nМөөнөтү: 7–14 күн\nҮлгү: Акысыз\nЖеткирүү: Бүт Кыргызстан",
                "team": "Гүлзат — технолог\nТемир — сатуу менеджери",
                "prices": "Футболка (логотип менен) — 350 сомдон\nМектеп формасы — 1 800 сомдон",
                "promo": "100 даанадан −10%"},
}

_ADMEX_JS = """<script>(function(){var EX=__EX__,LB=__LB__;
var s=document.querySelector('select[name=kind]');if(!s)return;
function lab(n){var e=document.querySelector('[name='+n+']');if(!e)return null;var l=e.previousElementSibling;return (l&&l.tagName==='LABEL')?l:null;}
function ap(){var k=s.value,ex=EX[k]||EX.store,lb=LB[k]||LB.store;
 Object.keys(ex).forEach(function(n){var e=document.querySelector('[name='+n+']');if(e)e.setAttribute('placeholder','Мис: '+ex[n].replace(/\\n/g,'\\n'));});
 var a=lab('services');if(a)a.textContent=lb[0]+' (үтүр менен)';
 var b=lab('team');if(b)b.textContent=lb[1]+' (ар бири өз сабында: «Аты — адистиги»)';
 var c=lab('prices');if(c)c.textContent='Баалар (ар бири өз сабында: «'+lb[2]+' — баа»)';}
s.addEventListener('change',ap);ap();})();</script>"""

_ADMEX_LB = {
    "store": ("Эмне сатабыз", "Кызматкерлер", "Товар"), "brigade": ("Эмне кылабыз", "Бригада", "Иш"),
    "realtor": ("Багыттар", "Агенттер", "Кызмат"), "auto": ("Кызматтар", "Менеджерлер", "Кызмат"),
    "builder": ("Долбоорлор", "Команда", "Объект"), "transport": ("Багыттар жана кызматтар", "Айдоочулар", "Унаа / багыт"),
    "salon": ("Кызматтар", "Адистер", "Кызмат"), "edu": ("Курстар", "Мугалимдер", "Курс"),
    "farm": ("Продукция", "Команда", "Продукция"), "factory": ("Продукция", "Команда", "Буюм"),
}

_admin_ex_base = admin


def admin(h, uid, q, p, msg, page, k):
    def page3(title, body, tab="", m=""):
        js = (_ADMEX_JS.replace("__EX__", _json.dumps(ADM_EX, ensure_ascii=False).replace("</", "<\\/"))
              .replace("__LB__", _json.dumps(_ADMEX_LB, ensure_ascii=False)))
        return page(title, body + js, tab, m)
    return _admin_ex_base(h, uid, q, p, msg, page3, k)
# ══ ADMEX_END


# ── INBOX: админ панелдеги «🔔 Кабарлар» (Telegram'дын ордуна) ──
_IB = {"ready": False}


def _ib_init():
    if _IB["ready"]:
        return
    if getattr(core, "IS_PG", False):
        core.query("CREATE TABLE IF NOT EXISTS admin_inbox (id SERIAL PRIMARY KEY, kind TEXT, body TEXT, "
                   "links TEXT, at TEXT, seen INTEGER DEFAULT 0)")
    else:
        core.query("CREATE TABLE IF NOT EXISTS admin_inbox (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, "
                   "body TEXT, links TEXT, at TEXT, seen INTEGER DEFAULT 0)")
    _IB["ready"] = True


def inbox_add(body_html, kb=None, kind=""):
    """body_html — даяр HTML (маанилери escape кылынган), \\n — жаңы сап."""
    try:
        _ib_init()
        site = (os.environ.get("SITE_URL") or "https://tapmeni.up.railway.app").rstrip("/")
        links = []
        for row in (kb or {}).get("inline_keyboard", []):
            for b in row:
                u = str(b.get("url") or "")
                if u:
                    if u.startswith(site):
                        u = u[len(site):] or "/"
                    links.append([str(b.get("text") or "›"), u])
        core.query("INSERT INTO admin_inbox (kind, body, links, at, seen) VALUES (?,?,?,?,0)",
                   (kind, str(body_html or "")[:4000], _json.dumps(links, ensure_ascii=False), core.now_str()))
    except Exception as e:
        print("inbox_add:", e, flush=True)


def inbox_unread():
    try:
        _ib_init()
        r = core.query("SELECT COUNT(*) AS n FROM admin_inbox WHERE seen=0", fetch="one") or {}
        return int(r.get("n") or 0)
    except Exception:
        return 0


_IB_CSS = ("<style>.ibx{background:#fff;border:1.5px solid #DCE4F0;border-radius:14px;padding:12px 13px;margin:0 0 10px;"
           "font-size:14.5px;line-height:1.45;color:#152741}.ibx.nw{border-color:#2458C6;box-shadow:0 0 0 2px #E6EEFA}"
           ".ibx .tm{font-size:12px;color:#7A889C;margin-bottom:6px;display:flex;justify-content:space-between}"
           ".ibx .tm b{background:#2458C6;color:#fff;border-radius:6px;padding:1px 7px;font-size:11px}"
           ".ibx .lk{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}.ibx .lk a{border:1.5px solid #9AA8BF;border-radius:10px;"
           "padding:7px 11px;font-size:13px;font-weight:600;color:#17365C;text-decoration:none}"
           ".ibf{display:flex;gap:6px;margin:0 0 12px;flex-wrap:wrap}.ibf a{border:1.5px solid #C9D3E1;border-radius:99px;padding:6px 12px;"
           "font-size:13px;color:#17365C;text-decoration:none}.ibf a.on{background:#17365C;color:#fff;border-color:#17365C}</style>")
_IB_KINDS = [("", "Баары"), ("shop", "✏️ Барак өзгөрдү"), ("ask", "✉️ Суроолор")]


def inbox_page(h, uid, q, p, msg, page, k):
    _ib_init()
    kind = ""
    try:
        from urllib.parse import parse_qs as _pq
        kind = (_pq(q).get("k", [""])[0] if isinstance(q, str) else (q.get("k", [""])[0] if q else "")) or ""
    except Exception:
        kind = ""
    if kind:
        rows = core.query("SELECT * FROM admin_inbox WHERE kind=? ORDER BY id DESC LIMIT 100", (kind,), fetch="all") or []
    else:
        rows = core.query("SELECT * FROM admin_inbox ORDER BY id DESC LIMIT 100", fetch="all") or []
    f = "".join("<a href='/admin/inbox%s'%s>%s</a>" % (("?k=" + kk) if kk else "", " class='on'" if kk == kind else "", nm)
                for kk, nm in _IB_KINDS)
    out = ""
    for r in rows:
        r = dict(r)
        try:
            t = (_dt.datetime.strptime(str(r.get("at"))[:19], "%Y-%m-%d %H:%M:%S")
                 + _dt.timedelta(hours=6)).strftime("%d.%m %H:%M")
        except Exception:
            t = str(r.get("at") or "")[:16]
        try:
            lk = _json.loads(r.get("links") or "[]")
        except Exception:
            lk = []
        out += ("<div class='ibx%s'><div class='tm'><span>%s</span>%s</div>%s%s</div>"
                % ("" if int(r.get("seen") or 0) else " nw", E(t), "" if int(r.get("seen") or 0) else "<b>ЖАҢЫ</b>",
                   str(r.get("body") or "").replace("\n", "<br>"),
                   ("<div class='lk'>%s</div>" % "".join("<a href='%s'>%s</a>" % (E(u), E(tx)) for tx, u in lk)) if lk else ""))
    if not out:
        out = "<p style='color:#5A6982'>Азырынча кабар жок.</p>"
    core.query("UPDATE admin_inbox SET seen=1 WHERE seen=0")
    h._send(page("Кабарлар", _IB_CSS + "<div class='ibf'>" + f + "</div>" + out, "ib", msg))


# ── KINDLBL: сүрөттөр бөлүмүнүн аты барактын түрүнө жараша ──
PF_LBL = {
    "store": ("Товарлардын сүрөттөрү", "Фото товаров"),
    "brigade": ("Бүткөн иштер", "Наши работы"),
    "realtor": ("Объектилерибиз", "Наши объекты"),
    "auto": ("Унаалар жана салон", "Автомобили и салон"),
    "builder": ("Курулган объектилер", "Построенные объекты"),
    "transport": ("Унааларыбыз", "Наш автопарк"),
    "salon": ("Иштерибиз", "Наши работы"),
    "edu": ("Сабактардан сүрөттөр", "Фото с занятий"),
    "farm": ("Фермадан сүрөттөр", "Фото с фермы"),
    "factory": ("Продукциябыз", "Наша продукция"),
}


def pf_label(k, ru=False):
    v = PF_LBL.get(k) or PF_LBL["store"]
    return v[1] if ru else v[0]


_KL_JS = """<script>(function(){var M=__M__;var s=document.querySelector('select[name=kind]'),l=document.getElementById('pflb');
if(!s||!l)return;function ap(){l.textContent='📸 '+(M[s.value]||M.store)[0]+' (бир нечесин тандаса болот)';}
s.addEventListener('change',ap);ap();})();</script>"""

_admin_kl_base = admin


def admin(h, uid, q, p, msg, page, k):
    def page4(title, body, tab="", m=""):
        body = body.replace("<label>Портфолио — бүткөн иштер (бир нечесин тандаса болот)</label>",
                            "<label id='pflb'>📸 Сүрөттөр (бир нечесин тандаса болот)</label>")
        return page(title, body + _KL_JS.replace("__M__", _json.dumps(PF_LBL, ensure_ascii=False)), tab, m)
    return _admin_kl_base(h, uid, q, p, msg, page4, k)


# ── PLUSSELF: сатуучу ТАП+'ты өзү ачат (7 күн акысыз), төлөмдү чек менен өзү узартат ──
_PP = {"ready": False}
PAY_MONTHS = {1: 1, 2: 2, 3: 2.4}   # PAYMON: 3 ай алса −20% (3 × 0.8 = 2.4 айдын баасы)


def pp_init():
    if _PP["ready"]:
        return
    _ensure2()
    if getattr(core, "IS_PG", False):
        core.query("CREATE TABLE IF NOT EXISTS plus_pay (id SERIAL PRIMARY KEY, tg_id TEXT, tier TEXT, months INTEGER, "
                   "amount INTEGER, img INTEGER, status TEXT, at TEXT, done_at TEXT)")
    else:
        core.query("CREATE TABLE IF NOT EXISTS plus_pay (id INTEGER PRIMARY KEY AUTOINCREMENT, tg_id TEXT, tier TEXT, "
                   "months INTEGER, amount INTEGER, img INTEGER, status TEXT, at TEXT, done_at TEXT)")
    _PP["ready"] = True


def pp_amount(tier, months):
    return int(round(TIER[tier][2] * PAY_MONTHS.get(int(months), int(months)) / 10.0)) * 10


def pp_extend(tg_id, tier, days):
    """Тарифти коюп, мөөнөтүн узартат (бүгүндөн же азыркы мөөнөттөн)."""
    r = get(tg_id) or {}
    start = max(_today(), str(r.get("until") or ""))
    d = _dt.date.fromisoformat(start) + _dt.timedelta(days=int(days))
    core.query("UPDATE sellers SET tier=?, until=? WHERE tg_id=?", (tier, d.isoformat(), str(tg_id)))
    _load(force=True)
    return d.isoformat()


_admin_pp_base = admin


def admin(h, uid, q, p, msg, page, k):
    if not p.startswith("/admin/plus/pay"):
        return _admin_pp_base(h, uid, q, p, msg, page, k)
    pp_init()
    if getattr(h, "command", "GET") == "POST":
        try:
            n = int(h.headers.get("Content-Length") or 0)
            d = parse_qs(h.rfile.read(n).decode("utf-8")) if 0 < n < 5000 else {}
        except Exception:
            d = {}
        g = lambda x: (d.get(x) or [""])[0]
        if g("k") != k:
            return h._send(page("ТАП+ төлөм", "<p class='er'>Ката: k</p>", "pl"))
        pid = int(g("id") or 0)
        r = core.query("SELECT * FROM plus_pay WHERE id=?", (pid,), fetch="one")
        if r and dict(r)["status"] == "wait":
            r = dict(r)
            if g("act") == "ok":
                until = pp_extend(r["tg_id"], r["tier"], int(r["months"]) * 30)
                core.query("UPDATE plus_pay SET status='ok', done_at=? WHERE id=?", (core.now_str(), pid))
                m = "✅ Ырасталды: %s чейин" % until
            else:
                core.query("UPDATE plus_pay SET status='no', done_at=? WHERE id=?", (core.now_str(), pid))
                m = "❌ Четке кагылды"
            return h._go("/admin/plus/pay?id=%d&m=%s" % (pid, quote(m)))
    pid = int((q.get("id") or ["0"])[0] or 0)
    if pid:
        r = core.query("SELECT * FROM plus_pay WHERE id=?", (pid,), fetch="one")
        if not r:
            return h._send(page("ТАП+ төлөм", "<p>Табылган жок.</p>", "pl", msg))
        r = dict(r)
        s = get(r["tg_id"]) or {}
        st = {"wait": "⏳ Күтүүдө", "ok": "✅ Ырасталды", "no": "❌ Четке кагылды", "trial": "🎁 Акысыз сыноо"}.get(r["status"], r["status"])
        body = ("<div style='background:#fff;border-radius:14px;padding:14px;line-height:1.6'>"
                "<b style='font-size:18px'>%s</b><br>📞 %s<br>🏷 %s · %d ай<br>💵 <b>%s сом</b><br>📅 %s<br>Абалы: <b>%s</b>"
                "<br>Азыркы мөөнөтү: %s</div>%s"
                % (E(str(s.get("name") or "")), E(str(s.get("phone") or "")), E(TIER.get(r["tier"], ("", r["tier"]))[1]),
                   int(r["months"] or 0), "{:,}".format(int(r["amount"] or 0)).replace(",", " "), E(str(r["at"] or "")[:16]),
                   st, E(str(s.get("until") or "—")),
                   ("<p><b>Чек:</b></p><a href='/pi/%d.jpg' target='_blank'><img src='/pi/%d.jpg' style='max-width:100%%;border-radius:12px'></a>"
                    % (int(r["img"]), int(r["img"]))) if r.get("img") else ""))
        if r["status"] == "wait":
            body += ("<form method='post' action='/admin/plus/pay' style='display:flex;gap:8px;margin-top:14px'>"
                     "<input type='hidden' name='k' value='%s'><input type='hidden' name='id' value='%d'>"
                     "<button name='act' value='ok' style='flex:1;border:0;border-radius:10px;padding:13px;background:#1F7A4D;color:#fff;font-weight:800;font-size:15px'>✅ Ырастоо (+%d күн)</button>"
                     "<button name='act' value='no' style='flex:1;border:1.5px solid #E24B4A;border-radius:10px;padding:13px;background:#fff;color:#A32D2D;font-weight:800;font-size:15px'>❌ Четке кагуу</button></form>"
                     % (E(k), pid, int(r["months"]) * 30))
        return h._send(page("ТАП+ төлөм №%d" % pid, body, "pl", msg))
    rows = core.query("SELECT * FROM plus_pay WHERE status<>'trial' ORDER BY id DESC LIMIT 100", fetch="all") or []
    t = "".join("<tr><td><a href='/admin/plus/pay?id=%d'>№%d</a></td><td>%s</td><td>%s · %d ай</td><td>%s</td></tr>"
                % (int(dict(r)["id"]), int(dict(r)["id"]), E(str((get(dict(r)["tg_id"]) or {}).get("name") or dict(r)["tg_id"])),
                   E(TIER.get(dict(r)["tier"], ("", dict(r)["tier"]))[1]), int(dict(r)["months"] or 0),
                   {"wait": "⏳", "ok": "✅", "no": "❌"}.get(dict(r)["status"], "")) for r in rows)
    return h._send(page("ТАП+ төлөмдөр", _ACSS + "<table class='pt'>%s</table>" % (t or "<tr><td>Азырынча жок</td></tr>"), "pl", msg))


# ── KINDS4: жаңы барак түрлөрү — кафе, тойкана, автосервис, мейманкана ──
for _k in [("cafe", "🍽", "Кафе, ресторан", "Меню", "Ашпозчулар", "🛵 Буйрутма / стол брондоо"),
           ("toy", "🎉", "Тойкана, иш-чара", "Залдар жана пакеттер", "Команда", "📅 Күндү брондоо"),
           ("autosvc", "🔧", "Автосервис, СТО", "Кызматтар", "Усталар", "🔧 Сервиске жазылуу"),
           ("hotel", "🏨", "Мейманкана, конок үй", "Бөлмөлөр", "Кызматкерлер", "🛏 Бөлмө брондоо")]:
    if _k[0] not in KIND:
        KINDS.append(_k)
        KIND[_k[0]] = _k
KIND_RU.update({"cafe": "Кафе, ресторан", "toy": "Банкетный зал, мероприятия", "autosvc": "Автосервис, СТО",
                "hotel": "Гостиница, гостевой дом"})
try:
    ADM_EX.update({
        "cafe": {"name": "«Ала-Тоо» кафеси", "address": "Бишкек, Чүй пр. 150", "hours": "10:00–23:00, күн сайын",
                 "about": "Улуттук жана европа ашканасы. Жеткирүү бар.", "facts": "🍽 80 орун\n🛵 Жеткирүү 40 мүнөттө\n🅿️ Унаа токтотмо",
                 "services": "Улуттук тамак, Шашлык, Пицца, Бизнес-ланч, Жеткирүү",
                 "conds": "Жеткирүү: 300 сомдон ашса акысыз\nБизнес-ланч: 12:00–15:00\nБанкет: 30 кишиге чейин",
                 "team": "Айбек — башкы ашпозчу", "prices": "Бешбармак — 450 сом\nЛагман — 300 сом\nБизнес-ланч — 350 сом",
                 "promo": "Бизнес-ланч −10%"},
        "toy": {"name": "«Ак Сарай» тойканасы", "address": "Бишкек, Ахунбаев 98", "hours": "Алдын ала жазылуу менен",
                "about": "Той, үлпөт, юбилей. Эки зал: 150 жана 300 киши.", "facts": "👥 300 кишиге чейин\n🎤 Үн жабдуулары\n🅿️ 100 унаа",
                "services": "Үйлөнүү той, Кыз узатуу, Юбилей, Корпоратив, Тушоо кесүү",
                "conds": "Алдын ала төлөм: 30%\nДекор: баасына кирет\nТамада: өзүнчө",
                "team": "Нургүл — менеджер", "prices": "Чоң зал — 1 500 сом/киши\nКичи зал — 1 200 сом/киши",
                "promo": "Жумуш күндөрү −10%"},
        "autosvc": {"name": "«Мотор» СТО", "address": "Бишкек, Ибраимов 115", "hours": "09:00–19:00, жекшембиден башка",
                    "about": "Корея жана Япония унааларын оңдойбуз. Компьютердик диагностика.",
                    "facts": "🔧 6 бокс\n⏱ 15 жыл тажрыйба\n✅ Кепилдик 3 ай",
                    "services": "Май алмаштыруу, Диагностика, Развал-схождение, Ходовой, Кузов, Электрика",
                    "conds": "Диагностика: ремонт болсо акысыз\nКепилдик: 3 ай\nЗапчасть: биздики же сиздики",
                    "team": "Талант — моторист\nЭрмек — электрик", "prices": "Май алмаштыруу — 500 сом\nРазвал — 1 200 сом\nДиагностика — 800 сом",
                    "promo": "Май алмаштырууда фильтр бекер"},
        "hotel": {"name": "«Көл Нуру» конок үйү", "address": "Ысык-Көл, Чолпон-Ата, Советская 45", "hours": "24/7",
                  "about": "Көлгө 300 м. Бакча, бассейн, мончо.", "facts": "🛏 12 бөлмө\n🏖 Көлгө 300 м\n🍳 Эртең мененки тамак",
                  "services": "Стандарт бөлмө, Үй-бүлөлүк бөлмө, Коттедж, Мончо, Трансфер",
                  "conds": "Кирүү: 14:00\nЧыгуу: 12:00\nАлдын ала төлөм: 1 түн",
                  "team": "Айгүл — администратор", "prices": "Стандарт — 3 500 сом/түн\nҮй-бүлөлүк — 5 500 сом/түн\nКоттедж — 9 000 сом/түн",
                  "promo": "Сентябрда −20%"},
    })
    _ADMEX_LB.update({"cafe": ("Меню", "Ашпозчулар", "Тамак"), "toy": ("Залдар жана пакеттер", "Команда", "Зал / пакет"),
                      "autosvc": ("Кызматтар", "Усталар", "Кызмат"), "hotel": ("Бөлмөлөр", "Кызматкерлер", "Бөлмө")})
    PF_LBL.update({"cafe": ("Кафенин сүрөттөрү", "Фото кафе"), "toy": ("Залдын сүрөттөрү", "Фото зала"),
                   "autosvc": ("Сервистин сүрөттөрү", "Фото сервиса"), "hotel": ("Мейманкананын сүрөттөрү", "Фото гостиницы")})
except Exception:
    pass


# ── KINDS6: дагы 6 барак түрү ──
for _k in [("clean", "🧹", "Тазалоо (клининг)", "Кызматтар", "Команда", "🧹 Тазалоого чакыруу"),
           ("photo", "📸", "Фото, видео, тамада", "Пакеттер", "Команда", "📅 Күндү брондоо"),
           ("vet", "🐾", "Ветеринария, зоо дүкөн", "Кызматтар жана товарлар", "Врачтар", "📅 Жазылуу"),
           ("legal", "⚖️", "Юрист, бухгалтер, нотариус", "Кызматтар", "Адистер", "📞 Консультация алуу"),
           ("fitness", "🏋️", "Спорт зал, фитнес", "Абонементтер", "Машыктыруучулар", "📅 Сынамык сабак"),
           ("travel", "✈️", "Туристтик агенттик", "Турлар", "Менеджерлер", "✈️ Турга жазылуу")]:
    if _k[0] not in KIND:
        KINDS.append(_k)
        KIND[_k[0]] = _k
KIND_RU.update({"clean": "Клининг", "photo": "Фото, видео, тамада", "vet": "Ветклиника, зоомагазин",
                "legal": "Юрист, бухгалтер, нотариус", "fitness": "Спортзал, фитнес", "travel": "Турагентство"})
try:
    ADM_EX.update({
        "clean": {"name": "«Таза Үй» клининг", "address": "Бишкек", "hours": "08:00–20:00, күн сайын",
                  "about": "Батир, офис, ремонттон кийинки тазалоо. Өз каражаттарыбыз менен.",
                  "facts": "🧹 10 кызматкер\n⏱ 3 саатта бүтөт\n✅ Кепилдик", "services": "Жалпы тазалоо, Ремонттон кийин, Терезе жуу, Килем жуу, Офис",
                  "conds": "Чыгуу: акысыз\nКаражат: биздики\nЭң аз буйрутма: 2 000 сом", "team": "Айгерим — менеджер",
                  "prices": "Жалпы тазалоо — 60 сом/м²\nРемонттон кийин — 90 сом/м²\nТерезе — 300 сом/даана", "promo": "Биринчи буйрутмага −15%"},
        "photo": {"name": "Нурлан Studio", "address": "Бишкек", "hours": "Алдын ала жазылуу менен",
                  "about": "Той, кыз узатуу, love story. Видео + дрон.", "facts": "📸 8 жыл тажрыйба\n🎬 300+ той\n🚁 Дрон",
                  "services": "Тойго фото, Видео, Дрон, Love story, Тамада", "conds": "Алдын ала төлөм: 30%\nДаяр болот: 14 күндө",
                  "team": "Нурлан — фотограф\nАйбек — видеограф", "prices": "Фото (6 саат) — 15 000 сом\nФото + видео — 30 000 сом", "promo": "Жумуш күндөрү −10%"},
        "vet": {"name": "«Достук» ветклиникасы", "address": "Бишкек, Токтогул 90", "hours": "09:00–21:00, күн сайын",
                "about": "Ит, мышык, мал үчүн дарылоо. Үйгө чыгуу бар.", "facts": "🩺 4 врач\n🏠 Үйгө чыгуу\n💉 Эмдөө",
                "services": "Кароо, Эмдөө, Стерилизация, Тиш тазалоо, Тамак-аш", "conds": "Үйгө чыгуу: 500 сом\nШашылыш: 24/7 телефон",
                "team": "Асель — ветеринар", "prices": "Кароо — 500 сом\nЭмдөө — 900 сом", "promo": "Эмдөө −20%"},
        "legal": {"name": "Юрист Айжан Токтосунова", "address": "Бишкек, Киев 77, 3-кабат", "hours": "09:00–18:00, ишемби-жекшемби дем алыш",
                  "about": "Үй-жер, мурас, ажырашуу, ишкер каттоо.", "facts": "⚖️ 12 жыл тажрыйба\n📄 500+ иш", "services": "Консультация, Келишим, Сот, ИП каттоо, Бухгалтерия",
                  "conds": "Биринчи консультация: 15 мүнөт акысыз", "team": "Айжан — юрист", "prices": "Консультация — 1 000 сом\nКелишим түзүү — 3 000 сом", "promo": ""},
        "fitness": {"name": "«Чемпион» спорт зал", "address": "Ош, Курманжан Датка 200", "hours": "07:00–23:00, күн сайын",
                    "about": "Тренажерлор, бокс, аэробика. Аялдар үчүн өзүнчө зал.", "facts": "🏋️ 600 м²\n👩 Аялдар залы\n🚿 Душ",
                    "services": "Тренажер зал, Бокс, Аэробика, Жеке машыктыруучу", "conds": "Сынамык сабак: акысыз",
                    "team": "Мирлан — бокс\nЖаңыл — аэробика", "prices": "Ай — 2 500 сом\n3 ай — 6 500 сом\nЖеке — 800 сом/сабак", "promo": "Студенттерге −20%"},
        "travel": {"name": "«Ала-Тоо Travel»", "address": "Бишкек, Чүй пр. 120", "hours": "09:00–19:00",
                   "about": "Ысык-Көл, Түркия, Дубай, Умра. Виза жардамы.", "facts": "✈️ 10 жыл\n🧳 5 000+ турист", "services": "Ысык-Көл, Түркия, Дубай, Умра, Виза",
                   "conds": "Бөлүп төлөө: бар\nАлдын ала: 30%", "team": "Айдана — менеджер",
                   "prices": "Ысык-Көл (3 күн) — 9 000 сом\nТүркия (7 күн) — 650 $", "promo": "Эрте брондоо −10%"},
    })
    _ADMEX_LB.update({"clean": ("Кызматтар", "Команда", "Кызмат"), "photo": ("Пакеттер", "Команда", "Пакет"),
                      "vet": ("Кызматтар жана товарлар", "Врачтар", "Кызмат"), "legal": ("Кызматтар", "Адистер", "Кызмат"),
                      "fitness": ("Абонементтер", "Машыктыруучулар", "Абонемент"), "travel": ("Турлар", "Менеджерлер", "Тур")})
    PF_LBL.update({"clean": ("Иштерибиз (чейин/кийин)", "Наши работы (до/после)"), "photo": ("Портфолио", "Портфолио"),
                   "vet": ("Клиниканын сүрөттөрү", "Фото клиники"), "legal": ("Офистин сүрөттөрү", "Фото офиса"),
                   "fitness": ("Залдын сүрөттөрү", "Фото зала"), "travel": ("Турлардан сүрөттөр", "Фото с туров")})
except Exception:
    pass


# ══ ADMDEL: админ — сатуучуну өчүрүү, логотип/баннерди алып салуу, витринаны тазалоо ══
import io as _adio
from urllib.parse import unquote as _ad_unq


def _ad_try(sql, args):
    try:
        core.query(sql, args)
    except Exception as e:
        print("admdel:", e, flush=True)


def _ad_del_seller(tg):
    tg = str(tg)
    _ad_try("DELETE FROM seller_imgs WHERE tg_id=?", (tg,))
    _ad_try("DELETE FROM seller_vit WHERE tg_id=?", (tg,))
    _ad_try("DELETE FROM seller_busy WHERE tg_id=?", (tg,))
    _ad_try("DELETE FROM seller_slugs WHERE tg_id=?", (tg,))
    _ad_try("DELETE FROM shop_events WHERE tg_id=?", (tg,))
    _ad_try("DELETE FROM sellers WHERE tg_id=?", (tg,))


def _ad_vit(tg):
    try:
        return [dict(r) for r in (core.query("SELECT id, img, name, price FROM seller_vit WHERE tg_id=? ORDER BY pos, id",
                                             (str(tg),), fetch="all") or [])]
    except Exception:
        return []


_admin_ad_base = admin


def admin(h, uid, q, p, msg, page, k):
    post = getattr(h, "command", "GET") == "POST"
    if p == "/admin/plus/del" and post:
        try:
            n = int(h.headers.get("Content-Length") or 0)
            d = parse_qs(h.rfile.read(n).decode("utf-8")) if 0 < n < 100000 else {}
        except Exception:
            d = {}
        g = lambda x: (d.get(x) or [""])[0].strip()
        if not hmac.compare_digest(g("k"), k):
            return h._go("/admin/plus?m=" + quote("Сессия бүттү, кайра кириңиз"))
        tg = g("tg")
        r = core.query("SELECT name FROM sellers WHERE tg_id=?", (tg,), fetch="one")
        if not r:
            return h._go("/admin/plus?m=" + quote("Сатуучу табылган жок"))
        _ad_del_seller(tg)
        _load(force=True)
        try:
            core.cache_clear()
        except Exception:
            pass
        return h._go("/admin/plus?m=" + quote("🗑 Өчүрүлдү: %s (жарыяларына тийилген жок)" % (dict(r).get("name") or tg)))
    if p == "/admin/plus/save" and post:
        try:
            n = int(h.headers.get("Content-Length") or 0)
            raw = h.rfile.read(n) if 0 < n < 16_000_000 else b""
        except Exception:
            raw = b""
        try:
            d = parse_qs(raw.decode("utf-8"))
            g = lambda x: (d.get(x) or [""])[0].strip()
            tg = g("old")
            if tg and hmac.compare_digest(g("k"), k):
                if g("logo_del"):
                    _ad_try("UPDATE sellers SET logo=NULL WHERE tg_id=?", (tg,))
                if g("banner_del"):
                    _ad_try("UPDATE sellers SET banner=NULL WHERE tg_id=?", (tg,))
                for vid in d.get("vit_del") or []:
                    if str(vid).isdigit():
                        r = core.query("SELECT img FROM seller_vit WHERE id=? AND tg_id=?", (int(vid), tg), fetch="one")
                        if r and dict(r).get("img"):
                            _ad_try("DELETE FROM seller_imgs WHERE id=? AND tg_id=?", (int(dict(r)["img"]), tg))
                        _ad_try("DELETE FROM seller_vit WHERE id=? AND tg_id=?", (int(vid), tg))
        except Exception as e:
            print("admdel save:", e, flush=True)
        h.rfile = _adio.BytesIO(raw)
        return _admin_ad_base(h, uid, q, p, msg, page, k)
    if p != "/admin/plus":
        return _admin_ad_base(h, uid, q, p, msg, page, k)
    orig = h._send
    ed = (q.get("edit") or [""])[0]

    def _send2(body, *a, **kw):
        try:
            # 🗑 ар бир сатуучунун жанында
            import re as _re

            def rep(m):
                tgq = m.group(1)
                tgv = _ad_unq(tgq)
                return (m.group(0) + "<form method='post' action='/admin/plus/del' style='display:inline;margin-left:10px' "
                        "onsubmit=\"return confirm('Бул сатуучунун ТАП+ барагы, сүрөттөрү жана витринасы толук өчөт. "
                        "Жарыяларына тийилбейт.\\n\\nЧын эле өчүрөсүзбү?')\">"
                        "<input type='hidden' name='k' value='%s'><input type='hidden' name='tg' value='%s'>"
                        "<button style='border:0;background:none;font-size:18px;cursor:pointer;padding:0'>🗑</button></form>"
                        % (E(k), E(tgv)))
            body = _re.sub(r"<a href='/admin/plus\?edit=([^']*)'>✏️</a>", rep, body)
            if ed:
                cur = _C["tg"].get(ed) or {}
                if cur.get("logo"):
                    body = body.replace("<img id='logo_data_p' class='im'>",
                                        "<img id='logo_data_p' class='im'><label class='ck'><input type='checkbox' name='logo_del' value='1'> 🗑 Логотипти алып салуу</label>", 1)
                if cur.get("banner"):
                    body = body.replace("<img id='banner_data_p' class='im' style='max-width:100%'>",
                                        "<img id='banner_data_p' class='im' style='max-width:100%'><label class='ck'><input type='checkbox' name='banner_del' value='1'> 🗑 Баннерди алып салуу</label>", 1)
                vit = _ad_vit(ed)
                if vit:
                    cells = "".join("<label><img src='/pi/%d.jpg'><input type='checkbox' name='vit_del' value='%d'> өчүрүү<br>%s%s</label>"
                                    % (int(v.get("img") or 0), int(v["id"]), E(str(v.get("name") or "")),
                                       (" · " + E(str(v.get("price")))) if v.get("price") else "") for v in vit)
                    fs = ("<fieldset><legend>🛍 Витрина (%d товар)</legend><div class='pfg'>%s</div>"
                          "<p style='font-size:12.5px;color:#5A6982;margin:6px 0 0'>Белгилеп, «💾 Сактоо» басыңыз.</p></fieldset>"
                          % (len(vit), cells))
                    body = body.replace("<fieldset><legend>🏷 Акция</legend>", fs + "<fieldset><legend>🏷 Акция</legend>", 1)
        except Exception as e:
            print("admdel page:", e, flush=True)
        return orig(body, *a, **kw)
    h._send = _send2
    try:
        return _admin_ad_base(h, uid, q, p, msg, page, k)
    finally:
        try:
            del h._send
        except Exception:
            pass


# ── MENUFIX: кафеде «Меню» — сүрөттүү тизме (витрина); тексттик талаа эми «Ашкана түрү» ──
try:
    _mk = KIND.get("cafe")
    if _mk:
        _nk = (_mk[0], _mk[1], _mk[2], "Ашкана түрү") + tuple(_mk[4:])
        KIND["cafe"] = _nk
        for _i, _x in enumerate(KINDS):
            if _x[0] == "cafe":
                KINDS[_i] = _nk
    ADM_EX["cafe"]["services"] = "Улуттук, Европа, Түрк, Пицца, Фаст-фуд"
except Exception as _e:
    print("menufix:", _e, flush=True)
