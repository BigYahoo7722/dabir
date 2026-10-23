<div dir="rtl">

# Dabir (دبیر)

> تبدیل گفتار به متن با ترجمه: ورودی فارسی و انگلیسی، خروجی در ۲۰ زبان.

[English](../README.md) · **فارسی** · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

دبیر ضبط‌های صوتی را به متن تبدیل می‌کند. فایل صوتی (mp3، m4a، wav و… تا ۱ گیگابایت) را آپلود کنید؛ دبیر فارسی یا انگلیسی بودن آن را تشخیص می‌دهد، متن را درمی‌آورد و در صورت نیاز به ۲۰ زبان دیگر ترجمه می‌کند. همه‌چیز با مدل‌های متن‌باز داخل مخزن گیت‌هاب خودتان اجرا می‌شود و به کلید API هوش مصنوعی نیاز ندارد.

## ویژگی‌ها

- آپلود تکه‌ای تا ۱ گیگابایت با تلاش مجدد، و فشرده‌سازی اختیاری در مرورگر برای اینترنت ضعیف
- تشخیص خودکار فارسی/انگلیسی و سه سطح کیفیت
- ترجمهٔ آفلاین به ۲۰ زبان (Argos Translate)
- حذف نویز و برچسب گوینده (اختیاری)
- نتیجهٔ رمزنگاری‌شده که فقط مرورگرِ آپلودکننده می‌خواند
- کتابخانهٔ خصوصی دوساعته، کپی و خروجی TXT/SRT، رابط فارسی و انگلیسی

## طرز کار

سایت (GitHub Pages) با یک Worker کوچک در Cloudflare که رمزها را نگه می‌دارد صحبت می‌کند. Worker صدا را در یک Release پیش‌نویس خصوصی می‌گذارد و یک کار GitHub Actions را اجرا می‌کند که رونویسی، ترجمه و رمزنگاری می‌کند و نتیجه را ثبت می‌کند.

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

## ساختار پروژه

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

## استقرار از صفر

1. یک مخزن **عمومی** (مثلاً `dabir`) با README بسازید.

2. همهٔ فایل‌های پروژه را با همان پوشه‌ها در ریشهٔ مخزن آپلود کنید. پوشهٔ مخفی `.github` را با **Add file → Create new file** بسازید.

3. **Settings → Actions → General → Workflow permissions →** گزینهٔ Read and write.

4. **Settings → Pages →** Deploy from a branch ← `main` / `(root)`.

5. یک رمز تصادفی بسازید (دستور پایین) و آن را به‌عنوان Secret گیت‌هاب با نام `JOB_SECRET` ذخیره کنید.

<div dir="ltr">

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

</div>

6. یک توکن Fine-grained فقط برای همین مخزن بسازید: دسترسی Contents و Actions، هر دو Read and write.

7. در Cloudflare یک Worker (Hello World) بسازید، کد `worker/src/index.js` را جایگزین کنید، متغیرها و Secretهای جدول را اضافه و Deploy کنید.

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

8. آدرس Worker را در `config.js` بگذارید، Commit کنید و سایت را با Ctrl+Shift+R تازه کنید.

9. یک فایل کوتاه آزمایشی آپلود کنید. اجرای اول کند است، چون مدل‌ها دانلود و ذخیره می‌شوند.

## پیکربندی

نام‌ها به حروف بزرگ و کوچک حساس‌اند. `GH_TOKEN` و `JOB_SECRET` باید از نوع Secret باشند و `JOB_SECRET` در گیت‌هاب و Cloudflare یکی باشد.

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

## توسعه و تست

<div dir="ltr">

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

</div>

## حریم خصوصی و امنیت

- صدا فقط در یک Release پیش‌نویس خصوصی می‌ماند و پس از پردازش پاک می‌شود.
- نتیجه با AES-GCM رمز می‌شود و کلید هرگز مرورگر آپلودکننده را ترک نمی‌کند.
- توکن گیت‌هاب فقط در Cloudflare است و هرگز به بازدیدکنندگان فرستاده نمی‌شود.
- نسخه‌های سرور حدود دو ساعت بعد حذف می‌شوند. برای محتوای حساس از مخزن خصوصی استفاده کنید.

## محدودیت‌ها

- دقت Whisper در فارسی کمتر از انگلیسی است: زبان و بالاترین کیفیت را انتخاب و متن را بازبینی کنید.
- GitHub Actions هر کار را حدود ۶ ساعت محدود می‌کند؛ صوت خیلی طولانی با کندترین کیفیت ممکن است تمام نشود.
- برچسب گوینده فقط متنی است؛ جداسازی صدای هر نفر در فایل جدا پیاده‌سازی نشده است.
- فقط پیشرفت آپلود واقعی است؛ پردازش «در صف، در حال اجرا، ثبت نتیجه» را نشان می‌دهد.
- پلن‌های رایگان گیت‌هاب و Cloudflare سقف مصرف دارند.
- ترجمه، حذف نویز، برچسب گوینده و فایل‌های ۱ گیگابایتی پیاده‌سازی شده‌اند اما در شرایط واقعی کم آزموده شده‌اند.

## عیب‌یابی

| ⚠️ | 🔧 |
|---|---|
| پیام «سرور پیکربندی نشده» | `config.js` خالی یا کش‌شده است: آدرس Worker را بگذارید و سایت را کامل تازه کنید (یا `config.js?v=2`). |
| خطای `Failed to fetch` هنگام آپلود | `ALLOWED_ORIGIN` باید دقیقاً `https://<user>.github.io` باشد (بدون اسلش آخر)؛ دوباره Deploy کنید. |
| خطای ۵۰۲ «ساخت کار ناموفق بود» | `GH_TOKEN` اشتباه، منقضی یا بدون دسترسی است؛ آن را عوض کنید. |
| کار در صف می‌ماند | تب Actions را ببینید؛ دسترسی workflow و وجود `process.yml` را بررسی کنید. |
| نتیجه با خطای «پیکربندی ناقص» | `JOB_SECRET` نیست یا در گیت‌هاب و Cloudflare یکسان نیست. |
| اجرا خیلی طول می‌کشد | خطوط مرحله‌ها را در لاگ اجرا بخوانید؛ اجرای اول مدل‌ها را دانلود می‌کند؛ اگر مرحله‌ای گیر کرد، کنسل و دوباره اجرا کنید. |

## مجوز و منابع

فایل `LICENSE` دلخواه خودتان را اضافه کنید. اجزای شخص ثالث مجوز خودشان را دارند:

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
