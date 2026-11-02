# -*- coding: utf-8 -*-
"""ААР-2024: айыл аймактары ирилештирилди (КР 18.07.2024 №128 Мыйзамы, №165 редакциясы).

Булак: Мыйзамдын тексти (аймактардын аттары, борборлору), Президенттин 29.12.2023 УП-370 Жарлыгы
(кайсы айыл аймактары кошулду), Нарын облусу — 2023-ж. жарлык, Түп району — райондун маалыматы.
geo2024.json: жаңы райондор, эски → жаңы дарек (жарыяларды көчүрүү үчүн).
"""
import json
import os

_P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo2024.json")
DATA = None
BISH = "Бишкекке кошулган айылдар"


def load():
    global DATA
    if DATA is None:
        with open(_P, encoding="utf-8") as f:
            DATA = json.load(f)
    return DATA


def apply(g):
    d = load()
    GEO = g["GEO"]
    back = {v: k for k, v in d["rename"].items()}
    for ob, ds in d["districts"].items():
        node = GEO.get(ob)
        if not isinstance(node, dict):
            continue
        items = list(node.items())
        node.clear()
        for di, val in items:
            nd = d["rename"].get(di, di)
            node[nd] = ds.get(nd, val) if isinstance(val, dict) else val
    try:
        GEO["Бишкек шаары"][BISH] = list(d["bishkek"])
        ja = GEO["Жалал-Абад облусу"]
        for k, extra in (("Манас шаары", d["ja_extra"]), ("Таш-Көмүр шаары", d["tk_extra"])):
            if isinstance(ja.get(k), list):
                for v in extra:
                    if v not in ja[k]:
                        ja[k].append(v)
    except Exception as e:
        print("geo2024 extra:", e, flush=True)
    for name in ("DISTRICT_RU", "REGION_RU"):
        m = g.get(name)
        if isinstance(m, dict):
            m["Айтматов району"] = "Айтматовский район"
            m[BISH] = "Сёла, присоединённые к Бишкеку"
    return True


def migrate_row(ob, di, lo, vg):
    """Эски дарек → жаңы (ob, di, lo, vg). Өзгөрбөсө None."""
    d = load()
    ob, di, lo, vg = ob or "", di or "", lo or "", vg or ""
    r = d["mig"].get("|".join((ob, di, lo, vg)))
    if r:
        return tuple(r)
    a = d["aamap"].get("|".join((ob, di, lo)))
    if a:
        return (a[0], a[1], a[2], vg)
    if di in d["rename"]:
        return (ob, d["rename"][di], lo, vg)
    return None
