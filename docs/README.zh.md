# Dabir (دبیر)

> 语音转文字并翻译：输入波斯语或英语，输出 20 种语言。

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · **中文** · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir 将录音转换为文字。上传音频（mp3、m4a、wav 等，最大 1 GB），它会判断是波斯语还是英语，完成转写，并可翻译成另外 20 种语言。使用开源模型，在你自己的 GitHub 仓库中运行，无需任何 AI API 密钥。

## 功能

- 最大 1 GB 的分块可续传上传，慢速网络可选浏览器内压缩
- 自动识别波斯语/英语，三档质量
- 离线翻译为 20 种语言（Argos Translate）
- 可选降噪与说话人标注
- 结果经加密，只有上传文件的浏览器能读取
- 两小时私人资料库、复制与 TXT/SRT 导出、波斯语和英语界面

## 工作原理

网站（GitHub Pages）调用一个保管密钥的小型 Cloudflare Worker。Worker 把音频存入私有草稿 Release，并启动 GitHub Actions 任务，完成转写、翻译、加密并发布结果。

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

## 项目结构

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

## 从零部署

1. 创建一个带 README 的**公开**仓库（例如 `dabir`）。

2. 将所有项目文件连同文件夹上传到仓库根目录。隐藏的 `.github` 文件夹需通过 **Add file → Create new file** 创建。

3. **Settings → Actions → General → Workflow permissions →** 选择 Read and write。

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`。

5. 生成随机密钥（见下方命令），保存为 Actions 密钥 `JOB_SECRET`。

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. 仅为此仓库创建 Fine-grained 令牌：Contents 和 Actions 均为 Read and write。

7. 在 Cloudflare 创建 Worker（Hello World），粘贴 `worker/src/index.js`，按表格添加变量和密钥，然后 Deploy。

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. 把 Worker 地址写入 `config.js`，Commit 后用 Ctrl+Shift+R 刷新网站。

9. 上传一个简短的测试文件。首次运行较慢，因为需要下载并缓存模型。

## 配置

名称区分大小写。`GH_TOKEN` 和 `JOB_SECRET` 必须是 Secret 类型；GitHub 与 Cloudflare 中的 `JOB_SECRET` 必须相同。

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

## 开发与测试

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## 隐私与安全

- 音频仅保存在私有草稿 Release 中，处理后即删除。
- 结果使用 AES-GCM 加密，密钥不会离开上传者的浏览器。
- GitHub 令牌只存在于 Cloudflare，绝不发送给访客。
- 服务器副本约两小时后过期。敏感内容请使用私有仓库。

## 限制

- Whisper 对波斯语的准确度低于英语：请选择语言和最高质量，并校对文本。
- GitHub Actions 单个任务约 6 小时上限；超长音频配最慢质量可能无法完成。
- 说话人标注仅为文字；尚未实现把每个人的声音拆分为独立音频文件。
- 只有上传进度是真实的；处理阶段显示排队、运行和保存。
- GitHub 与 Cloudflare 的免费方案有用量限制。
- 翻译、降噪、说话人标注和 1 GB 文件已实现，但实际测试有限。

## 故障排除

| ⚠️ | 🔧 |
|---|---|
| 提示“服务器未配置” | `config.js` 为空或被缓存：填入 Worker 地址并强制刷新（或访问 `config.js?v=2`）。 |
| 上传时出现 `Failed to fetch` | `ALLOWED_ORIGIN` 必须恰为 `https://<user>.github.io`（末尾无斜杠）；重新 Deploy。 |
| 502“创建任务失败” | `GH_TOKEN` 错误、过期或权限不足；请更换。 |
| 任务一直排队 | 打开 Actions 标签页；检查 workflow 权限和 `process.yml` 是否存在。 |
| 结果为“配置不完整” | 缺少 `JOB_SECRET`，或 GitHub 与 Cloudflare 中的值不一致。 |
| 运行时间很长 | 查看运行日志中的阶段行；首次运行会下载模型；某阶段卡住时取消并重试。 |

## 许可与致谢

请添加你自己的 `LICENSE` 文件。第三方组件保留各自许可：

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
