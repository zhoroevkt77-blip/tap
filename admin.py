"""ТАП! админ панели: кирүү (бот шилтемеси) жана статистика."""
import os
import time
import hmac
import hashlib
import html
from urllib.parse import parse_qs

import core

TTL_LINK = 600
TTL_SESS = 12 * 3600
_ENV = ("BOT_TOKEN", "TOKEN", "TELEGRAM_TOKEN", "TG_TOKEN", "DATABASE_URL")


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
    try:
        import bridge
        v = bridge.SECTION_LABELS.get(code, code)
    except Exception:
        v = code
    if isinstance(v, (list, tuple)):
        v = v[0]
    return str(v or "-").split(" / ")[0]


CSS = (
    "body{margin:0;font-family:system-ui,sans-serif;background:#F1F4F9;color:#152741}"
    "header{display:flex;justify-content:space-between;align-items:center;"
    "padding:14px 16px;background:#17365C;color:#fff;font-size:18px}"
    "header a{color:#E3C368;text-decoration:none;font-size:15px}"
    "nav{display:flex;gap:6px;overflow-x:auto;padding:10px 12px;background:#fff;"
    "border-bottom:1.5px solid #9AA8BF}"
    "nav a,nav span{white-space:nowrap;padding:7px 12px;border-radius:99px;font-size:14px}"
    "nav a{background:#17365C;color:#fff;text-decoration:none}"
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
)


def _page(title, body):
    nav = ("<nav><a href='/admin'>Статистика</a><span>Жарыялар</span>"
           "<span>Модерация</span><span>Колдонуучулар</span></nav>")
    t = html.escape(title)
    return ("<!doctype html><html lang='ky'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<meta name='robots' content='noindex'><title>ТАП! Админ · " + t +
            "</title><style>" + CSS + "</style></head><body>"
            "<header><b>ТАП! Админ</b><a href='/admin/logout'>Чыгуу</a></header>" +
            nav + "<main><h1>" + t + "</h1>" + body + "</main></body></html>")


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
        "<div class='k'><small>" + html.escape(a) + "</small><b>" + str(b) + "</b></div>"
        for a, b in tiles) + "</div>"
    try:
        rows = core.query(
            "SELECT category, COUNT(*) AS n FROM listings WHERE expires_at>? "
            "GROUP BY category ORDER BY n DESC", (now,), fetch="all") or []
    except Exception:
        rows = []
    if rows:
        body += "<h2>Бөлүмдөр (активдүү)</h2><table>" + "".join(
            "<tr><td>" + html.escape(_sec_name(_g(r, "category", 0))) +
            "</td><td>" + str(_g(r, "n", 1)) + "</td></tr>" for r in rows) + "</table>"
    return body


def _route(h, u):
    q = parse_qs(getattr(u, "query", "") or "")
    p = u.path.rstrip("/") or "/admin"
    if p == "/admin/login":
        uid = _check((q.get("t") or [""])[0], "L")
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
    if not _me(h):
        h._send(_page("Админ", "<p class='er'>Кирүү үчүн ботко /admin "
                      "деп жазыңыз.</p>"), 403)
        return
    h._send(_page("Статистика", _stats()))


def handle(h, u):
    try:
        _route(h, u)
    except Exception as e:
        h._send(_page("Ката", "<p class='er'>" + html.escape(repr(e)) + "</p>"), 500)
