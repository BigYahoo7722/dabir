# dabir

وب‌سایت تبدیل گفتار به متن با ترجمه — الهام‌گرفته از ایران باستان.
**نام رسمی: dabir** · made by Big_Yahoo8844

## قابلیت‌ها (وضعیت واقعی)
- آپلود فایل صوتی تا ۱ گیگابایت (mp3، m4a، wav، flac، ogg…) به‌صورت تکه‌های ۶۴ مگابایتی با تلاش مجدد هر تکه.
- تشخیص خودکار زبان بین **فارسی و انگلیسی** (یا انتخاب دستی)، رونویسی با Whisper (faster-whisper)، سه کیفیت: سریع=`small`، متعادل=`medium`، دقیق‌ترین=`large-v3`.
- ترجمه آفلاین با Argos Translate به فارسی و ۱۹ زبان دیگر: عربی، ترکی، فرانسوی، آلمانی، اسپانیایی، پرتغالی، ایتالیایی، روسی، چینی، ژاپنی، کره‌ای، هندی، اردو، بنگالی، اندونزیایی، هلندی، لهستانی، اوکراینی، یونانی (وجود بستهٔ دوطرفه با انگلیسی در فهرست رسمی Argos بررسی شده؛ کیفیت ترجمه آزموده نشده).
- حذف نویز (اختیاری، noisereduce) و برچسب‌گذاری گویندگان (اختیاری، Resemblyzer). **جداسازی فایل صوتی هر گوینده و تشخیص نوع نویز پیاده‌سازی نشده است.**
- کتابخانهٔ مرورگر: هر کار تا یک ساعت پس از اتمام می‌ماند؛ حذف دستی با تأیید.
- خروجی: کپی (با بازخورد واقعی)، دانلود TXT، دانلود SRT.
- انتخاب زبان‌های مقصد (پیش‌فرض فارسی) در `localStorage` با کلید `dabir_target_languages_v1` ذخیره می‌شود؛ فقط محلی است و بین دستگاه‌ها همگام نمی‌شود.

## معماری
```
مرورگر (GitHub Pages: index.html + config.js)
   │  HTTPS، بدون توکن
   ▼
Cloudflare Worker (worker/src/index.js)  ← Secretها: GH_TOKEN، JOB_SECRET
   │  GitHub API (Release پیش‌نویس خصوصی، dispatch)
   ▼
GitHub Actions (.github/workflows/process.yml → process.py)
   │  نتیجهٔ رمزنگاری‌شده (AES-GCM) در شاخهٔ jobs
   ▼
Worker → مرورگر (رمزگشایی با کلید همان کار؛ کلید فقط نزد کاربر)
```
- کاربر هیچ توکن یا نام مخزنی وارد نمی‌کند. توکن فقط Secret سمت Worker است.
- هر کار یک `id` تصادفی و یک کلید `HMAC(JOB_SECRET, id:release)` دارد؛ بدون کلید نمی‌شود وضعیت یا نتیجه را گرفت. جداسازی کاربران بر همین پایه است.
- فایل صوتی فقط در Release **پیش‌نویس** (غیرعمومی) می‌ماند و پس از پردازش حذف می‌شود؛ پاک‌سازی ساعتی Releaseهای باقی‌مانده را هم می‌برد.
- نتیجه قبل از ثبت در مخزن رمز می‌شود؛ حتی اگر مخزن عمومی باشد متن نتیجه خوانا نیست. فقط `id` کار و زمان اتمام آشکار است. اگر می‌خواهید این هم پنهان بماند، مخزن را خصوصی کنید.
- نگه‌داری سرور: `RETAIN_SECONDS` در `.github/workflows/cleanup.yml` (پیش‌فرض ۳۹۰۰ ثانیه ≈ ۶۵ دقیقه).

## ساختار فایل‌ها
| مسیر | کار |
|---|---|
| `index.html`, `config.js` | رابط کاربری؛ آدرس Worker در `config.js` |
| `worker/` | API امن (Cloudflare Worker) و `wrangler.toml` |
| `process.py` | دانلود تکه‌ها، رمزگشایی صوت با FFmpeg، نویزگیری، رونویسی، گویندگان، ترجمه، رمزنگاری نتیجه |
| `cleanup.py` | پاک‌سازی نتایج و Releaseهای قدیمی |
| `.github/workflows/` | `process.yml` (ربات)، `cleanup.yml` (ساعتی) |
| `tests/` | `selftest.py`، `pipeline_mock.py`، `worker.test.mjs`، `ui.test.cjs` |
| `requirements*.txt` | وابستگی‌های ربات (گویندگان جدا و اختیاری) |

## استقرار گام‌به‌گام
1. **GitHub Pages:** Settings → Pages → Deploy from a branch → `main` / root. Settings → Actions → General → Workflow permissions: Read and write.
2. **توکن Worker:** یک Fine-grained token فقط برای همین مخزن با دسترسی Contents و Actions روی Read and write بسازید (فقط برای Worker؛ به کاربران داده نمی‌شود).
3. **یک رمز تصادفی بلند** بسازید (مثلاً `openssl rand -hex 32`) و آن را همزمان در دو جا بگذارید: Secret مخزن با نام `JOB_SECRET` (Settings → Secrets and variables → Actions) و Secret کلودفلر (مرحلهٔ بعد). هر دو باید یکسان باشند.
4. **Worker:** حساب Cloudflare بسازید، سپس:
   ```
   cd worker
   npx wrangler login
   npx wrangler secret put GH_TOKEN      # توکن مرحلهٔ ۲
   npx wrangler secret put JOB_SECRET    # رمز مرحلهٔ ۳
   npx wrangler deploy
   ```
   مقدارهای `REPO` و `ALLOWED_ORIGIN` را در `worker/wrangler.toml` با مخزن و آدرس سایت خودتان یکی کنید.
5. آدرس Worker را در `config.js` بگذارید (`window.DABIR_API = "https://dabir-api.<نام>.workers.dev"`) و commit کنید.
6. با یک فایل کوتاه تست کنید؛ اجرای اول چند ده دقیقه برای دانلود مدل‌ها طول می‌کشد (بعد کش می‌شود).

## اجرای تست‌ها
```
pip install -r requirements.txt
npm install
npm test        # selftest.py + pipeline_mock.py + worker.test.mjs + ui.test.cjs
```
نیازمند FFmpeg. شرح نتایج: `TEST_REPORT.md`.

## محدودیت‌ها
- فایل‌های بسیار طولانی با کیفیت «دقیق‌ترین» ممکن است از سقف ۶ ساعتی GitHub Actions بگذرند.
- Worker رایگان بدنهٔ درخواست را تا ۱۰۰ مگابایت می‌پذیرد (تکه‌ها ۶۴ مگابایت‌اند) و سقف درخواست روزانه دارد. پرسش وضعیت هر ۱۵ ثانیه است؛ برای ترافیک زیاد باید Cache یا Durable Object اضافه شود.
- محدودیت نرخ درخواست در کد نیست: فقط سقف کارهای هم‌زمان (`MAX_ACTIVE`) هست. برای محافظت بیشتر، Rate Limiting Rule در داشبورد کلودفلر بسازید.
- نوار پیشرفت فقط برای آپلود واقعی است. در پردازش، مرحلهٔ دقیق (تشخیص زبان، رونویسی…) از ربات گزارش نمی‌شود؛ فقط «در صف / در حال پردازش / ثبت نتیجه» نمایش داده می‌شود.
- مجوزها: Whisper (MIT)، faster-whisper (MIT)، Argos Translate (MIT؛ مدل‌های ترجمه مجوز خودشان را دارند)، noisereduce (MIT)، Resemblyzer (Apache-2.0). پیش از استفادهٔ تجاری مجوز مدل‌ها را بررسی کنید.
