# Dabir (دبیر)

> Sprache zu Text mit Übersetzung: Persisch und Englisch rein, 20 Sprachen raus.

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · **Deutsch** · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir wandelt Aufnahmen in Text um. Laden Sie eine Audiodatei hoch (mp3, m4a, wav … bis 1 GB); Dabir erkennt Persisch oder Englisch, transkribiert und kann in 20 weitere Sprachen übersetzen. Es läuft mit Open-Source-Modellen in Ihrem eigenen GitHub-Repository, ohne KI-API-Schlüssel.

## Funktionen

- Fortsetzbarer Chunk-Upload bis 1 GB, optional mit Kompression im Browser für langsame Netze
- Automatische Erkennung Persisch/Englisch und drei Qualitätsstufen
- Offline-Übersetzung in 20 Sprachen (Argos Translate)
- Optionale Rauschunterdrückung und Sprecherlabels
- Verschlüsselte Ergebnisse, die nur der hochladende Browser lesen kann
- Private Bibliothek für zwei Stunden, Kopieren sowie TXT/SRT-Export, Oberfläche auf Persisch und Englisch

## Funktionsweise

Die Website (GitHub Pages) spricht mit einem kleinen Cloudflare Worker, der die Geheimnisse hält. Der Worker legt das Audio in einem privaten Entwurfs-Release ab und startet einen GitHub-Actions-Job, der transkribiert, übersetzt, verschlüsselt und das Ergebnis veröffentlicht.

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

## Projektstruktur

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

## Einrichtung von Grund auf

1. Erstellen Sie ein **öffentliches** Repository (z. B. `dabir`) mit README.

2. Laden Sie alle Projektdateien mit den Ordnern ins Stammverzeichnis hoch. Den versteckten Ordner `.github` legen Sie über **Add file → Create new file** an.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. Erzeugen Sie ein zufälliges Geheimnis (Befehl unten) und speichern Sie es als Actions-Secret `JOB_SECRET`.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. Erstellen Sie ein Fine-grained-Token nur für dieses Repository: Contents und Actions, beide Read and write.

7. Erstellen Sie in Cloudflare einen Worker (Hello World), fügen Sie `worker/src/index.js` ein, ergänzen Sie Variablen und Secrets aus der Tabelle und klicken Sie auf Deploy.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Tragen Sie die Worker-URL in `config.js` ein, committen Sie und laden Sie die Seite mit Strg+Umschalt+R neu.

9. Laden Sie eine kurze Testdatei hoch. Der erste Lauf ist langsam, da Modelle geladen und zwischengespeichert werden.

## Konfiguration

Namen unterscheiden Groß-/Kleinschreibung. `GH_TOKEN` und `JOB_SECRET` müssen vom Typ Secret sein; `JOB_SECRET` ist in GitHub und Cloudflare identisch.

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

## Entwicklung und Tests

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## Datenschutz und Sicherheit

- Das Audio liegt nur in einem privaten Entwurfs-Release und wird nach der Verarbeitung gelöscht.
- Ergebnisse sind mit AES-GCM verschlüsselt; der Schlüssel verlässt den Browser des Hochladenden nie.
- Das GitHub-Token liegt nur in Cloudflare und wird nie an Besucher gesendet.
- Serverkopien verfallen nach etwa zwei Stunden. Für sensible Inhalte ein privates Repository nutzen.

## Einschränkungen

- Whisper ist bei Persisch schwächer als bei Englisch: Sprache und höchste Qualität wählen, Text prüfen.
- GitHub Actions begrenzt Jobs auf etwa 6 Stunden; sehr langes Audio in langsamster Qualität wird evtl. nicht fertig.
- Sprecherlabels sind nur Text; das Trennen jeder Stimme in eigene Audiodateien ist nicht umgesetzt.
- Nur der Upload-Fortschritt ist echt; die Verarbeitung zeigt wartend, läuft und speichert.
- Die kostenlosen Tarife von GitHub und Cloudflare haben Nutzungsgrenzen.
- Übersetzung, Rauschunterdrückung, Sprecherlabels und 1-GB-Dateien sind umgesetzt, aber nur begrenzt in der Praxis getestet.

## Fehlerbehebung

| ⚠️ | 🔧 |
|---|---|
| Meldung „Server nicht konfiguriert“ | `config.js` ist leer oder im Cache: Worker-URL eintragen und Seite hart neu laden (oder `config.js?v=2`). |
| `Failed to fetch` beim Hochladen | `ALLOWED_ORIGIN` muss genau `https://<user>.github.io` sein (ohne Schrägstrich am Ende); erneut deployen. |
| 502 „Job konnte nicht erstellt werden“ | `GH_TOKEN` ist falsch, abgelaufen oder ohne Rechte; erneuern. |
| Job bleibt in der Warteschlange | Actions-Tab öffnen; Workflow-Berechtigungen und `process.yml` prüfen. |
| Ergebnis „unvollständige Konfiguration“ | `JOB_SECRET` fehlt oder unterscheidet sich zwischen GitHub und Cloudflare. |
| Lauf dauert sehr lange | Stufenzeilen im Run-Log lesen; der erste Lauf lädt Modelle; bei hängender Stufe abbrechen und neu starten. |

## Lizenz und Danksagung

Fügen Sie eine eigene `LICENSE`-Datei hinzu. Drittkomponenten behalten ihre Lizenzen:

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
