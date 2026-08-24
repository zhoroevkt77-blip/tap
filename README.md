# TAP! — жарыя системасы

Telegram бот аркылуу жарыя коюлат, витрина сайтта көрүнөт.

## Файлдар

| Файл | Эмне кылат |
|---|---|
| `core.py` | Жалпы өзөк: база, категориялар, издөө. Экөө тең ушуну колдонот |
| `bot.py` | Telegram бот |
| `tap.py` | Витрина (сайт) |

## База

- `DATABASE_URL` коюлса → **Postgres** (Railway)
- Коюлбаса → **SQLite**, `tap.db` файлы (жергиликтүү сынап көрүү үчүн)

Код өзгөрбөйт, экөөндө тең иштейт.

## Railway'де жайгаштыруу

Бир репозиторийден **эки кызмат** түзүлөт, экөө тең бир Postgres'ке туташат.

### 1. Postgres
Долбоордо `+ New` → `Database` → `Add PostgreSQL`.

### 2. Бот кызматы
- Start command: `python bot.py`
- Variables:
  - `TELEGRAM_BOT_TOKEN` — @BotFather'ден алынган токен
  - `DATABASE_URL` — Postgres'тен (Railway өзү сунуштайт)
  - `SITE_URL` — сайттын дареги (мис. `https://tap-web.up.railway.app`)

### 3. Сайт кызматы
- Start command: `python tap.py`
- Variables:
  - `DATABASE_URL` — ошол эле Postgres
- Networking → **Generate Domain** (ошондон чыккан дарек `SITE_URL` болот)

## Жергиликтүү иштетүү

```bash
echo -n "ТОКЕН" > token.txt
python bot.py       # бир терминалда
python tap.py       # экинчисинде → http://localhost:8000
```

## Эскертүүлөр

- `token.txt` GitHub'га **эч качан** жүктөлбөйт (`.gitignore`де турат)
- Сүрөттөр `media/` папкасында. Railway'де диск (Volume) кошулбаса, кайра
  жүктөгөндө сүрөттөр жоголот — жарыялар Postgres'те калат
- Модерация азырынча жок
