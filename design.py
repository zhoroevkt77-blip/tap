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
 font-family:"Inter",-apple-system,"Segoe UI",Roboto,system-ui,sans-serif;
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
/* Бөлүмдөр: эки катар торчо, ар биринде көлөмдүү белги, астында аты */
.cats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px 8px;
 overflow:visible;padding:14px 12px 10px;align-items:start}
.cat.pic{border:0;background:none;padding:0;overflow:visible;position:relative;
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
 box-shadow:0 3px 8px -6px rgba(18,32,58,.5)}
.cat.pic.on .picw{box-shadow:0 0 0 2.5px var(--moss)}
/* Аймак тандалганда бөлүмдүн бурчундагы жарыялардын саны */
.secn{position:absolute;top:5px;left:5px;z-index:2;min-width:19px;height:19px;
 padding:0 5px;border-radius:999px;background:var(--moss);color:#fff;
 font-size:10.5px;font-weight:700;line-height:19px;text-align:center;
 font-variant-numeric:tabular-nums;box-shadow:0 2px 6px -2px rgba(14,34,64,.55)}
.cat{position:relative}
.cat.pic.on .pill{background:var(--moss);border-color:var(--moss);color:#fff}
/* Ар бир бөлүмдүн жазуусу үстүндөгү сүрөттүн өңүндө болсун */
.cat.s-all .pill{background:#DCEBFB;border-color:#C5DDF4}
.cat.s-trade .pill{background:#FCE7D2;border-color:#F3D5B8}
.cat.s-wholesale .pill{background:#E6DEFB;border-color:#D5C9F5}
.cat.s-property .pill{background:#D9EDFB;border-color:#C2DFF4}
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
 box-shadow:0 0 0 2px var(--gold),0 10px 22px -12px rgba(14,34,64,.4)}
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
.fsec.s-trade .sel{background-color:#FCE7D2}
.fsec.s-trade .sel.set{background-color:#FCE7D2}
.fsec.s-wholesale .sel{background-color:#E6DEFB}
.fsec.s-wholesale .sel.set{background-color:#E6DEFB}
.fsec.s-property .sel{background-color:#D9EDFB}
.fsec.s-property .sel.set{background-color:#D9EDFB}
.fsec.s-service .sel{background-color:#E4DDFA}
.fsec.s-service .sel.set{background-color:#E4DDFA}
.fsec.s-rental .sel{background-color:#D8F0DA}
.fsec.s-rental .sel.set{background-color:#D8F0DA}
.fsec.s-delivery .sel{background-color:#D7EBFA}
.fsec.s-delivery .sel.set{background-color:#D7EBFA}
.fsec.s-cargo .sel{background-color:#E1E2FA}
.fsec.s-cargo .sel.set{background-color:#E1E2FA}
.fsec.s-jobseek .sel{background-color:#D8F0DE}
.fsec.s-jobseek .sel.set{background-color:#D8F0DE}
.fsec.s-job .sel{background-color:#FBDDE2}
.fsec.s-job .sel.set{background-color:#FBDDE2}
.fsec.s-markets .sel{background-color:#FCEBC8}
.fsec.s-malls .sel{background-color:#FBDDE2}
.fsec.s-malls .sel.set{background-color:#FBDDE2}
.fsec.s-markets .sel.set{background-color:#FCEBC8}
.fsec.s-taxi .sel{background-color:#D8EEFB}
.fsec.s-taxi .sel.set{background-color:#D8EEFB}


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
 padding:11px 20px;font-size:15px;font-weight:600;color:var(--ink);white-space:nowrap}.cb .rg{border:1.5px solid #9AA8BF}/*PINB2*/.cb .rg{font-size:11.5px;line-height:1.3;padding:4px 10px;margin:0 0 4px;white-space:normal;overflow:visible;text-overflow:clip}/*RG4*/.cb .rg2{opacity:1;color:var(--moss);font-weight:600}/*RG5*/.cb .sbt{font-size:12px;font-weight:600;color:#1F7A4D;margin:-6px 0 8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}/*SUBL*/.cb .sbt{white-space:normal;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;line-height:1.3}/*SUBL2*/.cb .sbt{display:block;-webkit-line-clamp:unset;overflow:visible;white-space:normal;text-overflow:clip}/*SUBL3*/div.srow{display:flex!important;flex-direction:column!important;overflow:visible!important;gap:10px;scroll-snap-type:none!important}div.srow>a.c{flex:0 0 auto!important;width:100%}div.srow>a.c:nth-child(n+4){display:none!important}div.g:has(>a.c){grid-template-columns:1fr!important}a.c{flex-direction:row!important;align-items:stretch}a.c .ph{flex:0 0 118px;width:118px;aspect-ratio:auto!important;height:auto!important;min-height:118px;align-self:stretch}a.c .fav{width:28px;height:28px;top:6px;right:6px}a.c .cb{padding:9px 11px 10px;min-width:0}a.c .t{margin:2px 0 4px}a.c .sbt{margin:0 0 5px}.rgl{display:flex;gap:4px;align-items:flex-start;font-size:12px;line-height:1.35;color:#33425A;margin:0 0 6px}.rgl svg{flex:0 0 auto;margin-top:1px}/*HC1*/
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
 color:#2E3B52;box-shadow:0 1px 4px rgba(18,32,58,.1);border:0;padding:0;
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
 font-size:10.5px;font-weight:500;color:#EEF3FA}
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
 box-shadow:0 6px 18px rgba(58,161,103,.45),0 0 0 4px #17365C}
.nav a.fab:active svg{transform:scale(.94)}

@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
:focus-visible{outline:2.5px solid var(--leaf);outline-offset:2px;border-radius:6px}
"""
