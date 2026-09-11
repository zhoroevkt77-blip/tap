"""ТАП! админ панели: кирүү, статистика, жарыялар."""
import os
import time
import hmac
import hashlib
import html
from datetime import datetime, timedelta
from urllib.parse import parse_qs, quote, urlencode

import core

TTL_LINK = 600
TTL_SESS = 12 * 3600
PER = 25
_ENV = ("BOT_TOKEN", "TOKEN", "TELEGRAM_TOKEN", "TG_TOKEN", "DATABASE_URL")
SEC_KY = {
    "personal": "Жеке буюмдар",
    "transport": "Транспорт",
    "shop": "Курулуш жана азык-түлүк",
    "realty": "Кыймылсыз мүлк",
}
E = html.escape


def _ids():
    raw = (os.environ.get("ADMIN_IDS") or "").replace(" ", "")
    return [x for x in raw.split(",") if x]


def _secret():
    s = os.environ.get("ADMIN_SECRET") or "|".join(
        os.environ.get(k, "") for k in _ENV)
    if not s.strip("|"):
        return None
    return hashlib.sha256(("tap-admin|" + s).encode()).digest()


def _sign(uid, exp, kind):
    key = _secret()
    if not key:
        return ""
    msg = "%s.%s.%s" % (kind, uid, exp)
    return hmac.new(key, msg.encode(), hashlib.sha256).hexdigest()[:32]


def make_token(uid):
    exp = int(time.time()) + TTL_LINK
    sig = _sign(uid, exp, "L")
    return "%s.%d.%s" % (uid, exp, sig) if sig else ""


def _check(tok, kind):
    try:
        uid, exp, sig = tok.split(".")
        if int(exp) < time.time():
            return None
        good = _sign(uid, exp, kind)
        if not good or not hmac.compare_digest(sig, good):
            return None
        return uid if uid in _ids() else None
    except Exception:
        return None


def _me(h):
    for part in (h.headers.get("Cookie") or "").split(";"):
        k, _, v = part.strip().partition("=")
        if k == "adm":
            return _check(v, "S")
    return None


def _csrf(uid):
    return _sign(uid, "0", "C")[:20]


def _q(q, k):
    return (q.get(k) or [""])[0]


def _g(r, key, i):
    try:
        return r[key]
    except Exception:
        return r[i]


def _n(sql, p=()):
    try:
        r = core.query(sql, p, fetch="one")
        return int(_g(r, "n", 0) or 0) if r else 0
    except Exception:
        return "?"


def _sec_name(code):
    code = str(code or "")
    if code in SEC_KY:
        return SEC_KY[code]
    try:
        import bridge
        v = bridge.SECTION_LABELS.get(code) or bridge.cat_label(code) or code
    except Exception:
        v = code
    if isinstance(v, (list, tuple)):
        v = v[0]
    return str(v or "-").split(" / ")[0]


def _parse(s):
    s = str(s or "").replace("T", " ")
    for n, f in ((19, "%Y-%m-%d %H:%M:%S"), (16, "%Y-%m-%d %H:%M"),
                 (10, "%Y-%m-%d")):
        try:
            return datetime.strptime(s[:n], f)
        except Exception:
            pass
    return None


def _fmt(dt):
    ref = core.now_str()
    sep = "T" if "T" in ref else " "
    return dt.strftime("%Y-%m-%d" + sep + "%H:%M:%S")[:len(ref)]


CSS = (
    "body{margin:0;font-family:system-ui,sans-serif;background:#F1F4F9;color:#152741}"
    "header{display:flex;justify-content:space-between;align-items:center;"
    "padding:14px 16px;background:#17365C;color:#fff;font-size:18px}"
    "header a{color:#E3C368;text-decoration:none;font-size:15px}"
    "nav{display:flex;gap:6px;overflow-x:auto;padding:10px 12px;background:#fff;"
    "border-bottom:1.5px solid #9AA8BF}"
    "nav a,nav span{white-space:nowrap;padding:7px 12px;border-radius:99px;font-size:14px}"
    "nav a{background:#fff;color:#17365C;border:1.5px solid #9AA8BF;text-decoration:none}"
    "nav a.on{background:#17365C;color:#fff;border-color:#17365C}"
    "nav span{color:#8B97AC;border:1px solid #D5DCE7}"
    "main{padding:14px}h1{font-size:20px;margin:4px 0 12px}h2{font-size:17px;margin:18px 0 8px}"
    ".g{display:grid;grid-template-columns:1fr 1fr;gap:10px}"
    ".k{background:#fff;border:1.5px solid #9AA8BF;border-radius:14px;padding:12px}"
    ".k small{display:block;font-size:13px;color:#33425A;margin-bottom:4px}"
    ".k b{font-size:24px}"
    "table{width:100%;border-collapse:collapse;background:#fff;border:1.5px solid #9AA8BF}"
    "td{padding:10px 12px;border-bottom:1px solid #E1E7F1;font-size:15px}"
    "td:last-child{text-align:right;font-weight:600}"
    ".er{background:#fff;border:1.5px solid #E24B4A;border-radius:12px;padding:14px}"
    ".ok{background:#E6F4EC;border:1.5px solid #1F7A4D;color:#1F5E3C;"
    "border-radius:12px;padding:10px 12px;margin-bottom:12px}"
    ".sf{display:flex;gap:8px;margin-bottom:10px}"
    ".sf input{flex:1;min-width:0;padding:10px 12px;border:1.5px solid #9AA8BF;"
    "border-radius:12px;font-size:15px}"
    ".sf button{padding:10px 16px;border:0;border-radius:12px;background:#C9A03A;"
    "color:#14243F;font-weight:700;font-size:15px}"
    ".fl{display:flex;gap:6px;overflow-x:auto;margin-bottom:10px}"
    ".fl a{white-space:nowrap;padding:6px 12px;border-radius:99px;border:1.5px solid #9AA8BF;"
    "color:#17365C;text-decoration:none;font-size:14px;background:#fff}"
    ".fl a.on{background:#17365C;color:#fff;border-color:#17365C}"
    ".cnt{font-size:14px;color:#33425A;margin:0 0 10px}"
    ".ad{background:#fff;border:1.5px solid #9AA8BF;border-radius:14px;padding:12px;margin-bottom:10px}"
    ".ah{font-size:15px;font-weight:600;margin-bottom:4px}"
    ".am{font-size:13px;color:#33425A;margin-top:3px}"
    ".b{display:inline-block;font-size:12px;padding:2px 8px;border-radius:99px;margin-left:4px}"
    ".b.ac{background:#E6F4EC;color:#1F5E3C}.b.ex{background:#F1F4F9;color:#5A6982}"
    ".b.w{background:#FAEEDA;color:#854F0B}"
    ".ab{display:flex;gap:8px;margin-top:10px}"
    ".ab a{flex:1;text-align:center;padding:8px 6px;border-radius:10px;font-size:14px;"
    "text-decoration:none;border:1.5px solid #9AA8BF;color:#17365C}"
    ".ab a.del{border-color:#E24B4A;color:#A32D2D}"
    ".pg{display:flex;justify-content:space-between;margin:12px 0}"
    ".pg a{color:#17365C;font-weight:600;text-decoration:none}"
)


def _page(title, body, tab="", msg=""):
    tabs = ""
    for href, key, name in (("/admin", "st", "Статистика"),
                            ("/admin/ads", "ads", "Жарыялар")):
        tabs += "<a href='%s'%s>%s</a>" % (href, " class='on'" if tab == key else "", name)
    tabs += "<span>Модерация</span><span>Колдонуучулар</span>"
    flash = "<p class='ok'>" + E(msg) + "</p>" if msg else ""
    return ("<!doctype html><html lang='ky'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<meta name='robots' content='noindex'><title>ТАП! Админ · " + E(title) +
            "</title><style>" + CSS + "</style></head><body>"
            "<header><b>ТАП! Админ</b><a href='/admin/logout'>Чыгуу</a></header>"
            "<nav>" + tabs + "</nav><main><h1>" + E(title) + "</h1>" + flash +
            body + "</main></body></html>")


def _stats():
    now = core.now_str()
    day = now[:10] + "%"
    tiles = [
        ("Жалпы жарыя", _n("SELECT COUNT(*) AS n FROM listings")),
        ("Активдүү", _n("SELECT COUNT(*) AS n FROM listings WHERE expires_at>?", (now,))),
        ("Бүгүн коюлду", _n("SELECT COUNT(*) AS n FROM listings WHERE created_at LIKE ?", (day,))),
        ("Мөөнөтү бүткөн", _n("SELECT COUNT(*) AS n FROM listings WHERE expires_at<=?", (now,))),
        ("⚠️ Шектүү", _n("SELECT COUNT(*) AS n FROM listings WHERE warned='1'")),
        ("Жалпы көрүү", _n("SELECT COALESCE(SUM(views),0) AS n FROM listings")),
        ("Колдонуучулар", _n("SELECT COUNT(*) AS n FROM users")),
        ("Бүгүн кошулду", _n("SELECT COUNT(*) AS n FROM users WHERE created_at LIKE ?", (day,))),
    ]
    body = "<div class='g'>" + "".join(
        "<div class='k'><small>" + E(a) + "</small><b>" + str(b) + "</b></div>"
        for a, b in tiles) + "</div>"
    try:
        rows = core.query(
            "SELECT category, COUNT(*) AS n FROM listings WHERE expires_at>? "
            "GROUP BY category ORDER BY n DESC", (now,), fetch="all") or []
    except Exception:
        rows = []
    if rows:
        body += "<h2>Бөлүмдөр (активдүү)</h2><table>" + "".join(
            "<tr><td>" + E(_sec_name(_g(r, "category", 0))) +
            "</td><td>" + str(_g(r, "n", 1)) + "</td></tr>" for r in rows) + "</table>"
    return body


def _delete(lid):
    for name in ("delete_listing", "del_listing", "remove_listing"):
        fn = getattr(core, name, None)
        if callable(fn):
            try:
                fn(lid)
                return
            except TypeError:
                break
    core.query("DELETE FROM listings WHERE id=?", (lid,))


def _extend(lid, days=7):
    r = core.query("SELECT expires_at FROM listings WHERE id=?", (lid,), fetch="one")
    if not r:
        return False
    now = _parse(core.now_str()) or datetime.now()
    cur = _parse(_g(r, "expires_at", 0)) or now
    new = max(cur, now) + timedelta(days=days)
    core.query("UPDATE listings SET expires_at=? WHERE id=?", (_fmt(new), lid))
    return True


def _do(h, uid, q):
    a, lid = _q(q, "a"), _q(q, "id")
    back = _q(q, "back") or "/admin/ads"
    if not back.startswith("/admin"):
        back = "/admin/ads"
    if not lid.isdigit() or not hmac.compare_digest(_q(q, "k"), _csrf(uid)):
        h._send(_page("Ката", "<p class='er'>Жараксыз суроо.</p>"), 403)
        return
    lid = int(lid)
    if a == "del":
        _delete(lid)
        msg = "№%d өчүрүлдү" % lid
    elif a == "ext":
        msg = ("№%d: +7 күн узартылды" % lid) if _extend(lid) else "Жарыя табылган жок"
    else:
        msg = "Белгисиз аракет"
    sep = "&" if "?" in back else "?"
    h._go(back + sep + "m=" + quote(msg), None)


def _ads(uid, q):
    s = _q(q, "q").strip()[:60]
    f = _q(q, "f") or "all"
    pg = _q(q, "p")
    pg = int(pg) if pg.isdigit() and int(pg) > 0 else 1
    now = core.now_str()
    where, par = [], []
    if f == "act":
        where.append("expires_at>?")
        par.append(now)
    elif f == "exp":
        where.append("expires_at<=?")
        par.append(now)
    elif f == "warn":
        where.append("warned='1'")
    if s:
        if s.isdigit():
            where.append("(id=? OR contact LIKE ?)")
            par += [int(s), "%" + s + "%"]
        else:
            like = "%" + s.lower() + "%"
            where.append("(LOWER(title) LIKE ? OR stext LIKE ?)")
            par += [like, like]
    w = (" WHERE " + " AND ".join(where)) if where else ""
    total = _n("SELECT COUNT(*) AS n FROM listings" + w, tuple(par))
    rows = core.query("SELECT * FROM listings" + w +
                      " ORDER BY id DESC LIMIT %d OFFSET %d" % (PER, (pg - 1) * PER),
                      tuple(par), fetch="all") or []

    def link(**kw):
        d = {"q": s, "f": f, "p": pg}
        d.update(kw)
        return "/admin/ads?" + urlencode({k: v for k, v in d.items() if v})

    back = link()
    k = _csrf(uid)
    body = ("<form class='sf' method='get' action='/admin/ads'>"
            "<input name='q' value='" + E(s) + "' placeholder='ID, телефон же сөз'>"
            "<input type='hidden' name='f' value='" + E(f) + "'>"
            "<button>Изде</button></form><div class='fl'>")
    for key, name in (("all", "Баары"), ("act", "Активдүү"),
                      ("exp", "Мөөнөтү бүткөн"), ("warn", "⚠️ Шектүү")):
        body += "<a href='%s'%s>%s</a>" % (E(link(f=key, p=1)),
                                           " class='on'" if f == key else "", name)
    body += "</div><p class='cnt'>Табылды: " + str(total) + "</p>"
    import bridge
    for r in rows:
        lid = r.get("id")
        title = bridge.show_title(r) or "-"
        cat = str(bridge.cat_label(r.get("cat_id")) or _sec_name(r.get("category")))
        cat = cat.split(" / ")[0]
        exp = str(r.get("expires_at") or "")
        st = ("<span class='b ac'>Активдүү</span>" if exp > now
              else "<span class='b ex'>Бүткөн</span>")
        wn = "<span class='b w'>⚠️</span>" if str(r.get("warned") or "") == "1" else ""

        def act(a):
            return E("/admin/do?" + urlencode({"a": a, "id": lid, "k": k, "back": back}))
        body += (
            "<div class='ad'><div class='ah'>№" + str(lid) + " · " + E(str(title)) +
            st + wn + "</div>"
            "<div class='am'>" + E(str(r.get("price") or "-")) + " · " + E(cat) +
            " · 👁 " + str(r.get("views") or 0) + "</div>"
            "<div class='am'>Коюлду: " + E(str(r.get("created_at") or "")[:16]) +
            " · Бүтөт: " + E(exp[:10]) + "</div>"
            "<div class='am'>👤 " + E(str(r.get("tg_name") or "-")) + " · 📞 " +
            E(str(r.get("contact") or "-")) + "</div>"
            "<div class='ab'><a href='/e/" + str(lid) + "' target='_blank'>Карап көрүү</a>"
            "<a href='" + act("ext") + "'>+7 күн</a>"
            "<a class='del' href='" + act("del") + "' onclick=\"return confirm('№" +
            str(lid) + " өчүрүлсүнбү?')\">Өчүрүү</a></div></div>")
    if not rows:
        body += "<p class='cnt'>Жарыя жок.</p>"
    nav = ""
    if pg > 1:
        nav += "<a href='" + E(link(p=pg - 1)) + "'>← Мурунку</a>"
    else:
        nav += "<span></span>"
    if isinstance(total, int) and pg * PER < total:
        nav += "<a href='" + E(link(p=pg + 1)) + "'>Кийинки →</a>"
    return body + "<div class='pg'>" + nav + "</div>"


def _route(h, u):
    q = parse_qs(getattr(u, "query", "") or "")
    p = u.path.rstrip("/") or "/admin"
    if p == "/admin/login":
        uid = _check(_q(q, "t"), "L")
        if not uid:
            h._send(_page("Кирүү", "<p class='er'>Шилтеме жараксыз же мөөнөтү "
                          "бүттү. Ботко /admin деп кайра жазыңыз.</p>"), 403)
            return
        exp = int(time.time()) + TTL_SESS
        val = "%s.%d.%s" % (uid, exp, _sign(uid, exp, "S"))
        h._go("/admin", "adm=%s; Path=/admin; Max-Age=%d; HttpOnly; Secure; "
              "SameSite=Lax" % (val, TTL_SESS))
        return
    if p == "/admin/logout":
        h._go("/", "adm=; Path=/admin; Max-Age=0")
        return
    uid = _me(h)
    if not uid:
        h._send(_page("Админ", "<p class='er'>Кирүү үчүн ботко /admin "
                      "деп жазыңыз.</p>"), 403)
        return
    msg = _q(q, "m")
    if p == "/admin/do":
        _do(h, uid, q)
    elif p == "/admin/ads":
        h._send(_page("Жарыялар", _ads(uid, q), "ads", msg))
    else:
        h._send(_page("Статистика", _stats(), "st", msg))


def handle(h, u):
    try:
        _route(h, u)
    except Exception as e:
        h._send(_page("Ката", "<p class='er'>" + E(repr(e)) + "</p>"), 500)
