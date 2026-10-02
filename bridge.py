# -*- coding: utf-8 -*-
"""
ТАП! — эски база менен жаңы менюну байланыштыруучу көпүрө.

Жаңы меню (tap_catalog) 100дөн ашык категориядан турат, ал эми базадагы
`category` тилкеси эски 6 категорияны күтөт жана сайт (tap.py) ошону
колдонот. Ошондуктан:

  • жаңы толук маалымат  -> жаңы тилкелерге (ad_type, cat_id, sub_id, …)
  • эски `category`/`subcat` -> ушул көпүрө аркылуу толтурулат

Натыйжада сайт эч өзгөрүүсүз иштей берет, бот болсо толук менюну колдонот.
"""

# ---------------------------------------------------------------------------
# Категориянын коду -> адам окуй турган аты
# ---------------------------------------------------------------------------
# Эски жарыяларда аталыш ордуна ички код (мисалы "appliances_home") жазылып
# калган. Ушул карта аркылуу код көрсөтүүдө нормалдуу атка айландырылат.
try:
    import tap_catalog as _tc
except Exception:          # каталог жок болсо да көпүрө иштей берсин
    _tc = None

CAT_LABELS = {}
if _tc is not None:
    for _name in ("TRADE_CATEGORIES", "SERVICE_CATEGORIES", "RENTAL_CATEGORIES",
                  "DELIVERY_CATEGORIES", "JOB_CATEGORIES", "MARKETS_TYPES",
                  "WHOLESALE_CATEGORIES", "CARGO_CATEGORIES", "JOBSEEK_CATEGORIES",
                  "PROPERTY_CATEGORIES", "VEHICLE_SALE_CATEGORIES"):
        for _c in (getattr(_tc, _name, None) or []):
            if isinstance(_c, dict) and _c.get("id"):
                CAT_LABELS.setdefault(_c["id"], _c.get("label") or _c["id"])

SECTION_LABELS = {
    "wholesale": "Соода-сатык (дүң) / Оптовая торговля",
    "property":  "Мүлк сатуу / Продажа имущества",
    "vehicle":   "Унаа сатуу / Продажа транспорта",
    "cargo":     "Жүк ташуу / Грузоперевозки",
    "jobseek":   "Жумуш издөө / Поиск работы",
    "trade":    "Соода-сатык / Торговля",
    "service":  "Кызмат көрсөтүү / Услуги",
    "rental":   "Ижарага берүү / Аренда",
    "delivery": "Жеткирүү / Доставка",
    "job":      "Жумуш берүү / Работа",
    "markets":  "Базарлар / Рынки",
    "malls":    "Соода борборлору / Торговые центры",
    "taxi":     "Такси / Такси",
}


# ── Кыргызча → орусча сөздүк ──────────────────────────────────
# Каталогдогу маанилер «кыргызча / орусча» түрүндө жазылган, бирок
# базага кыргызчасы гана сакталат (bridge._first). Ошондуктан орусча
# режимде аларды кайра которуш керек. Сөздүктү каталогдун өзүнөн
# чогултабыз: жаңы категория кошулса, котормосу өзүнөн-өзү пайда болот.
RU_MAP = {}


def _pair_ru(label, value):
    """
    {"label": "1 апта (7 күн) / 1 неделя (7 дней) — 100 сом",
     "value": "1 апта"} → RU_MAP["1 апта"] = "1 неделя"

    Базага `value` сакталат, ал эми котормо `label`дин оң жагында
    турат. Ошондуктан экөөн байланыштырабыз: баасы, кашаадагы
    түшүндүрмө жана эмодзи алынып салынат.
    """
    if not isinstance(label, str) or not isinstance(value, str):
        return
    if " / " not in label or value.startswith("__"):
        return
    ru = label.partition(" / ")[2].strip()
    ru = ru.split(" — ")[0].strip()          # «— 100 сом» кесилет
    if "(" not in value and "(" in ru:       # кашаа маанисинде жок болсо
        ru = ru.split(" (")[0].strip()
    if ru and ru != value:
        RU_MAP.setdefault(value.strip(), ru)


def _collect_ru(obj, depth=0):
    """Каталогдон «A / B» түрүндөгү саптарды таап, сөздүккө жазат."""
    if depth > 20:
        return
    if isinstance(obj, dict) and "label" in obj and "value" in obj:
        _pair_ru(obj.get("label"), obj.get("value"))
    if isinstance(obj, str):
        if " / " in obj:
            ky, _, ru = obj.partition(" / ")
            ky, ru = ky.strip(), ru.strip()
            if ky and ru and ky != ru:
                RU_MAP.setdefault(ky, ru)
        return
    if isinstance(obj, dict):
        for v in obj.values():
            _collect_ru(v, depth + 1)
        return
    if isinstance(obj, (list, tuple, set)):
        for v in obj:
            _collect_ru(v, depth + 1)


try:
    import tap_catalog as _tc
    for _nm in dir(_tc):
        if _nm.startswith("_"):
            continue
        _v = getattr(_tc, _nm)
        if isinstance(_v, (list, tuple, dict)):
            _collect_ru(_v)
except Exception as _e:      # каталог жүктөлбөсө, сайт иштей берсин
    print("RU_MAP курулбады:", _e)

# Агымдын өзүндөгү варианттар («Чекене / Розница» ж.б.) функциялардын
# ичинде жазылган, ошондуктан модулдан окуй албайбыз. Файлдын текстин
# сканерлейбиз: бул бир жолу, ишке киргенде гана болот.
try:
    import os as _os
    import re as _re
    _p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                       "tap_flow.py")
    _src = open(_p, encoding="utf-8").read()
    for _m in _re.findall(r'"([^"\n]{2,90} / [^"\n]{2,90})"', _src):
        _collect_ru(_m)
except Exception as _e:
    print("Агымдан котормо алынбады:", _e)

# Сүрөттөмөдөгү талаалардын аттары — кол менен жазылган, ошондуктан
# котормосу да ушул жерде турат.
RU_MAP.update({
    "Түрү": "Вид",                    "Сатуу": "Продажа",
    "Жеткирүү": "Доставка",           "Тукуму": "Порода",
    "Жашы/саны": "Возраст/кол-во",    "Абалы": "Состояние",
    "Маркасы": "Марка",               "Жылы": "Год",
    "Кыймылдаткыч": "Двигатель",      "Соода орду": "Торговое место",
    "Сапаты": "Качество",             "Карго": "Карго",
    "Дүкөн": "Магазин",               "Акция": "Акция",
    "Кабаты": "Этаж",                 "Иш убактысы": "Часы работы",
    "Багыты": "Направление",          "Дареги": "Адрес",
    "Мүнөздөмөсү": "Характеристики",  "Депозит": "Депозит",
    "Милдеттери": "Обязанности",      "Талаптар": "Требования",
    "Шарттары": "Условия",            "Чалуу убактысы": "Время звонка",
    "Мөөнөтү": "Срок",                "Аты": "Имя",
    "Машина": "Машина",               "Күнү": "Дата",
    "Саат": "Время",                  "Бош орун": "Свободных мест",
    "Жүргүнчү": "Пассажиры",          "Жүк": "Багаж",
    "Эң аз буйрутма": "Мин. заказ",
})


def ru_value(text, lang="ky"):
    """
    Базадан келген кыргызча маанини орусчага которот.

    Табылбаса, ошол бойдон кайтарат — жарым котормо жарым-жартылай
    көрүнгөнчө, кыргызчасы турганы жакшы.
    """
    if lang != "ru" or not text:
        return text
    t = str(text).strip()
    if t in RU_MAP:
        return RU_MAP[t]
    # «A | B | C» түрүндөгү курама аталыш — ар бир бөлүгүн өзүнчө
    if "|" in t:
        return " | ".join(ru_value(p.strip(), "ru") for p in t.split("|"))
    if ":" in t:  #COLON_SPLIT
        _a, _, _b = t.partition(":")
        _ra, _rb = ru_value(_a.strip(), "ru"), ru_value(_b.strip(), "ru")
        if _ra != _a.strip() or _rb != _b.strip():
            return _ra + ": " + _rb
    for _sep in (", ", " · "):   # RUDICT: бир нече маани («Свет бар, Суу бар»)
        if _sep in t:
            _src = [x.strip() for x in t.split(_sep)]
            _out = [ru_value(x, "ru") for x in _src]
            if _out != _src:
                return _sep.join(_out)
    return t


def cat_label(cat_id):
    """Категориянын кодун эки тилдүү атка айландырат."""
    if not cat_id:
        return ""
    return CAT_LABELS.get(cat_id, "")


def is_code(text):
    """Текст аталыш эмес, ички код экенин аныктайт."""
    t = (text or "").strip()
    if not t:
        return False
    if t in CAT_LABELS or t in SECTION_LABELS:
        return True
    # "appliances_home" сыяктуу: астын сызык бар, бош орун жок, баары кичине тамга
    return ("_" in t) and (" " not in t) and t.islower() and t.isascii()


def show_title(row):
    """
    Жарыяны көрсөткөндө колдонулуучу аталыш.

    Базадагы аталыш ички код болуп калса (эски жарыялар), категориянын
    атын кайтарат. Базага тийбейт — экрандагы жазуу гана оңолот.
    """
    row = row or {}
    t = str(row.get("title") or "").strip()
    if t and not is_code(t):
        # «appliances_home | Чекене | …» сыяктуу аталыштын биринчи бөлүгү
        # ички код болуп калышы мүмкүн — ошону гана атка алмаштырабыз.
        head, sep, tail = t.partition(" | ")
        if sep and is_code(head):
            lbl = cat_label(head)
            if lbl:
                return short_title(lbl.split(" / ")[0] + sep + tail)
        return short_title(t)
    cid = row.get("cat_id") or (t if t else "")
    lbl = cat_label(cid)
    if lbl:
        return lbl
    sub = str(row.get("sub_id") or "").strip()
    if sub:
        return sub
    return SECTION_LABELS.get(row.get("ad_type") or "", "Жарыя / Объявление")


# Жаңы категория -> эски категория коду
_TRADE_MAP = {
    "realestate":            ("realty",   "flat"),
    "vehicles":              ("transport", "car"),
    "agro_machinery":        ("transport", "truck"),
    "auto_parts":            ("transport", "parts"),
    "smartphones":           ("personal", "phone"),
    "computers":             ("personal", "comp"),
    "electronics":           ("personal", "tech"),
    "appliances_home":       ("personal", "tech"),
    "furniture":             ("personal", "furn"),
    "clothing":              ("personal", "cloth"),
    "footwear":              ("personal", "cloth"),
    "watches_jewelry":       ("personal", "other"),
    "construction_materials": ("shop",    "build"),
    "tools":                 ("shop",     "build"),
    "animals":               ("business", "other"),
    "kids":                  ("personal", "kids"),
    "sport":                 ("personal", "other"),
    "food":                  ("shop",     "food"),
    "beauty_goods":          ("personal", "other"),
    "medicine":              ("personal", "other"),
    "carpets":               ("personal", "furn"),
    "national":              ("personal", "other"),
    "books":                 ("personal", "other"),
    "handicraft":            ("personal", "other"),
    "optics":                ("personal", "other"),
    "toys_games":            ("personal", "kids"),
    "flowers":               ("personal", "other"),
    "heating_fuel":          ("shop",     "build"),
    "trade_other":           ("personal", "other"),
}

_SERVICE_MAP = {
    "home":          ("service", "build"),
    "construction":  ("service", "build"),
    "transport":     ("service", "transport"),
    "beauty":        ("service", "beauty"),
    "edu":           ("service", "teach"),
    "it":            ("service", "other"),
    "photo":         ("service", "other"),
    "events":        ("service", "other"),
    "agro":          ("service", "other"),
    "legal":         ("service", "other"),
    "family":        ("service", "other"),
    "moving":        ("service", "transport"),
    "pet_services":  ("service", "other"),
    "appliance_svc": ("service", "repair"),
    "money_transfer": ("service", "other"),
    "religious":     ("service", "other"),
    "tattoo":        ("service", "beauty"),
    "other":         ("service", "other"),
}

_RENTAL_MAP = {
    "rent_residential": ("realty",    "rent"),
    "rent_commercial":  ("realty",    "commerce"),
    "rent_land":        ("realty",    "land"),
    "rent_car":         ("transport", "car"),
    "rent_truck":       ("transport", "truck"),
    "rent_bus":         ("transport", "truck"),
    "rent_special":     ("transport", "truck"),
}

_JOB_MAP = {
    "drivers":      ("business", "other"),
    "construction": ("business", "other"),
}

_DELIVERY_DEFAULT = ("service", "transport")


def to_legacy(ad_type, cat_id):
    """
    Жаңы (ad_type, cat_id) жубун эски (category, subcat) жубуна которот.
    Сайт ушул экөөнү колдонот.
    """
    if ad_type == "trade":
        return _TRADE_MAP.get(cat_id, ("personal", "other"))
    if ad_type == "service":
        return _SERVICE_MAP.get(cat_id, ("service", "other"))
    if ad_type == "rental":
        return _RENTAL_MAP.get(cat_id, ("realty", "rent"))
    if ad_type == "delivery":
        return _DELIVERY_DEFAULT
    if ad_type == "job":
        return _JOB_MAP.get(cat_id, ("business", "other"))
    if ad_type in ("markets", "malls"):
        return ("shop", "other")
    if ad_type in ("taxi", "vehicle"):
        return ("transport", "car")
    return ("personal", "other")


def region_line(data):
    """
    Аймак дарагын базанын `region` тилкесине батчу бир сапка чогултат.
    Мисалы: "Чүй облусу, Аламүдүн району, Лебединовка"
    """
    parts = []
    for key in ("oblast", "district", "locality", "village"):
        v = data.get(key)
        if v and isinstance(v, str) and v.strip():
            parts.append(v.strip())
    # Аймак тандалбаса — жарыя бүт өлкө боюнча
    return (", ".join(parts)[:200]) or "Бүт Кыргызстан"


def _first(text):
    """
    Эки тилдүү саптын кыргызча бөлүгүн алат.

    Аталыш "A | B | C" түрүндө курама болушу мүмкүн, ошондуктан ар бир
    бөлүк өзүнчө тазаланат — антпесе биринчи " / " жерден кесилип калат.
    """
    if not text:
        return ""
    parts = [p.split(" / ")[0].strip() for p in str(text).split(" | ")]
    return " | ".join(x for x in parts if x)


_TSKIP = {"", "-", "—", "–", "none", "null"}


def short_title(t, limit=44):   # TITLE2: «A | B | - | Депозит: …» → «A | B»
    """
    Курама аталыштан кыскасын алат: бош, «-» жана «Аты: маани» түрүндөгү
    бөлүктөр түшүп калат (алар сүрөттөмөдө баары бир турат). Эң көп эки бөлүк.
    """
    t = str(t or "").strip()
    if " · " in t:
        t = " · ".join(x.strip() for x in t.split(" · ") if x.strip().lower() not in _TSKIP)
    if "|" not in t:
        return t
    raw = [x.strip() for x in t.split("|")]
    parts = [x for x in raw if x.lower() not in _TSKIP and ":" not in x]
    if not parts:
        parts = [x for x in raw if x.lower() not in _TSKIP][:1] or [t]
    out = parts[0]
    if len(parts) > 1 and len(out) + 3 + len(parts[1]) <= limit:
        out += " | " + parts[1]
    return out


def build_title(data):
    """
    Жарыянын аталышын чогултат.

    Эч качан ички код жазылбайт: категориянын коду болсо, ал алды менен
    каталогдогу атка айландырылат.
    """
    t = data.get("title")
    if t and not is_code(str(t)):
        return short_title(_first(str(t)))[:200]

    sub = str(data.get("subcategory") or "").strip()
    if sub and not is_code(sub):
        return _first(sub)[:200]

    lbl = cat_label(str(data.get("category") or "").strip())
    if lbl:
        return _first(lbl)[:200]

    sec = SECTION_LABELS.get(data.get("adType") or "", "")
    return _first(sec)[:200] or "Жарыя"


def build_description(data):
    """
    Флоу чогулткан бардык кошумча жоопторду бир сүрөттөмөгө айлантат.
    Базадагы `description` тилкесине жазылат, сайтта көрүнөт.
    """
    lines = []
    label = [
        ("subcategory",   "Түрү"),
        ("tradeWholesale", "Сатуу"),
        ("tradeDelivery", "Жеткирүү"),
        ("animalBreed",   "Тукуму"),
        ("animalAgeCount", "Жашы/саны"),
        ("animalCondition", "Абалы"),
        ("vehicleBrand",  "Маркасы"),
        ("vehicleYear",   "Жылы"),
        ("vehicleTransRoul", "Кыймылдаткыч"),
        ("vehicleCondition", "Абалы"),
        ("marketStall",   "Соода орду"),
        ("bazaarQuality", "Сапаты"),
        ("bazaarDelivery", "Карго"),
        ("mallName",      "Соода борбору"),   # MALLS2
        ("mallBrand",     "Дүкөн"),
        ("mallPromo",     "Акция"),
        ("mallFloor",     "Кабаты"),
        ("mallHours",     "Иш убактысы"),
        ("storeDirection", "Дүкөн"),
        ("storeAddress",  "Дареги"),
        ("storeHours",    "Иш убактысы"),
        ("storeDelivery", "Жеткирүү"),
        ("rentalPeriod",  "Ижара мөөнөтү"),
        ("rentalCharacteristics", "Мүнөздөмөсү"),
        ("rentalDeposit", "Депозит"),
        ("jobDuties",     "Милдеттери"),
        ("jobRequirements", "Талаптар"),
        ("jobConditions", "Шарттары"),
        ("callTime",      "Чалуу убактысы"),
        ("duration",      "Мөөнөтү"),
        # ── такси ───────────────────────────────
        ("taxiName",      "Аты"),
        ("taxiCar",       "Машина"),
        ("taxiDate",      "Күнү"),
        ("taxiTime",      "Саат"),
        ("taxiSeats",     "Бош орун"),
        ("taxiPeople",    "Жүргүнчү"),
        ("taxiBaggage",   "Жүк"),
        # ── дүң соода ───────────────────────────
        ("wsMinOrder",    "Эң аз буйрутма"),
        ("wsUnit",        "Өлчөө бирдиги"),
        ("wsDelivery",    "Жеткирүү"),
        # ── жүк ташуу ───────────────────────────
        ("cargoRoute",    "Багыт"),
        ("cargoCapacity", "Жүк көтөрүмү"),
        ("cargoBody",     "Кузовдун түрү"),
        # ── жумуш издөө ─────────────────────────
        ("seekExp",       "Стажы"),
        ("seekSchedule",  "График"),
        ("seekEdu",       "Билими"),
    ]
    for key, name in label:
        v = data.get(key)
        if v and str(v).strip() and str(v).strip() != "-":
            lines.append("%s: %s" % (name, _first(str(v))))

    c = data.get("postComment") or data.get("taxiComment")
    if c and str(c).strip() not in ("-", ""):
        lines.insert(0, str(c).strip())

    return "\n".join(lines)[:2000]


def taxi_route(data):
    """Таксинин багыты: «Ош шаары → Бишкек»."""
    a = str(data.get("taxiFrom") or "").strip()
    b = str(data.get("taxiTo") or "").strip()
    if a and b:
        return f"{a} → {b}"
    return a or b


def to_listing(data):
    """
    Флоунун натыйжасын core.add_listing() күткөн сөздүккө айлантат.
    """
    ad_type = data.get("adType") or "trade"
    cat_id = data.get("category") or ""
    legacy_cat, legacy_sub = to_legacy(ad_type, cat_id)

    # Такси бөлүмүнүн талаалары башка аталышта турат
    is_taxi = ad_type == "taxi"
    title = taxi_route(data) if is_taxi else build_title(data)
    region = (str(data.get("taxiFrom") or "").strip()
              if is_taxi else region_line(data))
    price = data.get("taxiPrice") if is_taxi else data.get("price")
    phone = data.get("taxiPhone") if is_taxi else data.get("phone")

    # Издөө үчүн: категориянын жана бөлүмдүн аты да сакталсын
    cat_nm = cat_label(cat_id)
    sec_nm = SECTION_LABELS.get(ad_type, "")

    return {
        "cat_name":    cat_nm,
        "sec_name":    sec_nm,
        # Такси сапары 1 күн турат — мөөнөт өзүнчө суралбайт
        "duration":    ("1 күн" if is_taxi
                        else _first(str(data.get("duration") or ""))),
        "category":    legacy_cat,
        "subcat":      legacy_sub,
        "region":      region or region_line(data),
        "title":       title or "Такси",
        "description": build_description(data),
        "price":       _first(str(price or "")),
        "contact":     str(phone or data.get("phone") or ""),
        # жаңы тилкелер
        "ad_type":     ad_type,
        "cat_id":      cat_id,
        "sub_id":      _first(str(data.get("subcategory") or ""))[:200],
        "oblast":      data.get("oblast") or data.get("taxiLoOblast") or "",
        "district":    data.get("district") or data.get("taxiFrom") or "",
        "locality":    data.get("locality") or "",
        "village":     data.get("village") or "",
    }

# OLD_CATS_RU
RU_MAP.update({
    "Жеткирүү жок": "Нет доставки",  #DELIV_RU
    "Жеткирүү бар": "Есть доставка",
    "Батир": "Квартира",
    "Там, үй": "Дом",
    "Жер участок": "Земельный участок",
    "Коммерциялык жай": "Коммерческое помещение",
    "Ижарага": "Аренда",
    "Телефон": "Телефон",
    "Компьютер, ноутбук": "Компьютер, ноутбук",
    "Кийим-кече": "Одежда",
    "Эмерек": "Мебель",
    "Тиричилик техникасы": "Бытовая техника",
    "Балдар буюмдары": "Детские товары",
    "Башка": "Другое",
    "Оңдоо, курулуш": "Ремонт, строительство",
    "Ташуу кызматы": "Грузоперевозки",
    "Техника оңдоо": "Ремонт техники",
    "Сулуулук, саламаттык": "Красота, здоровье",
    "Окутуу": "Обучение",
    "Азык-түлүк": "Продукты",
    "Кийим дүкөнү": "Магазин одежды",
    "Техника дүкөнү": "Магазин техники",
    "Курулуш материалдары": "Стройматериалы",
    "Даяр бизнес": "Готовый бизнес",
    "Жабдуу": "Оборудование",
    "Өнөктөштүк": "Партнёрство",
})



# ── RUDICT: баскыч менен тандалган жооптордун орусчасы ─────────────
RU_EXTRA = {
    # Сүрөттөмөдөгү талаалардын аттары
    "Соода борбору": "Торговый центр", "Ижара мөөнөтү": "Срок аренды",
    "Өлчөө бирдиги": "Единица измерения", "Багыт": "Направление",
    "Жүк көтөрүмү": "Грузоподъёмность", "Кузовдун түрү": "Тип кузова",
    "Стажы": "Стаж", "Билими": "Образование",
    # Жеткирүү
    "Бардык облустарга карго менен": "Карго во все области", "Жок": "Нет",
    "Келишим боюнча": "По договорённости", "Шаар ичинде гана": "Только по городу",
    "Жок, өзү алып кетет": "Нет, самовывоз", "Облустарга карго менен": "Карго в области",
    "Жеткирүү бар": "Есть доставка", "Жеткирүү жок": "Нет доставки",
    # Жүк ташуу
    "0.5 тоннага чейин": "до 0,5 тонны", "1.5 тонна": "1,5 тонны", "3 тонна": "3 тонны",
    "5 тонна": "5 тонн", "10 тонна": "10 тонн", "20+ тонна": "20+ тонн",
    "Бүт Кыргызстан": "Весь Кыргызстан", "Облустар аралык": "Между областями",
    "Эл аралык": "Международные",
    # Кыймылсыз мүлк
    "Жакшы ремонт": "Хороший ремонт", "Кара курулуш (ПСО)": "Черновая отделка (ПСО)",
    "Орточо": "Среднее", "Ремонт керек": "Требует ремонта",
    "1-кабат": "1 этаж", "2-кабат": "2 этаж", "3-кабат": "3 этаж", "4-кабат": "4 этаж",
    "5-кабат": "5 этаж", "6-9-кабат": "6–9 этаж", "10+кабат": "10+ этаж",
    "1-бөлмө": "1 комната", "2-бөлмө": "2 комнаты", "3-бөлмө": "3 комнаты",
    "4-бөлмө": "4 комнаты", "5+бөлмө": "5+ комнат",
    "Алмашуу каралат": "Рассмотрю обмен", "Ипотекага болот": "Возможна ипотека",
    "Катуу баа": "Цена окончательная", "Соодасы бар": "Торг уместен",
    # Жер
    "Свет бар": "Есть свет", "Суу бар": "Есть вода", "Газ бар": "Есть газ",
    "Канализация бар": "Есть канализация", "Сугат суу (арык)": "Поливная вода (арык)",
    "Жанында, тартса болот": "Рядом, можно подвести", "Коммуникация жок": "Нет коммуникаций",
    "Кызыл китеп": "Красная книга", "Мамлекеттик акт": "Госакт",
    "Чек арасы бекитилген": "Границы закреплены",
    "Сатып алуу-сатуу келишими": "Договор купли-продажи",
    "Документ даярдалууда": "Документы оформляются",
    # Ижара
    "1 айлык депозит": "Депозит за 1 месяц", "Депозит жок": "Без депозита",
    "Айына": "Помесячно", "Жумасына": "Понедельно", "Күнүнө": "Посуточно", "Саатына": "Почасово",
    # Жумуш
    "Жогорку": "Высшее", "Мааниси жок": "Не важно", "Орто": "Среднее",
    "Орто-атайын": "Среднее специальное",
    "1 жылга чейин": "До 1 года", "1–3 жыл": "1–3 года", "3–5 жыл": "3–5 лет",
    "5 жылдан ашык": "Более 5 лет", "Тажрыйбасыз": "Без опыта",
    "Жарым күн": "Неполный день", "Каалаган график": "Свободный график",
    "Сменалык": "Сменный", "Толук күн": "Полный день",
    # Дүкөн
    "24/7 (тынымсыз)": "24/7 (круглосуточно)",
    # Унаа
    "Электр": "Электро", "Кырсык болгон, оңдолгон": "Был в ДТП, восстановлен",
    "Кырсыксыз": "Без ДТП", "Алдыңкы привод": "Передний привод",
    "Арткы привод": "Задний привод", "Толук привод (4WD)": "Полный привод (4WD)",
    "1-ээси": "1 владелец", "2-ээси": "2 владельца",
    "3 жана андан көп ээси": "3 и более владельцев",
    "Жарым-жартылай боёлгон": "Частично окрашен", "Краскасы өзүнүкү": "Родная краска",
    "Толук боёлгон": "Полностью окрашен", "Оң руль": "Правый руль", "Сол руль": "Левый руль",
    # Дүң соода
    "даана": "шт.", "капка": "мешок", "куту": "коробка",
}
for _k, _v in RU_EXTRA.items():
    RU_MAP.setdefault(_k, _v)
