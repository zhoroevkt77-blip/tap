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
        rows = core.query("SELECT id, place, section, oblast, link, starts, ends, updated, slot, video "
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
             if not b.get("slot") and (b.get("place") or "all") in (place, "all")
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
    body = _slotmap(q) + _orders(k) + _cfg_form(k) + _form(b, k) + _list(k)   # BANSELL SLOTMAP
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
                     ("product", "TEXT"), ("weeks", "INTEGER"), ("slot", "TEXT"), ("video", "TEXT")):
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
    if d.get("slot"):   # SLOTS
        return _order_slot(h, d, ru, ip, hits, now)
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
    return _SELL_CSS + '<script>window.TAPOFFS=%s;</script>' % json.dumps(region_offs()) + slots_js(lang) + (   # ROFF
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
        'if(!p){$("tot").textContent="—";$("fr").textContent="";return;}if(!window.TAPSLOT)chk(p);var t=PR[p]*m;var ro=(window.TAPOFFS||{})[$("obl").value]||0;if(ro)t=Math.round(t*(100-ro)/1000)*10;'
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
        'if(window.TAPVBUSY){$("er").textContent=T("⏳ Видео али даярдалып жатат, бир аз күтүңүз","⏳ Видео ещё обрабатывается, подождите");return;}'
        'if(!IMG){$("er").textContent=window.TAPVMODE==="video"?T("Видеону жүктөңүз","Загрузите видео"):T("Баннердин сүрөтүн жүктөңүз","Загрузите изображение баннера");return;}'
        'if($("ph").value.replace(/\\D/g,"").length<9){$("er").textContent=T("Телефон номериңизди жазыңыз","Укажите номер телефона");return;}'
        'if(MB&&!RC){$("er").textContent=T("Төлөм чегинин сүрөтүн жүктөңүз","Загрузите фото чека");return;}'
        'b.disabled=true;b.textContent=T("Жөнөтүлүүдө…","Отправка…");'
        'fetch("/reklama/order",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({'
        'product:prod(),slot:window.TAPSLOT||"",video:window.TAPVIDEO||"",section:$("sec").value,oblast:$("obl").value,weeks:W,start:$("start").value,'
        'img:IMG,receipt:RC,link:$("lnk").value,name:$("nm").value,phone:$("ph").value})})'
        '.then(function(r){return r.json();}).then(function(j){if(j.ok){document.querySelectorAll(".rk .st").forEach(function(s){s.style.display="none";});'
        '$("done").textContent="✅ "+j.msg;$("done").style.display="block";scrollTo(0,0);}'
        'else{$("er").textContent=j.msg||T("Ката","Ошибка");b.disabled=false;b.textContent=T("Буйрутма берүү","Отправить заказ");}})'
        '.catch(function(){$("er").textContent=T("Байланыш катасы","Ошибка связи");b.disabled=false;b.textContent=T("Буйрутма берүү","Отправить заказ");});};'
        '(function(){'
        'var st=document.createElement("style");st.textContent=".rk .cps{display:flex;flex-wrap:wrap;gap:7px;margin:6px 0 4px}.rk .cps button{border:1.5px solid #C9D4E3;background:#fff;border-radius:99px;padding:8px 13px;font:700 14px system-ui,sans-serif;color:#17304F}.rk .cps button.on{background:#1E4FA8;border-color:#1E4FA8;color:#fff}.rk .cps button em{font-style:normal;font-size:12px;color:#1E9E5A;margin-left:5px}.rk .cps button.on em{color:#CFF5DD}.rk .av{font-size:11.5px;font-weight:800;color:#1E7A46;margin-left:5px}.rk .av.bz{color:#B42318}.rk .cps button.on .av{color:#CFF5DD}.rk .cps button.on .av.bz{color:#FFD2CC}.rk .map{border:1.5px solid #C9D4E3;border-radius:16px;padding:8px;background:#F6F8FC;margin:6px 0 4px}.rk .mr{font-size:12px;color:#8A97AA;padding:4px 8px;margin:3px 0;border-radius:8px;background:#fff;border:1px solid #E6EBF2}.rk .slc{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:10px 11px;margin:5px 0;border-radius:11px;border:1.5px dashed #9FD9B5;background:#EEFBF3;color:#155B33;font:700 14px system-ui,sans-serif;cursor:pointer}.rk .slc.bz{border-color:#D5DEEA;background:#fff;color:#6A7A90}.rk .slc.on{border:2px solid #1E4FA8;background:#EEF4FF;color:#17304F}.rk .slc small{font-weight:700;font-size:12.5px;text-align:right}.rk .wk small.wp{display:block;font-size:12px;font-weight:700;margin-top:2px;opacity:.9}.rk .pvw{font-size:14px;color:#17304F;margin:10px 0;line-height:1.45}.rk .pvr,.rk .pvrg,.rk .pvrt{display:flex;justify-content:space-between;font-size:13.5px;padding:2px 0;color:#17304F}.rk .pvrg{color:#1E7A46}.rk .pvrt{border-top:1px solid #D5DEEA;margin-top:4px;padding-top:6px;font-weight:800;font-size:16px}";document.head.appendChild(st);'
        'function nf(n){return Number(n).toLocaleString("ru-RU");}'
        'var OFFS=window.TAPOFFS||{},SL=window.TAPSLOTS||{home:[],sec:{},names:[]},MUL={1:1,2:2,4:3},SOM=" сом";'
        'var PG="home",SID="",OB="",AV=null,TD="";window.TAPSLOT="";var MODE="img",VP=SL.vpct||50;window.TAPVIDEO="";'
        'var box=document.querySelector(".rk .st");var h2=box.querySelector("h2");'
        'document.querySelectorAll(".rk .pr").forEach(function(l){l.style.display="none";});'
        '$("secw").style.display="none";var ob=$("obl");ob.style.display="none";'
        'if(ob.previousElementSibling)ob.previousElementSibling.style.display="none";'
        'if(ob.nextElementSibling&&ob.nextElementSibling.classList.contains("hint"))ob.nextElementSibling.style.display="none";'
        'function lab(t){var e=document.createElement("label");e.className="l";e.textContent=t;return e;}'
        'function sp(s){var r={};SL.home.forEach(function(x){r[x[0]]=x[1];});return r[s]!==undefined?r[s]:SL.sec[s.split(":")[1]];}'
        'function price(s,w,o){var t=sp(s)*MUL[w];if(MODE==="video")t=Math.round(t*(100+VP)/1000)*10;var ro=OFFS[o]||0;if(ro)t=Math.round(t*(100-ro)/1000)*10;return t;}'
        'function fr(s,o){return AV&&AV[s]?AV[s][o||""]:null;}'
        'function nm(c){var r="";SL.names.forEach(function(x){if(x[0]===c)r=x[1];});return r;}'
        'function slab(s){if(s.charAt(0)==="h")return "Б-"+s.slice(1);var k=s.split(":")[1];return k==="top"?T("Эң үстү","Самый верх"):k==="g1"?T("1-ара · 6-жарыядан кийин","1-й · после 6-го объявл."):T("2-ара · 12-жарыядан кийин","2-й · после 12-го объявл.");}'
        'var wrap=document.createElement("div");'
        'wrap.appendChild(lab(T("1) Кайсы бет","1) Страница")));'
        'var pc=document.createElement("div");pc.className="cps";wrap.appendChild(pc);'
        'wrap.appendChild(lab(T("2) Орунду тандаңыз — жашыл орундар бош (баалар 1 жума үчүн)","2) Выберите место — зелёные свободны (цены за 1 неделю)")));'
        'var mp=document.createElement("div");mp.className="map";wrap.appendChild(mp);'
        'wrap.appendChild(lab(T("3) Шаар / облус","3) Город / область")));'
        'var oc=document.createElement("div");oc.className="cps";wrap.appendChild(oc);'
        'var pw=document.createElement("div");box.appendChild(pw);'
        'function chip(cont,txt,val,cb,on){var b=document.createElement("button");b.type="button";b.dataset.v=val;b.appendChild(document.createTextNode(txt));var e=document.createElement("em");b.appendChild(e);var a=document.createElement("span");a.className="av";b.appendChild(a);'
        'if(on)b.classList.add("on");b.onclick=function(){cont.querySelectorAll("button").forEach(function(x){x.classList.toggle("on",x===b);});cb(val);};cont.appendChild(b);return b;}'
        'chip(pc,T("Башкы бет","Главная"),"home",function(v){PG=v;SID="";drawMap();apply();},true);'
        'SL.names.forEach(function(x){chip(pc,x[1],x[0],function(v){PG=v;SID="";drawMap();apply();});});'
        'chip(oc,T("Бүт Кыргызстан","Весь Кыргызстан"),"",function(v){OB=v;apply();},true);'
        'Array.prototype.forEach.call(ob.options,function(o){if(o.value)chip(oc,o.textContent,o.value,function(v){OB=v;apply();});});'
        'h2.parentNode.insertBefore(wrap,h2.nextSibling);'
        'function row(t){var d=document.createElement("div");d.className="mr";d.textContent=t;mp.appendChild(d);}'
        'function card(s){var d=document.createElement("div");d.className="slc";d.dataset.s=s;var b=document.createElement("span");b.textContent=slab(s);var m=document.createElement("small");d.appendChild(b);d.appendChild(m);'
        'd.onclick=function(){SID=s;apply();};mp.appendChild(d);}'
        'function drawMap(){mp.innerHTML="";if(PG==="home"){SL.names.forEach(function(x,i){if(i<SL.home.length){row((i+1)+T("-бөлүм · 4 жарыя","-й раздел · 4 объявл."));card(SL.home[i][0]);}});}'
        'else{row(T("«","«")+nm(PG)+T("» бөлүмү ачылганда","» — при открытии раздела"));card(PG+":top");row(T("6 жарыя","6 объявлений"));card(PG+":g1");row(T("6 жарыя","6 объявлений"));card(PG+":g2");row("…");}'
        'paint();}'
        'function fdl(f){var p=f.split("-"),L=["январда","февралда","мартта","апрелде","майда","июнда","июлда","августта","сентябрда","октябрда","ноябрда","декабрда"];return RU?"🔒 свободно с "+fd(f):"🔒 "+(+p[2])+"-"+L[+p[1]-1]+" бошойт";}/* FREETXT */function stat(f){if(!f)return "";return f>TD?fdl(f):"✓";}'
        'function paint(){mp.querySelectorAll(".slc").forEach(function(d){var s=d.dataset.s,f=fr(s,OB),bz=f&&f>TD;d.classList.toggle("bz",!!bz);d.classList.toggle("on",s===SID);'
        'd.querySelector("small").textContent=nf(price(s,1,OB))+SOM+(f?" · "+(bz?fdl(f):T("бош","свободно")):"");});'
        'oc.querySelectorAll("button").forEach(function(b){var v=b.dataset.v,ro=OFFS[v]||0,t=ro?"−"+ro+"%%":"";if(SID)t=(t?t+" · ":"")+nf(price(SID,1,v))+SOM;b.querySelector("em").textContent=t;var a=b.querySelector(".av"),f=SID?fr(SID,v):null;a.className="av"+(f&&f>TD?" bz":"");a.textContent=SID?stat(f):"";});'
        'pc.querySelectorAll("button").forEach(function(b){b.querySelector(".av").textContent="";});'
        'document.querySelectorAll("#wk button").forEach(function(b){var w=+b.dataset.w,sm=b.querySelector("small.wp");if(!sm){sm=document.createElement("small");sm.className="wp";b.appendChild(sm);}sm.textContent=SID?nf(price(SID,w,OB))+SOM:"";});'
        'over();}'
        'function over(){if(!SID){pw.innerHTML="";return;}var p=sp(SID),m=MUL[W],sub=p*m,ro=OFFS[OB]||0,tot=price(SID,W,OB);$("tot").textContent=nf(tot)+SOM;'
        'var f=fr(SID,OB);if(f){var s=$("start");s.min=f;if(!s.dataset.m||!s.value||s.value<f)s.value=f;$("fr").style.color=f>TD?"#B42318":"#1E7A46";$("fr").textContent=f>TD?T("🔒 Бош эмес. Эң жакынкы бош күн: ","🔒 Занято. Ближайшая свободная дата: ")+fd(f):T("✅ Бош — бүгүндөн баштаса болот","✅ Свободно — можно начать сегодня");}'
        'var on=OB?(oc.querySelector("button.on")||{}).firstChild:null,rn=on?on.textContent:"";'
        'var w=OB?T(rn+" тандаган колдонуучулар гана","Только пользователи, выбравшие «"+rn+"»"):T("Бүт Кыргызстандагы бардык колдонуучулар","Все пользователи Кыргызстана");'
        'w+=SID.charAt(0)==="h"?T(", башкы беттин "+SID.slice(1)+"-баннери",", баннер №"+SID.slice(1)+" на главной"):T(", «"+nm(PG)+"» бөлүмүндө: "+slab(SID),", раздел «"+nm(PG)+"»: "+slab(SID));'
        'pw.innerHTML="<p class=pvw></p><div class=pvc></div>";pw.querySelector(".pvw").textContent=T("Ким көрөт: ","Кто увидит: ")+w+".";'
        'pw.querySelector(".pvc").innerHTML="<div class=pvr><span>1 "+T("жума","нед.")+"</span><span>"+nf(p)+SOM+"</span></div><div class=pvr><span>× "+W+" "+T("жума","нед.")+(W===4?T(" (1 бекер)"," (1 в подарок)"):"")+"</span><span>"+nf(sub)+SOM+"</span></div>"+(ro?"<div class=pvrg><span>−"+ro+"%% "+T("аймак","регион")+"</span><span>−"+nf(sub-tot)+SOM+"</span></div>":"")+"<div class=pvrt><span>"+T("Төлөйсүз","К оплате")+"</span><span>"+nf(tot)+SOM+"</span></div>";}'
        'function apply(){window.TAPSLOT=SID;var k=!SID?"":SID.charAt(0)==="h"?"home":SID.indexOf(":top")>0?"top_sec":"grid_sec";'
        'document.querySelectorAll("input[name=prod]").forEach(function(r){r.checked=(r.value===k);});$("sec").value=PG!=="home"&&SID?PG:"";ob.value=OB;calc();paint();}'
        'function loadAv(){fetch("/reklama/avail?weeks="+W).then(function(r){return r.json();}).then(function(j){if(j&&j.ok){AV=j.s||{};TD=j.today;paint();}}).catch(function(){});}'
        'document.querySelectorAll("#wk button").forEach(function(b){b.addEventListener("click",function(){setTimeout(function(){paint();loadAv();},0);});});'
        '(function(){var imf=$("imf");if(!imf)return;var hint=imf.nextElementSibling,lb=imf.previousElementSibling;'
        'var tg=document.createElement("div");tg.className="wk";tg.style.margin="6px 0 8px";'
        'var bI=document.createElement("button");bI.type="button";bI.className="on";bI.textContent=T("🖼 Сүрөт","🖼 Картинка");'
        'var bV=document.createElement("button");bV.type="button";bV.textContent=T("🎬 Видео (+","🎬 Видео (+")+VP+"%%)";tg.appendChild(bI);tg.appendChild(bV);'
        'lb.parentNode.insertBefore(tg,lb);'
        'var vw=document.createElement("div");vw.style.display="none";'
        'var vl=document.createElement("label");vl.className="l";vl.textContent=T("Видео (5–20 сек.; тик болсо да толук көрүнөт; басканда үнү менен ойнойт)","Видео (5–20 сек.; вертикальное тоже покажется целиком; играет со звуком по нажатию)");'
        'var vf=document.createElement("input");vf.type="file";vf.accept="video/*";vf.className="f";'
        'var vs=document.createElement("div");vs.className="hint";vs.style.fontWeight="700";'
        'var vp=document.createElement("video");vp.controls=true;vp.playsInline=true;vp.className="prev";'
        'vw.appendChild(vl);vw.appendChild(vf);vw.appendChild(vs);vw.appendChild(vp);hint.parentNode.insertBefore(vw,$("imp").nextSibling);'
        'function mode(m){MODE=m;window.TAPVMODE=m;window.TAPVBUSY=0;bI.classList.toggle("on",m==="img");bV.classList.toggle("on",m==="video");'
        'imf.style.display=lb.style.display=hint.style.display=m==="img"?"":"none";$("imp").style.display=(m==="img"&&IMG)?"block":"none";vw.style.display=m==="video"?"block":"none";'
        'IMG="";window.TAPVIDEO="";vp.style.display="none";vp.removeAttribute("src");vs.textContent="";$("imp").style.display="none";imf.value="";vf.value="";paint();}'
        'bI.onclick=function(){mode("img");};bV.onclick=function(){mode("video");};'
        'vf.onchange=function(){var f=vf.files[0];if(!f)return;if(f.size>60*1024*1024){vs.textContent=T("Видео өтө чоң (60 МБ чейин)","Видео слишком большое (до 60 МБ)");return;}'
        'vs.style.color="#4A5A70";IMG="";window.TAPVIDEO="";window.TAPVBUSY=1;vs.textContent=T("⏳ Видео жүктөлүүдө…","⏳ Загрузка видео…");/* VIDBAN2 */'
        'var x=new XMLHttpRequest();x.open("POST","/reklama/video");x.timeout=300000;x.setRequestHeader("Content-Type","application/octet-stream");'
        'x.upload.onprogress=function(e){if(e.lengthComputable){var p=Math.round(e.loaded/e.total*100);vs.textContent=p<100?T("⏳ Видео жүктөлүүдө: ","⏳ Загрузка видео: ")+p+"%%":T("⏳ Видео даярдалууда, 1–2 мүнөт күтүңүз…","⏳ Видео обрабатывается, подождите 1–2 минуты…");}};'
        'function fail(m){window.TAPVBUSY=0;vs.style.color="#B42318";vs.textContent=m;}'
        'x.onload=function(){window.TAPVBUSY=0;var j={};try{j=JSON.parse(x.responseText);}catch(e){}if(j.ok){IMG=j.poster;window.TAPVIDEO=j.video;vp.src="/media/"+j.video;vp.style.display="block";vs.style.color="#1E7A46";vs.textContent=T("✅ Видео даяр","✅ Видео готово");}else{fail(j.msg||T("Ката, кайра аракет кылыңыз (","Ошибка, попробуйте снова (")+x.status+")");}};'
        'x.onerror=function(){fail(T("Байланыш катасы, кайра аракет кылыңыз","Ошибка связи, попробуйте снова"));};'
        'x.ontimeout=function(){fail(T("Убакыт бүттү — кыскараак видео жүктөп көрүңүз","Время истекло — попробуйте видео короче"));};'
        'x.send(f);};})();'
        'drawMap();loadAv();'
        '})();'
        '/* SLOTSUI */'
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
                      "product, weeks, receipt, video FROM banners WHERE status='pending' ORDER BY id",
                      fetch="all") or []
    if not rows:
        return ""
    pn = {p[0]: p[1] for p in PRODUCTS}
    pn.update(slot_labels())   # SLOTS
    out = "<h2>🆕 Төлөм күтүүдө (%d)</h2>" % len(rows)
    for b in rows:
        a = "/admin/banners/act?k=%s&id=%d&a=" % (k, b["id"])
        out += (
            "<div class='bn' id='o%d' style='border-color:#E3A008;scroll-margin-top:70px'><img src='/bimg/%d.jpg?v=o' alt=''>"
            "<div class='ah' style='margin-top:8px'>№%d · %s</div>"
            "<div class='am'>📍 %s%s · %s</div><div class='am'>📅 %s → %s (%s жума)</div>"
            "<div class='am'>💵 <b>%s сом</b> · 👤 %s · ☎️ %s</div>%s%s"
            "<div class='ab'><a href='%spaid' onclick=\"return confirm('Төлөм келдиби? №%d иштетилсинби?')\">✅ Төлөм келди, иштетүү</a>"
            "<a class='del' href='%srej' onclick=\"return confirm('№%d четке кагылсынбы?')\">❌ Четке кагуу</a></div></div>"
        ) % (b["id"], b["id"], b["id"], E(pn.get(b.get("product"), "")),
             E(_name(PLACES, b.get("place"), "")),
             (" · " + E(dict(SECTIONS).get(b.get("section") or "", ""))) if b.get("section") else "",
             E(b.get("oblast") or "Бүт Кыргызстан"), E(b.get("starts") or ""), E(b.get("ends") or ""),
             b.get("weeks") or "?", b.get("price") or "?", E(b.get("title") or "—"), E(b.get("owner") or "—"),
             (("<div class='am'>🔗 %s</div>" % E(b["link"])) if b.get("link") else "") + (("<div class='am'>🎬 Видео:</div><video src='/media/%s' controls playsinline style='width:100%%;border-radius:10px'></video>" % E(b["video"])) if b.get("video") else ""),
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
        + rows + _slot_rows() +
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
        "fetch('/admin/banners/cfg',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({k:'%s',prices:P,caps:C,sprices:(function(){var S={};document.querySelectorAll('.sp').forEach(function(e){S[e.dataset.k]=e.value;});return S;})(),offs:(function(){var O={};document.querySelectorAll('.roff').forEach(function(e){O[e.dataset.k]=e.value;});return O;})(),"
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
    for k, v in (d.get("sprices") or {}).items():   # SLOTS
        v = str(v or "").strip()
        if (k in slot_ids() or k in SEC_PRICES or k == "video_pct") and v.isdigit() and 0 <= int(v) < 10_000_000:
            _cfg_set("sprice_" + k, int(v))
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
    rows = core.query("SELECT place, section, oblast, starts, ends, status, active, created_at, slot "
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


def free_from(product, sec, obl, weeks, _occ=None):
    """Ушул орун ушул мөөнөткө бош болгон эң жакынкы күн (YYYY-MM-DD)."""
    prod = {p[0]: p for p in PRODUCTS}.get(product)
    if not prod:
        return _today()
    cap = caps().get(product, 1)
    sec = sec if prod[4] else ""
    occ = [r for r in (_occupied() if _occ is None else _occ) if _clash(prod[3], sec, obl, r)]
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


# AVAIL: бардык орун/бөлүм/аймактын бош-бош эместиги бир суроо менен
_AVC = {}


def avail(weeks):
    ck = (weeks, _today())
    c = _AVC.get(ck)
    if c and time.time() - c[0] < 20:
        return c[1]
    occ = _occupied()
    obls = [""] + [x for x, _n in _oblasts()]
    secs = [v for v, _n in SECTIONS]
    m = {}
    for p in PRODUCTS:
        ss = secs if p[4] else [""]
        m[p[0]] = {s: {o: free_from(p[0], s, o, weeks, occ) for o in obls} for s in ss}
    _AVC.clear()
    _AVC[ck] = (time.time(), m)
    return m


def avail_api(h, q):
    _ensure()
    try:
        w = int((q.get("weeks") or ["1"])[0])
    except Exception:
        w = 1
    if w not in dict(WEEKS):
        w = 1
    _json(h, {"ok": True, "today": _today(), "m": avail(w), "s": avail_slots(w)})


# ══ SLOTS: ар бир баннер орду өзүнчө сатылат (номерленген орундар) ══════
HOME_N = 13
HOME_PRICES = [1000, 800, 700, 600, 500, 400, 400, 300, 300, 300, 250, 250, 250]
SEC_PRICES = {"top": 500, "g1": 300, "g2": 200}
_SECN = {"top": ("Эң үстү", "Самый верх"),
         "g1": ("1-ара (6-жарыядан кийин)", "1-й (после 6-го объявления)"),
         "g2": ("2-ара (12-жарыядан кийин)", "2-й (после 12-го объявления)")}


def slot_ids():
    out = ["h%d" % i for i in range(1, HOME_N + 1)]
    for code, _n in SECTIONS:
        out += ["%s:%s" % (code, k) for k in ("top", "g1", "g2")]
    return out


def slot_prices():
    c = cfg()
    out = {}
    for i in range(1, HOME_N + 1):
        k = "h%d" % i
        try:
            out[k] = int(c.get("sprice_" + k) or HOME_PRICES[i - 1])
        except Exception:
            out[k] = HOME_PRICES[i - 1]
    base = {}
    for k, v in SEC_PRICES.items():
        try:
            base[k] = int(c.get("sprice_" + k) or v)
        except Exception:
            base[k] = v
    for code, _n in SECTIONS:
        for k in SEC_PRICES:
            out["%s:%s" % (code, k)] = base[k]
    return out, base


def slot_label(sid, ru=False):
    if sid.startswith("h") and sid[1:].isdigit():
        return ("Главная, баннер Б-%s" if ru else "Башкы бет, Б-%s") % sid[1:]
    code, _, k = sid.partition(":")
    nm = dict(SECTIONS).get(code, code)
    return "%s · %s" % (nm, _SECN.get(k, (k, k))[1 if ru else 0])


def slot_labels():
    return {s: slot_label(s) for s in slot_ids()}


def _slot_place(sid):
    if sid.startswith("h"):
        return "home", ""
    code, _, k = sid.partition(":")
    return ("top" if k == "top" else "grid"), code


def slot_free_from(sid, obl, weeks, occ=None):
    occ = _occupied() if occ is None else occ
    rows = [r for r in occ if (r.get("slot") or "") == sid
            and (not obl or not r.get("oblast") or r.get("oblast") == obl)]
    t0 = datetime.strptime(_today(), "%Y-%m-%d")
    span = 7 * max(1, int(weeks or 1))
    if not rows:
        return _today()
    for i in range(0, 400):
        ok = True
        for j in range(span):
            day = (t0 + timedelta(days=i + j)).strftime("%Y-%m-%d")
            if any((r.get("starts") or "0000") <= day <= (r.get("ends") or "9999") for r in rows):
                ok = False
                break
        if ok:
            return (t0 + timedelta(days=i)).strftime("%Y-%m-%d")
    return (t0 + timedelta(days=400)).strftime("%Y-%m-%d")


_SAVC = {}


def avail_slots(weeks):
    ck = (weeks, _today())
    c = _SAVC.get(ck)
    if c and time.time() - c[0] < 20:
        return c[1]
    occ = _occupied()
    obls = [""] + [x for x, _n in _oblasts()]
    m = {s: {o: slot_free_from(s, o, weeks, occ) for o in obls} for s in slot_ids()}
    _SAVC.clear()
    _SAVC[ck] = (time.time(), m)
    return m


def slot_calc(sid, weeks, obl):
    pr, _b = slot_prices()
    p = pr.get(sid)
    mult = dict(WEEKS).get(weeks)
    if p is None or mult is None:
        return None
    total = p * mult
    off = region_offs().get(obl, 0) if obl else 0
    if off:
        total = int(round(total * (100 - off) / 100.0 / 10.0)) * 10
    return total


def _html(b, lang, cls):
    if b.get("video"):   # VIDBAN
        return _vhtml(b, lang, cls)
    lbl = "Реклама" if lang == "ru" else "Жарнама"
    img = ('<img src="/bimg/%d.jpg?v=%s" alt="%s" loading="lazy">'
           % (b["id"], E(str(b.get("updated") or "0")[-8:].replace(":", "")), lbl))
    inner = img + '<span class="adl">%s</span>' % lbl
    if b.get("link"):
        tgt = ("" if str(b.get("link")).startswith("/")
               else ' target="_blank" rel="nofollow sponsored noopener"')
        return '<a class="%s pb" href="/bn/%d"%s>%s</a>' % (cls, b["id"], tgt, inner)
    return '<div class="%s pb">%s</div>' % (cls, inner)


def slot_at(sid, ob=None, lang="ky", cls="hban"):
    # Ушул номерленген орунга сатылган баннер (аймагы дал келгени биринчи).
    try:
        obl = ob or ""
        c = [b for b in _active() if (b.get("slot") or "") == sid
             and (b.get("oblast") or "") in ("", obl)]
        if not c:
            return ""
        c.sort(key=lambda b: (0 if (b.get("oblast") or "") == obl and obl else 1, b["id"]))
        b = c[0]
        _count(b["id"])
        return _html(b, lang, cls)
    except Exception as e:
        print("banners slot_at:", e, flush=True)
        return ""


def slots_js(lang="ky"):
    ru = lang == "ru"
    pr, base = slot_prices()
    d = {"home": [["h%d" % i, pr["h%d" % i]] for i in range(1, HOME_N + 1)],
         "sec": base,
         "names": [[c, n] for c, n in SECTIONS], "vpct": video_pct()}
    try:
        _sr = {"trade": "Торговля", "wholesale": "Оптовая торговля", "property": "Продажа недвижимости",
               "vehicle": "Продажа транспорта", "service": "Услуги", "rental": "Аренда",
               "delivery": "Доставка", "cargo": "Грузоперевозки", "jobseek": "Поиск работы",
               "job": "Работа", "markets": "Рынки", "malls": "Торговые центры", "taxi": "Такси"}
        if ru:
            d["names"] = [[c, _sr.get(c, n)] for c, n in SECTIONS]
    except Exception:
        pass
    return "<script>window.TAPSLOTS=%s;</script>" % json.dumps(d, ensure_ascii=False)


def _slot_rows():
    pr, base = slot_prices()
    out = "<div class='ah' style='margin-top:14px'>Номерленген орундардын баасы (сом/жума)</div>"
    for i in range(1, HOME_N + 1):
        out += ("<label>Башкы бет Б-%d</label><input class='sp' data-k='h%d' inputmode='numeric' value='%d'>"
                % (i, i, pr["h%d" % i]))
    for k, v in base.items():
        out += ("<label>Ар бир бөлүм: %s</label><input class='sp' data-k='%s' inputmode='numeric' value='%d'>"
                % (E(_SECN[k][0]), k, v))
    out += ("<label>Видео баннер үстөк баасы, %%%%</label><input class='sp' data-k='video_pct' "
            "inputmode='numeric' value='%d'>" % video_pct())   # VIDBAN
    return out


def _order_slot(h, d, ru, ip, hits, now):
    sid = str(d.get("slot") or "")
    t = lambda a, b: b if ru else a
    if sid not in slot_ids():
        return _json(h, {"ok": False, "msg": t("Орунду тандаңыз", "Выберите место")})
    try:
        weeks = int(d.get("weeks") or 0)
    except Exception:
        weeks = 0
    if weeks not in dict(WEEKS):
        return _json(h, {"ok": False, "msg": t("Мөөнөттү тандаңыз", "Выберите срок")})
    obl = str(d.get("oblast") or "")
    if obl and obl not in [x for x, _ in _oblasts()]:
        obl = ""
    img = _jpeg(d.get("img"))
    if not img:
        return _json(h, {"ok": False, "msg": t("Баннердин сүрөтүн жүктөңүз", "Загрузите изображение баннера")})
    phone = "".join(ch for ch in str(d.get("phone") or "") if ch.isdigit() or ch == "+")[:16]
    if len(phone.replace("+", "")) < 9:
        return _json(h, {"ok": False, "msg": t("Телефон номериңизди жазыңыз", "Укажите номер телефона")})
    link = str(d.get("link") or "").strip()[:500]
    if link and not _safe_link(link):
        link = ("https://" + link.lstrip("/")) if "." in link else ""
    c = cfg()
    rec = _jpeg(d.get("receipt"))
    if c.get("mbank") and not rec:
        return _json(h, {"ok": False, "msg": t("Төлөм чегинин сүрөтүн жүктөңүз", "Загрузите фото чека об оплате")})
    start = _date(d.get("start")) or _today()
    if start < _today():
        start = _today()
    ff = slot_free_from(sid, obl, weeks)
    if start < ff:
        return _json(h, {"ok": False, "msg": t("Бул орун тандалган күндөрү бош эмес. Эң жакынкы бош күн: %s." % _fdate(ff, False),
                                               "На выбранные даты место занято. Ближайшая свободная дата: %s." % _fdate(ff, True))})
    vid = str(d.get("video") or "")   # VIDBAN
    if vid and not _video_ok(vid):
        return _json(h, {"ok": False, "msg": t("Видео табылган жок, кайра жүктөңүз", "Видео не найдено, загрузите снова")})
    _pr, _b = slot_prices()
    total = _pr[sid] * dict(WEEKS)[weeks]
    if vid:
        total = int(round(total * (100 + video_pct()) / 100.0 / 10.0)) * 10
    _off = region_offs().get(obl, 0) if obl else 0
    if _off:
        total = int(round(total * (100 - _off) / 100.0 / 10.0)) * 10
    end = (datetime.strptime(start, "%Y-%m-%d") + timedelta(days=7 * weeks - 1)).strftime("%Y-%m-%d")
    place, sec = _slot_place(sid)
    title = str(d.get("name") or "").strip()[:120]
    bid = core.query(
        "INSERT INTO banners (place, section, oblast, link, title, owner, starts, ends, updated, img, "
        "active, shows, clicks, created_at, status, price, receipt, product, weeks, slot, video) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,0,0,0,?,?,?,?,?,?,?,?)",
        (place, sec, obl, link, title, phone, start, end, core.now_str(), img,
         core.now_str(), "pending", total, rec or "", sid, weeks, sid, vid), fetch="id")
    _RATE[ip] = hits + [now]
    _SAVC.clear()
    site = (__import__("os").environ.get("SITE_URL") or "https://tapmeni.up.railway.app").rstrip("/")
    _notify("💰 <b>Жаңы баннер буйрутмасы №%s</b>\n\n📍 %s%s\n📅 %s → %s (%d жума)\n💵 %s сом%s\n"
            "👤 %s\n☎️ %s\n\n🛠 <a href=\"%s\">Админде текшерүү</a>"
            % (bid, E(slot_label(sid)), (" · " + E(obl)) if obl else "", start, end, weeks, total,
               " · чек жүктөлдү" if rec else "", E(title or "—"), E(phone), "%s/admin/banners?pg=%s#o%s" % (site, "home" if sid.startswith("h") else sid.split(":")[0], bid)))
    msg = t("Буйрутма №%s кабыл алынды. Админ төлөмдү текшерип, баннериңизди иштетет — "
            "адатта бир нече сааттын ичинде." % bid,
            "Заказ №%s принят. Администратор проверит оплату и запустит баннер — "
            "обычно в течение нескольких часов." % bid)
    _json(h, {"ok": True, "msg": msg, "id": bid})


# ══ SLOTMAP: админде номерленген орундардын картасы ══════════════════
def _slotmap(q):
    try:
        _ensure()
        pg = (q.get("pg") or ["home"])[0]
        codes = [c for c, _n in SECTIONS]
        if pg != "home" and pg not in codes:
            pg = "home"
        d = _today()
        rows = core.query("SELECT id, slot, oblast, title, owner, starts, ends, status, active, price, "
                          "shows, clicks, created_at FROM banners WHERE slot IS NOT NULL AND slot<>'' "
                          "AND status IN ('pending','paid')", fetch="all") or []
        rows = [r for r in rows if r.get("status") == "pending"
                or (int(r.get("active") or 0) == 1 and (r.get("ends") or "9999") >= d)]
        by = {}
        for r in rows:
            by.setdefault(r["slot"], []).append(r)
        ids = slot_ids()
        n_free = sum(1 for s in ids if s not in by)
        n_pend = sum(1 for r in rows if r.get("status") == "pending")
        n_paid = sum(1 for r in rows if r.get("status") == "paid")
        month = d[:7]
        try:
            allp = core.query("SELECT price, created_at FROM banners WHERE status='paid'", fetch="all") or []
            rev = sum(int(r.get("price") or 0) for r in allp if str(r.get("created_at") or "")[:7] == month)
        except Exception:
            rev = 0

        def pcount(page):
            return sum(1 for r in rows if r.get("status") == "pending"
                       and ((page == "home" and r["slot"].startswith("h"))
                            or r["slot"].startswith(page + ":")))

        css = ("<style>.smx{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin:6px 0 10px}"
               ".smx div{border-radius:12px;padding:8px 4px;text-align:center;font-size:12px;font-weight:700}"
               ".smx b{display:block;font-size:19px}.smf{background:#E9F8EF;color:#155B33}"
               ".smp{background:#FFF4CC;color:#7A4B00}.smd{background:#E8F0FE;color:#17407A}"
               ".smr{background:#F1F4F8;color:#33425A}"
               ".pgc{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}"
               ".pgc a{font-size:13px;font-weight:700;padding:6px 11px;border-radius:99px;border:1.5px solid #C9D4E3;"
               "color:#17304F;text-decoration:none;background:#fff}.pgc a.on{background:#1E4FA8;border-color:#1E4FA8;color:#fff}"
               ".pgc em{font-style:normal;background:#F2C230;color:#3A2A00;border-radius:99px;padding:0 6px;margin-left:5px;font-size:11px}"
               ".smap{border:1.5px solid #C9D4E3;border-radius:16px;padding:8px;background:#F6F8FC;margin-bottom:14px}"
               ".smr2{font-size:12px;color:#8A97AA;padding:3px 8px}"
               ".scd{border-radius:12px;padding:9px 11px;margin:5px 0;font-size:13px;display:flex;justify-content:space-between;gap:10px}"
               ".scd>b{font-size:15px;white-space:nowrap}.scd .ln{text-align:right;line-height:1.45}"
               ".scd.f{background:#E9F8EF;color:#155B33}.scd.p{background:#FFF4CC;color:#7A4B00;border:2px solid #E3A008}"
               ".scd.d{background:#E8F0FE;color:#17407A}.scd a{color:inherit;font-weight:800}</style>")
        out = css + "<h2>🗺 Орундар картасы</h2>"
        out += ("<div class='smx'><div class='smf'><b>%d</b>Бош</div><div class='smp'><b>%d</b>Заявка</div>"
                "<div class='smd'><b>%d</b>Сатылган</div><div class='smr'><b>%s</b>сом / ай</div></div>"
                % (n_free, n_pend, n_paid, "{:,}".format(rev).replace(",", " ")))
        chips = [("home", "Башкы бет")] + [(c, n) for c, n in SECTIONS]
        out += "<div class='pgc'>" + "".join(
            "<a href='/admin/banners?pg=%s'%s>%s%s</a>"
            % (c, " class='on'" if c == pg else "", E(n), ("<em>%d</em>" % pcount(c)) if pcount(c) else "")
            for c, n in chips) + "</div>"

        def card(sid, label):
            es = by.get(sid, [])
            pend = [r for r in es if r.get("status") == "pending"]
            paid = [r for r in es if r.get("status") == "paid"]
            cls = "p" if pend else ("d" if paid else "f")
            lines = []
            for r in paid:
                lines.append("✅ %s · %s · %s–%s · 👁 %d · 👆 %d"
                             % (E(r.get("title") or r.get("owner") or "—"), E(r.get("oblast") or "Бүт КР"),
                                E(_fdate(r.get("starts") or "", False)), E(_fdate(r.get("ends") or "", False)),
                                int(r.get("shows") or 0), int(r.get("clicks") or 0)))
            for r in pend:
                lines.append("🆕 Заявка <a href='#o%d'>№%d</a> · %s · %s сом · <a href='#o%d'>Чекти көрүү ›</a>"
                             % (r["id"], r["id"], E(r.get("oblast") or "Бүт КР"), r.get("price") or "?", r["id"]))
            if es and any(not (r.get("oblast") or "") for r in es):
                pass
            elif es:
                lines.append("🟢 Калган аймактар бош")
            return ("<div class='scd %s'><b>%s</b><div class='ln'>%s</div></div>"
                    % (cls, E(label), "<br>".join(lines) if lines else "бош"))

        out += "<div class='smap'>"
        if pg == "home":
            for i in range(1, HOME_N + 1):
                out += "<div class='smr2'>%d-бөлүм · 4 жарыя</div>" % i
                out += card("h%d" % i, "Б-%d" % i)
        else:
            out += "<div class='smr2'>«%s» бөлүмү</div>" % E(dict(SECTIONS).get(pg, pg))
            out += card(pg + ":top", "Эң үстү")
            out += "<div class='smr2'>6 жарыя</div>" + card(pg + ":g1", "1-ара")
            out += "<div class='smr2'>6 жарыя</div>" + card(pg + ":g2", "2-ара")
        out += "</div>"
        return out
    except Exception as e:
        print("slotmap:", e, flush=True)
        return ""


# ══ VIDBAN: видео баннер (басканда үнү менен ойнойт) ═══════════════════
_VRATE = {}


def video_pct():
    try:
        return max(0, int(cfg().get("sprice_video_pct") or 50))
    except Exception:
        return 50


def upload_video(h):
    import os
    import re as _re
    import secrets
    import subprocess
    try:
        import vidopt
        ff = vidopt.ffmpeg()
    except Exception:
        ff = None
    ip = (h.headers.get("X-Forwarded-For") or h.client_address[0] or "").split(",")[0].strip()
    now = time.time()
    hits = [x for x in _VRATE.get(ip, []) if now - x < 3600]
    if len(hits) >= 10:
        return _json(h, {"ok": False, "msg": "Өтө көп аракет / Слишком много попыток"})
    n = int(h.headers.get("Content-Length") or 0)
    if not 0 < n <= 60 * 1024 * 1024:
        try:
            h.rfile.read(n) if 0 < n < 200 * 1024 * 1024 else None
        except Exception:
            pass
        return _json(h, {"ok": False, "msg": "Видео 60 МБ чейин болсун / Видео до 60 МБ"})
    raw = h.rfile.read(n)
    if raw[4:8] != b"ftyp":
        return _json(h, {"ok": False, "msg": "MP4/MOV видео гана / Только видео MP4/MOV"})
    if not ff:
        return _json(h, {"ok": False, "msg": "Сервер видеону иштете албайт / Сервер не может обработать видео"})
    _VRATE[ip] = hits + [now]
    media = core.MEDIA
    os.makedirs(media, exist_ok=True)
    tag = secrets.token_hex(5)
    src = os.path.join(media, "bnv_%s.src" % tag)
    out = os.path.join(media, "bnv_%s.mp4" % tag)
    pst = os.path.join(media, "bnv_%s.jpg" % tag)
    with open(src, "wb") as f:
        f.write(raw)
    try:
        r = subprocess.run([ff, "-y", "-v", "error", "-i", src, "-t", "20",
                            "-vf", "split=2[a][b];[a]scale=1280:640:force_original_aspect_ratio=increase,crop=1280:640,boxblur=20:2,eq=brightness=-0.08[bg];[b]scale=1280:640:force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1",   # VIDFIT: видео кесилбейт, капталдары бүдөмүк
                            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-movflags", "+faststart", out],
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=240)
        ok = r.returncode == 0 and os.path.isfile(out)
        if ok:
            subprocess.run([ff, "-y", "-v", "error", "-ss", "0.5", "-i", out, "-frames:v", "1",
                            "-q:v", "3", pst], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=60)
            if not os.path.isfile(pst):
                subprocess.run([ff, "-y", "-v", "error", "-i", out, "-frames:v", "1", "-q:v", "3", pst],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    except Exception as e:
        print("upload_video:", e, flush=True)
        ok = False
    if ok:   # VIDFULL: толук экран үчүн түп форматтагы нуска
        try:
            subprocess.run([ff, "-y", "-v", "error", "-i", src, "-t", "20",
                            "-vf", "scale=1280:1280:force_original_aspect_ratio=decrease,"
                                   "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "27", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-movflags", "+faststart",
                            os.path.join(media, "bnv_%s_f.mp4" % tag)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=240)
        except Exception as e:
            print("upload_video full:", e, flush=True)
    try:
        os.remove(src)
    except Exception:
        pass
    if not ok or not os.path.isfile(pst):
        return _json(h, {"ok": False, "msg": "Видеону иштетүү мүмкүн болбоду / Не удалось обработать видео"})
    with open(pst, "rb") as f:
        poster = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
    try:
        os.remove(pst)
    except Exception:
        pass
    _json(h, {"ok": True, "video": "bnv_%s.mp4" % tag, "poster": poster})


def _video_ok(name):
    import os
    import re as _re
    return bool(name and _re.match(r"^bnv_[0-9a-f]{10}\.mp4$", name)
                and os.path.isfile(os.path.join(core.MEDIA, name)))


def _vhtml(b, lang, cls):
    ru = lang == "ru"
    lbl = "Реклама" if ru else "Жарнама"
    v = E(b.get("video") or "")
    more = ""
    if b.get("link"):
        tgt = ("" if str(b.get("link")).startswith("/")
               else ' target="_blank" rel="nofollow sponsored noopener"')
        more = '<a class="vmore" href="/bn/%d"%s>%s</a>' % (b["id"], tgt, "Подробнее ›" if ru else "Кененирээк ›")
    return ('<div class="%s pb vb" data-v="/media/%s" data-f="%s"><img src="/bimg/%d.jpg?v=%s" alt="%s" loading="lazy">'
            '<span class="adl">%s</span><button class="vpl" type="button" aria-label="play">▶</button>%s</div>'
            % (cls, v, _vfull(b.get("video")), b["id"], E(str(b.get("updated") or "0")[-8:].replace(":", "")), lbl, lbl, more))


def _vfull(name):   # VIDFULL
    import os
    f = str(name or "").replace(".mp4", "_f.mp4")
    return E("/media/" + f) if f and os.path.isfile(os.path.join(core.MEDIA, f)) else ""
