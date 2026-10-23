# Dabir (دبیر)

> Spraak naar tekst met vertaling: Perzisch en Engels erin, 20 talen eruit.

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · **Nederlands** · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir zet opnames om in tekst. Upload audio (mp3, m4a, wav… tot 1 GB); Dabir herkent of het Perzisch of Engels is, transcribeert het en kan het naar 20 andere talen vertalen. Het draait op opensourcemodellen in je eigen GitHub-repository, zonder AI-API-sleutels.

## Functies

- Hervatbare upload in delen tot 1 GB, met optionele compressie in de browser voor trage netwerken
- Automatische herkenning Perzisch/Engels en drie kwaliteitsniveaus
- Offline vertaling naar 20 talen (Argos Translate)
- Optionele ruisonderdrukking en sprekerlabels
- Versleutelde resultaten die alleen de uploadende browser kan lezen
- Privébibliotheek van twee uur, kopiëren en TXT/SRT-export, Perzische en Engelse interface

## Hoe het werkt

De site (GitHub Pages) praat met een kleine Cloudflare Worker die de geheimen bewaart. De Worker slaat de audio op in een privé concept-Release en start een GitHub Actions-job die transcribeert, vertaalt, versleutelt en het resultaat publiceert.

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

## Projectstructuur

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

## Implementatie vanaf nul

1. Maak een **openbare** repository (bijv. `dabir`) met een README.

2. Upload alle projectbestanden met mappen naar de root van de repository. De verborgen map `.github` maak je met **Add file → Create new file**.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. Genereer een willekeurig geheim (commando hieronder) en sla het op als Actions-secret `JOB_SECRET`.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. Maak een Fine-grained token alleen voor deze repository: Contents en Actions, beide Read and write.

7. Maak in Cloudflare een Worker (Hello World), plak `worker/src/index.js`, voeg de variabelen en secrets uit de tabel toe en klik op Deploy.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Zet de Worker-URL in `config.js`, commit en ververs de site met Ctrl+Shift+R.

9. Upload een kort testbestand. De eerste run is traag omdat modellen worden gedownload en gecachet.

## Configuratie

Namen zijn hoofdlettergevoelig. `GH_TOKEN` en `JOB_SECRET` moeten van het type Secret zijn; gebruik dezelfde `JOB_SECRET` in GitHub en Cloudflare.

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

## Ontwikkeling en tests

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## Privacy en beveiliging

- De audio staat alleen in een privé concept-Release en wordt na verwerking verwijderd.
- Resultaten zijn met AES-GCM versleuteld; de sleutel verlaat de browser van de uploader nooit.
- Het GitHub-token staat alleen in Cloudflare en wordt nooit naar bezoekers gestuurd.
- Kopieën op de server verlopen na ongeveer twee uur. Gebruik voor gevoelige inhoud een privérepository.

## Beperkingen

- Whisper is zwakker in Perzisch dan in Engels: kies de taal en de beste kwaliteit en controleer de tekst.
- GitHub Actions beperkt een job tot ongeveer 6 uur; zeer lange audio in de traagste kwaliteit kan onafgemaakt blijven.
- Sprekerlabels zijn alleen tekst; elke stem in een eigen audiobestand scheiden is niet geïmplementeerd.
- Alleen de uploadvoortgang is echt; verwerking toont in wachtrij, bezig en opslaan.
- De gratis abonnementen van GitHub en Cloudflare hebben gebruikslimieten.
- Vertaling, ruisonderdrukking, sprekerlabels en bestanden van 1 GB zijn geïmplementeerd, maar beperkt getest in de praktijk.

## Problemen oplossen

| ⚠️ | 🔧 |
|---|---|
| Melding “server niet geconfigureerd” | `config.js` is leeg of gecachet: vul de Worker-URL in en ververs volledig (of `config.js?v=2`). |
| `Failed to fetch` bij uploaden | `ALLOWED_ORIGIN` moet exact `https://<user>.github.io` zijn (zonder slash aan het eind); deploy opnieuw. |
| 502 “job aanmaken mislukt” | `GH_TOKEN` is onjuist, verlopen of mist rechten; vernieuw het. |
| Job blijft in de wachtrij | Open het tabblad Actions; controleer workflow-rechten en of `process.yml` bestaat. |
| Resultaat “onvolledige configuratie” | `JOB_SECRET` ontbreekt of verschilt tussen GitHub en Cloudflare. |
| Run duurt erg lang | Lees de fase-regels in het runlog; de eerste run downloadt modellen; annuleer en probeer opnieuw als een fase vastloopt. |

## Licentie en credits

Voeg je eigen `LICENSE`-bestand toe. Componenten van derden behouden hun licenties:

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
