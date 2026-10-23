# Dabir (دبیر)

> 번역을 지원하는 음성-텍스트 변환: 페르시아어·영어 입력, 20개 언어 출력.

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · **한국어** · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir는 녹음을 텍스트로 바꿔 줍니다. 오디오 파일(mp3, m4a, wav 등, 최대 1 GB)을 올리면 페르시아어인지 영어인지 판별해 받아쓰고, 다른 20개 언어로 번역할 수도 있습니다. 오픈소스 모델을 내 GitHub 저장소에서 실행하며 AI API 키가 필요 없습니다.

## 기능

- 최대 1 GB 이어 올리기 가능한 분할 업로드, 느린 네트워크용 브라우저 내 압축(선택)
- 페르시아어/영어 자동 감지와 3단계 품질
- 20개 언어 오프라인 번역(Argos Translate)
- 선택형 소음 제거와 화자 표시
- 업로드한 브라우저만 읽을 수 있는 암호화된 결과
- 2시간 비공개 라이브러리, 복사 및 TXT/SRT 내보내기, 페르시아어·영어 인터페이스

## 작동 방식

사이트(GitHub Pages)는 비밀 값을 보관하는 작은 Cloudflare Worker를 호출합니다. Worker는 오디오를 비공개 초안 Release에 저장하고, 받아쓰기·번역·암호화·결과 게시를 수행하는 GitHub Actions 작업을 시작합니다.

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

## 프로젝트 구조

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

## 처음부터 배포하기

1. README가 있는 **공개** 저장소(예: `dabir`)를 만듭니다.

2. 프로젝트 파일 전체를 폴더 구조 그대로 저장소 루트에 업로드합니다. 숨김 폴더 `.github`는 **Add file → Create new file**로 만듭니다.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. 무작위 비밀 값을 생성하고(아래 명령) Actions 시크릿 `JOB_SECRET`으로 저장합니다.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. 이 저장소 전용 Fine-grained 토큰을 만듭니다. Contents와 Actions 모두 Read and write.

7. Cloudflare에서 Worker(Hello World)를 만들고 `worker/src/index.js`를 붙여 넣은 뒤 표의 변수와 시크릿을 추가하고 Deploy 합니다.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Worker 주소를 `config.js`에 넣고 Commit한 다음 Ctrl+Shift+R로 사이트를 새로 고칩니다.

9. 짧은 테스트 파일을 올립니다. 첫 실행은 모델을 내려받아 캐시하므로 느립니다.

## 설정

이름은 대소문자를 구분합니다. `GH_TOKEN`과 `JOB_SECRET`은 Secret 유형이어야 하며 `JOB_SECRET`은 GitHub와 Cloudflare에서 같아야 합니다.

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

## 개발 및 테스트

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## 개인정보 및 보안

- 오디오는 비공개 초안 Release에만 있고 처리 후 삭제됩니다.
- 결과는 AES-GCM으로 암호화되며 키는 업로드한 브라우저를 벗어나지 않습니다.
- GitHub 토큰은 Cloudflare에만 있고 방문자에게 전송되지 않습니다.
- 서버 사본은 약 2시간 후 만료됩니다. 민감한 내용은 비공개 저장소를 사용하세요.

## 제한 사항

- Whisper는 페르시아어가 영어보다 정확도가 낮습니다. 언어와 최고 품질을 선택하고 텍스트를 검토하세요.
- GitHub Actions는 작업을 약 6시간으로 제한하므로 매우 긴 오디오를 가장 느린 품질로 처리하면 끝나지 않을 수 있습니다.
- 화자 표시는 텍스트뿐이며, 화자별로 오디오 파일을 분리하는 기능은 구현되지 않았습니다.
- 실제 진행률은 업로드만 해당하며, 처리 중에는 대기·실행·저장 상태만 표시됩니다.
- GitHub와 Cloudflare 무료 요금제에는 사용 한도가 있습니다.
- 번역, 소음 제거, 화자 표시, 1 GB 파일은 구현되었지만 실제 환경 테스트는 제한적입니다.

## 문제 해결

| ⚠️ | 🔧 |
|---|---|
| “서버가 설정되지 않음” 메시지 | `config.js`가 비어 있거나 캐시되었습니다. Worker 주소를 넣고 강력 새로 고침하세요(또는 `config.js?v=2`). |
| 업로드 중 `Failed to fetch` | `ALLOWED_ORIGIN`은 끝에 슬래시 없이 정확히 `https://<user>.github.io`여야 합니다. 다시 Deploy 하세요. |
| 502 “작업 생성 실패” | `GH_TOKEN`이 잘못되었거나 만료되었거나 권한이 부족합니다. 교체하세요. |
| 작업이 계속 대기 중 | Actions 탭을 열고 workflow 권한과 `process.yml` 존재 여부를 확인하세요. |
| 결과가 “설정 불완전” | `JOB_SECRET`이 없거나 GitHub와 Cloudflare 값이 다릅니다. |
| 실행이 매우 오래 걸림 | 실행 로그의 단계 줄을 확인하세요. 첫 실행은 모델을 내려받습니다. 단계가 멈추면 취소 후 다시 실행하세요. |

## 라이선스 및 감사

원하는 `LICENSE` 파일을 추가하세요. 서드파티 구성 요소는 각자의 라이선스를 따릅니다:

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
