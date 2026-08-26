#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAP! — Telegram бот.

Меню структурасы tap_flow.py'да ("бир мээ"), бул файл Telegram'дын
"оозу" гана: баскычтарды тартат, жоопторду өткөрөт.

Токен: TELEGRAM_BOT_TOKEN чөйрө өзгөрмөсү, же token.txt файлы.
Иштетүү: python bot.py
"""

import json, os, ssl, time, urllib.parse, urllib.request, mimetypes

import core
from core import MEDIA, SITE_URL, price_label
import bridge
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
    if lang and not full:
        u["step"] = "main_menu"
        u["data"] = {"uiLanguage": lang}
    else:
        u["step"] = START_STEP
        u["data"] = {}


# ==================== Баскычтар ====================

HOME = {"keyboard": [[{"text": "🏠 Башкы меню"}]], "resize_keyboard": True}


def flow_kb(view, picked=None):
    """
    Флоунун көрүнүшүн Telegram клавиатурасына айлантат.

    МААНИЛҮҮ: callback_data'га 64 байт гана батат, ал эми биздин кээ бир
    опциялар 240 байтка жетет. Ошондуктан баскычка индекс жиберилет
    (o:0, o:1, …), чыныгы маани render()'ди кайра чакырып табылат.
    """
    if not view["options"]:
        return None
    picked = picked or []
    rows = []
    for i, o in enumerate(view["options"]):
        mark = "☑️ " if (view["multi"] and o["value"] in picked) else ""
        label = mark + o["label"]
        rows.append([{"text": label[:64], "callback_data": "o:%d" % i}])
    if view["multi"]:
        rows.append([{"text": "✅ Тандап бүттүм", "callback_data": "done"}])
    rows.append([{"text": "🏠 Башкы меню", "callback_data": "home"}])
    return {"inline_keyboard": rows}


def ask(chat, u, short=False):
    """
    Учурдагы кадамды көрсөтөт.

    short=True — иш бүткөндөн кийин (издөө, жарыя коюу) башкы меню кыска
    түрдө чыгат: узун саламдашууну ар жолу кайталабай.
    """
    view = render(u["step"], u["data"])
    text = view["text"]
    if short and u["step"] == "main_menu":
        text = "Эмне кыласыз? / Что делаете? 👇"
    if view["multi"]:
        text += "\n<i>Бир нече тандаса болот — тандап бүткөндөн кийин «Тандап бүттүм» басыңыз.</i>"
    if view["photo"]:
        text += "\n<i>Сүрөттү жөн эле жөнөтүңүз, же «Өткөрүү» деп жазыңыз.</i>"
    elif view["input"] and view["placeholder"]:
        text += "\n<i>%s</i>" % esc(view["placeholder"])
    send(chat, text, flow_kb(view, u.get("picked")))


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
        send(chat, "Баары ушул.", HOME)


def run_search(chat, u):
    """Флоу чогулткан чыпкалар боюнча базадан издейт."""
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
                send(chat, "Так дал келгени табылган жок, жакындарын көрсөтөм 👇")
            break
    if not total:
        reset(u)
        send(chat, "Эч нерсе табылган жок 😔\n"
                   "Башка сөз менен, же башка аймактан аракет кылып көрүңүз.")
        return
    rows = core.find(f["q"], limit=PER_PAGE, ad_type=f["ad_type"],
                     cat_id=f["cat_id"], oblast=f["oblast"])
    send(chat, f"🔎 <b>{total} жарыя табылды</b>")
    show_results(chat, rows, total, len(rows))
    reset(u)


def save_ad(chat, uid, name, u):
    """Даяр жарыяны базага жазат."""
    d = u["data"]
    row = bridge.to_listing(d)
    if not row["title"]:
        row["title"] = "Жарыя"
    lid = core.add_listing(row, uid, name)

    fid = d.get("photoFileId")
    if fid:
        fn = f"{lid}.jpg"
        if download_photo(fid, os.path.join(MEDIA, fn)):
            core.set_photo(lid, fn)

    link = (f"\n\n🌐 {SITE_URL}/e/{lid}"
            if SITE_URL and "localhost" not in SITE_URL else "")
    send(chat, f"✅ <b>Жарыя коюлду!</b>  №{lid}\n\n"
               f"📦 {esc(row['title'])}\n"
               f"💰 {esc(price_label(row.get('price')))}\n"
               f"📍 {esc(row.get('region') or '—')}{link}", HOME)
    reset(u)


def show_my(chat, uid, u):
    rows = core.my_listings(uid)
    if not rows:
        send(chat, "Сизде азырынча жарыя жок.", HOME)
    else:
        send(chat, f"📋 Сизде {len(rows)} жарыя бар:")
        for r in rows:
            status = "🟢" if r["is_active"] else "🔴 (өчүрүлгөн)"
            kb = ({"inline_keyboard": [[{"text": "🗑 Өчүрүү",
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
    try:
        u["step"], u["data"] = advance(u["step"], value, u["data"])
    except Exception as e:
        print("  Флоу катасы:", e, flush=True)
        reset(u)
        send(chat, "Кечиресиз, ката кетти. Башынан баштайлы.", HOME)
        ask(chat, u)
        return
    u["picked"] = []

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
            u["data"]["photoFileId"] = msg["photo"][-1]["file_id"]
            step_forward(chat, uid, name, u, "1")
        else:
            send(chat, "Азыр сүрөт күтүлбөй жатат.", None)
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

    if text in ("🏠 Башкы меню", "❌ Жокко чыгаруу", "/cancel"):
        reset(u)
        ask(chat, u)
        return

    # Текст күтүлүп жатабы?
    if view["photo"]:
        step_forward(chat, uid, name, u, text or "")
        return

    if view["input"]:
        if not text:
            send(chat, "Бир нерсе жазыңыз:")
            return
        step_forward(chat, uid, name, u, text[:500])
        return

    # Баскычтуу кадамда текст жазылса — жазуусу боюнча дал келтирүү
    for o in view["options"]:
        if o["label"][:64] == text or o["label"] == text:
            step_forward(chat, uid, name, u, o["value"])
            return

    send(chat, "Төмөнкү баскычтардан тандаңыз 👇")
    ask(chat, u)


# ==================== Баскыч басылганда ====================

def handle_callback(cb, st):
    chat = cb["message"]["chat"]["id"]
    uid = str(cb["from"]["id"])
    name = cb["from"].get("first_name", "")
    data = cb.get("data", "")
    u = user(st, uid)
    api("answerCallbackQuery", callback_query_id=cb["id"])

    if data == "home":
        reset(u)
        ask(chat, u)
        return

    if data.startswith("del:"):
        lid = int(data[4:])
        if core.deactivate(lid, uid):
            api("editMessageText", chat_id=chat,
                message_id=cb["message"]["message_id"],
                text=f"🔴 Жарыя №{lid} өчүрүлдү.")
        else:
            send(chat, "Өчүрүү мүмкүн болбоду.")
        return

    if data.startswith("more:"):
        shown = int(data[5:])
        f = u.get("find") or {}
        total = core.count(f.get("q"), ad_type=f.get("ad_type"),
                           cat_id=f.get("cat_id"), oblast=f.get("oblast"))
        rows = core.find(f.get("q"), limit=PER_PAGE, offset=shown,
                         ad_type=f.get("ad_type"), cat_id=f.get("cat_id"),
                         oblast=f.get("oblast"))
        show_results(chat, rows, total, shown + len(rows))
        return

    view = render(u["step"], u["data"])

    if data == "done":
        if not view["multi"]:
            return
        picked = u.get("picked") or []
        if not picked:
            send(chat, "Жок дегенде бирөөнү тандаңыз.")
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
                reply_markup=flow_kb(view, picked))
        except Exception:
            pass
        return

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
