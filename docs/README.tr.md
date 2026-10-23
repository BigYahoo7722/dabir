# Dabir (دبیر)

> Çeviri destekli konuşmadan metne: Farsça ve İngilizce girdi, 20 dilde çıktı.

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · **Türkçe** · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir ses kayıtlarını metne dönüştürür. Bir ses dosyası (mp3, m4a, wav… 1 GB'a kadar) yükleyin; Farsça mı İngilizce mi olduğunu algılar, metne döker ve isterseniz 20 başka dile çevirir. Açık kaynak modellerle kendi GitHub deponuzda çalışır, yapay zekâ API anahtarı gerekmez.

## Özellikler

- 1 GB'a kadar devam ettirilebilir parçalı yükleme; yavaş ağlar için tarayıcıda isteğe bağlı sıkıştırma
- Otomatik Farsça/İngilizce algılama ve üç kalite düzeyi
- 20 dile çevrimdışı çeviri (Argos Translate)
- İsteğe bağlı gürültü giderme ve konuşmacı etiketleri
- Yalnızca yükleyen tarayıcının okuyabildiği şifreli sonuçlar
- İki saatlik özel kitaplık, kopyalama ve TXT/SRT dışa aktarma, Farsça ve İngilizce arayüz

## Nasıl çalışır

Site (GitHub Pages), sırları tutan küçük bir Cloudflare Worker ile konuşur. Worker sesi özel bir taslak Release'te saklar ve metne dökme, çeviri, şifreleme ve sonucu yayımlama işini yapan bir GitHub Actions işi başlatır.

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

## Proje yapısı

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

## Sıfırdan kurulum

1. Bir README ile **herkese açık** bir depo oluşturun (ör. `dabir`).

2. Tüm proje dosyalarını klasörleri koruyarak deponun köküne yükleyin. Gizli `.github` klasörünü **Add file → Create new file** ile oluşturun.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. Rastgele bir sır üretin (aşağıdaki komut) ve `JOB_SECRET` adlı Actions sırrı olarak kaydedin.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. Yalnızca bu depo için Fine-grained bir token oluşturun: Contents ve Actions, ikisi de Read and write.

7. Cloudflare'de bir Worker (Hello World) oluşturun, `worker/src/index.js` kodunu yapıştırın, tablodaki değişken ve sırları ekleyip Deploy edin.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Worker adresini `config.js` içine yazın, Commit edin ve siteyi Ctrl+Shift+R ile yenileyin.

9. Kısa bir deneme dosyası yükleyin. Modeller indirilip önbelleğe alındığı için ilk çalışma yavaştır.

## Yapılandırma

Adlar büyük/küçük harfe duyarlıdır. `GH_TOKEN` ve `JOB_SECRET` Secret türünde olmalı; `JOB_SECRET` GitHub ve Cloudflare'de aynı olmalı.

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

## Geliştirme ve testler

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## Gizlilik ve güvenlik

- Ses yalnızca özel bir taslak Release'te kalır ve işlendikten sonra silinir.
- Sonuçlar AES-GCM ile şifrelenir; anahtar yükleyen tarayıcıdan asla çıkmaz.
- GitHub token'ı yalnızca Cloudflare'dedir, ziyaretçilere asla gönderilmez.
- Sunucudaki kopyalar yaklaşık iki saat sonra silinir. Hassas içerik için özel depo kullanın.

## Sınırlamalar

- Whisper Farsçada İngilizceden daha zayıftır: dili ve en yüksek kaliteyi seçin, metni gözden geçirin.
- GitHub Actions bir işi yaklaşık 6 saatle sınırlar; en yavaş kalitede çok uzun ses bitmeyebilir.
- Konuşmacı etiketleri yalnızca metindir; her sesi ayrı ses dosyasına ayırma uygulanmadı.
- Yalnızca yükleme ilerlemesi gerçektir; işleme sırada, çalışıyor ve kaydediliyor durumlarını gösterir.
- GitHub ve Cloudflare ücretsiz planlarının kullanım sınırları vardır.
- Çeviri, gürültü giderme, konuşmacı etiketleri ve 1 GB dosyalar uygulandı ancak gerçek ortamda sınırlı test edildi.

## Sorun giderme

| ⚠️ | 🔧 |
|---|---|
| “Sunucu yapılandırılmadı” mesajı | `config.js` boş veya önbellekte: Worker adresini yazın ve sayfayı tamamen yenileyin (veya `config.js?v=2`). |
| Yüklerken `Failed to fetch` | `ALLOWED_ORIGIN` tam olarak `https://<user>.github.io` olmalı (sonda eğik çizgi yok); yeniden Deploy edin. |
| 502 “iş oluşturulamadı” | `GH_TOKEN` yanlış, süresi dolmuş veya izinsiz; yenileyin. |
| İş sırada kalıyor | Actions sekmesine bakın; workflow izinlerini ve `process.yml` dosyasını kontrol edin. |
| “Eksik yapılandırma” sonucu | `JOB_SECRET` yok ya da GitHub ile Cloudflare'de farklı. |
| Çalışma çok uzun sürüyor | Çalışma günlüğündeki aşama satırlarını okuyun; ilk çalışma modelleri indirir; bir aşama takılırsa iptal edip yeniden deneyin. |

## Lisans ve kaynaklar

Kendi `LICENSE` dosyanızı ekleyin. Üçüncü taraf bileşenlerin kendi lisansları vardır:

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
