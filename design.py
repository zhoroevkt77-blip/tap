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
  --ink    #152741  негизги текст (кара эмес, жашылга тартылган)
  --moss   #17365C  терең жашыл — башкы тилке
  --leaf   #B0862B  бренд жашылы — басым
  --wheat  #C9A03A  буудай сарысы — баа жана акцент
  --paper  #F1F4F9  фон
  --mist   #E1E7F1  чек сызыктар
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
    "help": _N + '<circle cx="12" cy="12" r="8.6"/>'
                 '<path d="M9.6 9.4a2.5 2.5 0 1 1 3.3 2.4c-.6.2-.9.8-.9 1.4v.5"/>'
                 '<path d="M12 17.1h.01"/></svg>',
}

# Ботсуз иштей турган бет — «Тандалган» гана. Калган үчөө ботко алып барат,
# анткени жарыя коюу, кат жазуу жана өз жарыяларын башкаруу ошол жерде болот.
BOT = os.environ.get("BOT_USERNAME", "TapmeniBot").lstrip("@")


def nav(active="home", lang="ky"):
    from strings import T
    items = [
        ("home", "/",                              NAV_ICONS["home"], T("nav_home", lang)),
        ("fav",  "/fav",                           NAV_ICONS["fav"],  T("nav_fav", lang)),
        ("add",  "/add",                          NAV_ICONS["add"],  T("nav_add", lang)),
        ("msg",  "/msg",                           NAV_ICONS["help"], T("nav_msg", lang)),
        ("me",   "/me",                            NAV_ICONS["me"],   T("nav_me", lang)),
    ]
    out = ""
    for key, href, ic, label in items:
        cls = ' class="on"' if key == active else ""
        out += f'<a href="{href}"{cls}>{ic}<span>{label}</span></a>'
    return f'<nav class="nav">{out}</nav>'


CSS = """
:root{
 --ink:#152741; --soft:#5A6982; --faint:#8B97AC;
 --moss:#17365C; --leaf:#17365C; --wheat:#C9A03A;
 --paper:#F1F4F9; --card:#FFFDF7; --mist:#E1E7F1;
 --gold:#C9A03A; --gold2:#E3C368; --cream:#FBF5E6;
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
.top{background:url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='90' height='90' viewBox='0 0 90 90'><g fill='none' stroke='%23ffffff' stroke-opacity='.12' stroke-width='2' stroke-linecap='round'><path d='M45 8c-9 0-14 7-14 14s6 12 14 12 14-5 14-12-5-14-14-14z'/><path d='M45 34v22'/><path d='M31 56c0 8 6 14 14 14s14-6 14-14'/><circle cx='45' cy='22' r='4'/></g></svg>\") right -14px top -10px/150px repeat-y,linear-gradient(168deg,#1E4574 0%,#17365C 62%,#122B4C 100%);
 color:#fff;padding:10px 0 16px;position:sticky;top:0;z-index:20}
.tin{display:flex;align-items:center;gap:11px;padding:3px 0 13px}
.logo{display:flex;align-items:center;font-family:"Manrope",system-ui,sans-serif;
 font-weight:800;font-size:23px;letter-spacing:-.8px;flex:none}
.pin{font-size:13px;font-weight:500;background:rgba(255,255,255,.15);
 border:1px solid rgba(255,255,255,.14);padding:6px 12px;border-radius:15px;
 display:flex;align-items:center;gap:5px;max-width:44%;min-width:0;
 overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pin b{font-weight:400;opacity:.85;font-size:12px}
/* Тил алмаштыруу — оң четте, кичине, бирок басууга ыңгайлуу */
.lgs{margin-left:auto;display:flex;background:rgba(255,255,255,.14);
 border:1px solid rgba(255,255,255,.16);border-radius:13px;padding:2px;flex:none}
.lg{padding:4px 9px;font-size:11.5px;font-weight:600;border-radius:11px;
 color:rgba(255,255,255,.78);letter-spacing:.3px;line-height:1.3}
.lg.on{background:#fff;color:var(--moss)}
.lang{margin-left:auto;flex:none;font-size:12px;font-weight:700;letter-spacing:.4px;
 background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.2);
 padding:6px 11px;border-radius:14px}
.s{display:flex;align-items:center;gap:9px;background:#fff;border-radius:26px;
 padding:0 5px 0 15px;height:48px;box-shadow:0 3px 14px rgba(12,30,60,.16)}
.s .mg{flex:none;width:20px;height:20px;color:var(--faint)}
.s .mg svg{width:100%;height:100%;display:block}
.s input{flex:1;min-width:0;border:0;font-size:16px;font-family:inherit;
 background:transparent;padding:0;color:var(--ink)}
.s input:focus{outline:none}
.s input::placeholder{color:var(--faint)}
.s button{border:0;background:linear-gradient(180deg,var(--gold2),var(--gold));color:#14243F;height:38px;padding:0 18px;
 border-radius:19px;font-size:14px;font-weight:600;font-family:inherit;cursor:pointer}
.s button:active{transform:scale(.97)}

/* ---- Бөлүмдөр ---- */
.cats{display:flex;gap:8px;overflow-x:auto;padding:16px 14px 10px;
 scrollbar-width:none;max-width:1040px;margin:0 auto}
.cats::-webkit-scrollbar{display:none}
.cat{flex:none;width:94px;border-radius:15px;overflow:hidden;background:var(--card);
 border:1px solid var(--mist);transition:.18s;
 box-shadow:0 2px 5px rgba(18,32,58,.05),0 10px 20px -12px rgba(18,32,58,.18)}
.cat .ic{display:block;width:94px;height:74px;overflow:hidden}
.cat .ic svg{width:100%;height:100%;display:block}
.cat .lb{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
 overflow:hidden;padding:7px 6px 8px;font-size:11.5px;line-height:1.22;
 font-weight:600;color:var(--ink);text-align:center;min-height:38px}
/* Сүрөттүү бөлүм тактасы: сүрөт бүт тактаны ээлейт, аты сүрөттө жазылган */
.cat.pic{border:0;background:none;padding:0;overflow:hidden;
 width:104px;height:126px;border-radius:16px}
.cat.pic .pic{width:100%;height:100%;object-fit:cover;display:block}
.cat.pic.on{box-shadow:0 0 0 3px var(--gold),0 10px 22px -12px rgba(18,32,58,.5)}

.cat.on{border-color:var(--gold);
 box-shadow:0 0 0 2px var(--gold),0 10px 22px -12px rgba(14,34,64,.4)}
.cat.on .lb{background:transparent;color:var(--ink);font-weight:700}
.cat.on .ic{background:linear-gradient(160deg,#FFFFFF 0%,#E7EEF9 100%);
 border-bottom:1px solid #C9D6EA}
/* Тандалганда белги караңгы тактын үстүндө жарык болуп калат —
   үч катмар актын үч даражасына айланып, көлөмү сакталат. */
.cat.on .ic svg [data-t="lite"]{fill:#FFFFFF;stroke:#FFFFFF}
.cat.on .ic svg [data-t="mid"] {fill:#BFCFE8;stroke:#BFCFE8}
.cat.on .ic svg [data-t="deep"]{fill:#1B3355;stroke:#1B3355}
/* Тешик так менен бирдей түстө болсун — ичи көрүнүп турсун */
.cat.on .ic svg [data-t="hole"]{fill:#264873}
.cat.on{color:var(--ink);font-weight:600}

/* ---- Чыпкалар ---- */
/* ---- Жарыянын барагындагы катарлар ---- */
.facts{padding:0 15px}
.fr{display:flex;gap:11px;align-items:flex-start;padding:8px 0;
 border-bottom:1px solid #EEF2F8}
.fr:last-child{border-bottom:0}
.fr svg{flex:none;width:18px;height:18px;stroke:var(--moss);fill:none;
 stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;margin-top:2px;opacity:.8}
.ft{flex:1;min-width:0}
.ft i{display:block;font-style:normal;font-size:11.5px;color:var(--faint);
 font-weight:600;margin-bottom:0;line-height:1.3}
.ft b{display:block;font-size:14.5px;font-weight:700;line-height:1.3}
.ft b.dtx{font-weight:500;font-size:14.5px;line-height:1.45;white-space:pre-line}

/* ---- Чыпка тизмелери ---- */
.fbox{background:#fff;border-top:1px solid var(--mist);
 border-bottom:1px solid var(--mist);padding:12px 14px 14px;margin-bottom:8px}
.fhd{font-size:11px;font-weight:800;letter-spacing:.5px;text-transform:uppercase;
 color:var(--moss);margin:0 0 9px;display:flex;align-items:center;gap:7px}
.fhd::after{content:"";flex:1;height:1px;background:var(--mist)}
.ff{margin-bottom:9px}
.ff:last-child{margin-bottom:0}
.ff label{display:block;font-size:11px;font-weight:700;letter-spacing:.4px;
 text-transform:uppercase;color:var(--faint);margin:0 0 5px}
.sel{width:100%;-webkit-appearance:none;appearance:none;
 background:#fff url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 14 14'><path d='M3 5l4 4 4-4' fill='none' stroke='%2317365C' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>") no-repeat right 14px center;
 border:1.5px solid var(--mist);border-radius:13px;padding:13px 40px 13px 14px;
 font-size:15px;font-weight:600;color:var(--ink);font-family:inherit}
.sel:focus{outline:none;border-color:var(--moss)}
.sel.set{border-color:var(--moss);background-color:#F7FAFF}

/* ---- Аймак панели ---- */
.regbox{background:#fff;border-top:1px solid var(--mist);
 border-bottom:1px solid var(--mist);margin:0 0 4px}
.regbox>summary{list-style:none;cursor:pointer}
.regbox>summary::-webkit-details-marker{display:none}
.rgsum{display:flex;align-items:center;justify-content:space-between;
 gap:10px;padding:12px 14px;font-size:14px;font-weight:700;color:var(--ink)}
.rgs1{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rgs2{flex:none;font-size:12.5px;font-weight:600;color:var(--gold)}
.rgs2::after{content:" \25BE"}
.regbox[open] .rgs2::after{content:" \25B4"}
.regbox[open] .rgsum{border-bottom:1px solid var(--mist)}
.regin{padding-bottom:6px}
.rglb{padding:9px 14px 0;font-size:11px;font-weight:700;letter-spacing:.4px;
 text-transform:uppercase;color:var(--faint)}
.regbar,.subbar{display:flex;gap:7px;overflow-x:auto;padding:7px 14px 2px;
 scrollbar-width:none;max-width:1040px;margin:0 auto}
.regbar::-webkit-scrollbar,.subbar::-webkit-scrollbar{display:none}
.rg{flex:none;background:var(--card);border:1px solid var(--mist);border-radius:16px;
 padding:7px 14px;font-size:12.5px;font-weight:500;color:var(--soft);white-space:nowrap}
.rg.on{background:var(--ink);color:#fff;border-color:var(--ink);font-weight:600}
.sb2{flex:none;background:#EEF3FB;border:1px solid #D6E2F3;border-radius:16px;
 padding:7px 14px;font-size:12.5px;font-weight:500;color:#14304F;white-space:nowrap}
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
.c{background:var(--card);border:1px solid #EBE3D0;border-radius:var(--r);
 overflow:hidden;display:flex;flex-direction:column;transition:.16s}
.c:active{transform:scale(.985)}
.ph{position:relative;aspect-ratio:16/11;background:#EDF1F8;overflow:hidden;
 display:flex;align-items:center;justify-content:center;color:#C7D2E4}
.ph i{display:block;width:30px;height:30px;opacity:.45}
.ph i svg{width:100%;height:100%}
.ph img{position:absolute;inset:0;width:100%;height:100%;
 object-fit:cover;display:block}
.c.nophoto .ph{aspect-ratio:16/11}
.fav{position:absolute;top:9px;right:9px;width:33px;height:33px;border-radius:50%;
 background:rgba(255,255,255,.94);display:flex;align-items:center;justify-content:center;
 color:var(--faint);box-shadow:0 1px 4px rgba(18,32,58,.1);border:0;padding:0;
 cursor:pointer;transition:.15s}
.fav svg{width:17px;height:17px;transition:.15s}
.fav{color:var(--gold)}
.fav.on{color:var(--gold)}
.fav svg{fill:none}
.fav.on svg{fill:var(--gold);transform:scale(1.12)}
.fav:active{transform:scale(.88)}
.cb{padding:11px 12px 13px;display:flex;flex-direction:column;flex:1}
.p{font-family:"Manrope",system-ui,sans-serif;font-size:18px;font-weight:800;
 letter-spacing:-.4px;margin-bottom:5px;font-variant-numeric:tabular-nums}
.pd{font-family:"Golos Text",system-ui,sans-serif;font-size:15.5px;font-weight:700;
 color:var(--leaf);letter-spacing:0}
.rg{font-size:12px;font-weight:600;color:var(--moss);opacity:.82;line-height:1.35;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rg2{opacity:.62;font-weight:500}
.rg+.t,.rg2+.t{margin-top:6px}
.t{font-size:13.5px;line-height:1.38;margin:0 0 10px;font-weight:400;color:var(--soft);
 display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.m{margin-top:auto;display:flex;gap:8px;align-items:center;font-size:11.5px;
 color:var(--faint);white-space:nowrap}
.m span:first-child{color:var(--gold);font-weight:600}
.m span:first-child{overflow:hidden;text-overflow:ellipsis}
.m .vw{margin-left:auto;display:flex;align-items:center;gap:3px}
.m .vw svg{width:13px;height:13px}

/* ---- Бөлүмдөрдүн катарлары (башкы бет) ---- */
.shelf{padding:20px 0 4px}
.shead{display:flex;align-items:baseline;gap:10px;padding:0 0 9px}
.shead h2{font-size:17px;font-weight:700;margin:0;letter-spacing:-.3px}
.shead .more{margin-left:auto;font-size:13px;color:var(--leaf);font-weight:600;
 white-space:nowrap}
.shchips{padding:0 0 11px;margin:0}
.shchips .sb2{font-family:inherit;cursor:pointer}
.srow{display:flex;gap:11px;overflow-x:auto;scroll-snap-type:x proximity;
 padding-bottom:4px;scrollbar-width:none;-webkit-overflow-scrolling:touch}
.srow::-webkit-scrollbar{display:none}
.srow>.c{flex:0 0 46%;scroll-snap-align:start}
@media(min-width:620px){.srow>.c{flex:0 0 30%}}
@media(min-width:900px){.srow>.c{flex:0 0 23%}}
.srow.load{opacity:.45;transition:.15s}

/* ---- Толук барак ---- */
.back{display:inline-flex;align-items:center;gap:6px;padding:15px 0 9px;
 font-size:14px;color:var(--leaf);font-weight:600}
.dph{background:var(--card);border:1px solid var(--mist);border-radius:var(--r);
 overflow:hidden;margin-bottom:11px;display:flex;align-items:center;
 justify-content:center;min-height:150px;max-height:min(52vh,430px);
 color:#C7D2E4}
.dph i{display:block;width:52px;height:52px;opacity:.55}
.dph i svg{width:100%;height:100%}
.dph img{width:100%;height:auto;max-height:min(52vh,430px);
 object-fit:contain;display:block}
.dcard{background:var(--card);border:1px solid var(--mist);border-radius:var(--r);
 padding:16px;margin-bottom:11px}
.eb{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:600;
 color:#14304F;background:#EEF3FB;border-radius:13px;padding:5px 11px;margin-bottom:11px}
.eb svg{width:15px;height:15px}
.dp{font-family:"Manrope",system-ui,sans-serif;font-size:29px;font-weight:800;
 letter-spacing:-1px;margin-bottom:5px;font-variant-numeric:tabular-nums}
/* Толук баракта «Келишим баада» баа эмес, шарт — ошондуктан
   категориянын атынан да кичине, басымсыз турат. */
.dpd{font-family:"Golos Text",system-ui,sans-serif;font-size:15px;font-weight:600;
 color:var(--leaf);letter-spacing:0;margin-bottom:9px}
.dcard h1{font-size:18px;line-height:1.32;font-weight:600;margin:0 0 15px}
.f{display:flex;flex-direction:column;gap:1px;background:var(--mist);
 border-radius:13px;overflow:hidden;border:1px solid var(--mist)}
.f>div{display:flex;justify-content:space-between;gap:12px;background:var(--card);
 padding:11px 13px;font-size:13.5px}
.f b{font-weight:500;color:var(--faint)}
.f span{font-weight:500;text-align:right}
.d{margin:0;font-size:14.5px;line-height:1.55;white-space:pre-wrap;color:#243352}
/* ---- Байланыш баскычтары ---- */
.cbar{display:flex;gap:8px;margin-bottom:16px}
.cb1{flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;
 justify-content:center;gap:5px;height:64px;border-radius:15px;color:#fff;
 font-size:12.5px;font-weight:600;text-align:center;padding:0 4px}
.cb1 svg{width:22px;height:22px;flex:none}
.cb1 span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%}
.cb1:active{transform:scale(.97)}
.cb1.call{background:var(--leaf);box-shadow:0 4px 12px rgba(176,134,43,.26)}
.cb1.wa{background:#22C15E;box-shadow:0 4px 12px rgba(34,193,94,.24)}
.cb1.tg{background:#2AA3DA;box-shadow:0 4px 12px rgba(42,163,218,.24)}
.cnum{text-align:center;font-family:"Manrope",system-ui,sans-serif;font-weight:800;
 font-size:19px;letter-spacing:.2px;color:var(--ink);
 font-variant-numeric:tabular-nums;margin:2px 0 10px}

.btn{display:flex;align-items:center;justify-content:center;gap:8px;
 background:var(--leaf);color:#fff;border-radius:15px;padding:15px;
 font-size:16px;font-weight:600;box-shadow:0 5px 16px rgba(176,134,43,.28);
 margin-bottom:14px}
.btn svg{width:19px;height:19px}
.btn span{font-family:"Manrope",system-ui,sans-serif;font-weight:700;
 font-variant-numeric:tabular-nums;letter-spacing:.2px}
.btn:active{transform:scale(.985)}

/* ---- Аймак боюнча издөө жана Билдирүү барагы ---- */
.ftitle{font-size:23px;font-weight:700;letter-spacing:-.5px;margin:20px 0 6px}
.flead{font-size:14.5px;color:var(--soft);margin:0 0 16px;line-height:1.5}
.fsearch{display:flex;gap:8px;margin:0 0 20px}
.fsearch input{flex:1;min-width:0;height:46px;border:1px solid var(--mist);
 border-radius:15px;padding:0 15px;font-size:15px;font-family:inherit;
 background:var(--card);color:var(--ink)}
.fsearch input:focus{outline:none;border-color:var(--leaf)}
.fsearch input::placeholder{color:var(--faint)}
.fsearch button{border:0;background:var(--ink);color:#fff;height:46px;padding:0 20px;
 border-radius:15px;font-size:14.5px;font-weight:600;font-family:inherit;flex:none}
.fstep{font-size:12px;font-weight:600;color:var(--faint);text-transform:uppercase;
 letter-spacing:.6px;margin:0 0 9px}
.flist{background:var(--card);border:1px solid var(--mist);border-radius:var(--r);
 overflow:hidden;margin-bottom:16px}
.frow{display:flex;align-items:center;gap:12px;padding:15px 16px;font-size:15px;
 border-bottom:1px solid var(--mist)}
.frow:last-child{border-bottom:0}
.frow:active{background:#F2F5FA}
.fchev{margin-left:auto;color:var(--faint);font-size:20px;line-height:1}
.fnote{font-size:14px;color:var(--soft);padding:18px 16px;margin:0}
.fskip{display:block;text-align:center;margin-bottom:20px}
.qh{font-size:15.5px;font-weight:600;margin:0 0 7px;letter-spacing:-.1px}
.qp{font-size:14.5px;line-height:1.55;color:#243352;margin:0}

/* ---- Бөлүм катарлары (башкы бет) ---- */
.shelf{margin:26px 0 4px}
.shead{display:flex;align-items:baseline;gap:10px;padding:0 0 10px}
.shead h2{font-size:19px;font-weight:700;letter-spacing:-.4px;margin:0}
.more{margin-left:auto;font-size:13px;font-weight:600;color:var(--leaf);
 white-space:nowrap;flex:none}
.shchips{padding:0 0 11px!important;margin:0!important}
.shchips .sb2{border:1px solid #D6E2F3;cursor:pointer;font-family:inherit}
.srow{display:flex;gap:11px;overflow-x:auto;scroll-snap-type:x proximity;
 scrollbar-width:none;padding-bottom:4px;transition:opacity .15s}
.srow::-webkit-scrollbar{display:none}
.srow.load{opacity:.4}
.srow .c{flex:0 0 47%;scroll-snap-align:start}
@media(min-width:620px){.srow .c{flex:0 0 31%}}
@media(min-width:900px){.srow .c{flex:0 0 23%}}

/* ---- Бош барак ---- */
.em{text-align:center;padding:52px 22px 34px}
.em i{display:block;width:76px;height:76px;margin:0 auto 20px;color:#CBD6E6}
.em i svg{width:100%;height:100%}
.em h2{font-size:18px;font-weight:600;margin:0 0 7px;letter-spacing:-.2px}
.em p{font-size:14px;color:var(--soft);margin:0 0 22px;line-height:1.5}
.dk{display:inline-block;background:var(--ink);color:#fff;border-radius:15px;
 padding:13px 26px;font-size:14.5px;font-weight:600}

/* ---- Ылдыйкы тилке ---- */
.nav{position:fixed;left:0;right:0;bottom:0;
 background:linear-gradient(180deg,#1B3D68,#12294A);
 border-top:1px solid #0E2340;
 display:flex;padding:8px 0 max(8px,env(safe-area-inset-bottom));z-index:30}
.nav a{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;
 font-size:10.5px;font-weight:500;color:#B8C7DD}
.nav a svg{width:22px;height:22px}
.nav a:nth-child(1) svg{color:#7FB2F0}
.nav a:nth-child(2) svg{color:#F07A72}
.nav a:nth-child(3) svg{color:#5BC98A}
.nav a:nth-child(4) svg{color:#A38BE8}
.nav a:nth-child(5) svg{color:#E0C267}
.nav a.on{color:#fff;font-weight:700}

@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
:focus-visible{outline:2.5px solid var(--leaf);outline-offset:2px;border-radius:6px}
"""
