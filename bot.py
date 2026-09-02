#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAP! — Telegram бот.

Меню структурасы tap_flow.py'да ("бир мээ"), бул файл Telegram'дын
"оозу" гана: баскычтарды тартат, жоопторду өткөрөт.

Токен: TELEGRAM_BOT_TOKEN чөйрө өзгөрмөсү, же token.txt файлы.
Иштетүү: python bot.py
"""

import threading
import copy, json, os, ssl, time, urllib.parse, urllib.request, mimetypes

import core
from core import MEDIA, SITE_URL, price_label
import bridge
from strings import L as _pick
from tap_flow import render, advance, START_STEP

TOKEN_FILE = os.path.join(core.BASE, "token.txt")
# Абал туруктуу дискте сакталат — Railway кайра курганда колдонуучу
# жарыясынын ортосунда калбашы үчүн.
STATE_FILE = os.path.join(core.DATA_DIR, "bot_state.json")
PER_PAGE = 5

_ctx = ssl.create_default_context()
TOKEN = None
API = None


# ==================== Telegram API ====================

def read_token():
    t = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if t:
        return t
    if os.path.exists(TOKEN_FILE):
        t = open(TOKEN_FILE, encoding="utf-8").read().strip()
        if t:
            return t
    raise SystemExit(
        "\nТокен табылган жок!\n"
        "Railway'де: Variables ичине TELEGRAM_BOT_TOKEN кош.\n"
        "Жергиликтүү: echo -n \"ТОКЕН\" > token.txt\n")


# Админдер: Railway'де ADMIN_IDS деген өзгөрмөгө Telegram ID жазылат.
# Бирден көп болсо, үтүр менен: 123456,987654
ADMIN_IDS = [x.strip() for x in
             (os.environ.get("ADMIN_IDS") or "").replace(" ", "").split(",")
             if x.strip()]


def api(method, **params):
    data = urllib.parse.urlencode(
        {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
         for k, v in params.items() if v is not None}).encode()
    req = urllib.request.Request(API + method, data=data)
    try:
        with urllib.request.urlopen(req, timeout=70, context=_ctx) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("  API катасы:", method, e, flush=True)
        return {"ok": False}


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def send(chat, text, kb=None):
    return api("sendMessage", chat_id=chat, text=text, parse_mode="HTML",
               disable_web_page_preview=True, reply_markup=kb)


def send_photo(chat, path, caption, kb=None):
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

    req = urllib.request.Request(API + "sendPhoto", data=b"".join(parts))
    req.add_header("Content-Type", f"multipart/form-data; boundary={bnd}")
    try:
        with urllib.request.urlopen(req, timeout=90, context=_ctx) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("  Сүрөт жөнөтүлбөдү:", e, flush=True)
        return send(chat, caption, kb)


def download_photo(file_id, dest):
    r = api("getFile", file_id=file_id)
    if not r.get("ok"):
        return False
    url = f"https://api.telegram.org/file/bot{TOKEN}/{r['result']['file_path']}"
    try:
        with urllib.request.urlopen(url, timeout=90, context=_ctx) as resp:
            data = resp.read()
        os.makedirs(MEDIA, exist_ok=True)
        open(dest, "wb").write(data)
        return True
    except Exception as e:
        print("  Сүрөт жүктөлбөдү:", e, flush=True)
        return False


# ==================== Абалдар ====================

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE, encoding="utf-8"))
        except Exception:
            pass
    return {"offset": 0, "users": {}}


def save_state(st):
    try:
        os.makedirs(os.path.dirname(STATE_FILE) or ".", exist_ok=True)
        tmp = STATE_FILE + ".tmp"
        json.dump(st, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
        os.replace(tmp, STATE_FILE)
    except Exception:
        pass   # диск жазылбаса да бот иштей берсин


def user(st, uid):
    return st["users"].setdefault(
        str(uid), {"step": START_STEP, "data": {}, "picked": [], "find": {}})


def reset(u, full=False):
    """
    Флоуну башынан баштайт.

    full=False — тил тандалып койгон болсо, кайра сурабай түз башкы менюга.
    full=True  — /start басылганда: баарын нөлдөн.
    """
    lang = (u.get("data") or {}).get("uiLanguage")
    u["picked"] = []
    u["hist"] = []
    u.pop("titleasked", None)
    u.pop("edit", None)
    if lang and not full:
        u["step"] = "main_menu"
        u["data"] = {"uiLanguage": lang}
    else:
        u["step"] = START_STEP
        u["data"] = {}


# ==================== Баскычтар ====================

# ==================== Тил ====================

# Боттун өз жазуулары: (кыргызча, орусча)
MSG = {
    "home_btn":   ("🏠 Башкы меню",        "🏠 Главное меню"),
    "done_btn":   ("✅ Тандап бүттүм",      "✅ Готово"),
    "more_btn":   ("⬇️ Дагы көрсөт",       "⬇️ Показать ещё"),
    "del_btn":    ("🗑 Өчүрүү",            "🗑 Удалить"),
    "menu_short": ("Эмне кыласыз? 👇",     "Что делаете? 👇"),
    "multi_hint": ("Бир нече тандаса болот — бүткөндөн кийин «Тандап бүттүм» басыңыз.",
                   "Можно выбрать несколько — потом нажмите «Готово»."),
    "photo_hint": ("📎 кыстаргыч → Галерея → сүрөттөрдү тандаңыз.",
                   "📎 скрепка → Галерея → выберите фото."),
    "more_left":  ("Дагы %d жарыя бар.",   "Ещё %d объявлений."),
    "thats_all":  ("Баары ушул.",          "Это всё."),
    "near":       ("Так дал келгени табылган жок, жакындарын көрсөтөм 👇",
                   "Точных совпадений нет, показываю похожие 👇"),
    "nothing":    ("Эч нерсе табылган жок 😔\n"
                   "Башка сөз менен, же башка аймактан аракет кылып көрүңүз.",
                   "Ничего не найдено 😔\n"
                   "Попробуйте другое слово или другой регион."),
    "found":      ("🔎 <b>%d жарыя табылды</b>", "🔎 <b>Найдено объявлений: %d</b>"),
    "posted":     ("✅ <b>Жарыя коюлду!</b>  №%d", "✅ <b>Объявление размещено!</b>  №%d"),
    "no_posts":   ("Сизде азырынча жарыя жок.", "У вас пока нет объявлений."),
    "my_posts":   ("📋 Сизде %d жарыя бар:",  "📋 У вас %d объявлений:"),
    "removed":    ("(өчүрүлгөн)",           "(удалено)"),
    "del_ok":     ("🔴 Жарыя №%d өчүрүлдү.", "🔴 Объявление №%d удалено."),
    "del_fail":   ("Өчүрүү мүмкүн болбоду.", "Не удалось удалить."),
    "error":      ("Кечиресиз, ката кетти. Башынан баштайлы.",
                   "Извините, произошла ошибка. Начнём сначала."),
    "no_photo":   ("Азыр сүрөт күтүлбөй жатат.", "Сейчас фото не ожидается."),
    "write_smth": ("Бир нерсе жазыңыз:",     "Напишите что-нибудь:"),
    "use_btn":    ("Төмөнкү баскычтардан тандаңыз 👇",
                   "Выберите одну из кнопок ниже 👇"),
    "pick_one":   ("Жок дегенде бирөөнү тандаңыз.", "Выберите хотя бы один вариант."),
    "untitled":   ("Жарыя",                 "Объявление"),
    "photo_need": ("📸 %d сүрөт жүктөлдү. Дагы %d керек.",
                   "📸 Загружено фото: %d. Нужно ещё %d."),
    "photo_ok":   ("📸 %d сүрөт жүктөлдү. Бүтсөңүз «Даяр» басыңыз.",
                   "📸 Загружено фото: %d. Закончили — нажмите «Готово»."),
    "photo_max":  ("📸 %d сүрөт — эң көбү ушул. «Даяр» басыңыз.",
                   "📸 %d фото — это максимум. Нажмите «Готово»."),
    "photo_few":  ("Жок дегенде %d сүрөт керек.", "Нужно минимум %d фото."),
    "photo_done": ("✅ Даяр",                 "✅ Готово"),
    "back_btn":   ("⬅️ Артка", "⬅️ Назад"),
    # ── Аталышты колдонуучу өзү жазат ──
    "ask_title":  ("✍️ <b>Жарыяңызга аталыш жазыңыз</b>\n\n"
                   "Кыска жана түшүнүктүү болсун.\n"
                   "Мисалы: <i>Муздаткыч Beko, аз колдонулган</i>",
                   "✍️ <b>Напишите заголовок объявления</b>\n\n"
                   "Коротко и понятно.\n"
                   "Например: <i>Холодильник Beko, мало б/у</i>"),
    "skip_title": ("⏭ Өткөрүп жиберүү", "⏭ Пропустить"),
    # ── Жарыяны оңдоо ──
    "edit_btn":   ("✏️ Оңдоо",            "✏️ Изменить"),
    "edit_what":  ("✏️ Жарыя №%d — эмнени оңдойсуз?",
                   "✏️ Объявление №%d — что изменить?"),
    "ed_title":   ("📦 Аталышы",          "📦 Заголовок"),
    "ed_price":   ("💰 Баасы",            "💰 Цена"),
    "ed_desc":    ("📝 Сүрөттөмөсү",      "📝 Описание"),
    "ed_contact": ("☎️ Байланыш",         "☎️ Контакт"),
    "edit_ask":   ("Жаңы маанисин жазыңыз:", "Напишите новое значение:"),
    "edit_ok":    ("✅ Жарыя №%d оңдолду.", "✅ Объявление №%d изменено."),
    "edit_fail":  ("Оңдоо мүмкүн болбоду. Жарыя сиздики эмес окшойт.",
                   "Не удалось изменить. Похоже, объявление не ваше."),
}

# Бир жарыяга канча сүрөт. strings.py'дагы сандар менен бирдей.
PHOTO_MIN = 0
PHOTO_MAX = 10


def ulang(u):
    """Колдонуучунун тили: "ky" же "ru"."""
    return "ru" if (u.get("data") or {}).get("uiLanguage") == "ru" else "ky"


def m(key, lang, *args):
    """Боттун жазуусу — тандалган тилде."""
    ky, ru = MSG[key]
    s = ru if lang == "ru" else ky
    return (s % args) if args else s


def _stars(s):
    """Кош жылдызчаны калың текстке айлантат, жалгызын алып салат."""
    if s.count("*") % 2:
        return s.replace("*", "")
    out, bold = [], False
    for ch in s:
        if ch == "*":
            out.append("</b>" if bold else "<b>")
            bold = not bold
        else:
            out.append(ch)
    return "".join(out)


def _lead(s):
    """Саптын башындагы эмодзи/белги бөлүгү («🔍 », «• », «✅ »)."""
    i = 0
    while i < len(s) and (ord(s[i]) >= 0x2000 or s[i] == " "):
        i += 1
    return s[:i]


def loc(text, lang):
    """
    Флоунун «кыргызча / орусча» жазуусунан бир тилди алат.

    Эмодзи көбүнчө кыргызча жагында гана турат («🔍 Издейм / Ищу»),
    ошондуктан орусчаны тандаганда аны кайра кошуп коёбуз.
    """
    out = []
    for line in str(text or "").split("\n"):
        picked = _pick(line, lang)
        head = _lead(line)
        if head.strip() and not picked.startswith(head.strip()[:1]):
            picked = head + picked
        out.append(_stars(picked))
    return "\n".join(out)


# ==================== Баскычтар ====================

def home_kb(lang="ky"):
    return {"keyboard": [[{"text": m("home_btn", lang)}]], "resize_keyboard": True}


def flow_kb(view, picked=None, lang="ky", back=False):
    """
    Флоунун көрүнүшүн Telegram клавиатурасына айлантат.

    МААНИЛҮҮ: callback_data'га 64 байт гана батат, ал эми биздин кээ бир
    опциялар 240 байтка жетет. Ошондуктан баскычка индекс жиберилет
    (o:0, o:1, …), чыныгы маани render()'ди кайра чакырып табылат.
    """
    if not view["options"]:
        return None
    picked = picked or []
    ready = view.get("localized")
    rows = []
    has_home = False
    for i, o in enumerate(view["options"]):
        label = o["label"] if ready else loc(o["label"], lang)
        # «Биздин сайт» — түз шилтеме баскычы: бир басууда браузер ачылат.
        if o["value"] == "tap_site" and SITE_URL and "localhost" not in SITE_URL:
            rows.append([{"text": label[:64], "url": SITE_URL}])
            continue
        if label.lstrip().startswith("🏠"):
            has_home = True
        mark = "☑️ " if (view["multi"] and o["value"] in picked) else ""
        rows.append([{"text": (mark + label)[:64], "callback_data": "o:%d" % i}])
    if view["multi"]:
        rows.append([{"text": m("done_btn", lang), "callback_data": "done"}])
    # Флоу өзү «Башкы меню» сунуштап турса, кайталабайбыз.
    tail = []
    if back:
        tail.append({"text": m("back_btn", lang),
                     "callback_data": "back"})
    if not has_home:
        tail.append({"text": m("home_btn", lang),
                     "callback_data": "home"})
    if tail:
        rows.append(tail)
    return {"inline_keyboard": rows}


def photo_status(chat, u):
    """
    Канча сүрөт жүктөлгөнүн бир билдирүүдө көрсөтөт жана аны
    жаңыртып турат — албом келгенде он билдирүү жаадырбайт.
    """
    lang = ulang(u)
    n = len(u["data"].get("photoFileIds") or [])
    if n >= PHOTO_MAX:
        txt = m("photo_max", lang, PHOTO_MAX)
    elif n >= PHOTO_MIN:
        txt = m("photo_ok", lang, n)
    else:
        txt = m("photo_need", lang, n, PHOTO_MIN - n)
    kb = None
    if n >= PHOTO_MIN:
        kb = {"inline_keyboard": [[{"text": m("photo_done", lang),
                                    "callback_data": "photodone"}]]}
    mid = u.get("photoMsgId")
    if mid:
        r = api("editMessageText", chat_id=chat, message_id=mid,
                text=txt, parse_mode="HTML", reply_markup=kb)
        if r and r.get("ok"):
            return
    r = api("sendMessage", chat_id=chat, text=txt,
            parse_mode="HTML", reply_markup=kb)
    if r and r.get("ok"):
        u["photoMsgId"] = r["result"]["message_id"]


def add_photo(chat, u, fid):
    """Келген сүрөттү тизмеге кошот."""
    ids = u["data"].setdefault("photoFileIds", [])
    if fid not in ids and len(ids) < PHOTO_MAX:
        ids.append(fid)
    photo_status(chat, u)


def ask(chat, u, short=False):
    """
    Учурдагы кадамды көрсөтөт.

    short=True — иш бүткөндөн кийин (издөө, жарыя коюу) башкы меню кыска
    түрдө чыгат: узун саламдашууну ар жолу кайталабай.
    """
    lang = ulang(u)
    view = render(u["step"], u["data"])
    text = view["text"] if view.get("localized") else loc(view["text"], lang)
    if short and u["step"] == "main_menu":
        text = m("menu_short", lang)
    if view["multi"]:
        text += "\n<i>%s</i>" % m("multi_hint", lang)
    if view["photo"]:
        text += "\n<i>%s</i>" % m("photo_hint", lang)
    elif view["input"] and view["placeholder"]:
        text += "\n<i>%s</i>" % esc(loc(view["placeholder"], lang))
    send(chat, text, flow_kb(view, u.get("picked"), lang, back=bool(u.get("hist"))))


# ==================== Жарыяны көрсөтүү ====================

def fmt(r):
    lines = [f"<b>{esc(r['title'])}</b>",
             f"💰 {esc(price_label(r['price']))}",
             f"📍 {esc(r.get('region') or '—')}"]
    if r.get("description"):
        d = r["description"]
        lines.append("\n" + esc(d[:400] + ("…" if len(d) > 400 else "")))
    if r.get("contact"):
        lines.append(f"\n☎️ {esc(r['contact'])}")
    if SITE_URL and "localhost" not in SITE_URL:
        lines.append(f"\n🌐 {SITE_URL}/e/{r['id']}")
    return "\n".join(lines)


def show_results(chat, rows, total, shown, lang="ky"):
    for r in rows:
        photo = os.path.join(MEDIA, r["photo"]) if r.get("photo") else None
        if photo and os.path.isfile(photo):
            send_photo(chat, photo, fmt(r))
        else:
            send(chat, fmt(r))
    if shown < total:
        send(chat, m("more_left", lang, total - shown),
             {"inline_keyboard": [[{"text": m("more_btn", lang),
                                    "callback_data": f"more:{shown}"}]]})
    else:
        send(chat, m("thats_all", lang), home_kb(lang))


def run_search(chat, u):
    """Флоу чогулткан чыпкалар боюнча базадан издейт."""
    lang = ulang(u)
    d = u["data"]
    f = {
        "q":       d.get("keyword"),
        "ad_type": d.get("adType"),
        "cat_id":  d.get("category"),
        "oblast":  d.get("oblast"),
    }
    u["find"] = f
    # Тар издөөдөн кеңге карай: эски жарыяларда ad_type/cat_id бош болушу
    # мүмкүн, ошондуктан чыпкаларды акырындап алып салабыз.
    ladder = [
        dict(f),
        {**f, "cat_id": None},
        {**f, "cat_id": None, "ad_type": None},
        {**f, "cat_id": None, "ad_type": None, "oblast": None},
    ]
    total = 0
    for i, attempt in enumerate(ladder):
        total = core.count(attempt["q"], ad_type=attempt["ad_type"],
                           cat_id=attempt["cat_id"], oblast=attempt["oblast"])
        if total:
            f = attempt
            u["find"] = f
            if i:
                send(chat, m("near", lang))
            break
    if not total:
        reset(u)
        send(chat, m("nothing", lang))
        return
    rows = core.find(f["q"], limit=PER_PAGE, ad_type=f["ad_type"],
                     cat_id=f["cat_id"], oblast=f["oblast"])
    send(chat, m("found", lang, total))
    show_results(chat, rows, total, len(rows), lang)
    reset(u)


def notify_admins(lid, row, uid, name):
    """
    Жаңы жарыя коюлганда админдерге кабар жөнөтөт.

    Жарыя дароо сайтта чыга берет — бул кабар текшерүү үчүн гана.
    Жараксыз болсо, админ бир баскыч менен өчүрөт.
    """
    if not ADMIN_IDS:
        return
    link = (f"\n🌐 {SITE_URL}/e/{lid}"
            if SITE_URL and "localhost" not in SITE_URL else "")
    txt = ("🆕 <b>Жаңы жарыя</b> №%d\n\n"
           "📦 %s\n💰 %s\n📍 %s\n☎️ %s\n"
           "👤 %s (id %s)%s" % (
               lid, esc(row.get("title")), esc(price_label(row.get("price"))),
               esc(row.get("region") or "—"), esc(row.get("contact") or "—"),
               esc(name or "—"), uid, link))
    kb = {"inline_keyboard": [[
        {"text": "❌ Өчүрүү", "callback_data": f"adel:{lid}"}]]}
    photo = os.path.join(MEDIA, f"{lid}.jpg")
    for a in ADMIN_IDS:
        if os.path.isfile(photo):
            send_photo(a, photo, txt, kb)
        else:
            send(a, txt, kb)


# Бир колдонуучу суткасына канча жарыя коё алат
DAILY_LIMIT = int(os.environ.get("DAILY_LIMIT", "10"))


def save_ad(chat, uid, name, u):
    """Даяр жарыяны базага жазат."""
    lang = ulang(u)
    d = u["data"]

    # Спамга каршы: суткасына чектелген сандан ашык жарыя коюлбайт
    if str(uid) not in ADMIN_IDS and core.posted_today(uid) >= DAILY_LIMIT:
        send(chat, "⚠️ Бүгүнкү чек жетти: бир күндө %d жарыя.\n"
                   "Эртең кайра коё аласыз." % DAILY_LIMIT)
        return

    row = bridge.to_listing(d)
    if not row["title"]:
        row["title"] = m("untitled", lang)
    lid = core.add_listing(row, uid, name)

    ids = d.get("photoFileIds") or (
        [d["photoFileId"]] if d.get("photoFileId") else [])
    saved = []
    for i, fid in enumerate(ids[:PHOTO_MAX], 1):
        fn = f"{lid}.jpg" if i == 1 else f"{lid}_{i}.jpg"
        if download_photo(fid, os.path.join(MEDIA, fn)):
            saved.append(fn)
    if saved:
        core.set_photos(lid, saved)

    link = (f"\n\n🌐 {SITE_URL}/e/{lid}"
            if SITE_URL and "localhost" not in SITE_URL else "")
    notify_admins(lid, row, uid, name)
    send(chat, m("posted", lang, lid) + "\n\n"
               f"📦 {esc(row['title'])}\n"
               f"💰 {esc(price_label(row.get('price')))}\n"
               f"📍 {esc(row.get('region') or '—')}{link}", home_kb(lang))
    reset(u)


def ask_title(chat, u):
    """Жарыя сакталардын алдында аталышын сурайт."""
    lang = ulang(u)
    kb = {"inline_keyboard": [[{"text": m("skip_title", lang),
                                "callback_data": "skiptitle"}]]}
    send(chat, m("ask_title", lang), kb)


def do_edit(chat, uid, u, text):
    """Колдонуучу жазган жаңы маанини жарыяга жазат."""
    lang = ulang(u)
    e = u.get("edit") or {}
    if not e:
        return
    if not text:
        send(chat, m("write_smth", lang))
        return
    u.pop("edit", None)
    ok = core.update_listing(e["lid"], uid, {e["field"]: text[:2000]})
    send(chat, m("edit_ok", lang, e["lid"]) if ok else m("edit_fail", lang),
         home_kb(lang))


def show_my(chat, uid, u):
    lang = ulang(u)
    rows = core.my_listings(uid)
    if not rows:
        send(chat, m("no_posts", lang), home_kb(lang))
    else:
        send(chat, m("my_posts", lang, len(rows)))
        for r in rows:
            status = "🟢" if r["is_active"] else "🔴 " + m("removed", lang)
            kb = ({"inline_keyboard": [[
                      {"text": m("edit_btn", lang),
                       "callback_data": f"ed:{r['id']}"},
                      {"text": m("del_btn", lang),
                       "callback_data": f"del:{r['id']}"}]]}
                  if r["is_active"] else None)
            send(chat, f"{status} №{r['id']}\n"
                       f"📦 {esc(r['title'])}\n"
                       f"💰 {esc(price_label(r['price']))}   👁 {r['views']}", kb)
    reset(u)


# ==================== Флоуну алдыга жылдыруу ====================

def _apply_pending(u):
    """Сайттан келген «/start post» сыяктуу тапшырманы аткарат."""
    p = u.pop("pending", None)
    if not p:
        return
    if p == "my":
        u["step"] = "my_posts_phone"
    else:
        u["step"], u["data"] = advance("main_menu", p, dict(u["data"]))


def step_forward(chat, uid, name, u, value):
    """Бир жоопту кабыл алып, кийинки кадамга өтөт."""
    # «Артка» үчүн: учурдагы абалды эстеп калабыз.
    hist = u.setdefault("hist", [])
    hist.append({"step": u["step"],
                 "data": copy.deepcopy(u["data"])})
    del hist[:-25]
    try:
        u["step"], u["data"] = advance(u["step"], value, u["data"])
    except Exception as e:
        print("  Флоу катасы:", e, flush=True)
        lang = ulang(u)
        reset(u)
        send(chat, m("error", lang), home_kb(lang))
        ask(chat, u)
        return
    u["picked"] = []

    if u["step"] in ("main_menu", "language_select"):
        u["hist"] = []

    if u["step"] == "main_menu" and u.get("pending"):
        _apply_pending(u)

    # Атайын кадамдар — база менен иштейт
    if u["step"] == "search_results":
        run_search(chat, u)
        ask(chat, u, short=True)
        return
    if u["step"] == "my_posts":
        show_my(chat, u["data"].get("phone") or uid, u)
        ask(chat, u, short=True)
        return
    if u["step"] == "post_done":
        # Сактаардын алдында аталышты колдонуучунун өзүнөн сурайбыз
        if not u.get("titleasked"):
            u["titleasked"] = True
            ask_title(chat, u)
            return
        save_ad(chat, uid, name, u)
        ask(chat, u, short=True)
        return

    ask(chat, u)


# ==================== Билдирүүлөр ====================

def handle_message(msg, st):
    chat = msg["chat"]["id"]
    uid = str(msg["from"]["id"])
    name = msg["from"].get("first_name", "")
    u = user(st, uid)
    text = (msg.get("text") or "").strip()

    view = render(u["step"], u["data"])

    # Сүрөт күтүлүп жатканда
    if msg.get("photo"):
        if view["photo"]:
            add_photo(chat, u, msg["photo"][-1]["file_id"])
            save_state(st)
        else:
            send(chat, m("no_photo", ulang(u)), None)
        return

    if msg.get("contact"):
        text = msg["contact"].get("phone_number", "") or text

    # Сайттагы ылдыйкы баскычтар ботко «/start post» же «/start my» деп
    # келет — ошолорду түз керектүү кадамга алып барабыз.
    if text in ("/lang", "/til", "/язык"):
        reset(u, full=True)
        ask(chat, u)
        return

    if text.startswith("/start") or text == "/help":
        payload = text[6:].strip() if text.startswith("/start") else ""
        had_lang = bool((u.get("data") or {}).get("uiLanguage"))
        reset(u, full=not had_lang)
        u["pending"] = payload if payload in ("post", "search", "my") else None
        if u["pending"] and had_lang:
            _apply_pending(u)
        ask(chat, u)
        return

    if text in ("🏠 Башкы меню", "🏠 Главное меню",
                "❌ Жокко чыгаруу", "/cancel"):
        reset(u)
        ask(chat, u)
        return

    # ── Жарыяны оңдоо: жаңы маани күтүлүп жатат ──
    if u.get("edit"):
        do_edit(chat, uid, u, text)
        return

    # ── Аталыш күтүлүп жатат ──
    if u.get("titleasked") and u["step"] == "post_done":
        if not text:
            send(chat, m("write_smth", ulang(u)))
            return
        u["data"]["title"] = text[:120]
        save_ad(chat, uid, name, u)
        ask(chat, u, short=True)
        return

    # Текст күтүлүп жатабы?
    if view["photo"]:
        n = len(u["data"].get("photoFileIds") or [])
        if n < PHOTO_MIN:
            send(chat, m("photo_few", ulang(u), PHOTO_MIN))
            return
        u.pop("photoMsgId", None)
        step_forward(chat, uid, name, u, str(n))
        return

    if view["input"]:
        if not text:
            send(chat, m("write_smth", ulang(u)))
            return
        step_forward(chat, uid, name, u, text[:500])
        return

    # Баскычтуу кадамда текст жазылса — жазуусу боюнча дал келтирүү.
    # Баскычтар которулуп чыккандыктан, которулган жазуу менен да
    # салыштырабыз.
    lang = ulang(u)
    for o in view["options"]:
        shown = o["label"] if view.get("localized") else loc(o["label"], lang)
        if text in (o["label"], o["label"][:64], shown, shown[:64]):
            step_forward(chat, uid, name, u, o["value"])
            return

    send(chat, m("use_btn", lang))
    ask(chat, u)


# ==================== Баскыч басылганда ====================

def mark_chosen(chat, cb, view, opt, lang):
    """
    Тандалган баскычты белгилеп, калгандарын алып салат.
    Ошондо чаттын тарыхында эмне тандалганы көрүнүп турат.
    """
    label = opt["label"]
    if not view.get("localized"):
        label = loc(label, lang)
    try:
        api("editMessageReplyMarkup", chat_id=chat,
            message_id=cb["message"]["message_id"],
            reply_markup={"inline_keyboard": [[{
                "text": ("✅ " + label)[:64],
                "callback_data": "chosen"}]]})
    except Exception:
        pass


def handle_callback(cb, st):
    chat = cb["message"]["chat"]["id"]
    uid = str(cb["from"]["id"])
    name = cb["from"].get("first_name", "")
    data = cb.get("data", "")
    u = user(st, uid)
    api("answerCallbackQuery", callback_query_id=cb["id"])

    if data == "back":
        hist = u.get("hist") or []
        if not hist:
            reset(u)
        else:
            prev = hist.pop()
            u["step"] = prev["step"]
            u["data"] = prev["data"]
            u["picked"] = []
            u.pop("photoMsgId", None)
        save_state(st)
        ask(chat, u)
        return

    if data == "home":
        reset(u)
        ask(chat, u)
        return

    if data == "skiptitle":
        # Аталыш жазылбады — bridge.py автоматтык түрдө курат
        if u.get("titleasked") and u["step"] == "post_done":
            save_ad(chat, uid, name, u)
            ask(chat, u, short=True)
        return

    if data.startswith("ed:"):
        lid = int(data[3:])
        lang = ulang(u)
        kb = {"inline_keyboard": [
            [{"text": m("ed_title", lang),   "callback_data": f"edf:{lid}:title"}],
            [{"text": m("ed_price", lang),   "callback_data": f"edf:{lid}:price"}],
            [{"text": m("ed_desc", lang),    "callback_data": f"edf:{lid}:description"}],
            [{"text": m("ed_contact", lang), "callback_data": f"edf:{lid}:contact"}]]}
        send(chat, m("edit_what", lang, lid), kb)
        return

    if data.startswith("edf:"):
        try:
            _, slid, field = data.split(":", 2)
            u["edit"] = {"lid": int(slid), "field": field}
        except ValueError:
            return
        send(chat, m("edit_ask", ulang(u)))
        return

    if data.startswith("del:"):
        lid = int(data[4:])
        if core.deactivate(lid, uid):
            api("editMessageText", chat_id=chat,
                message_id=cb["message"]["message_id"],
                text=m("del_ok", ulang(u), lid))
        else:
            send(chat, m("del_fail", ulang(u)))
        return

    if data.startswith("revive:"):
        lid = int(data[7:])
        if core.revive(lid, uid):
            send(chat, f"✅ Жарыя №{lid} кайра жандырылды, 30 күн турат.")
        else:
            send(chat, f"Жарыя №{lid} табылган жок.")
        return

    if data.startswith("adel:"):
        if uid not in ADMIN_IDS:
            send(chat, "Бул баскыч админдер үчүн.")
            return
        lid = int(data[5:])
        ok = core.admin_deactivate(lid)
        api("editMessageReplyMarkup", chat_id=chat,
            message_id=cb["message"]["message_id"],
            reply_markup={"inline_keyboard": []})
        send(chat, f"🗑 Жарыя №{lid} өчүрүлдү." if ok
                   else f"Жарыя №{lid} табылган жок (мурда өчүрүлгөнбү?).")
        return

    if data.startswith("more:"):
        shown = int(data[5:])
        f = u.get("find") or {}
        total = core.count(f.get("q"), ad_type=f.get("ad_type"),
                           cat_id=f.get("cat_id"), oblast=f.get("oblast"))
        rows = core.find(f.get("q"), limit=PER_PAGE, offset=shown,
                         ad_type=f.get("ad_type"), cat_id=f.get("cat_id"),
                         oblast=f.get("oblast"))
        show_results(chat, rows, total, shown + len(rows), ulang(u))
        return

    view = render(u["step"], u["data"])

    if data == "photodone" or (data.startswith("o:") and view["photo"]):
        n = len(u["data"].get("photoFileIds") or [])
        if n < PHOTO_MIN:
            send(chat, m("photo_few", ulang(u), PHOTO_MIN))
            return
        u.pop("photoMsgId", None)
        step_forward(chat, uid, name, u, str(n))
        return

    if data == "done":
        if not view["multi"]:
            return
        picked = u.get("picked") or []
        if not picked:
            send(chat, m("pick_one", ulang(u)))
            return
        step_forward(chat, uid, name, u, ", ".join(picked))
        return

    if not data.startswith("o:"):
        return

    try:
        i = int(data[2:])
    except ValueError:
        return
    if not (0 <= i < len(view["options"])):
        return
    value = view["options"][i]["value"]

    # Көп тандоо: белгилеп, ошол эле кадамда калабыз
    if view["multi"]:
        picked = u.get("picked") or []
        if value in picked:
            picked.remove(value)
        else:
            picked.append(value)
        u["picked"] = picked
        try:
            api("editMessageReplyMarkup", chat_id=chat,
                message_id=cb["message"]["message_id"],
                reply_markup=flow_kb(view, picked, ulang(u)))
        except Exception:
            pass
        return

    mark_chosen(chat, cb, view, view["options"][i], ulang(u))
    step_forward(chat, uid, name, u, value)


# ==================== Негизги цикл ====================

def start_site():
    """Витринаны фондо жүргүзөт.

    Railway'де эки кызмат түзүү телефондон кыйын болгондуктан,
    бот менен сайт бир процессте иштейт. Экөө тең бир базаны колдонот.
    Сайт керек болбосо: RUN_SITE=0 деп койсоң болот.
    """
    if os.environ.get("RUN_SITE", "1") == "0":
        return
    try:
        import threading
        import tap
        srv = tap.Server(("0.0.0.0", tap.PORT), tap.H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        print(f"  Витрина ачык: порт {tap.PORT}", flush=True)
    except Exception as e:
        print("  Витрина иштебей калды:", e, flush=True)


def expire_worker():
    """
    Күнүнө бир жолу мөөнөтү бүткөн жарыяларды жашырат жана ээсине
    кабар жөнөтөт. Бөлөк жипте, ботко тоскоол болбойт.
    """
    while True:
        try:
            for r in core.expire_old():
                kb = {"inline_keyboard": [[
                    {"text": "🔄 Кайра жандыруу / Возобновить",
                     "callback_data": f"revive:{r['id']}"}]]}
                send(r["tg_id"],
                     "⏳ <b>Жарыяңыздын мөөнөтү бүттү</b>\n\n"
                     f"№{r['id']} — {esc(r['title'])}\n\n"
                     "Керек болсо, бир баскыч менен кайра жандырсаңыз болот.",
                     kb)
        except Exception as e:
            print("  Мөөнөт текшерүү катасы:", e, flush=True)
        time.sleep(6 * 60 * 60)      # алты сааттан кийин кайра карайт


def main():
    global TOKEN, API
    TOKEN = read_token()
    API = f"https://api.telegram.org/bot{TOKEN}/"

    core.init_db()

    # Telegram убактылуу жооп бербей калышы мүмкүн (502, тармак үзүлүшү).
    # Ошондо программаны токтотпойбуз — бир нече жолу кайра сурайбыз,
    # антпесе бот менен кошо сайт да өчүп калат.
    me = {}
    for i in range(6):
        me = api("getMe")
        if me.get("ok"):
            break
        print(f"  getMe жооп бербеди ({i + 1}/6), кайра аракет…", flush=True)
        time.sleep(5)

    if me.get("ok"):
        uname = me["result"].get("username")
    else:
        uname = "?"
        print("  Эскертүү: Telegram жооп бербей жатат. "
              "Бот сурамдарды кийинчерээк улантат.", flush=True)

    threading.Thread(target=expire_worker, daemon=True).start()

    print(f"\n  Бот иштеп жатат: @{uname}", flush=True)
    print(f"  База: {'Postgres' if core.IS_PG else 'SQLite'}", flush=True)
    print(f"  Сүрөттөр: {MEDIA}", flush=True)
    print(f"  Сайт: {SITE_URL}", flush=True)
    try:
        import whatsapp
        print("  WhatsApp: %s" % ("туташкан" if whatsapp.ENABLED
                                  else "өчүк (GREEN_* өзгөрмөлөрү жок)"), flush=True)
    except Exception as e:
        print("  WhatsApp жүктөлбөдү:", e, flush=True)
    start_site()
    print("", flush=True)

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
                print("  Ката:", e, flush=True)
            save_state(st)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Бот токтотулду.\n")
