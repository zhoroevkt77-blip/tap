# -*- coding: utf-8 -*-
"""
ТАП! — башкы беттин бөлүм такталары.

Ар бир бөлүм кичинекей белги эмес, толук көрүнүш: соода текчеси,
куралдар, ачкыч менен кулпу, посылка, портфель, дүкөндүн фасады, такси.
Астында ачык тилкеде аталышы турат.

Неге сүрөт эмес, SVG:
  • жети сүрөт 4G'де жүктөлүшү керек, SVG болсо бет менен кошо келет;
  • каалаган экранда даана — кичине телефондо да, чоңунда да;
  • түсүн бир жерден өзгөртсө, жетөө тең өзгөрөт.

Ар бир көрүнүш 100×100 квадратта тартылат.
"""

# Түстөр — беттин жалпы палитрасынан
SKY = "#EAF0EC"      # фон
SKY2 = "#DCE6DF"
WOOD = "#8C6440"
WOOD_D = "#6B4A2E"
WOOD_L = "#A57B52"
GREEN = "#2F7C4E"
GREEN_D = "#1F5C39"
GREEN_L = "#5AA678"
STEEL = "#B9C4BD"
STEEL_D = "#7E8D84"
STEEL_L = "#D8E0DA"
GOLD = "#E8A33D"
GOLD_D = "#C4831F"
RED = "#D45B4A"
CREAM = "#F6F1E6"
DARK = "#2B3A31"


def _svg(body, extra=""):
    return ('<svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid slice" '
            'aria-hidden="true">'
            '<defs>'
            f'<linearGradient id="bg{extra}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{SKY}"/>'
            f'<stop offset="1" stop-color="{SKY2}"/></linearGradient>'
            '</defs>'
            f'<rect width="100" height="100" fill="url(#bg{extra})"/>'
            + body + '</svg>')


# ── 1. Соода-сатык — базардагы текче ─────────────────────────
TRADE = _svg(
    # чатыр
    f'<path d="M14 30h72l-4-9a4 4 0 0 0-3.7-2.5H21.7A4 4 0 0 0 18 21l-4 9Z" fill="{GREEN_D}"/>'
    f'<path d="M22 18.5h11l-3 11.5H19l3-11.5Zm22 0h11l-1 11.5H43l1-11.5Zm22 0h11l3 11.5H67l-1-11.5Z" '
    f'fill="{CREAM}" opacity=".9"/>'
    # мамылар
    f'<rect x="17" y="30" width="4" height="46" fill="{WOOD_D}"/>'
    f'<rect x="79" y="30" width="4" height="46" fill="{WOOD_D}"/>'
    # текче
    f'<rect x="14" y="56" width="72" height="6" rx="1.5" fill="{WOOD_L}"/>'
    f'<rect x="18" y="62" width="64" height="16" rx="2" fill="{WOOD}"/>'
    f'<rect x="18" y="62" width="64" height="4" fill="{WOOD_D}" opacity=".45"/>'
    # себет
    f'<path d="M30 46h18l-2.5 10H32.5L30 46Z" fill="{WOOD_L}"/>'
    f'<path d="M30 46h18l-.6 2.4H30.6L30 46Z" fill="{WOOD_D}" opacity=".5"/>'
    f'<circle cx="35" cy="44" r="4" fill="{RED}"/>'
    f'<circle cx="42" cy="43" r="4.4" fill="#E0705E"/>'
    f'<circle cx="45" cy="45.5" r="3.4" fill="{RED}"/>'
    f'<path d="M42 38.6c1.4-1 3-.8 3.6.4-1.4.5-2.8.3-3.6-.4Z" fill="{GREEN_L}"/>'
    # бал банка
    f'<rect x="57" y="42" width="11" height="14" rx="2.4" fill="{GOLD}"/>'
    f'<rect x="57" y="42" width="4" height="14" fill="#F2BC63" opacity=".7"/>'
    f'<rect x="55.6" y="39.6" width="13.8" height="3.6" rx="1.6" fill="{GOLD_D}"/>'
)

# ── 2. Кызмат көрсөтүү — куралдар ────────────────────────────
SERVICE = _svg(
    # бурагыч (артында)
    '<g transform="rotate(34 62 52)">'
    f'<rect x="56" y="22" width="14" height="26" rx="6" fill="{RED}"/>'
    f'<rect x="56" y="22" width="5" height="26" rx="2.5" fill="#E2796A"/>'
    f'<rect x="60.5" y="46" width="5" height="8" fill="{STEEL_D}"/>'
    f'<rect x="60.6" y="53" width="4.8" height="22" fill="{STEEL}"/>'
    f'<path d="M59.6 75h6.8v5h-6.8z" fill="{STEEL_D}"/>'
    '</g>'
    # гайка ачкычы (алдында)
    '<g transform="rotate(-24 44 50)">'
    # ачык ооз
    f'<path d="M32 18h7.5v7h9v-7H56v13a12 12 0 0 1-24 0V18Z" fill="{STEEL}"/>'
    f'<path d="M32 18h7.5v7h4.5V18H32Z" fill="{STEEL_L}"/>'
    # сап
    f'<rect x="38.5" y="40" width="11" height="30" fill="{STEEL}"/>'
    f'<rect x="38.5" y="40" width="3.8" height="30" fill="{STEEL_L}"/>'
    # тегерек башы
    f'<circle cx="44" cy="76" r="11" fill="{STEEL}"/>'
    f'<circle cx="44" cy="76" r="5" fill="{SKY2}"/>'
    '</g>'
)

# ── 3. Ижарага берүү — ачкыч менен кулпу ─────────────────────
RENTAL = _svg(
    # кулпу
    f'<path d="M36 46v-7a11 11 0 0 1 22 0v7" stroke="{STEEL_D}" stroke-width="6" fill="none"/>'
    f'<rect x="27" y="45" width="40" height="33" rx="6" fill="{GOLD}"/>'
    f'<rect x="27" y="45" width="13" height="33" rx="6" fill="#F2BC63" opacity=".55"/>'
    f'<circle cx="47" cy="59" r="5" fill="{GOLD_D}"/>'
    f'<rect x="45" y="59" width="4" height="9" rx="2" fill="{GOLD_D}"/>'
    # ачкыч
    f'<g transform="rotate(38 74 40)">'
    f'<circle cx="74" cy="26" r="10" fill="none" stroke="{STEEL}" stroke-width="5.5"/>'
    f'<circle cx="74" cy="26" r="3.6" fill="{SKY}"/>'
    f'<rect x="71.4" y="34" width="5.2" height="30" fill="{STEEL}"/>'
    f'<rect x="76.6" y="50" width="8" height="4.6" rx="1.4" fill="{STEEL}"/>'
    f'<rect x="76.6" y="58" width="6" height="4.6" rx="1.4" fill="{STEEL}"/>'
    '</g>'
)

# ── 4. Жеткирүү — посылка ────────────────────────────────────
DELIVERY = _svg(
    # көлөкө
    f'<ellipse cx="50" cy="84" rx="30" ry="4.5" fill="{DARK}" opacity=".12"/>'
    # кичине кутуча — тереңдик берет
    f'<path d="M66 52l16 6.5v14l-16 6.5-16-6.5v-14L66 52Z" fill="{WOOD_L}"/>'
    f'<path d="M66 58.5v21l16-6.5v-14l-16 6.5Z" fill="{WOOD_D}"/>'
    f'<path d="M50 58.5 66 52l16 6.5-16 6.5-16-6.5Z" fill="#C79A6E"/>'
    # негизги куту
    f'<path d="M18 40 48 27l30 13v28a3 3 0 0 1-1.9 2.8L49 81a4 4 0 0 1-2 0l-27.1-10.2A3 3 0 0 1 18 68V40Z" '
    f'fill="{WOOD_L}"/>'
    f'<path d="M48 46 18 40v28a3 3 0 0 0 1.9 2.8L47 81a4 4 0 0 0 1 .2V46Z" fill="{WOOD}"/>'
    f'<path d="M48 46v35.2a4 4 0 0 0 1-.2l27.1-10.2A3 3 0 0 0 78 68V40L48 46Z" fill="{WOOD_D}"/>'
    f'<path d="M18 40 48 27l30 13-30 6-30-6Z" fill="#C79A6E"/>'
    # скотч
    f'<path d="M42 29.4 72 42.4l-6 1.2-30-13 6-1.2Z" fill="{CREAM}" opacity=".8"/>'
    # дарек кагазы
    f'<rect x="25" y="52" width="18" height="13" rx="1.8" fill="{CREAM}" opacity=".95"/>'
    f'<rect x="28" y="55.6" width="12" height="1.9" rx=".9" fill="{STEEL_D}"/>'
    f'<rect x="28" y="59.2" width="8" height="1.9" rx=".9" fill="{STEEL_D}"/>'
)

# ── 5. Жумуш берүү — портфель ────────────────────────────────
JOB = _svg(
    f'<path d="M38 34v-5a7 7 0 0 1 7-7h10a7 7 0 0 1 7 7v5" stroke="{WOOD_D}" '
    f'stroke-width="5" fill="none" stroke-linecap="round"/>'
    f'<rect x="18" y="34" width="64" height="44" rx="7" fill="{WOOD}"/>'
    f'<rect x="18" y="34" width="64" height="12" rx="7" fill="{WOOD_L}"/>'
    f'<path d="M82 44v9c-9.6 4.4-20.3 6.6-32 6.6S27.6 57.4 18 53v-9c9.6 5 20.3 7.5 32 7.5S72.4 49 82 44Z" '
    f'fill="{WOOD_D}" opacity=".5"/>'
    f'<rect x="43" y="50" width="14" height="10" rx="2.6" fill="{GOLD}"/>'
    f'<rect x="46.5" y="53.5" width="7" height="3" rx="1.5" fill="{GOLD_D}"/>'
)

# ── 6. Базарлар — дүкөндүн фасады ────────────────────────────
MARKETS = _svg(
    f'<rect x="8" y="20" width="84" height="60" fill="#9A6B55"/>'
    f'<g opacity=".35" fill="#7C523F">'
    f'<rect x="8" y="26" width="84" height="1.6"/><rect x="8" y="34" width="84" height="1.6"/>'
    f'<rect x="8" y="42" width="84" height="1.6"/><rect x="8" y="50" width="84" height="1.6"/>'
    '</g>'
    # маңдайча
    f'<rect x="18" y="22" width="64" height="12" rx="2" fill="{DARK}"/>'
    f'<rect x="21" y="25" width="58" height="6" rx="1" fill="{GOLD}"/>'
    # чатыр
    f'<path d="M10 42h80v7a3 3 0 0 1-3 3H13a3 3 0 0 1-3-3v-7Z" fill="{GREEN_D}"/>'
    f'<g fill="{CREAM}" opacity=".85">'
    f'<rect x="18" y="42" width="8" height="10"/><rect x="34" y="42" width="8" height="10"/>'
    f'<rect x="50" y="42" width="8" height="10"/><rect x="66" y="42" width="8" height="10"/>'
    '</g>'
    # витрина
    f'<rect x="16" y="56" width="68" height="24" rx="2" fill="{CREAM}"/>'
    f'<rect x="16" y="56" width="68" height="24" rx="2" fill="{GREEN_L}" opacity=".18"/>'
    f'<circle cx="27" cy="68" r="4.6" fill="{RED}"/>'
    f'<circle cx="38" cy="69" r="4" fill="{GOLD}"/>'
    f'<rect x="48" y="63" width="12" height="12" rx="2" fill="{GREEN}"/>'
    f'<rect x="65" y="61" width="12" height="16" rx="2" fill="{WOOD_L}"/>'
)

# ── 7. Такси ─────────────────────────────────────────────────
TAXI = _svg(
    f'<rect x="41" y="20" width="18" height="9" rx="2.6" fill="{DARK}"/>'
    f'<rect x="43.5" y="22" width="13" height="5" rx="1.4" fill="{GOLD}"/>'
    f'<path d="M28 48l5-13a6 6 0 0 1 5.6-3.9h22.8A6 6 0 0 1 67 35l5 13H28Z" fill="{GOLD_D}"/>'
    f'<path d="M35.5 45l3.2-8.4a2 2 0 0 1 1.9-1.3h8.4V45H35.5Zm15.5 0V35.3h8.4a2 2 0 0 1 1.9 1.3L64.5 45H51Z" '
    f'fill="#CFE0F0"/>'
    f'<path d="M14 58a8 8 0 0 1 6.6-7.9L30 48h40l9.4 2.1A8 8 0 0 1 86 58v10a4 4 0 0 1-4 4H18a4 4 0 0 1-4-4V58Z" '
    f'fill="{GOLD}"/>'
    f'<path d="M14 60h72v4H14z" fill="{DARK}" opacity=".14"/>'
    # шакмактар
    f'<g fill="{DARK}" opacity=".85">'
    f'<rect x="20" y="60" width="7" height="4"/><rect x="34" y="60" width="7" height="4"/>'
    f'<rect x="48" y="60" width="7" height="4"/><rect x="62" y="60" width="7" height="4"/>'
    f'<rect x="76" y="60" width="7" height="4"/>'
    '</g>'
    f'<circle cx="30" cy="72" r="9" fill="{DARK}"/><circle cx="30" cy="72" r="3.6" fill="{STEEL_L}"/>'
    f'<circle cx="70" cy="72" r="9" fill="{DARK}"/><circle cx="70" cy="72" r="3.6" fill="{STEEL_L}"/>'
)

# ── Баары ────────────────────────────────────────────────────
ALL = _svg(
    f'<rect x="18" y="18" width="28" height="28" rx="6" fill="{GREEN_L}"/>'
    f'<rect x="54" y="18" width="28" height="28" rx="6" fill="{GOLD}"/>'
    f'<rect x="18" y="54" width="28" height="28" rx="6" fill="{WOOD_L}"/>'
    f'<rect x="54" y="54" width="28" height="28" rx="6" fill="{GREEN_D}"/>'
)

SCENES = {
    "all": ALL,
    "trade": TRADE,
    "service": SERVICE,
    "rental": RENTAL,
    "delivery": DELIVERY,
    "job": JOB,
    "markets": MARKETS,
    "taxi": TAXI,
}
