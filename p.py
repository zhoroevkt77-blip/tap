#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ТАП! патч: ар бир бөлүмгө өз сүрөт чеги.

— Жүк ташуу, Жеткирүү кызматы: 1 сүрөт (унаанын сүрөтү жетиштүү)
— Кызмат көрсөтүү: видео да уруксат (уста аткарган ишин тартат)
— Калгандары: мурункудай 10 сүрөт

tap_flow.py жана bot.py экөөнү тең оңдойт. Идемпотент.
"""
import io
import sys

TAG = "__TAP_PHOTOMAX_V1__"

# ═══════════════════════ tap_flow.py ═══════════════════════
src = io.open("tap_flow.py", encoding="utf-8").read()

if TAG in src:
    print("tap_flow.py: мурун эле коюлган.")
else:
    pairs = [
        # 1. Кызмат көрсөтүүгө видео
        ('VIDEO_TYPES = ("wholesale", "rental")',
         'VIDEO_TYPES = ("wholesale", "rental", "service")',
         "VIDEO_TYPES"),

        # 2. Бир сүрөт менен чектелген бөлүмдөр
        ("PHOTO_STEP_TEXT = (",
         "# " + TAG + "\n"
         "# Бир гана сүрөт жетиштүү болгон бөлүмдөр: унаанын сүрөтү.\n"
         'ONE_PHOTO_TYPES = ("cargo", "delivery")\n'
         "\n"
         "PHOTO_STEP_TEXT = (",
         "PHOTO_STEP_TEXT"),

        # 3. _view: жаңы параметр
        ("          photo=False, final=False, localized=False, video=False):",
         "          photo=False, final=False, localized=False, video=False,\n"
         "          photo_max=None):",
         "_view signature"),

        # 4. _view: жаңы ачкыч
        ('        # video=True — бул кадамда видео да кабыл алынат\n'
         '        "video": video,',
         '        # video=True — бул кадамда видео да кабыл алынат\n'
         '        "video": video,\n'
         '        # photo_max — бул кадамда эң көп канча сүрөт (None = жалпы)\n'
         '        "photo_max": photo_max,',
         "_view body"),

        # 5. post_photo кадамында чекти коюу
        ('    if step == "post_photo":\n'
         '        return _view(PHOTO_STEP_TEXT,\n'
         '                     _opts([("✅ Даяр / Готово", "__photo_done__")]),\n'
         '                     photo=True, video=(at in VIDEO_TYPES))',
         '    if step == "post_photo":\n'
         '        return _view(PHOTO_STEP_TEXT,\n'
         '                     _opts([("✅ Даяр / Готово", "__photo_done__")]),\n'
         '                     photo=True, video=(at in VIDEO_TYPES),\n'
         '                     photo_max=(1 if at in ONE_PHOTO_TYPES else None))',
         "post_photo"),
    ]

    fn = 0
    for old, new, label in pairs:
        if new in src:          # мурун эле коюлган (өзүнчө коюлса да)
            fn += 1
        elif old in src:
            src = src.replace(old, new, 1)
            fn += 1
        else:
            print("!! tap_flow: %s табылган жок" % label)

    if fn == len(pairs):
        io.open("tap_flow.py", "w", encoding="utf-8").write(src)
        print("tap_flow.py: %d/%d блок коюлду." % (fn, len(pairs)))
    else:
        print("tap_flow.py токтотулду: %d/%d — файл өзгөргөн жок."
              % (fn, len(pairs)))
        sys.exit(1)

# ═══════════════════════ bot.py ═══════════════════════
b = io.open("bot.py", encoding="utf-8").read()

if TAG in b:
    print("bot.py: мурун эле коюлган.")
    sys.exit(0)

HELPER = (
    "def step_photo_max(u):\n"
    '    """Ушул кадамда эң көп канча сүрөт болот. ' + TAG + '"""\n'
    "    try:\n"
    '        v = render(u["step"], u["data"]).get("photo_max")\n'
    "    except Exception:\n"
    "        v = None\n"
    "    return min(int(v), PHOTO_MAX) if v else PHOTO_MAX\n"
    "\n"
    "\n"
    "def photo_status(chat, u):"
)

bpairs = [
    ("def photo_status(chat, u):", HELPER, "photo_status"),

    ('    n = len(u["data"].get("photoFileIds") or [])\n'
     "    if n >= PHOTO_MAX:\n"
     '        txt = m("photo_max", lang, PHOTO_MAX)',
     '    n = len(u["data"].get("photoFileIds") or [])\n'
     "    pmax = step_photo_max(u)\n"
     "    if n >= pmax:\n"
     '        txt = m("photo_max", lang, pmax)',
     "photo_status денеси"),

    ('    ids = u["data"].setdefault("photoFileIds", [])\n'
     "    if fid not in ids and len(ids) < PHOTO_MAX:\n"
     "        ids.append(fid)",
     '    ids = u["data"].setdefault("photoFileIds", [])\n'
     "    if fid not in ids and len(ids) < step_photo_max(u):\n"
     "        ids.append(fid)",
     "add_photo"),
]

bn = 0
for old, new, label in bpairs:
    if new in b:                # мурун эле коюлган
        bn += 1
    elif old in b:
        b = b.replace(old, new, 1)
        bn += 1
    else:
        print("!! bot: %s табылган жок" % label)

if bn == len(bpairs):
    io.open("bot.py", "w", encoding="utf-8").write(b)
    print("bot.py: %d/%d блок коюлду." % (bn, len(bpairs)))
else:
    print("bot.py токтотулду: %d/%d — файл өзгөргөн жок." % (bn, len(bpairs)))
    sys.exit(1)
