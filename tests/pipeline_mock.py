"""مسیر کامل process.py (دانلود ← پردازش ← مهر و رمز ← پاک‌سازی) با GitHub و مدل‌های جعلی (شبیه‌سازی؛ اثبات کیفیت مدل واقعی نیست)."""
import sys, os, json, types, subprocess, tempfile, base64, hmac, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import process as p, asr, notes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
os.chdir(tempfile.mkdtemp())
subprocess.run("ffmpeg -y -v error -f lavfi -i sine=f=300:d=60 s.m4a", shell=True, check=True); data = open("s.m4a", "rb").read()
ok = fail = 0
def t(n, c):
    global ok, fail
    ok, fail = (ok + 1, fail) if c else (ok, fail + 1); print("ok  " if c else "FAIL", n)
deleted, patches = [], []
def gh(*a):
    if "DELETE" in a: deleted.append(a[-1]); return b""
    if a[-1].endswith("/releases/9"): return json.dumps({"assets": [{"name": "part-00000", "id": 1}]}).encode()
    if a[-1].endswith("/assets/1"): return data
    if "PATCH" in a: patches.append(json.loads([x for x in a if x.startswith("body=")][0][5:]))
    return b""
p.gh = gh
S = lambda a, b, x: types.SimpleNamespace(start=a, end=b, text=x, avg_logprob=-.3, no_speech_prob=0)
class M:
    def __init__(s, scripts, langs=None): s.scripts, s.langs = list(scripts), list(langs or [])
    def detect_language(s, a): lg = s.langs.pop(0); return lg, .9, [(lg, .9)]
    def transcribe(s, a, **k): return iter(s.scripts.pop(0)), None
asr.plan_chunks = lambda x, **k: [{"a": 16000, "b": 16000 * 10, "forced": False}, {"a": 16000 * 20, "b": 16000 * 30, "forced": False}]
def mk(fa_state="not_configured"):
    g = M([[S(0, 9, "خب حالا می‌ریم سراغ gradient descent")], [S(0, 9, "this is the learning rate")]], ["fa", "en"])
    return asr.Models(g, None, {"fa": {"state": fa_state}})
p.ensure = lambda a, b: True; p.tr1 = lambda x, a, b: f"[{a}>{b}]{x}"
os.environ.update(JID="pm1", REPO="o/r", REL="9", JOB_SECRET="s3")
def dec(jid):
    key = hmac.new(b"s3", f"{jid}:9".encode(), hashlib.sha256).hexdigest(); e = json.load(open(f"data/results/{jid}.json"))
    return json.loads(AESGCM(bytes.fromhex(key)).decrypt(base64.b64decode(e["iv"]), base64.b64decode(e["ct"]), None))
def run(jid, opts, models=None, stage="all"):
    os.environ.update(JID=jid, STAGE=stage, OPTS=json.dumps({"parts": 1, "size": len(data), **opts}))
    asr.Models.load = classmethod(lambda c, w, fa_dir=None: models or mk()); p.main()
    return dec(jid) if stage in ("all", "seal") else None

# ۱) حالت بدون جزوه: هیچ مدل زبانی ساخته نشود؛ گفتار ترکیبی با زبان واقعی ثبت شود
built = []
notes.LlamaCppBackend = lambda: built.append(1) or (_ for _ in ()).throw(RuntimeError("should not be built"))
r = run("pm1", {"targets": ["en"]})
t("no notes requested -> LLM never constructed, no notes field", not built and "notes" not in r and "notes_error" not in r)
t("faithful mixed-language text", r["text"] == "خب حالا می‌ریم سراغ gradient descent\nthis is the learning rate" and [s["l"] for s in r["segments"]] == ["fa", "en"])
t("translation independent: English segment not re-translated from Persian", "[fa>en]خب" in r["translations"]["en"] and "this is the learning rate" in r["translations"]["en"] and "[fa>en]this" not in r["translations"]["en"])
t("SRT present with real segment times", "00:00:01,000 --> 00:00:10,000" in r["srt"] and "00:00:20,000 --> 00:00:29,000" in r["srt"])
t("model status + timing recorded", r["model"] == "general" and r["model_status"]["fa"]["state"] == "not_configured" and {"decode", "model", "transcribe", "total"} <= set(r["timing"]))
t("release deleted after result", deleted == ["repos/o/r/releases/9"])
t("progress reported with duration", any(x["s"] == "transcribe" for x in patches))

# ۲) جزوه روشن با مدل جعلی
class LLM:
    def chat(s, *a): return json.dumps({"summary": "خلاصه", "items": [{"type": "concept", "text": "gradient descent", "t": "00:01"}]}, ensure_ascii=False)
notes.LlamaCppBackend = lambda: LLM()
r = run("pm2", {"notes": True})
t("notes on -> separate notes output, transcript untouched", "gradient descent" in r["notes"] and r["text"].startswith("خب حالا") and r["notes_coverage"]["extracted"] == r["notes_coverage"]["chunks"] >= 1)

# ۳) شکست مدل جزوه: رونویسی سالم و هشدار روشن
notes.LlamaCppBackend = lambda: (_ for _ in ()).throw(RuntimeError("model download failed"))
r = run("pm3", {"notes": True})
t("notes backend failure -> visible warning, transcript intact, no fake notes", "notes" not in r and "model download failed" in r["notes_error"] and any("جزوه" in x for x in r["warnings"]) and r["text"])

# ۴) شکست مدل تخصصی باید دیده شود
def failed_fa(w, fa_dir=None):
    w.append("مدل تخصصی فارسی آماده نشد (x). رونویسی با مدل عمومی انجام شد."); m = mk("failed"); m.status["fa"]["error"] = "x"; return m
asr.Models.load = classmethod(lambda c, w, fa_dir=None: failed_fa(w)); os.environ.update(JID="pm4", STAGE="all", OPTS=json.dumps({"parts": 1, "size": len(data)})); p.main(); r = dec("pm4")
t("specialist failure is NOT silent", r["model_status"]["fa"]["state"] == "failed" and any("مدل تخصصی" in x for x in r["warnings"]) and not r.get("error"))

# ۵) خرابی ASR -> نتیجهٔ خطا، نه موفقیت
class Boom(M):
    def transcribe(s, *a, **k): raise RuntimeError("boom")
r = run("pm5", {}, models=asr.Models(Boom([], ["fa", "fa"]), None, {}))
t("ASR crash -> error result, no text", "boom" in r["error"] and "text" not in r)

# ۶) اجرای مرحله‌ای: مرحلهٔ process هیچ Secret ندارد و خروجی‌اش هنوز رمز نشده؛ seal آن را رمز می‌کند
os.environ.pop("JOB_SECRET"); deleted.clear()
run("pm6", {}, stage="fetch"); run("pm6", {}, stage="process")
plain = json.load(open("/tmp/job/pm6/out/pm6.json"))
t("process stage ran without JOB_SECRET, nothing deleted yet", plain["text"] and not deleted and not os.path.exists("data/results/pm6.json"))
os.environ["JOB_SECRET"] = "s3"; r = run("pm6", {}, stage="seal")
t("seal stage encrypts + deletes release", r["text"] == plain["text"] and deleted == ["repos/o/r/releases/9"])
# ۷) دانلود ناقص
gh_orig = p.gh; p.gh = lambda *a: json.dumps({"assets": []}).encode() if (a[-1].endswith("/releases/9") and "DELETE" not in a) else gh_orig(*a)
r = run("pm7", {}); t("incomplete upload -> clear error", "ناقص" in r["error"])
print(f"\n{ok} passed, {fail} failed"); sys.exit(1 if fail else 0)
