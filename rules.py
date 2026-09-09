# -*- coding: utf-8 -*-
"""
ТАП! — платформага көз каранды эмес эрежелер.

Telegram, WhatsApp жана сайт — үчөө тең ушул файлды колдонот.
Ошондо суткалык чек, бонус жана сөз фильтри бир жерде турат,
жаңы платформа кошулганда кайра жазуунун кереги болбойт.
"""
import os
from datetime import datetime, timedelta, timezone

import badwords
import core

# Суткасына канча жарыя коюуга болот
DAILY_LIMIT = int(os.environ.get("DAILY_LIMIT", "10"))

# Бир жарыяга канча сүрөт жана видеонун эң чоң көлөмү (МБ)
PHOTO_MIN = 0
PHOTO_MAX = 10
VIDEO_MAX_MB = int(os.environ.get("VIDEO_MAX_MB", "20"))

# «Жакында бүтөт» деп эсептелчү күн саны
SOON_DAYS = 3

ADMIN_IDS = [x.strip() for x in
             (os.environ.get("ADMIN_IDS") or "").split(",") if x.strip()]


def is_admin(uid):
    return str(uid) in ADMIN_IDS


def check_text(*parts):
    """(деңгээл, сөздөр). Деңгээл: swear / hard / soft / "" """
    return badwords.scan(*parts)


def spend_post(uid):
    """
    Жарыя коюуга уруксат барбы, бонус жумшалдыбы.

    Кайтарат: (ok, bonus_used, bonus_left)
    """
    if is_admin(uid):
        return True, False, 0
    try:
        used = core.posted_today(uid)
    except Exception:
        used = 0
    if used < DAILY_LIMIT:
        return True, False, 0
    if core.use_bonus_post(uid):
        left = int((core.get_user(uid) or {}).get("bonus_posts") or 0)
        return True, True, left
    return False, False, 0


def balance(uid, phone=None):
    """«Менин балансым» экраны үчүн сандар."""
    try:
        me = core.get_user(uid)
    except Exception:
        me = {}
    try:
        used = core.posted_today(uid)
    except Exception:
        used = 0

    active = soon = 0
    try:
        edge = (datetime.now(timezone.utc)
                + timedelta(days=SOON_DAYS)).strftime("%Y-%m-%d")
        for r in core.my_listings(uid, phone):
            if not int(r.get("is_active") or 0):
                continue
            active += 1
            exp = str(r.get("expires_at") or "")[:10]
            if exp and exp <= edge:
                soon += 1
    except Exception as e:
        print("  Баланс катасы:", e, flush=True)

    return {
        "used":    used,
        "limit":   DAILY_LIMIT,
        "left":    max(0, DAILY_LIMIT - used),
        "bonus":   int(me.get("bonus_posts") or 0),
        "friends": int(me.get("ref_count") or 0),
        "active":  active,
        "soon":    soon,
    }
