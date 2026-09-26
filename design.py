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
    'family=Onest:wght@400;500;600;700;800&'
    'family=Inter:wght@400;500;600;700;800&'
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
    "wallet": _N + '<rect x="3" y="6" width="18" height="13" rx="2.4"/>'
                   '<path d="M3 10h18"/><circle cx="17" cy="14.5" r="1.2"/></svg>',
    "msg":  _N + '<rect x="3" y="5.2" width="18" height="13.6" rx="2.4"/>'
                 '<path d="m3.6 6.6 7.3 5.3a2 2 0 0 0 2.2 0l7.3-5.3"/></svg>',
    "me":   _N + '<circle cx="12" cy="8.4" r="3.8"/>'
                 '<path d="M4.8 20.4a7.2 7.2 0 0 1 14.4 0"/></svg>',
    "help": _N + '<circle cx="12" cy="12" r="8.6"/>'
                 '<path d="M9.6 9.4a2.5 2.5 0 1 1 3.3 2.4c-.6.2-.9.8-.9 1.4v.5"/>'
                 '<path d="M12 17.1h.01"/></svg>',
    # ── Кабинеттин катарлары үчүн ──
    "grid": _N + '<rect x="3.4" y="3.4" width="7.2" height="7.2" rx="1.6"/>'
                 '<rect x="13.4" y="3.4" width="7.2" height="7.2" rx="1.6"/>'
                 '<rect x="3.4" y="13.4" width="7.2" height="7.2" rx="1.6"/>'
                 '<rect x="13.4" y="13.4" width="7.2" height="7.2" rx="1.6"/></svg>',
    "search": _N + '<circle cx="10.8" cy="10.8" r="6.6"/>'
                   '<path d="m15.6 15.6 4.2 4.2"/></svg>',
    "list": _N + '<rect x="4" y="3.6" width="16" height="16.8" rx="2.2"/>'
                 '<path d="M8 9h8M8 12.6h8M8 16.2h5"/></svg>',
    "globe": _N + '<circle cx="12" cy="12" r="8.6"/><path d="M3.6 12h16.8"/>'
                  '<path d="M12 3.4c2.2 2.4 3.3 5.4 3.3 8.6s-1.1 6.2-3.3 8.6'
                  'c-2.2-2.4-3.3-5.4-3.3-8.6S9.8 5.8 12 3.4Z"/></svg>',
    "doc": _N + '<path d="M13.4 3.6H7a2 2 0 0 0-2 2v12.8a2 2 0 0 0 2 2h10'
                'a2 2 0 0 0 2-2V9.2Z"/><path d="M13.4 3.6V9.2H19"/></svg>',
    "tg":  _N + '<path d="m21 4.6-2.9 14.2c-.2 1-.8 1.2-1.6.8l-4.4-3.3-2.1 2'
                'c-.2.2-.4.4-.9.4l.3-4.5 8.2-7.4c.4-.3-.1-.5-.6-.2L6.9 12.3'
                'l-4.3-1.4c-.9-.3-.9-.9.2-1.4l16.8-6.5c.8-.3 1.5.2 1.4 1.6Z"/></svg>',
    "wa":  _N + '<path d="M20.2 11.6a8.2 8.2 0 0 1-12.2 7.1L3.8 20l1.3-4.1'
                'a8.2 8.2 0 1 1 15.1-4.3Z"/>'
                '<path d="M9.2 9.1c.3-.7.6-.7.9-.7h.7c.2 0 .5 0 .8.6l1 2.3'
                'c.1.3.1.5 0 .7l-.4.6c-.1.2-.3.4-.1.7.5.8 1.4 1.7 2.4 2.2'
                '.3.2.5.1.7-.1l.6-.7c.2-.2.4-.2.7-.1l2 1c.3.2.4.3.4.5'
                'a2 2 0 0 1-1.4 1.6c-.6.1-1.4.2-4-.9-2.9-1.2-4.6-4.2-4.7-4.4'
                '-.2-.3-1.1-1.5-1.1-2.8 0-1.3.7-1.9 1-2.2Z"/></svg>',
    "ig":  _N + '<rect x="3.6" y="3.6" width="16.8" height="16.8" rx="4.6"/>'
                '<circle cx="12" cy="12" r="4"/><path d="M16.9 7.1h.01"/></svg>',
    "fb":  _N + '<path d="M14.8 8.4h2.4V5.2h-2.4a4 4 0 0 0-4 4v2h-2.2v3.2h2.2'
                'v6.4h3.2v-6.4h2.4l.6-3.2h-3v-2c0-.4.3-.8.8-.8Z"/></svg>',
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
        c = ["on"] if key == active else []
        if key == "add":
            c.append("fab")
        cls = ' class="%s"' % " ".join(c) if c else ""
        out += f'<a href="{href}"{cls}>{ic}<span>{label}</span></a>'
    return f'<nav class="nav">{out}</nav>'


CSS = """
:root{
 --ink:#152741; --soft:#33425A; --faint:#4E5B72;
 --moss:#17365C; --leaf:#17365C; --wheat:#C9A03A;
 --paper:#F1F4F9; --card:#F7FBFF; --mist:#E1E7F1;
 --gold:#C9A03A; --gold2:#E3C368; --cream:#FBF5E6;
 --heart:#F07A72;
 --r:18px;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);
 font-family:"Onest","Inter",-apple-system,"Segoe UI",Roboto,system-ui,sans-serif;
 font-size:15px;line-height:1.45;font-weight:400;padding-bottom:74px;
 -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
a{color:inherit;text-decoration:none}
svg{display:block}
.wrap{max-width:1040px;margin:0 auto;padding:0 14px}
/* Жаңы бет ачылганда мазмун жумшак пайда болот — бөлүмдөн бөлүмгө
   өтүү секирип эмес, агылып өткөндөй сезилет. */
@keyframes pageIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
main.wrap{animation:pageIn .26s ease-out both}

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
.pin b{font-weight:600;opacity:1;font-size:12px}
/* Тил алмаштыруу — оң четте, кичине, бирок басууга ыңгайлуу */
.lgs{margin-left:auto;display:flex;background:rgba(255,255,255,.14);
 border:1px solid rgba(255,255,255,.16);border-radius:13px;padding:2px;flex:none}
.lg{padding:4px 9px;font-size:11.5px;font-weight:600;border-radius:11px;
 color:rgba(255,255,255,.96);letter-spacing:.3px;line-height:1.3}
.lg.on{background:#fff;color:var(--moss)}
.lang{margin-left:auto;flex:none;font-size:12px;font-weight:700;letter-spacing:.4px;
 background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.2);
 padding:6px 11px;border-radius:14px}
.s{display:flex;align-items:center;gap:9px;background:#fff;border-radius:26px;
 padding:0 5px 0 15px;height:48px;box-shadow:0 3px 14px rgba(12,30,60,0.27)}
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
 box-shadow:0 2px 5px rgba(18,32,58,0.14),0 10px 20px -12px rgba(18,32,58,0.32)}
.cat .ic{display:block;width:94px;height:74px;overflow:hidden}
.cat .ic svg{width:100%;height:100%;display:block}
.cat .lb{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
 overflow:hidden;padding:7px 6px 8px;font-size:11.5px;line-height:1.22;
 font-weight:600;color:var(--ink);text-align:center;min-height:38px}
/* Бөлүмдөр: эки катар торчо, ар биринде көлөмдүү белги, астында аты */
.cats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px 8px;
 overflow:visible;padding:14px 12px 10px;align-items:start}
.cat.pic{box-shadow:0 7px 18px rgba(16,24,40,.5);/*PICSHADOW2*/border:0;background:none;padding:0;overflow:visible;position:relative;
 width:auto;height:auto;border-radius:0;box-shadow:none;
 display:flex;flex-direction:column;align-items:center;gap:6px}
.cat.pic .picw{display:block;width:100%;flex:none;aspect-ratio:1/1;
 border-radius:14px;overflow:hidden;position:relative;background:#EDF2F9;
 transition:box-shadow .18s,transform .18s}
/* Сүрөттүн катышы кабыктыкы менен бирдей (340x430), ошондуктан
   толук батат — бош жер да, кыркылган жер да калбайт. */
.cat.pic .pic{width:100%;height:100%;object-fit:cover;display:block;
 border-radius:0}
/* Аталыш тактанын өз ичинде, ылдый жагында турат — сүрөт менен
   жазуу бир бүтүн карточка болуп көрүнөт. */
/* Аталыш сүрөттүн астында, өзүнчө баскычта — сүрөттү жаппайт */
.cat.pic .pill{display:flex;align-items:center;justify-content:center;
 overflow-wrap:anywhere;hyphens:auto;width:100%;flex:none;min-height:36px;
 padding:5px 6px;border-radius:999px;background:#fff;
 border:1px solid var(--mist);text-align:center;
 font-size:11.5px;font-weight:700;line-height:1.2;color:var(--ink);
 box-shadow:0 3px 8px -6px rgba(18,32,58,0.85)}
.cat.pic.on .picw{box-shadow:0 0 0 2.5px var(--moss)}
/* Аймак тандалганда бөлүмдүн бурчундагы жарыялардын саны */
.secn{position:absolute;top:5px;left:5px;z-index:2;min-width:19px;height:19px;
 padding:0 5px;border-radius:999px;background:var(--moss);color:#fff;
 font-size:10.5px;font-weight:700;line-height:19px;text-align:center;
 font-variant-numeric:tabular-nums;box-shadow:0 2px 6px -2px rgba(14,34,64,0.85)}
.cat{position:relative}
.cat.pic.on .pill{background:var(--moss);border-color:var(--moss);color:#fff}
/* Ар бир бөлүмдүн жазуусу үстүндөгү сүрөттүн өңүндө болсун */
.cat.s-all .pill{background:#DCEBFB;border-color:#C5DDF4}
.cat.s-trade .pill{background:#FCE7D2;border-color:#F3D5B8}
.cat.s-wholesale .pill{background:#E6DEFB;border-color:#D5C9F5}
.cat.s-property .pill{background:#D9EDFB;border-color:#C2DFF4}
.cat.s-vehicle .pill{background:#FCE7D2;border-color:#F3D5B8}
.cat.s-service .pill{background:#E4DDFA;border-color:#D2C8F3}
.cat.s-rental .pill{background:#D8F0DA;border-color:#BFE4C3}
.cat.s-delivery .pill{background:#D7EBFA;border-color:#BFDCF3}
.cat.s-cargo .pill{background:#E1E2FA;border-color:#CCCEF2}
.cat.s-jobseek .pill{background:#D8F0DE;border-color:#BFE4C9}
.cat.s-job .pill{background:#FBDDE2;border-color:#F3C6CE}
.cat.s-markets .pill{background:#FCEBC8;border-color:#F3DCAB}
.cat.s-malls .pill{background:#FBDDE2;border-color:#F3C6CE}
.cat.s-taxi .pill{background:#D8EEFB;border-color:#BFE0F4}

/* ── Бөлүмдөрдүн жандуулугу ────────────────────────────────
   Басканда такта ичине басылгандай кичирейет — манжага дароо
   жооп берет. Коё бергенде өз ордуна жумшак кайтат.            */
.cat.pic .picw{transition:transform .18s cubic-bezier(.34,1.4,.5,1),
 box-shadow .18s, filter .18s}
.cat.pic .pill{transition:transform .18s cubic-bezier(.34,1.4,.5,1),
 background .18s, color .18s, border-color .18s}
.cat.pic:active .picw{transform:scale(.9);filter:brightness(.94)}
.cat.pic:active .pill{transform:scale(.94)}
.cat:not(.pic):active{transform:scale(.93)}

/* Тандалганы бир аз өйдө көтөрүлүп, жай дем алгандай кыймылдап
   турат: көз ошого өзүнөн-өзү тартылат, бирок жети секунддук жай
   цикл болгондуктан жүдөтпөйт. */
.cat.pic.on .picw{transform:translateY(-3px) scale(1.03)}

/* ---- Сүрөттүн ичи жай жылып турат ----
   Сүрөт алкагынан бир аз чоң кылынып, акырын жылдырылат: мотоцикл
   жүрүп бараткандай, үй жанаша өткөндөй сезилет. Ар тактанын өз
   багыты жана өз ылдамдыгы бар — баары бир убакта бирдей кыймылдаса,
   көзгө жагымсыз болмок. 18-24 секунддук жай цикл: көзгө урунбайт,
   бирок бет тирүү көрүнөт. */
@keyframes drift1{
 0%  {transform:scale(1.03) translate(-0.9%, 0.8%)}
 50% {transform:scale(1.06) translate(1.0%, -0.9%)}
 100%{transform:scale(1.03) translate(-0.9%, 0.8%)}}
@keyframes drift2{
 0%  {transform:scale(1.06) translate(1.0%, 0.7%)}
 50% {transform:scale(1.03) translate(-0.9%, -0.8%)}
 100%{transform:scale(1.06) translate(1.0%, 0.7%)}}
@keyframes drift3{
 0%  {transform:scale(1.03) translate(0.8%, -0.9%)}
 50% {transform:scale(1.07) translate(-1.0%, 1.1%)}
 100%{transform:scale(1.03) translate(0.8%, -0.9%)}}

.cat.pic .pic{animation:drift1 22s ease-in-out infinite;will-change:transform}
.cat.pic:nth-child(3n+2) .pic{animation-name:drift2;animation-duration:19s}
.cat.pic:nth-child(3n) .pic{animation-name:drift3;animation-duration:25s}
.cat.pic:nth-child(4n) .pic{animation-delay:-6s}
.cat.pic:nth-child(4n+2) .pic{animation-delay:-11s}
.cat.pic:nth-child(4n+3) .pic{animation-delay:-3s}

/* Тандалганынын кыймылы кыйла сезилерлик — көз ошого тартылат */
@keyframes driftOn{
 0%  {transform:scale(1.04) translate(-1.3%, 1.1%)}
 50% {transform:scale(1.09) translate(1.5%, -1.3%)}
 100%{transform:scale(1.04) translate(-1.3%, 1.1%)}}
.cat.pic.on .pic{animation:driftOn 11s ease-in-out infinite}

/* Аты жазылган баскыч да тандалганда бир кыймылдап коёт */
@keyframes pillPop{
 0%{transform:scale(.9)} 60%{transform:scale(1.06)} 100%{transform:none}}
.cat.pic.on .pill{animation:pillPop .34s cubic-bezier(.34,1.5,.5,1) both}

/* Жарыясы бар бөлүмдүн саны басканда сезилерлик чоңоюп коёт */
@keyframes numPop{
 0%{transform:scale(.4);opacity:0} 70%{transform:scale(1.15)}
 100%{transform:none;opacity:1}}
.secn{animation:numPop .3s cubic-bezier(.34,1.5,.5,1) both}

/* Такталар бет ачылганда бирден өйдө калкып чыгат */
@keyframes tileUp{
 from{opacity:0;transform:translateY(10px) scale(.97)}
 to{opacity:1;transform:none}}
.cats .cat{animation:tileUp .34s cubic-bezier(.2,.8,.3,1) both}
.cats .cat:nth-child(1){animation-delay:.00s}
.cats .cat:nth-child(2){animation-delay:.03s}
.cats .cat:nth-child(3){animation-delay:.06s}
.cats .cat:nth-child(4){animation-delay:.09s}
.cats .cat:nth-child(5){animation-delay:.12s}
.cats .cat:nth-child(6){animation-delay:.15s}
.cats .cat:nth-child(7){animation-delay:.18s}
.cats .cat:nth-child(8){animation-delay:.21s}
.cats .cat:nth-child(9){animation-delay:.24s}
.cats .cat:nth-child(10){animation-delay:.27s}
.cats .cat:nth-child(11){animation-delay:.30s}
.cats .cat:nth-child(12){animation-delay:.33s}

.cat.on{border-color:var(--gold);
 box-shadow:0 0 0 2px var(--gold),0 10px 22px -12px rgba(14,34,64,0.70)}
/* Сүрөттүү тактада сырткы кыр керек эмес — сүрөттүн өз кыры жетиштүү */
.cat.pic.on{border:0;box-shadow:none}
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
.facts{padding:0 14px}
.fr{display:flex;gap:10px;align-items:flex-start;padding:5px 0;
 border-bottom:1px solid #F2F5FA}
.fr:last-child{border-bottom:0}
.fr svg{flex:none;width:16px;height:16px;stroke:var(--moss);fill:none;
 stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;margin-top:2px;opacity:.75}
.ft{flex:1;min-width:0}
.ft i{display:block;font-style:normal;font-size:11px;color:var(--faint);
 font-weight:600;margin-bottom:0;line-height:1.2}
.ft b{display:block;font-size:14px;font-weight:700;line-height:1.25}
.ft b.dtx{font-weight:500;font-size:14.5px;line-height:1.45;white-space:pre-line}

/* ---- Бөлүшүү ---- */
.share{display:flex;align-items:center;gap:9px;flex-wrap:wrap;
 margin:14px 0 4px;font-size:13px}
.share span{color:var(--faint);font-weight:600}
.share a{padding:8px 15px;border-radius:999px;background:#fff;
 border:1px solid var(--mist);color:var(--moss);font-weight:700;
 text-decoration:none}

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

/* Фильтр полосалары тандалган бөлүмдүн өңүндө */
.xoff-trade .sel{background-color:#FCE7D2}
.xoff-trade .sel.set{background-color:#FCE7D2}
.xoff-wholesale .sel{background-color:#E6DEFB}
.xoff-wholesale .sel.set{background-color:#E6DEFB}
.xoff-property .sel{background-color:#D9EDFB}
.xoff-property .sel.set{background-color:#D9EDFB}
.xoff-service .sel{background-color:#E4DDFA}
.xoff-service .sel.set{background-color:#E4DDFA}
.xoff-rental .sel{background-color:#D8F0DA}
.xoff-rental .sel.set{background-color:#D8F0DA}
.xoff-delivery .sel{background-color:#D7EBFA}
.xoff-delivery .sel.set{background-color:#D7EBFA}
.xoff-cargo .sel{background-color:#E1E2FA}
.xoff-cargo .sel.set{background-color:#E1E2FA}
.xoff-jobseek .sel{background-color:#D8F0DE}
.xoff-jobseek .sel.set{background-color:#D8F0DE}
.xoff-job .sel{background-color:#FBDDE2}
.xoff-job .sel.set{background-color:#FBDDE2}
.xoff-markets .sel{background-color:#FCEBC8}
.xoff-malls .sel{background-color:#FBDDE2}
.xoff-malls .sel.set{background-color:#FBDDE2}
.xoff-markets .sel.set{background-color:#FCEBC8}
.xoff-taxi /*SELDARK*/.sel{background:#152741!important;background-color:#152741!important;color:#fff!important;border-color:#152741!important;font-weight:600!important}.sel option{background:#fff!important;color:#111!important}/*SELSET*/.sel.set{background:#152741!important;background-color:#152741!important;color:#fff!important;border-color:#152741!important;font-weight:600!important}.sel.set option{background:#fff!important;color:#111!important}/*SELSH*/.sel{box-shadow:0 2px 6px rgba(16,24,40,0.27)!important}.sel:focus{box-shadow:0 3px 10px rgba(16,24,40,0.43)!important}.sel{background-color:#D8EEFB}
.xoff-taxi .sel.set{background-color:#D8EEFB}


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
.regbar,.subbar{display:flex;gap:9px;overflow-x:auto;padding:10px 14px 4px;
 scrollbar-width:none;max-width:1040px;margin:0 auto}
.regbar::-webkit-scrollbar,.subbar::-webkit-scrollbar{display:none}
.rg{flex:none;background:var(--card);border:1px solid var(--mist);border-radius:20px;
 padding:11px 20px;font-size:15px;font-weight:600;color:var(--ink);white-space:nowrap}.cb .rg{border:1.5px solid #9AA8BF}/*PINB2*/.cb .rg{font-size:11.5px;line-height:1.3;padding:4px 10px;margin:0 0 4px;white-space:normal;overflow:visible;text-overflow:clip}/*RG4*/.cb .rg2{opacity:1;color:var(--moss);font-weight:600}/*RG5*/.cb .sbt{font-size:12px;font-weight:600;color:#1F7A4D;margin:-6px 0 8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}/*SUBL*/.cb .sbt{white-space:normal;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;line-height:1.3}/*SUBL2*/.cb .sbt{display:block;-webkit-line-clamp:unset;overflow:visible;white-space:normal;text-overflow:clip}/*SUBL4*/div.srow{display:flex!important;flex-direction:row!important;overflow-x:auto!important;overflow-y:hidden!important;gap:11px;scroll-snap-type:x proximity!important;scroll-padding-left:4px}div.srow>a.c{flex:0 0 78%!important;width:auto!important;scroll-snap-align:start}@media(min-width:620px){div.srow>a.c{flex:0 0 46%!important}}@media(min-width:900px){div.srow>a.c{flex:0 0 30%!important}}/*ARR1*/.swrap{position:relative}.sarr{position:absolute;top:42%;transform:translateY(-50%);left:2px;z-index:5;width:34px;height:34px;border-radius:50%;border:0;background:rgba(255,255,255,.94);box-shadow:0 2px 8px rgba(16,24,40,0.49);font-size:22px;line-height:1;color:#152741;padding:0;cursor:pointer}.sarr.sr{left:auto;right:2px}div.g:has(>a.c){grid-template-columns:repeat(2,minmax(0,1fr))!important}a.c{flex-direction:row!important;align-items:stretch}a.c .ph{flex:0 0 118px;width:118px;aspect-ratio:auto!important;height:auto!important;min-height:118px;align-self:stretch}a.c .fav{width:28px;height:28px;top:6px;right:6px}a.c .cb{padding:9px 11px 10px;min-width:0}a.c .t{margin:2px 0 4px}a.c .sbt{margin:0 0 5px}.rgl{display:flex;gap:4px;align-items:flex-start;font-size:12px;line-height:1.35;color:#33425A;margin:0 0 6px}.rgl svg{flex:0 0 auto;margin-top:1px}/*HC1*/a.c .csh{position:absolute;top:6px;left:6px;z-index:3;width:28px;height:28px;border-radius:50%;border:0;padding:0;background:rgba(255,255,255,.94);color:#33425A;display:flex;align-items:center;justify-content:center}a.c .csh svg{width:15px;height:15px}.pcnt{display:inline-flex;align-items:center;gap:3px}.pcnt svg{width:14px;height:14px}/*SHPC*/a.c .cta{width:30px!important;height:30px!important;flex:0 0 30px}a.c .cta svg{width:100%;height:100%}a.c .cta+.cta{margin-left:6px}a.c .m{gap:8px}/*CTA2*/a.c .nphw{background:transparent}a.c .nphw .nphp{object-fit:cover!important;object-position:center!important}/*NPC1*/body{background:#fff!important}.top{background:#fff!important;color:#101828!important;box-shadow:0 1px 0 rgba(16,24,40,0.19)}.top a,.top b,.top span,.top div{color:#101828}.top .pin{background:#F2F4F7!important;border:0!important;color:#101828!important}.top .pin b,.top .pin span{color:#101828!important}.lang,.langs,.top nav{background:#F2F4F7!important;border:0!important}.lang a,.langs a,.top nav a{color:#667085!important;background:transparent!important}.lang a.on,.langs a.on,.top nav a.on{background:#101828!important;color:#fff!important}.s{background:#F2F4F7!important;box-shadow:none!important}.s input{color:#101828!important}.c{border:0!important;background:#fff!important;box-shadow:0 2px 10px rgba(16,24,40,0.19)!important}/*WSEL2*/html,body{color-scheme:light;} select,option{color-scheme:light !important;}/*WSEL3*//*WSEL1*/select{background:#fff !important;color:#111 !important;border:1px solid #E3E6EA !important;} select option{background:#fff;color:#111;}/*PSHADOW*/.sb2{box-shadow:0 3px 8px rgba(21,39,65,0.49) !important}.sb2.on{box-shadow:0 5px 14px rgba(21,39,65,0.70) !important}.pill{box-shadow:0 3px 8px rgba(21,39,65,0.49) !important}.cat.pic.on .pill{box-shadow:0 5px 14px rgba(21,39,65,0.70) !important}.sb2{background:#fff!important;border:0!important;color:#101828!important;box-shadow:0 1px 6px rgba(16,24,40,0.19)}.sb2.on{background:#101828!important;color:#fff!important}.nav{background:#fff!important;border-top:1px solid #EAECF0!important;box-shadow:0 -2px 12px rgba(16,24,40,0.16)}.nav a{color:#475467!important}.nav a.on{color:#101828!important}.dcard,.dph{background:#fff!important;border:0!important;box-shadow:0 2px 10px rgba(16,24,40,0.19)!important}a.c .rg{border-color:#EAECF0!important}/*WHT1*/.sb2{box-shadow:0 2px 8px rgba(16,24,40,0.27)!important;border:1px solid #E4E7EC!important}.sb2.on{box-shadow:0 3px 10px rgba(16,24,40,0.49)!important;border-color:#101828!important}.c{box-shadow:0 3px 14px rgba(16,24,40,0.22)!important}/*PSH1*/.sb2{box-shadow:0 3px 10px rgba(16,24,40,0.46)!important;border:1px solid #CFD4DC!important}.sb2.on{box-shadow:0 4px 12px rgba(16,24,40,0.70)!important}.c{box-shadow:0 4px 18px rgba(16,24,40,0.35)!important}/*PSH2*/.sb2{border:1.5px solid #98A2B3!important;box-shadow:0 4px 12px rgba(16,24,40,0.59)!important}.sb2.on{border-color:#101828!important;box-shadow:0 5px 14px rgba(16,24,40,0.85)!important}/*PSH3*/.top .pin{border:1.5px solid #98A2B3!important;box-shadow:0 4px 12px rgba(16,24,40,0.59)!important}.lang,.langs,.top nav{border:1.5px solid #98A2B3!important;box-shadow:0 4px 12px rgba(16,24,40,0.59)!important}.s{border:1.5px solid #98A2B3!important;box-shadow:0 4px 12px rgba(16,24,40,0.59)!important}.rg.on,.reg,.regs a,.rgs a,.rg2s a,.pin.rgp{border:1.5px solid #98A2B3!important;box-shadow:0 4px 12px rgba(16,24,40,0.59)!important}/*PSH4*/.rg:not(.cb .rg):not(.cb2 .rg){border:1.5px solid #98A2B3!important;box-shadow:0 4px 12px rgba(16,24,40,0.59)!important}.rg.on{box-shadow:0 5px 14px rgba(16,24,40,0.85)!important}a.c .rg,.cb .rg{border:1.5px solid #9AA8BF!important;box-shadow:none!important}/*PSH5*//*SHCLIP*/.shchips{padding-top:8px!important;padding-bottom:10px!important}.sb2{box-shadow:0 3px 8px rgba(16,24,40,0.54)!important}.sb2.on{box-shadow:0 3px 0 rgba(16,24,40,0.49),0 6px 16px rgba(16,24,40,0.73)!important}/*SUBOV*/.subbar.shchips{overflow-y:visible!important;padding-top:10px!important;padding-bottom:12px!important}.subbar.shchips .sb2{box-shadow:0 2px 0 rgba(16,24,40,0.32),0 4px 10px rgba(16,24,40,0.54)!important}.subbar.shchips .sb2.on{box-shadow:0 3px 0 rgba(16,24,40,0.49),0 6px 16px rgba(16,24,40,0.73)!important}/*SB2LAST*/.sb2{box-shadow:0 3px 8px rgba(16,24,40,0.54)!important}.sb2.on{box-shadow:0 3px 0 rgba(16,24,40,0.49),0 6px 16px rgba(16,24,40,0.73)!important}.top .lgs{background:#F2F4F7!important;border:1.5px solid #98A2B3!important;box-shadow:0 4px 12px rgba(16,24,40,0.59)!important;border-radius:13px;padding:2px}.top .lg{color:#667085!important;background:transparent!important;padding:5px 11px!important}.top .lg.on{background:#101828!important;color:#fff!important}/*LNG1*/.rpt{margin:10px 0 4px}.rpt summary{list-style:none;cursor:pointer;font-size:13px;color:#8B5A1B;background:#FAEEDA;border-radius:10px;padding:8px 12px;display:inline-block}.rpt summary::-webkit-details-marker{display:none}.rptb{background:#fff;border-radius:12px;padding:10px 12px;margin-top:8px;box-shadow:0 2px 10px rgba(16,24,40,0.22)}.rptb p{margin:0 0 8px;font-size:13px;color:#475467}.rptb a{display:block;padding:9px 10px;border-radius:9px;font-size:14px;color:#152741;text-decoration:none;border-bottom:1px solid #EAECF0}.rptb a:last-child{border-bottom:0}.rok{background:#E6F4EC;border-radius:12px;padding:12px 14px;color:#1F5E3C;font-size:15px;margin:12px 0}/*RPT3*/.rptb select,.rptb textarea{width:100%;box-sizing:border-box;border:1px solid #D0D5DD;border-radius:10px;padding:9px 10px;font-size:15px;font-family:inherit;margin-bottom:8px;background:#fff;color:#152741}.rptb button{width:100%;border:0;border-radius:10px;padding:11px;background:#101828;color:#fff;font-size:15px;font-weight:600}/*RPT7*/
.rg.on{background:var(--ink);color:#fff;border-color:var(--ink);font-weight:600}
.sb2{flex:none;background:#EEF3FB;border:1px solid #D6E2F3;border-radius:16px;
 padding:7px 14px;font-size:12.5px;font-weight:500;color:#14304F;white-space:nowrap}
.sb2.on{background:var(--leaf);color:#fff;border-color:var(--leaf);font-weight:600}
.sb2 em{font-style:normal;opacity:.9;font-size:11px;margin-left:2px}
/* Аймак баскычындагы сан — курсив эмес, кадимки тамга */
.rg{transition:transform .16s, background .16s, border-color .16s}
.rg:active{transform:scale(.94)}
.sb2{transition:transform .16s, background .16s, border-color .16s}
.sb2:active{transform:scale(.94)}
.rg em{font-style:normal;opacity:.9;font-size:13px;margin-left:4px;
 font-weight:700;font-variant-numeric:tabular-nums}

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
.c{background:var(--card);border:1px solid var(--moss);border-radius:var(--r);
 overflow:hidden;display:flex;flex-direction:column;transition:.16s}
.c:active{transform:scale(.985)}
.ph{position:relative;aspect-ratio:16/11;background:#EDF1F8;overflow:hidden;
 display:flex;align-items:center;justify-content:center;color:#C7D2E4}
.ph i{display:block;width:30px;height:30px;opacity:.45}
.ph i svg{width:100%;height:100%}
.ph img{position:absolute;inset:0;width:100%;height:100%;
 object-fit:cover;display:block}
.c.nophoto .ph{aspect-ratio:auto;height:124px}
.fav{position:absolute;top:9px;right:9px;width:33px;height:33px;border-radius:50%;
 background:rgba(255,255,255,.94);display:flex;align-items:center;justify-content:center;
 color:#2E3B52;box-shadow:0 1px 4px rgba(18,32,58,0.27);border:0;padding:0;
 cursor:pointer;transition:.15s}
.fav svg{width:17px;height:17px;transition:.15s}
.fav{color:var(--heart)}
.fav.on{color:var(--heart)}
.fav svg{fill:none}
.fav.on svg{fill:var(--heart);transform:scale(1.12)}
/* Карточкадагы байланыш баскычтары — көздүн жанында */
.cta{width:24px;height:24px;border:0;background:transparent;padding:0;
 display:inline-flex;align-items:center;justify-content:center;
 cursor:pointer;margin-left:7px;vertical-align:middle;transition:.15s}
.cta svg{width:24px;height:24px;display:block}
.cta:active{transform:scale(.9)}
.m{align-items:center}
.fav:active{transform:scale(.88)}
.cb{padding:11px 12px 13px;display:flex;flex-direction:column;flex:1}
.p{font-family:"Manrope",system-ui,sans-serif;font-size:18px;font-weight:800;
 letter-spacing:-.4px;margin-bottom:5px;font-variant-numeric:tabular-nums}
.pd{font-family:"Golos Text",system-ui,sans-serif;font-size:15.5px;font-weight:700;
 color:var(--leaf);letter-spacing:0}
.rg{font-size:12px;font-weight:600;color:var(--moss);opacity:1;line-height:1.35;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rg2{opacity:.9;/*CLEAR1*/font-weight:500}
.rg+.t,.rg2+.t{margin-top:6px}
.t{font-size:13.5px;line-height:1.38;margin:0 0 10px;font-weight:500;color:var(--ink);
 display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.m{margin-top:auto;display:flex;gap:8px;align-items:center;font-size:11.5px;
 color:#2E3B52;white-space:nowrap}
.m span:first-child{color:var(--moss);font-weight:600}
.m span:first-child{overflow:hidden;text-overflow:ellipsis}
.m .vmark{margin-left:5px;font-size:12px}
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
 padding:16px;margin-bottom:11px}.dcard{border:1.5px solid #9AA8BF}/*DCB*/
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
.cb1.call{background:var(--leaf);box-shadow:0 4px 12px rgba(176,134,43,0.46)}
.cb1.wa{background:#22C15E;box-shadow:0 4px 12px rgba(34,193,94,0.43)}
.cb1.tg{background:#2AA3DA;box-shadow:0 4px 12px rgba(42,163,218,0.43)}
.cnum{text-align:center;font-family:"Manrope",system-ui,sans-serif;font-weight:800;
 font-size:19px;letter-spacing:.2px;color:var(--ink);
 font-variant-numeric:tabular-nums;margin:2px 0 10px}

.btn{display:flex;align-items:center;justify-content:center;gap:8px;
 background:var(--leaf);color:#fff;border-radius:15px;padding:15px;
 font-size:16px;font-weight:600;box-shadow:0 5px 16px rgba(176,134,43,0.49);
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
 font-size:11.5px;font-weight:500;color:#EEF3FA}/*NAVFS*/
.nav a svg{width:22px;height:22px}
.nav a:nth-child(1) svg{color:#7FB2F0}
.nav a:nth-child(2) svg{color:#F07A72}
.nav a:nth-child(3) svg{color:#5BC98A}
.nav a:nth-child(4) svg{color:#A38BE8}
.nav a:nth-child(5) svg{color:#E0C267}
.nav a.on{color:#fff;font-weight:700}
.nav a.fab{color:#EAF3FF;font-weight:600}
.nav a.fab svg{width:50px;height:50px;padding:13px;border-radius:50%;
 position:relative;top:-24px;margin-bottom:-22px;
 color:#fff!important;background:linear-gradient(180deg,#5BC98A,#3AA167);
 box-shadow:0 6px 18px rgba(58,161,103,0.78),0 0 0 4px #17365C}
.nav a.fab:active svg{transform:scale(.94)}

@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
:focus-visible{outline:2.5px solid var(--leaf);outline-offset:2px;border-radius:6px}

/* CARD2: бөлүм — сүрөт жана түстүү жазуу тилкеси бир карточкада */
.cats{gap:10px 7px;padding:14px 9px 10px}
.cat.pic{gap:0;border-radius:16px;overflow:hidden;background:#fff;isolation:isolate;
 box-shadow:0 8px 16px -8px rgba(16,24,40,.6);transition:transform .18s cubic-bezier(.34,1.4,.5,1)}
.cat.pic .picw{border-radius:0;aspect-ratio:1/1}
.cat.pic.on .picw{box-shadow:none;transform:none}
.cat.pic.on{box-shadow:0 0 0 2.5px var(--moss),0 8px 16px -8px rgba(16,24,40,.6)}
.cat.pic .pill,.cat.pic.on .pill{position:relative;z-index:1;margin-top:-12px;
 justify-content:flex-start;gap:3px;min-height:40px;padding:5px 4px 5px 5px;
 border:0;border-radius:12px 12px 0 0;color:#fff;text-align:left;
 font-size:10px;font-weight:800;line-height:1.1;letter-spacing:-.2px;
 text-shadow:0 1px 1px rgba(0,0,0,.2);box-shadow:0 -2px 6px rgba(0,0,0,.1);
 background:linear-gradient(180deg,var(--c1,#4A8FF0),var(--c2,#1E6FE0));
 overflow-wrap:anywhere;hyphens:auto;animation:none;
 font-family:Roboto,"Segoe UI",Arial,system-ui,sans-serif}
.cat.s-malls .pill,.cat.s-wholesale .pill{font-size:9.3px;letter-spacing:-.3px}
.cat.pic .pill::before{content:"";flex:none;width:13px;height:13px;background:#fff;
 -webkit-mask:var(--ic) center/contain no-repeat;mask:var(--ic) center/contain no-repeat}
.cat.pic:active{transform:scale(.95)}
.cat.pic:active .picw,.cat.pic:active .pill{transform:none;filter:none}
.cat.s-all{--c1:#5291DE;--c2:#005DCF;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='2.10 2.10 19.80 19.80'><g fill='%23000'><rect x='3' y='3' width='8' height='8' rx='2'/><rect x='13' y='3' width='8' height='8' rx='2'/><rect x='3' y='13' width='8' height='8' rx='2'/><rect x='13' y='13' width='8' height='8' rx='2'/></g></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='2.10 2.10 19.80 19.80'><g fill='%23005DCF'><rect x='3' y='3' width='8' height='8' rx='2'/><rect x='13' y='3' width='8' height='8' rx='2'/><rect x='3' y='13' width='8' height='8' rx='2'/><rect x='13' y='13' width='8' height='8' rx='2'/></g></svg>")}
.cat.s-trade{--c1:#FEA152;--c2:#FE7501;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0.41 0.96 21.67 21.67'><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M2.5 4h2.3l2.4 10.2h10.4L20 7.5H6'/><g fill='%23000'><circle cx='9' cy='19' r='1.7'/><circle cx='17' cy='19' r='1.7'/></g></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0.41 0.96 21.67 21.67'><path stroke='%23FE7501' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M2.5 4h2.3l2.4 10.2h10.4L20 7.5H6'/><g fill='%23FE7501'><circle cx='9' cy='19' r='1.7'/><circle cx='17' cy='19' r='1.7'/></g></svg>")}
.cat.s-wholesale{--c1:#9166F8;--c2:#5D1EF5;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0.34 0.34 23.32 23.32'><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M12 2.5 3.5 7v10l8.5 4.5 8.5-4.5V7z M3.5 7l8.5 4.5L20.5 7 M12 11.5v10'/></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0.34 0.34 23.32 23.32'><path stroke='%235D1EF5' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M12 2.5 3.5 7v10l8.5 4.5 8.5-4.5V7z M3.5 7l8.5 4.5L20.5 7 M12 11.5v10'/></svg>")}
.cat.s-property{--c1:#53C4BD;--c2:#02A89E;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0.89 0.89 22.22 22.22'><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M3 11.5 12 4l9 7.5 M5.5 10v10h4.5v-5.5h4V20h4.5V10'/></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0.89 0.89 22.22 22.22'><path stroke='%2302A89E' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M3 11.5 12 4l9 7.5 M5.5 10v10h4.5v-5.5h4V20h4.5V10'/></svg>")}
.cat.s-vehicle{--c1:#52B4F6;--c2:#0191F2;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='1.44 1.94 21.12 21.12'><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M4 15.5V12l2-5.5h12l2 5.5v3.5 M3.5 12h17 M3.5 15.5h17v3h-17z'/><g fill='%23000'><circle cx='7.5' cy='14' r='1.3'/><circle cx='16.5' cy='14' r='1.3'/></g></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='1.44 1.94 21.12 21.12'><path stroke='%230191F2' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M4 15.5V12l2-5.5h12l2 5.5v3.5 M3.5 12h17 M3.5 15.5h17v3h-17z'/><g fill='%230191F2'><circle cx='7.5' cy='14' r='1.3'/><circle cx='16.5' cy='14' r='1.3'/></g></svg>")}
.cat.s-service{--c1:#8E6BF2;--c2:#5925EC;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='1.57 4.32 18.15 18.15'><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M14.5 6.5a4 4 0 0 0-5 5.2L3.5 17.7l2.8 2.8 6-6a4 4 0 0 0 5.2-5l-2.4 2.4-2.3-.5-.5-2.3z'/></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='1.57 4.32 18.15 18.15'><path stroke='%235925EC' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M14.5 6.5a4 4 0 0 0-5 5.2L3.5 17.7l2.8 2.8 6-6a4 4 0 0 0 5.2-5l-2.4 2.4-2.3-.5-.5-2.3z'/></svg>")}
.cat.s-rental{--c1:#63BC93;--c2:#1A9C60;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0.91 0.41 21.67 21.67'><circle stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' cx='7.5' cy='15.5' r='4.5'/><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M10.8 12.2 20.5 2.5 M16.5 6.5l2.8 2.8 M14 9l2 2'/></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0.91 0.41 21.67 21.67'><circle stroke='%231A9C60' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' cx='7.5' cy='15.5' r='4.5'/><path stroke='%231A9C60' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M10.8 12.2 20.5 2.5 M16.5 6.5l2.8 2.8 M14 9l2 2'/></svg>")}
.cat.s-delivery{--c1:#52ACFE;--c2:#0085FE;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='-0.16 0.79 23.32 23.32'><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M2 6h11.5v10H2z M13.5 9.5h4l3.5 3.5v3h-7.5'/><g fill='%23000'><circle cx='6' cy='18' r='2'/><circle cx='17.5' cy='18' r='2'/></g></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='-0.16 0.79 23.32 23.32'><path stroke='%230085FE' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M2 6h11.5v10H2z M13.5 9.5h4l3.5 3.5v3h-7.5'/><g fill='%230085FE'><circle cx='6' cy='18' r='2'/><circle cx='17.5' cy='18' r='2'/></g></svg>")}
.cat.s-cargo{--c1:#8378F9;--c2:#4938F6;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='-0.87 -0.62 25.63 25.63'><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M1.5 5h13.5v11H1.5z M15 9h4.5l3 3.5V16H15'/><g fill='%23000'><circle cx='5' cy='18.5' r='2'/><circle cx='11' cy='18.5' r='2'/><circle cx='19' cy='18.5' r='2'/></g></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='-0.87 -0.62 25.63 25.63'><path stroke='%234938F6' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M1.5 5h13.5v11H1.5z M15 9h4.5l3 3.5V16H15'/><g fill='%234938F6'><circle cx='5' cy='18.5' r='2'/><circle cx='11' cy='18.5' r='2'/><circle cx='19' cy='18.5' r='2'/></g></svg>")}
.cat.s-jobseek{--c1:#65B86B;--c2:#1C9725;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='1.94 1.94 21.12 21.12'><circle stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' cx='10.5' cy='10.5' r='6.5'/><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M15.5 15.5 21 21'/></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='1.94 1.94 21.12 21.12'><circle stroke='%231C9725' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' cx='10.5' cy='10.5' r='6.5'/><path stroke='%231C9725' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M15.5 15.5 21 21'/></svg>")}
.cat.s-job{--c1:#F97399;--c2:#F63169;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0.31 0.56 23.87 23.87'><circle stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' cx='9' cy='8' r='3.5'/><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M2.5 20.5a6.5 6.5 0 0 1 13 0'/><circle stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' cx='17' cy='8.5' r='2.8'/><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M16.5 13.8a5 5 0 0 1 5.5 5.2'/></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0.31 0.56 23.87 23.87'><circle stroke='%23F63169' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' cx='9' cy='8' r='3.5'/><path stroke='%23F63169' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M2.5 20.5a6.5 6.5 0 0 1 13 0'/><circle stroke='%23F63169' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' cx='17' cy='8.5' r='2.8'/><path stroke='%23F63169' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M16.5 13.8a5 5 0 0 1 5.5 5.2'/></svg>")}
.cat.s-markets{--c1:#FDCB55;--c2:#FCB205;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0.89 0.89 22.22 22.22'><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M3 9.5 4.5 4h15L21 9.5z M3 9.5a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0 M5 12.5V20h14v-7.5 M10 20v-5h4v5'/></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0.89 0.89 22.22 22.22'><path stroke='%23FCB205' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M3 9.5 4.5 4h15L21 9.5z M3 9.5a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0 M5 12.5V20h14v-7.5 M10 20v-5h4v5'/></svg>")}
.cat.s-taxi{--c1:#FCC954;--c2:#FAB003;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='1.44 0.94 21.12 21.12'><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M4 16V12.5l2-5h12l2 5V16 M3.5 12.5h17 M3.5 16h17v3h-17z M9.5 4h5v3.5'/><g fill='%23000'><circle cx='7.5' cy='14.3' r='1.2'/><circle cx='16.5' cy='14.3' r='1.2'/></g></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='1.44 0.94 21.12 21.12'><path stroke='%23FAB003' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M4 16V12.5l2-5h12l2 5V16 M3.5 12.5h17 M3.5 16h17v3h-17z M9.5 4h5v3.5'/><g fill='%23FAB003'><circle cx='7.5' cy='14.3' r='1.2'/><circle cx='16.5' cy='14.3' r='1.2'/></g></svg>")}
.cat.s-malls{--c1:#F367A4;--c2:#EE1F79;--ic:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='1.16 1.41 21.67 21.67'><path stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M5 8h14l-1 13H6z M9 8V6.5a3 3 0 0 1 6 0V8'/></svg>");--ic2:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='1.16 1.41 21.67 21.67'><path stroke='%23EE1F79' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' fill='none' d='M5 8h14l-1 13H6z M9 8V6.5a3 3 0 0 1 6 0V8'/></svg>")}

/* CARD5: тилкесиз — аталыш сүрөттүн өзүндө, ылдыйы акырын карарат */
.cat.pic .pill,.cat.pic.on .pill{margin-top:-46px;min-height:46px;padding:14px 5px 6px 6px;
 border-radius:0;box-shadow:none;color:#fff;text-shadow:0 1px 3px rgba(0,0,0,.65);
 background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,.45) 35%,rgba(0,0,0,.78) 100%)}
.cat.pic .pill::before{background:#fff;filter:drop-shadow(0 1px 1px rgba(0,0,0,.5))}

/* CHIPSEL: тандалган чип — кочкул көк, ылдыйында жашыл сызык */
.regbar .rg.on:not(.cb .rg):not(.cb2 .rg),.regcat .rg.on:not(.cb .rg),.subbar .rg.on:not(.cb .rg){background:#152741!important;
 border-color:#152741!important;color:#fff!important;
 box-shadow:inset 0 -4px 0 #3AA167,0 4px 10px rgba(16,24,40,.45)!important}
.cb .rg.on,a.c .rg.on{box-shadow:none!important}

/* TILESEL: тандалган бөлүмдүн сүрөтүнүн астында жашыл сызык */
.cats .cat.pic{border-bottom:4px solid transparent!important;box-sizing:border-box}
.cats .cat.pic.on{border-bottom-color:#3AA167!important}

/* CARD11: белги ак тегеректе, жазуу ортодо; тандалганда — чиптердей */
.cats .cat.pic .pill,.cats .cat.pic.on .pill{position:relative;flex-direction:column;
 justify-content:center;align-items:center;text-align:center;gap:2px;
 margin-top:-10px;min-height:46px;padding:2px 5px 7px;border-radius:12px 12px 0 0;
 color:#fff;text-shadow:0 1px 1px rgba(0,0,0,.25);box-shadow:0 -2px 6px rgba(0,0,0,.12);
 background:linear-gradient(180deg,var(--c1,#4A8FF0),var(--c2,#1E6FE0))}
.cats .cat.pic .pill::before{content:"";flex:none;width:26px;height:26px;border-radius:50%;
 background:#fff;-webkit-mask:none;mask:none;filter:none;margin-top:-13px;
 box-shadow:0 2px 5px rgba(0,0,0,.3)}
.cats .cat.pic .pill::after{content:"";position:absolute;top:-8px;left:50%;
 transform:translateX(-50%);width:16px;height:16px;background:var(--c2,#1E6FE0);
 -webkit-mask:var(--ic) center/contain no-repeat;mask:var(--ic) center/contain no-repeat}
.cats .cat.pic.on .pill{background:#152741!important}

/* ICON_CENTER: белгилер тегеректин так ортосунда */

/* CARD11B: белги ак тегеректин так ортосунда */
.cats .cat.pic .pill::before{background:#fff var(--ic2) center/15px no-repeat!important}
.cats .cat.pic .pill::after{content:none!important}

/* TITLEBIG: жарыянын аталышы баадан чоң */
.cb .t{font-size:16px!important;line-height:1.3!important;font-weight:700!important;
 margin:0 0 6px!important}
.cb .p{font-size:15px!important;font-weight:700!important;margin-bottom:4px!important}
.cb .pd{font-size:13.5px!important;font-weight:600!important}
"""

# /*DEEPSHADOW*/
