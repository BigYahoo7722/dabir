"""تست منطق جزوه‌سازی با مدل زبانی جعلی. کیفیت واقعی خلاصه‌سازی مدل را اندازه نمی‌گیرد؛ پوشش، تطبیق با منبع و رفتار خطا را می‌آزماید."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import notes
ok = fail = 0
def t(n, c):
    global ok, fail
    ok, fail = (ok + 1, fail) if c else (ok, fail + 1); print("ok  " if c else "FAIL", n)
seg = lambda a, b, x: {"start": a, "end": b, "text": x}
segs = [seg(0, 20, "سلام بچه‌ها خوش اومدید، ببخشید تلفن دارم."),
        seg(20, 60, "یادگیری ماشین یعنی ساخت مدل از داده. learning rate را 0.01 می‌گیریم."),
        seg(60, 90, "دانشجو پرسید gradient descent چیه؟ استاد گفت کاهش تدریجی خطا با گام‌های کوچک."),
        seg(90, 130, "در پایان جلسه تأکید می‌کنم که overfitting خطرناک‌ترین مشکل است.")]
class LLM:
    def __init__(s, fn): s.fn, s.calls = fn, []
    def chat(s, sys_, user, mt=0): s.calls.append(user); return s.fn(user)
def good(user):
    if "تلفن" in user: return json.dumps({"summary": "", "items": []}, ensure_ascii=False)
    its = []
    if "learning rate" in user: its += [{"type": "definition", "text": "یادگیری ماشین: ساخت مدل از داده", "t": "00:20"}, {"type": "data", "text": "learning rate برابر 0.01 است", "t": "00:35"}]
    if "gradient descent" in user: its.append({"type": "qa", "text": "gradient descent: کاهش تدریجی خطا با گام‌های کوچک", "t": "01:00"})
    if "overfitting" in user: its.append({"type": "emphasis", "text": "overfitting خطرناک‌ترین مشکل است", "t": "01:30"})
    return "متن اضافه " + json.dumps({"summary": "خلاصه", "items": its}, ensure_ascii=False)
# همهٔ قطعه‌ها پوشش داده شوند (حتی اگر هر سگمنت یک قطعه شود)
chs = notes.chunk_segments(segs, max_chars=60)
t("chunks cover every segment once, in order", len(chs) >= 3 and chs[0]["start"] == 0 and chs[-1]["end"] == 130 and all(a["end"] <= b["start"] for a, b in zip(chs, chs[1:])))
llm = LLM(good); import notes as N
orig = N.chunk_segments; N.chunk_segments = lambda s, max_chars=3000: orig(s, 60)
r = notes.build(segs, llm); md = r["markdown"]
t("all chunks sent to LLM (end of file included)", r["coverage"]["extracted"] == r["coverage"]["chunks"] and any("overfitting" in c for c in llm.calls))
t("end-of-lecture emphasis kept", "overfitting" in md)
t("definition/number/QA kept with timestamps", "0.01" in md and "‹00:20›" in md and "gradient descent" in md and "پرسش و پاسخ کلاسی" in md)
t("administrative chatter dropped", "تلفن" not in md and "خوش اومدید" not in md)
# جعل: عدد/واژهٔ لاتینی که در منبع نیست
def inventing(user):
    return json.dumps({"summary": "", "items": [{"type": "formula", "text": "w = w - 0.5 * gradient و momentum", "t": "01:00"}]}, ensure_ascii=False) if "gradient descent" in user else json.dumps({"summary": "", "items": []})
r = notes.build(segs, LLM(inventing)); md = r["markdown"]
t("invented number/term NOT in notes body", "0.5" not in md.split("## نیازمند بررسی")[0] and "momentum" not in md.split("## نیازمند بررسی")[0])
t("invented item routed to review section", "## نیازمند بررسی" in md and any("0.5" in x.get("text", "") for x in r["review"]))
t("grounded check ignores Persian digits mapping", notes.ungrounded("مقدار ۰.۰۱", "learning rate 0.01") == [])
# خرابی خروجی مدل: ساکت حذف نشود
r = notes.build(segs, LLM(lambda u: "این JSON نیست"))
t("unparseable chunks reported, not silently dropped", r["coverage"]["extracted"] == 0 and len(r["review"]) == r["coverage"]["chunks"] and "محتوای آموزشی قابل‌اعتمادی" in r["markdown"])
# تکرار
dup = lambda u: json.dumps({"summary": "", "items": [{"type": "concept", "text": "کاهش تدریجی خطا با گام‌های کوچک", "t": "01:00"}, {"type": "concept", "text": "کاهش تدریجی خطا با گام های کوچک", "t": "01:05"}]}, ensure_ascii=False)
t("near-duplicates merged", notes.build(segs[2:3], LLM(dup))["markdown"].count("کاهش تدریجی خطا") == 1)
t("unclear audio ranges listed for review", "صدا کم‌کیفیت" in notes.build(segs, LLM(good), [{"s": 5, "e": 9}])["markdown"])
print(f"\n{ok} passed, {fail} failed"); sys.exit(1 if fail else 0)
