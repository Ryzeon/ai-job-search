#!/usr/bin/env python3
"""Search Get on Board (getonbrd.com) and read each posting's remote policy.

    python3 .agents/skills/getonbrd-search/cli.py search -q java -q "ai engineer" --days 14 --country Peru
    python3 .agents/skills/getonbrd-search/cli.py detail <job-id>

Uses the public API (/api/v0/search/jobs) for the listing and the public job page
for the parts the API does not expose: the remote policy ("Fully remote" vs
"Locally remote only ... must reside in X") and the application language.
No auth, standard library only. Keep the volume low.
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://www.getonbrd.com/api/v0/search/jobs"
UA = {"User-Agent": "Mozilla/5.0 (ai-job-search getonbrd-search)"}


def get(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def text(raw: str) -> str:
    raw = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw)))


def policy(job_id: str) -> dict:
    t = text(get(f"https://www.getonbrd.com/jobs/{job_id}"))
    m = re.search(r"(Fully remote[^.]{0,90}|Locally remote only[^.]{0,140}|Hybrid[^.]{0,90})", t)
    lang = re.search(r"Requires applying in (\w+)", t)
    return {"remote_policy": m.group(0).strip() if m else "", "apply_language": lang.group(1) if lang else ""}


def search(args) -> list:
    seen, out = set(), []
    for q in args.query:
        for page in range(1, args.pages + 1):
            url = f"{API}?{urllib.parse.urlencode({'query': q, 'per_page': 100, 'page': page})}"
            data = json.loads(get(url)).get("data", [])
            for j in data:
                a = j["attributes"]
                if j["id"] in seen:
                    continue
                if not (a.get("remote") or a.get("remote_modality") == "fully_remote"):
                    continue
                if time.time() - int(a["published_at"]) > args.days * 86400:
                    continue
                seen.add(j["id"])
                out.append({
                    "id": j["id"], "title": a["title"], "category": a.get("category_name"),
                    "min_salary": a.get("min_salary"), "max_salary": a.get("max_salary"),
                    "published_at": int(a["published_at"]), "applications": a.get("applications_count"),
                    "url": f"https://www.getonbrd.com/jobs/{j['id']}",
                })
            if len(data) < 100:
                break
    for job in out:
        job.update(policy(job["id"]))
        pol = job["remote_policy"]
        job["eligible"] = bool(re.search(r"anywhere", pol)) or (
            bool(args.country) and bool(re.search(re.escape(args.country), pol, re.I)))
    if args.country:
        out = [j for j in out if j["eligible"]]
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("-q", "--query", action="append", required=True)
    s.add_argument("--days", type=int, default=14, help="posted within N days")
    s.add_argument("--pages", type=int, default=1)
    s.add_argument("--country", help="keep only postings open to this country (or anywhere)")
    d = sub.add_parser("detail")
    d.add_argument("job_id")
    args = p.parse_args()
    if args.cmd == "search":
        json.dump(search(args), sys.stdout, ensure_ascii=False, indent=1)
    else:
        a = None
        for page in (1,):
            data = json.loads(get(f"{API}?{urllib.parse.urlencode({'query': args.job_id.split('-')[0], 'per_page': 100})}")).get("data", [])
            a = next((j["attributes"] for j in data if j["id"] == args.job_id), None)
        res = {"id": args.job_id, **policy(args.job_id)}
        if a:
            res.update({k: text(a.get(k) or "") for k in ("title", "description", "functions", "desirable", "benefits")})
        else:
            res["page_text"] = text(get(f"https://www.getonbrd.com/jobs/{args.job_id}"))[:6000]
        json.dump(res, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
