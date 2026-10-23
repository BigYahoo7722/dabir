<div dir="rtl">

# Dabir (دبیر)

> تحويل الكلام إلى نص مع الترجمة: إدخال بالفارسية والإنجليزية وإخراج بـ 20 لغة.

[English](../README.md) · [فارسی](README.fa.md) · **العربية** · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

يحوّل «دبير» التسجيلات الصوتية إلى نص. ارفع ملفاً صوتياً (mp3 وm4a وwav… حتى 1 غيغابايت)، فيكتشف هل هو بالفارسية أم الإنجليزية، ويفرّغه نصاً، ويمكنه ترجمته إلى 20 لغة أخرى. يعمل بنماذج مفتوحة المصدر داخل مستودع GitHub الخاص بك ودون مفاتيح API للذكاء الاصطناعي.

## الميزات

- رفع مجزأ قابل للاستئناف حتى 1 غيغابايت، مع ضغط اختياري داخل المتصفح للشبكات البطيئة
- اكتشاف تلقائي للفارسية/الإنجليزية وثلاثة مستويات جودة
- ترجمة دون اتصال إلى 20 لغة (Argos Translate)
- إزالة ضوضاء ووسم المتحدثين (اختياري)
- نتائج مشفّرة لا يقرؤها إلا المتصفح الذي رفع الملف
- مكتبة خاصة لمدة ساعتين، نسخ وتصدير TXT/SRT، وواجهة بالفارسية والإنجليزية

## طريقة العمل

يتصل الموقع (GitHub Pages) بـ Cloudflare Worker صغير يحفظ الأسرار. يخزّن الـ Worker الصوت في Release مسودة خاص ويشغّل مهمة GitHub Actions تفرّغ النص وتترجمه وتشفّره وتنشر النتيجة.

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

## بنية المشروع

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

## النشر من الصفر

1. أنشئ مستودعاً **عاماً** (مثل `dabir`) مع ملف README.

2. ارفع كل ملفات المشروع إلى جذر المستودع مع الحفاظ على المجلدات. المجلد المخفي `.github` يُنشأ عبر **Add file → Create new file**.

3. **Settings → Actions → General → Workflow permissions →** اختر Read and write.

4. **Settings → Pages →** Deploy from a branch ← `main` / `(root)`.

5. أنشئ سراً عشوائياً (الأمر أدناه) واحفظه كسر Actions باسم `JOB_SECRET`.

<div dir="ltr">

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

</div>

6. أنشئ رمز Fine-grained لهذا المستودع فقط: صلاحيتا Contents وActions كلتاهما Read and write.

7. في Cloudflare أنشئ Worker (Hello World) والصق `worker/src/index.js` وأضف المتغيرات والأسرار من الجدول ثم Deploy.

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

8. ضع عنوان الـ Worker في `config.js` ثم Commit وحدّث الموقع بـ Ctrl+Shift+R.

9. ارفع ملفاً قصيراً للتجربة. التشغيل الأول بطيء لأن النماذج تُنزَّل وتُخزَّن.

## الإعدادات

الأسماء حساسة لحالة الأحرف. يجب أن يكون `GH_TOKEN` و`JOB_SECRET` من النوع Secret، وبقيمة `JOB_SECRET` نفسها في GitHub وCloudflare.

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

## التطوير والاختبارات

<div dir="ltr">

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

</div>

## الخصوصية والأمان

- يبقى الصوت فقط في Release مسودة خاص ويُحذف بعد المعالجة.
- النتائج مشفّرة بـ AES-GCM والمفتاح لا يغادر متصفح الرافع.
- رمز GitHub موجود في Cloudflare فقط ولا يُرسل للزوار.
- تنتهي نسخ الخادم بعد نحو ساعتين. للمحتوى الحساس استخدم مستودعاً خاصاً.

## القيود

- دقة Whisper في الفارسية أقل منها في الإنجليزية: اختر اللغة وأعلى جودة ثم راجع النص.
- يحدّد GitHub Actions المهمة بنحو 6 ساعات؛ قد لا ينتهي صوت طويل جداً بأبطأ جودة.
- وسم المتحدثين نصي فقط؛ فصل صوت كل شخص في ملف مستقل غير منفّذ.
- تقدّم الرفع وحده حقيقي؛ المعالجة تعرض: في الطابور، قيد التنفيذ، حفظ النتيجة.
- للخطط المجانية في GitHub وCloudflare حدود استخدام.
- الترجمة وإزالة الضوضاء ووسم المتحدثين والملفات بحجم 1 غيغابايت منفّذة لكن اختبارها الفعلي محدود.

## استكشاف الأخطاء

| ⚠️ | 🔧 |
|---|---|
| رسالة «الخادم غير مهيأ» | ملف `config.js` فارغ أو مخزّن مؤقتاً: ضع عنوان Worker وحدّث الصفحة بالكامل (أو `config.js?v=2`). |
| خطأ `Failed to fetch` أثناء الرفع | يجب أن يكون `ALLOWED_ORIGIN` تماماً `https://<user>.github.io` دون شرطة مائلة أخيرة؛ أعد Deploy. |
| خطأ 502 «فشل إنشاء المهمة» | `GH_TOKEN` خاطئ أو منتهٍ أو بلا صلاحيات؛ استبدله. |
| المهمة تبقى في الطابور | افتح تبويب Actions وتحقق من صلاحيات workflow ووجود `process.yml`. |
| نتيجة «إعداد ناقص» | `JOB_SECRET` مفقود أو مختلف بين GitHub وCloudflare. |
| التشغيل يستغرق وقتاً طويلاً | اقرأ أسطر المراحل في سجل التشغيل؛ التشغيل الأول ينزّل النماذج؛ ألغِ وأعد المحاولة إذا علقت مرحلة. |

## الترخيص والمصادر

أضف ملف `LICENSE` الذي تختاره. للمكوّنات الخارجية تراخيصها:

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
