# Dabir (دبیر)

> Речь в текст с переводом: персидский и английский на входе, 20 языков на выходе.

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · **Русский** · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir превращает записи в текст. Загрузите аудио (mp3, m4a, wav… до 1 ГБ): оно определит, персидский это или английский, расшифрует речь и при желании переведёт на 20 других языков. Работает на открытых моделях в вашем репозитории GitHub, без ключей API ИИ.

## Возможности

- Загрузка частями с возобновлением до 1 ГБ и необязательное сжатие в браузере для медленных сетей
- Автоопределение персидского/английского и три уровня качества
- Офлайн-перевод на 20 языков (Argos Translate)
- Необязательное шумоподавление и метки говорящих
- Зашифрованные результаты, которые читает только загрузивший браузер
- Личная библиотека на два часа, копирование и экспорт TXT/SRT, интерфейс на персидском и английском

## Как это работает

Сайт (GitHub Pages) обращается к небольшому Cloudflare Worker, который хранит секреты. Worker кладёт аудио в закрытый черновой Release и запускает задачу GitHub Actions: расшифровка, перевод, шифрование и публикация результата.

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

## Структура проекта

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

## Развёртывание с нуля

1. Создайте **публичный** репозиторий (например, `dabir`) с README.

2. Загрузите все файлы проекта в корень репозитория, сохранив папки. Скрытую папку `.github` создайте через **Add file → Create new file**.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. Сгенерируйте случайный секрет (команда ниже) и сохраните его как секрет Actions `JOB_SECRET`.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. Создайте Fine-grained токен только для этого репозитория: Contents и Actions, оба Read and write.

7. В Cloudflare создайте Worker (Hello World), вставьте `worker/src/index.js`, добавьте переменные и секреты из таблицы и нажмите Deploy.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Впишите адрес Worker в `config.js`, сделайте Commit и обновите сайт через Ctrl+Shift+R.

9. Загрузите короткий тестовый файл. Первый запуск медленный: модели скачиваются и кэшируются.

## Настройка

Имена чувствительны к регистру. `GH_TOKEN` и `JOB_SECRET` должны быть типа Secret; `JOB_SECRET` одинаков в GitHub и Cloudflare.

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

## Разработка и тесты

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## Конфиденциальность и безопасность

- Аудио хранится только в закрытом черновом Release и удаляется после обработки.
- Результаты шифруются AES-GCM; ключ не покидает браузер загрузившего.
- Токен GitHub хранится только в Cloudflare и не отправляется посетителям.
- Копии на сервере удаляются примерно через два часа. Для чувствительных данных используйте приватный репозиторий.

## Ограничения

- Whisper хуже работает с персидским, чем с английским: выберите язык и лучшее качество и проверьте текст.
- GitHub Actions ограничивает задачу примерно 6 часами; очень длинное аудио на самом медленном качестве может не успеть.
- Метки говорящих только текстовые; разделение голосов по отдельным аудиофайлам не реализовано.
- Реален только прогресс загрузки; обработка показывает «в очереди», «выполняется» и «сохранение».
- У бесплатных тарифов GitHub и Cloudflare есть лимиты.
- Перевод, шумоподавление, метки говорящих и файлы до 1 ГБ реализованы, но проверены на практике ограниченно.

## Устранение неполадок

| ⚠️ | 🔧 |
|---|---|
| Сообщение «сервер не настроен» | `config.js` пуст или закэширован: укажите адрес Worker и полностью обновите страницу (или `config.js?v=2`). |
| `Failed to fetch` при загрузке | `ALLOWED_ORIGIN` должен быть точно `https://<user>.github.io` (без слэша в конце); повторите Deploy. |
| 502 «не удалось создать задачу» | `GH_TOKEN` неверный, просрочен или без прав; замените его. |
| Задача остаётся в очереди | Откройте вкладку Actions; проверьте права workflow и наличие `process.yml`. |
| Результат «неполная конфигурация» | `JOB_SECRET` отсутствует или отличается в GitHub и Cloudflare. |
| Запуск идёт очень долго | Читайте строки этапов в логе; первый запуск скачивает модели; если этап завис, отмените и повторите. |

## Лицензия и благодарности

Добавьте свой файл `LICENSE`. У сторонних компонентов свои лицензии:

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
