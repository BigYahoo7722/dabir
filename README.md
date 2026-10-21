# Dabir (دبیر)

> Speech-to-text with translation: Persian and English in, 20 languages out.

**English** · [فارسی](docs/README.fa.md) · [العربية](docs/README.ar.md) · [Türkçe](docs/README.tr.md) · [Français](docs/README.fr.md) · [Deutsch](docs/README.de.md) · [Español](docs/README.es.md) · [Português](docs/README.pt.md) · [Italiano](docs/README.it.md) · [Русский](docs/README.ru.md) · [中文](docs/README.zh.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [हिन्दी](docs/README.hi.md) · [اردو](docs/README.ur.md) · [বাংলা](docs/README.bn.md) · [Indonesia](docs/README.id.md) · [Nederlands](docs/README.nl.md) · [Polski](docs/README.pl.md) · [Українська](docs/README.uk.md) · [Ελληνικά](docs/README.el.md)

**Contents:** [Features](#features) · [How it works](#how-it-works) · [Project structure](#project-structure) · [Deploy from scratch](#deploy-from-scratch) · [Configuration](#configuration) · [Development and tests](#development-and-tests) · [Privacy and security](#privacy-and-security) · [Limitations](#limitations) · [Troubleshooting](#troubleshooting) · [License and credits](#license-and-credits)

Dabir turns recordings into text. Upload audio (mp3, m4a, wav… up to 1 GB); it detects Persian or English, transcribes it, and can translate it into 20 other languages. It runs on open-source models inside your own GitHub repository, with no AI API keys.

## Features

- Resumable chunked uploads up to 1 GB, plus optional in-browser compression for slow networks
- Automatic Persian/English detection and three quality levels
- Offline translation into 20 languages (Argos Translate)
- Optional noise reduction and speaker labels
- Encrypted results that only the uploading browser can read
- One-hour private library, copy / TXT / SRT export, Persian and English interface

## How it works

The site (GitHub Pages) calls a small Cloudflare Worker that holds the secrets. The Worker stores the audio in a private draft Release and starts a GitHub Actions job that transcribes, translates, encrypts and publishes the result.

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

## Project structure

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
│                           # ui.test.cjs, compress.test.cjs
├── docs/                   # this README in 21 languages
└── README.md
```

## Deploy from scratch

1. Create a **public** repository (for example `dabir`) with a README.

2. Upload all project files to the repository root, keeping the folders. The hidden `.github` folder must be created with **Add file → Create new file**.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. Generate a random secret (command below) and save it as the Actions secret `JOB_SECRET`.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. Create a fine-grained token for this repository only: Contents and Actions, both Read and write.

7. In Cloudflare create a Worker (Hello World), paste `worker/src/index.js`, add the variables and secrets from the table, then Deploy.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Put the Worker URL in `config.js`, commit, then hard-refresh the site (Ctrl+Shift+R).

9. Upload a short test file. The first run is slow because models are downloaded and cached.

## Configuration

Names are case-sensitive. `GH_TOKEN` and `JOB_SECRET` must be type Secret; use the same `JOB_SECRET` in GitHub and Cloudflare.

| Name | Type | Where | Value |
|---|---|---|---|
| `REPO` | text | Cloudflare | `<user>/dabir` |
| `BRANCH` | text | Cloudflare | `main` |
| `ALLOWED_ORIGIN` | text | Cloudflare | `https://<user>.github.io` |
| `MAX_BYTES` | text | Cloudflare | `1073741824` (1 GB) |
| `MAX_ACTIVE` | text | Cloudflare | `20` (parallel jobs) |
| `GH_TOKEN` | **secret** | Cloudflare | fine-grained token |
| `JOB_SECRET` | **secret** | Cloudflare **and** GitHub Actions | 64 hex characters |
| `RETAIN_SECONDS` | env | `cleanup.yml` | `3900` |
| `DABIR_API` | JS | `config.js` | Worker URL, no trailing slash |

## Development and tests

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## Privacy and security

- Audio stays only in a private draft Release and is deleted after processing.
- Results are AES-GCM encrypted; the key never leaves the uploader's browser.
- The GitHub token lives only in Cloudflare and is never sent to visitors.
- Server copies expire after about an hour. For sensitive content use a private repository.

## Limitations

- Whisper is weaker in Persian than in English: pick the language and best quality, then proofread.
- GitHub Actions caps a job at about 6 hours; very long audio at the slowest quality may not finish.
- Speaker labels are text only; splitting each voice into its own audio file is not implemented.
- Only upload progress is real; processing shows queued, running and saving.
- Free tiers of GitHub and Cloudflare have usage limits.
- Translation, noise reduction, speaker labels and 1 GB files are implemented but have had limited real-world testing.

## Troubleshooting

| ⚠️ | 🔧 |
|---|---|
| “Server not configured” message | `config.js` is empty or cached: set the Worker URL and hard-refresh (try `config.js?v=2`). |
| `Failed to fetch` during upload | `ALLOWED_ORIGIN` must be exactly `https://<user>.github.io` (no trailing slash); redeploy the Worker. |
| 502 “job creation failed” | `GH_TOKEN` is wrong, expired or lacks permissions; rotate it. |
| Job stays queued | Open the Actions tab; check workflow permissions and that `process.yml` exists. |
| “Incomplete configuration” result | `JOB_SECRET` is missing or differs between GitHub and Cloudflare. |
| Run takes very long | Read the stage lines in the run log; the first run downloads models; cancel and retry if a stage hangs. |

## License and credits

Add your own `LICENSE` file. Third-party components keep their licenses:

- [Whisper](https://github.com/openai/whisper) / [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — MIT
- [Argos Translate](https://github.com/argosopentech/argos-translate) — MIT (language models have their own licenses)
- [noisereduce](https://github.com/timsainb/noisereduce) — MIT
- [Resemblyzer](https://github.com/resemble-ai/Resemblyzer) — Apache-2.0
- [lamejs](https://github.com/zhuker/lamejs) — LGPL-3.0 (`lame.min.js`)
- [Vazirmatn](https://github.com/rastikerdar/vazirmatn) font — OFL-1.1
- FFmpeg — LGPL/GPL depending on the build

---
**made by Big_Yahoo8844**
