"""ТАП! админ панели: кирүү, статистика, жарыялар, модерация, колдонуучулар."""
import os
import re
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
FLG = "flagged IS NOT NULL AND flagged<>''"
ACT = "COALESCE(is_active,1)=1 AND expires_at>?"
E = html.escape
_READY = [False]
_BANC = {}


def _cols():
    if _READY[0]:
        return
    try:
        if getattr(core, "IS_PG", False):
            core.query("ALTER TABLE listings ADD COLUMN IF NOT EXISTS flagged TEXT")
        else:
            try:
                core.query("ALTER TABLE listings ADD COLUMN flagged TEXT")
            except Exception:
                pass
        core.query("CREATE TABLE IF NOT EXISTS bans (tid TEXT PRIMARY KEY, "
                   "reason TEXT, created_at TEXT)")
        _READY[0] = True
    except Exception as e:
        print("admin cols:", e, flush=True)


def flag(lid, why=""):
    """Бот чакырат: шектүү сөз табылган жарыяны белгилейт."""
    _cols()
    why = re.sub(r"<[^>]+>", "", str(why or "")).replace("⚠️", "")
    why = re.sub(r"\s+", " ", why).strip()[:200] or "1"
    core.query("UPDATE listings SET flagged=? WHERE id=?", (why, lid))


RSN = {"scam": "Алдамчылык", "gone": "Товар жок", "wrong": "Туура эмес бөлүм",
       "ban": "Тыюу салынган товар", "other": "Башка себеп"}


def report(h):
    """Колдонуучунун даттануусу (POST). #RPT8"""
    import tap
    lang = "ru" if "lang=ru" in (h.headers.get("Cookie") or "") else "ky"
    try:
        n = int(h.headers.get("Content-Length") or 0)
        q = parse_qs(h.rfile.read(n).decode("utf-8")) if 0 < n < 4000 else {}
    except Exception:
        q = {}
    lid, code = _q(q, "id"), _q(q, "r")
    note = re.sub(r"\s+", " ", _q(q, "t")).strip()[:150]
    ok = "Спасибо! Жалоба принята." if lang == "ru" else "Рахмат! Даттануу кабыл алынды."
    bad = "Жалоба не отправлена." if lang == "ru" else "Даттануу жөнөтүлгөн жок."
    done = False
    if lid.isdigit() and code in RSN:
        try:
            _cols()
            r = core.query("SELECT flagged FROM listings WHERE id=?", (int(lid),),
                           fetch="one")
            if r:
                cur = str(_g(r, "flagged", 0) or "")
                tag = "📣 " + RSN[code] + ((": " + note) if note else "")
                if tag not in cur:
                    core.query("UPDATE listings SET flagged=? WHERE id=?",
                               ((cur + " · " + tag).strip(" ·")[:400], int(lid)))
                done = True
        except Exception as e:
            print("report:", e, flush=True)
    back = "/e/" + lid if lid.isdigit() else "/"
    body = ("<main class='wrap'><div class='rok'>" + E(ok if done else bad) + "</div>"
            "<p><a href='" + E(back) + "'>← Артка</a></p></main>")
    h._send(tap.page(tap.header("", None, None, lang) + body, "ТАП!", "", lang))


WARN = {
    "photo": ("Сүрөт жарыяга туура келбейт. Оңдоп коюңуз.",
              "Фото не соответствует объявлению. Исправьте, пожалуйста."),
    "cat": ("Жарыя туура эмес бөлүмгө коюлган. Оңдоп коюңуз.",
            "Объявление в неверном разделе. Исправьте, пожалуйста."),
    "ban": ("Бул товарга тыюу салынган. Жарыя өчүрүлүшү мүмкүн.",
            "Этот товар запрещён. Объявление может быть удалено."),
    "phone": ("Байланыш номери туура эмес окшойт. Текшериңиз.",
              "Номер для связи указан неверно. Проверьте."),
    "text": ("Жарыянын аталышы же сүрөттөмөсү түшүнүксүз. Оңдоңуз.",
             "Заголовок или описание непонятны. Исправьте."),
}


def _token():
    t = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if t:
        return t
    try:
        return open(os.path.join(core.BASE, "token.txt"), encoding="utf-8").read().strip()
    except Exception:
        return ""


def _tg_send(chat, text):
    import json
    import urllib.request
    import urllib.parse
    tok = _token()
    if not tok:
        return False, "Токен табылган жок"
    data = urllib.parse.urlencode({
        "chat_id": chat, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": "true"}).encode()
    try:
        req = urllib.request.Request(
            "https://api.telegram.org/bot%s/sendMessage" % tok, data=data)
        with urllib.request.urlopen(req, timeout=25) as r:
            res = json.loads(r.read().decode())
        if res.get("ok"):
            return True, ""
        return False, str(res.get("description") or "ката")[:80]
    except Exception as e:
        return False, repr(e)[:80]


def _msg_form(uid, lid, back):
    r = core.query("SELECT * FROM listings WHERE id=?", (int(lid),), fetch="one")
    if not r:
        return "<p class='er'>Жарыя табылган жок.</p>"
    import bridge
    tid = str(_v(r, "tg_id") or "")
    title = str(bridge.show_title(r) or "-")
    opts = "".join("<option value='%s'>%s</option>" % (c, E(v[0]))
                   for c, v in WARN.items())
    if not tid.isdigit() or len(tid) > 10:
        return ("<div class='ad'><div class='ah'>№" + E(str(lid)) + " · " + E(title) +
                "</div><p class='am'>Бул колдонуучуга бот жаза албайт "
                "(Telegram эмес).</p><div class='ab'><a href='" + E(back) +
                "'>← Артка</a></div></div>")
    return ("<div class='ad'><div class='ah'>№" + E(str(lid)) + " · " + E(title) + "</div>"
            "<div class='am'>👤 " + E(str(_v(r, "tg_name") or "-")) + " · ID " + E(tid) + "</div>"
            "<form class='mf' method='post' action='/admin/msg'>"
            "<input type='hidden' name='id' value='" + E(str(lid)) + "'>"
            "<input type='hidden' name='k' value='" + _csrf(uid) + "'>"
            "<input type='hidden' name='back' value='" + E(back) + "'>"
            "<p>Даяр себеп:</p><select name='w'><option value=''>— тандаңыз —</option>" +
            opts + "</select>"
            "<p>Кошумча (каалаша):</p>"
            "<textarea name='t' rows='3' maxlength='400' "
            "placeholder='Өз сөзүңүз менен жазыңыз'></textarea>"
            "<button type='submit'>✉️ Жөнөтүү</button></form>"
            "<div class='ab'><a href='" + E(back) + "'>← Артка</a></div></div>")


def _msg_post(h, uid, q):
    lid, w = _q(q, "id"), _q(q, "w")
    note = re.sub(r"\s+", " ", _q(q, "t")).strip()[:400]
    back = _q(q, "back") or "/admin/ads"
    if not back.startswith("/admin"):
        back = "/admin/ads"
    if not lid.isdigit() or not hmac.compare_digest(_q(q, "k"), _csrf(uid)):
        h._send(_page("Ката", "<p class='er'>Жараксыз суроо.</p>"), 403)
        return
    r = core.query("SELECT * FROM listings WHERE id=?", (int(lid),), fetch="one")
    body = []
    if w in WARN:
        body.append(WARN[w][0])
    if note:
        body.append(note)
    if not r:
        msg = "Жарыя табылган жок"
    elif not body:
        msg = "Себеп же текст жазылган жок"
    else:
        import bridge
        tid = str(_v(r, "tg_id") or "")
        title = str(bridge.show_title(r) or "-")
        site = (os.environ.get("SITE_URL") or "").rstrip("/")
        link = ("\n🌐 %s/e/%s" % (site, lid)) if site and "localhost" not in site else ""
        txt = ("⚠️ <b>Администратордун эскертүүсү</b>\n\n"
               "Жарыя №%s: <b>%s</b>\n\n%s%s" %
               (lid, html.escape(title), html.escape("\n".join(body)), link))
        ok, err = _tg_send(tid, txt)
        msg = ("№%s: кабар жөнөтүлдү" % lid) if ok else ("Жөнөтүлгөн жок: " + err)
    sep = "&" if "?" in back else "?"
    h._go(back + sep + "m=" + quote(msg), None)


#BC1
BC = {"run": False, "done": 0, "fail": 0, "total": 0, "at": ""}


def _targets(who):
    out, seen = [], set()
    sql = ("SELECT DISTINCT tg_id FROM listings" if who == "ads"
           else "SELECT tg_id FROM users")
    for r in core.query(sql, fetch="all") or []:
        t = str(_v(r, "tg_id") or "").strip()
        if t.isdigit() and len(t) <= 10 and t not in seen:
            seen.add(t)
            out.append(t)
    try:
        ban = set(str(_g(x, "tid", 0)) for x in
                  (core.query("SELECT tid FROM bans", fetch="all") or []))
    except Exception:
        ban = set()
    return [t for t in out if t not in ban]


def _bc_run(ids, txt):
    BC.update(run=True, done=0, fail=0, total=len(ids), at=core.now_str()[:16])
    for t in ids:
        ok, _e = _tg_send(t, txt)
        if ok:
            BC["done"] += 1
        else:
            BC["fail"] += 1
        time.sleep(0.05)
    BC["run"] = False


def _bc_page(uid):
    n_all = len(_targets("all"))
    n_ads = len(_targets("ads"))
    st = ""
    if BC["run"]:
        st = ("<div class='ok'>Жөнөтүлүүдө: %d / %d · Жеткен жок: %d</div>"
              "<p class='cnt'><a href='/admin/bc'>🔄 Жаңыртуу</a></p>"
              % (BC["done"], BC["total"], BC["fail"]))
    elif BC["total"]:
        st = ("<div class='ok'>Акыркы жөнөтүү (%s): жетти %d, жеткен жок %d</div>"
              % (E(BC["at"]), BC["done"], BC["fail"]))
    return (st + "<form class='mf' method='post' action='/admin/bc'>"
            "<input type='hidden' name='k' value='" + _csrf(uid) + "'>"
            "<p>Кимге:</p><select name='w'>"
            "<option value='ads'>Жарыя койгондорго (%d)</option>"
            "<option value='all'>Бардык колдонуучуларга (%d)</option>"
            "</select>" % (n_ads, n_all) +
            "<p>Текст:</p>"
            "<textarea name='t' rows='6' maxlength='3000' "
            "placeholder='Кабардын тексти'></textarea>"
            "<button type='submit' name='a' value='test'>👤 Өзүмө сынап көрүү</button>"
            "<button type='submit' name='a' value='go'>📣 Баарына жөнөтүү</button>"
            "</form>")


def _bc_post(h, uid, q):
    if not hmac.compare_digest(_q(q, "k"), _csrf(uid)):
        h._send(_page("Ката", "<p class='er'>Жараксыз суроо.</p>"), 403)
        return
    txt = _q(q, "t").strip()[:3000]
    who = "all" if _q(q, "w") == "all" else "ads"
    if not txt:
        msg = "Текст жазылган жок"
    elif _q(q, "a") == "test":
        ok, err = _tg_send(uid, txt)
        msg = "Сынак кабар жөнөтүлдү" if ok else ("Ката: " + err)
    elif BC["run"]:
        msg = "Мурунку жөнөтүү бүтө элек"
    else:
        ids = _targets(who)
        if not ids:
            msg = "Кабар жөнөтүүчү адам жок"
        else:
            import threading
            threading.Thread(target=_bc_run, args=(ids, txt), daemon=True).start()
            msg = "Жөнөтүү башталды: %d адам" % len(ids)
    h._go("/admin/bc?m=" + quote(msg), None)


def is_banned(tid):
    """Бот жана WhatsApp чакырат. Ката болсо False кайтарат."""
    tid = str(tid or "").strip()
    if not tid:
        return False
    hit = _BANC.get(tid)
    if hit and hit[1] > time.time():
        return hit[0]
    try:
        _cols()
        val = bool(core.query("SELECT tid FROM bans WHERE tid=?", (tid,), fetch="one"))
    except Exception as e:
        print("ban check:", e, flush=True)
        val = False
    _BANC[tid] = (val, time.time() + 30)
    return val


def _ban(tid):
    core.query("DELETE FROM bans WHERE tid=?", (tid,))
    core.query("INSERT INTO bans (tid, reason, created_at) VALUES (?,?,?)",
               (tid, "admin", core.now_str()))
    core.query("UPDATE listings SET is_active=0 WHERE tg_id=?", (tid,))
    _BANC.pop(tid, None)


def _unban(tid):
    core.query("DELETE FROM bans WHERE tid=?", (tid,))
    _BANC.pop(tid, None)


def _bonus(tid, n=1):
    core.query("UPDATE users SET bonus_posts=COALESCE(bonus_posts,0)+? WHERE tg_id=?",
               (n, tid))


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


def _v(r, k):
    try:
        return r[k]
    except Exception:
        return None


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
    "nav a{white-space:nowrap;padding:7px 12px;border-radius:99px;font-size:14px;"
    "background:#fff;color:#17365C;border:1.5px solid #9AA8BF;text-decoration:none}"
    "nav a.on{background:#17365C;color:#fff;border-color:#17365C}"
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
    ".fw{font-size:13px;color:#854F0B;background:#FAEEDA;border-radius:8px;"
    "padding:6px 8px;margin-top:6px}"
    ".b{display:inline-block;font-size:12px;padding:2px 8px;border-radius:99px;margin-left:4px}"
    ".b.ac{background:#E6F4EC;color:#1F5E3C}.b.ex{background:#F1F4F9;color:#5A6982}"
    ".b.w{background:#FAEEDA;color:#854F0B}.b.bn{background:#FCEBEB;color:#A32D2D}"
    ".ab{display:flex;gap:8px;margin-top:10px}"
    ".ab a{flex:1;text-align:center;padding:8px 6px;border-radius:10px;font-size:14px;"
    "text-decoration:none;border:1.5px solid #9AA8BF;color:#17365C}"
    ".ab a.del{border-color:#E24B4A;color:#A32D2D}"
    ".ab a.okb{border-color:#1F7A4D;color:#1F5E3C}"
    ".pg{display:flex;justify-content:space-between;margin:12px 0}"
    ".pg a{color:#17365C;font-weight:600;text-decoration:none}.mf{margin-top:10px}.mf p{font-size:13px;color:#33425A;margin:8px 0 4px}.mf select,.mf textarea{width:100%;box-sizing:border-box;font-size:15px;font-family:inherit;border:1.5px solid #9AA8BF;border-radius:10px;padding:9px 10px;background:#fff;color:#152741}.mf button{width:100%;margin-top:10px;border:0;border-radius:10px;padding:11px;background:#17365C;color:#fff;font-size:15px;font-weight:600}"
)


def _page(title, body, tab="", msg=""):
    tabs = ""
    for href, key, name in (("/admin", "st", "Статистика"),
                            ("/admin/ads", "ads", "Жарыялар"),
                            ("/admin/mod", "mod", "Модерация"),
                            ("/admin/users", "us", "Колдонуучулар"),
                            ("/admin/bc", "bc", "Билдирүү")):
        tabs += "<a href='%s'%s>%s</a>" % (href, " class='on'" if tab == key else "", name)
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
        ("Активдүү", _n("SELECT COUNT(*) AS n FROM listings WHERE " + ACT, (now,))),
        ("Бүгүн коюлду", _n("SELECT COUNT(*) AS n FROM listings WHERE created_at LIKE ?", (day,))),
        ("Мөөнөтү бүткөн", _n("SELECT COUNT(*) AS n FROM listings WHERE NOT (" + ACT + ")", (now,))),
        ("⚠️ Шектүү", _n("SELECT COUNT(*) AS n FROM listings WHERE " + FLG)),
        ("Жалпы көрүү", _n("SELECT COALESCE(SUM(views),0) AS n FROM listings")),
        ("Колдонуучулар", _n("SELECT COUNT(*) AS n FROM users")),
        ("Бүгүн кошулду", _n("SELECT COUNT(*) AS n FROM users WHERE created_at LIKE ?", (day,))),
        ("⛔ Бандалган", _n("SELECT COUNT(*) AS n FROM bans")),
    ]
    body = "<div class='g'>" + "".join(
        "<div class='k'><small>" + E(a) + "</small><b>" + str(b) + "</b></div>"
        for a, b in tiles) + "</div>"
    try:
        rows = core.query(
            "SELECT category, COUNT(*) AS n FROM listings WHERE " + ACT +
            " GROUP BY category ORDER BY n DESC", (now,), fetch="all") or []
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
    core.query("UPDATE listings SET expires_at=?, is_active=1, warned='' WHERE id=?",
               (_fmt(new), lid))
    return True


def _do(h, uid, q):
    a, tid = _q(q, "a"), _q(q, "id")
    back = _q(q, "back") or "/admin/ads"
    if not back.startswith("/admin"):
        back = "/admin/ads"
    if not tid.isdigit() or not hmac.compare_digest(_q(q, "k"), _csrf(uid)):
        h._send(_page("Ката", "<p class='er'>Жараксыз суроо.</p>"), 403)
        return
    if a == "del":
        _delete(int(tid))
        msg = "№%s өчүрүлдү" % tid
    elif a == "ext":
        msg = ("№%s: +7 күн узартылды" % tid) if _extend(int(tid)) else "Жарыя табылган жок"
    elif a == "ok":
        core.query("UPDATE listings SET flagged='' WHERE id=?", (int(tid),))
        msg = "№%s калтырылды" % tid
    elif a == "ban":
        if tid in _ids():
            msg = "Админди бандоого болбойт"
        else:
            _ban(tid)
            msg = "%s бандалды, жарыялары жашырылды" % tid
    elif a == "unban":
        _unban(tid)
        msg = "%s бандан чыгарылды" % tid
    elif a == "bon":
        _bonus(tid, 1)
        msg = "%s: +1 бонус кошулду" % tid
    else:
        msg = "Белгисиз аракет"
    sep = "&" if "?" in back else "?"
    h._go(back + sep + "m=" + quote(msg), None)


def _card(r, k, back, now, mod=False):
    import bridge
    lid = r.get("id")
    title = bridge.show_title(r) or "-"
    cat = str(bridge.cat_label(r.get("cat_id")) or _sec_name(r.get("category")))
    cat = cat.split(" / ")[0]
    exp = str(r.get("expires_at") or "")
    live = exp > now and str(r.get("is_active")) != "0"
    st = ("<span class='b ac'>Активдүү</span>" if live
          else "<span class='b ex'>Бүткөн</span>")
    fl = str(r.get("flagged") or "")
    wn = "<span class='b w'>⚠️</span>" if fl else ""
    why = ""
    if fl and mod:
        why = "<div class='fw'>⚠️ " + E(fl if fl != "1" else "Шектүү сөз") + "</div>"

    def act(a):
        return E("/admin/do?" + urlencode({"a": a, "id": lid, "k": k, "back": back}))
    btn = "<a href='/e/" + str(lid) + "' target='_blank'>Карап көрүү</a>"
    btn += "<a href='" + E("/admin/msg?" + urlencode({"id": lid, "back": back})) + "'>✉️ Жазуу</a>"  #MSG1
    if mod:
        btn += "<a class='okb' href='" + act("ok") + "'>✅ Калтыр</a>"
    else:
        btn += "<a href='" + act("ext") + "'>+7 күн</a>"
    btn += ("<a class='del' href='" + act("del") + "' onclick=\"return confirm('№" +
            str(lid) + " өчүрүлсүнбү?')\">Өчүрүү</a>")
    return (
        "<div class='ad'><div class='ah'>№" + str(lid) + " · " + E(str(title)) +
        st + wn + "</div>"
        "<div class='am'>" + E(str(r.get("price") or "-")) + " · " + E(cat) +
        " · 👁 " + str(r.get("views") or 0) + "</div>"
        "<div class='am'>Коюлду: " + E(str(r.get("created_at") or "")[:16]) +
        " · Бүтөт: " + E(exp[:10]) + "</div>"
        "<div class='am'>👤 " + E(str(r.get("tg_name") or "-")) + " · 📞 " +
        E(str(r.get("contact") or "-")) + "</div>" + why +
        "<div class='ab'>" + btn + "</div></div>")


def _ads(uid, q):
    s = _q(q, "q").strip()[:60]
    f = _q(q, "f") or "all"
    pg = _q(q, "p")
    pg = int(pg) if pg.isdigit() and int(pg) > 0 else 1
    now = core.now_str()
    where, par = [], []
    if f == "act":
        where.append(ACT)
        par.append(now)
    elif f == "exp":
        where.append("NOT (" + ACT + ")")
        par.append(now)
    elif f == "warn":
        where.append(FLG)
    if s:
        if s.isdigit():
            where.append("(id=? OR contact LIKE ? OR tg_id=?)")
            par += [int(s), "%" + s + "%", s]
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
    body += "".join(_card(r, k, back, now) for r in rows)
    if not rows:
        body += "<p class='cnt'>Жарыя жок.</p>"
    nav = "<a href='" + E(link(p=pg - 1)) + "'>← Мурунку</a>" if pg > 1 else "<span></span>"
    if isinstance(total, int) and pg * PER < total:
        nav += "<a href='" + E(link(p=pg + 1)) + "'>Кийинки →</a>"
    return body + "<div class='pg'>" + nav + "</div>"


def _mod(uid):
    now = core.now_str()
    rows = core.query("SELECT * FROM listings WHERE " + FLG +
                      " ORDER BY id DESC LIMIT 100", fetch="all") or []
    k = _csrf(uid)
    body = "<p class='cnt'>Шектүү сөз менен коюлган жарыялар: " + str(len(rows)) + "</p>"
    if not rows:
        body += "<p class='ok'>Азырынча шектүү жарыя жок.</p>"
    return body + "".join(_card(r, k, "/admin/mod", now, True) for r in rows)


def _users(uid, q):
    s = _q(q, "q").strip()[:40].lower()
    f = _q(q, "f") or "all"
    pg = _q(q, "p")
    pg = int(pg) if pg.isdigit() and int(pg) > 0 else 1
    bans = set(str(_g(r, "tid", 0)) for r in
               (core.query("SELECT tid FROM bans", fetch="all") or []))
    people = {}

    def get(t):
        return people.setdefault(t, {"tid": t, "nm": "", "n": 0, "last": "",
                                     "joined": "", "bonus": None, "refs": 0})
    for r in core.query("SELECT * FROM users", fetch="all") or []:
        t = str(_v(r, "tg_id") or "")
        if not t:
            continue
        p = get(t)
        p["joined"] = str(_v(r, "created_at") or "")
        p["last"] = p["joined"]
        p["bonus"] = _v(r, "bonus_posts") or 0
        p["refs"] = _v(r, "ref_count") or 0
    for r in core.query("SELECT tg_id, MAX(tg_name) AS nm, COUNT(*) AS n, "
                        "MAX(created_at) AS last FROM listings GROUP BY tg_id",
                        fetch="all") or []:
        t = str(_v(r, "tg_id") or "")
        if not t:
            continue
        p = get(t)
        p["nm"] = str(_v(r, "nm") or "")
        p["n"] = int(_v(r, "n") or 0)
        p["last"] = max(p["last"], str(_v(r, "last") or ""))
    lst = list(people.values())
    if f == "ban":
        lst = [p for p in lst if p["tid"] in bans]
    if s:
        lst = [p for p in lst if s in p["tid"] or s in p["nm"].lower()]
    lst.sort(key=lambda p: p["last"], reverse=True)
    total = len(lst)
    rows = lst[(pg - 1) * PER: pg * PER]

    def link(**kw):
        d = {"q": s, "f": f, "p": pg}
        d.update(kw)
        return "/admin/users?" + urlencode({k: v for k, v in d.items() if v})

    back = link()
    k = _csrf(uid)
    admins = _ids()
    body = ("<form class='sf' method='get' action='/admin/users'>"
            "<input name='q' value='" + E(s) + "' placeholder='ID же аты'>"
            "<input type='hidden' name='f' value='" + E(f) + "'>"
            "<button>Изде</button></form><div class='fl'>")
    for key, name in (("all", "Баары"), ("ban", "⛔ Бандалгандар")):
        body += "<a href='%s'%s>%s</a>" % (E(link(f=key, p=1)),
                                           " class='on'" if f == key else "", name)
    body += "</div><p class='cnt'>Табылды: " + str(total) + "</p>"
    for p in rows:
        t = p["tid"]
        banned = t in bans

        def act(a):
            return E("/admin/do?" + urlencode({"a": a, "id": t, "k": k, "back": back}))
        kind = "WhatsApp" if len(t) >= 11 else "Telegram"
        tag = "<span class='b bn'>⛔ Бандалган</span>" if banned else ""
        if t in admins:
            tag += "<span class='b ac'>Админ</span>"
        btn = "<a href='" + E("/admin/ads?" + urlencode({"q": t})) + "'>Жарыялары</a>"
        if p["bonus"] is not None:
            btn += "<a class='okb' href='" + act("bon") + "'>+1 бонус</a>"
        if banned:
            btn += "<a class='okb' href='" + act("unban") + "'>Бандан чыгаруу</a>"
        elif t not in admins:
            btn += ("<a class='del' href='" + act("ban") + "' onclick=\"return confirm('" +
                    t + " бандалсынбы? Жарыялары жашырылат.')\">Бан</a>")
        bonus = "-" if p["bonus"] is None else str(p["bonus"])
        body += (
            "<div class='ad'><div class='ah'>👤 " + E(p["nm"] or "-") + tag + "</div>"
            "<div class='am'>" + kind + " · ID " + E(t) + "</div>"
            "<div class='am'>Жарыя: " + str(p["n"]) + " · Бонус: " + bonus +
            " · Чакырган: " + str(p["refs"]) + "</div>"
            "<div class='am'>Кошулду: " + E(p["joined"][:10] or "-") +
            " · Акыркы: " + E(p["last"][:10] or "-") + "</div>"
            "<div class='ab'>" + btn + "</div></div>")
    if not rows:
        body += "<p class='cnt'>Колдонуучу жок.</p>"
    nav = "<a href='" + E(link(p=pg - 1)) + "'>← Мурунку</a>" if pg > 1 else "<span></span>"
    if pg * PER < total:
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
    _cols()
    msg = _q(q, "m")
    if p == "/admin/do":
        _do(h, uid, q)
    elif p == "/admin/ads":
        h._send(_page("Жарыялар", _ads(uid, q), "ads", msg))
    elif p == "/admin/mod":
        h._send(_page("Модерация", _mod(uid), "mod", msg))
    elif p == "/admin/msg":
        if getattr(h, "command", "GET") == "POST":
            try:
                n = int(h.headers.get("Content-Length") or 0)
                d = parse_qs(h.rfile.read(n).decode("utf-8")) if 0 < n < 6000 else {}
            except Exception:
                d = {}
            _msg_post(h, uid, d)
        else:
            bk = _q(q, "back") or "/admin/ads"
            bk = bk if bk.startswith("/admin") else "/admin/ads"
            h._send(_page("Колдонуучуга жазуу", _msg_form(uid, _q(q, "id") or "0", bk),
                          "ads", msg))
    elif p == "/admin/bc":
        if getattr(h, "command", "GET") == "POST":
            try:
                n = int(h.headers.get("Content-Length") or 0)
                d = parse_qs(h.rfile.read(n).decode("utf-8")) if 0 < n < 9000 else {}
            except Exception:
                d = {}
            _bc_post(h, uid, d)
        else:
            h._send(_page("Жапырт билдирүү", _bc_page(uid), "bc", msg))
    elif p == "/admin/users":
        h._send(_page("Колдонуучулар", _users(uid, q), "us", msg))
    else:
        h._send(_page("Статистика", _stats(), "st", msg))


def handle(h, u):
    try:
        _route(h, u)
    except Exception as e:
        h._send(_page("Ката", "<p class='er'>" + E(repr(e)) + "</p>"), 500)
