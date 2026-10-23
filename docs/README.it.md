# Dabir (دبیر)

> Da voce a testo con traduzione: persiano e inglese in ingresso, 20 lingue in uscita.

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · **Italiano** · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir trasforma le registrazioni in testo. Carica un audio (mp3, m4a, wav… fino a 1 GB); rileva se è persiano o inglese, lo trascrive e può tradurlo in altre 20 lingue. Funziona con modelli open source nel tuo repository GitHub, senza chiavi API di IA.

## Funzionalità

- Caricamento a blocchi riprendibile fino a 1 GB, con compressione facoltativa nel browser per reti lente
- Rilevamento automatico persiano/inglese e tre livelli di qualità
- Traduzione offline in 20 lingue (Argos Translate)
- Riduzione del rumore ed etichette dei parlanti (facoltativi)
- Risultati cifrati leggibili solo dal browser che ha caricato il file
- Libreria privata di due ore, copia ed esportazione TXT/SRT, interfaccia in persiano e inglese

## Come funziona

Il sito (GitHub Pages) comunica con un piccolo Worker Cloudflare che custodisce i segreti. Il Worker salva l'audio in una Release bozza privata e avvia un job GitHub Actions che trascrive, traduce, cifra e pubblica il risultato.

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

## Struttura del progetto

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

## Distribuzione da zero

1. Crea un repository **pubblico** (ad esempio `dabir`) con un README.

2. Carica tutti i file del progetto nella radice del repository mantenendo le cartelle. La cartella nascosta `.github` si crea con **Add file → Create new file**.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. Genera un segreto casuale (comando sotto) e salvalo come segreto Actions `JOB_SECRET`.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. Crea un token Fine-grained solo per questo repository: Contents e Actions, entrambi in Read and write.

7. In Cloudflare crea un Worker (Hello World), incolla `worker/src/index.js`, aggiungi variabili e segreti della tabella e premi Deploy.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Inserisci l'URL del Worker in `config.js`, fai Commit e ricarica il sito con Ctrl+Shift+R.

9. Carica un breve file di prova. La prima esecuzione è lenta perché i modelli vengono scaricati e messi in cache.

## Configurazione

I nomi distinguono maiuscole e minuscole. `GH_TOKEN` e `JOB_SECRET` devono essere di tipo Secret; usa lo stesso `JOB_SECRET` in GitHub e Cloudflare.

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

## Sviluppo e test

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## Privacy e sicurezza

- L'audio resta solo in una Release bozza privata e viene eliminato dopo l'elaborazione.
- I risultati sono cifrati con AES-GCM; la chiave non lascia mai il browser di chi carica.
- Il token GitHub è solo in Cloudflare e non viene mai inviato ai visitatori.
- Le copie sul server scadono dopo circa due ore. Per contenuti sensibili usa un repository privato.

## Limitazioni

- Whisper è meno preciso in persiano che in inglese: scegli la lingua e la qualità migliore, poi rileggi il testo.
- GitHub Actions limita un job a circa 6 ore; un audio molto lungo alla qualità più lenta potrebbe non finire.
- Le etichette dei parlanti sono solo testo; separare ogni voce in un file audio a parte non è implementato.
- Solo l'avanzamento del caricamento è reale; l'elaborazione mostra in coda, in esecuzione e salvataggio.
- I piani gratuiti di GitHub e Cloudflare hanno limiti d'uso.
- Traduzione, riduzione del rumore, etichette dei parlanti e file da 1 GB sono implementati ma testati poco in condizioni reali.

## Risoluzione dei problemi

| ⚠️ | 🔧 |
|---|---|
| Messaggio «server non configurato» | `config.js` è vuoto o in cache: imposta l'URL del Worker e ricarica completamente (o `config.js?v=2`). |
| `Failed to fetch` durante il caricamento | `ALLOWED_ORIGIN` deve essere esattamente `https://<user>.github.io` (senza barra finale); ripeti il Deploy. |
| 502 «creazione del job non riuscita» | `GH_TOKEN` è errato, scaduto o senza permessi; rinnovalo. |
| Il job resta in coda | Apri la scheda Actions; controlla i permessi dei workflow e che `process.yml` esista. |
| Risultato «configurazione incompleta» | `JOB_SECRET` manca o differisce tra GitHub e Cloudflare. |
| L'esecuzione dura molto | Leggi le righe di fase nel log; la prima esecuzione scarica i modelli; annulla e riprova se una fase si blocca. |

## Licenza e crediti

Aggiungi un tuo file `LICENSE`. I componenti di terze parti mantengono le proprie licenze:

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
