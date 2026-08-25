#!/data/data/com.termux/files/usr/bin/bash
# ТАП! — жаңы менюну GitHub'ка коюу.
# Иштетүү:  bash koy.sh

set -e

REPO="$HOME/tap"
DL="$HOME/storage/downloads"
FILES="tap_catalog.py taxi_geo.py tap_flow.py bridge.py icons.py scenes.py strings.py design.py core.py bot.py tap.py whatsapp.py"

echo
echo "════════════════════════════════════════"
echo "  ТАП! — жаңы менюну коюу"
echo "════════════════════════════════════════"
echo

# ── 1. Репо ордундабы ──────────────────────────────
if [ ! -d "$REPO/.git" ]; then
  echo "❌ $REPO табылган жок (же git репо эмес)."
  echo "   Адегенде: cd ~/tap && ls"
  exit 1
fi

# ── 2. Файлдар жүктөлгөнбү ─────────────────────────
MISSING=""
for f in $FILES; do
  [ -f "$DL/$f" ] || MISSING="$MISSING $f"
done

if [ -n "$MISSING" ]; then
  echo "❌ Download папкасында жок:"
  for f in $MISSING; do echo "   - $f"; done
  echo
  echo "   Чатта ошол файлдарды басып, Download кыл."
  exit 1
fi

cd "$REPO"

# ── 3. Эски нускасын сактап коёбуз ─────────────────
STAMP=$(date +%Y%m%d-%H%M)
mkdir -p "eski-$STAMP"
for f in core.py bot.py tap.py; do
  [ -f "$f" ] && cp "$f" "eski-$STAMP/"
done
echo "💾 Эски core.py менен bot.py сакталды: eski-$STAMP/"

# ── 4. Жаңыларын көчүрөбүз ─────────────────────────
for f in $FILES; do
  cp "$DL/$f" "$REPO/$f"
  echo "   ✓ $f"
done

# ── 5. Синтаксисин текшеребиз ──────────────────────
echo
echo "🔍 Текшерүү..."
for f in $FILES; do
  python -c "import py_compile,sys; py_compile.compile('$f', doraise=True)" || {
    echo "❌ $f'де синтаксис катасы бар. Push кылынбады."
    exit 1
  }
done

python - <<'PY' || { echo "❌ Импорт катасы. Push кылынбады."; exit 1; }
import tap_catalog, taxi_geo, tap_flow, bridge, icons, scenes, strings, design, tap, whatsapp
from tap_flow import render, advance, START_STEP
s, d = START_STEP, {}
for v in ["ky", "post", "trade"]:
    s, d = advance(s, v, d)
assert render(s, d)["options"], "меню бош"
assert len(tap.SECTIONS) == 7, "сайтта жети бөлүм жок"
assert len(icons.ICONS) == 8, "эмблемалар толук эмес"
print("   ✓ бот менюсу иштейт, %d облус, %d соода категориясы"
      % (len(tap_catalog.OBLASTS), len(tap_catalog.TRADE_CATEGORIES)))
print("   ✓ сайт жети бөлүмдү тааныйт")
PY

# ── 6. GitHub'ка ───────────────────────────────────
# Керексиз файлдар кирип кетпесин
for line in "__pycache__/" "*.pyc" "tap.db" "bot_state.json" "media/" "token.txt"; do
  grep -qxF "$line" .gitignore 2>/dev/null || echo "$line" >> .gitignore
done

echo
echo "📤 GitHub'ка жөнөтүлүүдө..."
git add .gitignore
git rm -r --cached __pycache__ >/dev/null 2>&1 || true
git add tap_catalog.py taxi_geo.py tap_flow.py bridge.py icons.py scenes.py strings.py design.py core.py bot.py tap.py whatsapp.py
git add "eski-$STAMP" 2>/dev/null || true

if git diff --cached --quiet; then
  echo "   Өзгөрүү жок — баары мурунтан ордунда."
  exit 0
fi

git commit -m "Бөлүм такталары — толук көрүнүш"

if ! git pull --rebase; then
  echo
  echo "⚠️  git pull кайчылашып калды."
  echo "   Токтотуу үчүн:  git rebase --abort"
  echo "   Анан кайра:     bash koy.sh"
  exit 1
fi

if ! git push; then
  echo
  echo "⚠️  Push өтпөдү. Көбүнчө токен суралат — кайра аракет кыл:"
  echo "   cd ~/tap && git push"
  exit 1
fi

echo
echo "════════════════════════════════════════"
echo "  ✅ Бүттү!"
echo "════════════════════════════════════════"
echo
echo "  Railway азыр кайра курат (2-3 мүнөт)."
echo "  Анан @TapmeniBot'ко /start жаз."
echo
echo "  Эгер бир нерсе бузулса, кайтаруу:"
echo "    cd ~/tap && cp eski-$STAMP/*.py . && git commit -am 'кайтаруу' && git push"
echo
