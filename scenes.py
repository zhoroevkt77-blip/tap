# -*- coding: utf-8 -*-
"""
ТАП! — башкы беттин бөлүм такталары.

Ар бир бөлүм жумшак өтмө түстөгү белги менен көрсөтүлөт: көктөн көгүшкө
өткөн фигура, алтын басымы бар. Астында ачык тилкеде аталышы турат.

Неге сүрөт эмес, SVG:
  • жети сүрөт 4G'де жүктөлүшү керек, SVG болсо бет менен кошо келет;
  • каалаган экранда даана — кичине телефондо да, чоңунда да;
  • түсүн бир жерден өзгөртсө, жетөө тең өзгөрөт.

Ар бир көрүнүш 100×100 квадратта тартылат: ачык фон, ортосунда белги.
"""

BG1 = "#F6F9FD"      # фондун жогорку жагы
BG2 = "#E4ECF8"      # фондун ылдыйкы жагы


def _frame(uid, body):
    """Ачык фон + ортосуна коюлган белги (белги 48×48 торчодо тартылган)."""
    return (
        '<svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet" '
        'aria-hidden="true">'
        f'<defs><linearGradient id="bg{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG1}"/>'
        f'<stop offset="1" stop-color="{BG2}"/></linearGradient></defs>'
        f'<rect width="100" height="100" fill="url(#bg{uid})"/>'
        '<g transform="translate(20 20) scale(1.25)">' + body + '</g>'
        '</svg>')


SCENES = {
    "all": _frame("all", '<defs><linearGradient id="all_1" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6E93C0"/><stop offset="1" stop-color="#1D3B63"/></linearGradient><linearGradient id="all_1g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F0D68C"/><stop offset="1" stop-color="#C79A2E"/></linearGradient></defs><rect x="6" y="6" width="16.5" height="16.5" rx="5.5" fill="url(#all_1)"/><rect x="25.5" y="6" width="16.5" height="16.5" rx="5.5" fill="url(#all_1)" opacity=".55"/><rect x="6" y="25.5" width="16.5" height="16.5" rx="5.5" fill="url(#all_1)" opacity=".55"/><rect x="25.5" y="25.5" width="16.5" height="16.5" rx="5.5" fill="url(#all_1g)"/>'),
    "trade": _frame("trade", '<defs><linearGradient id="trade_2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6E93C0"/><stop offset="1" stop-color="#1D3B63"/></linearGradient><linearGradient id="trade_2g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F0D68C"/><stop offset="1" stop-color="#C79A2E"/></linearGradient></defs><path d="M10.5 15.5h27a2 2 0 0 1 2 2.2l-2.1 19.6a5.2 5.2 0 0 1-5.2 4.7H15.8a5.2 5.2 0 0 1-5.2-4.7L8.5 17.7a2 2 0 0 1 2-2.2Z" fill="url(#trade_2)"/><path d="M17.2 17.5v-4a6.8 6.8 0 0 1 13.6 0v4" stroke="url(#trade_2g)" stroke-width="3.4" stroke-linecap="round"/><ellipse cx="24" cy="25" rx="10" ry="4" fill="#fff" opacity=".13"/>'),
    "service": _frame("service", '<defs><linearGradient id="service_3" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6E93C0"/><stop offset="1" stop-color="#1D3B63"/></linearGradient><linearGradient id="service_3g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F0D68C"/><stop offset="1" stop-color="#C79A2E"/></linearGradient></defs><path d="M40.4 7.9a11 11 0 0 0-14.6 13.8L9.3 38.2a3.9 3.9 0 0 0 5.5 5.5L31.3 27.2A11 11 0 0 0 45 12.6l-5.9 5.9-5.8-1.6-1.6-5.8 8.7-3.2Z" fill="url(#service_3)"/><circle cx="12.6" cy="40.4" r="2.4" fill="url(#service_3g)"/>'),
    "rental": _frame("rental", '<defs><linearGradient id="rental_4" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6E93C0"/><stop offset="1" stop-color="#1D3B63"/></linearGradient><linearGradient id="rental_4g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F0D68C"/><stop offset="1" stop-color="#C79A2E"/></linearGradient></defs><circle cx="16.5" cy="16.5" r="10.5" fill="url(#rental_4)"/><circle cx="16.5" cy="16.5" r="4" fill="#EEF3FB"/><path d="M23.4 23.4 39 39" stroke="url(#rental_4g)" stroke-width="4.8" stroke-linecap="round"/><path d="M31.6 31.8 27.4 36M35.4 35.6l-4 4.2" stroke="url(#rental_4g)" stroke-width="3.4" stroke-linecap="round"/>'),
    "delivery": _frame("delivery", '<defs><linearGradient id="delivery_5" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6E93C0"/><stop offset="1" stop-color="#1D3B63"/></linearGradient><linearGradient id="delivery_5g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F0D68C"/><stop offset="1" stop-color="#C79A2E"/></linearGradient></defs><path d="M24 6 41 14v20L24 42 7 34V14L24 6Z" fill="url(#delivery_5)"/><path d="M7 14l17 8 17-8" stroke="#fff" stroke-width="2" opacity=".3" fill="none"/><path d="M24 22v20" stroke="#fff" stroke-width="2" opacity=".3"/><path d="M15.5 10 33 18.2v7" stroke="url(#delivery_5g)" stroke-width="3.2" stroke-linecap="round"/>'),
    "job": _frame("job", '<defs><linearGradient id="job_6" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6E93C0"/><stop offset="1" stop-color="#1D3B63"/></linearGradient><linearGradient id="job_6g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F0D68C"/><stop offset="1" stop-color="#C79A2E"/></linearGradient></defs><rect x="6" y="16" width="36" height="24" rx="5.5" fill="url(#job_6)"/><path d="M18 16v-3.5A3.5 3.5 0 0 1 21.5 9h5a3.5 3.5 0 0 1 3.5 3.5V16" stroke="url(#job_6g)" stroke-width="3.2" stroke-linecap="round"/><path d="M6 26h36" stroke="#fff" stroke-width="2" opacity=".25"/><rect x="20.5" y="23.2" width="7" height="5.6" rx="2" fill="url(#job_6g)"/>'),
    "markets": _frame("markets", '<defs><linearGradient id="markets_7" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6E93C0"/><stop offset="1" stop-color="#1D3B63"/></linearGradient><linearGradient id="markets_7g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F0D68C"/><stop offset="1" stop-color="#C79A2E"/></linearGradient></defs><path d="M7.5 20h33v17a4.5 4.5 0 0 1-4.5 4.5H12A4.5 4.5 0 0 1 7.5 37V20Z" fill="url(#markets_7)"/><path d="M4.5 19 8 8.5h32L43.5 19H4.5Z" fill="url(#markets_7g)"/><path d="M15.4 8.5 12.6 19M25.2 8.5v10.5M35 8.5l2.8 10.5" stroke="#fff" stroke-width="2.2" stroke-linecap="round" opacity=".45"/>'),
    "taxi": _frame("taxi", '<defs><linearGradient id="taxi_8" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6E93C0"/><stop offset="1" stop-color="#1D3B63"/></linearGradient><linearGradient id="taxi_8g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F0D68C"/><stop offset="1" stop-color="#C79A2E"/></linearGradient></defs><path d="M8 26.5 11.7 16A5 5 0 0 1 16.4 12.6h15.2A5 5 0 0 1 36.3 16L40 26.5v9.9a2.6 2.6 0 0 1-2.6 2.6h-2.6a2.6 2.6 0 0 1-2.6-2.6v-2H15.8v2a2.6 2.6 0 0 1-2.6 2.6h-2.6A2.6 2.6 0 0 1 8 36.4v-9.9Z" fill="url(#taxi_8)"/><path d="M12.5 25.5 15.2 18h17.6l2.7 7.5H12.5Z" fill="#EEF3FB" opacity=".85"/><circle cx="15" cy="30.5" r="2.4" fill="#EEF3FB" opacity=".8"/><circle cx="33" cy="30.5" r="2.4" fill="#EEF3FB" opacity=".8"/><rect x="18.5" y="6" width="11" height="5.6" rx="2.2" fill="url(#taxi_8g)"/>'),
}
