// dabir API: پروکسی امن بین سایت و GitHub. توکن و JOB_SECRET فقط اینجا (Secret کلودفلر) هستند.
const CH = 64 * 1024 * 1024;
const LANGS = new Set("fa en ar tr fr de es pt it ru zh ja ko hi ur bn id nl pl uk el".split(" "));
const QUAL = new Set(["small", "medium", "large-v3"]);
const te = new TextEncoder();
const hex = b => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
export async function sign(secret, msg) {
  const k = await crypto.subtle.importKey("raw", te.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", k, te.encode(msg)));
}
const same = (a, b) => a.length === b.length && [...a].reduce((x, c, i) => x | (c.charCodeAt(0) ^ b.charCodeAt(i)), 0) === 0;
export function clean(o = {}, max = 21) {
  const n = Number(o.nspeakers);
  return {
    targets: [...new Set((Array.isArray(o.targets) ? o.targets : []).filter(t => LANGS.has(t)))].slice(0, max),
    denoise: !!o.denoise, speakers: !!o.speakers,
    nspeakers: Number.isInteger(n) && n >= 2 && n <= 8 ? n : null,
    quality: QUAL.has(o.quality) ? o.quality : "medium",
    source: ["fa", "en"].includes(o.source) ? o.source : "auto",
  };
}
const gh = (env, path, init = {}) => fetch("https://api.github.com/repos/" + env.REPO + path, {
  ...init, headers: { Authorization: "Bearer " + env.GH_TOKEN, Accept: "application/vnd.github+json", "User-Agent": "dabir-worker", "X-GitHub-Api-Version": "2022-11-28", ...(init.headers || {}) } });

export default {
  async fetch(req, env) {
    const origin = req.headers.get("Origin") || "", allow = (env.ALLOWED_ORIGIN || "").split(",");
    const cors = { "Access-Control-Allow-Origin": allow.includes(origin) ? origin : allow[0], "Access-Control-Allow-Headers": "Content-Type,X-Key", "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS", Vary: "Origin", "Cache-Control": "no-store" };
    const J = (b, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { ...cors, "Content-Type": "application/json" } });
    if (origin && !allow.includes(origin)) return J({ error: "مبدأ درخواست مجاز نیست." }, 403);
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    try { return await route(req, env, J); } catch (e) { return J({ error: "خطای سرور؛ کمی بعد دوباره امتحان کنید." }, 500); }
  },
};

async function route(req, env, J) {
  const u = new URL(req.url), p = u.pathname.replace(/\/+$/, ""), max = Number(env.MAX_BYTES) || 1073741824;
  if (req.method === "POST" && p === "/api/jobs") {
    const b = await req.json().catch(() => ({}));
    if (!Number.isInteger(b.size) || b.size < 1) return J({ error: "حجم فایل نامعتبر است." }, 400);
    if (b.size > max) return J({ error: "حجم فایل بیش از حد مجاز است." }, 413);
    const act = await gh(env, "/releases?per_page=100");
    if (act.ok && (await act.json()).filter(r => r.draft && r.tag_name.startsWith("job-")).length >= (Number(env.MAX_ACTIVE) || 20)) return J({ error: "ظرفیت پردازش فعلاً پر است؛ چند دقیقه بعد تلاش کنید." }, 429);
    const br = await gh(env, "/git/ref/heads/jobs");
    if (br.status === 404) {
      const m = await gh(env, "/git/ref/heads/" + (env.BRANCH || "main"));
      if (!m.ok) return J({ error: "پیکربندی سرور ناقص است." }, 500);
      await gh(env, "/git/refs", { method: "POST", body: JSON.stringify({ ref: "refs/heads/jobs", sha: (await m.json()).object.sha }) });
    }
    const id = hex(crypto.getRandomValues(new Uint8Array(8)));
    const r = await gh(env, "/releases", { method: "POST", body: JSON.stringify({ tag_name: "job-" + id, name: "job", draft: true, target_commitish: env.BRANCH || "main" }) });
    if (!r.ok) return J({ error: "ساخت کار ناموفق بود." }, 502);
    const rel = (await r.json()).id;
    return J({ id, rel, key: await sign(env.JOB_SECRET, `${id}:${rel}`), chunk: CH, parts: Math.ceil(b.size / CH), opts: clean(b.opts) });
  }
  const m = p.match(/^\/api\/jobs\/([0-9a-f]{16})(?:\/(parts\/(\d{1,3})|start))?$/);
  if (!m) return J({ error: "یافت نشد." }, 404);
  const id = m[1], rel = u.searchParams.get("rel") || "", key = req.headers.get("X-Key") || u.searchParams.get("key") || "";
  if (!/^\d+$/.test(rel) || !same(key, await sign(env.JOB_SECRET, `${id}:${rel}`))) return J({ error: "دسترسی نامعتبر." }, 403);
  if (m[3] !== undefined && req.method === "PUT") {
    const n = Number(m[3]), len = Number(req.headers.get("Content-Length") || 0);
    if (n >= Math.ceil(max / CH) || !len || len > CH) return J({ error: "تکهٔ نامعتبر." }, 400);
    const r = await fetch(`https://uploads.github.com/repos/${env.REPO}/releases/${rel}/assets?name=part-${String(n).padStart(5, "0")}`, { method: "POST", body: req.body, duplex: "half", headers: { Authorization: "Bearer " + env.GH_TOKEN, "Content-Type": "application/octet-stream", "Content-Length": String(len), "User-Agent": "dabir-worker" } });
    return r.status === 201 || r.status === 422 ? J({ ok: true }) : J({ error: "ذخیرهٔ تکه ناموفق بود (" + r.status + ")." }, 502);
  }
  if (m[2] === "start" && req.method === "POST") {
    const b = await req.json().catch(() => ({}));
    if (!Number.isInteger(b.size) || b.size < 1 || b.size > max || !Number.isInteger(b.parts) || b.parts !== Math.ceil(b.size / CH)) return J({ error: "مشخصات فایل نامعتبر است." }, 400);
    if ((await runState(env, id)) !== "none") return J({ ok: true, again: true });
    const r = await gh(env, "/actions/workflows/process.yml/dispatches", { method: "POST", body: JSON.stringify({ ref: env.BRANCH || "main", inputs: { id, rel, opts: JSON.stringify({ ...clean(b.opts), parts: b.parts, size: b.size }) } }) });
    return r.status === 204 ? J({ ok: true }) : J({ error: "شروع ربات ناموفق بود (" + r.status + ")." }, 502);
  }
  if (!m[2] && req.method === "GET") {
    const r = await gh(env, `/contents/results/${id}.json?ref=jobs`, { headers: { Accept: "application/vnd.github.raw+json" } });
    if (r.ok) return J({ state: "done", payload: await r.json() });
    const s = await runState(env, id);
    let progress = null;
    if (s === "in_progress") {
      const rr = await gh(env, `/releases/${rel}`);
      if (rr.ok) { try { progress = JSON.parse((await rr.json()).body || "null"); } catch (e) { progress = null; } }
    }
    return J({ state: { none: "queued", queued: "queued", in_progress: "running", failed: "failed", success: "finishing" }[s] || "queued", progress });
  }
  return J({ error: "روش نامعتبر." }, 405);
}
async function runState(env, id) {
  const r = await gh(env, "/actions/workflows/process.yml/runs?per_page=50");
  if (!r.ok) return "none";
  const run = (await r.json()).workflow_runs.find(x => x.display_title === "process " + id);
  if (!run) return "none";
  return run.status !== "completed" ? run.status : run.conclusion === "success" ? "success" : "failed";
}
