# Dabir (دبیر)

> Parole vers texte avec traduction : persan et anglais en entrée, 20 langues en sortie.

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · **Français** · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir transforme des enregistrements en texte. Envoyez un fichier audio (mp3, m4a, wav… jusqu'à 1 Go) ; il détecte s'il est en persan ou en anglais, le transcrit et peut le traduire dans 20 autres langues. Il fonctionne avec des modèles open source dans votre propre dépôt GitHub, sans clé d'API d'IA.

## Fonctionnalités

- Envoi fractionné et reprenable jusqu'à 1 Go, avec compression facultative dans le navigateur pour les connexions lentes
- Détection automatique persan/anglais et trois niveaux de qualité
- Traduction hors ligne vers 20 langues (Argos Translate)
- Réduction de bruit et étiquettes de locuteurs (facultatif)
- Résultats chiffrés, lisibles uniquement par le navigateur qui a envoyé le fichier
- Bibliothèque privée de deux heures, copie et export TXT/SRT, interface persan et anglais

## Fonctionnement

Le site (GitHub Pages) appelle un petit Worker Cloudflare qui détient les secrets. Le Worker stocke l'audio dans une Release brouillon privée et lance une tâche GitHub Actions qui transcrit, traduit, chiffre et publie le résultat.

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

## Structure du projet

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

## Déploiement depuis zéro

1. Créez un dépôt **public** (par exemple `dabir`) avec un README.

2. Envoyez tous les fichiers du projet à la racine du dépôt en gardant les dossiers. Le dossier caché `.github` se crée via **Add file → Create new file**.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. Générez un secret aléatoire (commande ci-dessous) et enregistrez-le comme secret Actions `JOB_SECRET`.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. Créez un jeton Fine-grained pour ce dépôt uniquement : Contents et Actions, tous deux en Read and write.

7. Dans Cloudflare, créez un Worker (Hello World), collez `worker/src/index.js`, ajoutez les variables et secrets du tableau, puis Deploy.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Mettez l'URL du Worker dans `config.js`, faites un Commit, puis rechargez le site avec Ctrl+Shift+R.

9. Envoyez un court fichier de test. Le premier lancement est lent : les modèles sont téléchargés et mis en cache.

## Configuration

Les noms sont sensibles à la casse. `GH_TOKEN` et `JOB_SECRET` doivent être de type Secret ; utilisez le même `JOB_SECRET` dans GitHub et Cloudflare.

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

## Développement et tests

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## Confidentialité et sécurité

- L'audio reste uniquement dans une Release brouillon privée et est supprimé après traitement.
- Les résultats sont chiffrés en AES-GCM ; la clé ne quitte jamais le navigateur de l'expéditeur.
- Le jeton GitHub reste dans Cloudflare et n'est jamais envoyé aux visiteurs.
- Les copies serveur expirent après environ deux heures. Pour un contenu sensible, utilisez un dépôt privé.

## Limites

- Whisper est moins précis en persan qu'en anglais : choisissez la langue et la meilleure qualité, puis relisez.
- GitHub Actions limite une tâche à environ 6 heures ; un audio très long en qualité maximale peut ne pas finir.
- Les étiquettes de locuteurs sont textuelles ; séparer chaque voix dans un fichier audio n'est pas implémenté.
- Seule la progression de l'envoi est réelle ; le traitement affiche en attente, en cours et enregistrement.
- Les offres gratuites de GitHub et Cloudflare ont des limites d'usage.
- La traduction, la réduction de bruit, les étiquettes de locuteurs et les fichiers de 1 Go sont implémentés mais peu testés en conditions réelles.

## Dépannage

| ⚠️ | 🔧 |
|---|---|
| Message « serveur non configuré » | `config.js` est vide ou en cache : indiquez l'URL du Worker et rechargez complètement (ou `config.js?v=2`). |
| `Failed to fetch` pendant l'envoi | `ALLOWED_ORIGIN` doit être exactement `https://<user>.github.io` (sans barre finale) ; redéployez. |
| 502 « création de la tâche échouée » | `GH_TOKEN` est faux, expiré ou sans droits ; renouvelez-le. |
| La tâche reste en attente | Ouvrez l'onglet Actions ; vérifiez les permissions des workflows et la présence de `process.yml`. |
| Résultat « configuration incomplète » | `JOB_SECRET` est absent ou différent entre GitHub et Cloudflare. |
| L'exécution est très longue | Lisez les lignes d'étape du journal ; le premier lancement télécharge les modèles ; annulez et relancez si une étape bloque. |

## Licence et crédits

Ajoutez votre propre fichier `LICENSE`. Les composants tiers conservent leurs licences :

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
