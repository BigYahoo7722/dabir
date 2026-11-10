"""جزوه‌نویسی آموزشی از رونویسی کامل: استخراج قطعه‌به‌قطعه ← ادغام ← تطبیق با متن منبع.

مدل زبانی فقط «استخراج‌کننده» است و فقط از متن همان قطعه استفاده می‌کند. هر مورد استخراج‌شده که عدد یا
واژهٔ لاتینی‌اش در متن منبع نباشد، به‌جای جزوهٔ اصلی در «نیازمند بررسی» می‌رود. رونویسی اصلی هیچ‌گاه تغییر نمی‌کند.
"""
import json, os, re, difflib

NOTES_REPO = os.environ.get("NOTES_GGUF_REPO", "unsloth/Qwen3-4B-Instruct-2507-GGUF")
NOTES_FILE = os.environ.get("NOTES_GGUF_FILE", "Qwen3-4B-Instruct-2507-Q4_K_M.gguf")
NOTES_REV = os.environ.get("NOTES_GGUF_REV") or None
TYPES = {"definition": "تعریف‌ها و اصطلاحات", "concept": "مفاهیم و توضیحات", "formula": "فرمول‌ها، روابط و مراحل",
         "example": "مثال‌ها و کاربردها", "compare": "مقایسه‌ها و ارتباط مفاهیم", "emphasis": "نکات مهم و تأکیدهای استاد",
         "data": "اعداد و داده‌ها", "qa": "پرسش و پاسخ کلاسی"}
SYSTEM = ("تو دستیار جزوه‌نویسی هستی. فقط از «متن جلسه» که کاربر می‌دهد استفاده کن؛ از دانش خودت چیزی اضافه نکن. "
          "فقط محتوای آموزشی را استخراج کن و سلام‌واحوال‌پرسی، صحبت اداری، حاشیه‌ها و پرسش‌های نامرتبط را رها کن. "
          "تعریف، فرمول، عدد یا مثالی که در متن نیست نساز و عدد نامفهوم را حدس نزن. اصطلاحات انگلیسی را همان‌طور که هست نگه دار. "
          "اگر سؤال دانشجو باعث توضیح آموزشی شده، آن را با type=qa نگه دار. "
          "خروجی فقط یک JSON معتبر: {\"summary\": \"یک جملهٔ خلاصه از همین قطعه\", \"items\": [{\"type\": \"definition|concept|formula|example|compare|emphasis|data|qa\", \"text\": \"...\", \"t\": \"mm:ss\"}]}. "
          "اگر قطعه محتوای آموزشی ندارد: {\"summary\": \"\", \"items\": []}.")


def mmss(s): s = int(s); return f"{s // 60:02d}:{s % 60:02d}"


def chunk_segments(segs, max_chars=3000):
    """تقسیم رونویسی به قطعه‌هایی با مرز سگمنت (نه وسط جمله). همهٔ سگمنت‌ها دقیقاً یک بار پوشش داده می‌شوند."""
    out, cur, n = [], [], 0
    for s in segs:
        if cur and n + len(s["text"]) > max_chars:
            out.append(cur); cur, n = [], 0
        cur.append(s); n += len(s["text"]) + 1
    if cur: out.append(cur)
    return [{"i": i, "start": c[0]["start"], "end": c[-1]["end"],
             "text": "\n".join(f"[{mmss(s['start'])}] {s['text']}" for s in c), "plain": " ".join(s["text"] for s in c)}
            for i, c in enumerate(out)]


_FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
def norm(t): return t.translate(_FA).lower()


def ungrounded(text, source):
    """عدد یا واژهٔ لاتینی در متن جزوه که در منبع نیست. (برای واژه‌های فارسی بازبینی خودکار قابل‌اعتماد نیست.)"""
    src, bad = norm(source), []
    for tok in re.findall(r"\d+(?:[.,٫]\d+)?", norm(text)):
        if tok.replace(",", ".") not in src.replace(",", ".").replace("٫", "."): bad.append(tok)
    for tok in re.findall(r"[A-Za-z][A-Za-z\-']{2,}", text):
        if tok.lower() not in src: bad.append(tok)
    return bad


def parse(raw):
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m: return None
    try:
        d = json.loads(m.group(0))
        if isinstance(d.get("items"), list): return d
    except Exception: pass
    return None


def extract(llm, ch):
    for _ in range(2):  # یک تلاش مجدد برای JSON خراب
        d = parse(llm.chat(SYSTEM, "متن جلسه:\n" + ch["text"], 1200))
        if d is not None: return d
    return None


def dedupe(items, thr=0.88):
    out = []
    for it in items:
        if any(o["type"] == it["type"] and difflib.SequenceMatcher(None, o["text"], it["text"]).ratio() >= thr for o in out): continue
        out.append(it)
    return out


def build(segs, llm, unclear_ranges=None, prog=None):
    """خروجی: {'markdown','review','coverage'}. اگر قطعه‌ای شکست بخورد، گزارش می‌شود نه اینکه ساکت حذف شود."""
    chunks = chunk_segments(segs); items, summaries, review, covered = [], [], [], []
    for k, ch in enumerate(chunks):
        if prog: prog.put("notes", k / max(len(chunks), 1), force=True)
        d = extract(llm, ch)
        if d is None:
            review.append({"t": f"{mmss(ch['start'])}–{mmss(ch['end'])}", "why": "استخراج خودکار این بخش ناموفق بود؛ از رونویسی کامل استفاده کنید."}); continue
        covered.append(ch["i"])
        if d.get("summary"): summaries.append((ch["start"], str(d["summary"]).strip()))
        for it in d["items"]:
            if not isinstance(it, dict) or not str(it.get("text", "")).strip(): continue
            typ = it.get("type") if it.get("type") in TYPES else "concept"; txt = str(it["text"]).strip()
            t = it.get("t") if re.fullmatch(r"\d{1,3}:\d{2}", str(it.get("t", ""))) else mmss(ch["start"])
            bad = ungrounded(txt, ch["plain"])
            if bad: review.append({"t": t, "why": "مقدارهای «" + "، ".join(dict.fromkeys(bad)) + "» در متن منبع این بخش پیدا نشد", "text": txt})
            else: items.append({"type": typ, "text": txt, "t": t})
    items = dedupe(items)
    md = ["# جزوهٔ جلسه", ""]
    if summaries:
        md += ["## خلاصهٔ کلی", ""] + [f"- ({mmss(s)}) {t}" for s, t in summaries if t] + [""]
    for typ, title in TYPES.items():
        sel = [i for i in items if i["type"] == typ]
        if sel: md += [f"## {title}", ""] + [f"- {i['text']} ‹{i['t']}›" for i in sel] + [""]
    if not items: md += ["محتوای آموزشی قابل‌اعتمادی در این رونویسی پیدا نشد.", ""]
    rv = list(review) + [{"t": f"{r['s']:.0f}s–{r['e']:.0f}s", "why": "صدا کم‌کیفیت یا نامفهوم بود"} for r in (unclear_ranges or [])]
    if rv:
        md += ["## نیازمند بررسی", ""] + [f"- ‹{r['t']}› {r['why']}" + (f": {r['text']}" if r.get("text") else "") for r in rv] + [""]
    md.append("> این جزوه از روی رونویسی خودکار ساخته شده است؛ زمان‌های داخل ‹ › برای یافتن منبع در صوت‌اند.")
    return {"markdown": "\n".join(md), "review": rv, "coverage": {"chunks": len(chunks), "extracted": len(covered)}}


class LlamaCppBackend:
    """مدل زبانی محلی GGUF (بدون API پولی). بارگیری یک‌بار و با کش HuggingFace؛ شکست بارگیری خطا می‌دهد، جزوهٔ ساختگی نمی‌سازد."""
    def __init__(self, n_ctx=8192):
        from huggingface_hub import hf_hub_download
        from llama_cpp import Llama
        p = hf_hub_download(NOTES_REPO, NOTES_FILE, revision=NOTES_REV)
        self.m = Llama(model_path=p, n_ctx=n_ctx, n_threads=os.cpu_count() or 2, verbose=False)

    def chat(self, system, user, max_tokens=1200):
        r = self.m.create_chat_completion(messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                                          max_tokens=max_tokens, temperature=0.1)
        return r["choices"][0]["message"]["content"]
