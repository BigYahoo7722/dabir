import json, os, glob, subprocess, re, time, traceback, hmac, hashlib, base64
import asr, notes
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

def fmt(segs):
    """متن خطی با برچسب گوینده؛ فقط کلمه‌ها را می‌چسباند، چیزی تغییر نمی‌دهد."""
    lines, last = [], None
    for s in segs:
        sp = s.get("speaker")
        if sp is not None and sp == last and lines: lines[-1] += " " + s["text"]
        else: lines.append((f"[گوینده {sp}] " if sp is not None else "") + s["text"])
        last = sp
    return "\n".join(lines)

def seal(out, key_hex):
    """رمزنگاری AES-GCM نتیجه؛ فقط دارندهٔ کلید کار (کاربر) می‌تواند بخواند."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    iv = os.urandom(12)
    ct = AESGCM(bytes.fromhex(key_hex)).encrypt(iv, json.dumps(out, ensure_ascii=False).encode(), None)
    b = lambda x: base64.b64encode(x).decode()
    return {"v": 1, "finished": out.get("finished"), "iv": b(iv), "ct": b(ct)}

class Prog:
    """گزارش پیشرفت زنده: JSON کوچک در بدنهٔ Release پیش‌نویس (بدون commit)؛ Worker آن را به سایت می‌رساند."""
    def __init__(self, repo, rel): self.repo, self.rel, self.dur, self.last = repo, rel, 0.0, 0.0
    def put(self, stage, frac=None, eta=None, force=False):
        now = time.time()
        if not force and now - self.last < 12: return
        self.last = now
        body = json.dumps({"s": stage, "p": None if frac is None else round(frac, 3), "e": None if eta is None else int(eta), "t": int(now), "d": self.dur})
        try: gh("-X", "PATCH", f"repos/{self.repo}/releases/{self.rel}", "-f", f"body={body}")
        except Exception: pass

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
    """ترجمه جدا از رونویسی. هر قطعه از زبان واقعی خودش ترجمه می‌شود (گفتار ترکیبی)؛ قطعهٔ هم‌زبانِ مقصد دست‌نخورده می‌ماند."""
    def routes(sl):
        sl = sl or a
        return [[sl, b]] if "en" in (sl, b) else [[sl, b], [sl, "en", b]]
    def run(sl, path, items):
        for x, y in zip(path, path[1:]):
            if not ensure(x, y): return None
        res = []
        for _, s in items:
            t = s["text"]
            for x, y in zip(path, path[1:]): t = tr1(t, x, y)
            res.append(t.strip())
        return res
    out = [s["text"] for s in segs]; ok_all = True
    for sl in dict.fromkeys(s.get("lang") or a for s in segs):
        if sl == b: continue
        items = [(i, s) for i, s in enumerate(segs) if (s.get("lang") or a) == sl and s["text"] != asr.UNCLEAR]
        if not items: continue
        res = None
        for path in routes(sl):
            try: r = run(sl, path, items)
            except Exception: r = None
            same = sum(x == s["text"] for x, (_, s) in zip(r or [], items))
            if r and sum(bool(x) for x in r) >= 0.8 * len(r) and same < 0.5 * len(r): res = r; break
        if res is None: ok_all = False; continue
        for (i, s), x in zip(items, res): out[i] = x or s["text"]
    if not ok_all and out == [s["text"] for s in segs]:
        warns.append(f"ترجمه به {b} قابل اعتماد نبود و ارائه نشد."); return None
    if not ok_all: warns.append(f"ترجمهٔ بخشی از گفتار به {b} قابل اعتماد نبود؛ آن بخش‌ها به زبان اصلی ماندند.")
    return fmt([{**s, "text": x} for s, x in zip(segs, out)]), out

def process(jd, rdir="results", key=None, prog=None, models=None, llm=None):
    """رونویسی وفادار (+ اختیاری: جزوه، گوینده، ترجمه). تنظیم مدل/زبان/کیفیت خودکار است و از کاربر گرفته نمی‌شود."""
    jid = os.path.basename(jd); out = {"id": jid, "warnings": []}; w = out["warnings"]; tm = {}; T0 = time.time()
    try:
        job = json.load(open(jd + "/job.json"))
        src = next(iter(glob.glob(jd + "/audio.*")), None)
        if not src: raise ValueError("فایل صوتی پیدا نشد.")
        wav = f"/tmp/{jid}.wav"; out["duration"] = round(decode(src, wav), 1); tm["decode"] = round(time.time() - T0, 1)
        log(f"صدا آماده شد: {out['duration']} ثانیه")
        if prog: prog.dur = out["duration"]; prog.put("denoise" if job.get("denoise") else "model", force=True)
        if job.get("denoise"): denoise(wav, w)
        t1 = time.time()
        models = models or asr.Models.load(w)
        tm["model"] = round(time.time() - t1, 1); out["model_status"] = models.status
        if prog: prog.put("transcribe", 0.0, force=True)
        t2 = time.time()
        lang, segs, used = asr.transcribe(models, wav, w, prog)
        out["model"] = "+".join(used); tm["transcribe"] = round(time.time() - t2, 1)
        log(f"رونویسی تمام شد: زبان غالب {lang}، {len(segs)} قطعه")
        if job.get("speakers"):
            if prog: prog.put("speakers", force=True)
            speakers(wav, segs, job.get("nspeakers"), w)
        out.update(language=lang, text=fmt(segs), translations={}, tlines={}, review=asr.low_confidence(segs),
                   segments=[{"s": round(x["start"], 2), "e": round(x["end"], 2), "t": x["text"], "sp": x.get("speaker"), "l": x.get("lang"), "est": bool(x.get("est"))} for x in segs])
        out["srt"] = asr.to_srt(segs)
        if job.get("notes"):  # فقط وقتی کاربر خواسته؛ در غیر این صورت هیچ مدل زبانی بارگیری نمی‌شود
            t4 = time.time()
            try:
                if prog: prog.put("notes", 0.0, force=True)
                r = notes.build(segs, llm or notes.LlamaCppBackend(), out["review"], prog)
                out["notes"] = r["markdown"]; out["notes_coverage"] = r["coverage"]
                if r["coverage"]["extracted"] < r["coverage"]["chunks"]: w.append("بخشی از جزوه ساخته نشد؛ بخش «نیازمند بررسی» را ببینید.")
            except Exception as e:
                out["notes_error"] = str(e)[:300]; w.append(f"ساخت جزوه ناموفق بود ({e}); رونویسی کامل سالم است.")
            tm["notes"] = round(time.time() - t4, 1)
        tg = [t for t in job.get("targets", []) if t != lang]; t3 = time.time()
        for k, t in enumerate(tg):
            if prog: prog.put("translate", k / len(tg), force=True)
            try:
                r = translate(segs, lang, t, w)
                if r: out["translations"][t] = r[0]; out["tlines"][t] = r[1]
            except Exception as e:
                w.append(f"ترجمه به {t} ناموفق بود ({e}).")
        tm["translate"] = round(time.time() - t3, 1)
    except Exception as e:
        out["error"] = str(e); traceback.print_exc()
    out["finished"] = int(time.time()); tm["total"] = round(time.time() - T0, 1); out["timing"] = tm
    # شکست مرحلهٔ اصلی هرگز موفقیت نیست؛ مدل تخصصی ناموفق نیز در model_status و warnings دیده می‌شود.
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
    """STAGE=fetch (توکن لازم) ← process (بدون Secret) ← seal (Secret، بدون صوت). STAGE=all برای تست/اجرای محلی."""
    jid, repo, rel = os.environ["JID"], os.environ["REPO"], os.environ["REL"]
    assert re.fullmatch(r"[a-z0-9]+", jid)
    stage = os.environ.get("STAGE", "all")
    opts = json.loads(os.environ.get("OPTS") or "{}")
    jd = f"/tmp/job/{jid}"; os.makedirs(jd, exist_ok=True); os.makedirs("data/results", exist_ok=True)
    sec = os.environ.get("JOB_SECRET", "")
    key = hmac.new(sec.encode(), f"{jid}:{rel}".encode(), hashlib.sha256).hexdigest() if sec else None
    if stage in ("fetch", "all"):
        try:
            fetch_audio(repo, rel, jd + "/audio.bin", opts); json.dump(opts, open(jd + "/job.json", "w"))
        except Exception as e:
            json.dump({"error": str(e)}, open(jd + "/fetch_error.json", "w"))
        if stage == "fetch": return
    if stage in ("process", "all") and not os.path.exists(jd + "/fetch_error.json"):
        os.makedirs(jd + "/out", exist_ok=True)
        process(jd, jd + "/out" if stage == "process" else "data/results", key if stage == "all" else None, Prog(repo, rel))
    if stage == "process": return
    # seal: فقط JSON نتیجه را رمز می‌کند و Release را حذف می‌کند (در حالت all، process خودش مهر می‌کند)
    try:
        if not key: raise ValueError("پیکربندی سرور ناقص است (JOB_SECRET).")
        fe = jd + "/fetch_error.json"; rf = jd + f"/out/{jid}.json"
        if os.path.exists(fe): res = {"id": jid, "error": json.load(open(fe))["error"], "warnings": [], "finished": int(time.time())}
        elif stage == "seal": res = json.load(open(rf)) if os.path.exists(rf) else {"id": jid, "error": "پردازش بدون نتیجه پایان یافت.", "warnings": [], "finished": int(time.time())}
        else: res = None
        if res is not None: json.dump(seal(res, key), open(f"data/results/{jid}.json", "w"), ensure_ascii=False)
    except Exception as e:
        err = {"id": jid, "error": str(e), "warnings": [], "finished": int(time.time())}
        json.dump(seal(err, key) if key else err, open(f"data/results/{jid}.json", "w"), ensure_ascii=False)
    if stage in ("seal", "all"):
        try: gh("-X", "DELETE", f"repos/{repo}/releases/{rel}")
        except Exception as e: print(f"[cleanup] حذف Release ناموفق بود: {e}", flush=True)  # cleanup.py دوباره تلاش و گزارش می‌کند

if __name__ == "__main__":
    main()
