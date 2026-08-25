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


# ── Бөлүмдөрдүн белгилери ────────────────────────────────────
# Баары 24x24, сызык 1.8, учтары жумшак.

_S = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
      'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
      'aria-hidden="true">')

ICONS = {
    # Баары — төрт квадрат
    "all": _S + '<rect x="3.5" y="3.5" width="7" height="7" rx="2"/>'
                '<rect x="13.5" y="3.5" width="7" height="7" rx="2"/>'
                '<rect x="3.5" y="13.5" width="7" height="7" rx="2"/>'
                '<rect x="13.5" y="13.5" width="7" height="7" rx="2"/></svg>',

    # Соода-сатык — базар куржуну
    "trade": _S + '<path d="M4 8h16l-1.3 11.2a2 2 0 0 1-2 1.8H7.3a2 2 0 0 1-2-1.8L4 8Z"/>'
                  '<path d="M8.5 8V6a3.5 3.5 0 0 1 7 0v2"/>'
                  '<path d="M9.5 12v1.5M14.5 12v1.5"/></svg>',

    # Кызмат көрсөтүү — ачкыч менен балка
    "service": _S + '<path d="M14.5 3.5a4.5 4.5 0 0 0-4 6.6L3.8 16.8a1.8 1.8 0 0 0 2.5 2.5l6.7-6.7'
                    'a4.5 4.5 0 0 0 5.6-6.2l-2.6 2.6-2.4-.6-.6-2.4 2.6-2.6a4.5 4.5 0 0 0-1.1-.2Z"/>'
                    '</svg>',

    # Ижарага берүү — ачкыч
    "rental": _S + '<circle cx="8" cy="8" r="4.5"/>'
                   '<path d="M11.3 11.3 20 20"/><path d="M17 17l2-2"/>'
                   '<path d="M14.5 14.5l2-2"/></svg>',

    # Жеткирүү — куту
    "delivery": _S + '<path d="M3.5 7.8 12 3.5l8.5 4.3v8.4L12 20.5l-8.5-4.3V7.8Z"/>'
                     '<path d="M3.5 7.8 12 12l8.5-4.2"/><path d="M12 12v8.5"/>'
                     '<path d="M7.7 5.6 16.3 10"/></svg>',

    # Жумуш берүү — портфель
    "job": _S + '<rect x="2.8" y="7" width="18.4" height="13" rx="2.4"/>'
                '<path d="M8.6 7V5.4a2 2 0 0 1 2-2h2.8a2 2 0 0 1 2 2V7"/>'
                '<path d="M2.8 12.4c2.8 1.4 5.8 2.1 9.2 2.1s6.4-.7 9.2-2.1"/>'
                '<path d="M12 13.6v1.8"/></svg>',

    # Базарлар — соода катарынын чатыры
    "markets": _S + '<path d="M3.2 9.2 5 4.5h14l1.8 4.7"/>'
                    '<path d="M3.2 9.2c0 1.5 1.1 2.6 2.5 2.6s2.5-1.1 2.5-2.6c0 1.5 1.1 2.6 2.5 2.6'
                    's2.5-1.1 2.5-2.6c0 1.5 1.1 2.6 2.5 2.6s2.5-1.1 2.5-2.6"/>'
                    '<path d="M5 11.8V19a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 19v-7.2"/>'
                    '<path d="M9.8 20.5v-4.3h4.4v4.3"/></svg>',

    # Такси — үстүндө белгиси бар унаа
    "taxi": _S + '<path d="M3.5 16.5v-3.2l1.9-4.2A2 2 0 0 1 7.2 8h9.6a2 2 0 0 1 1.8 1.1l1.9 4.2v3.2"/>'
                 '<path d="M3.5 13.3h17"/>'
                 '<circle cx="7.2" cy="16.6" r="1.6"/><circle cx="16.8" cy="16.6" r="1.6"/>'
                 '<path d="M9.5 8V5.8h5V8"/></svg>',
}

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

NAV = ('<nav class="nav">'
       f'<a href="/" class="on">{NAV_ICONS["home"]}<span>Башкы бет</span></a>'
       f'<a href="/">{NAV_ICONS["fav"]}<span>Тандалган</span></a>'
       f'<a href="/">{NAV_ICONS["add"]}<span>Жарыя берүү</span></a>'
       f'<a href="/">{NAV_ICONS["msg"]}<span>Билдирүү</span></a>'
       f'<a href="/">{NAV_ICONS["me"]}<span>Кабинет</span></a>'
       '</nav>')


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
.cat .ic{width:56px;height:56px;border-radius:19px;background:var(--card);
 border:1px solid var(--mist);display:flex;align-items:center;justify-content:center;
 margin:0 auto 7px;color:var(--moss);transition:.18s}
.cat .ic svg{width:25px;height:25px}
.cat .lb{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
 overflow:hidden;height:29px}
.cat.on .ic{background:var(--moss);border-color:var(--moss);color:#fff;
 box-shadow:0 5px 14px rgba(11,110,63,.28)}
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
.fav{position:absolute;top:9px;right:9px;width:32px;height:32px;border-radius:50%;
 background:rgba(255,255,255,.94);display:flex;align-items:center;justify-content:center;
 color:var(--faint);box-shadow:0 1px 4px rgba(16,35,26,.1)}
.fav svg{width:17px;height:17px}
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
