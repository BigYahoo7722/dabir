import json, glob, os, time, subprocess, datetime
repo, now = os.environ["REPO"], time.time()
for f in glob.glob("data/results/*.json"):
    try: fin = json.load(open(f)).get("finished") or os.path.getmtime(f)
    except Exception: fin = 0
    if now - fin > int(os.environ.get("RETAIN_SECONDS", 7500)): os.remove(f)
for r in json.loads(subprocess.run(["gh", "api", f"repos/{repo}/releases?per_page=100"], capture_output=True, check=True).stdout):
    t = datetime.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")).timestamp()
    if r["draft"] and r["tag_name"].startswith("job-") and now - t > 8 * 3600:
        subprocess.run(["gh", "api", "-X", "DELETE", f"repos/{repo}/releases/{r['id']}"])
