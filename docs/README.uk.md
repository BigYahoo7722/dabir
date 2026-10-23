# Dabir (دبیر)

> Мовлення в текст з перекладом: перська й англійська на вході, 20 мов на виході.

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · **Українська** · [Ελληνικά](README.el.md)

Dabir перетворює записи на текст. Завантажте аудіо (mp3, m4a, wav… до 1 ГБ): воно визначить, перська це чи англійська, розшифрує мовлення й за бажання перекладе на 20 інших мов. Працює на відкритих моделях у вашому репозиторії GitHub, без ключів API штучного інтелекту.

## Можливості

- Завантаження частинами з відновленням до 1 ГБ і необов'язкове стиснення в браузері для повільних мереж
- Автовизначення перської/англійської та три рівні якості
- Офлайн-переклад на 20 мов (Argos Translate)
- Необов'язкове шумозаглушення та позначки мовців
- Зашифровані результати, які читає лише браузер, що завантажив файл
- Приватна бібліотека на дві години, копіювання й експорт TXT/SRT, інтерфейс перською та англійською

## Як це працює

Сайт (GitHub Pages) звертається до невеликого Cloudflare Worker, який зберігає секрети. Worker кладе аудіо в приватний чорновий Release і запускає завдання GitHub Actions: розшифрування, переклад, шифрування та публікація результату.

```
Browser (GitHub Pages)
   │  HTTPS, no token needed
   ▼
Cloudflare Worker ── holds GH_TOKEN, JOB_SECRET
   │  GitHub API: private draft Release (audio) + workflow dispatch
   ▼
GitHub Actions (process.py): FFmpeg → denoise → Whisper → Argos → AES-GCM
   │  encrypted result on branch `jobs`
   ▼
Worker → Browser (decrypts with the per-job key)
```

🧱 GitHub Pages · Cloudflare Workers · GitHub Actions · Python 3.11 · faster-whisper (Whisper) · Argos Translate · noisereduce · Resemblyzer · lamejs · FFmpeg · Web Crypto (AES-GCM) · IndexedDB

## Структура проєкту

```
dabir/
├── index.html              # UI (single file, Persian/English)
├── config.js               # Worker URL (DABIR_API)
├── lame.min.js             # in-browser MP3 encoder (LGPL-3.0)
├── process.py              # bot: decode, denoise, transcribe, translate, encrypt
├── cleanup.py              # hourly cleanup of old results/releases
├── requirements.txt        # bot dependencies
├── requirements-speakers.txt  # optional speaker-label dependencies
├── package.json            # test scripts (jsdom, fake-indexeddb)
├── worker/
│   ├── src/index.js        # Cloudflare Worker API
│   ├── wrangler.toml       # Worker variables
│   └── package.json
├── .github/workflows/
│   ├── process.yml         # runs process.py for each job
│   └── cleanup.yml         # hourly cleanup
├── tests/                  # selftest.py, pipeline_mock.py, worker.test.mjs,
│                           # specialist_mock.py, ui.test.cjs, compress.test.cjs
├── docs/                   # this README in 21 languages
└── README.md
```

## Розгортання з нуля

1. Створіть **публічний** репозиторій (наприклад, `dabir`) з README.

2. Завантажте всі файли проєкту разом із папками в корінь репозиторію. Приховану папку `.github` створіть через **Add file → Create new file**.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. Згенеруйте випадковий секрет (команда нижче) і збережіть його як секрет Actions `JOB_SECRET`.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. Створіть Fine-grained токен лише для цього репозиторію: Contents і Actions, обидва Read and write.

7. У Cloudflare створіть Worker (Hello World), вставте `worker/src/index.js`, додайте змінні та секрети з таблиці й натисніть Deploy.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Впишіть адресу Worker у `config.js`, зробіть Commit і оновіть сайт через Ctrl+Shift+R.

9. Завантажте короткий тестовий файл. Перший запуск повільний: моделі завантажуються й кешуються.

## Налаштування

Імена чутливі до регістру. `GH_TOKEN` і `JOB_SECRET` мають бути типу Secret; `JOB_SECRET` однаковий у GitHub і Cloudflare.

| Name | Type | Where | Value |
|---|---|---|---|
| `REPO` | text | Cloudflare | `<user>/dabir` |
| `BRANCH` | text | Cloudflare | `main` |
| `ALLOWED_ORIGIN` | text | Cloudflare | `https://<user>.github.io` |
| `MAX_BYTES` | text | Cloudflare | `1073741824` (1 GB) |
| `MAX_ACTIVE` | text | Cloudflare | `20` (parallel jobs) |
| `GH_TOKEN` | **secret** | Cloudflare | fine-grained token |
| `JOB_SECRET` | **secret** | Cloudflare **and** GitHub Actions | 64 hex characters |
| `RETAIN_SECONDS` | env | `cleanup.yml` | `7500` (2 h + margin) |
| `FA_MODEL` | variable (optional) | GitHub → Settings → Secrets and variables → Actions → Variables | `givia/whisper-large-v3-turbo-persian` (Persian specialist; converted to CTranslate2 on first use) |
| `DABIR_API` | JS | `config.js` | Worker URL, no trailing slash |

## Розробка й тести

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## Приватність і безпека

- Аудіо зберігається лише в приватному чорновому Release і видаляється після обробки.
- Результати шифруються AES-GCM; ключ ніколи не залишає браузер того, хто завантажив.
- Токен GitHub є лише в Cloudflare і ніколи не надсилається відвідувачам.
- Копії на сервері спливають приблизно за дві години. Для чутливого вмісту використовуйте приватний репозиторій.

## Обмеження

- Whisper гірше працює з перською, ніж з англійською: оберіть мову й найкращу якість і перевірте текст.
- GitHub Actions обмежує завдання приблизно 6 годинами; дуже довге аудіо на найповільнішій якості може не встигнути.
- Позначки мовців лише текстові; розділення голосів на окремі аудіофайли не реалізоване.
- Реальний лише прогрес завантаження; обробка показує «в черзі», «виконується» та «збереження».
- Безплатні тарифи GitHub і Cloudflare мають ліміти використання.
- Переклад, шумозаглушення, позначки мовців і файли до 1 ГБ реалізовані, але перевірені на практиці обмежено.

## Усунення несправностей

| ⚠️ | 🔧 |
|---|---|
| Повідомлення «сервер не налаштовано» | `config.js` порожній або закешований: вкажіть адресу Worker і повністю оновіть сторінку (або `config.js?v=2`). |
| `Failed to fetch` під час завантаження | `ALLOWED_ORIGIN` має бути точно `https://<user>.github.io` (без скісної риски в кінці); повторіть Deploy. |
| 502 «не вдалося створити завдання» | `GH_TOKEN` хибний, прострочений або без прав; замініть його. |
| Завдання застрягло в черзі | Відкрийте вкладку Actions; перевірте права workflow та наявність `process.yml`. |
| Результат «неповна конфігурація» | `JOB_SECRET` відсутній або відрізняється в GitHub і Cloudflare. |
| Запуск триває дуже довго | Читайте рядки етапів у журналі; перший запуск завантажує моделі; якщо етап завис, скасуйте й повторіть. |

## Ліцензія та подяки

Додайте власний файл `LICENSE`. Сторонні компоненти зберігають свої ліцензії:

- [Whisper](https://github.com/openai/whisper) / [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — MIT
- [Argos Translate](https://github.com/argosopentech/argos-translate) — MIT (language models have their own licenses)
- [noisereduce](https://github.com/timsainb/noisereduce) — MIT
- [Resemblyzer](https://github.com/resemble-ai/Resemblyzer) — Apache-2.0
- [lamejs](https://github.com/zhuker/lamejs) — LGPL-3.0 (`lame.min.js`)
- [givia/whisper-large-v3-turbo-persian](https://huggingface.co/givia/whisper-large-v3-turbo-persian) — CC-BY-4.0 (Persian specialist model, converted to CTranslate2 in the workflow)
- [Vazirmatn](https://github.com/rastikerdar/vazirmatn) font — OFL-1.1
- FFmpeg — LGPL/GPL depending on the build

---
**made by Big_Yahoo8844**
