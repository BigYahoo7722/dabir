# Dabir (دبیر)

> Voz a texto con traducción: persa e inglés de entrada, 20 idiomas de salida.

[English](../README.md) · [فارسی](README.fa.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · **Español** · [Português](README.pt.md) · [Italiano](README.it.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [हिन्दी](README.hi.md) · [اردو](README.ur.md) · [বাংলা](README.bn.md) · [Indonesia](README.id.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Ελληνικά](README.el.md)

Dabir convierte grabaciones en texto. Sube un audio (mp3, m4a, wav… hasta 1 GB); detecta si es persa o inglés, lo transcribe y puede traducirlo a otros 20 idiomas. Funciona con modelos de código abierto en tu propio repositorio de GitHub, sin claves de API de IA.

## Características

- Subida por fragmentos reanudable hasta 1 GB, con compresión opcional en el navegador para redes lentas
- Detección automática persa/inglés y tres niveles de calidad
- Traducción sin conexión a 20 idiomas (Argos Translate)
- Reducción de ruido y etiquetas de hablantes (opcional)
- Resultados cifrados que solo puede leer el navegador que subió el archivo
- Biblioteca privada de dos horas, copia y exportación TXT/SRT, interfaz en persa e inglés

## Cómo funciona

El sitio (GitHub Pages) habla con un pequeño Worker de Cloudflare que guarda los secretos. El Worker almacena el audio en un Release borrador privado e inicia un trabajo de GitHub Actions que transcribe, traduce, cifra y publica el resultado.

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

## Estructura del proyecto

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

## Despliegue desde cero

1. Crea un repositorio **público** (por ejemplo `dabir`) con un README.

2. Sube todos los archivos del proyecto a la raíz del repositorio manteniendo las carpetas. La carpeta oculta `.github` se crea con **Add file → Create new file**.

3. **Settings → Actions → General → Workflow permissions →** Read and write.

4. **Settings → Pages →** Deploy from a branch → `main` / `(root)`.

5. Genera un secreto aleatorio (comando abajo) y guárdalo como secreto de Actions `JOB_SECRET`.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

6. Crea un token Fine-grained solo para este repositorio: Contents y Actions, ambos en Read and write.

7. En Cloudflare crea un Worker (Hello World), pega `worker/src/index.js`, añade las variables y secretos de la tabla y pulsa Deploy.

```bash
# Alternative to the dashboard: deploy the Worker from a terminal
cd worker
npx wrangler login
npx wrangler secret put GH_TOKEN      # the fine-grained token
npx wrangler secret put JOB_SECRET    # the same value as in GitHub
npx wrangler deploy
```

8. Pon la URL del Worker en `config.js`, haz Commit y recarga el sitio con Ctrl+Shift+R.

9. Sube un archivo de prueba corto. La primera ejecución es lenta porque se descargan y guardan los modelos.

## Configuración

Los nombres distinguen mayúsculas. `GH_TOKEN` y `JOB_SECRET` deben ser de tipo Secret; usa el mismo `JOB_SECRET` en GitHub y Cloudflare.

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

## Desarrollo y pruebas

```bash
# requires Python 3.11+, Node 22+, FFmpeg
pip install -r requirements.txt
npm install
npm test    # selftest.py, pipeline_mock.py, worker, UI and compression tests
```

## Privacidad y seguridad

- El audio solo permanece en un Release borrador privado y se borra tras el procesamiento.
- Los resultados se cifran con AES-GCM; la clave nunca sale del navegador de quien sube el archivo.
- El token de GitHub solo está en Cloudflare y nunca se envía a los visitantes.
- Las copias del servidor caducan tras aproximadamente dos horas. Para contenido sensible usa un repositorio privado.

## Limitaciones

- Whisper es menos preciso en persa que en inglés: elige el idioma y la mejor calidad, y revisa el texto.
- GitHub Actions limita un trabajo a unas 6 horas; un audio muy largo con la calidad más lenta puede no terminar.
- Las etiquetas de hablantes son solo texto; separar cada voz en su propio archivo de audio no está implementado.
- Solo el progreso de la subida es real; el procesamiento muestra en cola, en ejecución y guardando.
- Los planes gratuitos de GitHub y Cloudflare tienen límites de uso.
- La traducción, la reducción de ruido, las etiquetas de hablantes y los archivos de 1 GB están implementados, pero con pruebas reales limitadas.

## Solución de problemas

| ⚠️ | 🔧 |
|---|---|
| Mensaje «servidor sin configurar» | `config.js` está vacío o en caché: pon la URL del Worker y recarga por completo (o `config.js?v=2`). |
| `Failed to fetch` al subir | `ALLOWED_ORIGIN` debe ser exactamente `https://<user>.github.io` (sin barra final); vuelve a hacer Deploy. |
| 502 «error al crear el trabajo» | `GH_TOKEN` es incorrecto, caducó o no tiene permisos; renuévalo. |
| El trabajo sigue en cola | Abre la pestaña Actions; revisa los permisos de workflow y que exista `process.yml`. |
| Resultado «configuración incompleta» | Falta `JOB_SECRET` o difiere entre GitHub y Cloudflare. |
| La ejecución tarda mucho | Lee las líneas de etapa del registro; la primera ejecución descarga modelos; cancela y reintenta si una etapa se bloquea. |

## Licencia y créditos

Añade tu propio archivo `LICENSE`. Los componentes de terceros conservan sus licencias:

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
