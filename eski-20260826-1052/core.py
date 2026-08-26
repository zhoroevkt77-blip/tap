#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAP! — жалпы өзөк. bot.py да, tap.py да ушуну колдонот.

База:
  DATABASE_URL коюлса      -> Postgres (Railway)
  Коюлбаса                 -> SQLite, tap.db файлы (жергиликтүү)

Ошондуктан код өзгөрбөй эле эки жерде тең иштейт.
"""

import os
import sqlite3
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))

# Туруктуу диск. Railway'де Volume /data'га тиркелет; MEDIA_DIR коюлбаса,
# Railway өзү берген RAILWAY_VOLUME_MOUNT_PATH колдонулат; экөө тең жок болсо
# (жергиликтүү Termux) — долбоордун ичиндеги media/ папкасы.
_VOL = (os.environ.get("MEDIA_DIR")
        or os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
        or "").strip()
if _VOL:
    MEDIA = _VOL if _VOL.rstrip("/").endswith("media") else os.path.join(_VOL, "media")
    DATA_DIR = os.path.dirname(MEDIA.rstrip("/")) or BASE
else:
    MEDIA = os.path.join(BASE, "media")
    DATA_DIR = BASE

DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()
IS_PG = DATABASE_URL.startswith(("postgres://", "postgresql://"))

SITE_URL = (os.environ.get("SITE_URL") or "http://localhost:8000").rstrip("/")


# ==================== Категориялар ====================

CATS = {
    "transport": ("Транспорт", "🚗"),
    "realty":    ("Кыймылсыз мүлк", "🏠"),
    "personal":  ("Жеке буюмдар", "👕"),
    "service":   ("Кызматтар", "🔧"),
    "shop":      ("Магазиндер", "🛍"),
    "business":  ("Бизнес", "🤝"),
}

# Категориянын ичиндеги түрлөр. Издөө үчүн эң маанилүү:
# эч ким жарыясына "телефон" деп жазбайт, "Redmi Note 13" деп жазат.
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

REGIONS = ["Жалал-Абад облусу", "Ош облусу", "Баткен облусу", "Чүй облусу",
           "Ысык-Көл облусу", "Нарын облусу", "Талас облусу", "Бишкек", "Ош шаары"]


def category_title(code):
    return CATS.get(code, (code, ""))[0]


def category_icon(code):
    return CATS.get(code, ("", ""))[1]


def sub_title(cat, code):
    for c, n in SUBS.get(cat, []):
        if c == code:
            return n
    return ""


# ==================== Латын / кириллица издөө ====================
# Кыргызстанда "батир" деп да, "batir" деп да жазышат.

_TR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "ң": "ng", "о": "o", "ө": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "у": "u", "ү": "u", "ф": "f", "х": "h", "ц": "c", "ч": "ch",
    "ш": "sh", "щ": "sh", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
    "я": "ya",
}


def translit(s):
    """Кириллицаны латынга которот."""
    return "".join(_TR.get(ch, ch) for ch in (s or "").lower())


def fold(s):
    """Латынча жазуунун варианттарын бир формага келтирет."""
    s = (s or "").lower()
    s = s.replace("ch", "\x01").replace("sh", "\x02")
    for a, b in (("zh", "j"), ("kh", "h"), ("ts", "k"), ("c", "k"),
                 ("yo", "o"), ("yu", "u"), ("ya", "a"), ("ye", "e"),
                 ("q", "k"), ("w", "v"), ("x", "ks"), ("y", "i")):
        s = s.replace(a, b)
    s = s.replace("\x01", "ch").replace("\x02", "sh")
    out = []
    for ch in s:
        if not out or out[-1] != ch:
            out.append(ch)
    return "".join(out)


def norm(s):
    """Издөө үчүн бир формага келтирилген текст."""
    return fold(translit(s))


# Кыргызча-орусча синонимдер
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


def mkstext(title, desc, sub_name=""):
    """Издөө талаасы: кириллица + синонимдер + латынча жазылышы."""
    raw = f"{title or ''} {desc or ''} {sub_name or ''}".lower()
    raw = raw + " " + expand(raw)
    return raw + " " + norm(raw)


# ==================== База ====================

def _connect():
    if IS_PG:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return conn
    conn = sqlite3.connect(os.path.join(BASE, "tap.db"))
    conn.row_factory = sqlite3.Row
    return conn


def _ph(sql):
    """SQLite '?' -> Postgres '%s'."""
    return sql.replace("?", "%s") if IS_PG else sql


def query(sql, params=(), fetch=None):
    """
    Бир суроо аткарат.
    fetch: None (жооп жок), "one" (бир сап), "all" (бардыгы), "id" (жаңы id)
    """
    conn = _connect()
    try:
        if IS_PG:
            import psycopg2.extras
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cur = conn.cursor()

        if fetch == "id":
            cur.execute(_ph(sql + (" RETURNING id" if IS_PG else "")), params)
            new_id = cur.fetchone()["id"] if IS_PG else cur.lastrowid
            conn.commit()
            return new_id

        cur.execute(_ph(sql), params)

        if fetch == "one":
            row = cur.fetchone()
            out = dict(row) if row else None
        elif fetch == "all":
            out = [dict(r) for r in cur.fetchall()]
        else:
            out = None

        conn.commit()
        return out
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL, subcat TEXT, region TEXT,
    title TEXT NOT NULL, description TEXT, price TEXT, contact TEXT,
    photo TEXT, tg_id TEXT, tg_name TEXT, stext TEXT,
    views INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    ad_type TEXT, cat_id TEXT, sub_id TEXT,
    oblast TEXT, district TEXT, locality TEXT, village TEXT)
"""

SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS listings (
    id SERIAL PRIMARY KEY,
    category TEXT NOT NULL, subcat TEXT, region TEXT,
    title TEXT NOT NULL, description TEXT, price TEXT, contact TEXT,
    photo TEXT, tg_id TEXT, tg_name TEXT, stext TEXT,
    views INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    ad_type TEXT, cat_id TEXT, sub_id TEXT,
    oblast TEXT, district TEXT, locality TEXT, village TEXT)
"""


NEW_COLUMNS = ["ad_type", "cat_id", "sub_id",
               "oblast", "district", "locality", "village"]


def _add_missing_columns():
    """
    Мурунтан бар базага жаңы тилкелерди кошот. Маалымат жоголбойт,
    эски жарыялар ордунда калат (жаңы тилкелери бош болот).
    """
    for col in NEW_COLUMNS:
        try:
            if IS_PG:
                query("ALTER TABLE listings ADD COLUMN IF NOT EXISTS %s TEXT" % col)
            else:
                query("ALTER TABLE listings ADD COLUMN %s TEXT" % col)
        except Exception:
            pass   # тилке мурунтан бар — баары жайында


def init_db():
    """Таблицаны түзөт. Кайра-кайра чакырса коопсуз."""
    os.makedirs(MEDIA, exist_ok=True)
    query(SCHEMA_PG if IS_PG else SCHEMA_SQLITE)
    _add_missing_columns()
    query("CREATE INDEX IF NOT EXISTS idx_active ON listings(is_active)")
    query("CREATE INDEX IF NOT EXISTS idx_cat ON listings(category)")
    try:
        query("CREATE INDEX IF NOT EXISTS idx_adtype ON listings(ad_type)")
        query("CREATE INDEX IF NOT EXISTS idx_oblast ON listings(oblast)")
    except Exception:
        pass
    _backfill_old_rows()


def _backfill_old_rows():
    """
    Эски жарыялардын `region` жазуусун жаңы `oblast` тилкесине көчүрөт,
    ошондо алар жаңы издөөдө да көрүнөт. Бир жолу гана иштейт.
    """
    try:
        query("UPDATE listings SET oblast=region "
              "WHERE (oblast IS NULL OR oblast='') AND region IS NOT NULL AND region<>''")
    except Exception:
        pass


def now_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ==================== Жарыялар ====================

def add_listing(d, tg_id, tg_name):
    """Жаңы жарыя кошот, номерин кайтарат."""
    stext = mkstext(
        d["title"],
        " ".join([d.get("description", "") or "",
                  d.get("sub_id", "") or "",
                  d.get("region", "") or ""]),
        sub_title(d["category"], d.get("subcat")))
    return query(
        """INSERT INTO listings
           (category, subcat, region, title, description, price, contact,
            tg_id, tg_name, stext, created_at,
            ad_type, cat_id, sub_id, oblast, district, locality, village)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (d["category"], d.get("subcat"), d.get("region", ""), d["title"],
         d.get("description", ""), d.get("price", ""), d.get("contact", ""),
         str(tg_id), tg_name, stext, now_str(),
         d.get("ad_type", ""), d.get("cat_id", ""), d.get("sub_id", ""),
         d.get("oblast", ""), d.get("district", ""),
         d.get("locality", ""), d.get("village", "")),
        fetch="id")


def set_photo(lid, name):
    query("UPDATE listings SET photo=? WHERE id=?", (name, lid))


def _filters(q=None, cat=None, region=None, sub=None,
             ad_type=None, cat_id=None, oblast=None, district=None):
    sql, p = "", []
    if cat:
        sql += " AND category=?"; p.append(cat)
    if sub:
        sql += " AND subcat=?"; p.append(sub)
    if region:
        sql += " AND region=?"; p.append(region)
    if ad_type:
        sql += " AND ad_type=?"; p.append(ad_type)
    if cat_id:
        sql += " AND cat_id=?"; p.append(cat_id)
    if oblast:
        sql += " AND oblast=?"; p.append(oblast)
    if district:
        sql += " AND district=?"; p.append(district)
    if q and q.strip():
        sql += " AND (stext LIKE ? OR stext LIKE ?)"
        p += [f"%{q.lower()}%", f"%{norm(q)}%"]
    return sql, p


def find(q=None, cat=None, region=None, sub=None, limit=30, offset=0,
         ad_type=None, cat_id=None, oblast=None, district=None):
    where, p = _filters(q, cat, region, sub, ad_type, cat_id, oblast, district)
    return query(
        "SELECT * FROM listings WHERE is_active=1" + where +
        " ORDER BY id DESC LIMIT ? OFFSET ?", tuple(p + [limit, offset]), fetch="all")


def count(q=None, cat=None, region=None, sub=None,
          ad_type=None, cat_id=None, oblast=None, district=None):
    where, p = _filters(q, cat, region, sub, ad_type, cat_id, oblast, district)
    r = query("SELECT COUNT(*) AS n FROM listings WHERE is_active=1" + where,
              tuple(p), fetch="one")
    return (r or {}).get("n", 0)


def one(lid, count_view=True):
    r = query("SELECT * FROM listings WHERE id=? AND is_active=1", (lid,), fetch="one")
    if r and count_view:
        query("UPDATE listings SET views=views+1 WHERE id=?", (lid,))
    return r


def my_listings(tg_id):
    return query("SELECT * FROM listings WHERE tg_id=? ORDER BY id DESC",
                 (str(tg_id),), fetch="all")


def deactivate(lid, tg_id):
    before = query("SELECT id FROM listings WHERE id=? AND tg_id=? AND is_active=1",
                   (lid, str(tg_id)), fetch="one")
    if not before:
        return False
    query("UPDATE listings SET is_active=0 WHERE id=? AND tg_id=?", (lid, str(tg_id)))
    return True


def cat_counts(region=None):
    where, p = ("", [])
    if region:
        where, p = " AND region=?", [region]
    rows = query("SELECT category, COUNT(*) AS n FROM listings WHERE is_active=1"
                 + where + " GROUP BY category", tuple(p), fetch="all")
    return {r["category"]: r["n"] for r in rows}


def sub_counts(cat, region=None):
    where, p = " AND category=?", [cat]
    if region:
        where += " AND region=?"; p.append(region)
    rows = query("SELECT subcat, COUNT(*) AS n FROM listings WHERE is_active=1"
                 + where + " GROUP BY subcat", tuple(p), fetch="all")
    return {r["subcat"]: r["n"] for r in rows if r["subcat"]}


# ── Жаңы таксономия боюнча эсептөөлөр (сайт үчүн) ────────────

def adtype_counts(oblast=None):
    """Ар бир бөлүмдө канча жарыя бар."""
    where, p = ("", [])
    if oblast:
        where, p = " AND oblast=?", [oblast]
    rows = query("SELECT ad_type, COUNT(*) AS n FROM listings WHERE is_active=1"
                 + where + " GROUP BY ad_type", tuple(p), fetch="all")
    return {r["ad_type"]: r["n"] for r in rows if r["ad_type"]}


def catid_counts(ad_type=None, oblast=None):
    """Бөлүмдүн ичиндеги категориялар боюнча эсеп."""
    where, p = ("", [])
    if ad_type:
        where += " AND ad_type=?"; p.append(ad_type)
    if oblast:
        where += " AND oblast=?"; p.append(oblast)
    rows = query("SELECT cat_id, COUNT(*) AS n FROM listings WHERE is_active=1"
                 + where + " GROUP BY cat_id", tuple(p), fetch="all")
    return {r["cat_id"]: r["n"] for r in rows if r["cat_id"]}


def used_oblasts():
    """Базада чындап жарыясы бар облустар."""
    rows = query("SELECT oblast, COUNT(*) AS n FROM listings WHERE is_active=1 "
                 "AND oblast IS NOT NULL AND oblast<>'' GROUP BY oblast "
                 "ORDER BY n DESC", (), fetch="all")
    return [r["oblast"] for r in rows]


def used_districts(oblast):
    """Тандалган облуста жарыясы бар райондор."""
    rows = query("SELECT district, COUNT(*) AS n FROM listings WHERE is_active=1 "
                 "AND oblast=? AND district IS NOT NULL AND district<>'' "
                 "GROUP BY district ORDER BY n DESC", (oblast,), fetch="all")
    return [r["district"] for r in rows]


def used_regions():
    """Базада чындап жарыясы бар аймактар."""
    rows = query("SELECT region, COUNT(*) AS n FROM listings WHERE is_active=1 "
                 "AND region IS NOT NULL AND region<>'' GROUP BY region "
                 "ORDER BY n DESC", (), fetch="all")
    return [r["region"] for r in rows]


def ago(ts):
    """'2026-08-23 03:53:00' -> '2 саат мурун'"""
    try:
        t = datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc)
    except Exception:
        return str(ts)[:16]
    sec = (datetime.now(timezone.utc) - t).total_seconds()
    if sec < 60:
        return "азыр эле"
    if sec < 3600:
        return f"{int(sec // 60)} мүнөт мурун"
    if sec < 86400:
        return f"{int(sec // 3600)} саат мурун"
    d = int(sec // 86400)
    if d == 1:
        return "кечээ"
    if d < 30:
        return f"{d} күн мурун"
    if d < 365:
        return f"{d // 30} ай мурун"
    return f"{d // 365} жыл мурун"


def price_label(price):
    return (price or "").strip() or "Келишимдүү"


DEAL_WORDS = {"келишимдүү", "келишим", "договорная", "келишимдуу", ""}


def is_deal(price):
    return (price or "").strip().lower() in DEAL_WORDS
