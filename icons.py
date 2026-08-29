# -*- coding: utf-8 -*-
"""
ТАП! — бөлүмдөрдүн эмблемалары.

Заманбап, тегиз формалар: жоон сызык эмес, толтурулган фигуралар.
Ар биринде үч катмар бар —
    lite — жарык бети      mid — ортоңку      deep — көлөкө
жана бир алтын басым (gold). Тандалган бөлүмдө CSS ошол катмарларды
актын даражаларына айландырат, ошондуктан белги көк тактын үстүндө
жарык болуп чыгат.
"""

_O = '<svg viewBox="0 0 48 48" fill="none" aria-hidden="true">'

# Көк — үч даража
L = "#B9CDE6"   # lite
M = "#5C82B0"   # mid
D = "#1D3B63"   # deep
# Алтын басым
G = "#D8AE45"
GL = "#EBCE7E"


ICONS = {

    # ── Баары — төрт така ───────────────────────────────────
    "all": _O +
    f'<rect data-t="mid"  x="6"  y="6"  width="16" height="16" rx="5" fill="{M}"/>'
    f'<rect data-t="lite" x="26" y="6"  width="16" height="16" rx="5" fill="{L}"/>'
    f'<rect data-t="lite" x="6"  y="26" width="16" height="16" rx="5" fill="{L}"/>'
    f'<rect x="26" y="26" width="16" height="16" rx="5" fill="{G}"/>'
    '</svg>',

    # ── Соода-сатык — соода баштыгы ─────────────────────────
    "trade": _O +
    f'<path data-t="lite" d="M11 15h26a2 2 0 0 1 2 2.2l-2.1 20A5 5 0 0 1 31.9 42H16.1a5 5 0 0 1'
    f'-5-4.8l-2.1-20A2 2 0 0 1 11 15Z" fill="{L}"/>'
    f'<path data-t="mid" d="M30 15h7a2 2 0 0 1 2 2.2l-2.1 20A5 5 0 0 1 31.9 42h-7a5 5 0 0 0 5-4.8'
    f'l2.1-20A2 2 0 0 0 30 15Z" fill="{M}"/>'
    f'<path d="M17 17v-3.5a7 7 0 0 1 14 0V17" stroke="{G}" stroke-width="3.4" '
    'stroke-linecap="round" fill="none"/>'
    '</svg>',

    # ── Кызмат көрсөтүү — ачкыч ─────────────────────────────
    "service": _O +
    f'<path data-t="mid" d="M40.4 7.9a11 11 0 0 0-14.6 13.8L9.3 38.2a3.9 3.9 0 0 0 5.5 5.5'
    f'L31.3 27.2A11 11 0 0 0 45 12.6l-5.9 5.9-5.8-1.6-1.6-5.8 8.7-3.2Z" fill="{M}"/>'
    f'<path data-t="lite" d="M38.8 8.6a11 11 0 0 0-13 13.1L9.3 38.2a3.9 3.9 0 0 0 2.7 6.7'
    f'c-.8-1.4-.6-3.3.6-4.5l17.1-17.1a8.9 8.9 0 0 1 9.1-14.7Z" fill="{L}"/>'
    f'<circle cx="12.6" cy="40.4" r="2.4" fill="{G}"/>'
    '</svg>',

    # ── Ижарага берүү — ачкыч ───────────────────────────────
    "rental": _O +
    f'<circle data-t="lite" cx="16" cy="16" r="10.5" fill="{L}"/>'
    f'<circle data-t="deep" cx="16" cy="16" r="4.2" fill="{D}"/>'
    f'<path d="M22.6 23.2 39 39.6" stroke="{G}" stroke-width="4.6" stroke-linecap="round"/>'
    f'<path d="M31.4 32 27 36.4M35.4 36 31.4 40" stroke="{GL}" stroke-width="3.4" '
    'stroke-linecap="round"/>'
    '</svg>',

    # ── Жеткирүү — кутуча ───────────────────────────────────
    "delivery": _O +
    f'<path data-t="lite" d="M24 6 41 14v20L24 42 7 34V14L24 6Z" fill="{L}"/>'
    f'<path data-t="mid" d="M24 24 41 14v20L24 42V24Z" fill="{M}"/>'
    f'<path data-t="deep" d="M24 24 7 14v20l17 8V24Z" fill="{D}"/>'
    f'<path d="M15.5 10 33 18.2v7" stroke="{G}" stroke-width="3.2" stroke-linecap="round" '
    'fill="none"/>'
    '</svg>',

    # ── Жумуш берүү — портфель ──────────────────────────────
    "job": _O +
    f'<rect data-t="lite" x="6" y="16" width="36" height="24" rx="5" fill="{L}"/>'
    f'<path data-t="mid" d="M6 26h36v9a5 5 0 0 1-5 5H11a5 5 0 0 1-5-5v-9Z" fill="{M}"/>'
    f'<path d="M18 16v-3.5A3.5 3.5 0 0 1 21.5 9h5a3.5 3.5 0 0 1 3.5 3.5V16" stroke="{G}" '
    'stroke-width="3.2" stroke-linecap="round" fill="none"/>'
    f'<rect x="20.5" y="23.5" width="7" height="5.5" rx="2" fill="{G}"/>'
    '</svg>',

    # ── Базарлар — тент ─────────────────────────────────────
    "markets": _O +
    f'<path data-t="lite" d="M7 20h34v17a4 4 0 0 1-4 4H11a4 4 0 0 1-4-4V20Z" fill="{L}"/>'
    f'<path data-t="mid" d="M27 20h14v17a4 4 0 0 1-4 4h-10V20Z" fill="{M}"/>'
    f'<path d="M4.5 19 8 8.5h32L43.5 19H4.5Z" fill="{G}"/>'
    f'<path d="M15.4 8.5 12.6 19M25.2 8.5v10.5M35 8.5l2.8 10.5" stroke="{GL}" '
    'stroke-width="2.4" stroke-linecap="round"/>'
    '</svg>',

    # ── Такси — унаа ────────────────────────────────────────
    "taxi": _O +
    f'<path data-t="lite" d="M8 26.5 11.7 16A5 5 0 0 1 16.4 12.6h15.2A5 5 0 0 1 36.3 16L40 26.5'
    f'v9.9a2.6 2.6 0 0 1-2.6 2.6h-2.6a2.6 2.6 0 0 1-2.6-2.6v-2H15.8v2a2.6 2.6 0 0 1-2.6 2.6h-2.6'
    f'A2.6 2.6 0 0 1 8 36.4v-9.9Z" fill="{L}"/>'
    f'<path data-t="mid" d="M12.5 25.5 15.2 18h17.6l2.7 7.5H12.5Z" fill="{M}"/>'
    f'<circle data-t="deep" cx="15" cy="30.5" r="2.4" fill="{D}"/>'
    f'<circle data-t="deep" cx="33" cy="30.5" r="2.4" fill="{D}"/>'
    f'<rect x="18.5" y="6" width="11" height="5.6" rx="2.2" fill="{G}"/>'
    '</svg>',
}
