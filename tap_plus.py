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

