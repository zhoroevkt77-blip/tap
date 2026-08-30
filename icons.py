# -*- coding: utf-8 -*-
"""
ТАП! — бөлүмдөрдүн эмблемалары.

Жумшак өтмө түстөгү (көлөмдүү) стиль: ар бир белги көктөн көгүшкө
өткөн түс менен толтурулган, алтын басымы бар. Тандалган бөлүмдө
белгинин алды ачык бойдон калат — CSS ошондо гана окулат.
"""

O = '<svg viewBox="0 0 48 48" fill="none" aria-hidden="true">'
G, GL = "#D8AE45", "#EBCE7E"


def grad(uid):
    return (f'<defs><linearGradient id="{uid}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="#6E93C0"/>'
            f'<stop offset="1" stop-color="#1D3B63"/></linearGradient>'
            f'<linearGradient id="{uid}g" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="#F0D68C"/>'
            f'<stop offset="1" stop-color="#C79A2E"/></linearGradient></defs>')


def c(uid, body):
    return O + grad(uid) + body + "</svg>"


ICONS = {
    "all": c("a1",
        f'<rect x="6" y="6" width="16.5" height="16.5" rx="5.5" fill="url(#a1)"/>'
        f'<rect x="25.5" y="6" width="16.5" height="16.5" rx="5.5" fill="url(#a1)" opacity=".55"/>'
        f'<rect x="6" y="25.5" width="16.5" height="16.5" rx="5.5" fill="url(#a1)" opacity=".55"/>'
        f'<rect x="25.5" y="25.5" width="16.5" height="16.5" rx="5.5" fill="url(#a1g)"/>'),

    "trade": c("a2",
        f'<path d="M10.5 15.5h27a2 2 0 0 1 2 2.2l-2.1 19.6a5.2 5.2 0 0 1-5.2 4.7H15.8a5.2 5.2 0 0 1'
        f'-5.2-4.7L8.5 17.7a2 2 0 0 1 2-2.2Z" fill="url(#a2)"/>'
        f'<path d="M17.2 17.5v-4a6.8 6.8 0 0 1 13.6 0v4" stroke="url(#a2g)" stroke-width="3.4" '
        'stroke-linecap="round"/>'
        f'<ellipse cx="24" cy="25" rx="10" ry="4" fill="#fff" opacity=".13"/>'),

    "service": c("a3",
        f'<path d="M40.4 7.9a11 11 0 0 0-14.6 13.8L9.3 38.2a3.9 3.9 0 0 0 5.5 5.5L31.3 27.2'
        f'A11 11 0 0 0 45 12.6l-5.9 5.9-5.8-1.6-1.6-5.8 8.7-3.2Z" fill="url(#a3)"/>'
        f'<circle cx="12.6" cy="40.4" r="2.4" fill="url(#a3g)"/>'),

    "rental": c("a4",
        f'<circle cx="16.5" cy="16.5" r="10.5" fill="url(#a4)"/>'
        f'<circle cx="16.5" cy="16.5" r="4" fill="#EEF3FB"/>'
        f'<path d="M23.4 23.4 39 39" stroke="url(#a4g)" stroke-width="4.8" stroke-linecap="round"/>'
        f'<path d="M31.6 31.8 27.4 36M35.4 35.6l-4 4.2" stroke="url(#a4g)" stroke-width="3.4" '
        'stroke-linecap="round"/>'),

    "delivery": c("a5",
        f'<path d="M24 6 41 14v20L24 42 7 34V14L24 6Z" fill="url(#a5)"/>'
        f'<path d="M7 14l17 8 17-8" stroke="#fff" stroke-width="2" opacity=".3" fill="none"/>'
        f'<path d="M24 22v20" stroke="#fff" stroke-width="2" opacity=".3"/>'
        f'<path d="M15.5 10 33 18.2v7" stroke="url(#a5g)" stroke-width="3.2" '
        'stroke-linecap="round"/>'),

    "job": c("a6",
        f'<rect x="6" y="16" width="36" height="24" rx="5.5" fill="url(#a6)"/>'
        f'<path d="M18 16v-3.5A3.5 3.5 0 0 1 21.5 9h5a3.5 3.5 0 0 1 3.5 3.5V16" '
        f'stroke="url(#a6g)" stroke-width="3.2" stroke-linecap="round"/>'
        f'<path d="M6 26h36" stroke="#fff" stroke-width="2" opacity=".25"/>'
        f'<rect x="20.5" y="23.2" width="7" height="5.6" rx="2" fill="url(#a6g)"/>'),

    "markets": c("a7",
        f'<path d="M7.5 20h33v17a4.5 4.5 0 0 1-4.5 4.5H12A4.5 4.5 0 0 1 7.5 37V20Z" '
        f'fill="url(#a7)"/>'
        f'<path d="M4.5 19 8 8.5h32L43.5 19H4.5Z" fill="url(#a7g)"/>'
        f'<path d="M15.4 8.5 12.6 19M25.2 8.5v10.5M35 8.5l2.8 10.5" stroke="#fff" '
        'stroke-width="2.2" stroke-linecap="round" opacity=".45"/>'),

    "taxi": c("a8",
        f'<path d="M8 26.5 11.7 16A5 5 0 0 1 16.4 12.6h15.2A5 5 0 0 1 36.3 16L40 26.5v9.9'
        f'a2.6 2.6 0 0 1-2.6 2.6h-2.6a2.6 2.6 0 0 1-2.6-2.6v-2H15.8v2a2.6 2.6 0 0 1-2.6 2.6h-2.6'
        f'A2.6 2.6 0 0 1 8 36.4v-9.9Z" fill="url(#a8)"/>'
        f'<path d="M12.5 25.5 15.2 18h17.6l2.7 7.5H12.5Z" fill="#EEF3FB" opacity=".85"/>'
        f'<circle cx="15" cy="30.5" r="2.4" fill="#EEF3FB" opacity=".8"/>'
        f'<circle cx="33" cy="30.5" r="2.4" fill="#EEF3FB" opacity=".8"/>'
        f'<rect x="18.5" y="6" width="11" height="5.6" rx="2.2" fill="url(#a8g)"/>'),
}
