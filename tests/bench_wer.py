"""مقایسهٔ مدل‌ها روی صدای واقعی خودتان (نه داده‌ی تمیز). استفاده:
  python3 tests/bench_wer.py audio.wav reference.txt            # فقط مدل عمومی
  FA_MODEL_DIR=~/ct2-fa ASR_FA_REPO=x/y python3 tests/bench_wer.py audio.wav reference.txt   # عمومی و تخصصی
reference.txt متن درستِ نوشته‌شده‌ی دستی است. خروجی: WER هر مدل + WER فقط روی واژه‌های لاتین (برای سنجش گفتار ترکیبی)."""
import sys, os, re, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import asr

def toks(t): return re.findall(r"[\w\u0600-\u06FF']+", re.sub(r"[\u064B-\u065F\u200c]", "", t.lower().replace("ي", "ی").replace("ك", "ک")))
def wer(ref, hyp):
    r, h = toks(ref), toks(hyp)
    d = list(range(len(h) + 1))
    for i, a in enumerate(r, 1):
        prev, d[0] = d[0], i
        for j, b in enumerate(h, 1): prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (a != b))
    return d[-1] / max(len(r), 1)
def latin(t): return " ".join(w for w in toks(t) if re.fullmatch(r"[a-z']+", w))

if __name__ == "__main__":
    wav, ref = sys.argv[1], open(sys.argv[2], encoding="utf-8").read(); w = []
    m = asr.Models.load(w); print("وضعیت:", m.status, w)
    for name, mod in (("general", asr.Models(m.general, None, {})), ("specialist+general", m if m.fa else None)):
        if mod is None: continue
        t0 = time.time(); _, segs, _ = asr.transcribe(mod, wav, [], None); hyp = " ".join(s["text"] for s in segs)
        print(f"{name}: WER={wer(ref, hyp):.3f}  Latin-WER={wer(latin(ref), latin(hyp)):.3f}  time={time.time() - t0:.0f}s")
