# Dabir (دبیر)

> অনুবাদসহ স্পিচ-টু-টেক্সট: ফারসি ও ইংরেজি ইনপুট, ২০টি ভাষায় আউটপুট।

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · **বাংলা** · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir রেকর্ডিংকে টেক্সটে রূপান্তর করে। অডিও ফাইল (mp3, m4a, wav ইত্যাদি, ১ GB পর্যন্ত) আপলোড করুন; এটি ফারসি না ইংরেজি তা শনাক্ত করে, লিখিত রূপ দেয় এবং চাইলে আরও ২০টি ভাষায় অনুবাদ করে। এটি ওপেন-সোর্স মডেলে আপনার নিজের GitHub রিপোজিটরিতে চলে এবং কোনো AI API কী লাগে না।

## বৈশিষ্ট্য

- ১ GB পর্যন্ত পুনরায় শুরু করা যায় এমন খণ্ডে আপলোড, ধীর নেটওয়ার্কের জন্য ব্রাউজারে ঐচ্ছিক কম্প্রেশন
- ফারসি/ইংরেজি স্বয়ংক্রিয় শনাক্তকরণ ও তিন স্তরের মান
- ২০টি ভাষায় অফলাইন অনুবাদ (Argos Translate)
- ঐচ্ছিক শব্দ-দূষণ হ্রাস ও বক্তা লেবেল
- এনক্রিপ্টেড ফলাফল, যা শুধু আপলোডকারী ব্রাউজার পড়তে পারে
- দুই ঘণ্টার ব্যক্তিগত লাইব্রেরি, কপি ও TXT/SRT এক্সপোর্ট, ফারসি ও ইংরেজি ইন্টারফেস

## কীভাবে কাজ করে

সাইট (GitHub Pages) একটি ছোট Cloudflare Worker-এর সঙ্গে কথা বলে, যেখানে গোপন মান থাকে। Worker অডিও একটি ব্যক্তিগত খসড়া Release-এ রাখে এবং GitHub Actions কাজ চালু করে, যা লিপ্যন্তর, অনুবাদ, এনক্রিপশন ও ফলাফল প্রকাশ করে।

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

## প্রকল্পের কাঠামো

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

## শূন্য থেকে ডিপ্লয়

1. README সহ একটি **পাবলিক** রিপোজিটরি তৈরি করুন (যেমন `dabir`)।

2. প্রকল্পের সব ফাইল ফোল্ডারসহ রিপোজিটরির রুটে আপলোড করুন। লুকানো `.github` ফোল্ডার **Add file → Create new file** দিয়ে বানান।

3. **Settings → Actions → General → Workflow permissions →** Read and write বেছে নিন।

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`।

5. একটি এলোমেলো গোপন মান তৈরি করুন (নিচের কমান্ড) এবং Actions সিক্রেট `JOB_SECRET` হিসেবে সংরক্ষণ করুন।

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. শুধু এই রিপোজিটরির জন্য Fine-grained টোকেন বানান: Contents ও Actions দুটোই Read and write।

7. Cloudflare-এ Worker (Hello World) বানান, `worker/src/index.js` পেস্ট করুন, টেবিলের ভেরিয়েবল ও সিক্রেট যোগ করে Deploy করুন।

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Worker-এর ঠিকানা `config.js`-এ দিন, Commit করুন এবং Ctrl+Shift+R দিয়ে সাইট রিফ্রেশ করুন।

9. একটি ছোট পরীক্ষামূলক ফাইল আপলোড করুন। প্রথমবার ধীর হবে, কারণ মডেল ডাউনলোড ও ক্যাশ হয়।

## কনফিগারেশন

নামগুলো বড়/ছোট হাতের অক্ষরের প্রতি সংবেদনশীল। `GH_TOKEN` ও `JOB_SECRET` Secret ধরনের হতে হবে; `JOB_SECRET` GitHub ও Cloudflare-এ একই রাখুন।

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

## ডেভেলপমেন্ট ও টেস্ট

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## গোপনীয়তা ও নিরাপত্তা

- অডিও শুধু ব্যক্তিগত খসড়া Release-এ থাকে এবং প্রক্রিয়ার পর মুছে যায়।
- ফলাফল AES-GCM দিয়ে এনক্রিপ্টেড; চাবি আপলোডকারীর ব্রাউজার ছাড়ে না।
- GitHub টোকেন শুধু Cloudflare-এ থাকে, দর্শকদের কাছে কখনো পাঠানো হয় না।
- সার্ভারের কপি প্রায় দুই ঘণ্টা পরে মেয়াদোত্তীর্ণ হয়। স্পর্শকাতর বিষয়বস্তুর জন্য ব্যক্তিগত রিপোজিটরি ব্যবহার করুন।

## সীমাবদ্ধতা

- Whisper ফারসিতে ইংরেজির চেয়ে কম নির্ভুল: ভাষা ও সর্বোচ্চ মান বেছে লেখাটি যাচাই করুন।
- GitHub Actions একটি কাজকে প্রায় ৬ ঘণ্টায় সীমাবদ্ধ করে; খুব দীর্ঘ অডিও সবচেয়ে ধীর মানে শেষ নাও হতে পারে।
- বক্তা লেবেল শুধু টেক্সটে; প্রতিটি কণ্ঠ আলাদা অডিও ফাইলে ভাগ করা বাস্তবায়িত হয়নি।
- শুধু আপলোডের অগ্রগতি বাস্তব; প্রক্রিয়াকরণে সারি, চলমান ও সংরক্ষণ দেখায়।
- GitHub ও Cloudflare-এর বিনামূল্যের প্ল্যানের ব্যবহারসীমা আছে।
- অনুবাদ, শব্দ-দূষণ হ্রাস, বক্তা লেবেল ও ১ GB ফাইল বাস্তবায়িত, তবে বাস্তব পরীক্ষা সীমিত।

## সমস্যা সমাধান

| ⚠️ | 🔧 |
|---|---|
| “সার্ভার কনফিগার করা নেই” বার্তা | `config.js` খালি বা ক্যাশড: Worker-এর ঠিকানা দিন এবং পেজ পুরো রিফ্রেশ করুন (বা `config.js?v=2`)। |
| আপলোডে `Failed to fetch` | `ALLOWED_ORIGIN` ঠিক `https://<user>.github.io` হতে হবে (শেষে স্ল্যাশ নয়); আবার Deploy করুন। |
| 502 “কাজ তৈরি ব্যর্থ” | `GH_TOKEN` ভুল, মেয়াদোত্তীর্ণ বা অনুমতিহীন; বদলে নিন। |
| কাজ সারিতে আটকে থাকে | Actions ট্যাব খুলুন; workflow অনুমতি ও `process.yml` আছে কি না দেখুন। |
| ফলাফল “অসম্পূর্ণ কনফিগারেশন” | `JOB_SECRET` নেই বা GitHub ও Cloudflare-এ আলাদা। |
| রান অনেক সময় নেয় | রান লগে ধাপের লাইনগুলো পড়ুন; প্রথম রানে মডেল ডাউনলোড হয়; ধাপ আটকে গেলে বাতিল করে আবার চালান। |

## লাইসেন্স ও কৃতজ্ঞতা

নিজের পছন্দের `LICENSE` ফাইল যোগ করুন। তৃতীয়-পক্ষের উপাদানের নিজস্ব লাইসেন্স আছে:

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
