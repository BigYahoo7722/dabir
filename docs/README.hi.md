# Dabir (دبیر)

> अनुवाद के साथ स्पीच-टू-टेक्स्ट: फ़ारसी और अंग्रेज़ी इनपुट, 20 भाषाओं में आउटपुट।

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · **हिन्दी** · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir रिकॉर्डिंग को टेक्स्ट में बदलता है। ऑडियो फ़ाइल (mp3, m4a, wav आदि, 1 GB तक) अपलोड करें; यह पहचानता है कि वह फ़ारसी है या अंग्रेज़ी, उसे लिखित रूप देता है और चाहें तो 20 अन्य भाषाओं में अनुवाद करता है। यह ओपन-सोर्स मॉडल से आपकी अपनी GitHub रिपॉज़िटरी में चलता है और इसमें AI API कुंजी नहीं लगती।

## विशेषताएँ

- 1 GB तक फिर से शुरू होने वाला खंडों में अपलोड, धीमे नेटवर्क के लिए ब्राउज़र में वैकल्पिक संपीड़न
- फ़ारसी/अंग्रेज़ी की स्वचालित पहचान और तीन गुणवत्ता स्तर
- 20 भाषाओं में ऑफ़लाइन अनुवाद (Argos Translate)
- वैकल्पिक शोर-निवारण और वक्ता लेबल
- एन्क्रिप्टेड परिणाम, जिन्हें केवल अपलोड करने वाला ब्राउज़र पढ़ सकता है
- दो घंटे की निजी लाइब्रेरी, कॉपी और TXT/SRT निर्यात, फ़ारसी व अंग्रेज़ी इंटरफ़ेस

## यह कैसे काम करता है

साइट (GitHub Pages) एक छोटे Cloudflare Worker से बात करती है जो गोपनीय कुंजियाँ रखता है। Worker ऑडियो को निजी ड्राफ़्ट Release में रखता है और GitHub Actions जॉब शुरू करता है, जो लिप्यंतरण, अनुवाद, एन्क्रिप्शन और परिणाम का प्रकाशन करता है।

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

## प्रोजेक्ट संरचना

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

## शुरू से डिप्लॉय करना

1. README के साथ एक **सार्वजनिक** रिपॉज़िटरी बनाएँ (जैसे `dabir`)।

2. प्रोजेक्ट की सभी फ़ाइलें फ़ोल्डरों सहित रिपॉज़िटरी की रूट में अपलोड करें। छिपा फ़ोल्डर `.github` **Add file → Create new file** से बनाएँ।

3. **Settings → Actions → General → Workflow permissions →** Read and write चुनें।

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`।

5. एक यादृच्छिक गुप्त कुंजी बनाएँ (नीचे का कमांड) और उसे Actions सीक्रेट `JOB_SECRET` के रूप में सहेजें।

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. केवल इसी रिपॉज़िटरी के लिए Fine-grained टोकन बनाएँ: Contents और Actions, दोनों Read and write।

7. Cloudflare में Worker (Hello World) बनाएँ, `worker/src/index.js` पेस्ट करें, तालिका के वेरिएबल और सीक्रेट जोड़ें और Deploy करें।

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Worker का पता `config.js` में डालें, Commit करें और Ctrl+Shift+R से साइट रीफ़्रेश करें।

9. एक छोटी परीक्षण फ़ाइल अपलोड करें। पहली बार धीमा होगा, क्योंकि मॉडल डाउनलोड और कैश होते हैं।

## कॉन्फ़िगरेशन

नाम अक्षर-संवेदी हैं। `GH_TOKEN` और `JOB_SECRET` का प्रकार Secret होना चाहिए; `JOB_SECRET` GitHub और Cloudflare में एक ही रखें।

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

## विकास और परीक्षण

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## गोपनीयता और सुरक्षा

- ऑडियो केवल निजी ड्राफ़्ट Release में रहता है और प्रोसेसिंग के बाद हटा दिया जाता है।
- परिणाम AES-GCM से एन्क्रिप्टेड हैं; कुंजी अपलोड करने वाले ब्राउज़र से बाहर नहीं जाती।
- GitHub टोकन केवल Cloudflare में रहता है और आगंतुकों को कभी नहीं भेजा जाता।
- सर्वर की प्रतियाँ लगभग दो घंटे बाद समाप्त हो जाती हैं। संवेदनशील सामग्री के लिए निजी रिपॉज़िटरी इस्तेमाल करें।

## सीमाएँ

- Whisper फ़ारसी में अंग्रेज़ी से कम सटीक है: भाषा और सर्वोत्तम गुणवत्ता चुनें और पाठ की जाँच करें।
- GitHub Actions एक जॉब को लगभग 6 घंटे तक सीमित करता है; बहुत लंबा ऑडियो सबसे धीमी गुणवत्ता पर पूरा न हो सकता है।
- वक्ता लेबल केवल टेक्स्ट में हैं; हर आवाज़ को अलग ऑडियो फ़ाइल में बाँटना लागू नहीं है।
- केवल अपलोड की प्रगति वास्तविक है; प्रोसेसिंग में कतार, चालू और सहेजना दिखता है।
- GitHub और Cloudflare की मुफ़्त योजनाओं की उपयोग-सीमाएँ हैं।
- अनुवाद, शोर-निवारण, वक्ता लेबल और 1 GB फ़ाइलें लागू हैं, पर वास्तविक परीक्षण सीमित है।

## समस्या निवारण

| ⚠️ | 🔧 |
|---|---|
| “सर्वर कॉन्फ़िगर नहीं है” संदेश | `config.js` खाली या कैश्ड है: Worker का पता डालें और पेज पूरा रीफ़्रेश करें (या `config.js?v=2`)। |
| अपलोड में `Failed to fetch` | `ALLOWED_ORIGIN` ठीक `https://<user>.github.io` हो (अंत में स्लैश नहीं); फिर Deploy करें। |
| 502 “जॉब बनाना विफल” | `GH_TOKEN` गलत, समाप्त या अनुमति-रहित है; उसे बदलें। |
| जॉब कतार में अटका रहता है | Actions टैब खोलें; workflow अनुमतियाँ और `process.yml` की मौजूदगी जाँचें। |
| परिणाम “अधूरा कॉन्फ़िगरेशन” | `JOB_SECRET` नहीं है या GitHub और Cloudflare में अलग है। |
| रन बहुत देर लेता है | रन लॉग में चरणों की पंक्तियाँ पढ़ें; पहला रन मॉडल डाउनलोड करता है; चरण अटके तो रद्द करके दोबारा चलाएँ। |

## लाइसेंस और श्रेय

अपनी पसंद की `LICENSE` फ़ाइल जोड़ें। तृतीय-पक्ष घटकों के अपने लाइसेंस हैं:

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
