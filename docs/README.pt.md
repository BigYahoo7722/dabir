# Dabir (دبیر)

> Fala para texto com tradução: persa e inglês na entrada, 20 idiomas na saída.

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md) · **Português** · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

O Dabir transforma gravações em texto. Envie um áudio (mp3, m4a, wav… até 1 GB); ele detecta se é persa ou inglês, transcreve e pode traduzir para outros 20 idiomas. Roda com modelos de código aberto no seu próprio repositório do GitHub, sem chaves de API de IA.

## Recursos

- Envio em partes retomável até 1 GB, com compressão opcional no navegador para redes lentas
- Detecção automática persa/inglês e três níveis de qualidade
- Tradução offline para 20 idiomas (Argos Translate)
- Redução de ruído e rótulos de falantes (opcional)
- Resultados criptografados que só o navegador que enviou o arquivo consegue ler
- Biblioteca privada de duas horas, cópia e exportação TXT/SRT, interface em persa e inglês

## Como funciona

O site (GitHub Pages) conversa com um pequeno Worker da Cloudflare que guarda os segredos. O Worker armazena o áudio em um Release rascunho privado e inicia um job do GitHub Actions que transcreve, traduz, criptografa e publica o resultado.

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

## Estrutura do projeto

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

## Implantação do zero

1. Crie um repositório **público** (por exemplo `dabir`) com um README.

2. Envie todos os arquivos do projeto para a raiz do repositório mantendo as pastas. A pasta oculta `.github` é criada com **Add file → Create new file**.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. Gere um segredo aleatório (comando abaixo) e salve como segredo do Actions `JOB_SECRET`.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. Crie um token Fine-grained apenas para este repositório: Contents e Actions, ambos em Read and write.

7. Na Cloudflare crie um Worker (Hello World), cole `worker/src/index.js`, adicione as variáveis e segredos da tabela e clique em Deploy.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Coloque a URL do Worker em `config.js`, faça Commit e atualize o site com Ctrl+Shift+R.

9. Envie um arquivo de teste curto. A primeira execução é lenta porque os modelos são baixados e guardados em cache.

## Configuração

Os nomes diferenciam maiúsculas e minúsculas. `GH_TOKEN` e `JOB_SECRET` devem ser do tipo Secret; use o mesmo `JOB_SECRET` no GitHub e na Cloudflare.

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

## Desenvolvimento e testes

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## Privacidade e segurança

- O áudio fica apenas em um Release rascunho privado e é apagado após o processamento.
- Os resultados são criptografados com AES-GCM; a chave nunca sai do navegador de quem enviou.
- O token do GitHub fica só na Cloudflare e nunca é enviado aos visitantes.
- As cópias do servidor expiram após cerca de duas horas. Para conteúdo sensível, use um repositório privado.

## Limitações

- O Whisper é menos preciso em persa do que em inglês: escolha o idioma e a melhor qualidade e revise o texto.
- O GitHub Actions limita um job a cerca de 6 horas; áudio muito longo na qualidade mais lenta pode não terminar.
- Os rótulos de falantes são apenas texto; separar cada voz em um arquivo de áudio próprio não está implementado.
- Só o progresso do envio é real; o processamento mostra na fila, em execução e salvando.
- Os planos gratuitos do GitHub e da Cloudflare têm limites de uso.
- Tradução, redução de ruído, rótulos de falantes e arquivos de 1 GB estão implementados, mas com testes reais limitados.

## Solução de problemas

| ⚠️ | 🔧 |
|---|---|
| Mensagem “servidor não configurado” | `config.js` está vazio ou em cache: informe a URL do Worker e recarregue por completo (ou `config.js?v=2`). |
| `Failed to fetch` no envio | `ALLOWED_ORIGIN` deve ser exatamente `https://<user>.github.io` (sem barra no fim); faça Deploy de novo. |
| 502 “falha ao criar o job” | `GH_TOKEN` está errado, expirou ou não tem permissões; renove-o. |
| O job fica na fila | Abra a aba Actions; verifique as permissões de workflow e se `process.yml` existe. |
| Resultado “configuração incompleta” | `JOB_SECRET` está ausente ou difere entre GitHub e Cloudflare. |
| A execução demora muito | Leia as linhas de etapa no log; a primeira execução baixa modelos; cancele e tente de novo se uma etapa travar. |

## Licença e créditos

Adicione seu próprio arquivo `LICENSE`. Componentes de terceiros mantêm suas licenças:

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
