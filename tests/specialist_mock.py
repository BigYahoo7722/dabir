"""مدل تخصصی فارسی، پیشرفت زنده و زمان‌سنجی با مدل جعلی (شبیه‌سازی؛ اثبات کیفیت مدل واقعی نیست)."""
import sys, os, json, types, subprocess, tempfile, base64, hmac, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import process as p, faster_whisper.vad as vad
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
os.chdir(tempfile.mkdtemp())
subprocess.run("ffmpeg -y -v error -f lavfi -i sine=f=300:d=60 s.m4a", shell=True, check=True)
data = open("s.m4a", "rb").read()
patches = []
def gh(*a):
    if a[-1].endswith("/releases/9"): return json.dumps({"assets": [{"name": "part-00000", "id": 1}]}).encode()
    if a[-1].endswith("/assets/1"): return data
    if "PATCH" in a: patches.append(json.loads([x for x in a if x.startswith("body=")][0][5:]))
    return b""
p.gh = gh
calls = []
class Spec:
    def transcribe(s, audio, **k):
        calls.append(k); assert k["without_timestamps"] is True and k["language"] == "fa" and hasattr(audio, "shape")
        return iter([types.SimpleNamespace(start=0, end=1, text=" سلام دنیا ")]), None
vad.get_speech_timestamps = lambda x, o=None, **k: [{"start": 16000, "end": 16000 * 20}, {"start": 16000 * 25, "end": 16000 * 40}]
p.p = None
S = lambda t: types.SimpleNamespace(start=0, end=1, text=t)
class Base:
    def transcribe(s, w, language=None, vad_filter=True, **k):
        return iter([S("base text")]), types.SimpleNamespace(language="fa", all_language_probs=[("fa", .9), ("en", .05)])
p.load_model = lambda n, w: (Base(), n); p.ensure = lambda a, b: True; p.tr1 = lambda t, a, b: f"[{b}]{t}"
os.environ.update(JID="sp1", REPO="o/r", REL="9", JOB_SECRET="s3")
def run(jid, opts):
    os.environ.update(JID=jid, OPTS=json.dumps({"parts": 1, "size": len(data), **opts})); p.main()
    key = hmac.new(b"s3", f"{jid}:9".encode(), hashlib.sha256).hexdigest(); e = json.load(open(f"data/results/{jid}.json"))
    return json.loads(AESGCM(bytes.fromhex(key)).decrypt(base64.b64decode(e["iv"]), base64.b64decode(e["ct"]), None))
# ۱) مسیر تخصصی
p.load_fa = lambda w: Spec()
r = run("sp1", {"source": "fa", "quality": "large-v3", "targets": ["en"]})
assert r["model"] == "fa-specialist" and r["language"] == "fa", r
assert [s["t"] for s in r["segments"]] == ["سلام دنیا", "سلام دنیا"] and r["segments"][0]["s"] == 1.0 and r["segments"][1]["e"] == 40.0
assert len(calls) == 2 and "en" in r["translations"]
assert {"decode", "model", "transcribe", "translate", "total"} <= set(r["timing"]), r["timing"]
assert any(x["s"] == "transcribe" for x in patches) and any(x["s"] == "translate" for x in patches), patches
assert all(x["d"] == r["duration"] for x in patches if x["s"] in ("transcribe", "translate"))
# ۲) مدل تخصصی نباشد -> large-v3 با هشدار
p.load_fa = lambda w: (w.append("مدل تخصصی فارسی آماده نبود؛ از large-v3 استفاده شد.") or None)
r = run("sp2", {"source": "fa", "quality": "large-v3"})
assert r["model"] == "large-v3" and r["text"] == "base text" and any("آماده نبود" in x for x in r["warnings"]), r
# ۳) مدل تخصصی خراب شود -> بازگشت امن
class Bad:
    def transcribe(s, *a, **k): raise RuntimeError("boom")
p.load_fa = lambda w: Bad()
r = run("sp3", {"source": "fa", "quality": "large-v3"})
assert r["model"] == "large-v3" and r["text"] == "base text" and any("boom" in x for x in r["warnings"]), r
# ۴) فقط فارسی + دقیق‌ترین از مدل تخصصی استفاده می‌کند
used = []
p.load_fa = lambda w: used.append(1) or Spec()
run("sp4", {"source": "en", "quality": "large-v3"}); run("sp5", {"source": "fa", "quality": "medium"}); run("sp6", {"source": "auto", "quality": "large-v3"})
assert not used, "specialist must only run for source=fa + quality=large-v3"
print("specialist mock OK")
