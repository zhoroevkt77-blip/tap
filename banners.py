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
    _cfg_ensure()   # BANSELL
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
        if b.get("link"):   # ADLINKS: сайттын ичиндеги шилтеме ошол эле өтмөктө
            tgt = ("" if str(b.get("link")).startswith("/")
                   else ' target="_blank" rel="nofollow sponsored noopener"')
            return ('<a class="%s pb" href="/bn/%d"%s>%s</a>' % (cls, b["id"], tgt, inner))
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
    "padding:10px;margin-bottom:12px}.bn img{width:100%;aspect-ratio:2/1;object-fit:cover;border-radius:10px;display:block}"
    ".bn .am{margin-top:6px}.bf label{display:block;font-size:13px;color:#33425A;"
    "margin:10px 0 4px}.bf input,.bf select{width:100%;box-sizing:border-box;font-size:15px;"
    "border:1.5px solid #9AA8BF;border-radius:10px;padding:9px 10px;background:#fff}"
    ".bf .row{display:flex;gap:8px}.bf .row>div{flex:1}.bf button{width:100%;margin-top:14px;"
    "border:0;border-radius:10px;padding:12px;background:#17365C;color:#fff;font-size:16px;"
    "font-weight:700}#bprev{width:100%;aspect-ratio:2/1;object-fit:cover;border-radius:10px;margin-top:8px;display:none}"
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
        '<label>Сүрөт (туурасына 2:1, мис. 1200×600)</label>'   # BANFW
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
        'var im=new Image();im.onload=function(){var sw=Math.min(im.width,im.height*2),sh=sw/2,w=Math.min(1200,Math.round(sw)),hh=Math.round(w/2);'
        'var c=document.createElement("canvas");c.width=w;c.height=hh;var g=c.getContext("2d");'
        'g.fillStyle="#fff";g.fillRect(0,0,w,hh);g.drawImage(im,(im.width-sw)/2,(im.height-sh)/2,sw,sh,0,0,w,hh);'
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
         "Жаңы сүрөт тандабасаңыз, эскиси калат." if bid else "Сүрөт ортосунан 2:1 болуп кесилет (1200×600). Кара чет жок сүрөт тандаңыз.",
         E(b.get("title") or ""), E(b.get("owner") or ""), E(b.get("link") or ""),
         _opts(PLACES, b.get("place") or "all"), _opts(SECTIONS, b.get("section")),
         _opts(_oblasts(), b.get("oblast")),
         E(b.get("starts") or _today()), E(b.get("ends") or ""),
         "Сактоо" if bid else "Кошуу", "true" if bid else "false", k, bid)


def _list(k):
    rows = core.query("SELECT id, place, section, oblast, link, title, owner, starts, ends, "
                      "active, shows, clicks, updated FROM banners "
                      "WHERE COALESCE(status,'')<>'pending' ORDER BY id DESC",
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
    elif a == "paid":   # BANSELL: төлөм ырасталды
        core.query("UPDATE banners SET active=1, status='paid', updated=? WHERE id=?",
                   (core.now_str(), int(bid)))
        msg = "№%s ырасталды, баннер иштеп жатат" % bid
    elif a == "rej":
        core.query("UPDATE banners SET active=0, status='rejected', updated=? WHERE id=?",
                   (core.now_str(), int(bid)))
        msg = "№%s четке кагылды" % bid
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
    if p == "/admin/banners/cfg" and getattr(h, "command", "GET") == "POST":   # BANSELL
        return _cfg_save(h, uid, k)
    ed = (q.get("edit") or [""])[0]
    b = None
    if ed.isdigit():
        b = core.query("SELECT id, place, section, oblast, link, title, owner, starts, ends "
                       "FROM banners WHERE id=?", (int(ed),), fetch="one")
    body = _orders(k) + _cfg_form(k) + _form(b, k) + _list(k)   # BANSELL
    h._send(page("Баннерлер", body, "bn", msg))


# ══ BANSELL: колдонуучуга баннер сатуу (туруктуу баа) ═══════════════════
PRODUCTS = [
    # ачкыч, кыргызча, орусча, орун, бөлүм тандалабы, жумалык баа
    ("all", "Бардык орундар", "Все места", "all", False, 1500),
    ("home", "Башкы бет", "Главная страница", "home", False, 1000),
    ("top_all", "Бөлүмдөрдүн эң үстү (бардыгы)", "Верх всех разделов", "top", False, 1000),
    ("top_sec", "Бир бөлүмдүн эң үстү", "Верх одного раздела", "top", True, 500),
    ("grid_all", "Жарыялардын арасы (бардык бөлүмдөр)", "Между объявлениями (все разделы)", "grid", False, 600),
    ("grid_sec", "Жарыялардын арасы (бир бөлүм)", "Между объявлениями (один раздел)", "grid", True, 300),
]
WEEKS = [(1, 1), (2, 2), (4, 3)]      # (жума, канча жумага төлөйт)
REGION_OFF = 30                        # бир облус үчүн арзандатуу, %
# ROFF: ар бир аймактын өз арзандатуусу (админден өзгөрөт)
REGION_OFFS = {"Бишкек шаары": 10, "Ош шаары": 30, "Чүй облусу": 30,
               "Жалал-Абад облусу": 40, "Ош облусу": 40, "Ысык-Көл облусу": 40,
               "Нарын облусу": 50, "Талас облусу": 50, "Баткен облусу": 50}


def region_offs():
    c = cfg()
    out = {}
    for k, v in REGION_OFFS.items():
        try:
            out[k] = min(90, max(0, int(c.get("off_" + k) or v)))
        except Exception:
            out[k] = v
    return out
_RATE = {}


def _cfg_ensure():
    core.query("CREATE TABLE IF NOT EXISTS banner_cfg (k TEXT PRIMARY KEY, v TEXT)")
    for col, typ in (("status", "TEXT"), ("price", "INTEGER"), ("receipt", "TEXT"),
                     ("product", "TEXT"), ("weeks", "INTEGER")):
        try:
            if getattr(core, "IS_PG", False):
                core.query("ALTER TABLE banners ADD COLUMN IF NOT EXISTS %s %s" % (col, typ))
            else:
                core.query("ALTER TABLE banners ADD COLUMN %s %s" % (col, typ))
        except Exception:
            pass


def cfg():
    try:
        rows = core.query("SELECT k, v FROM banner_cfg", fetch="all") or []
        return {r["k"]: r["v"] for r in rows}
    except Exception:
        return {}


def _cfg_set(k, v):
    core.query("DELETE FROM banner_cfg WHERE k=?", (k,))
    core.query("INSERT INTO banner_cfg (k, v) VALUES (?, ?)", (k, str(v)))


def prices():
    c = cfg()
    out = {}
    for key, _ky, _ru, _pl, _ns, base in PRODUCTS:
        try:
            out[key] = int(c.get("price_" + key) or base)
        except Exception:
            out[key] = base
    return out


def calc(product, weeks, oblast):
    pr = prices().get(product)
    mult = dict(WEEKS).get(weeks)
    if pr is None or mult is None:
        return None
    total = pr * mult
    off = region_offs().get(oblast, 0) if oblast else 0   # ROFF
    if off:
        total = int(round(total * (100 - off) / 100.0 / 10.0)) * 10
    return total


def _jpeg(data_url, maxlen=3_000_000):
    s = str(data_url or "")
    if not s.startswith("data:image/jpeg;base64,"):
        return None
    b64 = s.split(",", 1)[1]
    if len(b64) > maxlen * 4 // 3:
        return None
    try:
        if base64.b64decode(b64)[:2] != b"\xff\xd8":
            return None
    except Exception:
        return None
    return b64


def _notify(text):
    try:
        import admin as _adm
        import os
        for a in [x for x in (os.environ.get("ADMIN_IDS") or "").replace(" ", "").split(",") if x]:
            _adm._tg_send(a, text)
    except Exception as e:
        print("banner notify:", e, flush=True)


def order(h, lang="ky"):
    """POST /reklama/order — колдонуучунун буйрутмасы."""
    ru = lang == "ru"
    _ensure()
    ip = (h.headers.get("X-Forwarded-For") or h.client_address[0] or "").split(",")[0].strip()
    now = time.time()
    hits = [x for x in _RATE.get(ip, []) if now - x < 3600]
    if len(hits) >= 5:
        return _json(h, {"ok": False, "msg": "Өтө көп аракет. Бир сааттан кийин кайталаңыз." if not ru
                         else "Слишком много попыток. Попробуйте через час."})
    try:
        n = int(h.headers.get("Content-Length") or 0)
        if not 0 < n < 9_000_000:
            return _json(h, {"ok": False, "msg": "Сүрөт өтө чоң" if not ru else "Слишком большой файл"})
        d = json.loads(h.rfile.read(n).decode("utf-8"))
    except Exception:
        return _json(h, {"ok": False, "msg": "Ката" if not ru else "Ошибка"})
    prod = {p[0]: p for p in PRODUCTS}.get(d.get("product"))
    try:
        weeks = int(d.get("weeks") or 0)
    except Exception:
        weeks = 0
    obl = str(d.get("oblast") or "")
    if obl and obl not in [x for x, _ in _oblasts()]:
        obl = ""
    sec = d.get("section") if (prod and prod[4] and d.get("section") in dict(SECTIONS)) else ""
    err = None
    if not prod or weeks not in dict(WEEKS):
        err = ("Орунду жана мөөнөттү тандаңыз", "Выберите место и срок")
    elif prod[4] and not sec:
        err = ("Бөлүмдү тандаңыз", "Выберите раздел")
    img = _jpeg(d.get("img"))
    if not err and not img:
        err = ("Баннердин сүрөтүн жүктөңүз", "Загрузите изображение баннера")
    phone = "".join(ch for ch in str(d.get("phone") or "") if ch.isdigit() or ch == "+")[:16]
    if not err and len(phone.replace("+", "")) < 9:
        err = ("Телефон номериңизди жазыңыз", "Укажите номер телефона")
    link = str(d.get("link") or "").strip()[:500]
    if link and not _safe_link(link):
        if link.startswith("www.") or "." in link:
            link = "https://" + link.lstrip("/")
        else:
            link = ""
    c = cfg()
    rec = _jpeg(d.get("receipt"))
    if not err and c.get("mbank") and not rec:
        err = ("Төлөм чегинин сүрөтүн жүктөңүз", "Загрузите фото чека об оплате")
    start = _date(d.get("start")) or _today()
    if start < _today():
        start = _today()
    if not err:   # BANCAP
        ff = free_from(prod[0], sec, obl, weeks)
        if start < ff:
            err = ("Бул орун тандалган күндөрү бош эмес. Эң жакынкы бош күн: %s." % _fdate(ff, False),
                   "На выбранные даты место занято. Ближайшая свободная дата: %s." % _fdate(ff, True))
    if err:
        return _json(h, {"ok": False, "msg": err[1] if ru else err[0]})
    total = calc(prod[0], weeks, obl)
    end = (datetime.strptime(start, "%Y-%m-%d") + timedelta(days=7 * weeks - 1)).strftime("%Y-%m-%d")
    title = str(d.get("name") or "").strip()[:120]
    bid = core.query(
        "INSERT INTO banners (place, section, oblast, link, title, owner, starts, ends, updated, img, "
        "active, shows, clicks, created_at, status, price, receipt, product, weeks) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,0,0,0,?,?,?,?,?,?)",
        (prod[3], sec, obl, link, title, phone, start, end, core.now_str(), img,
         core.now_str(), "pending", total, rec or "", prod[0], weeks), fetch="id")
    _RATE[ip] = hits + [now]
    site = (__import__("os").environ.get("SITE_URL") or "https://tapmeni.up.railway.app").rstrip("/")
    _notify("💰 <b>Жаңы баннер буйрутмасы №%s</b>\n\n📍 %s%s%s\n📅 %s → %s (%d жума)\n💵 %s сом%s\n"
            "👤 %s\n☎️ %s\n\n🛠 <a href=\"%s/admin/banners\">Админде текшерүү</a>"
            % (bid, E(prod[1]), (" · " + E(dict(SECTIONS)[sec])) if sec else "",
               (" · " + E(obl)) if obl else "", start, end, weeks, total,
               " · чек жүктөлдү" if rec else "", E(title or "—"), E(phone), site))
    msg = ("Буйрутма №%s кабыл алынды. Админ төлөмдү текшерип, баннериңизди иштетет — "
           "адатта бир нече сааттын ичинде." % bid) if not ru else \
          ("Заказ №%s принят. Администратор проверит оплату и запустит баннер — "
           "обычно в течение нескольких часов." % bid)
    _json(h, {"ok": True, "msg": msg, "id": bid})


_SELL_CSS = """<style>
.rk{max-width:620px;margin:0 auto;padding:4px 14px 120px}
.rk h1{font-size:24px;margin:8px 0 6px;color:#0B1B30}.rk .lead{color:#4A5A70;font-size:15px;margin:0 0 14px;line-height:1.5}
.rk .st{background:#fff;border:1.5px solid #D5DEEA;border-radius:18px;padding:14px;margin:12px 0}
.rk .st h2{font-size:17px;margin:0 0 10px;color:#17304F}
.rk .pr{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:12px;border:1.5px solid #D5DEEA;border-radius:14px;margin:8px 0;cursor:pointer;font-weight:600;color:#17304F}
.rk .pr input{width:20px;height:20px;flex:none;accent-color:#1E4FA8}.rk .pr .nm{flex:1}.rk .pr em{font-style:normal;color:#1E4FA8;font-weight:800;white-space:nowrap}
.rk .pr.on{border-color:#1E4FA8;background:#EEF4FF}
.rk label.l{display:block;font-size:13px;color:#4A5A70;margin:12px 0 5px;font-weight:600}
.rk input.f,.rk select.f{width:100%;box-sizing:border-box;font-size:16px;border:1.5px solid #C9D4E3;border-radius:12px;padding:11px 12px;background:#fff;color:#0B1B30}
.rk .wk{display:flex;gap:8px}.rk .wk button{flex:1;border:1.5px solid #C9D4E3;background:#fff;border-radius:12px;padding:10px 4px;font-size:14px;font-weight:700;color:#17304F}
.rk .wk button.on{background:#1E4FA8;border-color:#1E4FA8;color:#fff}.rk .wk small{display:block;font-weight:600;font-size:11px;opacity:.85}
.rk .prev{width:100%;aspect-ratio:2/1;object-fit:cover;border-radius:14px;margin-top:8px;display:none;background:#EEF3FA}
.rk .tot{font-size:30px;font-weight:800;color:#0B1B30;margin:4px 0}.rk .hint{font-size:12.5px;color:#6A7A90;margin-top:5px;line-height:1.45}
.rk .pay{background:#F3F8FF;border-radius:14px;padding:12px;margin-top:10px;font-size:15px;line-height:1.6;color:#17304F}
.rk .pay b{font-size:18px}.rk .qr{max-width:220px;width:100%;display:block;margin:10px auto 0;border-radius:12px}
.rk .go{width:100%;border:0;border-radius:16px;padding:15px;background:#1E9E5A;color:#fff;font-size:17px;font-weight:800;margin-top:14px}
.rk .ok{background:#E9F8EF;border:1.5px solid #9FD9B5;border-radius:16px;padding:16px;font-size:16px;color:#155B33;line-height:1.5}
.rk .er{color:#B42318;font-size:14px;margin-top:8px;font-weight:600}
</style>"""


def sell_body(lang="ky"):
    _ensure()
    ru = lang == "ru"
    t = lambda a, b: b if ru else a
    pr = prices()
    c = cfg()
    plist = "".join(
        '<label class="pr" data-k="%s" data-sec="%d"><input type="radio" name="prod" value="%s">'
        '<span class="nm">%s</span><em>%s %s</em></label>'
        % (k, 1 if ns else 0, k, E(rn if ru else kn), "{:,}".format(pr[k]).replace(",", " "),
           t("сом/жума", "сом/нед."))
        for k, kn, rn, _pl, ns, _b in PRODUCTS)
    # SELRU: бөлүм жана аймак аттары орусча бетте орусча
    _sr = {"trade": "Торговля", "wholesale": "Оптовая торговля", "property": "Продажа недвижимости",
           "vehicle": "Продажа транспорта", "service": "Услуги", "rental": "Аренда",
           "delivery": "Доставка", "cargo": "Грузоперевозки", "jobseek": "Поиск работы",
           "job": "Работа", "markets": "Рынки", "malls": "Торговые центры", "taxi": "Такси"}
    _or = {"Бишкек шаары": "г. Бишкек", "Ош шаары": "г. Ош", "Баткен облусу": "Баткенская область",
           "Жалал-Абад облусу": "Джалал-Абадская область", "Нарын облусу": "Нарынская область",
           "Ош облусу": "Ошская область", "Талас облусу": "Таласская область",
           "Чүй облусу": "Чуйская область", "Ысык-Көл облусу": "Иссык-Кульская область"}
    secs = "".join('<option value="%s">%s</option>' % (E(v), E(_sr.get(v, n) if ru else n))
                   for v, n in SECTIONS)
    obls = "".join('<option value="%s">%s</option>' % (E(v), E(_or.get(v, n) if ru else n))
                   for v, n in _oblasts())
    wk = "".join('<button type="button" data-w="%d"%s>%d %s%s</button>'
                 % (w, ' class="on"' if w == 1 else "", w, t("жума", "нед."),
                    ("<small>%s</small>" % t("1 жума бекер", "1 нед. в подарок")) if w == 4 else "")
                 for w, _m in WEEKS)
    if c.get("mbank"):
        pay = ('<div class="pay">%s<br>📱 MBank: <b>%s</b>%s%s</div>'
               '<label class="l">%s</label><input type="file" id="rcf" accept="image/*" class="f">'
               '<img id="rcp" class="prev" style="aspect-ratio:auto;max-height:260px;object-fit:contain">'
               % (t("Төмөнкү номерге которуңуз:", "Переведите на номер:"), E(c["mbank"]),
                  ("<br>👤 " + E(c.get("mname", ""))) if c.get("mname") else "",
                  '<img class="qr" src="/reklama/qr.jpg" alt="QR">' if c.get("qr") else "",
                  t("Төлөм чегинин сүрөтү (скриншот)", "Фото чека об оплате (скриншот)")))
    else:
        pay = '<div class="pay">%s</div>' % t(
            "Буйрутманы жөнөтүңүз — админ сиз менен байланышып, төлөмдү айтат.",
            "Отправьте заказ — администратор свяжется с вами насчёт оплаты.")
    js_pr = json.dumps(pr)
    return _SELL_CSS + '<script>window.TAPOFFS=%s;</script>' % json.dumps(region_offs()) + (   # ROFF
        '<main class="rk"><h1>📢 %s</h1><p class="lead">%s</p>'
        '<div class="st"><h2>1. %s</h2>%s'
        '<div id="secw" style="display:none"><label class="l">%s</label><select id="sec" class="f">'
        '<option value="">—</option>%s</select></div>'
        '<label class="l">%s</label><select id="obl" class="f"><option value="">%s</option>%s</select>'
        '<div class="hint">%s</div>'
        '<label class="l">%s</label><div class="wk" id="wk">%s</div>'
        '<label class="l">%s</label><input type="date" id="start" class="f" value="%s" min="%s"><div id="fr" class="hint" style="font-weight:700"></div></div>'
        '<div class="st"><h2>2. %s</h2>'
        '<label class="l">%s</label><input type="file" id="imf" accept="image/*" class="f">'
        '<div class="hint">%s</div><img id="imp" class="prev">'
        '<label class="l">%s</label><input id="lnk" class="f" placeholder="https://wa.me/996700123456">'
        '<label class="l">%s</label><input id="nm" class="f" placeholder="%s">'
        '<label class="l">%s</label><input id="ph" class="f" inputmode="tel" placeholder="0700 123 456"></div>'
        '<div class="st"><h2>3. %s</h2><div class="tot" id="tot">—</div>%s'
        '<div id="er" class="er"></div><button class="go" id="go" type="button">%s</button></div>'
        '<div id="done" class="ok" style="display:none"></div></main>'
    ) % (
        t("ТАП!'та жарнама берүү", "Реклама на ТАП!"),
        t("Баннериңиз бүт Кыргызстандагы же өзүңүздүн облусуңуздагы колдонуучуларга көрүнөт. "
          "Көрсөтүү жана басуу саны эсептелип турат.",
          "Ваш баннер увидят пользователи по всему Кыргызстану или в вашей области. "
          "Показы и клики учитываются."),
        t("Орун жана мөөнөт", "Место и срок"), plist,
        t("Бөлүмдү тандаңыз", "Выберите раздел"), secs,   # SECCHIP
        t("Аймак", "Регион"), t("Бүт Кыргызстан", "Весь Кыргызстан"), obls,
        t("Бир облус тандасаңыз — %d%% чейин арзан." % max(region_offs().values()), "Одна область — дешевле на %d%%." % REGION_OFF),
        t("Мөөнөтү", "Срок"), wk,
        t("Башталышы", "Начало"), _today(), _today(),
        t("Баннер", "Баннер"),
        t("Сүрөт (туурасына, 2:1)", "Изображение (горизонтальное, 2:1)"),
        t("Сүрөт ортосунан 1200×600 болуп кесилет.", "Изображение обрежется по центру до 1200×600."),
        t("Шилтеме (WhatsApp, сайт, Instagram) — милдеттүү эмес", "Ссылка (WhatsApp, сайт, Instagram) — необязательно"),
        t("Ишканаңыздын аты", "Название компании"), t("Мис: Береке дүкөнү", "Напр.: Магазин Береке"),
        t("Телефон номериңиз", "Ваш номер телефона"),
        t("Төлөм", "Оплата"), pay,
        t("Буйрутма берүү", "Отправить заказ"),
    ) + (
        '<script>(function(){var PR=%s,RO=%d,MB=%s,RU=%s;function T(a,b){return RU?b:a;}'
        'var W=1,IMG="",RC="";var $=function(i){return document.getElementById(i);};'
        'function prod(){var r=document.querySelector("input[name=prod]:checked");return r?r.value:"";}'
        'var MK=RU?["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]:["январь","февраль","март","апрель","май","июнь","июль","август","сентябрь","октябрь","ноябрь","декабрь"];'
        'function fd(s){var p=s.split("-");return RU?(+p[2])+" "+MK[+p[1]-1]:(+p[2])+"-"+MK[+p[1]-1];}'
        'function chk(p){var l=document.querySelector(".pr.on");if(l&&l.dataset.sec==="1"&&!$("sec").value){$("fr").textContent="";return;}'
        'fetch("/reklama/free?product="+p+"&weeks="+W+"&oblast="+encodeURIComponent($("obl").value)+"&section="+encodeURIComponent($("sec").value))'
        '.then(function(r){return r.json();}).then(function(j){if(!j.ok)return;var s=$("start");s.min=j.free;if(!s.dataset.m||!s.value||s.value<j.free)s.value=j.free;'
        '$("fr").style.color=j.busy?"#B42318":"#1E7A46";$("fr").textContent=j.busy?T("🔒 Бош эмес. Эң жакынкы бош күн: ","🔒 Занято. Ближайшая свободная дата: ")+fd(j.free):T("✅ Бош — бүгүндөн баштаса болот","✅ Свободно — можно начать сегодня");}).catch(function(){});}'
        'function calc(){var p=prod(),m={1:1,2:2,4:3}[W];document.querySelectorAll(".pr").forEach(function(l){'
        'l.classList.toggle("on",l.dataset.k===p);});var l=document.querySelector(".pr.on");'
        '$("secw").style.display="none";'
        'if(!p){$("tot").textContent="—";$("fr").textContent="";return;}chk(p);var t=PR[p]*m;var ro=(window.TAPOFFS||{})[$("obl").value]||0;if(ro)t=Math.round(t*(100-ro)/1000)*10;'
        '$("tot").textContent=t.toLocaleString("ru-RU").replace(/,/g," ")+" "+T("сом","сом");}'
        'document.querySelectorAll("input[name=prod]").forEach(function(r){r.onchange=calc;});'
        '$("obl").onchange=calc;$("sec").onchange=calc;$("start").onchange=function(){this.dataset.m=1;};/* BANCAP2 */document.querySelectorAll("#wk button").forEach(function(b){b.onclick=function(){'
        'W=+b.dataset.w;document.querySelectorAll("#wk button").forEach(function(x){x.classList.toggle("on",x===b);});calc();};});'
        'function rd(f,crop,mx,cb){var r=new FileReader();r.onload=function(){var im=new Image();im.onload=function(){'
        'var c=document.createElement("canvas"),g=c.getContext("2d"),sx=0,sy=0,sw=im.width,sh=im.height;'
        'if(crop){sw=Math.min(im.width,im.height*2);sh=sw/2;sx=(im.width-sw)/2;sy=(im.height-sh)/2;}'
        'var k=Math.min(1,mx/Math.max(sw,sh));c.width=Math.round(sw*k);c.height=Math.round(sh*k);'
        'g.fillStyle="#fff";g.fillRect(0,0,c.width,c.height);g.drawImage(im,sx,sy,sw,sh,0,0,c.width,c.height);'
        'cb(c.toDataURL("image/jpeg",0.85));};im.src=r.result;};r.readAsDataURL(f);}'
        '$("imf").onchange=function(){var f=this.files[0];if(f)rd(f,true,1200,function(u){IMG=u;$("imp").src=u;$("imp").style.display="block";});};'
        'if($("rcf"))$("rcf").onchange=function(){var f=this.files[0];if(f)rd(f,false,1400,function(u){RC=u;$("rcp").src=u;$("rcp").style.display="block";});};'
        '$("go").onclick=function(){var b=this;$("er").textContent="";'
        'if(!prod()){$("er").textContent=T("Орунду тандаңыз","Выберите место");return;}'
        'if(!IMG){$("er").textContent=T("Баннердин сүрөтүн жүктөңүз","Загрузите изображение баннера");return;}'
        'if($("ph").value.replace(/\\D/g,"").length<9){$("er").textContent=T("Телефон номериңизди жазыңыз","Укажите номер телефона");return;}'
        'if(MB&&!RC){$("er").textContent=T("Төлөм чегинин сүрөтүн жүктөңүз","Загрузите фото чека");return;}'
        'b.disabled=true;b.textContent=T("Жөнөтүлүүдө…","Отправка…");'
        'fetch("/reklama/order",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({'
        'product:prod(),section:$("sec").value,oblast:$("obl").value,weeks:W,start:$("start").value,'
        'img:IMG,receipt:RC,link:$("lnk").value,name:$("nm").value,phone:$("ph").value})})'
        '.then(function(r){return r.json();}).then(function(j){if(j.ok){document.querySelectorAll(".rk .st").forEach(function(s){s.style.display="none";});'
        '$("done").textContent="✅ "+j.msg;$("done").style.display="block";scrollTo(0,0);}'
        'else{$("er").textContent=j.msg||T("Ката","Ошибка");b.disabled=false;b.textContent=T("Буйрутма берүү","Отправить заказ");}})'
        '.catch(function(){$("er").textContent=T("Байланыш катасы","Ошибка связи");b.disabled=false;b.textContent=T("Буйрутма берүү","Отправить заказ");});};'
        '(function(){'
        'var st=document.createElement("style");st.textContent=".rk .tl{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:6px 0 4px}.rk .tl button{text-align:left;border:1.5px solid #C9D4E3;background:#fff;border-radius:14px;padding:11px 12px;color:#17304F;font:700 15px system-ui,sans-serif}.rk .tl button small{display:block;font-weight:600;font-size:12.5px;color:#1E4FA8;margin-top:3px}.rk .tl button.on{border-color:#1E4FA8;background:#EEF4FF}.rk .cps{display:flex;flex-wrap:wrap;gap:7px;margin:6px 0 4px}.rk .cps button{border:1.5px solid #C9D4E3;background:#fff;border-radius:99px;padding:8px 13px;font:700 14px system-ui,sans-serif;color:#17304F}.rk .cps button.on{background:#1E4FA8;border-color:#1E4FA8;color:#fff}.rk .cps button em{font-style:normal;font-size:12px;color:#1E9E5A;margin-left:5px}.rk .cps button.on em{color:#CFF5DD}.rk .wk small.wp{display:block;font-size:12px;font-weight:700;margin-top:2px;opacity:.9}.rk .pv{display:grid;grid-template-columns:140px minmax(0,1fr);gap:12px;margin-top:14px;align-items:start}.rk .pvp{border:1.5px solid #C9D4E3;border-radius:16px;padding:7px;background:#F6F8FC}.rk .pvp p{font-size:11px;color:#5A6B82;margin:6px 2px 3px;font-weight:700}.rk .bk{border-radius:7px;font-size:11px;padding:5px 6px;margin:3px 0;background:#fff;color:#8A97AA;border:1px solid #E1E7F0}.rk .bka{border-radius:7px;font-size:11px;padding:5px 6px;margin:3px 0;background:#FFF4CC;border-color:#E3A008;color:#7A4B00;font-weight:800}.rk .pvl{font-size:12.5px;color:#4A5A70;font-weight:700;margin:0 0 3px}.rk .pvw{font-size:14px;color:#17304F;margin:0 0 10px;line-height:1.45}.rk .pvr{display:flex;justify-content:space-between;font-size:13.5px;padding:2px 0;color:#17304F}.rk .pvrg{display:flex;justify-content:space-between;font-size:13.5px;padding:2px 0;color:#1E7A46}.rk .pvrt{display:flex;justify-content:space-between;color:#17304F;border-top:1px solid #D5DEEA;margin-top:4px;padding-top:6px;font-weight:800;font-size:16px}";document.head.appendChild(st);'
        'function nf(n){return Number(n).toLocaleString("ru-RU");}'
        'var OFFS=window.TAPOFFS||{},MUL={1:1,2:2,4:3},SOM=T(" сом"," сом");'
        'var PL="",SC="",OB="";'
        'var box=document.querySelector(".rk .st");var h2=box.querySelector("h2");'
        'document.querySelectorAll(".rk .pr").forEach(function(l){l.style.display="none";});'
        '$("secw").style.display="none";var ob=$("obl");ob.style.display="none";'
        'if(ob.previousElementSibling)ob.previousElementSibling.style.display="none";'
        'if(ob.nextElementSibling&&ob.nextElementSibling.classList.contains("hint"))ob.nextElementSibling.style.display="none";'
        'function lab(t){var e=document.createElement("label");e.className="l";e.textContent=t;return e;}'
        'function key(){return PL==="top"?(SC?"top_sec":"top_all"):PL==="grid"?(SC?"grid_sec":"grid_all"):PL;}'
        'function price(k,w,o){var t=PR[k]*MUL[w];var ro=OFFS[o]||0;if(ro)t=Math.round(t*(100-ro)/1000)*10;return t;}'
        'var wrap=document.createElement("div");'
        'wrap.appendChild(lab(T("Орду","Место")));'
        'var tl=document.createElement("div");tl.className="tl";wrap.appendChild(tl);'
        'var places=[["all",T("Бардык орундар","Все места"),[nf(PR.all)+SOM]],["home",T("Башкы бет","Главная"),[nf(PR.home)+SOM]],'
        '["top",T("Бөлүмдүн эң үстү","Верх раздела"),[T("1 бөлүм: ","1 раздел: ")+nf(PR.top_sec)+SOM,T("Бардыгы: ","Все: ")+nf(PR.top_all)+SOM]],'
        '["grid",T("Жарыялардын арасы","Между объявлениями"),[T("1 бөлүм: ","1 раздел: ")+nf(PR.grid_sec)+SOM,T("Бардыгы: ","Все: ")+nf(PR.grid_all)+SOM]]];'
        'places.forEach(function(p){var b=document.createElement("button");b.type="button";b.dataset.p=p[0];'
        'b.appendChild(document.createTextNode(p[1]));p[2].forEach(function(x){var sm=document.createElement("small");sm.textContent=x+T(" /жума"," /нед.");b.appendChild(sm);});'
        'b.onclick=function(){PL=p[0];tl.querySelectorAll("button").forEach(function(x){x.classList.toggle("on",x===b);});sw.style.display=(PL==="top"||PL==="grid")?"block":"none";apply();};tl.appendChild(b);});'
        'var sw=document.createElement("div");sw.style.display="none";sw.appendChild(lab(T("Бөлүм","Раздел")));'
        'var sc=document.createElement("div");sc.className="cps";sw.appendChild(sc);wrap.appendChild(sw);'
        'function chip(cont,txt,val,cb,on){var b=document.createElement("button");b.type="button";b.dataset.v=val;b.appendChild(document.createTextNode(txt));var e=document.createElement("em");b.appendChild(e);'
        'if(on)b.classList.add("on");b.onclick=function(){cont.querySelectorAll("button").forEach(function(x){x.classList.toggle("on",x===b);});cb(val);};cont.appendChild(b);return b;}'
        'chip(sc,T("Бардык бөлүмдөр","Все разделы"),"",function(v){SC=v;apply();},true);'
        'Array.prototype.forEach.call($("sec").options,function(o){if(o.value)chip(sc,o.textContent,o.value,function(v){SC=v;apply();});});'
        'wrap.appendChild(lab(T("Шаар / облус","Город / область")));'
        'var oc=document.createElement("div");oc.className="cps";wrap.appendChild(oc);'
        'chip(oc,T("Бүт Кыргызстан","Весь Кыргызстан"),"",function(v){OB=v;apply();},true);'
        'Array.prototype.forEach.call(ob.options,function(o){if(o.value)chip(oc,o.textContent,o.value,function(v){OB=v;apply();});});'
        'h2.parentNode.insertBefore(wrap,h2.nextSibling);'
        'var pv=document.createElement("div");pv.className="pv";pv.innerHTML="<div><p class=pvl></p><div class=pvp></div></div><div><p class=pvl></p><p class=pvw></p><p class=pvl></p><div class=pvc></div></div>";box.appendChild(pv);'
        'var PVL=pv.querySelectorAll(".pvl");PVL[0].textContent=T("Сайтта кайда чыгат","Где на сайте");PVL[1].textContent=T("Ким көрөт","Кто увидит");PVL[2].textContent=T("Баасы","Цена");'
        'function cname(cont){var b=cont.querySelector("button.on");return b?b.firstChild.textContent:"";}'
        'function bk(on,txt){return "<div class="+(on?"bka":"bk")+">"+(on?T("Сиздин баннер","Ваш баннер"):txt)+"</div>";}'
        'function pvw(){var k=key();var H=PL==="home"||PL==="all",TP=PL==="top"||PL==="all",G=PL==="grid"||PL==="all";var tb=T("ТАП! баннери","Баннер ТАП!");var sn=(PL==="top"||PL==="grid")&&SC?cname(sc):T("Ар бир бөлүм","Любой раздел");'
        'pv.querySelector(".pvp").innerHTML="<p>"+T("Башкы бет","Главная")+"</p>"+bk(0,T("Бөлүм: 4 жарыя","Раздел: 4 объявл."))+bk(H,tb)+bk(0,T("Бөлүм: 4 жарыя","Раздел: 4 объявл."))+"<p>"+sn+"</p>"+bk(TP,tb)+bk(0,T("6 жарыя","6 объявл."))+bk(G,tb)+bk(0,T("6 жарыя","6 объявл."));'
        'var rn=OB?cname(oc):"";var w=OB?T(rn+" тандаган колдонуучулар гана","Только пользователи, выбравшие «"+rn+"»"):T("Бүт Кыргызстандагы бардык колдонуучулар","Все пользователи Кыргызстана");'
        'if(PL==="top"||PL==="grid")w+=SC?T(", «"+sn+"» бөлүмүн ачканда",", при открытии раздела «"+sn+"»"):T(", каалаган бөлүмдү ачканда",", при открытии любого раздела");'
        'pv.querySelector(".pvw").textContent=PL?w+".":T("Жогорудан орунду тандаңыз.","Выберите место выше.");'
        'var c=pv.querySelector(".pvc");if(!k){c.innerHTML="";return;}var p=PR[k],m=MUL[W],sub=p*m,ro=OFFS[OB]||0,tot=price(k,W,OB);'
        'c.innerHTML="<div class=pvr><span>1 "+T("жума","нед.")+"</span><span>"+nf(p)+SOM+"</span></div><div class=pvr><span>× "+W+" "+T("жума","нед.")+(W===4?T(" (1 бекер)"," (1 в подарок)"):"")+"</span><span>"+nf(sub)+SOM+"</span></div>"+(ro?"<div class=pvrg><span>−"+ro+"%% "+T("аймак","регион")+"</span><span>−"+nf(sub-tot)+SOM+"</span></div>":"")+"<div class=pvrt><span>"+T("Төлөйсүз","К оплате")+"</span><span>"+nf(tot)+SOM+"</span></div>";}'
        'function refresh(){var k=key();'
        'oc.querySelectorAll("button").forEach(function(b){var ro=OFFS[b.dataset.v]||0,s=ro?"−"+ro+"%%":"";if(k){s=(s?s+" · ":"")+nf(price(k,1,b.dataset.v))+SOM;}b.querySelector("em").textContent=s;});'
        'document.querySelectorAll("#wk button").forEach(function(b){var w=+b.dataset.w,sm=b.querySelector("small.wp");if(!sm){sm=document.createElement("small");sm.className="wp";b.appendChild(sm);}'
        'sm.textContent=k?nf(price(k,w,OB))+SOM:"";});pvw();}'
        'function apply(){refresh();if(!PL)return;var k=key();'
        'var r=document.querySelector("input[name=prod][value="+k+"]");if(r)r.checked=true;$("sec").value=(PL==="top"||PL==="grid")?SC:"";ob.value=OB;calc();}'
        'document.querySelectorAll("#wk button").forEach(function(b){b.addEventListener("click",function(){setTimeout(refresh,0);});});'
        'refresh();'
        '})();'
        '/* CHIPUI3 */'
        'calc();})();</script>'
    ) % (js_pr, REGION_OFF, "true" if c.get("mbank") else "false", "true" if ru else "false")


def serve_qr(h):
    c = cfg()
    try:
        data = base64.b64decode(c.get("qr") or "")
    except Exception:
        data = b""
    if not data:
        return _404(h)
    h.send_response(200)
    h.send_header("Content-Type", "image/jpeg")
    h.send_header("Content-Length", str(len(data)))
    h.send_header("Cache-Control", "max-age=600")
    h.end_headers()
    h.wfile.write(data)


def _orders(k):
    rows = core.query("SELECT id, place, section, oblast, link, title, owner, starts, ends, price, "
                      "product, weeks, receipt FROM banners WHERE status='pending' ORDER BY id",
                      fetch="all") or []
    if not rows:
        return ""
    pn = {p[0]: p[1] for p in PRODUCTS}
    out = "<h2>🆕 Төлөм күтүүдө (%d)</h2>" % len(rows)
    for b in rows:
        a = "/admin/banners/act?k=%s&id=%d&a=" % (k, b["id"])
        out += (
            "<div class='bn' style='border-color:#E3A008'><img src='/bimg/%d.jpg?v=o' alt=''>"
            "<div class='ah' style='margin-top:8px'>№%d · %s</div>"
            "<div class='am'>📍 %s%s · %s</div><div class='am'>📅 %s → %s (%s жума)</div>"
            "<div class='am'>💵 <b>%s сом</b> · 👤 %s · ☎️ %s</div>%s%s"
            "<div class='ab'><a href='%spaid' onclick=\"return confirm('Төлөм келдиби? №%d иштетилсинби?')\">✅ Төлөм келди, иштетүү</a>"
            "<a class='del' href='%srej' onclick=\"return confirm('№%d четке кагылсынбы?')\">❌ Четке кагуу</a></div></div>"
        ) % (b["id"], b["id"], E(pn.get(b.get("product"), "")),
             E(_name(PLACES, b.get("place"), "")),
             (" · " + E(dict(SECTIONS).get(b.get("section") or "", ""))) if b.get("section") else "",
             E(b.get("oblast") or "Бүт Кыргызстан"), E(b.get("starts") or ""), E(b.get("ends") or ""),
             b.get("weeks") or "?", b.get("price") or "?", E(b.get("title") or "—"), E(b.get("owner") or "—"),
             ("<div class='am'>🔗 %s</div>" % E(b["link"])) if b.get("link") else "",
             ("<div class='am'>🧾 Чек:</div><img src='data:image/jpeg;base64,%s' style='aspect-ratio:auto;max-width:100%%;object-fit:contain'>"
              % b["receipt"]) if b.get("receipt") else "<div class='am'>🧾 Чек жүктөлгөн эмес</div>",
             a, b["id"], a, b["id"])
    return out


def _cfg_form(k):
    c = cfg()
    pr = prices()
    cp = caps()   # BANCAP
    rows = "".join('<label>%s (сом/жума)</label><input id="p_%s" inputmode="numeric" value="%d">'
                   '<label style="font-size:12px">↳ бир убакта канча баннер</label>'
                   '<input id="cap_%s" inputmode="numeric" value="%d">'
                   % (E(kn), key, pr[key], key, cp.get(key, 1))
                   for key, kn, _r, _p, _n, _b in PRODUCTS)
    return (
        "<details class='bf ad' style='margin-bottom:12px'><summary class='ah'>💰 Баалар жана төлөм маалыматы</summary>"
        + rows +
        "<div class='ah' style='margin-top:14px'>Аймак боюнча арзандатуу, %%</div>"
        + "".join("<label>%s</label><input id='o_%d' data-k='%s' class='roff' inputmode='numeric' value='%d'>"
                  % (E(k), i, E(k), v) for i, (k, v) in enumerate(region_offs().items())) +
        "<label>MBank номери (бош калса, чек суралбайт)</label><input id='c_mb' value='%s' placeholder='0700 123 456'>"
        "<label>Алуучунун аты</label><input id='c_mn' value='%s' placeholder='Азамат Ж.'>"
        "<label>MBank QR сүрөтү %s</label><input type='file' id='c_qr' accept='image/*'>"
        "<button type='button' id='c_sv'>Сактоо</button></details>"
        "<script>(function(){var QR='';var f=document.getElementById('c_qr');f.onchange=function(){var x=f.files[0];if(!x)return;"
        "var r=new FileReader();r.onload=function(){var im=new Image();im.onload=function(){var k=Math.min(1,700/Math.max(im.width,im.height));"
        "var c=document.createElement('canvas');c.width=Math.round(im.width*k);c.height=Math.round(im.height*k);var g=c.getContext('2d');"
        "g.fillStyle='#fff';g.fillRect(0,0,c.width,c.height);g.drawImage(im,0,0,c.width,c.height);QR=c.toDataURL('image/jpeg',0.9);};im.src=r.result;};r.readAsDataURL(x);};"
        "document.getElementById('c_sv').onclick=function(){var P={},C={};%s.forEach(function(k){P[k]=document.getElementById('p_'+k).value;C[k]=document.getElementById('cap_'+k).value;});"
        "fetch('/admin/banners/cfg',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({k:'%s',prices:P,caps:C,offs:(function(){var O={};document.querySelectorAll('.roff').forEach(function(e){O[e.dataset.k]=e.value;});return O;})(),"
        "mbank:document.getElementById('c_mb').value,mname:document.getElementById('c_mn').value,qr:QR})})"
        ".then(function(r){return r.json();}).then(function(j){location.href='/admin/banners?m='+encodeURIComponent(j.msg||'');});};})();</script>"
    ) % (E(c.get("mbank", "")), E(c.get("mname", "")), "(жүктөлгөн ✅)" if c.get("qr") else "",
         json.dumps([p[0] for p in PRODUCTS]), k)


def _cfg_save(h, uid, k):
    try:
        n = int(h.headers.get("Content-Length") or 0)
        d = json.loads(h.rfile.read(n).decode("utf-8")) if 0 < n < 3_000_000 else {}
    except Exception:
        d = {}
    if not hmac.compare_digest(str(d.get("k") or ""), k):
        return _json(h, {"ok": False, "msg": "Сессия бүттү"})
    for key, *_r in PRODUCTS:
        v = str((d.get("prices") or {}).get(key) or "").strip()
        if v.isdigit() and 0 < int(v) < 10_000_000:
            _cfg_set("price_" + key, int(v))
    for key in CAPS:   # BANCAP
        v = str((d.get("caps") or {}).get(key) or "").strip()
        if v.isdigit() and 0 < int(v) <= 20:
            _cfg_set("cap_" + key, int(v))
    for k in REGION_OFFS:   # ROFF
        v = str((d.get("offs") or {}).get(k) or "").strip()
        if v.isdigit() and 0 <= int(v) <= 90:
            _cfg_set("off_" + k, int(v))
    _cfg_set("mbank", str(d.get("mbank") or "").strip()[:30])
    _cfg_set("mname", str(d.get("mname") or "").strip()[:60])
    q = _jpeg(d.get("qr"))
    if q:
        _cfg_set("qr", q)
    _json(h, {"ok": True, "msg": "Баалар сакталды"})



# ══ BANCAP: ар бир орундун сыйымдуулугу, бош эмес болсо — эң жакынкы бош күн ══
CAPS = {"all": 1, "home": 2, "top_all": 1, "top_sec": 1, "grid_all": 3, "grid_sec": 3}
_HOLD_H = 48          # төлөм күтүп турган буйрутма орунду канча саат кармайт


def caps():
    c = cfg()
    out = {}
    for k, v in CAPS.items():
        try:
            out[k] = max(1, int(c.get("cap_" + k) or v))
        except Exception:
            out[k] = v
    return out


def _dt(x):
    try:
        return datetime.strptime(str(x)[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _occupied():
    """Орунду ээлеген баннерлер: төлөнгөн+күйүк, же 48 сааттан жаңы буйрутма.
    Админдин өз баннерлери (статусу жок) эсептелбейт."""
    rows = core.query("SELECT place, section, oblast, starts, ends, status, active, created_at "
                      "FROM banners WHERE status IN ('paid','pending')", fetch="all") or []
    now = _dt(core.now_str())
    out = []
    for r in rows:
        if r.get("status") == "paid" and int(r.get("active") or 0) != 1:
            continue
        if r.get("status") == "pending":
            c = _dt(r.get("created_at"))
            if now and c and (now - c).total_seconds() > _HOLD_H * 3600:
                continue
        out.append(r)
    return out


def _clash(place, sec, obl, r):
    pl = r.get("place") or "all"
    if not (place == "all" or pl == "all" or pl == place):
        return False
    rs = r.get("section") or ""
    if sec and rs and rs != sec:
        return False
    ro = r.get("oblast") or ""
    if obl and ro and ro != obl:
        return False
    return True


def free_from(product, sec, obl, weeks):
    """Ушул орун ушул мөөнөткө бош болгон эң жакынкы күн (YYYY-MM-DD)."""
    prod = {p[0]: p for p in PRODUCTS}.get(product)
    if not prod:
        return _today()
    cap = caps().get(product, 1)
    sec = sec if prod[4] else ""
    occ = [r for r in _occupied() if _clash(prod[3], sec, obl, r)]
    t0 = datetime.strptime(_today(), "%Y-%m-%d")
    span = 7 * max(1, int(weeks or 1))
    if len(occ) < cap:
        return _today()
    for i in range(0, 400):
        ok = True
        for j in range(span):
            day = (t0 + timedelta(days=i + j)).strftime("%Y-%m-%d")
            n = sum(1 for r in occ if (r.get("starts") or "0000") <= day <= (r.get("ends") or "9999"))
            if n >= cap:
                ok = False
                break
        if ok:
            return (t0 + timedelta(days=i)).strftime("%Y-%m-%d")
    return (t0 + timedelta(days=400)).strftime("%Y-%m-%d")


def _fdate(s, ru=False):
    mk = (["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
           "сентября", "октября", "ноября", "декабря"] if ru else
          ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август",
           "сентябрь", "октябрь", "ноябрь", "декабрь"])
    try:
        y, m, d = [int(x) for x in s.split("-")]
        return ("%d %s" if ru else "%d-%s") % (d, mk[m - 1])
    except Exception:
        return s


def free_api(h, q):
    """GET /reklama/free?product=&section=&oblast=&weeks="""
    _ensure()
    g = lambda x: (q.get(x) or [""])[0]
    try:
        w = int(g("weeks") or 1)
    except Exception:
        w = 1
    obl = g("oblast")
    if obl and obl not in [x for x, _ in _oblasts()]:
        obl = ""
    f = free_from(g("product"), g("section"), obl, w)
    _json(h, {"ok": True, "free": f, "busy": f > _today()})
