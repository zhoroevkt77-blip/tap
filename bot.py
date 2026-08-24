#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAP! — Telegram бот.

Токен: TELEGRAM_BOT_TOKEN чөйрө өзгөрмөсү, же token.txt файлы.
Иштетүү: python bot.py
"""

import json, os, ssl, time, urllib.parse, urllib.request, mimetypes

import core
from core import (CATS, SUBS, MEDIA, SITE_URL, sub_title, used_regions, price_label)

TOKEN_FILE = os.path.join(core.BASE, "token.txt")
STATE_FILE = os.path.join(core.BASE, "bot_state.json")
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
        tmp = STATE_FILE + ".tmp"
        json.dump(st, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
        os.replace(tmp, STATE_FILE)
    except Exception:
        pass   # диск жазылбаса да бот иштей берсин


# ==================== Баскычтар ====================

MENU = {"keyboard": [
    [{"text": "📢 Жарыя берем"}, {"text": "🔍 Издеймин"}],
    [{"text": "📋 Менин жарыяларым"}]], "resize_keyboard": True}

SKIP = {"keyboard": [[{"text": "⏭ Өткөрүү"}], [{"text": "❌ Жокко чыгаруу"}]],
        "resize_keyboard": True}

CANCEL = {"keyboard": [[{"text": "❌ Жокко чыгаруу"}]], "resize_keyboard": True}


def cat_kb(prefix, with_all=False):
    rows = []
    if with_all:
        rows.append([{"text": "🔎 Бардыгы", "callback_data": f"{prefix}:all"}])
    items = list(CATS.items())
    for i in range(0, len(items), 2):
        rows.append([{"text": f"{ic} {nm}", "callback_data": f"{prefix}:{c}"}
                     for c, (nm, ic) in items[i:i + 2]])
    return {"inline_keyboard": rows}


def sub_kb(cat, prefix, with_all=False):
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
    for r in core.REGIONS:
        row.append({"text": r})
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([{"text": "❌ Жокко чыгаруу"}])
    return {"keyboard": rows, "resize_keyboard": True}


def find_region_kb():
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
                         [{"text": "❌ Жокко чыгаруу"}]], "resize_keyboard": True}


# ==================== Жарыяны көрсөтүү ====================

def fmt(r):
    nm, ic = CATS.get(r["category"], ("—", ""))
    sn = sub_title(r["category"], r.get("subcat"))
    lines = [f"<b>{esc(r['title'])}</b>",
             f"💰 {esc(price_label(r['price']))}",
             f"{ic} {esc(sn or nm)}   📍 {esc(r['region'] or '—')}"]
    if r.get("description"):
        d = r["description"]
        lines.append("\n" + esc(d[:300] + ("…" if len(d) > 300 else "")))
    if r.get("contact"):
        lines.append(f"\n☎️ {esc(r['contact'])}")
    if SITE_URL and "localhost" not in SITE_URL:
        lines.append(f"\n🌐 {SITE_URL}/e/{r['id']}")
    return "\n".join(lines)


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


# ==================== Билдирүүлөр ====================

def handle_message(msg, st):
    chat = msg["chat"]["id"]
    uid = str(msg["from"]["id"])
    name = msg["from"].get("first_name", "")
    u = st["users"].setdefault(uid, {"step": None, "data": {}})
    text = (msg.get("text") or "").strip()

    if msg.get("photo") and u["step"] == "photo":
        u["data"]["photo_file_id"] = msg["photo"][-1]["file_id"]
        u["step"] = "contact"
        send(chat, "<b>6/6</b> Байланыш телефонуңузду жазыңыз:\n"
                   "<i>мисалы: +996700123456</i>", phone_kb())
        return

    if msg.get("contact") and u["step"] == "contact":
        text = msg["contact"].get("phone_number", "")

    if text in ("❌ Жокко чыгаруу", "/cancel"):
        u["step"] = None; u["data"] = {}
        send(chat, "Жокко чыгарылды.", MENU)
        return

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
        d = u["data"]
        lid = core.add_listing(d, uid, name)

        fid = d.get("photo_file_id")
        if fid:
            fn = f"{lid}.jpg"
            if download_photo(fid, os.path.join(MEDIA, fn)):
                core.set_photo(lid, fn)

        u["step"] = None; u["data"] = {}
        link = (f"\n\n🌐 {SITE_URL}/e/{lid}"
                if SITE_URL and "localhost" not in SITE_URL else "")
        send(chat, f"✅ <b>Жарыя коюлду!</b>  №{lid}\n\n"
                   f"📦 {esc(d['title'])}\n"
                   f"💰 {esc(price_label(d.get('price')))}\n"
                   f"📍 {esc(d.get('region') or '—')}{link}", MENU)
        return

    # ---------- Издөө ----------
    if text == "🔍 Издеймин":
        u["step"] = "find_cat"; u["data"] = {}
        send(chat, "Кайсы категориядан издейли?", cat_kb("fc", with_all=True))
        return

    if u["step"] == "find_q":
        q = None if text.lower() in ("бардыгы", "баары", "все", "-") else text
        u["data"]["q"] = q
        cat, reg, sub = u["data"].get("cat"), u["data"].get("reg"), u["data"].get("sub")
        total = core.count(q, cat, reg, sub)
        if not total:
            u["step"] = None
            where = f" ({reg})" if reg else ""
            send(chat, f"Эч нерсе табылган жок{esc(where)} 😔\n"
                       "Башка сөз менен, же башка аймактан аракет кылып көрүңүз.", MENU)
            return
        rows = core.find(q, cat, reg, sub, limit=PER_PAGE)
        u["step"] = "browsing"
        place = f" · 📍 {esc(reg)}" if reg else ""
        send(chat, f"🔎 <b>{total} жарыя табылды</b>{place}")
        show_results(chat, rows, total, len(rows))
        return

    # ---------- Менин жарыяларым ----------
    if text == "📋 Менин жарыяларым":
        u["step"] = None
        rows = core.my_listings(uid)
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
                       f"💰 {esc(price_label(r['price']))}   👁 {r['views']}", kb)
        return

    send(chat, "Менюдан тандаңыз 👇", MENU)


# ==================== Баскыч басылганда ====================

def _ask_region(chat, u):
    regs = used_regions()
    if len(regs) > 1:
        u["step"] = "find_reg"
        send(chat, "Кайсы аймактан издейли?", find_region_kb())
    else:
        u["data"]["reg"] = None
        u["step"] = "find_q"
        send(chat, "Ачкыч сөз жазыңыз.\n"
                   "<i>Баарын көрүү үчүн «баары» деп жазыңыз</i>", CANCEL)


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
        _ask_region(chat, u)

    elif data.startswith("fs:"):
        code = data[3:]
        u["data"]["sub"] = None if code == "all" else code
        _ask_region(chat, u)

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
        d = u["data"]
        total = core.count(d.get("q"), d.get("cat"), d.get("reg"), d.get("sub"))
        rows = core.find(d.get("q"), d.get("cat"), d.get("reg"), d.get("sub"),
                         limit=PER_PAGE, offset=shown)
        show_results(chat, rows, total, shown + len(rows))

    elif data.startswith("del:"):
        lid = int(data[4:])
        if core.deactivate(lid, uid):
            api("editMessageText", chat_id=chat,
                message_id=cb["message"]["message_id"],
                text=f"🔴 Жарыя №{lid} өчүрүлдү.")
        else:
            send(chat, "Өчүрүү мүмкүн болбоду.")


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


def main():
    global TOKEN, API
    TOKEN = read_token()
    API = f"https://api.telegram.org/bot{TOKEN}/"

    core.init_db()
    me = api("getMe")
    if not me.get("ok"):
        raise SystemExit("Токен туура эмес окшойт.")

    print(f"\n  Бот иштеп жатат: @{me['result'].get('username')}", flush=True)
    print(f"  База: {'Postgres' if core.IS_PG else 'SQLite'}", flush=True)
    print(f"  Сайт: {SITE_URL}", flush=True)
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

