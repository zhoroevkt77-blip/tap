# -*- coding: utf-8 -*-
"""
ТАП! — медиа файлдарды тазалоо.

Базада шилтемеси бар файлдар тийбейт. Шилтемесиз файл MIN_AGE_DAYS'тен
эски болсо гана өчүрүлөт (жаңы, бүтө элек жарыялардын сүрөтү жоголбосун).

    python3 media_cleanup.py            — эч нерсе өчүрбөй, отчёт гана
    python3 media_cleanup.py --delete   — чын эле өчүрөт
"""
import os
import sys
import time

import core

KEEP_DAYS = 30      # мөөнөтү бүткөндөн кийин файлдар ушунча күн сакталат
MIN_AGE_DAYS = 7    # мындан жаңы файлдар эч качан өчүрүлбөйт


def _val(row, key):
    if hasattr(row, "get"):
        return row.get(key)
    try:
        return row[key]
    except Exception:
        return None


def _columns():
    """listings таблицасында кайсы мамычалар бар."""
    want = ("is_active", "expires_at", "photo", "photos", "video")
    try:
        rows = core.query("SELECT * FROM listings LIMIT 1", (), fetch="all") or []
    except Exception as e:
        raise SystemExit("❌ listings таблицасы окулбады: %s" % e)
    if rows:
        r = rows[0]
        keys = set(r.keys()) if hasattr(r, "keys") else set()
        if keys:
            return [c for c in want if c in keys]
    out = []
    for c in want:
        try:
            core.query("SELECT %s FROM listings LIMIT 1" % c, (), fetch="all")
            out.append(c)
        except Exception:
            pass
    return out


def _fetch_rows():
    cols = [c for c in _columns()]
    media_cols = [c for c in cols if c in ("photo", "photos", "video")]
    if not media_cols:
        raise SystemExit("❌ listings ичинде photo/photos/video мамычалары жок")
    print("Мамычалар: %s" % ", ".join(cols))
    return core.query("SELECT %s FROM listings" % ", ".join(cols),
                      (), fetch="all") or []


def referenced_names():
    """Базада шилтемеси бар файлдардын аттары."""
    rows = _fetch_rows()
    cutoff = time.strftime("%Y-%m-%d",
                           time.localtime(time.time() - KEEP_DAYS * 86400))
    names = set()
    for r in rows:
        exp = str(_val(r, "expires_at") or "")[:10]
        act = _val(r, "is_active")
        active = act is None or str(act) in ("1", "True", "true")
        if not active and exp and exp < cutoff:
            continue           # эскирген — файлдары өчө берсин
        for key in ("photo", "photos", "video"):
            v = _val(r, key)
            if not v:
                continue
            for part in str(v).replace(";", ",").split(","):
                part = os.path.basename(part.strip())
                if part:
                    names.add(part)
    return names


def run(delete=False):
    """Тазалоо. delete=False болсо эч нерсе өчүрбөйт, отчёт гана."""
    media = core.MEDIA
    if not os.path.isdir(media):
        print("[media] папка жок: %s" % media, flush=True)
        return 0, 0

    keep = referenced_names()
    now = time.time()
    n_all = n_del = 0
    size_all = size_del = 0

    for name in os.listdir(media):
        fp = os.path.join(media, name)
        if not os.path.isfile(fp):
            continue
        try:
            st = os.stat(fp)
        except OSError:
            continue
        n_all += 1
        size_all += st.st_size
        if name in keep:
            continue
        if now - st.st_mtime < MIN_AGE_DAYS * 86400:
            continue
        n_del += 1
        size_del += st.st_size
        if delete:
            try:
                os.remove(fp)
            except OSError as e:
                print("[media] ⚠️ %s: %s" % (name, e), flush=True)

    mb = lambda b: "%.1f МБ" % (b / 1048576.0)
    print("[media] базада %d ат; дискте %d файл (%s); %s %d файл (%s)"
          % (len(keep), n_all, mb(size_all),
             "өчүрүлдү" if delete else "өчүрүлмөк",
             n_del, mb(size_del)), flush=True)
    return n_del, size_del


def main():
    delete = "--delete" in sys.argv
    n, _ = run(delete=delete)
    if not delete and n:
        print("\nЧын эле өчүрүү үчүн: python3 media_cleanup.py --delete")


if __name__ == "__main__":
    main()
