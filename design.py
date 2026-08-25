# -*- coding: utf-8 -*-
"""
ТАП! — визуалдык тил.

Идеясы: платформанын белгиси — **түндүк**. Ал кыргыз үйүнүн чокусу,
желекте турат жана ТАП!тын өз эмблемасында да бар. Ошондуктан:

  • түндүк — логотиптин жанындагы белги, сүрөтү жок жарыянын орду
    жана бош барактын эмблемасы;
  • бөлүмдөрдүн белгилери — эмодзи эмес, бир калыпта тартылган SVG
    (бирдей сызык калыңдыгы, жумшак бурчтар), ошондуктан ар кандай
    телефондо бирдей көрүнөт;
  • шрифт — Golos Text (кириллица үчүн атайын жасалган, майда өлчөмдө
    ачык окулат) жана баада/санда Manrope (кең, бекем сандар).

Түстөр:
  --ink    #10231A  негизги текст (кара эмес, жашылга тартылган)
  --moss   #0B6E3F  терең жашыл — башкы тилке
  --leaf   #12A05C  бренд жашылы — басым
  --wheat  #E8A33D  буудай сарысы — баа жана акцент
  --paper  #F4F6F4  фон
  --mist   #E4E9E5  чек сызыктар
"""

import os

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    'family=Golos+Text:wght@400;500;600;700&'
    'family=Manrope:wght@600;700;800&display=swap" rel="stylesheet">'
)

# ── Түндүк ───────────────────────────────────────────────────
# Тегерек курчоо + айкаш ичи. Логотипте, бош орунда, бош баракта.

TUNDUK = (
    '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" '
    'stroke-linecap="round" aria-hidden="true">'
    # тегерек боо
    '<circle cx="24" cy="24" r="18.4" stroke-width="2.7"/>'
    # үч уук боону алты жерден кайчылаштырат
    '<path d="M5.6 24h36.8" stroke-width="2"/>'
    '<path d="M14.8 8.1 33.2 39.9" stroke-width="2"/>'
    '<path d="M33.2 8.1 14.8 39.9" stroke-width="2"/>'
    # ортодогу чакан чамбар
    '<circle cx="24" cy="24" r="4.6" stroke-width="2" fill="none"/>'
    '</svg>'
)


from icons import ICONS  # noqa: E402  (көлөмдүү эмблемалар)


# ── Ылдыйкы тилке ────────────────────────────────────────────

_N = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
      'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">')

NAV_ICONS = {
    "home": _N + '<path d="M3.5 10.2 12 3.6l8.5 6.6V19a1.6 1.6 0 0 1-1.6 1.6H5.1A1.6 1.6 0 0 1 3.5 19v-8.8Z"/>'
                 '<path d="M9.4 20.6v-6h5.2v6"/></svg>',
    "fav":  _N + '<path d="M12 20.3s-7.4-4.6-7.4-9.4a4.2 4.2 0 0 1 7.4-2.7 4.2 4.2 0 0 1 7.4 2.7'
                 'c0 4.8-7.4 9.4-7.4 9.4Z"/></svg>',
    "add":  _N + '<circle cx="12" cy="12" r="8.6"/><path d="M12 8.4v7.2M8.4 12h7.2"/></svg>',
    "msg":  _N + '<rect x="3" y="5.2" width="18" height="13.6" rx="2.4"/>'
                 '<path d="m3.6 6.6 7.3 5.3a2 2 0 0 0 2.2 0l7.3-5.3"/></svg>',
    "me":   _N + '<circle cx="12" cy="8.4" r="3.8"/>'
                 '<path d="M4.8 20.4a7.2 7.2 0 0 1 14.4 0"/></svg>',
}

# Ботсуз иштей турган бет — «Тандалган» гана. Калган үчөө ботко алып барат,
# анткени жарыя коюу, кат жазуу жана өз жарыяларын башкаруу ошол жерде болот.
BOT = os.environ.get("BOT_USERNAME", "TapmeniBot").lstrip("@")


def nav(active="home"):
    items = [
        ("home", "/",                                  NAV_ICONS["home"], "Башкы бет"),
        ("fav",  "/fav",                               NAV_ICONS["fav"],  "Тандалган"),
        ("add",  f"https://t.me/{BOT}?start=post",     NAV_ICONS["add"],  "Жарыя берүү"),
        ("msg",  f"https://t.me/{BOT}",                NAV_ICONS["msg"],  "Билдирүү"),
        ("me",   f"https://t.me/{BOT}?start=my",       NAV_ICONS["me"],   "Кабинет"),
    ]
    out = ""
    for key, href, ic, label in items:
        cls = ' class="on"' if key == active else ""
        out += f'<a href="{href}"{cls}>{ic}<span>{label}</span></a>'
    return f'<nav class="nav">{out}</nav>'


CSS = """
:root{
 --ink:#10231A; --soft:#5B6B62; --faint:#8A9A91;
 --moss:#0B6E3F; --leaf:#12A05C; --wheat:#E8A33D;
 --paper:#F4F6F4; --card:#fff; --mist:#E4E9E5;
 --r:18px;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);
 font-family:"Golos Text",-apple-system,"Segoe UI",Roboto,system-ui,sans-serif;
 font-size:15px;line-height:1.45;font-weight:400;padding-bottom:74px;
 -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
a{color:inherit;text-decoration:none}
svg{display:block}
.wrap{max-width:1040px;margin:0 auto;padding:0 14px}

/* ---- Башкы тилке ---- */
.top{background:linear-gradient(168deg,#0E7C47 0%,#0B6E3F 62%,#095E36 100%);
 color:#fff;padding:10px 0 16px;position:sticky;top:0;z-index:20}
.tin{display:flex;align-items:center;gap:11px;padding:3px 0 13px}
.logo{display:flex;align-items:center;gap:8px;font-family:"Manrope",system-ui,sans-serif;
 font-weight:800;font-size:21px;letter-spacing:-.6px}
.logo svg{width:23px;height:23px;opacity:.9;flex:none}
.pin{font-size:13px;font-weight:500;background:rgba(255,255,255,.15);
 border:1px solid rgba(255,255,255,.14);padding:6px 12px;border-radius:15px;
 display:flex;align-items:center;gap:5px;max-width:57%;
 overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pin b{font-weight:400;opacity:.85;font-size:12px}
.s{display:flex;align-items:center;background:#fff;border-radius:26px;
 padding:0 5px 0 17px;height:48px;box-shadow:0 3px 14px rgba(6,52,30,.16)}
.s input{flex:1;min-width:0;border:0;font-size:16px;font-family:inherit;
 background:transparent;padding:0;color:var(--ink)}
.s input:focus{outline:none}
.s input::placeholder{color:var(--faint)}
.s button{border:0;background:var(--ink);color:#fff;height:38px;padding:0 18px;
 border-radius:19px;font-size:14px;font-weight:600;font-family:inherit;cursor:pointer}
.s button:active{transform:scale(.97)}

/* ---- Бөлүмдөр ---- */
.cats{display:flex;gap:6px;overflow-x:auto;padding:16px 14px 8px;
 scrollbar-width:none;max-width:1040px;margin:0 auto}
.cats::-webkit-scrollbar{display:none}
.cat{flex:none;width:76px;text-align:center;font-size:11.5px;line-height:1.25;
 color:var(--soft);font-weight:500}
.cat .ic{width:58px;height:58px;border-radius:20px;
 background:linear-gradient(160deg,#FFFFFF 0%,#F4F7F4 100%);
 border:1px solid #E7EDE8;display:flex;align-items:center;justify-content:center;
 margin:0 auto 7px;transition:.18s;
 box-shadow:0 2px 5px rgba(16,35,26,.06),0 8px 18px -8px rgba(16,35,26,.14)}
.cat .ic svg{width:34px;height:34px}
.cat .lb{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
 overflow:hidden;height:29px}
.cat.on .ic{background:linear-gradient(160deg,#2F7C4E 0%,#1F5C39 100%);
 border-color:#1F5C39;
 box-shadow:0 4px 10px rgba(16,72,42,.3),0 12px 26px -10px rgba(16,72,42,.5)}
/* Тандалганда белги караңгы тактын үстүндө жарык болуп калат —
   үч катмар актын үч даражасына айланып, көлөмү сакталат. */
.cat.on .ic svg [data-t="lite"]{fill:#FFFFFF;stroke:#FFFFFF}
.cat.on .ic svg [data-t="mid"] {fill:#A9D5BC;stroke:#A9D5BC}
.cat.on .ic svg [data-t="deep"]{fill:#164A31;stroke:#164A31}
/* Тешик так менен бирдей түстө болсун — ичи көрүнүп турсун */
.cat.on .ic svg [data-t="hole"]{fill:#255E3E}
.cat.on{color:var(--ink);font-weight:600}

/* ---- Чыпкалар ---- */
.regbar,.subbar{display:flex;gap:7px;overflow-x:auto;padding:7px 14px 2px;
 scrollbar-width:none;max-width:1040px;margin:0 auto}
.regbar::-webkit-scrollbar,.subbar::-webkit-scrollbar{display:none}
.rg{flex:none;background:var(--card);border:1px solid var(--mist);border-radius:16px;
 padding:7px 14px;font-size:12.5px;font-weight:500;color:var(--soft);white-space:nowrap}
.rg.on{background:var(--ink);color:#fff;border-color:var(--ink);font-weight:600}
.sb2{flex:none;background:#E9F4EE;border:1px solid #D2E8DC;border-radius:16px;
 padding:7px 14px;font-size:12.5px;font-weight:500;color:#0A6238;white-space:nowrap}
.sb2.on{background:var(--leaf);color:#fff;border-color:var(--leaf);font-weight:600}
.sb2 em{font-style:normal;opacity:.62;font-size:11px;margin-left:2px}

/* ---- Жыйынтык ---- */
.rl{display:flex;align-items:baseline;gap:7px;padding:16px 0 11px}
.rn{font-family:"Manrope",system-ui,sans-serif;font-size:19px;font-weight:800;
 letter-spacing:-.4px;font-variant-numeric:tabular-nums}
.rlb{font-size:14px;color:var(--soft);font-weight:500}
.cl{margin-left:auto;font-size:13px;color:var(--leaf);font-weight:600}

/* ---- Карточкалар ---- */
.g{display:grid;grid-template-columns:repeat(2,1fr);gap:11px;padding-bottom:26px}
@media(min-width:620px){.g{grid-template-columns:repeat(3,1fr);gap:13px}}
@media(min-width:900px){.g{grid-template-columns:repeat(4,1fr)}}
.c{background:var(--card);border:1px solid var(--mist);border-radius:var(--r);
 overflow:hidden;display:flex;flex-direction:column;transition:.16s}
.c:active{transform:scale(.985)}
.ph{position:relative;aspect-ratio:4/3;background:#EDF1EE;
 display:flex;align-items:center;justify-content:center;color:#C2D2C8}
.ph i{display:block;width:34px;height:34px;opacity:.5}
.ph i svg{width:100%;height:100%}
.ph img{width:100%;height:100%;object-fit:cover;display:block}
.c.nophoto .ph{aspect-ratio:16/9}
.fav{position:absolute;top:9px;right:9px;width:33px;height:33px;border-radius:50%;
 background:rgba(255,255,255,.94);display:flex;align-items:center;justify-content:center;
 color:var(--faint);box-shadow:0 1px 4px rgba(16,35,26,.1);border:0;padding:0;
 cursor:pointer;transition:.15s}
.fav svg{width:17px;height:17px;transition:.15s}
.fav.on{color:#E0483C}
.fav.on svg{fill:#E0483C;transform:scale(1.12)}
.fav:active{transform:scale(.88)}
.cb{padding:11px 12px 13px;display:flex;flex-direction:column;flex:1}
.p{font-family:"Manrope",system-ui,sans-serif;font-size:18px;font-weight:800;
 letter-spacing:-.4px;margin-bottom:5px;font-variant-numeric:tabular-nums}
.pd{font-family:"Golos Text",system-ui,sans-serif;font-size:14.5px;font-weight:600;
 color:var(--leaf);letter-spacing:0}
.t{font-size:13.5px;line-height:1.38;margin:0 0 10px;font-weight:400;color:var(--soft);
 display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.m{margin-top:auto;display:flex;gap:8px;align-items:center;font-size:11.5px;
 color:var(--faint);white-space:nowrap}
.m span:first-child{overflow:hidden;text-overflow:ellipsis}
.m .vw{margin-left:auto;display:flex;align-items:center;gap:3px}
.m .vw svg{width:13px;height:13px}

/* ---- Толук барак ---- */
.back{display:inline-flex;align-items:center;gap:6px;padding:15px 0 9px;
 font-size:14px;color:var(--leaf);font-weight:600}
.dph{background:var(--card);border:1px solid var(--mist);border-radius:var(--r);
 overflow:hidden;margin-bottom:11px;display:flex;align-items:center;
 justify-content:center;min-height:150px;color:#C2D2C8}
.dph i{display:block;width:52px;height:52px;opacity:.55}
.dph i svg{width:100%;height:100%}
.dph img{width:100%;height:auto;display:block}
.dcard{background:var(--card);border:1px solid var(--mist);border-radius:var(--r);
 padding:16px;margin-bottom:11px}
.eb{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:600;
 color:#0A6238;background:#E9F4EE;border-radius:13px;padding:5px 11px;margin-bottom:11px}
.eb svg{width:15px;height:15px}
.dp{font-family:"Manrope",system-ui,sans-serif;font-size:29px;font-weight:800;
 letter-spacing:-1px;margin-bottom:5px;font-variant-numeric:tabular-nums}
.dpd{font-family:"Golos Text",system-ui,sans-serif;font-size:21px;font-weight:600;
 color:var(--leaf);letter-spacing:-.2px}
.dcard h1{font-size:18px;line-height:1.32;font-weight:600;margin:0 0 15px}
.f{display:flex;flex-direction:column;gap:1px;background:var(--mist);
 border-radius:13px;overflow:hidden;border:1px solid var(--mist)}
.f>div{display:flex;justify-content:space-between;gap:12px;background:var(--card);
 padding:11px 13px;font-size:13.5px}
.f b{font-weight:500;color:var(--faint)}
.f span{font-weight:500;text-align:right}
.d{margin:0;font-size:14.5px;line-height:1.55;white-space:pre-wrap;color:#2A3B32}
.btn{display:flex;align-items:center;justify-content:center;gap:8px;
 background:var(--leaf);color:#fff;border-radius:15px;padding:15px;
 font-size:16px;font-weight:600;box-shadow:0 5px 16px rgba(18,160,92,.28);
 margin-bottom:14px}
.btn svg{width:19px;height:19px}
.btn span{font-family:"Manrope",system-ui,sans-serif;font-weight:700;
 font-variant-numeric:tabular-nums;letter-spacing:.2px}
.btn:active{transform:scale(.985)}

/* ---- Бош барак ---- */
.em{text-align:center;padding:52px 22px 34px}
.em i{display:block;width:76px;height:76px;margin:0 auto 20px;color:#C6D6CC}
.em i svg{width:100%;height:100%}
.em h2{font-size:18px;font-weight:600;margin:0 0 7px;letter-spacing:-.2px}
.em p{font-size:14px;color:var(--soft);margin:0 0 22px;line-height:1.5}
.dk{display:inline-block;background:var(--ink);color:#fff;border-radius:15px;
 padding:13px 26px;font-size:14.5px;font-weight:600}

/* ---- Ылдыйкы тилке ---- */
.nav{position:fixed;left:0;right:0;bottom:0;background:rgba(255,255,255,.97);
 backdrop-filter:saturate(180%) blur(14px);border-top:1px solid var(--mist);
 display:flex;padding:7px 0 max(7px,env(safe-area-inset-bottom));z-index:30}
.nav a{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;
 font-size:10.5px;font-weight:500;color:var(--faint)}
.nav a svg{width:22px;height:22px}
.nav a.on{color:var(--leaf);font-weight:600}

@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
:focus-visible{outline:2.5px solid var(--leaf);outline-offset:2px;border-radius:6px}
"""
