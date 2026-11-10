"""رونویسی وفادار فارسی/انگلیسی: قطعه‌بندی با VAD، تشخیص زبان در سطح قطعه، زمان‌بندی معتبر.

اصل‌ها: متن گفته‌شده بازنویسی/خلاصه نمی‌شود؛ بخش نامفهوم با برچسب مشخص می‌شود؛ شکست مدل تخصصی
پنهان نمی‌شود (در status و warnings می‌آید)؛ هیچ عدد اطمینان ساختگی تولید نمی‌شود.
"""
import os, re, time
import numpy as np

SR = 16000
UNCLEAR = "[نامفهوم]"
# مدل عمومی چندزبانه (قالب CTranslate2 رسمی faster-whisper). نسخه را با ASR_GENERAL_REV قفل کنید.
GENERAL_REPO = os.environ.get("ASR_GENERAL_REPO", "Systran/faster-whisper-large-v3")
GENERAL_REV = os.environ.get("ASR_GENERAL_REV") or None
# مدل تخصصی فارسی: فقط اگر صراحتاً فعال شود (ASR_FA_REPO) و پوشهٔ تبدیل‌شده سالم باشد.
FA_REPO = os.environ.get("ASR_FA_REPO") or None


# ---------- قطعه‌بندی ----------
def plan_chunks(x, max_s=28.0, vad=None):
    """برش در مکث‌ها. خروجی: [{'a','b','forced'}] به نمونه. forced یعنی برش اجباری وسط گفتار (نیازمند هم‌پوشانی)."""
    if vad is None:
        from faster_whisper.vad import get_speech_timestamps, VadOptions
        vad = lambda a: get_speech_timestamps(a, VadOptions(max_speech_duration_s=max_s, min_silence_duration_ms=400, speech_pad_ms=300))
    out = []
    for c in vad(x):
        a, b = int(c["start"]), int(c["end"])
        out.append({"a": a, "b": b, "forced": (b - a) >= (max_s - 0.6) * SR})
    return out


def merge_short(chunks, min_s=1.0, gap_s=0.6, max_s=28.0):
    """قطعه‌های خیلی کوتاه و نزدیک را ادغام می‌کند (کلمهٔ کوتاه مثل «آها» جدا و گم نشود)."""
    out = []
    for c in chunks:
        if out and (c["a"] - out[-1]["b"]) < gap_s * SR and (c["b"] - out[-1]["a"]) <= max_s * SR and \
                ((c["b"] - c["a"]) < min_s * SR or (out[-1]["b"] - out[-1]["a"]) < min_s * SR):
            out[-1] = {"a": out[-1]["a"], "b": c["b"], "forced": c["forced"]}
        else:
            out.append(dict(c))
    return out


def words(t): return re.findall(r"\S+", t or "")


def dedupe_overlap(prev, new, min_words=3, max_words=25):
    """حذف کلمات تکراریِ ناشی از هم‌پوشانی: فقط اگر پسوند متن قبلی با پیشوند متن جدید دقیقاً یکی باشد."""
    a, b = words(prev), words(new)
    for k in range(min(len(a), len(b), max_words), min_words - 1, -1):
        if a[-k:] == b[:k]: return " ".join(b[k:])
    return new


# ---------- زمان‌بندی ----------
def valid_timing(segs, dur):
    """آیا زمان‌های مدل قابل‌اعتماد است؟ (صعودی، داخل قطعه، پوشش معقول)"""
    if not segs: return False
    last = -1e-6; cover = 0.0
    for s in segs:
        if s["end"] <= s["start"] or s["start"] < last - 0.05 or s["end"] > dur + 1.0 or s["start"] < -0.05: return False
        last = s["end"]; cover += s["end"] - s["start"]
    return cover >= 0.4 * dur or dur < 2.0


def split_timing(text, a, b):
    """تقسیم تقریبی متنِ یک قطعه به جمله‌ها، متناسب با تعداد حروف، داخل [a,b]. برآورد است نه اندازه‌گیری."""
    parts = [p.strip() for p in re.split(r"(?<=[.!؟?!،,؛;])\s+", text) if p.strip()] or [text.strip()]
    if len(parts) > 1 and (b - a) / len(parts) < 1.2: parts = [text.strip()]
    tot = sum(len(p) for p in parts) or 1; t = a; out = []
    for p in parts:
        e = t + (b - a) * len(p) / tot
        out.append({"start": round(t, 3), "end": round(e, 3), "text": p, "est": True}); t = e
    return out


# ---------- پاک‌سازی بدون تغییر گفتار ----------
def collapse_loops(segs, warns, run=4):
    """فقط حلقهٔ توهمی (≥۴ تکرار پشت‌سرهم یک جملهٔ بلند) را کم می‌کند و گزارش می‌دهد. تکرار واقعی کوتاه حفظ می‌شود."""
    out, i = [], 0
    while i < len(segs):
        j = i
        while j + 1 < len(segs) and segs[j + 1]["text"] == segs[i]["text"]: j += 1
        n = j - i + 1
        if n >= run and len(words(segs[i]["text"])) >= 3:
            out.append(segs[i]); warns.append(f"{n} تکرار پشت‌سرهم یک جمله در حدود {fmt_t(segs[i]['start'])} به‌عنوان توهم مدل یکی شد؛ بازبینی کنید.")
        else: out.extend(segs[i:j + 1])
        i = j + 1
    return out


def fmt_t(s): s = int(s); return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


# ---------- مدیریت مدل ----------
class Models:
    """مدل عمومی همیشه لازم است. مدل تخصصی اختیاری؛ شکستش در status ثبت و به کاربر نشان داده می‌شود."""
    def __init__(self, general=None, fa=None, status=None):
        self.general, self.fa, self.status = general, fa, status or {}

    @classmethod
    def load(cls, warns, fa_dir=None):
        from faster_whisper import WhisperModel
        from huggingface_hub import snapshot_download
        st = {"general": {"repo": GENERAL_REPO, "rev": GENERAL_REV or "unpinned"}, "fa": {"state": "not_configured"}}
        path = snapshot_download(GENERAL_REPO, revision=GENERAL_REV)
        g = WhisperModel(path, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 2)
        fa = None; fa_dir = os.path.expanduser(fa_dir or os.environ.get("FA_MODEL_DIR") or "") or None
        if FA_REPO or fa_dir:
            st["fa"] = {"state": "failed", "repo": FA_REPO}
            try:
                if not (fa_dir and os.path.exists(fa_dir + "/model.bin") and os.path.exists(fa_dir + "/ok")):
                    raise RuntimeError("تبدیل مدل تخصصی به CTranslate2 کامل نشد یا فایل تأیید ok نیست")
                fa = WhisperModel(fa_dir, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 2)
                st["fa"]["state"] = "ok"
            except Exception as e:
                st["fa"]["error"] = str(e)[:300]
                warns.append(f"مدل تخصصی فارسی آماده نشد ({e}). رونویسی با مدل عمومی انجام شد و ممکن است برای فارسی کمی ضعیف‌تر باشد.")
        return cls(g, fa, st)


def detect_lang(model, a, warns_seen):
    """زبان قطعه، فقط بین fa/en مگر زبان دیگری با اطمینان بالا باشد."""
    try:
        lang, prob, allp = model.detect_language(a[:SR * 30])
        p = dict(allp or [(lang, prob)])
    except Exception:
        return "fa", {}
    fa, en = p.get("fa", 0.0), p.get("en", 0.0)
    if fa + en < 0.3 and prob > 0.6 and lang not in ("fa", "en"): warns_seen.add(lang)
    return ("en" if en > fa and en >= 0.5 else "fa"), p


def transcribe_chunk(models, audio, lang, hotwords=None):
    """رونویسی یک قطعه؛ فارسی با مدل تخصصی (اگر هست)، انگلیسی با مدل عمومی. خروجی: (segments نسبی, مدل_استفاده‌شده)."""
    dur = len(audio) / SR
    kw = dict(beam_size=5, condition_on_previous_text=False, temperature=[0, 0.2, 0.4], compression_ratio_threshold=2.4,
              log_prob_threshold=-1.0, no_speech_threshold=0.6, vad_filter=False)
    if hotwords: kw["hotwords"] = hotwords
    use_fa = lang == "fa" and models.fa is not None
    m = models.fa if use_fa else models.general
    def run(ts):
        it, _ = m.transcribe(audio, language=lang, task="transcribe", without_timestamps=not ts, **kw)
        res = []
        for s in it:
            t = (s.text or "").strip()
            if not t: continue
            if getattr(s, "no_speech_prob", 0) > 0.8 and getattr(s, "avg_logprob", 0) < -1.0: continue
            res.append({"start": s.start if ts else 0.0, "end": s.end if ts else dur, "text": t,
                        "lp": getattr(s, "avg_logprob", None)})
        return res
    segs = run(True)
    if not valid_timing(segs, dur):
        flat = run(False) if not segs or any(s["end"] > dur + 1 for s in segs) else segs
        txt = " ".join(s["text"] for s in flat).strip()
        segs = split_timing(txt, 0.0, dur) if txt else []
    return segs, ("fa-specialist" if use_fa else "general")


def transcribe(models, wav_path, warns, prog=None, hotwords=None, vad=None):
    """رونویسی کل فایل. خروجی: (lang_main, segments[{start,end,text,lang,lp?,est?}], used_models)."""
    import soundfile as sf
    x, _ = sf.read(wav_path, dtype="float32"); total = len(x) / SR
    chunks = merge_short(plan_chunks(x, vad=vad))
    if not chunks: raise ValueError("گفتاری در فایل پیدا نشد.")
    segs, used, other, t0, prev_text = [], set(), set(), time.time(), ""
    for c in chunks:
        a = max(0, c["a"] - (SR if c["forced"] else 0))  # هم‌پوشانی یک‌ثانیه‌ای فقط برای برش اجباری
        audio = x[a:c["b"]]
        lang, _ = detect_lang(models.general, audio, other)
        rel, mdl = transcribe_chunk(models, audio, lang, hotwords); used.add(mdl)
        if not rel and (c["b"] - c["a"]) >= SR:  # گفتار VAD بود ولی متنی نیامد
            rel = [{"start": 0.0, "end": (c["b"] - a) / SR, "text": UNCLEAR, "lang": lang, "unclear": True}]
        for s in rel:
            txt = s["text"]
            if c["forced"] and prev_text and not s.get("unclear"): txt = dedupe_overlap(prev_text, txt)
            if not txt: continue
            st, en = a / SR + s["start"], a / SR + s["end"]
            segs.append({**s, "text": txt, "start": round(max(st, 0), 3), "end": round(min(max(en, st + 0.05), total), 3), "lang": lang})
            prev_text = txt
        if prog and prog.dur:
            el = time.time() - t0; done = c["b"] / SR; r = done / el if el > 1 else 0
            prog.put("transcribe", min(done / total, 1), (total - done) / r if r else None)
    for lg in sorted(other): warns.append(f"بخشی از گفتار احتمالاً به زبان «{lg}» است؛ برای این زبان کیفیت تضمین نمی‌شود.")
    segs = collapse_loops(segs, warns)
    segs.sort(key=lambda s: s["start"])
    if not [s for s in segs if not s.get("unclear")]: raise ValueError("گفتاری در فایل پیدا نشد.")
    n_fa = sum(1 for s in segs if s["lang"] == "fa"); main = "fa" if n_fa >= len(segs) - n_fa else "en"
    return main, segs, sorted(used)


def low_confidence(segs, thr=-1.0):
    """بخش‌هایی که مدل خودش اطمینان کمی دارد (avg_logprob خود مدل؛ نه عدد ساختگی)."""
    return [{"s": round(s["start"], 1), "e": round(s["end"], 1)} for s in segs if s.get("lp") is not None and s["lp"] < thr]


def to_srt(segs):
    def ts(t): ms = int(round(t * 1000)); return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"
    return "\n".join(f"{i}\n{ts(s['start'])} --> {ts(max(s['end'], s['start'] + 0.2))}\n{s['text']}\n" for i, s in enumerate(segs, 1))
