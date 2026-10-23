# Dabir (دبیر)

> Μετατροπή ομιλίας σε κείμενο με μετάφραση: είσοδος περσικά και αγγλικά, έξοδος σε 20 γλώσσες.

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · **Ελληνικά**

Το Dabir μετατρέπει ηχογραφήσεις σε κείμενο. Ανεβάστε ήχο (mp3, m4a, wav… έως 1 GB)· εντοπίζει αν είναι περσικά ή αγγλικά, τον απομαγνητοφωνεί και μπορεί να τον μεταφράσει σε 20 άλλες γλώσσες. Τρέχει με μοντέλα ανοιχτού κώδικα στο δικό σας αποθετήριο GitHub, χωρίς κλειδιά API τεχνητής νοημοσύνης.

## Χαρακτηριστικά

- Ανέβασμα σε τμήματα με δυνατότητα συνέχισης έως 1 GB και προαιρετική συμπίεση στο πρόγραμμα περιήγησης για αργά δίκτυα
- Αυτόματος εντοπισμός περσικών/αγγλικών και τρία επίπεδα ποιότητας
- Μετάφραση χωρίς σύνδεση σε 20 γλώσσες (Argos Translate)
- Προαιρετική μείωση θορύβου και ετικέτες ομιλητών
- Κρυπτογραφημένα αποτελέσματα που διαβάζει μόνο το πρόγραμμα περιήγησης που ανέβασε το αρχείο
- Ιδιωτική βιβλιοθήκη δύο ωρών, αντιγραφή και εξαγωγή TXT/SRT, διεπαφή σε περσικά και αγγλικά

## Πώς λειτουργεί

Ο ιστότοπος (GitHub Pages) επικοινωνεί με ένα μικρό Cloudflare Worker που κρατά τα μυστικά. Το Worker αποθηκεύει τον ήχο σε ιδιωτικό πρόχειρο Release και ξεκινά μια εργασία GitHub Actions που απομαγνητοφωνεί, μεταφράζει, κρυπτογραφεί και δημοσιεύει το αποτέλεσμα.

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

## Δομή του έργου

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

## Ανάπτυξη από το μηδέν

1. Δημιουργήστε ένα **δημόσιο** αποθετήριο (π.χ. `dabir`) με README.

2. Ανεβάστε όλα τα αρχεία του έργου με τους φακέλους στη ρίζα του αποθετηρίου. Ο κρυφός φάκελος `.github` δημιουργείται με **Add file → Create new file**.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. Δημιουργήστε ένα τυχαίο μυστικό (εντολή παρακάτω) και αποθηκεύστε το ως μυστικό Actions `JOB_SECRET`.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. Δημιουργήστε token Fine-grained μόνο για αυτό το αποθετήριο: Contents και Actions, και τα δύο Read and write.

7. Στο Cloudflare δημιουργήστε Worker (Hello World), επικολλήστε το `worker/src/index.js`, προσθέστε τις μεταβλητές και τα μυστικά του πίνακα και πατήστε Deploy.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Βάλτε τη διεύθυνση του Worker στο `config.js`, κάντε Commit και ανανεώστε τον ιστότοπο με Ctrl+Shift+R.

9. Ανεβάστε ένα σύντομο δοκιμαστικό αρχείο. Η πρώτη εκτέλεση είναι αργή, γιατί τα μοντέλα κατεβαίνουν και αποθηκεύονται στη μνήμη cache.

## Ρυθμίσεις

Τα ονόματα κάνουν διάκριση πεζών-κεφαλαίων. Τα `GH_TOKEN` και `JOB_SECRET` πρέπει να είναι τύπου Secret· το `JOB_SECRET` να είναι ίδιο σε GitHub και Cloudflare.

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

## Ανάπτυξη και δοκιμές

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## Απόρρητο και ασφάλεια

- Ο ήχος μένει μόνο σε ιδιωτικό πρόχειρο Release και διαγράφεται μετά την επεξεργασία.
- Τα αποτελέσματα κρυπτογραφούνται με AES-GCM· το κλειδί δεν φεύγει ποτέ από το πρόγραμμα περιήγησης του χρήστη που ανέβασε το αρχείο.
- Το token του GitHub υπάρχει μόνο στο Cloudflare και δεν στέλνεται ποτέ στους επισκέπτες.
- Τα αντίγραφα στον διακομιστή λήγουν μετά από περίπου δύο ώρες. Για ευαίσθητο περιεχόμενο χρησιμοποιήστε ιδιωτικό αποθετήριο.

## Περιορισμοί

- Το Whisper είναι λιγότερο ακριβές στα περσικά απ' ό,τι στα αγγλικά: επιλέξτε γλώσσα και την καλύτερη ποιότητα και ελέγξτε το κείμενο.
- Το GitHub Actions περιορίζει μια εργασία σε περίπου 6 ώρες· πολύ μεγάλος ήχος στην πιο αργή ποιότητα μπορεί να μην ολοκληρωθεί.
- Οι ετικέτες ομιλητών είναι μόνο κείμενο· ο διαχωρισμός κάθε φωνής σε ξεχωριστό αρχείο ήχου δεν έχει υλοποιηθεί.
- Μόνο η πρόοδος του ανεβάσματος είναι πραγματική· η επεξεργασία δείχνει σε αναμονή, εκτελείται και αποθήκευση.
- Τα δωρεάν πακέτα του GitHub και του Cloudflare έχουν όρια χρήσης.
- Η μετάφραση, η μείωση θορύβου, οι ετικέτες ομιλητών και τα αρχεία 1 GB έχουν υλοποιηθεί, αλλά έχουν δοκιμαστεί περιορισμένα σε πραγματικές συνθήκες.

## Αντιμετώπιση προβλημάτων

| ⚠️ | 🔧 |
|---|---|
| Μήνυμα «ο διακομιστής δεν έχει ρυθμιστεί» | Το `config.js` είναι κενό ή στη μνήμη cache: βάλτε τη διεύθυνση του Worker και κάντε πλήρη ανανέωση (ή `config.js?v=2`). |
| `Failed to fetch` κατά το ανέβασμα | Το `ALLOWED_ORIGIN` πρέπει να είναι ακριβώς `https://<user>.github.io` (χωρίς κάθετο στο τέλος)· κάντε ξανά Deploy. |
| 502 «αποτυχία δημιουργίας εργασίας» | Το `GH_TOKEN` είναι λάθος, έχει λήξει ή δεν έχει δικαιώματα· αντικαταστήστε το. |
| Η εργασία μένει στην ουρά | Ανοίξτε την καρτέλα Actions· ελέγξτε τα δικαιώματα workflow και την ύπαρξη του `process.yml`. |
| Αποτέλεσμα «ελλιπής ρύθμιση» | Λείπει το `JOB_SECRET` ή διαφέρει μεταξύ GitHub και Cloudflare. |
| Η εκτέλεση διαρκεί πολύ | Διαβάστε τις γραμμές σταδίων στο αρχείο καταγραφής· η πρώτη εκτέλεση κατεβάζει μοντέλα· αν κάποιο στάδιο κολλήσει, ακυρώστε και ξαναδοκιμάστε. |

## Άδεια και ευχαριστίες

Προσθέστε δικό σας αρχείο `LICENSE`. Τα στοιχεία τρίτων διατηρούν τις άδειές τους:

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
