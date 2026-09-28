# -*- coding: utf-8 -*-
"""
ТАП! — флоу кыймылдаткычы ("бир мээ").

Бул модуль платформага көз каранды эмес: Telegram, WhatsApp, сайт — баары
ушул бир файлды колдонот. Тышкы китепкана талап кылынбайт.

API (болгону эки функция):

    from tap_flow import render, advance, START_STEP

    # 1) Учурдагы кадамды көрсөтүү
    view = render(step, data)
    #  -> {"text": str,
    #      "options": [{"label": str, "value": str}, ...],
    #      "input": bool,          # текст киргизүү керекпи
    #      "placeholder": str,
    #      "multi": bool,          # бир нече тандоо мүмкүнбү
    #      "photo": bool,          # сүрөт күтүлөбү
    #      "final": bool}          # жарыя даярбы

    # 2) Колдонуучунун жообун кабыл алуу
    step, data = advance(step, value, data)

`data` — жөнөкөй dict. Аны базада JSON катары сактаса болот.
Бир нече тандоо (multi) учурунда `value` — үтүр менен бөлүнгөн сап.
"""

import re

from taxi_geo import (REGIONS as TX_REGIONS, REGION_LIST as TX_REGION_LIST,
                      DISTRICTS as TX_DISTRICTS,
                      DISTRICT_OBLASTS as TX_OBLASTS,
                      steps_of, day_hours, date_label)
from tap_catalog import (
    GREETING, MAIN_OPTIONS, OBLASTS, STANDALONE, GEO,
    TRADE_CATEGORIES, PROPERTY_CATEGORIES, VEHICLE_SALE_CATEGORIES,
    HEATING_FUEL_SUBS, TRADE_PRICE_PRESETS, TRADE_CONDITION,
    DEMOGRAPHICS, SEASONS, REALESTATE_TYPES, REALESTATE_SUBS,
    VEHICLE_BODY_TYPES, VEHICLE_ENGINE_TYPES, VEHICLE_CATEGORIES, VEHICLE_SUBS,
    MARKETS_TYPES, MALLS_TYPES, MARKETS_GROUPS, MARKETS_SUBS_BY_TYPE,
    RENTAL_CATEGORIES, SERVICE_CATEGORIES, JOB_CATEGORIES, DELIVERY_CATEGORIES,
    DURATION_PLANS, SERVICE_PRICE_PRESETS, JOB_SALARY_PRESETS, CALL_TIME_PRESETS,
    GROUP_TABLES, SERVICE_GROUP_TABLES,
    get_districts, get_localities, get_villages,
    get_categories, get_subs_for_category,
    get_clothing_subs, get_footwear_subs, ru_name,
)
from strings import H as _help_text
from strings import TOPICS as _HELP_TOPICS, topic_title as _topic_title

START_STEP = "language_select"


# Башкы менюга кошумча эки баскыч. tap_catalog.MAIN_OPTIONS'ко
# тийбей, ушул жерден кошулат — ошондуктан каталог өзгөрбөйт.
MENU_EXTRA = [
    {"label": "💰 Менин балансым / Мой баланс", "value": "tap_balance"},
    {"label": "🌍 Биздин сайт / Наш сайт", "value": "tap_site"},
    {"label": "❓ Жардам / Помощь",        "value": "tap_help"},
    # Тил баскычы атайын эки тилде: кайсы тилде турса да табылсын.
    # Ичинде « / » бөлгүчү жок, ошондуктан которулбайт.
    {"label": "🔤 Тил/Язык",               "value": "tap_lang"},
]


# Жардам бөлүмүнүн баскычтары — тандалган тилде гана.
_HELP_BTN = {
    "guide": ("📖 Нускама",                "📖 Инструкция"),
    "faq":   ("❓ Көп берилүүчү суроолор",  "❓ Частые вопросы"),
    "home":  ("🏠 Башкы меню",             "🏠 Главное меню"),
    "back":  ("⬅️ Артка",                  "⬅️ Назад"),
}


def _main_options():
    """Башкы менюнун толук тизмеси."""
    return ([{"label": o["label"], "value": o["value"]} for o in MAIN_OPTIONS]
            + list(MENU_EXTRA))


def _ui_lang(d):
    """Колдонуучу тандаган тил: "ky" же "ru"."""
    return "ru" if (d or {}).get("uiLanguage") == "ru" else "ky"


def _hb(key, d):
    """Жардам баскычынын жазуусу — тандалган тилде."""
    ky, ru = _HELP_BTN[key]
    return ru if _ui_lang(d) == "ru" else ky


OTHER = "Башка / Другое"

# TRADE_SIMPLE_FLOW: соода — топсуз субкатегориялар, унаада «өткөрүп жиберүү»
SKIP = "__skip__"
SKIP_OPT = {"label": "⏭ Өткөрүп жиберүү / Пропустить", "value": SKIP}


def _trade_subs(cat_id):
    """Соода/мүлк категориясынын субкатегориялары (топсуз)."""
    for c in (list(PROPERTY_CATEGORIES) + list(VEHICLE_SALE_CATEGORIES)
              + list(TRADE_CATEGORIES)):
        if c.get("id") == cat_id:
            return c.get("subs") or []
    return []


# ─────────────────────────────────────────────────────────────
#  Кичине жардамчылар
# ─────────────────────────────────────────────────────────────

def _opts(pairs):
    """[(label, value)] -> опциялар тизмеси."""
    return [{"label": l, "value": v} for l, v in pairs]


# Баскычтагы аталыш ушул узундуктан ашпасын. Каталогдо толук аты
# сакталып кала берет — кыскартуу көрсөтүүдө гана болот.
LABEL_MAX = 32

_PAREN_RE = re.compile(r"\s*\([^)]*\)")
_TAIL_WORDS = ("жана", "менен", "же", "и", "или", "для", "по")


def _short_one(s, ru=False):
    """Бир тилдеги аталышты баскычка сыйгыдай кыскартат."""
    s = str(s).strip()
    if len(s) <= LABEL_MAX:
        return s
    etc = "и др." if ru else "ж.б."
    # Кашаанын ичи узун болгондо гана алынат — «(вторичка)» сыяктуу
    # маанилүү тактоолор кыска аталышта сакталып калсын.
    s2 = _PAREN_RE.sub("", s).strip()
    if len(s2) <= LABEL_MAX:
        return s2
    s = s2
    if "," in s:                       # тизме — биринчилерин калтырабыз
        parts = [p.strip() for p in s.split(",") if p.strip()]
        out = parts[0]
        for p in parts[1:]:
            if len(out) + 2 + len(p) + len(etc) + 1 > LABEL_MAX:
                break
            out += ", " + p
        return out + " " + etc
    words = s.split()                  # тизме эмес — сөз чегинде кесебиз
    out = ""
    for w in words:
        if len(out) + 1 + len(w) > LABEL_MAX - 1:
            break
        out = (out + " " + w).strip()
    while out.split() and out.split()[-1].lower() in _TAIL_WORDS:
        out = " ".join(out.split()[:-1])
    return (out or s[:LABEL_MAX - 1]) + "…"


def _short_label(s):
    """«Кыргызча / Орусча» аталыштын эки жагын тең кыскартат."""
    parts = str(s).split(" / ")
    if len(parts) == 2:
        return "%s / %s" % (_short_one(parts[0]), _short_one(parts[1], True))
    return _short_one(s)


def _from_list(items):
    """Жөнөкөй сап тизмесин опцияга айлантуу. Бош болсо — "Башка"."""
    items = list(items or [])
    if not items:
        items = [OTHER]
    # Баскычта кыска аты, базага толук аты жазылат
    return [{"label": _short_label(s), "value": s} for s in items]


def _has_choice(items):
    """Тизмеде чыныгы тандоо барбы.

    Бош болсо, же ичинде «Башка» дегенден башка эч нерсе жок болсо —
    ал экранды көрсөтүүнүн мааниси жок: колдонуучу бир гана нерсени
    басып, кийинки кадамга өтмөк. Ошондуктан аттап өтөбүз.
    """
    items = [str(x) for x in (items or [])]
    return any(not x.startswith("Башка") for x in items)


def _from_groups(groups):
    """[{id,label,emoji?}] -> опциялар."""
    out = []
    for g in groups:
        label = g.get("label", g["id"])
        if g.get("emoji"):
            label = "%s %s" % (g["emoji"], label)
        out.append({"label": label, "value": g["id"]})
    return out


# Аймакты тандабай эле, бүт өлкө боюнча жарыя бергиси келгендер үчүн
ALL_KG = "__all_kg__"


def _regions():
    """Аймактардын тизмеси. Башында — бүт өлкө."""
    return ([{"label": "🇰🇬 Бүт Кыргызстан / Весь Кыргызстан",
              "value": ALL_KG}]
            + [{"label": "%s / %s" % (o, ru_name(o)), "value": o}
               for o in OBLASTS])


# Категориянын коду -> адам окуй турган аталышы.
_CAT_LABELS = {}
for _lst in (TRADE_CATEGORIES, RENTAL_CATEGORIES, SERVICE_CATEGORIES,
             JOB_CATEGORIES, DELIVERY_CATEGORIES):
    for _c in (_lst or []):
        if isinstance(_c, dict) and _c.get("id"):
            _CAT_LABELS[_c["id"]] = _c.get("label") or _c["id"]
del _lst, _c


def _cat_label(code):
    """Категориянын аталышы. Табылбаса кодду өзүн кайтарат."""
    return _CAT_LABELS.get(code, code or "")


def _view(text, options=None, input=False, placeholder="", multi=False,
          photo=False, final=False, localized=False, video=False, photo_max=None):
    return {
        "text": text,
        "options": options or [],
        "input": input,
        "placeholder": placeholder,
        "multi": multi,
        "photo": photo,
        "video": video,
        "photo_max": photo_max,
        "final": final,
        # localized=True — текст мурунтан бир тилде даяр, кайра
        # которуунун кереги жок (Жардам, Нускама, Сайт).
        "localized": localized,
    }


def _is_city(oblast):
    return oblast in STANDALONE


# ─────────────────────────────────────────────────────────────
#  Суроо чынжырлары (бир кадамда бир нече суроо берилет)
#  (талаа, суроо, мисал)
# ─────────────────────────────────────────────────────────────

CHAIN_ANIMALS = [
    ("animalBreed", "🐄 Малдын түрү жана тукуму (породасы)? / Вид и порода животного?",
     "Мис: Ала-Тоо тукумундагы бука / Например: Бык породы Алатау"),
    ("animalAgeCount", "🔢 Жашы жана саны канча? / Возраст и количество?",
     "Мис: 1,5 жашар, 3 баш / Например: 1,5 года, 3 головы"),
    ("animalCondition", "📋 Абалы жана өзгөчөлүгү кандай? / Состояние и особенности?",
     "Мис: Семиз, жемге жакшы байланган / Например: Упитанный"),
]

# Кыргызстанда эң көп кездешкен маркалар. Тизмеде жогу — колдонуучу
# өзү жазып кете алат (баскычтар турганда да текст кабыл алынат).
CAR_BRANDS = _opts([(b, b) for b in (
    # Ирети — Кыргызстанда катталган саны боюнча
    "Daewoo", "Mercedes-Benz", "Hyundai", "Kia", "Toyota",
    "Honda", "Lada (ВАЗ)", "Nissan", "Lexus", "BMW",
    "Audi", "Volkswagen", "Mitsubishi", "Chevrolet", "Opel",
    "Subaru", "Mazda", "Ford",
)] + [("🇨🇳 Кытай маркалары / Китайские марки", "__china__")])

# Кытай маркалары өзүнчө экранда — биринчи тизме кыска калсын үчүн.
CHINA_BRANDS = _opts([(b, b) for b in (
    "BYD", "Chery", "Changan", "Haval", "Geely",
    "Jetour", "Zeekr", "Li Auto", "GAC", "Exeed",
    "Tank", "Deepal", "Leapmotor", "NIO", "Xpeng",
    "Voyah", "Omoda", "Dongfeng",
)] + [("⬅️ Артка / Назад", "__back__")])

VEHICLE_BARGAIN = _opts([
    ("💬 Соодасы бар / Торг есть", "Соодасы бар"),
    ("🔒 Катуу баа / Цена твёрдая", "Катуу баа"),
    ("🔁 Алмашуу каралат / Возможен обмен", "Алмашуу каралат"),
])

VEHICLE_FUEL = _opts([(x, x) for x in (
    "Бензин", "Дизель", "Газ", "Электр", "Гибрид", "Плагин-гибрид",
)])

# HELP_CHIPS: колдонуучуга жазууга жардам берген баскычтар
def _o(*xs):
    return _opts([(x, x) for x in xs])

NUMERIC_KEYS = {"vehicleYear", "vehicleMileage", "vehicleEngVol", "homeArea",
                "wsMinOrder", "cargoCapacity"}
UNIT_SUFFIX = {"vehicleMileage": " км", "cargoCapacity": " тонна", "vehicleEngVol": " л"}

VEH_ENGVOL = _o("1.0–1.4", "1.5", "1.6", "1.8", "2.0", "2.4", "2.5", "3.0", "3.5+")
VEH_GEARBOX = _o("Автомат", "Механика", "Вариатор", "Робот")
VEH_WHEEL = _o("Сол руль", "Оң руль")
VEH_DRIVE = _o("Алдыңкы привод", "Арткы привод", "Толук привод (4WD)")
VEH_CRASH = _o("Кырсыксыз", "Кырсык болгон, оңдолгон")
VEH_PAINT = _o("Краскасы өзүнүкү", "Жарым-жартылай боёлгон", "Толук боёлгон")
VEH_OWNERS = _o("1-ээси", "2-ээси", "3 жана андан көп ээси")
LAND_UTILS = _o("Свет бар", "Суу бар", "Газ бар", "Канализация бар",   # LANDMULTI
                "Сугат суу (арык)", "Жанында, тартса болот", "Коммуникация жок")
LAND_DOCS = _o("Кызыл китеп", "Мамлекеттик акт", "Чек арасы бекитилген",
               "Сатып алуу-сатуу келишими", "Документ даярдалууда")
MULTI_KEYS = {"landUtils", "landDocs"}
HOME_COND = _o("Евроремонт", "Жакшы ремонт", "Орточо", "Ремонт керек", "Кара курулуш (ПСО)")
DELIVERY_OPTS = _o("Жеткирүү бар", "Шаар ичинде гана", "Облустарга карго менен",
                   "Жок, өзү алып кетет", "Келишим боюнча")
CARGO_ROUTE = _o("Шаар ичинде", "Облустар аралык", "Бүт Кыргызстан", "Эл аралык")
CARGO_CAP = _o("0.5 тоннага чейин", "1.5 тонна", "3 тонна", "5 тонна", "10 тонна", "20+ тонна")
CARGO_BODY = _o("Тент", "Борттуу", "Фургон", "Рефрижератор", "Самосвал", "Контейнер", "Эвакуатор")
SEEK_EXP = _o("Тажрыйбасыз", "1 жылга чейин", "1–3 жыл", "3–5 жыл", "5 жылдан ашык")
SEEK_SCHED = _o("Толук күн", "Жарым күн", "Сменалык", "Вахта", "Каалаган график")
SEEK_EDU = _o("Орто", "Орто-атайын", "Жогорку", "Студент", "Мааниси жок")
RENT_PERIOD = _o("Саатына", "Күнүнө", "Жумасына", "Айына", "Келишим боюнча")
RENT_DEPOSIT = _o("Депозит жок", "1 айлык депозит", "Келишим боюнча")
BAZAAR_DELIVERY = _o("Бардык облустарга карго менен", "Шаар ичинде гана", "Жок", "Келишим боюнча")


CHAIN_VEHICLES = [
    ("vehicleBrand", "🚘 Маркасын тандаңыз, же өзүңүз жазыңыз / "
     "Выберите марку или впишите свою",
     "Мис: Chery / Например: Chery", CAR_BRANDS),
    ("vehicleModel", "🚗 Үлгүсү (модели)? / Модель?",
     "Мис: CR-V / Например: CR-V"),
    ("vehicleYear", "📅 Чыккан жылы? / Год выпуска?",
     "Мис: 2015 / Например: 2015"),
    ("vehicleMileage", "🛣 Пробеги канча км? / Какой пробег (км)?",
     "Мис: 115000 / Например: 115000"),
    ("vehicleEngVol", "🔧 Кыймылдаткычтын көлөмү? / Объём двигателя?",
     "Же өзүңүз жазыңыз, мис: 2.2 / Или впишите, например: 2.2", VEH_ENGVOL),
    ("vehicleGearbox", "⚙️ Коробкасы кандай? / Коробка передач?", "", VEH_GEARBOX),
    ("vehicleWheel", "🎯 Руль кайсы жакта? / Где руль?", "", VEH_WHEEL),
    ("vehicleDrive", "🚙 Приводу кандай? / Привод?", "", VEH_DRIVE),
    ("vehicleFuel", "⛽ Куяр майы кандай? / На чём ездит?",
     "", VEHICLE_FUEL),
    ("vehicleCrash", "💥 Кырсыкка кабылганбы? / Было ли ДТП?", "", VEH_CRASH),
    ("vehiclePaint", "🎨 Краскасы кандай? / Покраска?", "", VEH_PAINT),
    ("vehicleOwners", "👤 Канчанчы ээси? / Какой по счёту владелец?", "", VEH_OWNERS),
    ("vehicleBargain", "💵 Баа боюнча шарт кандай? / Условия по цене?",
     "", VEHICLE_BARGAIN),
    ("vehicleCondition", "🛠 Абалы, документтери жана комплектациясы? / Состояние, документы и комплектация?",
     "Мис: Мотор/коробка идеалдуу, документтери таза, климат-контроль, камера / Например: Мотор и коробка идеальные, документы чистые, климат, камера"),
]

# Кошуна райондорду бирден ашык тандай ала турган бөлүмдөр
MULTI_DISTRICT_TYPES = ("service", "delivery", "cargo")

REALESTATE_BARGAIN = _opts([
    ("💬 Соодасы бар / Торг есть", "Соодасы бар"),
    ("🔒 Катуу баа / Цена твёрдая", "Катуу баа"),
    ("🏦 Ипотека/кредитке болот / Возможна ипотека", "Ипотекага болот"),
    ("🔁 Алмашуу каралат / Возможен обмен", "Алмашуу каралат"),
])

HOME_FLOOR = _opts([(x, x) for x in (
    "1-кабат", "2-кабат", "3-кабат", "4-кабат", "5-кабат",
    "6-9-кабат", "10+кабат",
)])

HOME_ROOMS = _opts([(x, x) for x in (
    "Студия", "1-бөлмө", "2-бөлмө", "3-бөлмө", "4-бөлмө", "5+бөлмө",
)])

CHAIN_HOME = [
    ("homeArea", "📐 Аянты канча м²? / Площадь в м²?",
     "Мис: 64 / Например: 64"),
    ("homeRooms", "🚪 Канча бөлмө? / Сколько комнат?",
     "", HOME_ROOMS),
    ("homeFloor", "🏢 Канчанчы кабат? / На каком этаже?",
     "", HOME_FLOOR),
    ("homeCondition", "🔨 Абалы жана ремонту кандай? / Состояние и ремонт?",
     "Же өзүңүз жазыңыз / Или впишите свой", HOME_COND),
    ("homeDocs", "📄 Документтери жана сериясы? / Документы и серия?",
     "Мис: Кызыл китеп, 105-серия / Например: Красная книга, 105 серия"),
    ("homeArea2", "🏫 Айланасында эмнелер бар? / Что рядом?",
     "Мис: Мектеп, бала бакча жакын, лифт, автотуруучу жай / Например: Школа, садик рядом, лифт, парковка"),
    ("homeBargain", "💵 Баа боюнча шарт кандай? / Условия по цене?",
     "", REALESTATE_BARGAIN),
]

CHAIN_LAND = [
    ("landArea", "📐 Аянты жана максаты? / Площадь и назначение?",
     "Мис: 8 сотых, үй салууга / Например: 8 соток, под строительство"),
    ("landUtils", "🔌 Коммуникациялары барбы? / Есть ли коммуникации?",
     "Башка болсо жазыңыз / Другое — впишите", LAND_UTILS),
    ("landDocs", "📄 Документтери кандай? / Какие документы?",
     "Башка болсо жазыңыз / Другое — впишите", LAND_DOCS),
    ("landPlace", "📍 Жайгашкан жери жана жолу? / Расположение и подъезд?",
     "Мис: Асфальт жолдун боюнда, борборго 15 км / Например: У асфальтированной дороги, 15 км до центра"),
    ("landBargain", "💵 Баа боюнча шарт кандай? / Условия по цене?",
     "", REALESTATE_BARGAIN),
]

CHAIN_COMMERCIAL = [
    ("comArea", "📐 Аянты, кабаты жана багыты? / Площадь, этаж и назначение?",
     "Мис: 120 м², 1-кабат, дүкөн үчүн / Например: 120 м², 1 этаж, под магазин"),
    ("comCondition", "🔌 Абалы жана коммуникациялары? / Состояние и коммуникации?",
     "Мис: Ремонт бар, өзүнчө кирүү, 380V / Например: Ремонт есть, отдельный вход, 380V"),
    ("comDocs", "📄 Документтери кандай? / Какие документы?",
     "Мис: Менчик, каттоого даяр / Например: Собственность, готово к оформлению"),
    ("comPlace", "🚶 Жайгашкан жери жана эл өтүмү? / Расположение и проходимость?",
     "Мис: Базардын жанында, эл көп өтөт / Например: Рядом с рынком, высокая проходимость"),
    ("comBargain", "💵 Баа боюнча шарт кандай? / Условия по цене?",
     "", REALESTATE_BARGAIN),
]

CHAIN_GARAGE = [
    ("garArea", "📐 Аянты жана түрү? / Площадь и тип?",
     "Мис: 18 м², капиталдык, подвалы менен / Например: 18 м², капитальный, с подвалом"),
    ("garCondition", "🔌 Абалы жана коммуникациялары? / Состояние и коммуникации?",
     "Мис: Свет бар, жылуу, темир эшик / Например: Свет есть, тёплый, железные ворота"),
    ("garDocs", "📄 Документтери кандай? / Какие документы?",
     "Мис: Кооперативдин китепчеси / Например: Книжка кооператива"),
    ("garPlace", "📍 Жайгашкан жери? / Расположение?",
     "Мис: Үйдүн короосунда, кире бериш жакын / Например: Во дворе дома, рядом с въездом"),
    ("garBargain", "💵 Баа боюнча шарт кандай? / Условия по цене?",
     "", REALESTATE_BARGAIN),
]

REALESTATE_CHAINS = {
    "residential": CHAIN_HOME,
    "land":        CHAIN_LAND,
    "commercial":  CHAIN_COMMERCIAL,
    "garage":      CHAIN_GARAGE,
}

CHAIN_BAZAAR = [
    ("bazaarQuality", "🏭 Товардын сапаты/өндүрүлгөн жери кайсы? / Качество товара и место производства?",
     "Мис: Түркиядан келген, фабрикалык / Например: Из Турции, фабричный"),
    ("bazaarPrice", "💰 Баасы кандай (чекене жана дүң)? / Цена (розница и опт)?",
     "Мис: Чекене 1500 сом, дүң 900 сом / Например: Розница 1500, опт 900"),
    ("bazaarDelivery", "🚚 Башка облустарга/өлкөлөргө жеткирүү (карго) барбы? / Есть ли доставка (карго)?",
     "Же өзүңүз жазыңыз / Или впишите свой", BAZAAR_DELIVERY),
]

CHAIN_MALL = [
    ("mallBrand", "👜 Дүкөнүңүздүн аты жана эмне сунуштайсыз? / Название магазина и что предлагаете?",
     "Мис: «Элегант» — италиялык сумкалар / Например: «Элегант» — сумки из Италии"),
    ("mallPromo", "🎁 Өзгөчөлүгү же учурдагы акциялар барбы? / Особенности или акции?",
     "Мис: Жаңы коллекция, 20% арзандатуу / Например: Новая коллекция, скидка 20%"),
    ("mallFloor", "🏢 Кабаты жана ориентир кайсы? / Этаж и ориентир?",
     "Мис: 1-кабат, борбордук фонтандын оң тарабында / Например: 1 этаж, справа от фонтана"),
    ("mallHours", "⏰ Иш убактысы кандай? / Часы работы?",
     "Мис: 10:00–22:00 (дем алышсыз) / Например: 10:00–22:00 (без выходных)"),
]

CHAIN_STORE = [
    ("storeDirection", "🏪 Дүкөнүңүздүн аты жана эмнеге адистешкен? / Название магазина и специализация?",
     "Мис: «Балдар дүйнөсү» — балдар кийими / Например: «Детский мир» — детская одежда"),
    ("storeAddress", "📍 Так дареги жана ориентир кайсы? / Точный адрес и ориентир?",
     "Мис: Сухэ-Батор көчөсү 23А / Например: ул. Сухэ-Батора 23А"),
    ("storeHours", "⏰ Иш убактысы кандай? / Часы работы?",
     "Мис: 09:00–20:00 (дем алышсыз) / Например: 09:00–20:00 (без выходных)"),
    ("storeDelivery", "🚚 Жеткирүү кызматы барбы? / Есть ли доставка?",
     "Мис: Шаар ичинде жеткирүү бар / Например: Есть доставка по городу"),
]

CHAIN_RENTAL = [
    ("rentalPeriod", "📅 Кандай мөөнөткө бересиз? / На какой срок сдаёте?", "", RENT_PERIOD),
    ("rentalCharacteristics", "🛋️ Негизги мүнөздөмөлөрү жана шарттары кандай? / Основные характеристики и условия?",
     "Мис: абалы жакшы, жеткирүү бар / 2 бөлмө, эмерек менен"),
    ("rentalDeposit", "💰 Депозит (залог) барбы? / Есть ли депозит?",
     "Же өзүңүз жазыңыз / Или впишите свой", RENT_DEPOSIT),
]

CHAIN_JOB = [
    ("jobDuties", "🛠️ Милдеттери кандай? / Обязанности?",
     "Мис: Кардарларды тейлөө, товар тизүү / Например: Обслуживание клиентов"),
    ("jobRequirements", "🎯 Талаптар кандай? (жашы, тажрыйбасы, тили) / Требования (возраст, опыт, языки)?",
     "Мис: 20-35 жаш, кыргыз/орус тили эркин / Например: 20-35 лет, кыргызский/русский"),
    ("jobConditions", "☀️ Иш шарттары кандай? (график, орду, тамак) / Условия работы?",
     "Мис: 5/2, 09:00–19:00, түшкү тамак бар / Например: 5/2, 09:00–19:00, обед"),
]

# Дүң соода: көлөм жана жеткирүү шарты сурлат
WS_UNITS = _opts([(x, x) for x in (   # WS_UNITS: өлчөө бирдиктери
    "кг", "тонна", "даана", "капка", "куту", "литр", "метр", "м²")])

CHAIN_WHOLESALE = [
    ("wsUnit", "⚖️ Өлчөө бирдиги кандай? / Единица измерения?",
     "Же өзүңүз жазыңыз / Или впишите свою", WS_UNITS),
    ("wsMinOrder", "📦 Эң аз буйрутма канча? / Минимальный заказ?",
     "Мис: 5 / Например: 5"),
    ("wsDelivery", "🚚 Жеткирүү барбы? / Есть ли доставка?",
     "Же өзүңүз жазыңыз / Или впишите свой", DELIVERY_OPTS),
]

# Жүк ташуу: багыт, көтөрүмү, кузов
CHAIN_CARGO = [
    ("cargoRoute", "🗺️ Багыт кайсы? / Маршрут?",
     "Же өзүңүз жазыңыз / Или впишите свой", CARGO_ROUTE),
    ("cargoCapacity", "🏋️ Жүк көтөрүмү канча? / Грузоподъёмность?",
     "Же тоннасын жазыңыз, мис: 2 / Или впишите тонны", CARGO_CAP),
    ("cargoBody", "🚚 Кузовдун түрү кандай? / Тип кузова?",
     "Же өзүңүз жазыңыз / Или впишите свой", CARGO_BODY),
]

# Жумуш издөө: стажы, графиги, билими
CHAIN_JOBSEEK = [
    ("seekExp", "🧰 Стажыңыз канча? / Ваш опыт работы?", "", SEEK_EXP),
    ("seekSchedule", "🕒 Кандай график ыңгайлуу? / Какой график удобен?", "", SEEK_SCHED),
    ("seekEdu", "🎓 Билимиңиз кандай? / Ваше образование?", "", SEEK_EDU),
]

TRADE_WHOLESALE_OPTS = _opts([
    ("🛒 Чекене / Розница", "Чекене / Розница"),
    ("📦 Дүң / Опт", "Дүң / Опт"),
    ("🛍️ Чекене жана дүң / Розница и опт", "Чекене жана дүң / Розница и опт"),
])

CHAIN_TRADE_TAIL_TEXT = (
    "🚚 Жеткирүү (доставка) шарттары кандай? / Условия доставки?",
    "Мис: Чүй жана Ош аймактарына жеткирүү бар / Например: Есть доставка по Чуй и Ош",
)

PHOTO_TYPES = ("wholesale", "rental", "service", "cargo", "delivery")
VIDEO_TYPES = ("wholesale", "rental", "service")
ONE_PHOTO_TYPES = ("cargo", "delivery")
PHOTO_STEP_TEXT = ("📸 Сүрөт жүктөңүз, же «Даяр» басыңыз / \n"
                   "Загрузите фото или нажмите «Готово»:")

COMMENT_PROMPTS = {
    "trade":    "📝 Сатып жаткан товарларыңыз жөнүндө кыскача жазыңыз! / Напишите кратко о продаваемых товарах!",
    "vehicle":  "📝 Сатып жаткан унааңыз жөнүндө кыскача жазыңыз! / Напишите кратко о продаваемом транспорте!",
    "property": "📝 Сатып жаткан мүлкүңүз жөнүндө кыскача жазыңыз! / Напишите кратко о продаваемом имуществе!",
    "service":  "📝 Көрсөткөн кызматыңыз жөнүндө кыскача жазыңыз! / Напишите кратко о предоставляемой услуге!",
    "rental":   "📝 Ижарага берген нерсеңиз жөнүндө кыскача жазыңыз! / Напишите кратко о сдаваемом в аренду!",
    "delivery": "📝 Жеткирүү боюнча кыскача жазыңыз! / Напишите кратко о доставке!",
    "job":      "📝 Жумуш берүү боюнча кыскача жазыңыз! / Напишите кратко о вакансии!",
}

WARNING_TEXT = (
    "⚠️ Маанилүү эскертүү! / Важное предупреждение!\n"
    "Сураныч, жарыяңызда орунсуз, уят сөздөрдү жазбаңыз жана мыйзам тарабынан "
    "тыюу салынган товарларды же кызматтарды сунуштабаңыз. / Пожалуйста, не используйте "
    "неуместные слова и не размещайте запрещённые товары или услуги.\n"
    "Жарыялар автоматтык түрдө чыпкаланат. / Вся реклама проходит автоматическую фильтрацию."
)

# Базар/соода борбор кодун облуска байлоо
MARKET_OBLAST_MAP = {
    "bishkek": "Бишкек шаары", "osh": "Ош шаары",
    "jalalabad": "Жалал-Абад облусу", "karakol": "Ысык-Көл облусу",
    "balykchy": "Ысык-Көл облусу", "cholponata": "Ысык-Көл облусу",
    "naryn": "Нарын облусу", "talas": "Талас облусу",
    "kyzylkiya": "Баткен облусу", "batken": "Баткен облусу",
    "suluktu": "Баткен облусу", "razzakov": "Баткен облусу",
    "aidarken": "Баткен облусу", "kadamjai": "Баткен облусу",
    "karakol_jal": "Жалал-Абад облусу", "mailuusuu": "Жалал-Абад облусу",
    "tashkomur": "Жалал-Абад облусу", "kokjangak": "Жалал-Абад облусу",
    "bazarkorgon": "Жалал-Абад облусу", "shamaldysai": "Жалал-Абад облусу",
    "karasuu": "Ош облусу", "nookat": "Ош облусу", "ozgon": "Ош облусу",
    "tokmok": "Чүй облусу", "karabalta": "Чүй облусу", "kant": "Чүй облусу",
    "kemin": "Чүй облусу", "orlovka": "Чүй облусу", "kainyndy": "Чүй облусу",
    "shopokov": "Чүй облусу",
}


# __TAP_PATCH_V1__
def norm_phone(raw):
    """Ар кандай жазылышты +996XXXXXXXXX түрүнө келтирет.

    0775415688 / 775415688 / 996775415688 / +996 775 41 56 88
    / 0775-41-56-88  ->  +996775415688
    Жараксыз болсо None кайтарат.
    """
    d = "".join(ch for ch in str(raw or "") if ch.isdigit())
    if d.startswith("00996"):
        d = d[5:]
    elif d.startswith("996") and len(d) > 9:
        d = d[3:]
    if len(d) == 10 and d.startswith("0"):
        d = d[1:]
    if len(d) == 9 and not d.startswith("0"):
        return "+996" + d
    return None


def _cview(p, opts=None, text=None):
    v = _view(text or p[1], opts if opts is not None else (p[3] if len(p) > 3 else None),
              input=True, placeholder=p[2])
    if p[0] in MULTI_KEYS:
        v["multi"] = True
    if p[0] in NUMERIC_KEYS:
        v["numeric"] = True
    return v


def _unitize(key, value):
    suf = UNIT_SUFFIX.get(key)
    v = str(value).strip()
    if suf and v.replace(",", "").replace(".", "").replace(" ", "").isdigit():
        return v + suf
    return value


def _veh_prefill(d):
    """Кыймылдаткычтын түрү мурун тандалган — куяр майды кайра сурабайбыз."""
    eng = str(d.get("vehicleEngine") or "").split(" / ")[0].strip()
    if d.get("vehicleFuel") is None and eng:
        d["vehicleFuel"] = "Электр" if eng.startswith("Электр") else eng
    if eng.startswith("Электр") and d.get("vehicleEngVol") is None:
        d["vehicleEngVol"] = "Электр"


def _chain_pending(chain, data):
    """Чынжырда жооп берилбеген биринчи суроону кайтарат.

    Суроо 3 элементтүү (талаа, текст, мисал) же 4 элементтүү
    (кошумча — баскычтардын тизмеси) болушу мүмкүн.
    """
    for item in chain:
        if data.get(item[0]) is None:
            return item
    return None


# ─────────────────────────────────────────────────────────────
#  RENDER — кадамды көрсөтүү
# ─────────────────────────────────────────────────────────────

def render(step, data=None):
    d = data or {}
    at = d.get("adType")
    act = d.get("action")

    # Аймактар тандалып бүткөндөн кийинки биринчи суроонун башында
    # тандалган маршрут көрүнөт.
    if (step.startswith("taxi_") and not d.get("_rtshown")
            and step == _taxi_first_step(d)):
        _d2 = dict(d)
        _d2["_rtshown"] = 1
        _v = render(step, _d2)
        _v["text"] = _taxi_route(d) + _v["text"]
        return _v

    # ── Башталышы ───────────────────────────────────────────
    if step == "language_select":
        return _view("Колдонуу тилин тандаңыз / Выберите язык использования",
                     _opts([("🇰🇬 Кыргызча", "ky"), ("🇷🇺 Орусча / Русский", "ru")]))

    if step == "main_menu":
        return _view(GREETING + "\n\nЭмне кыласыз? / Что делаете? 👇",
                     _main_options())

    # ── Биздин сайт жана Жардам ─────────────────────────────
    if step == "post_site":   # POST_SITE_ONLY
        import os as _os
        lg = _ui_lang(d)
        url = (_os.environ.get("SITE_URL") or "").rstrip("/")
        if not url or "localhost" in url:
            url = "https://tapmeni.up.railway.app"
        url += "/post"
        if lg == "ru":
            txt = ("📢 Объявления теперь подаются на сайте.\n\n"
                   "Нажмите кнопку ниже — откроется форма. Номер подтверждается один раз, "
                   "а ваши объявления видны и здесь, в «📋 Мои рекламы».\n\n🌐 " + url)
            btn = "🌐 Разместить на сайте"
        else:
            txt = ("📢 Жарыя эми сайттан берилет.\n\n"
                   "Төмөнкү баскычты басыңыз — жарыя берүү формасы ачылат. Номериңизди бир жолу "
                   "ырастайсыз, ал эми жарыяларыңыз ушул ботто «📋 Менин жарыяларым» бөлүмүндө да көрүнөт.\n\n🌐 " + url)
            btn = "🌐 Сайтта жарыя берүү"
        return _view(txt, _opts([(btn, "tap_post_site"), (_hb("home", d), "home")]), localized=True)

    if step == "site_info":
        return _view(_help_text("site", _ui_lang(d)),
                     _opts([(_hb("home", d), "home")]), localized=True)

    if step == "help_menu":
        lg = _ui_lang(d)
        pairs = [(_topic_title(k, lg), "t:" + k) for k, _, _ in _HELP_TOPICS]
        pairs.append((_hb("home", d), "home"))
        return _view(_help_text("head", lg), _opts(pairs), localized=True)

    if step == "help_topic":
        lg = _ui_lang(d)
        key = d.get("helpTopic") or "about"
        return _view(_topic_title(key, lg).upper() + "\n\n"
                     + _help_text(key, lg),
                     _opts([(_hb("back", d), "back"),
                            (_hb("home", d), "home")]), localized=True)

    if step == "type_select":
        head = WARNING_TEXT + "\n\n" if act == "post" else ""
        q = ("Кандай жарыя бергиңиз келет? / Какую рекламу хотите разместить?"
             if act == "post" else "Эмнени издеп жатасыз? / Что ищете?")
        return _view(head + q, _opts([
            ("🛍 Соода-сатык / Торговля", "trade"),
            ("🏭 Соода-сатык (дүң) / Оптовая торговля", "wholesale"),
            ("🏘 Мүлк сатуу / Продажа имущества", "property"),
            ("🚗 Унаа сатуу / Продажа транспорта", "vehicle"),
            ("🛠 Кызмат көрсөтүү / Услуги", "service"),
            ("🔑 Ижарага берүү / Аренда", "rental"),
            ("📦 Жеткирүү кызматы / Доставка", "delivery"),
            ("🚛 Жүк ташуу / Грузоперевозки", "cargo"),
            ("🙋 Жумуш издөө / Поиск работы", "jobseek"),
            ("💼 Жумуш берүү / Работа", "job"),
            ("🏪 Базарлар / Рынки", "markets"),
            ("🏬 Соода борборлору, ири соода дүкөндөрү / Торговые центры и крупные магазины", "malls"),
            ("🚕 Такси Аймактар / Такси РЕГИОН", "taxi"),
        ]))

    # ── Аймак тандоо ────────────────────────────────────────
    if step == "oblast_select":
        return _view("Шаарды же облусту тандаңыз! / Выберите город или область!", _regions())

    if step == "city_scope_select":
        ob = d.get("oblast", "")
        verb = "жарыя бересизби" if act == "post" else "издейсизби"
        verb_ru = "Разместите рекламу" if act == "post" else "Ищете"
        if ob == "Ош шаары":
            sub = ("📍 Кичи район/МАБ/конуш/квартал тандоо / "
                   "Выбрать микрорайон/МАБ/посёлок/квартал")
        else:
            sub = "📍 Райондун бирин тандоо / Выбрать один из районов"
        return _view("%s боюнча %s (бүт шаар)? / %s по всему городу?" % (ob, verb, verb_ru),
                     _opts([("🏙 Бүт шаар боюнча / По всему городу", "city"), (sub, "district")]))

    if step == "district_select":
        ob = d.get("oblast", "")
        # Уста, жеткирүү жана жүк ташуу кошуна райондорду тейлейт —
        # аларга бир нече район тандоого уруксат.
        multi = _is_city(ob) or at in MULTI_DISTRICT_TYPES
        # CITY_ALL: шаарда — «Бүт шаар боюнча» жана аймактык башкармалыктар
        if _is_city(ob):
            text = ("Бүт шаар боюнча, же аймактык башкармалыктарды тандаңыз / "
                    "По всему городу или выберите территориальные управления:")
        elif multi:
            text = "Бир же бир нече районду тандаңыз / Выберите один или несколько районов:"
        else:
            text = "%s — район же шаарды тандаңыз / Выберите район или город:" % ob
        opts = [{"label": "%s / %s" % (x, ru_name(x)), "value": x}
                for x in get_districts(ob)]
        if _is_city(ob):
            opts = [{"label": "🏙 Бүт шаар боюнча / По всему городу",
                     "value": "__city__"}] + opts
        return _view(text, opts, multi=multi)

    if step == "city_district_scope_select":
        verb = "жарыя бересизби" if act == "post" else "издейсизби"
        return _view("%s боюнча %s (бүт район)? / По всему району?" % (d.get("district", ""), verb),
                     _opts([("📍 Бүт район боюнча / По всему району", "district_only"),
                            ("🏘 Кичи район/МАБ/конуш/квартал тандоо / Выбрать микрорайон/МАБ", "locality")]))

    if step == "oblast_district_scope_select":
        dist = d.get("district", "") or ""
        unit = "шаар" if dist.endswith("шаары") else "район"
        unit_ru = "городу" if dist.endswith("шаары") else "району"
        verb = "жарыя бересизби" if act == "post" else "издейсизби"
        return _view("%s боюнча %s (бүт %s)? / По всему %s?" % (dist, verb, unit, unit_ru),
                     _opts([("📍 Бүт %s боюнча / По всему %s" % (unit, unit_ru), "district_only"),
                            (("🏘 Кичи район/конуш тандоо / Выбрать микрорайон/посёлок"   # GEOFIX
                              if unit == "шаар" else
                              "🏘 Айыл аймактын бирин тандоо / Выбрать аильный округ"), "locality")]))

    if step == "locality_select":
        ob = d.get("oblast", "")
        text = ("Бир же бир нече кичи районду/МАБды/конушту тандаңыз / Выберите микрорайон(ы):"
                if _is_city(ob) or str(d.get("district") or "").endswith("шаары")   # GEOFIX
                else "Шаарды же айыл аймакты тандаңыз (бир же бир нече) / Выберите город или аильный округ:")
        return _view(text, _from_list(get_localities(ob, d.get("district"))), multi=True)

    if step == "locality_scope_select":
        verb = "жарыя бересизби" if act == "post" else "издейсизби"
        _ln = str(d.get("locality", "")).split(" / ")[0].strip()   # GEOFIX
        if "шаар" in _ln:
            return _view("%s боюнча %s (бүт шаар)? / По всему городу?" % (_ln, verb),
                         _opts([("🏙 Бүт шаар боюнча / По всему городу", "locality_only"),
                                ("🏡 Кичи район/конуш тандоо / Выбрать микрорайон", "village")]))
        return _view("%s боюнча %s (бүт айыл аймак)? / По всему аильному округу?" % (_ln, verb),
                     _opts([("🏘 Бүт айыл аймак боюнча / По всему аильному округу", "locality_only"),
                            ("🏡 Айылдын бирин тандоо / Выбрать одно из сёл", "village")]))

    if step == "village_select":
        return _view("Бир же бир нече айыл тандаңыз / Выберите одно или несколько сёл:",
                     _from_list(get_villages(d.get("oblast"), d.get("district"), d.get("locality"))),
                     multi=True)

    # ── Базарлар / соода борборлору ─────────────────────────
    if step == "markets_type":
        return _view("Кайсы түрдөн? / Какой тип объекта?",
                     [{"label": "%s %s" % (t["emoji"], t["label"]), "value": t["id"]}
                      for t in (MALLS_TYPES if at == "malls" else MARKETS_TYPES)])

    if step == "livestock_oblast_select":
        return _view("Кайсы шаар/облустан? / Из какого города/области?", _regions())

    if step == "livestock_district_select":
        return _view("Кайсы район/шаардан? / Из какого района/города?",
                     [{"label": "%s / %s" % (x, ru_name(x)), "value": x}
                      for x in get_districts(d.get("oblast"))])

    if step == "livestock_market_name":
        return _view("Мал базарынын аты кандай? / Название скотного рынка:",
                     input=True,
                     placeholder="Мис: Жапалак мал базары / Например: рынок Жапалак")

    if step == "generic_markets_group":
        return _view("Кайсы шаардан? / Из какого города?", _from_groups(MARKETS_GROUPS))

    if step == "generic_markets_sub":
        subs = (MARKETS_SUBS_BY_TYPE.get(d.get("marketsType")) or {}).get(d.get("marketsGroup")) or []
        return _view("Кайсы жерден? / Из какого места?", _from_list(subs))

    # ── Соода-сатык категориялары ───────────────────────────
    if step == "trade_category":
        if at == "vehicle":
            q = ("Кандай унаа сатасыз? / Какой транспорт продаёте?" if act == "post"
                 else "Кандай унаа издеп жатасыз? / Какой транспорт ищете?")
        elif at == "property":
            q = ("Кандай мүлк сатасыз? / Какое имущество продаёте?" if act == "post"
                 else "Кандай мүлк издеп жатасыз? / Какое имущество ищете?")
        else:
            q = ("Кандай товар сатасыз? / Что продаёте?" if act == "post"
                 else "Кандай товар издеп жатасыз? / Какой товар ищете?")

        # Мүлктүн категориялары өзүнчө тизмеде — базар үчүн экөөн кошобуз
        _ALL_TRADE = PROPERTY_CATEGORIES + VEHICLE_SALE_CATEGORIES + TRADE_CATEGORIES
        mt = d.get("marketsType")
        if at == "property":
            cats = PROPERTY_CATEGORIES
        elif at == "vehicle":
            cats = VEHICLE_SALE_CATEGORIES
        elif at == "markets" and mt == "car_market":
            cats = [c for c in _ALL_TRADE if c["id"] in ("vehicles", "auto_parts")]
        elif at == "markets" and mt == "livestock_market":
            cats = [c for c in TRADE_CATEGORIES if c["id"] == "animals"]
        elif at in ("markets", "malls"):
            cats = TRADE_CATEGORIES
        else:
            cats = TRADE_CATEGORIES
        return _view(q,
                     [{"label": "%s %s" % (c["emoji"], c["label"]), "value": c["id"]} for c in cats])

    if step == "trade_demographic":
        return _view("Кимге арналган? / Для кого?",
                     [{"label": "%s %s" % (x["emoji"], x["label"]), "value": x["id"]}
                      for x in DEMOGRAPHICS])

    if step == "trade_season":
        return _view("Кайсы мезгилге? / На какой сезон?",
                     [{"label": "%s %s" % (x["emoji"], x["label"]), "value": x["id"]}
                      for x in SEASONS])

    if step == "trade_item_type":
        subs = (get_footwear_subs() if d.get("category") == "footwear"
                else get_clothing_subs(d.get("demographic"), d.get("season")))
        # (тандоо экөөндө тең бирдей — түрүн тактоо)
        return _view("Түрүн тандаңыз / Выберите тип:", _from_list(subs), multi=True)

    if step == "trade_heating_fuel_select":
        return _view("Кайсы отун? / Какое топливо?", _from_list(HEATING_FUEL_SUBS), multi=True)

    if step == "trade_realestate_type":
        return _view("Кайсы түрү? / Какой тип?", _from_groups(REALESTATE_TYPES))

    if step == "trade_realestate_sub":
        return _view("Тагыраак тандаңыз / Уточните:",
                     _from_list(REALESTATE_SUBS.get(d.get("realestateType"), [OTHER])), multi=True)

    if step == "trade_vehicle_category":
        return _view("Унаанын түрү? / Тип транспорта?", _from_groups(VEHICLE_CATEGORIES))

    if step == "trade_vehicle_body":
        return _view("Кузовдун түрү? / Тип кузова?",
                     _from_list(VEHICLE_BODY_TYPES) + [SKIP_OPT])

    if step == "trade_vehicle_engine":
        return _view("Кыймылдаткычы? / Двигатель?",
                     _from_list(VEHICLE_ENGINE_TYPES) + [SKIP_OPT])

    if step == "trade_vehicle_sub":
        return _view("Тагыраак тандаңыз / Уточните:",
                     _from_list(VEHICLE_SUBS.get(d.get("vehicleCategory"), [OTHER])), multi=True)

    if step == "trade_sub_select":
        return _view("Түрүн тандаңыз / Выберите тип:",
                     _from_list(_trade_subs(d.get("category"))), multi=True)

    # Соода: топ/подтоп (14 категория үчүн бирдей)
    if step == "trade_group":
        groups, _ = GROUP_TABLES[d["category"]]
        return _view("Кайсы топко кирет? / К какой группе относится?", _from_groups(groups))

    if step == "trade_group_sub":
        _, subs = GROUP_TABLES[d["category"]]
        return _view("Түрүн тандаңыз / Выберите тип:",
                     _from_list(subs.get(d.get("tradeGroup"), [OTHER])), multi=True)

    # ── Кызмат/ижара/жумуш/жеткирүү категориялары ───────────
    if step == "category_select":
        cats = get_categories(at)
        title = ({
            "service":  "Кандай кызмат көрсөтөсүз? / Какую услугу оказываете?",
            "rental":   "Эмнени ижарага бересиз? / Что сдаёте в аренду?",
            "job":      "Кайсы тармакта жумуш? / В какой сфере работа?",
            "delivery": "Эмнени жеткиресиз? / Что доставляете?",
            "wholesale": "Кайсы товарды дүң сатасыз? / Какой товар продаёте оптом?",
            "cargo":     "Кандай жүк ташуу кызматы? / Какая услуга грузоперевозки?",
            "jobseek":   "Кайсы тармактан жумуш издейсиз? / В какой сфере ищете работу?",
        } if act == "post" else {
            "service":  "Кандай кызмат керек? / Какая услуга нужна?",
            "rental":   "Эмне ижарага керек? / Что хотите арендовать?",
            "job":      "Кайсы тармактан жумуш издейсиз? / В какой сфере ищете работу?",
            "delivery": "Эмнени жеткирүү керек? / Что нужно доставить?",
            "wholesale": "Кайсы товар дүң керек? / Какой товар нужен оптом?",
            "cargo":     "Кандай жүк ташуу керек? / Какая грузоперевозка нужна?",
            "jobseek":   "Кайсы тармактан кызматкер издейсиз? / В какой сфере ищете работника?",
        }).get(at, "Категорияны тандаңыз / Выберите категорию:")
        return _view(title,
                     [{"label": ("%s %s" % (c.get("emoji", ""), c["label"])).strip(),
                       "value": c["id"]} for c in cats])

    if step == "subcategory_select":
        return _view("Тагыраак тандаңыз / Уточните:",
                     _from_list(get_subs_for_category(at, d.get("category"))), multi=True)

    if step == "svc_group":
        groups, _ = SERVICE_GROUP_TABLES[d["category"]]
        return _view("Кайсы топко кирет? / К какой группе относится?", _from_groups(groups))

    if step == "svc_group_sub":
        _, subs = SERVICE_GROUP_TABLES[d["category"]]
        return _view("Түрүн тандаңыз / Выберите тип:",
                     _from_list(subs.get(d.get("svcGroup"), [OTHER])), multi=True)

    # ── Соода жарыясынын аталышы (чынжыр) ───────────────────
    if step == "trade_title":
        mt = d.get("marketsType")
        cat = d.get("category")

        if (at == "markets" and mt not in ("mall", "store", "livestock_market")
                and not (mt == "car_market" and (cat == "vehicles"
                                                 or str(cat).startswith("veh_")))
                and d.get("marketStall") is None):
            return _view("Кайсы катар/өтмөк жана соода орду? / Ряд/проход и торговое место:",
                         input=True, placeholder="Мис: 3-катар, 45-орун / Например: 3-й ряд, место 45")

        if cat == "animals":
            p = _chain_pending(CHAIN_ANIMALS, d)
            if p:
                return _cview(p)

        if cat == "vehicles" or str(cat).startswith("veh_"):   # VEH_SPLIT
            _veh_prefill(d)
            p = _chain_pending(CHAIN_VEHICLES, d)
            if p:
                # Баскычтары бар кадамда да текст жазса болот
                opts = p[3] if len(p) > 3 else None
                if p[0] == "vehicleBrand" and d.get("_china"):
                    opts = CHINA_BRANDS
                return _cview(p, opts=opts)

        if cat == "realestate" or str(cat).startswith("re_"):   # RE_SPLIT
            _rch = REALESTATE_CHAINS.get(
                d.get("realestateType") or str(cat)[3:], CHAIN_HOME)
            p = _chain_pending(_rch, d)
            if p:
                opts = p[3] if len(p) > 3 else None
                return _cview(p, opts=opts)

        if at == "markets" and mt == "bazaar":
            p = _chain_pending(CHAIN_BAZAAR, d)
            if p:
                return _cview(p)

        if at in ("markets", "malls") and mt == "mall":
            p = _chain_pending(CHAIN_MALL, d)
            if p:
                return _cview(p)

        if at in ("markets", "malls") and mt == "store":
            p = _chain_pending(CHAIN_STORE, d)
            if p:
                return _cview(p)

        if (at == "trade" and not str(cat).startswith(("re_", "veh_"))
                and cat not in ("vehicles", "animals", "realestate",
                                "agro_machinery")):
            if d.get("tradeDelivery") is None:
                return _view(CHAIN_TRADE_TAIL_TEXT[0], DELIVERY_OPTS, input=True,
                             placeholder="Же өзүңүз жазыңыз / Или впишите свой")

        return _view("Жарыянын аталышын жазыңыз / Введите название объявления:",
                     input=True, placeholder="Мис: Жаңы кийимдер / Например: Новая одежда")

    if step == "trade_price":
        return _view("Баасы канча? / Цена? (сом)",
                     [{"label": p["label"], "value": p["value"]} for p in TRADE_PRICE_PRESETS])

    if step == "trade_price_custom":
        return _view("Баасын жазыңыз / Введите цену:", input=True, placeholder="Мис: 1 500 сом")

    if step == "trade_bargain":
        return _view("Соодалашса болобу? / Торг уместен?",
                     _opts([("🤝 Ооба, соодалашса болот / Да, торг уместен", "yes"),
                            ("🔒 Жок, баа катуу / Нет, цена твёрдая", "no")]))

    if step == "trade_photo":
        return _view("📸 Сүрөт жүктөңүз, же «Даяр» басыңыз / \nЗагрузите фото или нажмите «Готово»:",
                     _opts([("✅ Даяр / Готово", "__photo_done__")]),
                     photo=True, video=True)

    # ── Жалпы куйрук ────────────────────────────────────────
    if step == "post_name":
        if at == "rental":
            p = _chain_pending(CHAIN_RENTAL, d)
            if p:
                return _cview(p)
        if at == "job":
            p = _chain_pending(CHAIN_JOB, d)
            if p:
                return _cview(p)
        for _at, _chain in (("wholesale", CHAIN_WHOLESALE),
                            ("cargo", CHAIN_CARGO),
                            ("jobseek", CHAIN_JOBSEEK)):
            if at == _at:
                p = _chain_pending(_chain, d)
                if p:
                    if p[0] == "wsMinOrder" and d.get("wsUnit"):   # WS_UNITS
                        u = d["wsUnit"]
                        v = _view("📦 Эң аз буйрутма канча %s? / Минимальный заказ (%s)?" % (u, u),
                                  input=True, placeholder=p[2])
                        v["numeric"] = True
                        return v
                    return _cview(p)
        return _view("Сиздин атыңыз же компанияңыздын аты кандай? / Ваше имя или название компании? 👤",
                     input=True, placeholder="Мис: Айбек / Например: Айбек")

    if step == "post_price":
        text = ("Айлык канча? / Зарплата? (сом)" if at == "job"
                else "Күткөн айлыгыңыз? / Ожидаемая зарплата? (сом)" if at == "jobseek"
                else "Жеткирүү баасы канча? / Стоимость доставки? (сом)" if at == "delivery"
                else "Ташуу баасы канча? / Стоимость перевозки? (сом)" if at == "cargo"
                else "Дүң баасы канча? / Оптовая цена? (сом)" if at == "wholesale"
                else "Баасы канча? / Цена? (сом)")
        presets = (JOB_SALARY_PRESETS if at in ("job", "jobseek")
                   else SERVICE_PRICE_PRESETS)
        return _view(text, [{"label": p["label"], "value": p["value"]} for p in presets])

    if step == "post_price_custom":
        _jb = at in ("job", "jobseek")   # HELP_CHIPS
        return _view("Айлыкты жазыңыз / Введите зарплату:" if _jb
                     else "Баасын жазыңыз / Введите цену:",
                     input=True, placeholder="Мис: 25 000 сом" if _jb else "Мис: 1 500 сом")

    if step == "post_calltime":
        return _view("📞 Сизге качан чалса болот? / Когда вам можно звонить?",
                     [{"label": p["label"], "value": p["value"]} for p in CALL_TIME_PRESETS])

    if step == "post_calltime_custom":
        return _view("Ыңгайлуу убактыңызды жазыңыз / Введите удобное время:",
                     input=True, placeholder="Мис: 09:00–18:00")

    if step == "post_whatsapp":
        err = ("❗️ Номер туура эмес — 9 сан керек. / Неверный номер — нужно 9 цифр.\n\n"
               if d.get("phoneErr") else "")
        return _view(err + "📱 Байланыш номериңизди жазыңыз (чалуу жана WhatsApp үчүн) / "
                     "Введите номер для связи (звонки и WhatsApp):\n"
                     "(0700 000 000 же 700 000 000 — экөө тең болот / "
                     "можно 0700 000 000 или 700 000 000)",
                     input=True, placeholder="0700 000 000")

    if step == "post_duration":
        return _view("⏳ Жарыя канча күн жарыяланат? / На сколько дней разместить рекламу?",
                     [{"label": p["label"], "value": p["value"]} for p in DURATION_PLANS])

    if step == "post_comment":
        base = COMMENT_PROMPTS.get(at, "📝 Комментарий жазыңыз / Напишите комментарий")
        return _view(base + "\n(болбосо — сызыкча коюңуз / если нет — поставьте прочерк):",
                     input=True, placeholder="Мис: Тез жана сапаттуу / Например: Быстро и качественно")

    if step == "post_photo":
        return _view(PHOTO_STEP_TEXT,
                     _opts([("✅ Даяр / Готово", "__photo_done__")]),
                     photo=True, video=(at in VIDEO_TYPES and at not in ONE_PHOTO_TYPES),
                     photo_max=(1 if at in ONE_PHOTO_TYPES else None))

    if step == "post_preview":
        return _view("Жарыяңыз даяр! Жарыялайлыбы? / Ваше объявление готово! Публикуем?",
                     _opts([("✅ Ооба, жарыялайлы / Да, опубликовать", "confirm"),
                            ("🏠 Башкы меню / Главное меню", "cancel")]),
                     final=True)

    if step == "post_done":
        return _view("🎉 Жарыяңыз жарыяланды! / Ваше объявление опубликовано!",
                     _opts([("🏠 Башкы меню / Главное меню", "menu")]))

    # ── Издөө ───────────────────────────────────────────────
    if step == "search_method_choice":
        return _view("Кантип издейсиз? / Как искать?",
                     _opts([("📂 Категория боюнча / По категориям", "category"),
                            ("🔤 Сөз боюнча издөө / Поиск по слову", "keyword")]))

    if step == "search_keyword_input":
        return _view("Эмнени издейсиз? Сөз жазыңыз / Что ищете? Введите слово:",
                     input=True, placeholder="Мис: батир, дөңгөлөк / Например: квартира, шины")

    if step == "search_results":
        return _view("🔍 Издөө натыйжалары / Результаты поиска", final=True)

    # ── Такси ───────────────────────────────────────────────
    # Флоу «Такси роБОТ» ботундагыдай: адегенде ким экениң,
    # анан багыт (Бишкекке / район аралык), анан маршрут, анан суроолор.

    if step == "taxi_role":
        if act == "post":
            return _view("🚕 Такси боюнча ким болуп жарыя бересиз? / "
                         "Кем вы в этом объявлении?",
                         _opts([("🚖 Айдоочумун / Я водитель", "driver"),
                                ("🧍 Жүргүнчүмүн / Я пассажир", "passenger")]))
        return _view("🚕 Кимди издеп жатасыз? / Кого ищете?",
                     _opts([("🚖 Айдоочу издейм / Ищу водителя", "driver"),
                            ("🧍 Жүргүнчү издейм / Ищу пассажира", "passenger")]))

    if step == "taxi_mode":
        return _view(("Кайсы багытта жарыя бересиз? / В каком направлении?"
                      if act == "post" else
                      "Кайсы багыт боюнча издейсиз? / По какому направлению ищете?"),
                     _opts([("Облустардын район/шаарларынан Бишкекке жана кайтуу",
                             "bishkek"),
                            ("Район/шаар аралык", "local"),
                            ("✈️ Манас аэропортко барып-кайтуу", "air_manas"),
                            ("✈️ Ош аэропортко барып-кайтуу", "air_osh")]))   # TAXI_AIR_BOT

    if step == "taxi_air_dir":   # TAXI_AIR_BOT
        ap = "Манас" if d.get("taxiMode") == "air_manas" else "Ош"
        return _view("✈️ %s аэропорту\nБагытты тандаңыз: / Выберите направление:" % ap,
                     _opts([("✈️ %s аэропортко барам" % ap, "to_air"),
                            ("✈️ %s аэропорттон кайтам" % ap, "from_air")]))

    if step == "taxi_air_oblast":
        q = ("Кайсы облустан чыгасыз?" if d.get("taxiAirDir") == "to_air"
             else "Кайсы облуска барасыз?")
        return _view("🗺 " + q, _from_list(TX_OBLASTS))

    if step == "taxi_air_place":
        ob = d.get("taxiAirOblast")
        q = ("Кайсы райондон/шаардан чыгасыз?" if d.get("taxiAirDir") == "to_air"
             else "Кайсы районго/шаарга барасыз?")
        return _view("📍 %s\n%s" % (ob, q), _from_list(TX_DISTRICTS.get(ob, [])))

    if step == "taxi_dir":
        return _view("Багытты тандаңыз: / Выберите направление:",
                     _opts([("🚕 Бишкекке барам", "to_bishkek"),
                            ("🚕 Бишкектен кайтам", "from_bishkek")]))

    if step == "taxi_region":
        q = ("Кайсы облуска барасыз?" if d.get("taxiDir") == "from_bishkek"
             else "Кайсы облустан чыгасыз?")
        return _view("🗺 " + q, _from_list(TX_REGION_LIST))

    if step == "taxi_city":
        reg = d.get("taxiRegion")
        return _view("📍 %s\nШаар/район тандаңыз:" % reg,
                     _from_list(TX_REGIONS.get(reg, [])))

    if step == "taxi_lo_oblast":
        return _view("🗺 Кайсы облустан чыгасыз?", _from_list(TX_OBLASTS))

    if step == "taxi_lo_from":
        ob = d.get("taxiLoOblast")
        return _view("📍 %s\nКайсы райондон/шаардан чыгасыз?" % ob,
                     _from_list(TX_DISTRICTS.get(ob, [])))

    if step == "taxi_lo_to_oblast":
        return _view("📍 Чыгуу: %s\n🗺 Кайсы облуска барасыз?" % d.get("taxiFrom"),
                     _from_list(TX_OBLASTS))

    if step == "taxi_lo_to":
        ob = d.get("taxiLoToOblast")
        items = [c for c in TX_DISTRICTS.get(ob, []) if c != d.get("taxiFrom")]
        return _view("📍 %s\nКайсы районго/шаарга барасыз?" % ob, _from_list(items))

    # ── Суроолор ────────────────────────────────────────────

    if step == "taxi_name":
        return _view("Атыңызды жазыңыз:", input=True, placeholder="Мис: Азамат")

    if step == "taxi_car":
        return _view("Машинаңыздын маркасы жана модели:",
                     input=True, placeholder="Мис: Toyota Camry, ак")

    if step == "taxi_date":
        return _view("📅 Качан жолго чыгасыз?",
                     _opts([(date_label(0), "d0"), (date_label(1), "d1")]))

    if step == "taxi_time":
        opts = [{"label": h, "value": h} for h in day_hours()]
        if d.get("taxiRole") == "driver":
            # Айдоочу так убакыт коё албаганда: орун толгондо чыгат.
            # Кыргызстанда эң кеңири таралган иштөө ыкмасы.
            opts.append({"label": "🚗 Орун толгондо чыгам", "value": "__full__"})
        return _view("⏰ Саат канчада жолго чыгасыз?\n"
                     "Тизмеде жок убакыт болсо — жазып жибериңиз "
                     "(мис. 05:30 же 22:00).", opts)

    if step == "taxi_seats":
        return _view("👥 Канча бош орун бар?",
                     _from_list([str(i) for i in range(1, 8)]))

    if step == "taxi_people":
        return _view("👥 Канча киши жолго чыгасыңар?\n"
                     "Салон болсо — «Салон» деп жазып жибериңиз.",
                     _from_list([str(i) for i in range(1, 8)]))

    if step == "taxi_baggage":
        return _view("🎒 Багажыңыз барбы?\n"
                     "Жок болсо — төмөнкү баскычты басыңыз.\n"
                     "Бар болсо — жазып жибериңиз (мис. 2 чемодан).",
                     _opts([("🚫 Жок", "__no__")]))

    if step == "taxi_price":
        return _view("💰 Жол киреси канча?\n"
                     "Сумманы жазыңыз (мис. 1200), же төмөнкү баскычты басыңыз.",
                     _opts([("🤝 Келишим баада", "__deal__")]))

    if step == "taxi_comment":
        q = ("📝 Кошумча комментарий (жазбасаңыз, «жок» деп жазыңыз):"
             if d.get("taxiRole") == "driver"
             else "📝 Айдоочуларга эмне деп жазасыз?")
        return _view(q, input=True, placeholder="Мис: Жүк ташыйм")

    if step == "taxi_phone":
        return _view("📞 Мобилдик телефон номериңиз:",
                     input=True, placeholder="700 000 000")

    if step == "taxi_safety":
        return _view(
            "🚦 Коопсуздук эрежелерин окуп алыңыз!\n\n"
            "Жолго чыгаардан мурун жүргүнчүнүн атын жана номерин жазып алыңыз, "
            "жакындарыңызга маршрутуңузду билдирип коюңуз, түнкүсүн бейтааныш "
            "жерде токтобоңуз.\n\n"
            "Бул сиздин жана жүргүнчүлөрдүн өмүрү үчүн маанилүү.",
            _opts([("✅ Түшүндүм, жарыялаймын", "confirm")]))

    if step == "taxi_preview":
        return _view("Такси жарыяңыз даяр! Жарыялайлыбы? / Объявление готово?",
                     _opts([("✅ Ооба, жарыялайлы / Да, опубликовать", "confirm"),
                            ("🏠 Башкы меню / Главное меню", "cancel")]),
                     final=True)

    if step == "my_posts_phone":
        return _view("📱 Телефон номериңизди жазыңыз / Введите ваш номер телефона:",
                     input=True, placeholder="700 000 000")

    if step == "my_posts":
        return _view("📋 Сиздин жарыяларыңыз / Ваши объявления", final=True)

    # Белгисиз кадам
    return _view("Башкы менюга кайттык 🏠 / Вернулись в главное меню 🏠",
                 _main_options())


# ─────────────────────────────────────────────────────────────
#  ADVANCE — кийинки кадамга өтүү
# ─────────────────────────────────────────────────────────────

def _after_region(d):
    """Аймак тандалгандан кийин кайда барабыз."""
    if d.get("action") == "post":
        return ("trade_category" if d.get("adType") in ("trade", "property", "vehicle")
                else "category_select")
    if d.get("searchByRegion"):
        return "search_results"
    return "search_method_choice"


def _after_subcategory(d):
    """Подкатегория тандалгандан кийин кайда барабыз."""
    if d.get("action") == "post":
        return ("trade_title"
                if d.get("adType") in ("trade", "markets", "malls", "property", "vehicle")
                else "post_name")
    return "search_results"


def _taxi_route(d):
    """«Манас → Бишкек» түрүндөгү маршрут сабы."""
    a, b = d.get("taxiFrom"), d.get("taxiTo")
    return "🚕 %s → %s\n\n" % (a, b) if a and b else ""


def _taxi_step_name(step):
    """"taxi_name" -> "name" """
    return step[5:] if step.startswith("taxi_") else step


def _taxi_first_step(d):
    """
    Маршрут тандалгандан кийин кайда барабыз.
    Издөө болсо — түз натыйжага; суроолор жарыя берүүгө гана таандык.
    """
    if d.get("action") != "post":
        return "search_results"
    return "taxi_" + steps_of(d.get("taxiRole"))[0]


def _taxi_next(d, current):
    """Тизмедеги кийинки суроо, же аягы."""
    steps = steps_of(d.get("taxiRole"))
    try:
        i = steps.index(current)
    except ValueError:
        i = len(steps) - 1
    if i < len(steps) - 1:
        return "taxi_" + steps[i + 1]
    # Айдоочуга коопсуздук эскертүүсү, жүргүнчүгө түз алдын ала көрүү
    return "taxi_safety" if d.get("taxiRole") == "driver" else "taxi_preview"


def _after_subcategory(d):
    """Подкатегория тандалгандан кийин кайда барабыз."""
    if d.get("action") == "post":
        return ("trade_title"
                if d.get("adType") in ("trade", "markets", "malls", "property", "vehicle")
                else "post_name")
    return "search_results"


def advance(step, value, data=None):
    """Кийинки (step, data) жупту кайтарат."""
    d = dict(data or {})
    at = d.get("adType")

    def go(next_step, **patch):
        d.update(patch)
        return next_step, d

    # ── Башталышы ───────────────────────────────────────────
    if step == "language_select":
        return go("main_menu", uiLanguage=value)

    if step == "main_menu":
        if value == "tap_site":
            return go("site_info")
        if value == "tap_help":
            return go("help_menu")
        if value == "tap_lang":
            # Тилди кайра тандоо — башка маалымат сакталбайт.
            return "language_select", {}
        if value == "myposts":
            return go("my_posts", phone="")   # MYPOSTS_VERIFIED
        if value == "post":   # POST_SITE_ONLY: жарыя сайттан гана берилет
            return go("post_site")
        return go("type_select", action=value)

    # ── Биздин сайт жана Жардам ─────────────────────────────
    if step == "post_site":   # POST_SITE_ONLY
        return go("main_menu")

    if step == "site_info":
        return go("main_menu")

    if step == "help_menu":
        if str(value).startswith("t:"):
            return go("help_topic", helpTopic=str(value)[2:])
        return go("main_menu")

    if step == "help_topic":
        return go("help_menu") if value == "back" else go("main_menu")

    if step == "type_select":
        if value == "taxi":
            return go("taxi_role", adType="taxi")
        if value in ("markets", "malls"):
            return go("markets_type", adType=value)
        return go("oblast_select", adType=value)

    # ── Аймак ───────────────────────────────────────────────
    if step == "oblast_select":
        if value == ALL_KG:
            # Бүт өлкө: район, конуш сурабайбыз — жарыя баары жерде көрүнөт
            d.update(oblast="", district=None, locality=None, village=None)
            return _after_region(d), d
        d["oblast"] = value
        # CITY_SCOPE_ALWAYS: шаарда ар дайым «Бүт шаар / МАБ тандоо» экраны
        return ("city_scope_select" if _is_city(value) else "district_select"), d

    if step == "city_scope_select":
        if value == "city":
            d.update(district=None, locality=None)
            return _after_region(d), d
        return go("district_select")

    if step == "district_select":
        if "__city__" in str(value).split(","):   # CITY_ALL
            d.update(district=None, locality=None)
            return _after_region(d), d
        d["district"] = value
        if "," in value:            # бир нече район тандалды
            d["locality"] = None
            return _after_region(d), d
        if _is_city(d.get("oblast")):
            return "city_district_scope_select", d
        return "oblast_district_scope_select", d

    if step in ("city_district_scope_select", "oblast_district_scope_select"):
        if value == "district_only":
            d["locality"] = None
            return _after_region(d), d
        return go("locality_select")

    if step == "locality_select":
        d["locality"] = value
        if _is_city(d.get("oblast")) or "," in value:
            return _after_region(d), d
        node = (GEO.get(d.get("oblast")) or {}).get(d.get("district"))
        if isinstance(node, list):
            return _after_region(d), d
        try:   # GEOFIX: «Кара-Суу шаары» → айылы бирөө гана («Кара-Суу») — сурабайбыз
            if len(get_villages(d.get("oblast"), d.get("district"), value) or []) <= 1:
                d["village"] = None
                return _after_region(d), d
        except Exception:
            pass
        return "locality_scope_select", d

    if step == "locality_scope_select":
        if value == "locality_only":
            d["village"] = None
            return _after_region(d), d
        return go("village_select")

    if step == "village_select":
        d["village"] = value
        return _after_region(d), d

    # ── Базарлар ────────────────────────────────────────────
    if step == "markets_type":
        d["marketsType"] = value
        return ("livestock_oblast_select" if value == "livestock_market"
                else "generic_markets_group"), d

    if step == "livestock_oblast_select":
        return go("livestock_district_select", oblast=value)

    if step == "livestock_district_select":
        return go("livestock_market_name", district=value)

    if step == "livestock_market_name":
        return go("trade_category", subcategory=value, title=value,
                  locality=value, category="markets")

    if step == "generic_markets_group":
        return go("generic_markets_sub", marketsGroup=value)

    if step == "generic_markets_sub":
        return go("trade_category", subcategory=value, title=value,
                  oblast=MARKET_OBLAST_MAP.get(d.get("marketsGroup"), "Кыргызстан"),
                  locality=value, category="markets")

    # ── Соода категориялары ─────────────────────────────────
    if step == "trade_category":
        d["category"] = value
        if value == "clothing":
            return "trade_demographic", d
        if value == "footwear":
            return "trade_item_type", d
        if value == "heating_fuel":
            return "trade_heating_fuel_select", d
        if str(value).startswith("re_"):   # RE_SPLIT
            d["realestateType"] = str(value)[3:]
            return "trade_realestate_sub", d
        if value == "realestate":
            return "trade_realestate_type", d
        if str(value).startswith("veh_"):   # VEH_SPLIT
            _vc = str(value)[4:]
            d["vehicleCategory"] = _vc
            if _vc == "electric":
                d.update(vehicleBody="", vehicleEngine="Электромобиль / Электромобиль")
                return "trade_vehicle_sub", d
            if _vc != "light":
                d["vehicleBody"] = ""
                return "trade_vehicle_engine", d
            return "trade_vehicle_body", d
        if value == "vehicles":
            return "trade_vehicle_category", d
        if _has_choice(_trade_subs(value)):
            return "trade_sub_select", d
        if value in GROUP_TABLES:
            return "trade_group", d
        return _after_subcategory(d), d

    if step == "trade_demographic":
        return go("trade_item_type", demographic=value, season=None)

    if step == "trade_season":
        return go("trade_item_type", season=value)

    if step in ("trade_item_type", "trade_heating_fuel_select",
                "trade_realestate_sub", "trade_vehicle_sub", "trade_group_sub",
                "trade_sub_select"):
        d["subcategory"] = value
        _sb = str(value).split(" / ")[0].lower()
        if (str(d.get("category") or "").startswith("re_")
                and not any(w in _sb for w in ("батир", "гостинка", "студия",
                                               "бөлмө", "таунхаус"))):
            d["homeFloor"] = "—"   # HOME_FLOOR: үйдө кабат суралбайт
        return _after_subcategory(d), d

    if step == "trade_realestate_type":
        return go("trade_realestate_sub", realestateType=value)

    if step == "trade_vehicle_category":
        d["vehicleCategory"] = value
        if value == "electric":
            d.update(vehicleBody="", vehicleEngine="Электромобиль / Электромобиль")
            return "trade_vehicle_sub", d
        if value != "light":
            d["vehicleBody"] = ""
            return "trade_vehicle_engine", d
        return "trade_vehicle_body", d

    if step == "trade_vehicle_body":
        return go("trade_vehicle_engine",
                  vehicleBody="" if value == SKIP else value)

    if step == "trade_vehicle_engine":
        d["vehicleEngine"] = "" if value == SKIP else value
        # Жеңил автоунаада кузов менен кыймылдаткыч ансыз да
        # тактап берди — бош «Башка» экранын көрсөтпөйбүз
        if not _has_choice(VEHICLE_SUBS.get(d.get("vehicleCategory"))):
            d["subcategory"] = d.get("vehicleBody") or ""
            return _after_subcategory(d), d
        return "trade_vehicle_sub", d

    if step == "trade_group":
        return go("trade_group_sub", tradeGroup=value)

    # ── Кызмат/ижара/жумуш/жеткирүү ─────────────────────────
    if step == "category_select":
        d["category"] = value
        if at == "service" and value in SERVICE_GROUP_TABLES:
            return "svc_group", d
        # «Башка» сыяктуу категорияларда тагыраак тандоо жок —
        # бош экранды көрсөтпөй, кийинки кадамга өтөбүз
        if not _has_choice(get_subs_for_category(at, value)):
            _lb = _cat_label(value)
            d.update(subcategory="", title=_lb if _lb != value else "Башка / Другое")
            return _after_subcategory(d), d
        return "subcategory_select", d

    if step == "svc_group":
        return go("svc_group_sub", svcGroup=value)

    if step in ("subcategory_select", "svc_group_sub"):
        d.update(subcategory=value, title=value)
        return _after_subcategory(d), d

    # ── Соода аталышы (чынжыр) ──────────────────────────────
    if step == "trade_title":
        mt = d.get("marketsType")
        cat = d.get("category")

        if (at == "markets" and mt not in ("mall", "store", "livestock_market")
                and not (mt == "car_market" and (cat == "vehicles"
                                                 or str(cat).startswith("veh_")))
                and d.get("marketStall") is None):
            return go("trade_title", marketStall=value)

        if cat == "animals":
            p = _chain_pending(CHAIN_ANIMALS, d)
            if p:
                d[p[0]] = value
                if p[0] == "animalCondition":
                    d["title"] = "%s | Жашы/саны: %s | Абалы: %s" % (
                        d.get("animalBreed"), d.get("animalAgeCount"), value)
                    return "trade_price", d
                return "trade_title", d

        if cat == "vehicles" or str(cat).startswith("veh_"):   # VEH_SPLIT
            _veh_prefill(d)
            p = _chain_pending(CHAIN_VEHICLES, d)
            if p:
                if p[0] == "vehicleBrand" and value in ("__china__", "__back__"):
                    # Кытай тизмесин ачуу/жабуу — марка азырынча сакталбайт
                    if value == "__china__":
                        d["_china"] = 1
                    else:
                        d.pop("_china", None)
                    return "trade_title", d
                d.pop("_china", None)
                d[p[0]] = _unitize(p[0], value)
                if p[0] == "vehicleDrive":
                    d["vehicleTransRoul"] = ", ".join(str(d.get(k) or "") for k in (
                        "vehicleEngVol", "vehicleGearbox", "vehicleWheel", "vehicleDrive")
                        if d.get(k) and d.get(k) != "Электр")
                if p[0] == "vehicleOwners":
                    d["vehicleHistory"] = ", ".join(str(d.get(k) or "") for k in (
                        "vehicleCrash", "vehiclePaint", "vehicleOwners") if d.get(k))
                if p[0] == "vehicleCondition":
                    d["title"] = "%s %s, %s-ж., %s | %s, %s" % (
                        d.get("vehicleBrand"), d.get("vehicleModel"),
                        d.get("vehicleYear"), d.get("vehicleMileage"),
                        d.get("vehicleTransRoul"), d.get("vehicleFuel") or "")
                    return "trade_price", d
                return "trade_title", d

        if cat == "realestate" or str(cat).startswith("re_"):   # RE_SPLIT
            _rch = REALESTATE_CHAINS.get(
                d.get("realestateType") or str(cat)[3:], CHAIN_HOME)
            p = _chain_pending(_rch, d)
            if p:
                d[p[0]] = value
                if p[0] == _rch[-1][0]:
                    _ar = str(d.get(_rch[0][0]) or "").strip()
                    if _ar.replace(",", ".").replace(".", "").isdigit():
                        _ar += " м²"
                    _pt = [d.get("subcategory") or _cat_label(d.get("category")),
                           d.get("homeRooms"), _ar, d.get("homeFloor")]
                    d["title"] = " · ".join(
                        str(x).strip() for x in _pt if x and str(x).strip() != "—")
                    return "trade_price", d
                return "trade_title", d

        if at == "markets" and mt == "bazaar":
            p = _chain_pending(CHAIN_BAZAAR, d)
            if p:
                d[p[0]] = value
                if p[0] == "bazaarDelivery":
                    d["title"] = "%s | %s | Жеткирүү: %s" % (
                        d.get("subcategory") or _cat_label(d.get("category")),
                        d.get("bazaarQuality"), value)
                    d["price"] = d.get("bazaarPrice")
                    d["tradeBargain"] = ""
                    return "trade_photo", d
                return "trade_title", d

        if at in ("markets", "malls") and mt == "mall":
            p = _chain_pending(CHAIN_MALL, d)
            if p:
                d[p[0]] = value
                if p[0] == "mallHours":
                    d["title"] = "%s | %s | %s | Иш убактысы: %s" % (
                        d.get("mallBrand"), d.get("mallPromo"), d.get("mallFloor"), value)
                    return "trade_price", d
                return "trade_title", d

        if at in ("markets", "malls") and mt == "store":
            p = _chain_pending(CHAIN_STORE, d)
            if p:
                d[p[0]] = value
                if p[0] == "storeDelivery":
                    d["title"] = "%s | %s | Иш убактысы: %s | Жеткирүү: %s" % (
                        d.get("storeDirection"), d.get("storeAddress"),
                        d.get("storeHours"), value)
                    return "trade_price", d
                return "trade_title", d

        if (at == "trade" and not str(cat).startswith(("re_", "veh_"))
                and cat not in ("vehicles", "animals", "realestate",
                                "agro_machinery")):
            if d.get("tradeDelivery") is None:
                d["tradeDelivery"] = value
                d["title"] = "%s | Жеткирүү: %s" % (
                    d.get("subcategory") or _cat_label(d.get("category")), value)
                return "trade_price", d

        return go("trade_price", title=value)

    if step == "trade_price":
        if value == "__custom__":
            return go("trade_price_custom")
        return go("trade_photo", price=value, tradeBargain="")

    if step == "trade_price_custom":
        if any(d.get(k) for k in ("vehicleBargain", "homeBargain", "landBargain",
                                  "comBargain", "garBargain")):   # HELP_CHIPS
            return go("trade_photo", price=value, tradeBargain="")
        return go("trade_bargain", price=value)

    if step == "trade_bargain":
        return go("trade_photo",
                  tradeBargain="Соодалашса болот" if value == "yes" else "Баа катуу")

    if step == "trade_photo":
        return go("post_name", photos=value)

    # ── Жалпы куйрук ────────────────────────────────────────
    if step == "post_name":
        if at == "rental":
            p = _chain_pending(CHAIN_RENTAL, d)
            if p:
                d[p[0]] = value
                if p[0] == "rentalDeposit":
                    d["title"] = "%s | %s | %s | Депозит: %s" % (
                        d.get("title"), d.get("rentalPeriod"), d.get("rentalCharacteristics"), value)
                return "post_name", d
        if at == "job":
            p = _chain_pending(CHAIN_JOB, d)
            if p:
                d[p[0]] = value
                if p[0] == "jobConditions":
                    d["title"] = "%s | Милдеттери: %s | Талаптар: %s | Шарттары: %s" % (
                        d.get("title"), d.get("jobDuties"), d.get("jobRequirements"), value)
                return "post_name", d
        for _at, _chain, _last in (("wholesale", CHAIN_WHOLESALE, "wsDelivery"),
                                   ("cargo", CHAIN_CARGO, "cargoBody"),
                                   ("jobseek", CHAIN_JOBSEEK, "seekEdu")):
            if at == _at:
                p = _chain_pending(_chain, d)
                if p:
                    if p[0] == "wsMinOrder" and d.get("wsUnit"):   # WS_UNITS
                        _v = str(value).strip()
                        if _v.replace(",", "").replace(".", "").replace(" ", "").isdigit():
                            value = "%s %s" % (_v, d["wsUnit"])
                    value = _unitize(p[0], value)
                    d[p[0]] = value
                    if p[0] == _last:
                        d["title"] = " | ".join(
                            [str(d.get(it[0]) or "") for it in _chain[:-1] if it[0] != "wsUnit"]
                            + [str(value)])
                        base = d.get("subcategory") or _cat_label(d.get("category"))
                        if base == d.get("category"):
                            base = "Башка / Другое"
                        d["title"] = f"{base} | {d['title']}"
                    return "post_name", d
        d["personName"] = value
        # Соода менен базар жолунда баа мурунтан суралып койгон
        # (trade_price). Кайра сурабай, түз чалуу убактысына өтөбүз.
        return ("post_calltime" if d.get("price") is not None else "post_price"), d

    if step == "post_price":
        if value == "__custom__":
            return go("post_price_custom")
        return go("post_calltime", price=value)

    if step == "post_price_custom":
        return go("post_calltime", price=value)

    if step == "post_calltime":
        if value == "__custom_time__":
            return go("post_calltime_custom")
        return go("post_whatsapp", callTime=value)

    if step == "post_calltime_custom":
        return go("post_whatsapp", callTime=value)

    if step == "post_whatsapp":
        ph = norm_phone(value)
        if not ph:
            d["phoneErr"] = True
            return "post_whatsapp", d
        d.pop("phoneErr", None)
        return go("post_duration", phone=ph)

    if step == "post_duration":
        return go("post_comment", duration=value)

    if step == "post_comment":
        d["postComment"] = value
        return ("post_photo" if at in PHOTO_TYPES else "post_preview"), d

    if step == "post_photo":
        return go("post_preview", photos=value)

    if step == "post_preview":
        return (("post_done", d) if value == "confirm" else ("main_menu", {}))

    if step == "post_done":
        return "main_menu", {}

    # ── Издөө ───────────────────────────────────────────────
    if step == "search_method_choice":
        if value == "keyword":
            return go("search_keyword_input")
        return (("trade_category" if at in ("trade", "property", "vehicle")
                 else "category_select"), d)

    if step == "search_keyword_input":
        return go("search_results", keyword=value)

    if step == "search_results":
        return "main_menu", {}

    # ── Такси ───────────────────────────────────────────────
    # ── Такси ───────────────────────────────────────────────

    if step == "taxi_role":
        return go("taxi_mode", taxiRole=value)

    if step == "taxi_mode":
        d["taxiMode"] = value
        if value in ("air_manas", "air_osh"):   # TAXI_AIR_BOT
            return "taxi_air_dir", d
        return ("taxi_lo_oblast" if value == "local" else "taxi_dir"), d

    if step == "taxi_air_dir":   # TAXI_AIR_BOT
        ap = ("Манас" if d.get("taxiMode") == "air_manas" else "Ош") + " аэропорту"
        d["taxiAirDir"] = value
        if value == "to_air":
            d["taxiTo"] = ap
            d.pop("taxiFrom", None)
        else:
            d["taxiFrom"] = ap
            d.pop("taxiTo", None)
        return "taxi_air_oblast", d

    if step == "taxi_air_oblast":
        return go("taxi_air_place", taxiAirOblast=value,
                  taxiLoOblast=value, taxiRegion=value)

    if step == "taxi_air_place":
        if d.get("taxiAirDir") == "to_air":
            d["taxiFrom"] = value
        else:
            d["taxiTo"] = value
        return _taxi_first_step(d), d

    if step == "taxi_dir":
        d["taxiDir"] = value
        if value == "to_bishkek":
            d["taxiTo"] = "Бишкек"
        else:
            d["taxiFrom"] = "Бишкек"
        return "taxi_region", d

    if step == "taxi_region":
        return go("taxi_city", taxiRegion=value)

    if step == "taxi_city":
        if d.get("taxiDir") == "to_bishkek":
            d["taxiFrom"] = value
        else:
            d["taxiTo"] = value
        return _taxi_first_step(d), d

    if step == "taxi_lo_oblast":
        return go("taxi_lo_from", taxiLoOblast=value)

    if step == "taxi_lo_from":
        return go("taxi_lo_to_oblast", taxiFrom=value)

    if step == "taxi_lo_to_oblast":
        return go("taxi_lo_to", taxiLoToOblast=value)

    if step == "taxi_lo_to":
        d["taxiTo"] = value
        return _taxi_first_step(d), d

    # Суроолор: ар бир жооптон кийин тизмедеги кийинкисине

    if step == "taxi_name":
        d["taxiName"] = value
        return _taxi_next(d, "name"), d

    if step == "taxi_car":
        d["taxiCar"] = value
        return _taxi_next(d, "car"), d

    if step == "taxi_date":
        d["taxiDate"] = date_label(1 if value == "d1" else 0)
        return _taxi_next(d, "date"), d

    if step == "taxi_time":
        d["taxiTime"] = ("Орун толгондо жолго чыгам" if value == "__full__"
                         else "Саат %sдө жолго чыгам" % value)
        return _taxi_next(d, "time"), d

    if step == "taxi_seats":
        d["taxiSeats"] = value
        return _taxi_next(d, "seats"), d

    if step == "taxi_people":
        d["taxiPeople"] = value
        return _taxi_next(d, "people"), d

    if step == "taxi_baggage":
        d["taxiBaggage"] = "Жок" if value == "__no__" else value
        return _taxi_next(d, "baggage"), d

    if step == "taxi_price":
        d["taxiPrice"] = "Келишим" if value == "__deal__" else value
        return _taxi_next(d, "price"), d

    if step == "taxi_comment":
        d["taxiComment"] = value
        return _taxi_next(d, "comment"), d

    if step == "taxi_phone":
        d["taxiPhone"] = value
        return _taxi_next(d, "phone"), d

    if step == "taxi_safety":
        return ("taxi_preview", d) if value == "confirm" else ("main_menu", {})

    if step == "taxi_preview":
        return ("post_done", d) if value == "confirm" else ("main_menu", {})

    if step == "my_posts_phone":
        return go("my_posts", phone=value)

    if step == "my_posts":
        return "main_menu", {}

    return "main_menu", {}
