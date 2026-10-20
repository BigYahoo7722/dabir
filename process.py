import json, os, glob, subprocess, re, time, traceback, hmac, hashlib, base64
import numpy as np, soundfile as sf

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def decode(src, dst):
    """لایه ۱: تبدیل هر فرمت (mp3/m4a/...) به wav تک‌کانال ۱۶k با چند روش جایگزین."""
    tries = [(None, []), (None, ["-err_detect", "ignore_err"]), ("mp3", []), ("mov", []), ("aac", [])]
    for fmt, extra in tries:
        cmd = ["ffmpeg", "-y", "-v", "error"] + (["-f", fmt] if fmt else []) + extra + \
              ["-i", src, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", dst]
        if subprocess.run(cmd, capture_output=True).returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 2000:
            x, sr = sf.read(dst, dtype="float32")
            if len(x) / sr < 0.5: raise ValueError("فایل صوتی خیلی کوتاه است.")
            if float(np.abs(x).max()) < 1e-4: raise ValueError("فایل صوتی ساکت است.")
            return len(x) / sr
    raise ValueError("این فایل قابل خواندن نیست؛ فرمت یا فایل خراب است.")

def denoise(wav, warns):
    """لایه ۲: حذف نویز تکه‌تکه (کم‌مصرف)؛ اگر خراب شد فایل اصلی حفظ می‌شود."""
    try:
        import noisereduce as nr
        x, sr = sf.read(wav, dtype="float32"); step = sr * 45; out = []
        for i in range(0, len(x), step):
            c = x[i:i + step]
            out.append(nr.reduce_noise(y=c, sr=sr, stationary=False, prop_decrease=0.85).astype("float32") if len(c) > sr else c)
        y = np.concatenate(out)
        if not np.isfinite(y).all() or float(np.abs(y).max()) < 1e-4: raise ValueError("خروجی نامعتبر")
        sf.write(wav, y, sr)
    except Exception as e:
        warns.append(f"حذف نویز انجام نشد ({e}); متن از فایل اصلی ساخته شد.")

def clean(segs):
    out = []
    for s in segs:
        t = s["text"].strip()
        if not t: continue
        if len(out) >= 2 and t == out[-1]["text"] == out[-2]["text"]: continue  # حذف تکرار توهمی
        out.append({**s, "text": t})
    return out

def fmt(segs):
    lines, last = [], None
    for s in segs:
        sp = s.get("speaker")
        if sp is not None and sp == last and lines: lines[-1] += " " + s["text"]
        else: lines.append((f"[گوینده {sp}] " if sp is not None else "") + s["text"])
        last = sp
    return "\n".join(lines)

def load_model(name, warns):
    from faster_whisper import WhisperModel
    for n in dict.fromkeys([name, "medium", "small"]):
        try:
            return WhisperModel(n, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 2), n
        except Exception as e:
            warns.append(f"بارگذاری مدل {n} ناموفق بود: {e}")
    raise RuntimeError("هیچ مدلی بارگذاری نشد.")

def seal(out, key_hex):
    """رمزنگاری AES-GCM نتیجه؛ فقط دارندهٔ کلید کار (کاربر) می‌تواند بخواند."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    iv = os.urandom(12)
    ct = AESGCM(bytes.fromhex(key_hex)).encrypt(iv, json.dumps(out, ensure_ascii=False).encode(), None)
    b = lambda x: base64.b64encode(x).decode()
    return {"v": 1, "finished": out.get("finished"), "iv": b(iv), "ct": b(ct)}

def transcribe(model, wav, warns, forced=None):
    """لایه ۳: تشخیص فارسی/انگلیسی + رونویسی با تلاش مجدد."""
    kw = dict(beam_size=5, condition_on_previous_text=False, temperature=[0, 0.2, 0.4], compression_ratio_threshold=2.4)
    _, info = model.transcribe(wav, vad_filter=True, **kw)
    p = dict(info.all_language_probs or [(info.language, 1.0)])
    lang = forced or ("fa" if p.get("fa", 0) >= p.get("en", 0) else "en")
    if not forced and p.get("fa", 0) + p.get("en", 0) < 0.3:
        warns.append(f"زبان گفتار احتمالاً فارسی یا انگلیسی نیست (تشخیص: {info.language}).")
    for vad in (True, False):
        it, _ = model.transcribe(wav, language=lang, vad_filter=vad, **kw)
        segs = clean([{"start": s.start, "end": s.end, "text": s.text} for s in it])
        if segs: return lang, segs
    raise ValueError("گفتاری در فایل پیدا نشد.")

def speakers(wav, segs, n, warns):
    """جداسازی گوینده؛ خطا در این مرحله کل کار را خراب نمی‌کند."""
    try:
        from resemblyzer import VoiceEncoder
        from resemblyzer.audio import normalize_volume
        from sklearn.cluster import AgglomerativeClustering
        enc = VoiceEncoder("cpu")
        w, _ = sf.read(wav, dtype="float32"); w = normalize_volume(w, -30, increase_only=True)  # بدون حذف سکوت تا زمان‌بندی نماند
        idx, embs = [], []
        for i, s in enumerate(segs):
            part = w[int(s["start"] * 16000):int(s["end"] * 16000)]
            if len(part) >= 16000:
                idx.append(i); embs.append(enc.embed_utterance(part))
        if len(embs) < 2:
            for s in segs: s["speaker"] = 1
            return
        kw = {"n_clusters": min(int(n), len(embs))} if n else {"n_clusters": None, "distance_threshold": 0.28}
        lab = AgglomerativeClustering(metric="cosine", linkage="average", **kw).fit_predict(np.array(embs))
        cur, m = 1, dict(zip(idx, lab))
        for i, s in enumerate(segs):
            if i in m: cur = int(m[i]) + 1
            s["speaker"] = cur
    except Exception as e:
        for s in segs: s.pop("speaker", None)
        warns.append(f"جداسازی گوینده انجام نشد ({e}).")

_argos = {}
def translator():
    if not _argos:
        import argostranslate.package as P, argostranslate.translate as T
        P.update_package_index(); _argos.update(P=P, T=T, pk=P.get_available_packages())
    return _argos["P"], _argos["T"], _argos["pk"]

def ensure(a, b):
    P, T, pk = translator()
    def ok():
        L = {l.code: l for l in T.get_installed_languages()}
        return a in L and b in L and L[a].get_translation(L[b]) is not None
    if ok(): return True
    for p in pk:
        if p.from_code == a and p.to_code == b:
            log(f"دانلود بستهٔ ترجمه {a} به {b}"); P.install_from_path(p.download()); break
    return ok()

def tr1(t, a, b):
    return translator()[1].translate(t, a, b)

def translate(segs, a, b, warns):
    """لایه ۴: ترجمه مستقیم؛ در صورت نبود یا خروجی مشکوک، ترجمه از طریق انگلیسی."""
    def run(path):
        for x, y in zip(path, path[1:]):
            if not ensure(x, y): return None
        res = []
        for s in segs:
            t = s["text"]
            for x, y in zip(path, path[1:]): t = tr1(t, x, y)
            res.append(t.strip())
        return res
    def good(r):
        if not r or sum(bool(x) for x in r) < 0.8 * len(r): return False
        same = sum(x == s["text"] for x, s in zip(r, segs))
        return same < 0.5 * len(r)
    res = None
    for path in ([a, b], [a, "en", b]) if "en" not in (a, b) else ([a, b],):
        try: res = run(path)
        except Exception: res = None
        if good(res):
            res = [x or s["text"] for s, x in zip(segs, res)]
            return fmt([{**s, "text": x} for s, x in zip(segs, res)]), res
    warns.append(f"ترجمه به {b} قابل اعتماد نبود و ارائه نشد.")
    return None

def process(jd, rdir="results", key=None):
    jid = os.path.basename(jd); out = {"id": jid, "warnings": []}; w = out["warnings"]
    try:
        job = json.load(open(jd + "/job.json"))
        src = next(iter(glob.glob(jd + "/audio.*")), None)
        if not src: raise ValueError("فایل صوتی پیدا نشد.")
        wav = f"/tmp/{jid}.wav"; out["duration"] = round(decode(src, wav), 1); log(f"صدا آماده شد: {out['duration']} ثانیه")
        if job.get("denoise"): denoise(wav, w)
        model, used = load_model(job.get("quality", "medium"), w); out["model"] = used; log(f"مدل بارگذاری شد: {used}")
        lang, segs = transcribe(model, wav, w, job.get("source") if job.get("source") in ("fa", "en") else None); log(f"رونویسی تمام شد: زبان {lang}، {len(segs)} قطعه")
        if job.get("speakers"): speakers(wav, segs, job.get("nspeakers"), w)
        out.update(language=lang, text=fmt(segs), translations={}, tlines={}, segments=[{"s": round(x["start"], 2), "e": round(x["end"], 2), "t": x["text"], "sp": x.get("speaker")} for x in segs])
        for t in job.get("targets", []):
            if t == lang: continue
            try:
                log(f"شروع ترجمه به {t}")
                r = translate(segs, lang, t, w)
                log(f"ترجمه به {t} تمام شد")
                if r: out["translations"][t] = r[0]; out["tlines"][t] = r[1]
            except Exception as e:
                w.append(f"ترجمه به {t} ناموفق بود ({e}).")
    except Exception as e:
        out["error"] = str(e); traceback.print_exc()
    out["finished"] = int(time.time())
    json.dump(seal(out, key) if key else out, open(f"{rdir}/{jid}.json", "w"), ensure_ascii=False)

def gh(*a):
    return subprocess.run(["gh", "api", *a], capture_output=True, check=True).stdout

def fetch_audio(repo, rel, dst, opts):
    """دانلود تکه‌های فایل از Release خصوصی و چسباندن آن‌ها؛ با بررسی کامل بودن."""
    assets = sorted(json.loads(gh(f"repos/{repo}/releases/{rel}"))["assets"], key=lambda a: a["name"])
    if not assets or len(assets) != opts.get("parts", len(assets)): raise ValueError("بارگذاری فایل ناقص بود؛ دوباره آپلود کنید.")
    with open(dst, "wb") as out:
        for a in assets: out.write(gh("-H", "Accept: application/octet-stream", f"repos/{repo}/releases/assets/{a['id']}"))
    if opts.get("size") and os.path.getsize(dst) != opts["size"]: raise ValueError("حجم فایل دریافتی با فایل اصلی نمی‌خواند؛ دوباره آپلود کنید.")

def main():
    jid, repo, rel = os.environ["JID"], os.environ["REPO"], os.environ["REL"]
    assert re.fullmatch(r"[a-z0-9]+", jid)
    opts = json.loads(os.environ.get("OPTS") or "{}")
    jd = f"/tmp/job/{jid}"; os.makedirs(jd, exist_ok=True); os.makedirs("data/results", exist_ok=True)
    sec = os.environ.get("JOB_SECRET", "")
    key = hmac.new(sec.encode(), f"{jid}:{rel}".encode(), hashlib.sha256).hexdigest() if sec else None
    try:
        if not key: raise ValueError("پیکربندی سرور ناقص است (JOB_SECRET).")
        fetch_audio(repo, rel, jd + "/audio.bin", opts)
        json.dump(opts, open(jd + "/job.json", "w")); process(jd, "data/results", key)
    except Exception as e:
        err = {"id": jid, "error": str(e), "warnings": [], "finished": int(time.time())}
        json.dump(seal(err, key) if key else err, open(f"data/results/{jid}.json", "w"), ensure_ascii=False)
    try: gh("-X", "DELETE", f"repos/{repo}/releases/{rel}")  # فایل صوتی از سرور پاک می‌شود
    except Exception: pass

if __name__ == "__main__":
    main()
