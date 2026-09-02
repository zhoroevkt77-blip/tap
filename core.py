#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAP! — жалпы өзөк. bot.py да, tap.py да ушуну колдонот.

База:
  DATABASE_URL коюлса      -> Postgres (Railway)
  Коюлбаса                 -> SQLite, tap.db файлы (жергиликтүү)

Ошондуктан код өзгөрбөй эле эки жерде тең иштейт.
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone

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


def price_number(price):
    """
    «4 000 000 сом», «25 сом/кг» сыяктуу жазуудан санды бөлүп алат.
    Келишим баада болсо, None кайтат — иргөөдө четте калат.
    """
    digits = "".join(ch for ch in str(price or "") if ch.isdigit())
    if not digits or len(digits) > 12:
        return None
    return int(digits)


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
    photo TEXT, photos TEXT, tg_id TEXT, tg_name TEXT, stext TEXT,
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
    photo TEXT, photos TEXT, tg_id TEXT, tg_name TEXT, stext TEXT,
    views INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    ad_type TEXT, cat_id TEXT, sub_id TEXT,
    oblast TEXT, district TEXT, locality TEXT, village TEXT)
"""


NEW_COLUMNS = ["ad_type", "cat_id", "sub_id",
               "oblast", "district", "locality", "village", "photos",
               # жарыянын мөөнөтү бүтө турган күн (ISO), жана
               # иргөө үчүн бааны сан түрүндө сактайбыз
               "expires_at", "price_num"]


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

# Колдонуучу тандаган мөөнөт — канча күн
DURATION_DAYS = {
    "1 күн": 1, "3 күн": 3, "1 апта": 7, "2 апта": 14,
    "1 ай": 30, "2 ай": 60, "3 ай": 90,
}


def expiry_from(duration, days=None):
    """Мөөнөттүн бүтөр күнү. Тандалбаса — 30 күн."""
    if days is None:
        d = str(duration or "").strip().lower()
        days = 30
        for k, v in DURATION_DAYS.items():
            if k.lower() in d:
                days = v
                break
    return (datetime.now(timezone.utc)
            + timedelta(days=int(days))).strftime("%Y-%m-%d %H:%M:%S")


def add_listing(d, tg_id, tg_name):
    """Жаңы жарыя кошот, номерин кайтарат."""
    # Издөө талаасына категориянын, бөлүмдүн аттары да кирет —
    # «телефон» деп издегенде «Смартфондор» табылсын.
    stext = mkstext(
        d["title"],
        " ".join([d.get("description", "") or "",
                  d.get("sub_id", "") or "",
                  d.get("cat_name", "") or "",
                  d.get("sec_name", "") or "",
                  d.get("region", "") or "",
                  d.get("oblast", "") or "",
                  d.get("district", "") or ""]),
        sub_title(d["category"], d.get("subcat")))
    return query(
        """INSERT INTO listings
           (category, subcat, region, title, description, price, contact,
            tg_id, tg_name, stext, created_at,
            ad_type, cat_id, sub_id, oblast, district, locality, village,
            expires_at, price_num)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (d["category"], d.get("subcat"), d.get("region", ""), d["title"],
         d.get("description", ""), d.get("price", ""), d.get("contact", ""),
         str(tg_id), tg_name, stext, now_str(),
         d.get("ad_type", ""), d.get("cat_id", ""), d.get("sub_id", ""),
         d.get("oblast", ""), d.get("district", ""),
         d.get("locality", ""), d.get("village", ""),
         expiry_from(d.get("duration")), price_number(d.get("price"))),
        fetch="id")


def set_photo(lid, name):
    query("UPDATE listings SET photo=? WHERE id=?", (name, lid))


def set_photos(lid, names):
    """
    Жарыянын бардык сүрөттөрүн жазат.

    `photos` — JSON тизме, `photo` — биринчи сүрөт. Экинчиси эски
    код (сайттын карточкалары, боттун тизмеси) үчүн сакталат.
    """
    names = [n for n in (names or []) if n]
    if not names:
        return
    query("UPDATE listings SET photo=?, photos=? WHERE id=?",
          (names[0], json.dumps(names, ensure_ascii=False), lid))


def photo_list(row):
    """Жарыянын сүрөттөрү. Эски жарыяларда бирөө гана."""
    raw = row.get("photos") if hasattr(row, "get") else None
    if raw:
        try:
            got = json.loads(raw)
            if isinstance(got, list):
                out = [str(x) for x in got if x]
                if out:
                    return out
        except (ValueError, TypeError):
            pass
    one = row.get("photo") if hasattr(row, "get") else None
    return [one] if one else []


def _filters(q=None, cat=None, region=None, sub=None,
             ad_type=None, cat_id=None, oblast=None, district=None,
             village=None, sub_id=None, pmin=None, pmax=None):
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
    if sub_id:
        sql += " AND sub_id=?"; p.append(sub_id)
    if oblast:
        sql += " AND oblast=?"; p.append(oblast)
    if district:
        sql += " AND district=?"; p.append(district)
    if village:
        sql += " AND " + VILLAGE_EXPR + "=?"; p.append(village)
    if pmin is not None:
        sql += " AND price_num IS NOT NULL AND price_num>=?"; p.append(int(pmin))
    if pmax is not None:
        sql += " AND price_num IS NOT NULL AND price_num<=?"; p.append(int(pmax))
    if q and q.strip():
        # Ар бир сөз өз-өзүнчө изделет — «кызыл кийим» деп жазса да табылат
        for w in [x for x in str(q).lower().split() if len(x) > 1][:5]:
            sql += " AND (stext LIKE ? OR stext LIKE ?)"
            p += [f"%{w}%", f"%{norm(w)}%"]
    return sql, p


# Сайттагы иргөө тартиптери
SORTS = {
    "new":   "id DESC",                                   # жаңысынан
    "old":   "id ASC",                                    # эскисинен
    "cheap": "price_num IS NULL, price_num ASC, id DESC",  # арзандан
    "rich":  "price_num IS NULL, price_num DESC, id DESC",  # кымбаттан
    "views": "views DESC, id DESC",                        # көп көрүлгөн
}


def find(q=None, cat=None, region=None, sub=None, limit=30, offset=0,
         ad_type=None, cat_id=None, oblast=None, district=None, village=None,
         sub_id=None, pmin=None, pmax=None, sort="new"):
    where, p = _filters(q, cat, region, sub, ad_type, cat_id, oblast,
                        district, village, sub_id, pmin, pmax)
    order = SORTS.get(sort or "new", SORTS["new"])
    return query(
        "SELECT * FROM listings WHERE is_active=1" + where +
        " ORDER BY " + order + " LIMIT ? OFFSET ?",
        tuple(p + [limit, offset]), fetch="all")


def count(q=None, cat=None, region=None, sub=None,
          ad_type=None, cat_id=None, oblast=None, district=None, village=None,
          sub_id=None, pmin=None, pmax=None):
    where, p = _filters(q, cat, region, sub, ad_type, cat_id, oblast,
                        district, village, sub_id, pmin, pmax)
    r = query("SELECT COUNT(*) AS n FROM listings WHERE is_active=1" + where,
              tuple(p), fetch="one")
    return (r or {}).get("n", 0)


def one(lid, count_view=True):
    r = query("SELECT * FROM listings WHERE id=? AND is_active=1", (lid,), fetch="one")
    if r and count_view:
        query("UPDATE listings SET views=views+1 WHERE id=?", (lid,))
    return r


def _digits(s):
    return "".join(c for c in str(s or "") if c.isdigit())


# Байланыш номерин базада тазалап салыштыруу үчүн (боштук, дефис, плюс)
_CLEAN = ("REPLACE(REPLACE(REPLACE(contact, ' ', ''), '-', ''), '+', '')")


def owns(lid, tg_id, phone=None):
    """Жарыя ушул колдонуучунуку бекен: Telegram ID же телефон боюнча."""
    r = query("SELECT id FROM listings WHERE id=? AND tg_id=?",
              (lid, str(tg_id)), fetch="one")
    if r:
        return True
    d = _digits(phone)[-9:]
    if len(d) == 9:
        r = query("SELECT id FROM listings WHERE id=? AND %s LIKE ?" % _CLEAN,
                  (lid, "%" + d), fetch="one")
        if r:
            return True
    return False


def my_listings(tg_id, phone=None):
    """
    Колдонуучунун жарыялары.

    Telegram аркылуу коюлганы `tg_id` менен, ал эми башка түзмөктөн же
    сайттан коюлганы байланыш номери боюнча табылат.
    """
    rows = query("SELECT * FROM listings WHERE tg_id=? ORDER BY id DESC",
                 (str(tg_id),), fetch="all") or []
    d = _digits(phone)[-9:]
    if len(d) == 9:
        extra = query("SELECT * FROM listings WHERE %s LIKE ?"
                      " ORDER BY id DESC" % _CLEAN,
                      ("%" + d,), fetch="all") or []
        seen = {r["id"] for r in rows}
        rows = rows + [r for r in extra if r["id"] not in seen]
        rows.sort(key=lambda r: r["id"], reverse=True)
    return rows


def deactivate(lid, tg_id, phone=None):
    if not owns(lid, tg_id, phone):
        return False
    before = query("SELECT id FROM listings WHERE id=? AND is_active=1",
                   (lid,), fetch="one")
    if not before:
        return False
    query("UPDATE listings SET is_active=0 WHERE id=?", (lid,))
    return True


def expire_old(limit=200):
    """
    Мөөнөтү бүткөн жарыяларды жашырат жана ээлеринин тизмесин кайтарат
    (ошолорго кабар жөнөтүү үчүн). Күнүнө бир жолу чакырылат.
    """
    rows = query(
        "SELECT id, tg_id, title FROM listings WHERE is_active=1"
        " AND expires_at IS NOT NULL AND expires_at<>'' AND expires_at<?"
        " ORDER BY id LIMIT ?", (now_str(), limit), fetch="all") or []
    for r in rows:
        query("UPDATE listings SET is_active=0 WHERE id=?", (r["id"],))
    return rows


def revive(lid, tg_id, days=30, phone=None):
    """Жарыяны кайра жандырат жана мөөнөтүн узартат."""
    if not owns(lid, tg_id, phone):
        return False
    query("UPDATE listings SET is_active=1, expires_at=? WHERE id=?",
          (expiry_from(None, days=days), lid))
    return True


def posted_today(tg_id):
    """Бүгүн ушул колдонуучу канча жарыя койду."""
    day = now_str()[:10]
    r = query("SELECT COUNT(*) AS n FROM listings WHERE tg_id=?"
              " AND created_at>=?", (str(tg_id), day + " 00:00:00"), fetch="one")
    return (r or {}).get("n", 0)


def update_listing(lid, tg_id, fields, phone=None):
    """Жарыянын айрым талааларын оңдойт (ээси гана)."""
    allowed = ("title", "description", "price", "contact")
    sets, p = [], []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k}=?"); p.append(v)
    if not sets:
        return False
    if "price" in fields:
        sets.append("price_num=?"); p.append(price_number(fields["price"]))
    if not owns(lid, tg_id, phone):
        return False
    row = query("SELECT * FROM listings WHERE id=?", (lid,), fetch="one")
    if not row:
        return False
    # Аталыш же сүрөттөмө өзгөрсө, издөө талаасын кайра курабыз —
    # антпесе жарыя эски сөздөр боюнча табылып калат.
    if "title" in fields or "description" in fields:
        t = fields.get("title", row.get("title"))
        d = fields.get("description", row.get("description"))
        sets.append("stext=?")
        p.append(mkstext(t, " ".join([
            d or "",
            row.get("sub_id") or "", row.get("region") or "",
            row.get("oblast") or "", row.get("district") or ""]),
            sub_title(row.get("category") or "", row.get("subcat"))))
    query(f"UPDATE listings SET {', '.join(sets)} WHERE id=?", tuple(p + [lid]))
    return True


def admin_deactivate(lid):
    """Админ өчүрөт — жарыянын ээси ким экенине карабай."""
    row = query("SELECT id FROM listings WHERE id=? AND is_active=1",
                (lid,), fetch="one")
    if not row:
        return False
    query("UPDATE listings SET is_active=0 WHERE id=?", (lid,))
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


def catid_counts(ad_type=None, oblast=None, district=None,
                 village=None, q=None, sub_id=None):
    """
    Бөлүмдүн ичиндеги категориялар боюнча эсеп.

    Тандалган аймак толугу менен эсепке алынат: облус, район,
    айыл аймагы. Ошондуктан сандар экрандагы тизме менен дал келет.
    """
    where, p = _filters(q=q, ad_type=ad_type, oblast=oblast,
                        district=district, village=village, sub_id=sub_id)
    rows = query("SELECT cat_id, COUNT(*) AS n FROM listings WHERE is_active=1"
                 + where + " GROUP BY cat_id", tuple(p), fetch="all")
    return {r["cat_id"]: r["n"] for r in rows if r["cat_id"]}


def subid_counts(ad_type=None, cat_id=None, oblast=None, district=None,
                 village=None, q=None):
    """Категориянын ичиндеги субкатегориялар боюнча эсеп."""
    where, p = _filters(q=q, ad_type=ad_type, cat_id=cat_id, oblast=oblast,
                        district=district, village=village)
    rows = query("SELECT sub_id, COUNT(*) AS n FROM listings WHERE is_active=1"
                 + where + " GROUP BY sub_id", tuple(p), fetch="all")
    return {r["sub_id"]: r["n"] for r in rows if r["sub_id"]}


# Айыл да, кичи район да ушул бир туюнтма менен эсептелет.
VILLAGE_EXPR = "COALESCE(NULLIF(village,''), NULLIF(locality,''))"


def region_counts(level, oblast=None, district=None,
                  q=None, ad_type=None, cat_id=None, sub_id=None):
    """
    Аймактар боюнча жарыялардын саны — учурдагы чыпканын ичинде.

    level: "oblast" | "district" | "village"
    Бөлүм, категория жана издөө сөзү эсепке алынат, ошондуктан
    сандар экранда көрүнүп турган тизме менен дал келет.
    """
    expr = {"oblast": "oblast",
            "district": "district"}.get(level, VILLAGE_EXPR)
    where, p = _filters(q=q, ad_type=ad_type, cat_id=cat_id,
                        oblast=oblast, district=district, sub_id=sub_id)
    rows = query("SELECT " + expr + " AS k, COUNT(*) AS n FROM listings "
                 "WHERE is_active=1" + where +
                 " AND " + expr + " IS NOT NULL AND " + expr + "<>'' "
                 "GROUP BY " + expr, tuple(p), fetch="all")
    return {r["k"]: r["n"] for r in rows if r["k"]}


def oblast_counts(**kw):
    """Ар бир облуста канча жарыя бар."""
    return region_counts("oblast", **kw)


def district_counts(oblast, **kw):
    """Облустагы райондор боюнча эсеп."""
    return region_counts("district", oblast=oblast, **kw)


def village_counts(oblast, district, **kw):
    """Райондогу айылдар/кичи райондор боюнча эсеп."""
    return region_counts("village", oblast=oblast, district=district, **kw)


def used_villages(oblast, district):
    """Райондо жарыясы бар айылдар/кичи райондор."""
    c = village_counts(oblast, district)
    return sorted(c, key=lambda x: -c[x])


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
    return (price or "").strip() or "Келишим баада"


DEAL_WORDS = {"келишимдүү", "келишим", "договорная", "келишимдуу", ""}


def is_deal(price):
    """Баа келишим боюнчабы. «Келишим баада» сыяктуулар да кирет."""
    p = (price or "").strip().lower()
    return (p in DEAL_WORDS
            or p.startswith("келишим")
            or p.startswith("договор"))
