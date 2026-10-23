<div dir="rtl">

# Dabir (دبیر)

> ترجمے کے ساتھ تقریر سے متن: فارسی اور انگریزی ان پٹ، 20 زبانوں میں آؤٹ پٹ۔

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · **اردو** · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir ریکارڈنگ کو متن میں بدلتا ہے۔ آڈیو فائل (mp3، m4a، wav وغیرہ، 1 GB تک) اپ لوڈ کریں؛ یہ پہچانتا ہے کہ وہ فارسی ہے یا انگریزی، اسے متن میں لکھتا ہے اور چاہیں تو 20 دیگر زبانوں میں ترجمہ کرتا ہے۔ یہ اوپن سورس ماڈلز کے ساتھ آپ کی اپنی GitHub ریپوزٹری میں چلتا ہے اور AI API کلید کی ضرورت نہیں۔

## خصوصیات

- 1 GB تک دوبارہ شروع ہونے والی ٹکڑوں میں اپ لوڈ، سست نیٹ ورک کے لیے براؤزر میں اختیاری کمپریشن
- فارسی/انگریزی کی خودکار شناخت اور تین معیاری درجے
- 20 زبانوں میں آف لائن ترجمہ (Argos Translate)
- اختیاری شور کا خاتمہ اور بولنے والوں کے لیبل
- خفیہ شدہ نتائج جنہیں صرف اپ لوڈ کرنے والا براؤزر پڑھ سکتا ہے
- دو گھنٹے کی نجی لائبریری، کاپی اور TXT/SRT برآمد، فارسی اور انگریزی انٹرفیس

## یہ کیسے کام کرتا ہے

سائٹ (GitHub Pages) ایک چھوٹے Cloudflare Worker سے بات کرتی ہے جو رازدارانہ کلیدیں رکھتا ہے۔ Worker آڈیو کو نجی ڈرافٹ Release میں رکھتا ہے اور GitHub Actions جاب چلاتا ہے جو متن نکالتی، ترجمہ کرتی، انکرپٹ کرتی اور نتیجہ شائع کرتی ہے۔

<div dir="ltr">

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

</div>

🧱 GitHub Pages · Cloudflare Workers · GitHub Actions · Python 3.11 · faster-whisper (Whisper) · Argos Translate · noisereduce · Resemblyzer · lamejs · FFmpeg · Web Crypto (AES-GCM) · IndexedDB

## پروجیکٹ کا ڈھانچہ

<div dir="ltr">

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

</div>

## شروع سے ڈپلائے کرنا

1. README کے ساتھ ایک **عوامی** ریپوزٹری بنائیں (مثلاً `dabir`)۔

2. پروجیکٹ کی تمام فائلیں فولڈروں سمیت ریپوزٹری کی روٹ میں اپ لوڈ کریں۔ چھپا ہوا فولڈر `.github` **Add file → Create new file** سے بنائیں۔

3. **Settings → Actions → General → Workflow permissions →** Read and write منتخب کریں۔

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`۔

5. ایک بے ترتیب خفیہ کلید بنائیں (نیچے کمانڈ) اور اسے Actions سیکرٹ `JOB_SECRET` کے طور پر محفوظ کریں۔

<div dir="ltr">

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

</div>

6. صرف اسی ریپوزٹری کے لیے Fine-grained ٹوکن بنائیں: Contents اور Actions دونوں Read and write۔

7. Cloudflare میں Worker (Hello World) بنائیں، `worker/src/index.js` پیسٹ کریں، جدول کے متغیرات اور سیکرٹس شامل کریں اور Deploy کریں۔

<div dir="ltr">

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

</div>

8. Worker کا پتہ `config.js` میں لکھیں، Commit کریں اور Ctrl+Shift+R سے سائٹ ریفریش کریں۔

9. ایک مختصر ٹیسٹ فائل اپ لوڈ کریں۔ پہلی بار سست ہوگا کیونکہ ماڈل ڈاؤن لوڈ اور کیش ہوتے ہیں۔

## ترتیبات

نام حروف کی بڑی/چھوٹی شکل کے حساس ہیں۔ `GH_TOKEN` اور `JOB_SECRET` کی قسم Secret ہو، اور `JOB_SECRET` GitHub اور Cloudflare میں ایک ہی ہو۔

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

## ڈیولپمنٹ اور ٹیسٹ

<div dir="ltr">

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

</div>

## رازداری اور سکیورٹی

- آڈیو صرف نجی ڈرافٹ Release میں رہتی ہے اور پراسیسنگ کے بعد حذف ہو جاتی ہے۔
- نتائج AES-GCM سے انکرپٹ ہوتے ہیں؛ کلید اپ لوڈ کرنے والے براؤزر سے باہر نہیں جاتی۔
- GitHub ٹوکن صرف Cloudflare میں ہے اور وزیٹرز کو کبھی نہیں بھیجا جاتا۔
- سرور کی کاپیاں تقریباً دو گھنٹے بعد ختم ہو جاتی ہیں۔ حساس مواد کے لیے نجی ریپوزٹری استعمال کریں۔

## حدود

- Whisper فارسی میں انگریزی سے کم درست ہے: زبان اور بہترین معیار چنیں اور متن کی جانچ کریں۔
- GitHub Actions ایک جاب کو تقریباً 6 گھنٹے تک محدود کرتا ہے؛ بہت لمبی آڈیو سست ترین معیار پر مکمل نہ ہو سکتی ہے۔
- بولنے والوں کے لیبل صرف متن میں ہیں؛ ہر آواز کو الگ آڈیو فائل میں بانٹنا نافذ نہیں۔
- صرف اپ لوڈ کی پیش رفت حقیقی ہے؛ پراسیسنگ میں قطار، جاری اور محفوظ کرنا دکھایا جاتا ہے۔
- GitHub اور Cloudflare کے مفت پلانز کی استعمال کی حدود ہیں۔
- ترجمہ، شور کا خاتمہ، بولنے والوں کے لیبل اور 1 GB فائلیں نافذ ہیں مگر حقیقی ٹیسٹنگ محدود ہے۔

## مسائل کا حل

| ⚠️ | 🔧 |
|---|---|
| پیغام «سرور ترتیب نہیں دیا گیا» | `config.js` خالی یا کیش شدہ ہے: Worker کا پتہ لکھیں اور صفحہ مکمل ریفریش کریں (یا `config.js?v=2`)۔ |
| اپ لوڈ میں `Failed to fetch` | `ALLOWED_ORIGIN` بالکل `https://<user>.github.io` ہو (آخر میں سلیش نہیں)؛ دوبارہ Deploy کریں۔ |
| 502 «جاب بنانے میں ناکامی» | `GH_TOKEN` غلط، میعاد ختم یا اجازتوں کے بغیر ہے؛ اسے بدلیں۔ |
| جاب قطار میں رکی رہتی ہے | Actions ٹیب کھولیں؛ workflow اجازتیں اور `process.yml` کی موجودگی جانچیں۔ |
| نتیجہ «نامکمل ترتیب» | `JOB_SECRET` موجود نہیں یا GitHub اور Cloudflare میں مختلف ہے۔ |
| رن بہت دیر لیتا ہے | رن لاگ میں مراحل کی سطریں پڑھیں؛ پہلا رن ماڈل ڈاؤن لوڈ کرتا ہے؛ مرحلہ اٹکے تو منسوخ کر کے دوبارہ چلائیں۔ |

## لائسنس اور اعتراف

اپنی پسند کی `LICENSE` فائل شامل کریں۔ تھرڈ پارٹی اجزا کے اپنے لائسنس ہیں:

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

</div>
