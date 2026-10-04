"""
ТАП! — видеону телефондо тез ачылгыдай кылуу (VIDOPT).

  * узун жагы 1280px'тен ашпайт (720p), H.264 + AAC, ~2 Мбит/с
  * moov атому файлдын башына коюлат (faststart) — видео дароо башталат
  * iPhone'дун HEVC видеолору да бардык телефондо ойнойт

ffmpeg системада болсо ошол, болбосо imageio-ffmpeg пакетиндеги колдонулат.
ffmpeg табылбаса — эч нерсе өзгөрбөйт, видео мурункудай берилет.
"""
import json
import os
import shutil
import subprocess
import threading
import time

_FF = [None, False]
_LOCK = threading.Lock()
_DONE_NAME = ".vopt.json"


def ffmpeg():
    if _FF[1]:
        return _FF[0]
    p = shutil.which("ffmpeg")
    if not p:
        try:
            import imageio_ffmpeg
            p = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            p = None
    _FF[0], _FF[1] = p, True
    print("vidopt: ffmpeg =", p, flush=True)
    return p


def _faststart(path):
    """moov атому mdat'тан мурун турабы."""
    try:
        with open(path, "rb") as f:
            pos, size = 0, os.path.getsize(path)
            while pos + 8 <= size:
                f.seek(pos)
                h = f.read(16)
                n = int.from_bytes(h[:4], "big")
                kind = h[4:8]
                if n == 1:
                    n = int.from_bytes(h[8:16], "big")
                elif n == 0:
                    n = size - pos
                if kind == b"moov":
                    return True
                if kind == b"mdat":
                    return False
                if n < 8:
                    return False
                pos += n
    except Exception:
        pass
    return False


def optimize(path, timeout=150):
    """Видеону ордунда оптималдаштырат. Ийгиликтүү болсо True."""
    ff = ffmpeg()
    if not ff or not os.path.isfile(path):
        return False
    tmp = path + ".opt.mp4"
    cmd = [ff, "-y", "-v", "error", "-i", path,
           "-map", "0:v:0", "-map", "0:a:0?",
           "-vf", "scale=1280:1280:force_original_aspect_ratio=decrease,"
                  "scale=trunc(iw/2)*2:trunc(ih/2)*2",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "27",
           "-maxrate", "2500k", "-bufsize", "5000k", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "96k", "-ac", "2",
           "-movflags", "+faststart", "-t", "300", tmp]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                           timeout=timeout)
        ok = r.returncode == 0 and os.path.isfile(tmp) and os.path.getsize(tmp) > 1000
        if not ok:
            print("vidopt fail:", os.path.basename(path),
                  (r.stderr or b"")[-300:].decode("utf-8", "ignore"), flush=True)
    except Exception as e:
        print("vidopt:", e, flush=True)
        ok = False
    if not ok:
        try:
            os.remove(tmp)
        except Exception:
            pass
        return False
    a, b = os.path.getsize(path), os.path.getsize(tmp)
    if b < a or not _faststart(path):
        os.replace(tmp, path)
        print("vidopt: %s %d КБ → %d КБ, %.1f с" % (os.path.basename(path), a // 1024,
                                                   b // 1024, time.time() - t0), flush=True)
    else:
        os.remove(tmp)
    return True


def _load(media):
    try:
        with open(os.path.join(media, _DONE_NAME), encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save(media, done):
    try:
        with open(os.path.join(media, _DONE_NAME), "w", encoding="utf-8") as f:
            json.dump(sorted(done), f)
    except Exception:
        pass


def mark(media, name):
    with _LOCK:
        d = _load(media)
        d.add(name)
        _save(media, d)


def _sweep(media):
    """Мурунку видеолорду бирден оптималдаштырат (web_ убактылуу файлдарга тийбейт)."""
    time.sleep(60)
    while True:
        try:
            if ffmpeg():
                done = _load(media)
                for nm in sorted(os.listdir(media)):
                    low = nm.lower()
                    if (not low.endswith((".mp4", ".mov")) or low.startswith("web_")
                            or ".opt." in low or nm in done):
                        continue
                    optimize(os.path.join(media, nm))
                    mark(media, nm)
                    time.sleep(5)
        except Exception as e:
            print("vidopt sweep:", e, flush=True)
        time.sleep(600)


def start(media):
    t = threading.Thread(target=_sweep, args=(media,), daemon=True)
    t.start()
