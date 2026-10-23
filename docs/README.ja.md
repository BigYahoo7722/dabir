# Dabir (دبیر)

> 翻訳付きの音声文字起こし：ペルシア語・英語を入力し、20 言語で出力。

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · **日本語** · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir は録音をテキストに変換します。音声ファイル（mp3、m4a、wav など、最大 1 GB）をアップロードすると、ペルシア語か英語かを判定して文字起こしし、ほかの 20 言語への翻訳もできます。オープンソースのモデルをあなた自身の GitHub リポジトリで実行し、AI の API キーは不要です。

## 機能

- 最大 1 GB の再開可能な分割アップロードと、低速回線向けのブラウザ内圧縮（任意）
- ペルシア語/英語の自動判定と 3 段階の品質
- 20 言語へのオフライン翻訳（Argos Translate）
- ノイズ除去と話者ラベル（任意）
- アップロードしたブラウザだけが読める暗号化結果
- 2 時間の非公開ライブラリ、コピーと TXT/SRT 出力、ペルシア語・英語 UI

## 仕組み

サイト（GitHub Pages）は、シークレットを保持する小さな Cloudflare Worker を呼び出します。Worker は音声を非公開のドラフト Release に保存し、文字起こし・翻訳・暗号化・結果公開を行う GitHub Actions ジョブを起動します。

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

## プロジェクト構成

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

## ゼロからのデプロイ

1. README 付きの**公開**リポジトリ（例: `dabir`）を作成します。

2. プロジェクトの全ファイルをフォルダごとリポジトリ直下にアップロードします。隠しフォルダ `.github` は **Add file → Create new file** で作成します。

3. **Settings → Actions → General → Workflow permissions →** Read and write。

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`。

5. ランダムなシークレットを生成し（下のコマンド）、Actions シークレット `JOB_SECRET` として保存します。

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. このリポジトリ専用の Fine-grained トークンを作成します。Contents と Actions をどちらも Read and write にします。

7. Cloudflare で Worker（Hello World）を作成し、`worker/src/index.js` を貼り付け、表の変数とシークレットを追加して Deploy します。

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Worker の URL を `config.js` に書き、Commit して、Ctrl+Shift+R でサイトを再読み込みします。

9. 短いテストファイルをアップロードします。初回はモデルのダウンロードとキャッシュのため遅くなります。

## 設定

名前は大文字と小文字を区別します。`GH_TOKEN` と `JOB_SECRET` は Secret 型にし、`JOB_SECRET` は GitHub と Cloudflare で同じ値にします。

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

## 開発とテスト

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## プライバシーとセキュリティ

- 音声は非公開のドラフト Release にのみ保存され、処理後に削除されます。
- 結果は AES-GCM で暗号化され、鍵はアップロードしたブラウザから出ません。
- GitHub トークンは Cloudflare にのみ置かれ、訪問者には送られません。
- サーバー上のコピーは約 2 時間で期限切れになります。機密性の高い内容は非公開リポジトリを使ってください。

## 制限事項

- Whisper はペルシア語では英語より精度が下がります。言語と最高品質を選び、テキストを確認してください。
- GitHub Actions のジョブは約 6 時間が上限で、非常に長い音声を最も遅い品質で処理すると終わらない場合があります。
- 話者ラベルはテキストのみで、話者ごとの音声ファイル分離は未実装です。
- 実際の進捗はアップロードのみで、処理は「待機中・実行中・保存中」を表示します。
- GitHub と Cloudflare の無料プランには利用上限があります。
- 翻訳、ノイズ除去、話者ラベル、1 GB ファイルは実装済みですが、実環境での検証は限定的です。

## トラブルシューティング

| ⚠️ | 🔧 |
|---|---|
| 「サーバー未設定」と表示される | `config.js` が空かキャッシュ中です。Worker の URL を設定し、強制再読み込みしてください（または `config.js?v=2`）。 |
| アップロード中に `Failed to fetch` | `ALLOWED_ORIGIN` は末尾スラッシュなしで正確に `https://<user>.github.io` にし、再度 Deploy してください。 |
| 502「ジョブ作成に失敗」 | `GH_TOKEN` が誤り・期限切れ・権限不足です。再発行してください。 |
| ジョブが待機中のまま | Actions タブを開き、workflow 権限と `process.yml` の有無を確認してください。 |
| 結果が「設定が不完全」 | `JOB_SECRET` がないか、GitHub と Cloudflare で値が違います。 |
| 実行に非常に時間がかかる | 実行ログの各段階の行を確認してください。初回はモデルをダウンロードします。止まる場合はキャンセルして再実行します。 |

## ライセンスと謝辞

ご自身の `LICENSE` ファイルを追加してください。サードパーティのコンポーネントは各自のライセンスに従います。

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
