# Dabir (دبیر)

> Ucapan ke teks dengan terjemahan: masukan Persia dan Inggris, keluaran 20 bahasa.

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · **Indonesia** · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir mengubah rekaman menjadi teks. Unggah audio (mp3, m4a, wav… hingga 1 GB); Dabir mendeteksi apakah Persia atau Inggris, mentranskripsikannya, dan dapat menerjemahkannya ke 20 bahasa lain. Berjalan dengan model sumber terbuka di repositori GitHub Anda sendiri, tanpa kunci API AI.

## Fitur

- Unggah per bagian yang dapat dilanjutkan hingga 1 GB, dengan kompresi opsional di browser untuk jaringan lambat
- Deteksi otomatis Persia/Inggris dan tiga tingkat kualitas
- Terjemahan offline ke 20 bahasa (Argos Translate)
- Peredam derau dan label pembicara (opsional)
- Hasil terenkripsi yang hanya bisa dibaca browser pengunggah
- Pustaka pribadi dua jam, salin dan ekspor TXT/SRT, antarmuka Persia dan Inggris

## Cara kerja

Situs (GitHub Pages) memanggil Cloudflare Worker kecil yang menyimpan rahasia. Worker menyimpan audio di Release draf pribadi dan memulai tugas GitHub Actions yang mentranskripsi, menerjemahkan, mengenkripsi, dan menerbitkan hasil.

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

## Struktur proyek

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

## Deploy dari nol

1. Buat repositori **publik** (misalnya `dabir`) dengan README.

2. Unggah semua berkas proyek ke root repositori beserta foldernya. Folder tersembunyi `.github` dibuat lewat **Add file → Create new file**.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. Buat rahasia acak (perintah di bawah) dan simpan sebagai secret Actions `JOB_SECRET`.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. Buat token Fine-grained hanya untuk repositori ini: Contents dan Actions, keduanya Read and write.

7. Di Cloudflare buat Worker (Hello World), tempel `worker/src/index.js`, tambahkan variabel dan secret dari tabel, lalu Deploy.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Isi URL Worker di `config.js`, Commit, lalu muat ulang situs dengan Ctrl+Shift+R.

9. Unggah berkas uji pendek. Proses pertama lambat karena model diunduh dan disimpan di cache.

## Konfigurasi

Nama peka huruf besar-kecil. `GH_TOKEN` dan `JOB_SECRET` harus bertipe Secret; gunakan `JOB_SECRET` yang sama di GitHub dan Cloudflare.

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

## Pengembangan dan pengujian

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## Privasi dan keamanan

- Audio hanya berada di Release draf pribadi dan dihapus setelah diproses.
- Hasil dienkripsi dengan AES-GCM; kunci tidak pernah meninggalkan browser pengunggah.
- Token GitHub hanya ada di Cloudflare dan tidak pernah dikirim ke pengunjung.
- Salinan di server kedaluwarsa sekitar dua jam. Untuk konten sensitif gunakan repositori privat.

## Keterbatasan

- Whisper kurang akurat untuk bahasa Persia dibanding Inggris: pilih bahasa dan kualitas terbaik, lalu periksa teksnya.
- GitHub Actions membatasi satu job sekitar 6 jam; audio sangat panjang pada kualitas paling lambat mungkin tidak selesai.
- Label pembicara hanya berupa teks; memisahkan tiap suara ke berkas audio sendiri belum diimplementasikan.
- Hanya progres unggah yang nyata; pemrosesan menampilkan antre, berjalan, dan menyimpan.
- Paket gratis GitHub dan Cloudflare memiliki batas penggunaan.
- Terjemahan, peredam derau, label pembicara, dan berkas 1 GB sudah diimplementasikan, tetapi pengujian nyatanya terbatas.

## Pemecahan masalah

| ⚠️ | 🔧 |
|---|---|
| Pesan “server belum dikonfigurasi” | `config.js` kosong atau tersimpan di cache: isi URL Worker dan muat ulang penuh (atau `config.js?v=2`). |
| `Failed to fetch` saat mengunggah | `ALLOWED_ORIGIN` harus persis `https://<user>.github.io` (tanpa garis miring di akhir); Deploy ulang. |
| 502 “gagal membuat job” | `GH_TOKEN` salah, kedaluwarsa, atau tanpa izin; ganti. |
| Job tetap antre | Buka tab Actions; periksa izin workflow dan keberadaan `process.yml`. |
| Hasil “konfigurasi tidak lengkap” | `JOB_SECRET` hilang atau berbeda antara GitHub dan Cloudflare. |
| Proses sangat lama | Baca baris tahap di log; proses pertama mengunduh model; batalkan dan coba lagi jika suatu tahap macet. |

## Lisensi dan kredit

Tambahkan berkas `LICENSE` pilihan Anda. Komponen pihak ketiga mempertahankan lisensinya:

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
