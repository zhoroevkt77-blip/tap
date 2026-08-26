#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ТАП! — WhatsApp «оозу» (Green API аркылуу).

Бүт логика tap_flow.py'да, бул файл WhatsApp'тын өзгөчөлүктөрүн гана
эсепке алат.

НЕГЕ БАСКЫЧ ЭМЕС, САН?
Green API'нин өз документациясы эскертет: баскыч жиберүү төмөнкү
деңгээлде жасалган, WhatsApp'тын расмий веб-клиенти аны колдобойт,
ошондуктан туруктуулугу WhatsApp'тын өзгөрүүлөрүнө көз каранды. Алар
баскычтарды дайыма кадимки жазуу менен кайталоону, тандоону сандар
менен белгилөөнү сунуштайт. Ошондуктан меню сандуу.

Жанаша пайдасы: Telegram'да 40 райондун баары бир экранга батпай
кыйналчубуз — сандуу тизмеде андай чек жок, барактап көрсөтөбүз.

Керектүү өзгөрмөлөр (Railway → Variables):
    GREEN_ID     — idInstance,      мис. 7107626489
    GREEN_TOKEN  — apiTokenInstance
    GREEN_URL    — apiUrl,          мис. https://7107.api.greenapi.com

Green API'нин жөндөөлөрүндө:
    webhookUrl      = https://<сайттын дареги>/wa
    incomingWebhook = yes
"""

import json
import os
import ssl
import urllib.parse
import urllib.request

import core
from core import MEDIA, SITE_URL, price_label
import bridge
from tap_flow import render, advance, START_STEP

GREEN_ID = (os.environ.get("GREEN_ID") or "").strip()
GREEN_TOKEN = (os.environ.get("GREEN_TOKEN") or "").strip()
GREEN_URL = (os.environ.get("GREEN_URL") or "").strip().rstrip("/")

ENABLED = bool(GREEN_ID and GREEN_TOKEN and GREEN_URL)

PAGE = 9          # бир экранга канча тандоо чыгат
_ctx = ssl.create_default_context()


# ==================== Green API ====================

def _call(method, payload):
    if not ENABLED:
        return None
    url = "%s/waInstance%s/%s/%s" % (GREEN_URL, GREEN_ID, method, GREEN_TOKEN)
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=40, context=_ctx) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("  WhatsApp катасы:", method, e, flush=True)
        return None


def send(chat_id, text):
    return _call("sendMessage", {"chatId": chat_id, "message": text[:3500]})


def send_file(chat_id, path, caption=""):
    """Сүрөттү сайттын дареги аркылуу жиберет."""
    if not (SITE_URL and "localhost" not in SITE_URL):
        return send(chat_id, caption)
    name = os.path.basename(path)
    return _call("sendFileByUrl", {
        "chatId": chat_id,
        "urlFile": "%s/media/%s" % (SITE_URL.rstrip("/"), name),
        "fileName": name,
        "caption": caption[:900],
    })


def download(url, dest):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TAP/1.0"})
        with urllib.request.urlopen(req, timeout=60, context=_ctx) as r:
            data = r.read()
        os.makedirs(MEDIA, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print("  Сүрөт жүктөлбөдү:", e, flush=True)
        return False


# ==================== Абалдар ====================
# Telegram'дын bot_state.json'у менен чаташпашы үчүн өзүнчө файл.

STATE_FILE = os.path.join(core.DATA_DIR, "wa_state.json")
_state = None


def _load():
    global _state
    if _state is None:
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                _state = json.load(f)
        except Exception:
            _state = {}
    return _state


def _save():
    try:
        os.makedirs(os.path.dirname(STATE_FILE) or ".", exist_ok=True)
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_state, f, ensure_ascii=False)
        os.replace(tmp, STATE_FILE)
    except Exception:
        pass


def _user(chat_id):
    st = _load()
    return st.setdefault(chat_id, {"step": START_STEP, "data": {},
                                   "picked": [], "page": 0, "find": {}})


def _reset(u, full=False):
    lang = (u.get("data") or {}).get("uiLanguage")
    u["picked"] = []
    u["page"] = 0
    if lang and not full:
        u["step"] = "main_menu"
        u["data"] = {"uiLanguage": lang}
    else:
        u["step"] = START_STEP
        u["data"] = {}


# ==================== Менюну жазууга айлантуу ====================

def _clean(label):
    """Баскычтын жазуусунан эмодзини алып, эки тилдүүнү кыскартат."""
    s = "".join(ch for ch in str(label) if ord(ch) < 0x1F000).strip()
    return s or str(label).strip()


def _menu(view, u):
    """Тандоолорду сандуу тизме кылып жазат. Керек болсо барактайт."""
    opts = view["options"]
    total = len(opts)
    page = u.get("page", 0)
    start = page * PAGE
    chunk = opts[start:start + PAGE]

    lines = [view["text"], ""]
    for i, o in enumerate(chunk, start=start + 1):
        lines.append("*%d* — %s" % (i, _clean(o["label"])))

    lines.append("")
    if total > PAGE:
        pages = (total + PAGE - 1) // PAGE
        nav = []
        if start + PAGE < total:
            nav.append("*+* — кийинки")
        if page:
            nav.append("*-* — мурунку")
        lines.append("(%d/%d бет)  %s" % (page + 1, pages, "   ".join(nav)))

    if view["multi"]:
        picked = u.get("picked") or []
        if picked:
            lines.append("Тандалды: %s" % ", ".join(_clean(x) for x in picked))
        lines.append("_Бир нечесин үтүр менен жазсаңыз болот: 1,3,5_")
        lines.append("*0* — тандап бүттүм")

    lines.append("*Меню* — башына кайтуу")
    return "\n".join(lines)


def _screen(chat_id, u, short=False):
    """
    Учурдагы кадамды көрсөтөт.

    short=True — иш бүткөндөн кийин башкы меню кыска чыгат: узун
    саламдашууну ар бир издөөдөн кийин кайталабай.
    """
    view = render(u["step"], u["data"])

    if view["options"]:
        if short and u["step"] == "main_menu":
            view = dict(view, text="Эмне кыласыз? / Что делаете? 👇")
        send(chat_id, _menu(view, u))
        return

    text = view["text"]
    if view["photo"]:
        text += "\n\n_Сүрөттү жөн эле жөнөтүңүз, же «өткөрүү» деп жазыңыз._"
    elif view["placeholder"]:
        text += "\n\n_%s_" % view["placeholder"]
    text += "\n\n*Меню* — башына кайтуу"
    send(chat_id, text)


# ==================== Жоопту окуу ====================

def _pick(view, u, text):
    """
    Колдонуучунун жообун маанige айлантат.
    Кайтарат: ("value", маани) | ("page", ±1) | ("multi", None) | (None, None)
    """
    opts = view["options"]
    t = text.strip().lower()

    if t in ("+", "кийинки", "далее", "next"):
        return ("page", 1)
    if t in ("-", "мурунку", "назад", "back"):
        return ("page", -1)

    if view["multi"]:
        if t in ("0", "бүттү", "болду", "готово"):
            return ("multi", None)
        nums, ok = [], True
        for part in t.replace(" ", "").split(","):
            if part.isdigit() and 1 <= int(part) <= len(opts):
                nums.append(int(part))
            elif part:
                ok = False
        if nums and ok:
            picked = u.get("picked") or []
            for n in nums:
                v = opts[n - 1]["value"]
                if v in picked:
                    picked.remove(v)
                else:
                    picked.append(v)
            u["picked"] = picked
            return ("marked", None)

    if t.isdigit() and 1 <= int(t) <= len(opts):
        return ("value", opts[int(t) - 1]["value"])

    # Жазуусу боюнча дал келтирүү
    for o in opts:
        if _clean(o["label"]).lower() == t:
            return ("value", o["value"])
    return (None, None)


# ==================== Базага жазуу / издөө ====================

def _save_ad(chat_id, u):
    d = u["data"]
    row = bridge.to_listing(d)
    if not row["title"]:
        row["title"] = "Жарыя"
    lid = core.add_listing(row, chat_id.split("@")[0], d.get("waName", ""))

    src = d.get("photoUrl")
    if src:
        fn = "%s.jpg" % lid
        if download(src, os.path.join(MEDIA, fn)):
            core.set_photo(lid, fn)

    link = ("\n\n%s/e/%s" % (SITE_URL, lid)
            if SITE_URL and "localhost" not in SITE_URL else "")
    send(chat_id,
         "✅ *Жарыя коюлду!*  №%s\n\n📦 %s\n💰 %s\n📍 %s%s"
         % (lid, row["title"], price_label(row.get("price")),
            row.get("region") or "—", link))
    _reset(u)


def _search(chat_id, u):
    d = u["data"]
    f = {"q": d.get("keyword"), "ad_type": d.get("adType"),
         "cat_id": d.get("category"), "oblast": d.get("oblast")}
    ladder = [dict(f),
              {**f, "cat_id": None},
              {**f, "cat_id": None, "ad_type": None},
              {**f, "cat_id": None, "ad_type": None, "oblast": None}]
    total, chosen = 0, f
    for i, a in enumerate(ladder):
        total = core.count(a["q"], ad_type=a["ad_type"],
                           cat_id=a["cat_id"], oblast=a["oblast"])
        if total:
            chosen = a
            if i:
                send(chat_id, "Так дал келгени табылган жок, жакындарын көрсөтөм 👇")
            break
    if not total:
        send(chat_id, "Эч нерсе табылган жок 😔\n"
                      "Башка сөз менен, же башка аймактан аракет кылып көрүңүз.")
        _reset(u)
        return

    rows = core.find(chosen["q"], limit=5, ad_type=chosen["ad_type"],
                     cat_id=chosen["cat_id"], oblast=chosen["oblast"])
    send(chat_id, "🔎 *%d жарыя табылды*" % total)
    for r in rows:
        _show(chat_id, r)
    if total > len(rows):
        send(chat_id, "Дагы %d жарыя бар. Баарын сайттан көрүңүз:\n%s"
             % (total - len(rows), SITE_URL))
    _reset(u)


def _show(chat_id, r):
    parts = ["*%s*" % r["title"], "💰 %s" % price_label(r["price"]),
             "📍 %s" % (r.get("region") or "—")]
    if r.get("description"):
        parts.append("\n" + r["description"][:350])
    if r.get("contact"):
        parts.append("\n☎️ %s" % r["contact"])
    if SITE_URL and "localhost" not in SITE_URL:
        parts.append("\n%s/e/%s" % (SITE_URL, r["id"]))
    text = "\n".join(parts)

    photo = os.path.join(MEDIA, r["photo"]) if r.get("photo") else None
    if photo and os.path.isfile(photo):
        send_file(chat_id, photo, text)
    else:
        send(chat_id, text)


def _my(chat_id, u):
    rows = core.my_listings(u["data"].get("phone") or chat_id.split("@")[0])
    if not rows:
        send(chat_id, "Сизде азырынча жарыя жок.")
    else:
        send(chat_id, "📋 Сизде %d жарыя бар:" % len(rows))
        for r in rows[:10]:
            mark = "🟢" if r["is_active"] else "🔴"
            send(chat_id, "%s №%s\n📦 %s\n💰 %s   👁 %s"
                 % (mark, r["id"], r["title"], price_label(r["price"]), r["views"]))
    _reset(u)


# ==================== Негизги кабылдагыч ====================

def _forward(chat_id, u, value):
    try:
        u["step"], u["data"] = advance(u["step"], value, u["data"])
    except Exception as e:
        print("  Флоу катасы:", e, flush=True)
        _reset(u)
        send(chat_id, "Кечиресиз, ката кетти. Башынан баштайлы.")
        _screen(chat_id, u)
        return
    u["picked"] = []
    u["page"] = 0

    done = u["step"] in ("search_results", "my_posts", "post_done")
    if u["step"] == "search_results":
        _search(chat_id, u)
    elif u["step"] == "my_posts":
        _my(chat_id, u)
    elif u["step"] == "post_done":
        _save_ad(chat_id, u)
    _screen(chat_id, u, short=done)


def handle(body):
    """Green API'ден келген webhook'ту иштетет."""
    if body.get("typeWebhook") != "incomingMessageReceived":
        return

    sender = body.get("senderData") or {}
    chat_id = sender.get("chatId") or ""
    if not chat_id or chat_id.endswith("@g.us"):
        return                      # топтогу жазышууга кийлигишпейбиз

    md = body.get("messageData") or {}
    kind = md.get("typeMessage") or ""
    text, photo_url = "", None

    if kind in ("textMessage", "extendedTextMessage"):
        text = ((md.get("textMessageData") or {}).get("textMessage")
                or (md.get("extendedTextMessageData") or {}).get("text") or "")
    elif kind == "imageMessage":
        fd = md.get("fileMessageData") or {}
        photo_url = fd.get("downloadUrl")
        text = fd.get("caption") or ""
    elif kind == "interactiveButtonsReply":
        text = ((md.get("interactiveButtonsReply") or {}).get("buttonText") or "")
    else:
        return

    text = (text or "").strip()
    u = _user(chat_id)
    u["data"]["waName"] = sender.get("senderName") or ""

    if text.lower() in ("меню", "menu", "старт", "start", "/start", "баштоо"):
        _reset(u, full=not u["data"].get("uiLanguage"))
        _screen(chat_id, u)
        _save()
        return

    if text.lower() in ("тил", "/lang", "язык"):
        _reset(u, full=True)
        _screen(chat_id, u)
        _save()
        return

    view = render(u["step"], u["data"])

    if photo_url:
        if view["photo"]:
            u["data"]["photoUrl"] = photo_url
            _forward(chat_id, u, "1")
        else:
            send(chat_id, "Азыр сүрөт күтүлбөй жатат.")
        _save()
        return

    if not text:
        _save()
        return

    if view["photo"]:
        _forward(chat_id, u, text)
        _save()
        return

    if view["input"]:
        _forward(chat_id, u, text[:500])
        _save()
        return

    kind_, val = _pick(view, u, text)
    if kind_ == "value":
        _forward(chat_id, u, val)
    elif kind_ == "page":
        total = len(view["options"])
        last = (total - 1) // PAGE
        u["page"] = max(0, min(last, u.get("page", 0) + val))
        _screen(chat_id, u)
    elif kind_ == "marked":
        _screen(chat_id, u)
    elif kind_ == "multi":
        picked = u.get("picked") or []
        if picked:
            _forward(chat_id, u, ", ".join(picked))
        else:
            send(chat_id, "Жок дегенде бирөөнү тандаңыз.")
            _screen(chat_id, u)
    else:
        send(chat_id, "Тизмедеги санды жазыңыз 👇")
        _screen(chat_id, u)

    _save()
