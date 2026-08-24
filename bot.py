#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAP! — Telegram бот. КОШУМЧА КИТЕПКАНА КЕРЕК ЭМЕС.

Иштетүү:
    1) Токенди жаз:  echo "СЕНИН_ТОКЕНИҢ" > token.txt
    2) Ботту иштет:  python bot.py

Бот tap.py менен бир эле базаны колдонот (tap.db).
Ботко коюлган жарыя сайтта дароо көрүнөт.
"""

import json, os, sqlite3, time, urllib.parse, urllib.request, mimetypes
import ssl

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "tap.db")
MEDIA = os.path.join(BASE, "media")
TOKEN_FILE = os.path.join(BASE, "token.txt")
STATE_FILE = os.path.join(BASE, "bot_state.json")

# Сайттын дареги. Интернетке чыгаргандан кийин бул жерди өз доменине алмаштыр.
SITE_URL = os.environ.get("SITE_URL", "http://localhost:8000")

CATS = {
    "transport": ("Транспорт", "🚗"),
    "realty":    ("Кыймылсыз мүлк", "🏠"),
    "personal":  ("Жеке буюмдар", "👕"),
    "service":   ("Кызматтар", "🔧"),
    "shop":      ("Магазиндер", "🛍"),
    "business":  ("Бизнес", "🤝"),
}


# ---- Латын / кириллица издөө ----
# Кыргызстанда "батир" деп да, "batir" деп да жазышат.
# Ошондуктан ар бир жарыянын латынча жазылышын да сактайбыз,
# издөөдө болсо суроону эки формада тең текшеребиз.

_TR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "ң": "ng", "о": "o", "ө": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "у": "u", "ү": "u", "ф": "f", "х": "h", "ц": "c", "ч": "ch",
    "ш": "sh", "щ": "sh", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
    "я": "ya",
}

# Латынча жазуунун ар кандай варианттарын бир формага келтирүү:
# jantyk / zhantyk, han / khan, cai / tsai — баары бир болуп калсын.

def translit(s):
    """Кириллицаны латынга которот. Латын тамгалар тийбейт."""
    return "".join(_TR.get(ch, ch) for ch in (s or "").lower())


def fold(s):
    """Латынча жазуунун варианттарын бир формага келтирет."""
    s = (s or "").lower()
    # ch/sh убактылуу белгиге — алардын ичиндеги тамгалар өзгөрбөш үчүн
    s = s.replace("ch", "\x01").replace("sh", "\x02")
    for a, b in (("zh", "j"), ("kh", "h"), ("ts", "k"), ("c", "k"),
                 ("yo", "o"), ("yu", "u"), ("ya", "a"), ("ye", "e"),
                 ("q", "k"), ("w", "v"), ("x", "ks"), ("y", "i")):
        s = s.replace(a, b)
    s = s.replace("\x01", "ch").replace("\x02", "sh")
    # Кайталанган тамгаларды бирге түшүрөбүз: donggolok -> dongolok
    out = []
    for ch in s:
        if not out or out[-1] != ch:
            out.append(ch)
    return "".join(out)


def norm(s):
    """Издөө үчүн бир формага келтирилген текст."""
    return fold(translit(s))

# Кыргызча-орусча синонимдер. Киши "квартира" деп издейт,
# жарыяда "батир" деп жазылган болушу мүмкүн — экөө тең табылсын.
SYNS = [
    ["батир", "квартира"],
    ["там", "үй", "дом"],
    ["унаа", "машина", "авто", "автомобиль"],
    ["телефон", "смартфон"],
    ["дөңгөлөк", "резина", "шина", "колесо"],
    ["эмерек", "мебель"],
    ["кийим", "одежда"],
    ["жер", "участок"],
    ["иш", "жумуш", "работа", "вакансия"],
    ["ижара", "аренда", "арендага"],
    ["сатылат", "продается", "продам"],
    ["компьютер", "ноутбук", "комп"],
    ["курулуш", "стройка", "ремонт", "оңдоо"],
]


def expand(text):
    """Тексттеги сөздөрдүн синонимдерин кошуп берет."""
    low = (text or "").lower()
    extra = []
    for group in SYNS:
        if any(w in low for w in group):
            extra += group
    return " ".join(extra)


# Категориянын ичиндеги түрлөр.
# Бул издөө үчүн эң маанилүү: эч ким жарыясына "телефон" деп жазбайт,
# "Redmi Note 13" деп жазат. Түр тандалганда ошол сөз жарыяга байланат.
SUBS = {
    "transport": [("car", "Унаа"), ("parts", "Унаа тетиктери"), ("tire", "Дөңгөлөк"),
                  ("moto", "Мотоцикл, велосипед"), ("truck", "Жүк техникасы")],
    "realty":    [("flat", "Батир"), ("house", "Там, үй"), ("land", "Жер участок"),
                  ("commerce", "Коммерциялык жай"), ("rent", "Ижарага")],
    "personal":  [("phone", "Телефон"), ("comp", "Компьютер, ноутбук"),
                  ("cloth", "Кийим-кече"), ("furn", "Эмерек"),
                  ("tech", "Тиричилик техникасы"), ("kids", "Балдар буюмдары"),
                  ("other", "Башка")],
    "service":   [("build", "Оңдоо, курулуш"), ("transport", "Ташуу кызматы"),
                  ("repair", "Техника оңдоо"), ("beauty", "Сулуулук, саламаттык"),
                  ("teach", "Окутуу"), ("other", "Башка")],
    "shop":      [("food", "Азык-түлүк"), ("cloth", "Кийим дүкөнү"),
                  ("tech", "Техника дүкөнү"), ("build", "Курулуш материалдары"),
                  ("other", "Башка")],
    "business":  [("ready", "Даяр бизнес"), ("equip", "Жабдуу"),
                  ("partner", "Өнөктөштүк"), ("other", "Башка")],
}


def sub_title(cat, code):
    for c, n in SUBS.get(cat, []):
        if c == code:
            return n
    return ""

REGIONS = ["Жалал-Абад облусу", "Ош облусу", "Баткен облусу", "Чүй облусу",
           "Ысык-Көл облусу", "Нарын облусу", "Талас облусу", "Бишкек", "Ош шаары"]

PER_PAGE = 5   # издөөдө бир жолу канча жарыя көрсөтүлөт

_ctx = ssl.create_default_context()


# ==================== Telegram API ====================

def token():
    if os.path.exists(TOKEN_FILE):
        t = open(TOKEN_FILE, encoding="utf-8").read().strip()
        if t:
            return t
    t = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not t:
        raise SystemExit(
            "\nТокен табылган жок!\n"
            "Мындай кыл:  echo \"СЕНИН_ТОКЕНИҢ\" > token.txt\n")
    return t


TOKEN = None
API = None


def api(method, **params):
    """Telegram API'ге кайрылуу."""
    data = urllib.parse.urlencode(
        {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
         for k, v in params.items() if v is not None}).encode()
    req = urllib.request.Request(API + method, data=data)
    try:
        with urllib.request.urlopen(req, timeout=70, context=_ctx) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("  API катасы:", method, e)
        return {"ok": False}


def send(chat, text, kb=None, preview=False):
    return api("sendMessage", chat_id=chat, text=text, parse_mode="HTML",
               disable_web_page_preview=not preview,
               reply_markup=kb)


def send_photo(chat, path, caption, kb=None):
    """Сүрөттү multipart менен жөнөтөт."""
    if not os.path.isfile(path):
        return send(chat, caption, kb)
    bnd = "----TAPBOUNDARY7391"
    parts = []

    def field(name, value):
        parts.append(f"--{bnd}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n"
                     f"{value}\r\n".encode())

    field("chat_id", chat)
    field("caption", caption)
    field("parse_mode", "HTML")
    if kb:
        field("reply_markup", json.dumps(kb, ensure_ascii=False))

    ctype = mimetypes.guess_type(path)[0] or "image/jpeg"
    parts.append(
        f"--{bnd}\r\nContent-Disposition: form-data; name=\"photo\"; "
        f"filename=\"{os.path.basename(path)}\"\r\nContent-Type: {ctype}\r\n\r\n".encode())
    parts.append(open(path, "rb").read())
    parts.append(f"\r\n--{bnd}--\r\n".encode())

    body = b"".join(parts)
    req = urllib.request.Request(API + "sendPhoto", data=body)
    req.add_header("Content-Type", f"multipart/form-data; boundary={bnd}")
    try:
        with urllib.request.urlopen(req, timeout=90, context=_ctx) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("  Сүрөт жөнөтүлбөдү:", e)
        return send(chat, caption, kb)


def download_photo(file_id, dest):
    """Telegram'дан сүрөттү жүктөп алат."""
    r = api("getFile", file_id=file_id)
    if not r.get("ok"):
        return False
    path = r["result"]["file_path"]
    url = f"https://api.telegram.org/file/bot{TOKEN}/{path}"
    try:
        with urllib.request.urlopen(url, timeout=90, context=_ctx) as resp:
            data = resp.read()
        os.makedirs(MEDIA, exist_ok=True)
        open(dest, "wb").write(data)
        return True
    except Exception as e:
        print("  Сүрөт жүктөлбөдү:", e)
        return False


# ==================== База ====================

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL, region TEXT, title TEXT NOT NULL,
            description TEXT, price TEXT, contact TEXT,
            photo TEXT, tg_id TEXT, tg_name TEXT, stext TEXT, subcat TEXT,
            views INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')))""")
        have = {r[1] for r in c.execute("PRAGMA table_info(listings)")}
        for col in ("photo", "tg_id", "tg_name", "stext", "subcat"):
            if col not in have:
                c.execute(f"ALTER TABLE listings ADD COLUMN {col} TEXT")
        # Эски жазуулардын издөө талаасын толтуруу
        for r in c.execute("SELECT id,title,description FROM listings "
                           "WHERE stext IS NULL").fetchall():
            c.execute("UPDATE listings SET stext=? WHERE id=?",
                      (mkstext(r["title"], r["description"]), r["id"]))
    os.makedirs(MEDIA, exist_ok=True)


def mkstext(title, desc, sub_name=""):
    """Издөө үчүн кичине тамгага айландырылган текст.
    SQLite'тын LIKE'ы кириллицада чоң-кичине тамганы айырмалайт,
    ошондуктан издөөнү ушул талаа боюнча жүргүзөбүз."""
    raw = f"{title or ''} {desc or ''} {sub_name or ''}".lower()
    raw = raw + " " + expand(raw)            # синонимдер
    return raw + " " + norm(raw)             # + латынча жазылышы


def add_listing(d, tg_id, tg_name):
    with conn() as c:
        cur = c.execute(
            """INSERT INTO listings
               (category,subcat,title,price,region,description,contact,tg_id,tg_name,stext)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (d["category"], d.get("subcat"), d["title"], d.get("price", ""),
             d.get("region", ""), d.get("description", ""), d.get("contact", ""),
             str(tg_id), tg_name,
             mkstext(d["title"], d.get("description", ""),
                     sub_title(d["category"], d.get("subcat")))))
        return cur.lastrowid


def set_photo(lid, name):
    with conn() as c:
        c.execute("UPDATE listings SET photo=? WHERE id=?", (name, lid))


def find(q=None, cat=None, region=None, sub=None, limit=PER_PAGE, offset=0):
    sql = "SELECT * FROM listings WHERE is_active=1"
    p = []
    if cat:
        sql += " AND category=?"; p.append(cat)
    if sub:
        sql += " AND subcat=?"; p.append(sub)
    if region:
        sql += " AND region=?"; p.append(region)
    if q:
        sql += " AND (stext LIKE ? OR stext LIKE ?)"
        p += [f"%{q.lower()}%", f"%{norm(q)}%"]
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    p += [limit, offset]
    with conn() as c:
        return [dict(r) for r in c.execute(sql, p)]


def count(q=None, cat=None, region=None, sub=None):
    sql = "SELECT COUNT(*) n FROM listings WHERE is_active=1"
    p = []
    if cat:
        sql += " AND category=?"; p.append(cat)
    if sub:
        sql += " AND subcat=?"; p.append(sub)
    if region:
        sql += " AND region=?"; p.append(region)
    if q:
        sql += " AND (stext LIKE ? OR stext LIKE ?)"
        p += [f"%{q.lower()}%", f"%{norm(q)}%"]
    with conn() as c:
        return c.execute(sql, p).fetchone()["n"]


def used_regions():
    """Базада чындап жарыясы бар аймактар."""
    with conn() as c:
        return [r["region"] for r in c.execute(
            "SELECT region, COUNT(*) n FROM listings WHERE is_active=1 "
            "AND region IS NOT NULL AND region<>'' GROUP BY region ORDER BY n DESC")]


def my_listings(tg_id):
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM listings WHERE tg_id=? ORDER BY id DESC", (str(tg_id),))]


def deactivate(lid, tg_id):
    with conn() as c:
        cur = c.execute("UPDATE listings SET is_active=0 WHERE id=? AND tg_id=?",
                        (lid, str(tg_id)))
        return cur.rowcount > 0


# ==================== Абалдарды сактоо ====================

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE, encoding="utf-8"))
        except Exception:
            pass
    return {"offset": 0, "users": {}}


def save_state(st):
    tmp = STATE_FILE + ".tmp"
    json.dump(st, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, STATE_FILE)


# ==================== Баскычтар ====================

MENU = {"keyboard": [
    [{"text": "📢 Жарыя берем"}, {"text": "🔍 Издеймин"}],
    [{"text": "📋 Менин жарыяларым"}]],
    "resize_keyboard": True}

SKIP = {"keyboard": [[{"text": "⏭ Өткөрүү"}], [{"text": "❌ Жокко чыгаруу"}]],
        "resize_keyboard": True}

CANCEL = {"keyboard": [[{"text": "❌ Жокко чыгаруу"}]], "resize_keyboard": True}


def cat_kb(prefix, with_all=False):
    rows = []
    if with_all:
        rows.append([{"text": "🔎 Бардыгы", "callback_data": f"{prefix}:all"}])
    items = list(CATS.items())
    for i in range(0, len(items), 2):
        row = [{"text": f"{ic} {nm}", "callback_data": f"{prefix}:{code}"}
               for code, (nm, ic) in items[i:i + 2]]
        rows.append(row)
    return {"inline_keyboard": rows}


def sub_kb(cat, prefix, with_all=False):
    """Категориянын ичиндеги түрлөр."""
    rows = []
    if with_all:
        rows.append([{"text": "🔎 Бардыгы", "callback_data": f"{prefix}:all"}])
    items = SUBS.get(cat, [])
    for i in range(0, len(items), 2):
        rows.append([{"text": nm, "callback_data": f"{prefix}:{c}"}
                     for c, nm in items[i:i + 2]])
    return {"inline_keyboard": rows}


def region_kb():
    rows, row = [], []
    for r in REGIONS:
        row.append({"text": r})
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([{"text": "❌ Жокко чыгаруу"}])
    return {"keyboard": rows, "resize_keyboard": True}


def find_region_kb():
    """Издөөдө аймак тандоо. Базада жарыясы бар аймактар гана."""
    used = used_regions()
    rows = [[{"text": "🌍 Бүт Кыргызстан", "callback_data": "fr:all"}]]
    row = []
    for i, rg in enumerate(used):
        row.append({"text": rg, "callback_data": f"fr:{i}"})
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    return {"inline_keyboard": rows}


def phone_kb():
    return {"keyboard": [[{"text": "📱 Номеримди жиберүү", "request_contact": True}],
                         [{"text": "❌ Жокко чыгаруу"}]],
            "resize_keyboard": True}


# ==================== Жарыяны форматтоо ====================

def fmt(r):
    nm, ic = CATS.get(r["category"], ("—", ""))
    sn = sub_title(r["category"], r.get("subcat"))
    price = (r["price"] or "").strip() or "Келишимдүү"
    lines = [f"<b>{esc(r['title'])}</b>",
             f"💰 {esc(price)}",
             f"{ic} {esc(sn or nm)}   📍 {esc(r['region'] or '—')}"]
    if r.get("description"):
        d = r["description"]
        lines.append("\n" + esc(d[:300] + ("…" if len(d) > 300 else "")))
    if r.get("contact"):
        lines.append(f"\n☎️ {esc(r['contact'])}")
    lines.append(f"\n🌐 {SITE_URL}/e/{r['id']}")
    return "\n".join(lines)


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def show_results(chat, rows, total, shown):
    for r in rows:
        photo = os.path.join(MEDIA, r["photo"]) if r.get("photo") else None
        if photo and os.path.isfile(photo):
            send_photo(chat, photo, fmt(r))
        else:
            send(chat, fmt(r))
    if shown < total:
        send(chat, f"Дагы {total - shown} жарыя бар.",
             {"inline_keyboard": [[{"text": "⬇️ Дагы көрсөт",
                                    "callback_data": f"more:{shown}"}]]})
    else:
        send(chat, "Баары ушул.", MENU)


# ==================== Негизги логика ====================

def handle_message(msg, st):
    chat = msg["chat"]["id"]
    uid = str(msg["from"]["id"])
    name = msg["from"].get("first_name", "")
    users = st["users"]
    u = users.setdefault(uid, {"step": None, "data": {}})
    text = (msg.get("text") or "").strip()

    # --- сүрөт келсе ---
    if msg.get("photo") and u["step"] == "photo":
        u["data"]["photo_file_id"] = msg["photo"][-1]["file_id"]
        u["step"] = "contact"
        send(chat, "<b>6/6</b> Байланыш телефонуңузду жазыңыз:\n"
                   "<i>мисалы: +996700123456</i>", phone_kb())
        return

    # --- контакт келсе ---
    if msg.get("contact") and u["step"] == "contact":
        text = msg["contact"].get("phone_number", "")

    # --- жокко чыгаруу ---
    if text in ("❌ Жокко чыгаруу", "/cancel"):
        u["step"] = None; u["data"] = {}
        send(chat, "Жокко чыгарылды.", MENU)
        return

    # --- /start ---
    if text in ("/start", "/help"):
        u["step"] = None; u["data"] = {}
        send(chat, "Салам! Бул <b>TAP!</b> — жарыя ботту.\n\n"
                   "📢 Жарыя койсоңуз, ал дароо жарыяланат\n"
                   "🔍 Керектүү нерсени издей аласыз\n\n"
                   "Төмөнкү менюдан тандаңыз 👇", MENU)
        return

    # ---------- Жарыя берүү ----------
    if text == "📢 Жарыя берем":
        u["step"] = "category"; u["data"] = {}
        send(chat, "Категорияны тандаңыз:", cat_kb("nc"))
        return

    if u["step"] == "title":
        if len(text) < 3:
            send(chat, "Аталышы өтө кыска. Кайра жазыңыз:")
            return
        u["data"]["title"] = text[:200]
        u["step"] = "price"
        send(chat, "<b>2/6</b> Баасы канча?\n"
                   "<i>мисалы: 5000 сом. Баасы жок болсо «Өткөрүү» басыңыз</i>", SKIP)
        return

    if u["step"] == "price":
        u["data"]["price"] = "" if text == "⏭ Өткөрүү" else text[:60]
        u["step"] = "region"
        send(chat, "<b>3/6</b> Кайсы аймактасыз?", region_kb())
        return

    if u["step"] == "region":
        u["data"]["region"] = text[:80]
        u["step"] = "description"
        send(chat, "<b>4/6</b> Кыскача сүрөттөмө жазыңыз:", SKIP)
        return

    if u["step"] == "description":
        u["data"]["description"] = "" if text == "⏭ Өткөрүү" else text[:2000]
        u["step"] = "photo"
        send(chat, "<b>5/6</b> Сүрөт жөнөтүңүз.\n"
                   "<i>Сүрөтү бар жарыя алда канча көп көрүлөт.</i>", SKIP)
        return

    if u["step"] == "photo":
        u["data"]["photo_file_id"] = None
        u["step"] = "contact"
        send(chat, "<b>6/6</b> Байланыш телефонуңузду жазыңыз:\n"
                   "<i>мисалы: +996700123456</i>", phone_kb())
        return

    if u["step"] == "contact":
        if not text:
            send(chat, "Байланыш номерин жазыңыз:")
            return
        u["data"]["contact"] = text[:120]
        lid = add_listing(u["data"], uid, name)

        fid = u["data"].get("photo_file_id")
        if fid:
            fn = f"{lid}.jpg"
            if download_photo(fid, os.path.join(MEDIA, fn)):
                set_photo(lid, fn)

        d = u["data"]
        u["step"] = None; u["data"] = {}
        send(chat, f"✅ <b>Жарыя коюлду!</b>  №{lid}\n\n"
                   f"📦 {esc(d['title'])}\n"
                   f"💰 {esc(d.get('price') or 'Келишимдүү')}\n"
                   f"📍 {esc(d.get('region') or '—')}\n\n"
                   f"🌐 {SITE_URL}/e/{lid}", MENU)
        return

    # ---------- Издөө ----------
    if text == "🔍 Издеймин":
        u["step"] = "find_cat"; u["data"] = {}
        send(chat, "Кайсы категориядан издейли?", cat_kb("fc", with_all=True))
        return

    if u["step"] == "find_q":
        q = None if text.lower() in ("бардыгы", "баары", "все", "-") else text
        u["data"]["q"] = q
        cat, reg = u["data"].get("cat"), u["data"].get("reg")
        sub = u["data"].get("sub")
        total = count(q, cat, reg, sub)
        if not total:
            u["step"] = None
            where = f" ({reg})" if reg else ""
            send(chat, f"Эч нерсе табылган жок{esc(where)} 😔\n"
                       "Башка сөз менен, же башка аймактан аракет кылып көрүңүз.", MENU)
            return
        rows = find(q, cat, reg, sub, limit=PER_PAGE)
        u["step"] = "browsing"
        place = f" · 📍 {esc(reg)}" if reg else ""
        send(chat, f"🔎 <b>{total} жарыя табылды</b>{place}")
        show_results(chat, rows, total, len(rows))
        return

    # ---------- Менин жарыяларым ----------
    if text == "📋 Менин жарыяларым":
        u["step"] = None
        rows = my_listings(uid)
        if not rows:
            send(chat, "Сизде азырынча жарыя жок.", MENU)
            return
        send(chat, f"📋 Сизде {len(rows)} жарыя бар:")
        for r in rows:
            status = "🟢" if r["is_active"] else "🔴 (өчүрүлгөн)"
            kb = ({"inline_keyboard": [[{"text": "🗑 Өчүрүү",
                                         "callback_data": f"del:{r['id']}"}]]}
                  if r["is_active"] else None)
            send(chat, f"{status} №{r['id']}\n"
                       f"📦 {esc(r['title'])}\n"
                       f"💰 {esc(r['price'] or 'Келишимдүү')}   👁 {r['views']}\n"
                       f"🌐 {SITE_URL}/e/{r['id']}", kb)
        return

    # ---------- Түшүнбөдү ----------
    send(chat, "Менюдан тандаңыз 👇", MENU)


def handle_callback(cb, st):
    chat = cb["message"]["chat"]["id"]
    uid = str(cb["from"]["id"])
    data = cb.get("data", "")
    u = st["users"].setdefault(uid, {"step": None, "data": {}})
    api("answerCallbackQuery", callback_query_id=cb["id"])

    if data.startswith("nc:"):
        code = data[3:]
        if code not in CATS:
            return
        u["data"]["category"] = code
        if SUBS.get(code):
            u["step"] = "sub"
            send(chat, f"✅ {CATS[code][1]} {CATS[code][0]}\n\nЭмне жарыялайсыз?",
                 sub_kb(code, "ns"))
        else:
            u["step"] = "title"
            send(chat, "<b>1/6</b> Жарыянын аталышын жазыңыз:", CANCEL)

    elif data.startswith("ns:"):
        cat = u["data"].get("category")
        code = data[3:]
        u["data"]["subcat"] = code
        u["step"] = "title"
        send(chat, f"✅ {esc(sub_title(cat, code))}\n\n"
                   "<b>1/6</b> Жарыянын аталышын жазыңыз:\n"
                   "<i>мисалы: Redmi Note 13 Pro, 8/256</i>", CANCEL)

    elif data.startswith("fc:"):
        code = data[3:]
        u["data"]["cat"] = None if code == "all" else code
        u["data"]["sub"] = None
        if code != "all" and SUBS.get(code):
            u["step"] = "find_sub"
            send(chat, "Эмнени издеп жатасыз?", sub_kb(code, "fs", with_all=True))
            return
        regs = used_regions()
        if len(regs) > 1:
            u["step"] = "find_reg"
            send(chat, "Кайсы аймактан издейли?", find_region_kb())
        else:
            u["data"]["reg"] = None
            u["step"] = "find_q"
            send(chat, "Ачкыч сөз жазыңыз.\n"
                       "<i>Баарын көрүү үчүн «баары» деп жазыңыз</i>", CANCEL)

    elif data.startswith("fs:"):
        code = data[3:]
        u["data"]["sub"] = None if code == "all" else code
        regs = used_regions()
        if len(regs) > 1:
            u["step"] = "find_reg"
            send(chat, "Кайсы аймактан издейли?", find_region_kb())
        else:
            u["data"]["reg"] = None
            u["step"] = "find_q"
            send(chat, "Ачкыч сөз жазыңыз.\n"
                       "<i>Баарын көрүү үчүн «баары» деп жазыңыз</i>", CANCEL)

    elif data.startswith("fr:"):
        code = data[3:]
        if code == "all":
            u["data"]["reg"] = None
        else:
            regs = used_regions()
            i = int(code)
            u["data"]["reg"] = regs[i] if 0 <= i < len(regs) else None
        u["step"] = "find_q"
        where = u["data"]["reg"] or "Бүт Кыргызстан"
        send(chat, f"📍 {esc(where)}\n\nАчкыч сөз жазыңыз.\n"
                   "<i>Баарын көрүү үчүн «баары» деп жазыңыз</i>", CANCEL)

    elif data.startswith("more:"):
        shown = int(data[5:])
        q = u["data"].get("q")
        cat = u["data"].get("cat")
        reg = u["data"].get("reg")
        sub = u["data"].get("sub")
        total = count(q, cat, reg, sub)
        rows = find(q, cat, reg, sub, limit=PER_PAGE, offset=shown)
        show_results(chat, rows, total, shown + len(rows))

    elif data.startswith("del:"):
        lid = int(data[4:])
        if deactivate(lid, uid):
            api("editMessageText", chat_id=chat,
                message_id=cb["message"]["message_id"],
                text=f"🔴 Жарыя №{lid} өчүрүлдү.")
        else:
            send(chat, "Өчүрүү мүмкүн болбоду.")


# ==================== Негизги цикл ====================

def main():
    global TOKEN, API
    TOKEN = token()
    API = f"https://api.telegram.org/bot{TOKEN}/"

    init_db()
    me = api("getMe")
    if not me.get("ok"):
        raise SystemExit("Токен туура эмес окшойт. token.txt файлын текшериңиз.")
    print(f"\n  Бот иштеп жатат: @{me['result'].get('username')}")
    print(f"  Сайт дареги: {SITE_URL}")
    print("  Токтотуу: CTRL+C\n")

    st = load_state()

    while True:
        r = api("getUpdates", offset=st["offset"], timeout=50)
        if not r.get("ok"):
            time.sleep(3)
            continue
        for up in r.get("result", []):
            st["offset"] = up["update_id"] + 1
            try:
                if "message" in up:
                    handle_message(up["message"], st)
                elif "callback_query" in up:
                    handle_callback(up["callback_query"], st)
            except Exception as e:
                print("  Ката:", e)
            save_state(st)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Бот токтотулду.\n")
