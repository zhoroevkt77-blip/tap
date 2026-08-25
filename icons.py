# -*- coding: utf-8 -*-
"""
ТАП! — бөлүмдөрдүн эмблемалары.

Жалпак сызык эмес, көлөмдүү буюм катары тартылган: ар биринин жарык
бети, ортоңку көлөкөсү жана терең тереңдиги бар. Ошондон улам алар
эмодзи сыяктуу «жандуу» көрүнөт, бирок SVG болгондуктан ар кандай
телефондо бирдей чыгат жана эч нерсе жүктөлбөйт.

Ар бир фигурада data-t белгиси турат:
    lite — жарык бети      mid — ортоңку      deep — көлөкө
Тандалган бөлүмдө CSS ошолорду актын үч даражасына айландырат,
ошондуктан белги караңгы жашыл тактын үстүндө жарык болуп калат.
"""

_O = ('<svg viewBox="0 0 48 48" fill="none" aria-hidden="true">')

# Түстөр: жарык жалбырак → терең мүк
L = "#CFE4D7"   # lite
M = "#8CB69C"   # mid
D = "#38684A"   # deep
# Металл (ачкыч, устаканын куралы)
ML = "#C9D4CD"
MM = "#94A79B"
MD = "#586B5F"


ICONS = {

    # ── Баары — төрт така ───────────────────────────────────
    "all": _O +
    f'<rect data-t="mid"  x="6"  y="6"  width="15" height="15" rx="4.5" fill="{M}"/>'
    f'<rect data-t="lite" x="27" y="6"  width="15" height="15" rx="4.5" fill="{L}"/>'
    f'<rect data-t="lite" x="6"  y="27" width="15" height="15" rx="4.5" fill="{L}"/>'
    f'<rect data-t="deep" x="27" y="27" width="15" height="15" rx="4.5" fill="{D}"/>'
    '</svg>',

    # ── Соода-сатык — базар куржуну ─────────────────────────
    "trade": _O +
    f'<path data-t="mid" d="M17 16v-2.5a7 7 0 0 1 14 0V16" stroke="{M}" '
    'stroke-width="3" stroke-linecap="round" fill="none"/>'
    f'<path data-t="lite" d="M9.5 17h29l-2.2 20.4a4 4 0 0 1-4 3.6H15.7a4 4 0 0 1-4-3.6L9.5 17Z" '
    f'fill="{L}"/>'
    f'<path data-t="mid" d="M31 17h7.5l-2.2 20.4a4 4 0 0 1-4 3.6h-7.5a4 4 0 0 0 4-3.6L31 17Z" '
    f'fill="{M}"/>'
    f'<circle data-t="deep" cx="18.5" cy="24" r="2.1" fill="{D}"/>'
    f'<circle data-t="deep" cx="29.5" cy="24" r="2.1" fill="{D}"/>'
    '</svg>',

    # ── Кызмат көрсөтүү — ачкыч (гайка ачкычы) ──────────────
    "service": _O +
    f'<path data-t="mid" d="M32.6 7.4a10.4 10.4 0 0 0-11.9 13.4L8.2 33.3a4.4 4.4 0 0 0 6.2 6.2'
    f'l12.5-12.5a10.4 10.4 0 0 0 13.4-11.9l-6.1 6.1-5.7-1.5-1.5-5.7 5.6-6.6Z" fill="{MM}"/>'
    f'<path data-t="lite" d="M30.9 8.1a10.4 10.4 0 0 0-10.2 12.7L8.2 33.3a4.4 4.4 0 0 0 3.1 7.5'
    'c-1-1.6-.8-3.8.6-5.2l13.3-13.3a8.4 8.4 0 0 1 5.7-14.2Z" '
    f'fill="{ML}"/>'
    f'<circle data-t="deep" cx="11.5" cy="36.5" r="2.2" fill="{MD}"/>'
    '</svg>',

    # ── Ижарага берүү — кооздолгон эски ачкыч ───────────────
    "rental": _O +
    # баш — тегерек курчоо жана үч кулакча
    f'<circle data-t="mid"  cx="18" cy="14" r="4.4" fill="{M}"/>'
    f'<circle data-t="mid"  cx="27.5" cy="9.5" r="3.6" fill="{M}"/>'
    f'<circle data-t="mid"  cx="27.5" cy="18.5" r="3.6" fill="{M}"/>'
    f'<circle data-t="lite" cx="22" cy="14" r="9.6" fill="{L}"/>'
    f'<path data-t="mid"   d="M22 4.4a9.6 9.6 0 0 1 0 19.2 9.6 9.6 0 0 0 0-19.2Z" fill="{M}"/>'
    '<circle data-t="hole" cx="22" cy="14" r="3.9" fill="#FBFCFB"/>'
    # сап
    f'<path data-t="deep" d="M19.4 22.6h5.2v18.1a1.7 1.7 0 0 1-1.7 1.7h-1.8a1.7 1.7 0 0 1-1.7-1.7V22.6Z" '
    f'fill="{D}"/>'
    # тиштери
    f'<rect data-t="deep" x="24.6" y="27.5" width="7.4" height="3.5" rx="1.6" fill="{D}"/>'
    f'<rect data-t="deep" x="24.6" y="33.6" width="5.4" height="3.5" rx="1.6" fill="{D}"/>'
    '</svg>',

    # ── Жеткирүү — ачык куту ────────────────────────────────
    "delivery": _O +
    # ичи (караңгы көңдөй)
    f'<path data-t="deep" d="M13 19.5 24 24l11-4.5L24 15l-11 4.5Z" fill="{D}"/>'
    # алдыңкы жана каптал беттери
    f'<path data-t="lite" d="M11.5 20.2 24 25.3v16.2l-11.6-4.7a1.6 1.6 0 0 1-1-1.5V20.2Z" fill="{L}"/>'
    f'<path data-t="mid"  d="M36.5 20.2 24 25.3v16.2l11.6-4.7a1.6 1.6 0 0 0 1-1.5V20.2Z" fill="{M}"/>'
    # ачылып турган төрт капкак
    f'<path data-t="lite" d="M11.5 20.2 4.6 15.6l7.6-4.4 8.3 4.6-9 4.4Z" fill="{L}"/>'
    f'<path data-t="mid"  d="M36.5 20.2 43.4 15.6l-7.6-4.4-8.3 4.6 9 4.4Z" fill="{M}"/>'
    f'<path data-t="mid"  d="M20.5 15.8 17.6 6.9l6.4-1.4 3 8.9-6.5 1.4Z" fill="{M}" opacity=".85"/>'
    f'<path data-t="lite" d="M27.5 15.8 30.4 6.9 24 5.5l-3 8.9 6.5 1.4Z" fill="{L}"/>'
    '</svg>',

    # ── Жумуш берүү — портфель ──────────────────────────────
    "job": _O +
    f'<path data-t="mid" d="M18 14v-2.6a3.4 3.4 0 0 1 3.4-3.4h5.2a3.4 3.4 0 0 1 3.4 3.4V14" '
    f'stroke="{M}" stroke-width="3.2" stroke-linecap="round" fill="none"/>'
    f'<rect data-t="lite" x="6" y="14" width="36" height="26" rx="4.6" fill="{L}"/>'
    f'<path data-t="mid" d="M42 18.6v6.1c-5.6 2.6-11.6 3.9-18 3.9S11.6 27.3 6 24.7v-6.1'
    f'c5.6 2.9 11.6 4.3 18 4.3s12.4-1.4 18-4.3Z" fill="{M}"/>'
    f'<rect data-t="deep" x="21" y="22.4" width="6" height="4.6" rx="1.6" fill="{D}"/>'
    '</svg>',

    # ── Базарлар — соода катарынын чатыры ───────────────────
    "markets": _O +
    f'<path data-t="lite" d="M9 21h30v17.5a2.5 2.5 0 0 1-2.5 2.5h-25A2.5 2.5 0 0 1 9 38.5V21Z" fill="{L}"/>'
    f'<path data-t="mid" d="M28 41V29.5a1.8 1.8 0 0 1 1.8-1.8h5.4a1.8 1.8 0 0 1 1.8 1.8V41H28Z" fill="{M}"/>'
    f'<rect data-t="mid" x="12.5" y="27.7" width="11" height="7.4" rx="1.8" fill="{M}"/>'
    f'<path data-t="deep" d="M6 20.5 9.6 10a2 2 0 0 1 1.9-1.4h25a2 2 0 0 1 1.9 1.4L42 20.5'
    f'a1 1 0 0 1-.9 1.3H6.9a1 1 0 0 1-.9-1.3Z" fill="{D}"/>'
    f'<path data-t="lite" d="M15.6 8.6h6.2l-2.1 13.2h-6.2l2.1-13.2Zm10.6 0h6.2l2.1 13.2h-6.2'
    f'L26.2 8.6Z" fill="{L}" opacity=".55"/>'
    '</svg>',

    # ── Такси — капталынан көрүнгөн унаа ────────────────────
    "taxi": _O +
    # чатырдагы белги
    f'<rect data-t="deep" x="20" y="6.2" width="8" height="4.4" rx="1.5" fill="{D}"/>'
    # кабина
    f'<path data-t="mid" d="M15.2 12.4a2.4 2.4 0 0 1 2.2-1.5h13.2a2.4 2.4 0 0 1 2.2 1.5l3.3 8.4'
    f'H11.9l3.3-8.4Z" fill="{M}"/>'
    # айнектер
    f'<path data-t="deep" d="M16.6 19.2l2.3-5.9h4.1v5.9h-6.4Zm8.4 0v-5.9h4.1l2.3 5.9H25Z" '
    f'fill="{D}" opacity=".45"/>'
    # кузов
    f'<rect data-t="lite" x="5.5" y="20.4" width="37" height="12.4" rx="4.4" fill="{L}"/>'
    f'<path data-t="mid" d="M38.1 20.4h.4a4 4 0 0 1 4 4v4.4a4 4 0 0 1-4 4h-.4a2.6 2.6 0 0 0 2.6-2.6'
    f'v-7.2a2.6 2.6 0 0 0-2.6-2.6Z" fill="{M}"/>'
    f'<rect data-t="mid" x="5.5" y="26.2" width="37" height="2.2" fill="{M}" opacity=".5"/>'
    # дөңгөлөктөр
    f'<circle data-t="deep" cx="14.8" cy="34.4" r="5.2" fill="{D}"/>'
    f'<circle data-t="deep" cx="33.2" cy="34.4" r="5.2" fill="{D}"/>'
    f'<circle cx="14.8" cy="34.4" r="2.1" fill="{L}"/>'
    f'<circle cx="33.2" cy="34.4" r="2.1" fill="{L}"/>'
    '</svg>',
}
