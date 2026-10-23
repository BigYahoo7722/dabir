# Dabir (دبیر)

> Mowa na tekst z tłumaczeniem: perski i angielski na wejściu, 20 języków na wyjściu.

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · **Polski** · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir zamienia nagrania na tekst. Prześlij plik audio (mp3, m4a, wav… do 1 GB); Dabir rozpozna, czy jest po persku, czy po angielsku, dokona transkrypcji i może przetłumaczyć na 20 innych języków. Działa na modelach open source w Twoim własnym repozytorium GitHub, bez kluczy API sztucznej inteligencji.

## Funkcje

- Wznawialne przesyłanie we fragmentach do 1 GB, z opcjonalną kompresją w przeglądarce dla wolnych sieci
- Automatyczne wykrywanie perskiego/angielskiego i trzy poziomy jakości
- Tłumaczenie offline na 20 języków (Argos Translate)
- Opcjonalne usuwanie szumu i etykiety mówców
- Zaszyfrowane wyniki, które odczyta tylko przeglądarka, która przesłała plik
- Prywatna biblioteka na dwie godziny, kopiowanie i eksport TXT/SRT, interfejs po persku i angielsku

## Jak to działa

Strona (GitHub Pages) łączy się z małym Cloudflare Workerem przechowującym sekrety. Worker zapisuje audio w prywatnym roboczym Release i uruchamia zadanie GitHub Actions, które transkrybuje, tłumaczy, szyfruje i publikuje wynik.

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

## Struktura projektu

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

## Wdrożenie od zera

1. Utwórz **publiczne** repozytorium (np. `dabir`) z plikiem README.

2. Prześlij wszystkie pliki projektu z folderami do katalogu głównego repozytorium. Ukryty folder `.github` utworzysz przez **Add file → Create new file**.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. Wygeneruj losowy sekret (polecenie poniżej) i zapisz go jako sekret Actions `JOB_SECRET`.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. Utwórz token Fine-grained tylko dla tego repozytorium: Contents i Actions, oba Read and write.

7. W Cloudflare utwórz Worker (Hello World), wklej `worker/src/index.js`, dodaj zmienne i sekrety z tabeli i kliknij Deploy.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Wpisz adres Workera w `config.js`, zrób Commit i odśwież stronę przez Ctrl+Shift+R.

9. Prześlij krótki plik testowy. Pierwsze uruchomienie jest wolne, bo modele są pobierane i buforowane.

## Konfiguracja

Nazwy rozróżniają wielkość liter. `GH_TOKEN` i `JOB_SECRET` muszą być typu Secret; użyj tego samego `JOB_SECRET` w GitHub i Cloudflare.

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

## Rozwój i testy

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## Prywatność i bezpieczeństwo

- Audio znajduje się tylko w prywatnym roboczym Release i jest usuwane po przetworzeniu.
- Wyniki są szyfrowane AES-GCM; klucz nigdy nie opuszcza przeglądarki przesyłającego.
- Token GitHub jest tylko w Cloudflare i nigdy nie trafia do odwiedzających.
- Kopie na serwerze wygasają po około dwóch godzinach. Dla wrażliwych treści użyj prywatnego repozytorium.

## Ograniczenia

- Whisper jest mniej dokładny dla perskiego niż dla angielskiego: wybierz język i najwyższą jakość, a potem sprawdź tekst.
- GitHub Actions ogranicza zadanie do około 6 godzin; bardzo długie audio w najwolniejszej jakości może się nie zakończyć.
- Etykiety mówców są tylko tekstowe; rozdzielanie każdego głosu do osobnego pliku audio nie jest zaimplementowane.
- Prawdziwy jest tylko postęp przesyłania; przetwarzanie pokazuje: w kolejce, w toku, zapisywanie.
- Darmowe plany GitHub i Cloudflare mają limity użycia.
- Tłumaczenie, usuwanie szumu, etykiety mówców i pliki 1 GB są zaimplementowane, ale testowane w praktyce w ograniczonym stopniu.

## Rozwiązywanie problemów

| ⚠️ | 🔧 |
|---|---|
| Komunikat „serwer nieskonfigurowany” | `config.js` jest pusty lub w pamięci podręcznej: wpisz adres Workera i odśwież całkowicie (lub `config.js?v=2`). |
| `Failed to fetch` podczas przesyłania | `ALLOWED_ORIGIN` musi być dokładnie `https://<user>.github.io` (bez ukośnika na końcu); wdróż ponownie. |
| 502 „nie udało się utworzyć zadania” | `GH_TOKEN` jest błędny, wygasł lub nie ma uprawnień; wymień go. |
| Zadanie tkwi w kolejce | Otwórz kartę Actions; sprawdź uprawnienia workflow i obecność `process.yml`. |
| Wynik „niepełna konfiguracja” | Brak `JOB_SECRET` lub różni się w GitHub i Cloudflare. |
| Uruchomienie trwa bardzo długo | Przeczytaj wiersze etapów w logu; pierwsze uruchomienie pobiera modele; jeśli etap się zawiesi, anuluj i spróbuj ponownie. |

## Licencja i podziękowania

Dodaj własny plik `LICENSE`. Komponenty stron trzecich zachowują swoje licencje:

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
