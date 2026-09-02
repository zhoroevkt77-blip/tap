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

from taxi_geo import (REGIONS as TX_REGIONS, REGION_LIST as TX_REGION_LIST,
                      DISTRICTS as TX_DISTRICTS,
                      DISTRICT_OBLASTS as TX_OBLASTS,
                      steps_of, day_hours, date_label)
from tap_catalog import (
    GREETING, MAIN_OPTIONS, OBLASTS, STANDALONE, GEO,
    TRADE_CATEGORIES, HEATING_FUEL_SUBS, TRADE_PRICE_PRESETS, TRADE_CONDITION,
    DEMOGRAPHICS, SEASONS, REALESTATE_TYPES, REALESTATE_SUBS,
    VEHICLE_BODY_TYPES, VEHICLE_ENGINE_TYPES, VEHICLE_CATEGORIES, VEHICLE_SUBS,
    MARKETS_TYPES, MARKETS_GROUPS, MARKETS_SUBS_BY_TYPE,
    RENTAL_CATEGORIES, SERVICE_CATEGORIES, JOB_CATEGORIES, DELIVERY_CATEGORIES,
    DURATION_PLANS, SERVICE_PRICE_PRESETS, JOB_SALARY_PRESETS, CALL_TIME_PRESETS,
    GROUP_TABLES, SERVICE_GROUP_TABLES,
    get_districts, get_localities, get_villages,
    get_categories, get_subs_for_category,
    get_clothing_subs, get_footwear_subs, ru_name,
)
from strings import H as _help_text

START_STEP = "language_select"


# Башкы менюга кошумча эки баскыч. tap_catalog.MAIN_OPTIONS'ко
# тийбей, ушул жерден кошулат — ошондуктан каталог өзгөрбөйт.
MENU_EXTRA = [
    {"label": "🌐 Биздин сайт / Наш сайт", "value": "tap_site"},
    {"label": "🆘 Жардам / Помощь",        "value": "tap_help"},
    # Тил баскычы атайын эки тилде: кайсы тилде турса да табылсын.
    # Ичинде « / » бөлгүчү жок, ошондуктан которулбайт.
    {"label": "🌐 Тил/Язык",               "value": "tap_lang"},
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


# ─────────────────────────────────────────────────────────────
#  Кичине жардамчылар
# ─────────────────────────────────────────────────────────────

def _opts(pairs):
    """[(label, value)] -> опциялар тизмеси."""
    return [{"label": l, "value": v} for l, v in pairs]


def _from_list(items):
    """Жөнөкөй сап тизмесин опцияга айлантуу. Бош болсо — "Башка"."""
    items = list(items or [])
    if not items:
        items = [OTHER]
    return [{"label": s, "value": s} for s in items]


def _from_groups(groups):
    """[{id,label,emoji?}] -> опциялар."""
    out = []
    for g in groups:
        label = g.get("label", g["id"])
        if g.get("emoji"):
            label = "%s %s" % (g["emoji"], label)
        out.append({"label": label, "value": g["id"]})
    return out


def _regions():
    return [{"label": "%s / %s" % (o, ru_name(o)), "value": o} for o in OBLASTS]


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
          photo=False, final=False, localized=False):
    return {
        "text": text,
        "options": options or [],
        "input": input,
        "placeholder": placeholder,
        "multi": multi,
        "photo": photo,
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

CHAIN_VEHICLES = [
    ("vehicleBrand", "🚘 Маркасы жана үлгүсү (модели)? / Марка и модель?",
     "Мис: Honda CR-V / Например: Honda CR-V"),
    ("vehicleYear", "📅 Чыккан жылы? / Год выпуска?",
     "Мис: 2015-жылкы / Например: 2015 года"),
    ("vehicleTransRoul", "🕹 Кыймылдаткычтын көлөмү, коробкасы жана руулу? / Объём двигателя, коробка и руль?",
     "Мис: 2.0, автомат, оң рул / Например: 2.0, автомат, правый руль"),
    ("vehicleCondition", "🛠 Абалы, документтери жана кошумча маалымат? / Состояние, документы и доп. информация?",
     "Мис: Мотор/коробка идеалдуу, ОСАГО бар / Например: Мотор и коробка идеальные"),
]

CHAIN_BAZAAR = [
    ("bazaarQuality", "🏭 Товардын сапаты/өндүрүлгөн жери кайсы? / Качество товара и место производства?",
     "Мис: Түркиядан келген, фабрикалык / Например: Из Турции, фабричный"),
    ("bazaarPrice", "💰 Баасы кандай (чекене жана дүң)? / Цена (розница и опт)?",
     "Мис: Чекене 1500 сом, дүң 900 сом / Например: Розница 1500, опт 900"),
    ("bazaarDelivery", "🚚 Башка облустарга/өлкөлөргө жеткирүү (карго) барбы? / Есть ли доставка (карго)?",
     "Мис: Бардык облустарга карго менен / Например: Во все области через карго"),
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
    ("rentalCharacteristics", "🛋️ Негизги мүнөздөмөлөрү жана шарттары кандай? / Основные характеристики и условия?",
     "Мис: 2 бөлмө, 4-кабат, эмерекдүү / Например: 2 комнаты, 4 этаж, с мебелью"),
    ("rentalDeposit", "💰 Депозит (залог) барбы? Канча? / Есть ли депозит? Сколько?",
     "Мис: 1 айлык депозит милдеттүү / Например: Депозит за 1 месяц"),
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
CHAIN_WHOLESALE = [
    ("wsMinOrder", "📦 Эң аз буйрутма канча? / Минимальный заказ?",
     "Мис: 1 тонна / Например: 1 тонна"),
    ("wsUnit", "⚖️ Өлчөө бирдиги кандай? / Единица измерения?",
     "Мис: кг, тонна, даана, капка / Например: кг, тонна, штука, мешок"),
    ("wsDelivery", "🚚 Жеткирүү барбы? / Есть ли доставка?",
     "Мис: Өзү алып кетет / Например: Самовывоз"),
]

# Жүк ташуу: багыт, көтөрүмү, кузов
CHAIN_CARGO = [
    ("cargoRoute", "🗺️ Багыт кайсы? / Маршрут?",
     "Мис: Шаар ичинде / Например: По городу"),
    ("cargoCapacity", "🏋️ Жүк көтөрүмү канча? / Грузоподъёмность?",
     "Мис: 3 тонна / Например: 3 тонны"),
    ("cargoBody", "🚚 Кузовдун түрү кандай? / Тип кузова?",
     "Мис: Тент / Например: Тент"),
]

# Жумуш издөө: стажы, графиги, билими
CHAIN_JOBSEEK = [
    ("seekExp", "🧰 Стажыңыз канча? / Ваш опыт работы?",
     "Мис: 3 жыл / Например: 3 года"),
    ("seekSchedule", "🕒 Кандай график ыңгайлуу? / Какой график удобен?",
     "Мис: Толук күн / Например: Полный день"),
    ("seekEdu", "🎓 Билимиңиз кандай? / Ваше образование?",
     "Мис: Жогорку / Например: Высшее"),
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

COMMENT_PROMPTS = {
    "trade":    "📝 Сатып жаткан товарларыңыз жөнүндө кыскача жазыңыз! / Напишите кратко о продаваемых товарах!",
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


def _chain_pending(chain, data):
    """Чынжырда жооп берилбеген биринчи суроону кайтарат."""
    for field, text, ph in chain:
        if data.get(field) is None:
            return field, text, ph
    return None


# ─────────────────────────────────────────────────────────────
#  RENDER — кадамды көрсөтүү
# ─────────────────────────────────────────────────────────────

def render(step, data=None):
    d = data or {}
    at = d.get("adType")
    act = d.get("action")

    # ── Башталышы ───────────────────────────────────────────
    if step == "language_select":
        return _view("Колдонуу тилин тандаңыз / Выберите язык использования",
                     _opts([("🇰🇬 Кыргызча", "ky"), ("🇷🇺 Орусча / Русский", "ru")]))

    if step == "main_menu":
        return _view(GREETING + "\n\nЭмне кыласыз? / Что делаете? 👇",
                     _main_options())

    # ── Биздин сайт жана Жардам ─────────────────────────────
    if step == "site_info":
        return _view(_help_text("site", _ui_lang(d)),
                     _opts([(_hb("home", d), "home")]), localized=True)

    if step == "help_menu":
        return _view(_help_text("head", _ui_lang(d)),
                     _opts([(_hb("guide", d), "guide"),
                            (_hb("faq", d), "faq"),
                            (_hb("home", d), "home")]), localized=True)

    if step in ("help_guide", "help_faq"):
        key = "guide" if step == "help_guide" else "faq"
        return _view(_help_text(key, _ui_lang(d)),
                     _opts([(_hb("back", d), "back"),
                            (_hb("home", d), "home")]), localized=True)

    if step == "type_select":
        head = WARNING_TEXT + "\n\n" if act == "post" else ""
        q = ("Кандай жарыя бергиңиз келет? / Какую рекламу хотите разместить?"
             if act == "post" else "Эмнени издеп жатасыз? / Что ищете?")
        return _view(head + q, _opts([
            ("🛍 Соода-сатык / Торговля", "trade"),
            ("🛠 Кызмат көрсөтүү / Услуги", "service"),
            ("🔑 Ижарага берүү / Аренда", "rental"),
            ("📦 Жеткирүү кызматы / Доставка", "delivery"),
            ("💼 Жумуш берүү / Работа", "job"),
            ("🙋 Жумуш издөө / Поиск работы", "jobseek"),
            ("🏭 Соода-сатык (дүң) / Оптовая торговля", "wholesale"),
            ("🚛 Жүк ташуу / Грузоперевозки", "cargo"),
            ("🏬 Базарлар, соода борборлор жана ири соода дүкөндөр / Рынки, ТЦ и крупные магазины", "markets"),
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
        multi = _is_city(ob)
        text = ("Бир же бир нече районду тандаңыз / Выберите один или несколько районов:"
                if multi else "%s — район же шаарды тандаңыз / Выберите район или город:" % ob)
        return _view(text,
                     [{"label": "%s / %s" % (x, ru_name(x)), "value": x} for x in get_districts(ob)],
                     multi=multi)

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
                            ("🏘 Айыл аймактын бирин тандоо / Выбрать аильный округ", "locality")]))

    if step == "locality_select":
        ob = d.get("oblast", "")
        text = ("Бир же бир нече кичи районду/МАБды/конушту тандаңыз / Выберите микрорайон(ы):"
                if _is_city(ob)
                else "Бир же бир нече айыл аймак тандаңыз / Выберите аильный округ(а):")
        return _view(text, _from_list(get_localities(ob, d.get("district"))), multi=True)

    if step == "locality_scope_select":
        verb = "жарыя бересизби" if act == "post" else "издейсизби"
        return _view("%s боюнча %s (бүт айыл аймак)? / По всему аильному округу?" % (d.get("locality", ""), verb),
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
                      for t in MARKETS_TYPES])

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
        q = ("Кандай товар сатасыз? / Что продаёте?" if act == "post"
             else "Кандай товар издеп жатасыз? / Какой товар ищете?")
        excluded = ["realestate", "vehicles", "agro_machinery"]
        mt = d.get("marketsType")
        if at == "markets" and mt == "car_market":
            cats = [c for c in TRADE_CATEGORIES if c["id"] in ("vehicles", "auto_parts")]
        elif at == "markets" and mt == "livestock_market":
            cats = [c for c in TRADE_CATEGORIES if c["id"] == "animals"]
        elif at == "markets":
            cats = [c for c in TRADE_CATEGORIES if c["id"] not in excluded]
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
        return _view("Кузовдун түрү? / Тип кузова?", _from_list(VEHICLE_BODY_TYPES))

    if step == "trade_vehicle_engine":
        return _view("Кыймылдаткычы? / Двигатель?", _from_list(VEHICLE_ENGINE_TYPES))

    if step == "trade_vehicle_sub":
        return _view("Тагыраак тандаңыз / Уточните:",
                     _from_list(VEHICLE_SUBS.get(d.get("vehicleCategory"), [OTHER])), multi=True)

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
                and not (mt == "car_market" and cat == "vehicles")
                and d.get("marketStall") is None):
            return _view("Кайсы катар/өтмөк жана соода орду? / Ряд/проход и торговое место:",
                         input=True, placeholder="Мис: 3-катар, 45-орун / Например: 3-й ряд, место 45")

        if cat == "animals":
            p = _chain_pending(CHAIN_ANIMALS, d)
            if p:
                return _view(p[1], input=True, placeholder=p[2])

        if cat == "vehicles":
            p = _chain_pending(CHAIN_VEHICLES, d)
            if p:
                return _view(p[1], input=True, placeholder=p[2])

        if at == "markets" and mt == "bazaar":
            p = _chain_pending(CHAIN_BAZAAR, d)
            if p:
                return _view(p[1], input=True, placeholder=p[2])

        if at == "markets" and mt == "mall":
            p = _chain_pending(CHAIN_MALL, d)
            if p:
                return _view(p[1], input=True, placeholder=p[2])

        if at == "markets" and mt == "store":
            p = _chain_pending(CHAIN_STORE, d)
            if p:
                return _view(p[1], input=True, placeholder=p[2])

        if at == "trade" and cat not in ("vehicles", "animals", "realestate", "agro_machinery"):
            if d.get("tradeWholesale") is None:
                return _view("🤝 Чекене, дүң же экөөнү тең сатасызбы? / Продаёте в розницу, оптом или и то и другое?",
                             TRADE_WHOLESALE_OPTS)
            if d.get("tradeDelivery") is None:
                return _view(CHAIN_TRADE_TAIL_TEXT[0], input=True, placeholder=CHAIN_TRADE_TAIL_TEXT[1])

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
                     photo=True)

    # ── Жалпы куйрук ────────────────────────────────────────
    if step == "post_name":
        if at == "rental":
            p = _chain_pending(CHAIN_RENTAL, d)
            if p:
                return _view(p[1], input=True, placeholder=p[2])
        if at == "job":
            p = _chain_pending(CHAIN_JOB, d)
            if p:
                return _view(p[1], input=True, placeholder=p[2])
        for _at, _chain in (("wholesale", CHAIN_WHOLESALE),
                            ("cargo", CHAIN_CARGO),
                            ("jobseek", CHAIN_JOBSEEK)):
            if at == _at:
                p = _chain_pending(_chain, d)
                if p:
                    return _view(p[1], input=True, placeholder=p[2])
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
        return _view("Айлыкты жазыңыз / Введите зарплату:" if at == "job"
                     else "Баасын жазыңыз / Введите цену:",
                     input=True, placeholder="Мис: 25 000 сом" if at == "job" else "Мис: 1 500 сом")

    if step == "post_calltime":
        return _view("📞 Сизге качан чалса болот? / Когда вам можно звонить?",
                     [{"label": p["label"], "value": p["value"]} for p in CALL_TIME_PRESETS])

    if step == "post_calltime_custom":
        return _view("Ыңгайлуу убактыңызды жазыңыз / Введите удобное время:",
                     input=True, placeholder="Мис: 09:00–18:00")

    if step == "post_whatsapp":
        return _view("📱 WhatsApp номериңизди жазыңыз / Введите номер WhatsApp:\n"
                     "(+996 автоматтык түрдө коюлат / +996 добавляется автоматически)",
                     input=True, placeholder="700 000 000")

    if step == "post_duration":
        return _view("⏳ Жарыя канча күн жарыяланат? / На сколько дней разместить рекламу?",
                     [{"label": p["label"], "value": p["value"]} for p in DURATION_PLANS])

    if step == "post_comment":
        base = COMMENT_PROMPTS.get(at, "📝 Комментарий жазыңыз / Напишите комментарий")
        return _view(base + "\n(болбосо — сызыкча коюңуз / если нет — поставьте прочерк):",
                     input=True, placeholder="Мис: Тез жана сапаттуу / Например: Быстро и качественно")

    if step == "post_preview":
        return _view("Жарыяңыз даяр! Жарыялайлыбы? / Ваше объявление готово! Публикуем?",
                     _opts([("✅ Ооба, жарыялоо / Да, опубликовать", "confirm"),
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
                            ("Район/шаар аралык", "local")]))

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
                     _opts([("✅ Ооба, жарыялоо / Да, опубликовать", "confirm"),
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
        return "trade_category" if d.get("adType") == "trade" else "category_select"
    if d.get("searchByRegion"):
        return "search_results"
    return "search_method_choice"


def _after_subcategory(d):
    """Подкатегория тандалгандан кийин кайда барабыз."""
    if d.get("action") == "post":
        return "trade_title" if d.get("adType") in ("trade", "markets") else "post_name"
    return "search_results"


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
        return "trade_title" if d.get("adType") in ("trade", "markets") else "post_name"
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
            return go("my_posts_phone")
        return go("type_select", action=value)

    # ── Биздин сайт жана Жардам ─────────────────────────────
    if step == "site_info":
        return go("main_menu")

    if step == "help_menu":
        if value == "guide":
            return go("help_guide")
        if value == "faq":
            return go("help_faq")
        return go("main_menu")

    if step in ("help_guide", "help_faq"):
        return go("help_menu") if value == "back" else go("main_menu")

    if step == "type_select":
        if value == "taxi":
            return go("taxi_role", adType="taxi")
        if value == "markets":
            return go("markets_type", adType="markets")
        return go("oblast_select", adType=value)

    # ── Аймак ───────────────────────────────────────────────
    if step == "oblast_select":
        d["oblast"] = value
        return ("city_scope_select" if _is_city(value) else "district_select"), d

    if step == "city_scope_select":
        if value == "city":
            d.update(district=None, locality=None)
            return _after_region(d), d
        return go("district_select")

    if step == "district_select":
        d["district"] = value
        if _is_city(d.get("oblast")):
            if "," in value:
                d["locality"] = None
                return _after_region(d), d
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
        if value in ("clothing", "footwear"):
            return "trade_demographic", d
        if value == "heating_fuel":
            return "trade_heating_fuel_select", d
        if value == "realestate":
            return "trade_realestate_type", d
        if value == "vehicles":
            return "trade_vehicle_category", d
        if value in GROUP_TABLES:
            return "trade_group", d
        return _after_subcategory(d), d

    if step == "trade_demographic":
        return go("trade_season", demographic=value)

    if step == "trade_season":
        return go("trade_item_type", season=value)

    if step in ("trade_item_type", "trade_heating_fuel_select",
                "trade_realestate_sub", "trade_vehicle_sub", "trade_group_sub"):
        d["subcategory"] = value
        return _after_subcategory(d), d

    if step == "trade_realestate_type":
        return go("trade_realestate_sub", realestateType=value)

    if step == "trade_vehicle_category":
        return go("trade_vehicle_body", vehicleCategory=value)

    if step == "trade_vehicle_body":
        return go("trade_vehicle_engine", vehicleBody=value)

    if step == "trade_vehicle_engine":
        return go("trade_vehicle_sub", vehicleEngine=value)

    if step == "trade_group":
        return go("trade_group_sub", tradeGroup=value)

    # ── Кызмат/ижара/жумуш/жеткирүү ─────────────────────────
    if step == "category_select":
        d["category"] = value
        if at == "service" and value in SERVICE_GROUP_TABLES:
            return "svc_group", d
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
                and not (mt == "car_market" and cat == "vehicles")
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

        if cat == "vehicles":
            p = _chain_pending(CHAIN_VEHICLES, d)
            if p:
                d[p[0]] = value
                if p[0] == "vehicleCondition":
                    d["title"] = "%s, %s-ж. | %s | %s" % (
                        d.get("vehicleBrand"), d.get("vehicleYear"),
                        d.get("vehicleTransRoul"), value)
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

        if at == "markets" and mt == "mall":
            p = _chain_pending(CHAIN_MALL, d)
            if p:
                d[p[0]] = value
                if p[0] == "mallHours":
                    d["title"] = "%s | %s | %s | Иш убактысы: %s" % (
                        d.get("mallBrand"), d.get("mallPromo"), d.get("mallFloor"), value)
                    return "trade_price", d
                return "trade_title", d

        if at == "markets" and mt == "store":
            p = _chain_pending(CHAIN_STORE, d)
            if p:
                d[p[0]] = value
                if p[0] == "storeDelivery":
                    d["title"] = "%s | %s | Иш убактысы: %s | Жеткирүү: %s" % (
                        d.get("storeDirection"), d.get("storeAddress"),
                        d.get("storeHours"), value)
                    return "trade_price", d
                return "trade_title", d

        if at == "trade" and cat not in ("vehicles", "animals", "realestate", "agro_machinery"):
            if d.get("tradeWholesale") is None:
                return go("trade_title", tradeWholesale=value)
            if d.get("tradeDelivery") is None:
                d["tradeDelivery"] = value
                d["title"] = "%s | %s | Жеткирүү: %s" % (
                    d.get("subcategory") or _cat_label(d.get("category")), d.get("tradeWholesale"), value)
                return "trade_price", d

        return go("trade_price", title=value)

    if step == "trade_price":
        if value == "__custom__":
            return go("trade_price_custom")
        return go("trade_photo", price=value, tradeBargain="")

    if step == "trade_price_custom":
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
                    d["title"] = "%s | %s | Депозит: %s" % (
                        d.get("title"), d.get("rentalCharacteristics"), value)
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
                    d[p[0]] = value
                    if p[0] == _last:
                        d["title"] = " | ".join(
                            [str(d.get(k) or "") for k, _q, _ph in _chain[:-1]]
                            + [str(value)])
                        base = d.get("subcategory") or _cat_label(d.get("category"))
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
        return go("post_duration", phone=value)

    if step == "post_duration":
        return go("post_comment", duration=value)

    if step == "post_comment":
        return go("post_preview", postComment=value)

    if step == "post_preview":
        return (("post_done", d) if value == "confirm" else ("main_menu", {}))

    if step == "post_done":
        return "main_menu", {}

    # ── Издөө ───────────────────────────────────────────────
    if step == "search_method_choice":
        if value == "keyword":
            return go("search_keyword_input")
        return ("trade_category" if at == "trade" else "category_select"), d

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
        return ("taxi_lo_oblast" if value == "local" else "taxi_dir"), d

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
