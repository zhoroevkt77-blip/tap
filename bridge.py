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
                  "WHOLESALE_CATEGORIES", "CARGO_CATEGORIES", "JOBSEEK_CATEGORIES"):
        for _c in (getattr(_tc, _name, None) or []):
            if isinstance(_c, dict) and _c.get("id"):
                CAT_LABELS.setdefault(_c["id"], _c.get("label") or _c["id"])

SECTION_LABELS = {
    "wholesale": "Соода-сатык (дүң) / Оптовая торговля",
    "cargo":     "Жүк ташуу / Грузоперевозки",
    "jobseek":   "Жумуш издөө / Поиск работы",
    "trade":    "Соода-сатык / Торговля",
    "service":  "Кызмат көрсөтүү / Услуги",
    "rental":   "Ижарага берүү / Аренда",
    "delivery": "Жеткирүү / Доставка",
    "job":      "Жумуш берүү / Работа",
    "markets":  "Базарлар / Рынки",
    "taxi":     "Такси / Такси",
}


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
                return (lbl.split(" / ")[0] + sep + tail)
        return t
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
    if ad_type == "markets":
        return ("shop", "other")
    if ad_type == "taxi":
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
    return ", ".join(parts)[:200]


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


def build_title(data):
    """
    Жарыянын аталышын чогултат.

    Эч качан ички код жазылбайт: категориянын коду болсо, ал алды менен
    каталогдогу атка айландырылат.
    """
    t = data.get("title")
    if t and not is_code(str(t)):
        return _first(str(t))[:200]

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
        ("mallBrand",     "Дүкөн"),
        ("mallPromo",     "Акция"),
        ("mallFloor",     "Кабаты"),
        ("mallHours",     "Иш убактысы"),
        ("storeDirection", "Багыты"),
        ("storeAddress",  "Дареги"),
        ("storeHours",    "Иш убактысы"),
        ("storeDelivery", "Жеткирүү"),
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

    return {
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
