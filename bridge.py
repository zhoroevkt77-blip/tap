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


from taxi_geo import route_tag


def region_line(data):
    """
    Аймак дарагын базанын `region` тилкесине батчу бир сапка чогултат.
    Мисалы: "Чүй облусу, Аламүдүн району, Лебединовка"
    """
    if data.get("adType") == "taxi":
        frm, to = data.get("taxiFrom"), data.get("taxiTo")
        if frm and to:
            return ("%s → %s" % (frm, to))[:200]

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
    """Жарыянын аталышын чогултат."""
    if data.get("adType") == "taxi":
        frm, to = data.get("taxiFrom"), data.get("taxiTo")
        if frm and to:
            who = "Айдоочу" if data.get("taxiRole") == "driver" else "Жүргүнчү"
            return "%s ➡️ %s · %s" % (frm, to, who)
    t = data.get("title")
    if t:
        return _first(str(t))[:200]
    sub = data.get("subcategory") or data.get("category") or ""
    return _first(str(sub))[:200] or "Жарыя"


def build_description(data):
    """
    Флоу чогулткан бардык кошумча жоопторду бир сүрөттөмөгө айлантат.
    Базадагы `description` тилкесине жазылат, сайтта көрүнөт.
    """
    lines = []
    if data.get("adType") == "taxi":
        return _taxi_description(data)

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
    ]
    for key, name in label:
        v = data.get(key)
        if v and str(v).strip() and str(v).strip() != "-":
            lines.append("%s: %s" % (name, _first(str(v))))

    c = data.get("postComment")
    if c and str(c).strip() not in ("-", ""):
        lines.insert(0, str(c).strip())

    return "\n".join(lines)[:2000]


def _taxi_description(data):
    """Такси жарыясынын тексти — Такси роБОТтогудай тартипте."""
    lines = []
    for key, name in [("taxiName", "Аты"), ("taxiCar", "Унаа"),
                      ("taxiDate", "Күнү"), ("taxiTime", "Убактысы"),
                      ("taxiSeats", "Бош орун"), ("taxiPeople", "Жүргүнчү"),
                      ("taxiBaggage", "Багаж")]:
        v = data.get(key)
        if v and str(v).strip():
            lines.append("%s: %s" % (name, v))
    c = data.get("taxiComment")
    if c and str(c).strip().lower() not in ("-", "жок", "нет", ""):
        lines.append("📝 %s" % str(c).strip())
    frm, to = data.get("taxiFrom"), data.get("taxiTo")
    if frm and to:
        lines.append(route_tag(frm, to))
    return "\n".join(lines)[:2000]


def to_listing(data):
    """
    Флоунун натыйжасын core.add_listing() күткөн сөздүккө айлантат.
    """
    ad_type = data.get("adType") or "trade"
    cat_id = data.get("category") or ""
    legacy_cat, legacy_sub = to_legacy(ad_type, cat_id)

    return {
        "category":    legacy_cat,
        "subcat":      legacy_sub,
        "region":      region_line(data),
        "title":       build_title(data),
        "description": build_description(data),
        "price":       _first(str(data.get("price") or data.get("taxiPrice") or "")),
        "contact":     str(data.get("phone") or data.get("taxiPhone") or ""),
        # жаңы тилкелер
        "ad_type":     ad_type,
        "cat_id":      cat_id,
        "sub_id":      _first(str(data.get("subcategory") or ""))[:200],
        "oblast":      data.get("oblast") or "",
        "district":    data.get("district") or "",
        "locality":    data.get("locality") or "",
        "village":     data.get("village") or "",
    }
