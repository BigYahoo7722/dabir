"""تست واحد منطق رونویسی (با مدل جعلی). کیفیت واقعی گفتار را اندازه نمی‌گیرد؛ فقط منطق قطعه‌بندی، زبان، زمان و خطا را می‌آزماید."""
import sys, os, types, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np, soundfile as sf, asr
ok = fail = 0
def t(name, c):
    global ok, fail
    ok, fail = (ok + 1, fail) if c else (ok, fail + 1); print("ok  " if c else "FAIL", name)
S = lambda a, b, x, lp=-0.3, ns=0.0: types.SimpleNamespace(start=a, end=b, text=x, avg_logprob=lp, no_speech_prob=ns)

# --- قطعه‌بندی
cs = asr.merge_short([{"a": 0, "b": 8000, "forced": False}, {"a": 9000, "b": 16000 * 5, "forced": False}, {"a": 16000 * 20, "b": 16000 * 25, "forced": False}])
t("short neighbouring chunks merged, far chunk kept", len(cs) == 2 and cs[0]["b"] == 16000 * 5)
t("long chunks not merged", len(asr.merge_short([{"a": 0, "b": 16000 * 10, "forced": False}, {"a": 16000 * 10 + 100, "b": 16000 * 20, "forced": False}])) == 2)

# --- هم‌پوشانی و تکرار واقعی
t("overlap duplicate removed", asr.dedupe_overlap("این مدل با داده آموزش می‌بیند و", "با داده آموزش می‌بیند و بعد ارزیابی می‌شود") == "بعد ارزیابی می‌شود")
t("real repetition kept (no overlap)", asr.dedupe_overlap("من فکر می‌کنم", "من من فکر می‌کنم درسته") == "من من فکر می‌کنم درسته")
w = []; seg = lambda x, i: {"start": i, "end": i + 1, "text": x}
r = asr.collapse_loops([seg("آره آره آره", i) for i in range(3)], w)
t("short real repeats kept", len(r) == 3 and not w)
w = []; r = asr.collapse_loops([seg("ممنون که تماشا کردید دوستان", i) for i in range(5)], w)
t("hallucination loop collapsed + reported", len(r) == 1 and len(w) == 1)

# --- زمان‌بندی
t("valid timing accepted", asr.valid_timing([{"start": 0, "end": 4, "text": "a"}, {"start": 4, "end": 9, "text": "b"}], 10))
t("one-giant-or-overflow timing rejected", not asr.valid_timing([{"start": 0, "end": 40, "text": "a"}], 10))
t("non-monotonic rejected", not asr.valid_timing([{"start": 5, "end": 6, "text": "a"}, {"start": 1, "end": 2, "text": "b"}], 10))
sp = asr.split_timing("جمله اول است. جمله دوم کمی بلندتر است. سوم؟", 10.0, 22.0)
t("split_timing stays inside chunk, monotonic, marked estimate", len(sp) == 3 and sp[0]["start"] == 10 and abs(sp[-1]["end"] - 22) < 1e-6 and all(a["end"] <= b["start"] + 1e-6 for a, b in zip(sp, sp[1:])) and all(s["est"] for s in sp))

# --- رونویسی با مدل جعلی: گفتار ترکیبی، مدل تخصصی، ترتیب، نامفهوم
class M:
    def __init__(s, name, script): s.name, s.script, s.calls, s.langs = name, list(script), 0, []
    def detect_language(s, a): lg = s.langs.pop(0); return lg, .9, [(lg, .9), ("en" if lg == "fa" else "fa", .05)]
    def transcribe(s, audio, language=None, **k):
        s.calls += 1; out = s.script.pop(0); return iter(out), None
d = tempfile.mkdtemp(); sf.write(d + "/a.wav", np.zeros(16000 * 60, dtype="float32") + 0.01, 16000)
vad = lambda x: [{"start": 16000 * 1, "end": 16000 * 10}, {"start": 16000 * 20, "end": 16000 * 30}, {"start": 16000 * 40, "end": 16000 * 42}]
g = M("g", [[S(0, 9, "now gradient descent")]]); g.langs = ["fa", "en", "fa"]
fa = M("fa", [[S(0, 9, "خب حالا می‌ریم سراغ آها")]]);
# چنک ۳ فارسی است ولی مدل تخصصی خروجی ندارد (هم با زمان هم بدون زمان) -> نامفهوم
fa.script += [[], []]
m = asr.Models(g, fa, {"fa": {"state": "ok"}}); w = []
lang, segs, used = asr.transcribe(m, d + "/a.wav", w, vad=vad)
t("order + absolute times", [round(s["start"]) for s in segs] == [1, 20, 40] and segs[1]["start"] > segs[0]["end"])
t("per-chunk language: fa->specialist, en->general", [s["lang"] for s in segs] == ["fa", "en", "fa"] and fa.calls >= 2 and g.calls >= 1)
t("English words kept verbatim", segs[1]["text"] == "now gradient descent")
t("short colloquial 'آها' kept", "آها" in segs[0]["text"])
t("empty model output on real speech -> [نامفهوم], no invented text", segs[2]["text"] == asr.UNCLEAR and segs[2].get("unclear"))
t("used models reported", used == ["fa-specialist", "general"])
srt = asr.to_srt(segs); t("SRT has 3 cues with ascending timestamps", srt.count("-->") == 3 and "00:00:01,000 --> 00:00:10,000" in srt)

# --- Models.load: شکست مدل تخصصی ساکت نیست
import faster_whisper, huggingface_hub
faster_whisper.WhisperModel = lambda *a, **k: object(); huggingface_hub.snapshot_download = lambda *a, **k: "/x"
asr.FA_REPO = "someone/model"; w = []
mm = asr.Models.load(w, fa_dir="/nonexistent")
t("specialist failure visible in status + warnings", mm.fa is None and mm.status["fa"]["state"] == "failed" and any("مدل تخصصی" in x for x in w))
asr.FA_REPO = None; w = []; mm = asr.Models.load(w)
t("not configured specialist -> no warning noise", mm.status["fa"]["state"] == "not_configured" and not w)
print(f"\n{ok} passed, {fail} failed"); sys.exit(1 if fail else 0)
