"""
ТАП! — жарнама баннерлери (BANADM).

Баннерлер базада сакталат (сүрөтү да — Railway'дин диски туруктуу эмес).
Админ /admin/banners бетинен кошот, өзгөртөт, өчүрүп-күйгүзөт.
Сайттагы үч орун:
  home — башкы беттеги бөлүмдөрдүн ортосу
  top  — бөлүм ачылганда эң үстүндө
  grid — жарыялардын арасында (ар 6 жарыядан кийин)
  all  — үчөөндө тең
Орунга ылайык баннер жок болсо, ТАП!'тын өз баннери (secimg) чыгат.
"""
import base64
import hmac
import html
import json
import random
import threading
import time
from datetime import datetime, timedelta
from urllib.parse import quote

import core

E = html.escape

PLACES = [("all", "Бардык орундар"), ("home", "Башкы бет (бөлүмдөрдүн ортосу)"),
          ("top", "Бөлүмдүн эң үстү"), ("grid", "Жарыялардын арасы")]
SECTIONS = [("trade", "Соода-сатык"), ("wholesale", "Соода-сатык (дүң)"),
            ("property", "Мүлк сатуу"), ("vehicle", "Унаа сатуу"),
            ("service", "Кызмат көрсөтүү"), ("rental", "Ижарага берүү"),
            ("delivery", "Жеткирүү"), ("cargo", "Жүк ташуу"),
            ("jobseek", "Жумуш издөө"), ("job", "Жумуш берүү"),
            ("markets", "Базарлар"), ("malls", "Соода борборлору"), ("taxi", "Такси")]

_READY = [False]
_CACHE = {"at": 0.0, "rows": []}
_IMG = {}
_SHOWS = {}
_FLUSH = {"at": time.time()}
_LOCK = threading.Lock()


# ── База ─────────────────────────────────────────────────────

def _ensure():
    if _READY[0]:
        return
    idc = "id SERIAL PRIMARY KEY" if getattr(core, "IS_PG", False) \
        else "id INTEGER PRIMARY KEY AUTOINCREMENT"
    core.query("CREATE TABLE IF NOT EXISTS banners (" + idc + ", "
               "img TEXT, place TEXT, section TEXT, oblast TEXT, link TEXT, "
               "title TEXT, owner TEXT, starts TEXT, ends TEXT, "
               "active INTEGER DEFAULT 1, shows INTEGER DEFAULT 0, "
               "clicks INTEGER DEFAULT 0, updated TEXT, created_at TEXT)")
    _READY[0] = True


def _today():
    """Бишкектеги бүгүнкү күн (UTC+6)."""
    return (datetime.utcnow() + timedelta(hours=6)).strftime("%Y-%m-%d")


def _reset():
    _CACHE["at"] = 0.0
    _IMG.clear()


def _active():
    """Азыр чыгышы керек болгон баннерлер (30 секунд кэште)."""
    if time.time() - _CACHE["at"] < 30:
        return _CACHE["rows"]
    try:
        _ensure()
        rows = core.query("SELECT id, place, section, oblast, link, starts, ends, updated "
                          "FROM banners WHERE COALESCE(active,1)=1", fetch="all") or []
        d = _today()
        rows = [r for r in rows
                if (not r.get("starts") or r["starts"] <= d)
                and (not r.get("ends") or r["ends"] >= d)]
    except Exception as e:
        print("banners:", e, flush=True)
        rows = []
    _CACHE.update(at=time.time(), rows=rows)
    return rows


def _flush():
    with _LOCK:
        items = list(_SHOWS.items())
        _SHOWS.clear()
        _FLUSH["at"] = time.time()
    for bid, n in items:
        try:
            core.query("UPDATE banners SET shows=COALESCE(shows,0)+? WHERE id=?", (n, bid))
        except Exception:
            pass


def _count(bid):
    with _LOCK:
        _SHOWS[bid] = _SHOWS.get(bid, 0) + 1
        due = time.time() - _FLUSH["at"] > 60
        if due:
            _FLUSH["at"] = time.time()
    if due:
        threading.Thread(target=_flush, daemon=True).start()


# ── Сайт ─────────────────────────────────────────────────────

def slot(place, at=None, ob=None, k=0, lang="ky", cls="hban"):
    """Орунга ылайык сатылган баннердин HTML'и. Жок болсо бош сап."""
    try:
        sec, obl = at or "", ob or ""
        c = [b for b in _active()
             if (b.get("place") or "all") in (place, "all")
             and (b.get("section") or "") in ("", sec)
             and (b.get("oblast") or "") in ("", obl)]
        if not c:
            return ""
        c.sort(key=lambda b: b["id"])
        b = c[(k + random.randrange(len(c))) % len(c)]
        _count(b["id"])
        lbl = "Реклама" if lang == "ru" else "Жарнама"
        img = ('<img src="/bimg/%d.jpg?v=%s" alt="%s" loading="lazy">'
               % (b["id"], E(str(b.get("updated") or "0")[-8:].replace(":", "")), lbl))
        inner = img + '<span class="adl">%s</span>' % lbl
        if b.get("link"):
            return ('<a class="%s pb" href="/bn/%d" target="_blank" rel="nofollow sponsored noopener">%s</a>'
                    % (cls, b["id"], inner))
        return '<div class="%s pb">%s</div>' % (cls, inner)
    except Exception as e:
        print("banners slot:", e, flush=True)
        return ""


def _404(h):
    h.send_response(404)
    h.send_header("Content-Length", "0")
    h.end_headers()


def serve_img(h, u):
    """/bimg/<id>.jpg"""
    try:
        bid = int(u.path[6:].split(".")[0])
        data = _IMG.get(bid)
        if data is None:
            _ensure()
            r = core.query("SELECT img FROM banners WHERE id=?", (bid,), fetch="one")
            data = base64.b64decode(r["img"]) if r and r.get("img") else b""
            if len(_IMG) > 50:
                _IMG.clear()
            _IMG[bid] = data
        if not data:
            return _404(h)
        h.send_response(200)
        h.send_header("Content-Type", "image/jpeg")
        h.send_header("Content-Length", str(len(data)))
        h.send_header("Cache-Control", "max-age=86400")
        h.end_headers()
        h.wfile.write(data)
    except Exception:
        _404(h)


def _safe_link(s):
    s = str(s or "").strip()
    if s.startswith(("https://", "http://", "tel:", "/")) and not s.startswith("//"):
        return s
    return ""


def click(h, u):
    """/bn/<id> — басууну эсептеп, шилтемеге жөнөтөт."""
    try:
        bid = int(u.path[4:].strip("/"))
        _ensure()
        r = core.query("SELECT link FROM banners WHERE id=?", (bid,), fetch="one")
        url = _safe_link(r.get("link")) if r else ""
        if not url:
            return h._go("/", None)
        core.query("UPDATE banners SET clicks=COALESCE(clicks,0)+1 WHERE id=?", (bid,))
        h._go(url, None)
    except Exception:
        h._go("/", None)


# ── Админ ────────────────────────────────────────────────────

_CSS = (
    "<style>.bn{background:#fff;border:1.5px solid #9AA8BF;border-radius:14px;"
    "padding:10px;margin-bottom:12px}.bn img{width:100%;max-width:220px;aspect-ratio:1/1;object-fit:cover;border-radius:10px;display:block}"
    ".bn .am{margin-top:6px}.bf label{display:block;font-size:13px;color:#33425A;"
    "margin:10px 0 4px}.bf input,.bf select{width:100%;box-sizing:border-box;font-size:15px;"
    "border:1.5px solid #9AA8BF;border-radius:10px;padding:9px 10px;background:#fff}"
    ".bf .row{display:flex;gap:8px}.bf .row>div{flex:1}.bf button{width:100%;margin-top:14px;"
    "border:0;border-radius:10px;padding:12px;background:#17365C;color:#fff;font-size:16px;"
    "font-weight:700}#bprev{width:100%;max-width:220px;border-radius:10px;margin-top:8px;display:none}"
    ".bf .hint{font-size:12px;color:#5A6982;margin-top:4px}</style>")


def _opts(items, cur):
    return "".join('<option value="%s"%s>%s</option>'
                   % (E(v), " selected" if v == (cur or "") else "", E(n)) for v, n in items)


def _oblasts():
    try:
        import tap_catalog
        return [(x, x) for x in tap_catalog.OBLASTS]
    except Exception:
        return []


def _name(items, v, empty):
    return dict(items).get(v or "", empty) if v else empty


def _form(b, k):
    b = b or {}
    bid = b.get("id") or ""
    return _CSS + (
        '<div class="bf ad"><div class="ah">%s</div>'
        '<label>Сүрөт (жарыянын сүрөтүндөй чарчы)</label>'   # BANSZ
        '<input type="file" id="bfile" accept="image/*">'
        '<div class="hint">%s</div><img id="bprev">'
        '<label>Аталышы (өзүңүз үчүн)</label><input id="btitle" value="%s" placeholder="Мис: Береке дүкөнү">'
        '<label>Ээсинин байланышы</label><input id="bowner" value="%s" placeholder="Мис: 0700 123 456, Азамат">'
        '<label>Шилтеме (басканда ачылат)</label><input id="blink" value="%s" '
        'placeholder="https://wa.me/996700123456 же https://... же tel:+996...">'
        '<label>Орду</label><select id="bplace">%s</select>'
        '<label>Бөлүм</label><select id="bsec"><option value="">Бардык бөлүмдөр</option>%s</select>'
        '<label>Аймак</label><select id="bobl"><option value="">Бүт Кыргызстан</option>%s</select>'
        '<div class="row"><div><label>Башталышы</label><input type="date" id="bstart" value="%s"></div>'
        '<div><label>Бүтүшү</label><input type="date" id="bend" value="%s"></div></div>'
        '<button type="button" id="bsave">%s</button></div>'
        '<script>(function(){var IMG="",f=document.getElementById("bfile"),pv=document.getElementById("bprev");'
        'f.onchange=function(){var x=f.files[0];if(!x)return;var r=new FileReader();r.onload=function(){'
        'var im=new Image();im.onload=function(){var s=Math.min(im.width,im.height),w=Math.min(800,s),hh=w;'
        'var c=document.createElement("canvas");c.width=w;c.height=hh;var g=c.getContext("2d");'
        'g.fillStyle="#fff";g.fillRect(0,0,w,hh);g.drawImage(im,(im.width-s)/2,(im.height-s)/2,s,s,0,0,w,hh);'
        'IMG=c.toDataURL("image/jpeg",0.85);pv.src=IMG;pv.style.display="block";};im.src=r.result;};r.readAsDataURL(x);};'
        'function v(i){return document.getElementById(i).value;}'
        'document.getElementById("bsave").onclick=function(){var t=this;'
        'if(!IMG&&!%s){alert("Сүрөт тандаңыз");return;}t.disabled=true;t.textContent="Сакталууда…";'
        'fetch("/admin/banners/save",{method:"POST",headers:{"Content-Type":"application/json"},'
        'body:JSON.stringify({k:"%s",id:"%s",img:IMG,title:v("btitle"),owner:v("bowner"),link:v("blink"),'
        'place:v("bplace"),section:v("bsec"),oblast:v("bobl"),starts:v("bstart"),ends:v("bend")})})'
        '.then(function(r){return r.json();}).then(function(j){if(j.ok){location.href="/admin/banners?m="+encodeURIComponent(j.msg);}'
        'else{alert(j.msg||"Ката");t.disabled=false;t.textContent="Сактоо";}})'
        '.catch(function(){alert("Байланыш катасы");t.disabled=false;t.textContent="Сактоо";});};})();</script>'
    ) % ("№%s баннерди өзгөртүү" % bid if bid else "Жаңы баннер",
         "Жаңы сүрөт тандабасаңыз, эскиси калат." if bid else "Сүрөт ортосунан чарчы болуп кесилет (800×800).",
         E(b.get("title") or ""), E(b.get("owner") or ""), E(b.get("link") or ""),
         _opts(PLACES, b.get("place") or "all"), _opts(SECTIONS, b.get("section")),
         _opts(_oblasts(), b.get("oblast")),
         E(b.get("starts") or _today()), E(b.get("ends") or ""),
         "Сактоо" if bid else "Кошуу", "true" if bid else "false", k, bid)


def _list(k):
    rows = core.query("SELECT id, place, section, oblast, link, title, owner, starts, ends, "
                      "active, shows, clicks, updated FROM banners ORDER BY id DESC",
                      fetch="all") or []
    if not rows:
        return "<p class='cnt'>Азырынча баннер жок. Бош орундарда ТАП!'тын өз баннерлери чыгат.</p>"
    d = _today()
    out = "<h2>Баннерлер (%d)</h2>" % len(rows)
    for b in rows:
        on = int(b.get("active") or 0) == 1
        if not on:
            st = "<span class='b ex'>Өчүк</span>"
        elif b.get("ends") and b["ends"] < d:
            st = "<span class='b bn'>Мөөнөтү бүттү</span>"
        elif b.get("starts") and b["starts"] > d:
            st = "<span class='b w'>Күтүүдө</span>"
        else:
            st = "<span class='b ac'>Иштеп жатат</span>"
        sh, cl = int(b.get("shows") or 0), int(b.get("clicks") or 0)
        ctr = ("%.1f%%" % (cl * 100.0 / sh)) if sh else "—"
        v = str(b.get("updated") or "0")[-8:].replace(":", "")
        a = "/admin/banners/act?k=%s&id=%d&a=" % (k, b["id"])
        out += (
            "<div class='bn'><img src='/bimg/%d.jpg?v=%s' alt=''>"
            "<div class='ah' style='margin-top:8px'>№%d %s %s</div>"
            "<div class='am'>📍 %s · %s · %s</div>"
            "<div class='am'>📅 %s → %s</div>"
            "<div class='am'>👁 %d көрсөтүү · 👆 %d басуу · %s</div>"
            "%s%s"
            "<div class='ab'><a href='%s'>%s</a><a href='/admin/banners?edit=%d'>Өзгөртүү</a>"
            "<a class='del' href='%sdel' onclick=\"return confirm('№%d өчүрүлсүнбү?')\">Өчүрүү</a></div></div>"
        ) % (b["id"], E(v), b["id"], E(b.get("title") or ""), st,
             E(_name(PLACES, b.get("place"), "Бардык орундар")),
             E(_name(SECTIONS, b.get("section"), "Бардык бөлүмдөр")),
             E(b.get("oblast") or "Бүт Кыргызстан"),
             E(b.get("starts") or "—"), E(b.get("ends") or "чексиз"), sh, cl, ctr,
             ("<div class='am'>👤 %s</div>" % E(b["owner"])) if b.get("owner") else "",
             ("<div class='am'>🔗 %s</div>" % E(b["link"])) if b.get("link") else "",
             a + ("off" if on else "on"), "Өчүрүү ⏸" if on else "Күйгүзүү ▶",
             b["id"], a, b["id"])
    return out


def _json(h, d, code=200):
    data = json.dumps(d, ensure_ascii=False).encode("utf-8")
    h.send_response(code)
    h.send_header("Content-Type", "application/json; charset=utf-8")
    h.send_header("Content-Length", str(len(data)))
    h.end_headers()
    h.wfile.write(data)


def _date(s):
    s = str(s or "").strip()[:10]
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return s
    except Exception:
        return ""


def _save(h, uid, k):
    try:
        n = int(h.headers.get("Content-Length") or 0)
        if not 0 < n < 6_000_000:
            return _json(h, {"ok": False, "msg": "Сүрөт өтө чоң"})
        d = json.loads(h.rfile.read(n).decode("utf-8"))
    except Exception:
        return _json(h, {"ok": False, "msg": "Жараксыз суроо"})
    if not hmac.compare_digest(str(d.get("k") or ""), k):
        return _json(h, {"ok": False, "msg": "Сессия бүттү, кайра кириңиз"})
    img = str(d.get("img") or "")
    if img:
        if not img.startswith("data:image/jpeg;base64,"):
            return _json(h, {"ok": False, "msg": "Сүрөт JPEG болушу керек"})
        img = img.split(",", 1)[1]
        try:
            if base64.b64decode(img)[:2] != b"\xff\xd8":
                raise ValueError
        except Exception:
            return _json(h, {"ok": False, "msg": "Сүрөт бузук"})
    place = d.get("place") if d.get("place") in dict(PLACES) else "all"
    sec = d.get("section") if d.get("section") in dict(SECTIONS) else ""
    obl = str(d.get("oblast") or "")[:60]
    link = str(d.get("link") or "").strip()[:500]
    if link and not _safe_link(link):
        return _json(h, {"ok": False, "msg": "Шилтеме https://, tel: же / менен башталсын"})
    f = (place, sec, obl, link, str(d.get("title") or "")[:120],
         str(d.get("owner") or "")[:200], _date(d.get("starts")), _date(d.get("ends")),
         core.now_str())
    bid = str(d.get("id") or "")
    if bid.isdigit():
        core.query("UPDATE banners SET place=?, section=?, oblast=?, link=?, title=?, owner=?, "
                   "starts=?, ends=?, updated=? WHERE id=?", f + (int(bid),))
        if img:
            core.query("UPDATE banners SET img=? WHERE id=?", (img, int(bid)))
        msg = "№%s сакталды" % bid
    else:
        if not img:
            return _json(h, {"ok": False, "msg": "Сүрөт тандаңыз"})
        new = core.query("INSERT INTO banners (place, section, oblast, link, title, owner, "
                         "starts, ends, updated, img, active, shows, clicks, created_at) "
                         "VALUES (?,?,?,?,?,?,?,?,?,?,1,0,0,?)",
                         f + (img, core.now_str()), fetch="id")
        bid, msg = new, "№%s кошулду" % new
    _reset()
    try:
        core.log_event("adm:banner", int(bid), uid, "admin", note=msg)
    except Exception:
        pass
    _json(h, {"ok": True, "msg": msg})


def _act(h, uid, q, k):
    g = lambda x: (q.get(x) or [""])[0]
    a, bid = g("a"), g("id")
    if not bid.isdigit() or not hmac.compare_digest(g("k"), k):
        return h._go("/admin/banners?m=" + quote("Жараксыз суроо"), None)
    if a == "del":
        core.query("DELETE FROM banners WHERE id=?", (int(bid),))
        msg = "№%s өчүрүлдү" % bid
    elif a in ("on", "off"):
        core.query("UPDATE banners SET active=?, updated=? WHERE id=?",
                   (1 if a == "on" else 0, core.now_str(), int(bid)))
        msg = "№%s %s" % (bid, "күйгүзүлдү" if a == "on" else "өчүрүлдү")
    else:
        msg = "Белгисиз аракет"
    _reset()
    try:
        core.log_event("adm:banner", int(bid), uid, "admin", note=msg)
    except Exception:
        pass
    h._go("/admin/banners?m=" + quote(msg), None)


def admin(h, uid, q, p, msg, page, k):
    """admin.py'ден чакырылат: /admin/banners..."""
    _ensure()
    if p == "/admin/banners/save" and getattr(h, "command", "GET") == "POST":
        return _save(h, uid, k)
    if p == "/admin/banners/act":
        return _act(h, uid, q, k)
    ed = (q.get("edit") or [""])[0]
    b = None
    if ed.isdigit():
        b = core.query("SELECT id, place, section, oblast, link, title, owner, starts, ends "
                       "FROM banners WHERE id=?", (int(ed),), fetch="one")
    body = _form(b, k) + _list(k)
    h._send(page("Баннерлер", body, "bn", msg))
